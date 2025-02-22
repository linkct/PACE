#!/bin/bash
python train_.py --env-name KuhnPoker \
  --algo ppo --num-steps 1000 --num-processes 80 --use-gae --eps 1e-8 \
  --lr 2e-4 --entropy-coef 5e-4 --value-loss-coef 0.5 --num-epochs 15 --num-mini-batch 12 --gamma 0.99 --gae-lambda 0.95 \
  --max-grad-norm 2.0 \
  --num-env-steps 5000000 \
  --save-interval 1000000 --log-interval 10000 --eval-interval 100000 --eval-episodes 100 \
  --exp-name "pace" \
  --wandb-comment "100 episodes of context" \
  --latent-training --e2e-obj \
  --deterministic-latent \
  --use-latent-critic \
  --pre-hidden-dims 64 64 --encoder-base mlp --agg-func mean --post-hidden-dims 64 \
  --latent-dim 64 --kl-coef 0 \
  --hidden-dims 128 128 --act-func relu \
  --train-pool-size 40 --eval-pool-size 10 \
  --rule-based-opponents 40 \
  --auxiliary-policy-cls-coef 1.0 \
  --policy-cls-reward-coef 0.1 --policy-cls-reward-type accuracy --policy-cls-reward-mode full --policy-cls-warmup-steps 10000 \
  --policy-cls-reward-decay-steps 4000000 \
  --use-dummy-vec-env \
  --self-obs-mode \
  --use-meta-episode \
  --history-size 100 \
  --history-full-size 100 \
  --history-use-episodes \
  --include-current-episode \
  --merge-encoder-computation \
  --clear-history-on-full \
  --separate-history \
  --seed $1 \
  --wandb-user-name <wandb_user_name>
