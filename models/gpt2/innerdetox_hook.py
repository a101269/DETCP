from functools import partial
from mmengine import Registry
import torch
import torch.nn.functional as F

InnerDetoxHook = Registry('innerdetox_hook')


@InnerDetoxHook.register_module()
class BaseInnerDetoxHook():
    def __init__(self, norm_exp=0, neg_sim_exp=0, renorm=False):
        self.mem = dict()
        self.hook_handles = dict()
        self.norm_exp = norm_exp
        self.neg_sim_exp = neg_sim_exp
        self.renorm = renorm

    def read_hook(self, module, input, output, module_name=None, prompt_end_indices=None):

        # print(input[0].shape) #  1  torch.Size([128, 20, 37, 64])
        # print(output.shape) #128, 20, 37, 64     // 128, 20, 1, 64        正负各64，batch 64, head=20, length, dim/head=64,64*20=1280
        half_bsz = output.shape[0] // 2 # 正负两句，对半分，分别是正、负
        # neg - pos
        if self.mem.get(module_name, None) is None:  # remove_hooks会清楚各层中间参数，self.mem用来cache中间计算结果，
            self.mem[module_name] = dict()
        self.mem[module_name]['delta'] = (output[half_bsz:,:,-1:,:] - output[:half_bsz,:,-1:,:]).detach() # 最后一个字符的表示，负-正的差值，pos在前
        if prompt_end_indices is not None and self.mem[module_name].get('neg_end', None) is None: #  给neg_end赋值
            h,n,d = output.shape[1:]  # head, length, dim
            neg_end_indices = prompt_end_indices[half_bsz:,None,None,None].expand(-1, h, 1, d).to(output.device)
            self.mem[module_name]['neg_end'] = \
                torch.gather(output[half_bsz:,:,:,:], dim=2, index=neg_end_indices)[:1,:,:,:].detach() # 保存负向结果


    def write_hook(self, module, input, output, module_name=None):
        return self.modification_fn(output, self.mem[module_name], module_name)

    def register_hooks(self, model, hook):
        for n, m in model.named_modules():
            if self.module_match_fn(n):
                handle = m.register_forward_hook(partial(hook, module_name=n))
                self.hook_handles[n] = handle

    def remove_hooks(self):
        for n in list(self.hook_handles.keys()):
            self.hook_handles[n].remove()
            self.hook_handles.pop(n)
    
    def module_match_fn(self, module_name):
        return module_name.endswith('.before_mergehead')

    def modification_fn(self, v, v_mem, module_name): # 计算实际的input后与正负结果进行加权，改变 output 输出结果
        if self.renorm:
            v_norm = v[:,:,-1:,:].norm(dim=(1,3), keepdim=True)

        delta = v_mem['delta']
        neg_end = v_mem['neg_end']

        norm_scale = 1
        if self.norm_exp > 0:
            norm_scale = (1 + delta.norm(dim=-1, keepdim=True)) ** self.norm_exp

        neg_sim_scale = 1
        if self.neg_sim_exp > 0:
            neg_sim = (neg_end * v[:,:,-1:,:]).sum(dim=-1, keepdim=True) / (neg_end.norm(dim=-1, keepdim=True) * v[:,:,-1:,:].norm(dim=-1, keepdim=True))
            neg_sim_scale = (1 + F.relu(neg_sim)) ** self.neg_sim_exp

        v[:,:,-1:,:] = v[:,:,-1:,:] - norm_scale * neg_sim_scale * delta  # 各项均为 batch, head, length, dim, 所以可以画热度图

        if self.renorm:
            new_v_norm = v[:,:,-1:,:].norm(dim=(1,3), keepdim=True)
            v[:,:,-1:,:] = v[:,:,-1:,:] * (v_norm / new_v_norm)
        return v


@InnerDetoxHook.register_module()
class LayerAblationInnerDetoxHook(BaseInnerDetoxHook):
    def __init__(self, norm_exp=0, neg_sim_exp=0, renorm=False,
                 ablation_layers=[]):
        super().__init__(norm_exp, neg_sim_exp, renorm)
        self.ablation_layers = ablation_layers

    def module_match_fn(self, module_name):
        layer_idxs = module_name.split('.')
        if len(layer_idxs) < 3:
            return False
        layer_idx = layer_idxs[-3]
        if not layer_idx.isdigit():
            return False
        return module_name.endswith(f'.before_mergehead') and (int(layer_idx) not in self.ablation_layers)