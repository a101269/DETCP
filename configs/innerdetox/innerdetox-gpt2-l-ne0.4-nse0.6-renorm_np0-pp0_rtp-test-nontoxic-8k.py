_base_ = [
    '../_base_/models/innerdetox/detcp-gpt2-l.py',
    '../_base_/datasets/rtp-test-nontoxic-8k.py',
    '../_base_/common.py',
]

neg_prompt_idx = 0  # np
pos_prompt_idx = 0  # pp


innerdetox_hook = dict(
    type='BaseInnerDetoxHook',
    norm_exp=0.4, #ne
    neg_sim_exp=0.6, #nse
    renorm=True,
)
