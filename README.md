# DETCP
Code for the paper "DETCP: SELF-DETOXIFYING LANGUAGE MODELS WITH CONTRASTIVE PAIRS"


### Environment
```
pip3 install -r requirements.txt
```
## Run
1. Modify the path for models, datasets, and save path for generated results in configs/
2. Get the generation texts:
```
python scripts/run_generation.py --config configs/dectp/detcp-gpt2-l-ne0.4-nse0.6-renorm_np0-pp0_rtp-test-toxic-2k.py --lama 2
```
## Evaluate:
```
python scripts/run_evaluation.py --config configs/dectp/detcp-gpt2-l-ne0.4-nse0.6-renorm_np0-pp0_rtp-test-toxic-2k.py --eval_type ppl  

python scripts/run_evaluation.py --config configs/dectp/detcp-gpt2-l-ne0.4-nse0.6-renorm_np0-pp0_rtp-test-toxic-2k.py --eval_type toxicity

python scripts/merge_evaluations.py --config --config configs/dectp/detcp-gpt2-l-ne0.4-nse0.6-renorm_np0-pp0_rtp-test-toxic-2k.py

```

