#!/bin/bash
conda create -n pace python=3.8 setuptools=65.6.3
conda activate pace
conda install pytorch==1.12.1 torchvision==0.13.1 
conda install torchaudio==0.12.1 cudatoolkit=11.3  -c pytorch
conda install scikit-learn==1.0.2 -c conda-forge
pip install pip==23.0.1
pip install wheel==0.38.4 PettingZoo==1.9.0 pygame==2.0.1 wandb==0.14.0 tqdm==4.65.0 stable-baselines3==1.7.0 seaborn==0.13.0 pyglet==1.5.27
cd environment/overcooked/gym_cooking/rebar
pip install -e .
cd ../..
pip install -e .
cd ../..
