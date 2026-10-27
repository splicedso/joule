#!/bin/sh
# Checkpoint test for qat.py: a 4-step run that dies right after its step-2 checkpoint and is started again must end with
# exactly the weights and log of an uninterrupted 4-step run. CPU, the stock 0.5B, tiny batches: no GPU needed.
#   sh experiments/lattice/test_checkpoint.sh      (about 5 minutes)
set -eu
cd "$(dirname "$0")/../.."
export DEVICE=cpu QUANT=0 DATA=data/rft/rft-1.5b.jsonl STEPS=4 BATCH=2 SEQ=128 GENERAL_FRAC=0.5 EVAL_EVERY=4 CKPT_EVERY=2
PY=.venv-torch/bin/python; SRC=models/hf-0.5b; T=models/ckpt-test
rm -rf "$T"; mkdir -p "$T"
echo "=== A: uninterrupted $(date)"; nice $PY experiments/lattice/qat.py $SRC $T/a
echo "=== B1: dies after the step-2 checkpoint $(date)"
set +e; STOP_AFTER=2 nice $PY experiments/lattice/qat.py $SRC $T/b; rc=$?; set -e
[ "$rc" -eq 3 ] || { echo "B1 exited $rc, expected 3"; exit 1; }
[ -f $T/b/checkpoint/latest.pt ] || { echo "no checkpoint written"; exit 1; }
echo "=== B2: started again, must resume $(date)"; nice $PY experiments/lattice/qat.py $SRC $T/b | tee $T/b2.log
grep -q 'resumed from the checkpoint at step 2' $T/b2.log || { echo "did not resume"; exit 1; }
[ ! -e $T/b/checkpoint ] || { echo "checkpoint left behind after the final save"; exit 1; }
cmp $T/a/model.safetensors $T/b/model.safetensors || { echo "weights differ"; $PY -c "
from safetensors.torch import load_file; a=load_file('$T/a/model.safetensors'); b=load_file('$T/b/model.safetensors')
print('max abs diff', max((a[k].float()-b[k].float()).abs().max().item() for k in a))"; exit 1; }
$PY -c "
import json; a=json.load(open('$T/a/train_log.json')); b=json.load(open('$T/b/train_log.json'))
assert a['log']==b['log'], (a['log'], b['log']); assert b['resumed_from']==3 and a['resumed_from'] is None
print('weights byte-identical, logs identical, resumed_from', b['resumed_from'])"
echo "=== CHECKPOINT TEST PASSED $(date)"
