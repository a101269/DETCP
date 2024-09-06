#CONFIG=configs/detcp/detcp-gpt2-l-ne0.4-nse0.6-renorm_np0-pp0_rtp-test-nontoxic-8k.py
CONFIG=configs/replace/replace-gpt2-l-ne0.4-nse0.6-renorm_np0-pp0_rtp-test-toxic-2k.py
#CONFIG=configs/dexperts/dexperts-gpt2-l_rtp-test-toxic-2k.py

echo "run_generation"
CUDA_VISIBLE_DEVICES=6 python scripts/run_generation.py --config  $CONFIG --part 2  --lama 3
sleep 2
echo "run_evaluation：ppl"
CUDA_VISIBLE_DEVICES=6 python scripts/run_evaluation.py --config $CONFIG --eval_type ppl  --part 2
sleep 2
echo "run_evaluation：toxicity"
CUDA_VISIBLE_DEVICES=6 python scripts/run_evaluation.py --config $CONFIG --eval_type toxicity  --part 2
sleep 2
echo "merge_evaluations"
CUDA_VISIBLE_DEVICES=6 python scripts/merge_evaluations.py --config $CONFIG  --part 2


CONFIG=configs/replace/replace-gpt2-l-ne0.4-nse0.6-renorm_np0-pp0_rtp-test-nontoxic-8k.py
#CONFIG=configs/detcp/detcp-gpt2-l-ne0.4-nse0.6-renorm_np0-pp0_rtp-test-toxic-2k.py
#CONFIG=configs/dexperts/dexperts-gpt2-l_rtp-test-toxic-2k.py

echo "run_generation"
CUDA_VISIBLE_DEVICES=6 python scripts/run_generation.py --config  $CONFIG --part 2  --lama 5
sleep 2
echo "run_evaluation：ppl"
CUDA_VISIBLE_DEVICES=6 python scripts/run_evaluation.py --config $CONFIG --eval_type ppl  --part 2
sleep 2
echo "run_evaluation：toxicity"
CUDA_VISIBLE_DEVICES=6 python scripts/run_evaluation.py --config $CONFIG --eval_type toxicity  --part 2
sleep 2
echo "merge_evaluations"
CUDA_VISIBLE_DEVICES=6 python scripts/merge_evaluations.py --config $CONFIG  --part 2
