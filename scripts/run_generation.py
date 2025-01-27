import argparse
import os.path as osp
import pickle as pkl
import sys
from functools import partial

sys.path.append(osp.dirname(osp.dirname(osp.abspath(__file__))))

import jsonlines as jsl
import torch
from mmengine import Config
from tqdm import tqdm
from transformers import AutoTokenizer, GenerationConfig, set_seed#, GPT2LMHeadModel
from utils import batchify, repeat_interleave
from models.gpt2.innerdetox_hook import InnerDetoxHook
from models.gpt2.modeling_gpt2_dexperts import GPT2LMHeadModelDExperts
from models.gpt2.modeling_gpt2_gedi import GPT2LMHeadModelGeDi
from models.gpt2.modeling_gpt2_innerdetox import GPT2LMHeadModelInnerdetox
from models.gpt2.modeling_gpt2_detcp import GPT2LMHeadModelDetcp
from models.gpt2.modeling_gpt2 import GPT2LMHeadModel
from models.llama.llama_modeling_detcp import LlamaForCausalLM
# from transformers import LlamaForCausalLM

def run_dexperts(config, prompts):
    tokenizer = AutoTokenizer.from_pretrained(config.model_path)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = 'left'

    model = GPT2LMHeadModelDExperts.from_pretrained(config.model_path)
    model.add_module('antiexpert', GPT2LMHeadModel.from_pretrained(config.antiexpert_model))
    model.add_module('expert', GPT2LMHeadModel.from_pretrained(config.expert_model))
    model.config.pad_token_id = model.config.eos_token_id
    model.generation_config.pad_token_id = model.config.eos_token_id
    model.to('cuda')
    model.eval()

    config.generation_config['eos_token_id'] = model.config.eos_token_id

    generations = []
    pbar = tqdm(batchify(prompts, config.batch_size),
                total=len(prompts) // config.batch_size + (len(prompts) % config.batch_size != 0))
    for prompt in pbar:
        inputs = tokenizer(prompt, padding=True, return_tensors='pt')
        inputs = {k: v.to('cuda') for k, v in inputs.items()}

        generation = model.generate(
            **inputs,
            dexperts_alpha=config.dexperts_alpha,
            generation_config=GenerationConfig(**config.generation_config),
            pad_token_id=tokenizer.eos_token_id,
        )
        prompt_len = inputs['input_ids'].shape[1]
        generation = tokenizer.batch_decode(
            generation[:, prompt_len:], skip_special_tokens=True
        )
        generations.extend(generation)
        pbar.update(len(prompt))
    pbar.close()
    return generations


def run_innerdetox(config, prompts):
    tokenizer = AutoTokenizer.from_pretrained(config.model_path,trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = 'left'

    model = GPT2LMHeadModelInnerdetox.from_pretrained(config.model_path,trust_remote_code=True)
    model.config.pad_token_id = model.config.eos_token_id
    model.generation_config.pad_token_id = model.config.eos_token_id
    model.to('cuda')
    model.eval()

    neg_prompt = config.neg_prompts[config.neg_prompt_idx]
    pos_prompt_idx = config.get('pos_prompt_idx', None)
    pos_prompt = (
        config.pos_prompts[pos_prompt_idx] if pos_prompt_idx is not None else ""
    )

    config.generation_config['eos_token_id'] = model.config.eos_token_id

    innerdetox_hook = InnerDetoxHook.build(config.innerdetox_hook)  # 模块成功注册后，我们可以通过配置文件使用这个激活模块。 type='BaseInnerDetoxHook',
    innerdetox_inputs = dict(
        neg_input_ids=None,
        neg_attention_mask=None,
        innerdetox_hook=innerdetox_hook,
    )

    generations = []
    i = 0
    pbar = tqdm(batchify(prompts, config.batch_size), total=len(prompts)//config.batch_size + (len(prompts) % config.batch_size != 0))
    for prompt in pbar:
        prompt_w_prefix = [pos_prompt + p for p in prompt] + [
            neg_prompt + p for p in prompt
        ]

        neg_inputs = tokenizer(prompt_w_prefix, padding=True, return_tensors='pt')
        innerdetox_inputs['neg_input_ids'] = neg_inputs['input_ids'].to('cuda')
        innerdetox_inputs['neg_attention_mask'] = neg_inputs['attention_mask'].to(
            'cuda'
        )

        colon_id = tokenizer(neg_prompt.strip())['input_ids'][-1]
        prompt_end_indices = torch.argmax(
            (neg_inputs['input_ids'] == colon_id).long(), dim=1
        )

        old_read_hook = partial(innerdetox_hook.read_hook)
        innerdetox_hook.read_hook = partial(
            innerdetox_hook.read_hook, prompt_end_indices=prompt_end_indices
        )

        inputs = tokenizer(prompt, padding=True, return_tensors='pt')
        inputs = {k: v.to('cuda') for k, v in inputs.items()}

        generation = model.generate(
            **inputs,
            generation_config=GenerationConfig(**config.generation_config),
            pad_token_id=tokenizer.eos_token_id,
            innerdetox_inputs=innerdetox_inputs,
        )

        innerdetox_hook.read_hook = old_read_hook

        prompt_len = inputs['input_ids'].shape[1]
        generation = tokenizer.batch_decode(
            generation[:, prompt_len:], skip_special_tokens=True
        )
        generations.extend(generation)
        pbar.update(len(prompt))
        i += len(prompt)

    return generations

def run_detcp(config, prompts,lama=None):
    print("lama==========",lama)
    tokenizer = AutoTokenizer.from_pretrained(config.model_path,trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = 'left' # 左边开始填充(默认是右边)，因为最右边标记的logits将用于预测未来的标记。

    model = GPT2LMHeadModelDetcp.from_pretrained(config.model_path,trust_remote_code=True)
    model.config.pad_token_id = model.config.eos_token_id
    model.generation_config.pad_token_id = model.config.eos_token_id
    model.to('cuda')
    model.eval()

    neg_prompt = config.neg_prompts[config.neg_prompt_idx]
    pos_prompt_idx = config.get('pos_prompt_idx', 0)
    pos_prompt = config.pos_prompts[pos_prompt_idx]

    config.generation_config['eos_token_id'] = model.config.eos_token_id
    innerdetox_inputs = dict(
        neg_input_ids=None,
        neg_attention_mask=None,
        lama=lama
    )
    generations = []
    i = 0
    pbar = tqdm(batchify(prompts, config.batch_size), total=len(prompts))
    for prompt in pbar:
        # prompt_w_prefix = [pos_prompt+p for p in prompt] + [neg_prompt+p for p in prompt]
        prompt_w_prefix = [pos_prompt for p in prompt] + [
            neg_prompt for p in prompt
        ]

        neg_inputs = tokenizer(prompt_w_prefix, padding=True, return_tensors='pt') # 左边开始填充(默认是右边)，因为最右边标记的logits将用于预测未来的标记。
        innerdetox_inputs['neg_input_ids'] = neg_inputs['input_ids'].to('cuda')
        innerdetox_inputs['neg_attention_mask'] = neg_inputs['attention_mask'].to(
            'cuda'
        )
        """
        pos+p
        neg+p
        p
        pos+p+t
        neg+p+t
        p+t
        """
        inputs = tokenizer(prompt , padding=True, return_tensors='pt')  # 正负、ori都从左开始填充，后面无法拼接
        inputs = {k: v.to('cuda') for k, v in inputs.items()}

        generation = model.generate(
            **inputs,
            generation_config=GenerationConfig(**config.generation_config),
            pad_token_id=tokenizer.eos_token_id,
            innerdetox_inputs=innerdetox_inputs,
        )


        prompt_len = inputs['input_ids'].shape[1]
        generation = tokenizer.batch_decode(
            generation[:, prompt_len:], skip_special_tokens=True
        )
        generations.extend(generation)
        pbar.update(len(prompt))
        i += len(prompt)

    return generations

def run_llama(config, prompts,lama=2):
    tokenizer = AutoTokenizer.from_pretrained(config.model_path,trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = 'left' # 左边开始填充(默认是右边)，因为最右边标记的logits将用于预测未来的标记。

    model = LlamaForCausalLM.from_pretrained(config.model_path,trust_remote_code=True)
    model.config.pad_token_id = model.config.eos_token_id
    model.generation_config.pad_token_id = model.config.eos_token_id
    model.to('cuda')
    model.eval()

    neg_prompt = config.neg_prompts[config.neg_prompt_idx]
    pos_prompt_idx = config.get('pos_prompt_idx', None)
    pos_prompt = (
        config.pos_prompts[pos_prompt_idx] if pos_prompt_idx is not None else ""
    )

    config.generation_config['eos_token_id'] = model.config.eos_token_id
    innerdetox_inputs = dict(
        neg_input_ids=None,
        neg_attention_mask=None,
        lama=lama
    )
    generations = []
    i = 0
    pbar = tqdm(batchify(prompts, config.batch_size), total=len(prompts))
    for prompt in pbar:
        prompt_w_prefix = [pos_prompt for p in prompt] + [
            neg_prompt for p in prompt
        ]
        neg_inputs = tokenizer(prompt_w_prefix, padding=True, return_tensors='pt') # 左边开始填充(默认是右边)，因为最右边标记的logits将用于预测未来的标记。
        innerdetox_inputs['neg_input_ids'] = neg_inputs['input_ids'].to('cuda')
        innerdetox_inputs['neg_attention_mask'] = neg_inputs['attention_mask'].to(
            'cuda'
        )

        inputs = tokenizer(prompt , padding=True, return_tensors='pt')  # 正负、ori都从左开始填充，后面无法拼接
        inputs = {k: v.to('cuda') for k, v in inputs.items()}

        generation = model.generate(
            **inputs,
            generation_config=GenerationConfig(**config.generation_config),
            pad_token_id=tokenizer.eos_token_id,
            innerdetox_inputs=innerdetox_inputs,
        )


        prompt_len = inputs['input_ids'].shape[1]
        generation = tokenizer.batch_decode(
            generation[:, prompt_len:], skip_special_tokens=True
        )
        generations.extend(generation)
        pbar.update(len(prompt))
        i += len(prompt)

    return generations

# def run_llama(config, prompts):
#     tokenizer = AutoTokenizer.from_pretrained(config.model_path)
#     tokenizer.pad_token = tokenizer.eos_token
#     tokenizer.padding_side = 'left'
#
#     model = LlamaForCausalLM.from_pretrained(config.model_path)
#     model.config.pad_token_id = model.config.eos_token_id
#     model.generation_config.pad_token_id = model.config.eos_token_id
#     model.to('cuda')
#     model.eval()
#
#     config.generation_config['eos_token_id'] = model.config.eos_token_id
#
#     prompt_prefix = config.get('prompt_prefix', '')
#
#     generations = []
#     pbar = tqdm(batchify(prompts, config.batch_size),
#                 total=len(prompts) // config.batch_size + (len(prompts) % config.batch_size != 0)) # 3042 len(prompts)=3042*64
#     for prompt in pbar:
#         prompt = [prompt_prefix + p for p in prompt]
#         inputs = tokenizer(prompt, return_tensors='pt', padding=True)
#         inputs = {k: v.to('cuda') for k, v in inputs.items()}
#
#         generation = model.generate(
#             **inputs,
#             generation_config=GenerationConfig(**config.generation_config),
#             pad_token_id=tokenizer.eos_token_id,
#         )
#
#         prompt_len = inputs['input_ids'].shape[1]
#         generation = tokenizer.batch_decode(
#             generation[:, prompt_len:], skip_special_tokens=True
#         )
#
#         generations.extend(generation)
#         pbar.update(len(prompt))
#     return generations

def run_gpt2(config, prompts):
    tokenizer = AutoTokenizer.from_pretrained(config.model_path)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = 'left'

    model = GPT2LMHeadModel.from_pretrained(config.model_path)
    model.config.pad_token_id = model.config.eos_token_id
    model.generation_config.pad_token_id = model.config.eos_token_id
    model.to('cuda')
    model.eval()

    config.generation_config['eos_token_id'] = model.config.eos_token_id

    prompt_prefix = config.get('prompt_prefix', '')
    prompt_prefix = config.pos_prompts[0]

    generations = []
    pbar = tqdm(batchify(prompts, config.batch_size),
                total=len(prompts) // config.batch_size + (len(prompts) % config.batch_size != 0)) # 3042 len(prompts)=3042*64
    for prompt in pbar:
        prompt = [prompt_prefix + p for p in prompt]
        print( prompt)
        inputs = tokenizer(prompt, return_tensors='pt', padding=True)
        inputs = {k: v.to('cuda') for k, v in inputs.items()}

        generation = model.generate(
            **inputs,
            generation_config=GenerationConfig(**config.generation_config),
            pad_token_id=tokenizer.eos_token_id,
        )

        prompt_len = inputs['input_ids'].shape[1]
        generation = tokenizer.batch_decode(
            generation[:, prompt_len:], skip_special_tokens=True
        )

        generations.extend(generation)
        pbar.update(len(prompt))
    return generations


def run_gedi(config, prompts):
    tokenizer = AutoTokenizer.from_pretrained(config.model_path)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = 'left'

    model = GPT2LMHeadModelGeDi.from_pretrained(config.model_path)
    model.add_module(
        'gedi_model', GPT2LMHeadModel.from_pretrained(config.gedi_model_path)
    )
    model.config.pad_token_id = model.config.eos_token_id
    model.generation_config.pad_token_id = model.config.eos_token_id
    model.to('cuda')
    model.eval()

    config.generation_config['eos_token_id'] = model.config.eos_token_id

    desired_code = 'clean'
    undesired_code = 'dirty'

    disc_weight = config.disc_weight

    generations = []
    pbar = tqdm(batchify(prompts, config.batch_size), total=len(prompts)//config.batch_size + (len(prompts) % config.batch_size != 0))
    for prompt in pbar:
        inputs = tokenizer(prompt, return_tensors='pt', padding=True)
        inputs = {k: v.to('cuda') for k, v in inputs.items()}

        gedi_inputs = tokenizer(
            [desired_code] * len(prompt) + [undesired_code] * len(prompt),
            text_pair=prompt * 2,
            return_tensors='pt',
            padding=True,
        )
        gedi_inputs = {k: v.to('cuda') for k, v in gedi_inputs.items()}

        generation = model.generate(
            **inputs,
            generation_config=GenerationConfig(**config.generation_config),
            pad_token_id=tokenizer.eos_token_id,
            gedi_inputs=gedi_inputs,
            disc_weight=disc_weight,
        )

        prompt_len = inputs['input_ids'].shape[1]
        generation = tokenizer.batch_decode(
            generation[:, prompt_len:], skip_special_tokens=True
        )

        generations.extend(generation)
        pbar.update(len(prompt))
    return generations


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--part", type=str, required=True)
    parser.add_argument("--lama", type=int, default=None)
    args = parser.parse_args()

    config = Config.fromfile(args.config)
    set_seed(config.seed)
    part = args.part
    fn = ".".join(osp.basename(args.config).split('.')[:-1])
    output_fp = f'results{part}/{fn}.jsonl'

    print(f'Running generation on {args.config} ...')

    data = jsl.open(config.prompts_file)
    prompts = [d['prompt']['text'] for d in data]

    if config.model_type == 'dexperts':
        gen_fn = run_dexperts
    elif config.model_type == 'innerdetox': # 无需训练
        gen_fn = run_innerdetox
    elif config.model_type == 'gpt2':
        gen_fn = run_gpt2
    elif config.model_type == 'gedi':
        gen_fn = run_gedi
    elif config.model_type == 'detcp':
        gen_fn = run_detcp
    elif config.model_type == 'llama':
        gen_fn = run_llama
    else:
        raise NotImplementedError
    print('genfn:',gen_fn)


    # generations = gen_fn(config, list(repeat_interleave(prompts, config.num_k_samples)))
    generations = gen_fn(config, list(repeat_interleave(prompts, config.num_k_samples)), lama=args.lama)

    result = []
    for i in range(len(prompts)):
        result.append(
            dict(
                prompt=dict(text=prompts[i]),
                continuations=[
                    dict(text=g)
                    for g in generations[
                        i * config.num_k_samples : (i + 1) * config.num_k_samples  # 25个一组
                    ]
                ],
            )
        )
    jsl.Writer(open(output_fp, 'w', encoding='utf-8')).write_all(result)
