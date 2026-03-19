#!/bin/bash
source /home/zy/anaconda3/etc/profile.d/conda.sh
conda activate rxn_front
export PATH="/home/zy/anaconda3/envs/rxn_front/bin:$PATH"
cd /home/zy/zhangyi/rxncommons/frontend
npm run dev
