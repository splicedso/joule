"""Token streams for Kinetic: FineWeb-Edu (ODC-BY), tokenized with Qwen2.5's tokenizer.

Streams the sample-10BT subset and writes flat uint32 files: the first VALID tokens to
valid.bin, the next TRAIN tokens to train.bin, documents separated by the end-of-text token.
Every shape trains on the same file in the same order.

    python experiments/kinetic/prepare.py data/kinetic [TRAIN_TOKENS]
"""

import os
import sys
from pathlib import Path

import numpy as np
from datasets import load_dataset
from transformers import AutoTokenizer

VALID = 10_000_000


def main():
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    train_tokens = int(float(sys.argv[2])) if len(sys.argv) > 2 else 1_000_000_000
    tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B")
    eos = tok.convert_tokens_to_ids("<|endoftext|>")
    stream = load_dataset("HuggingFaceFW/fineweb-edu", "sample-10BT", split="train", streaming=True)
    files = {"valid": open(out / "valid.bin", "wb"), "train": open(out / "train.bin", "wb")}
    written = {"valid": 0, "train": 0}
    target = {"valid": VALID, "train": train_tokens}
    buf = []
    for doc in stream:
        buf.extend(tok(doc["text"])["input_ids"] + [eos])
        if len(buf) < 1_000_000:
            continue
        part = "valid" if written["valid"] < VALID else "train"
        take = min(len(buf), target[part] - written[part])
        np.asarray(buf[:take], dtype=np.uint32).tofile(files[part])
        written[part] += take; buf = buf[take:]
        print(f"valid {written['valid'] / 1e6:.0f}M  train {written['train'] / 1e6:.0f}M", flush=True)
        if written["train"] >= train_tokens:
            break
    for f in files.values():
        f.close()
    # The streaming dataset's download thread aborts the interpreter at exit
    # (PyGILState_Release during finalizing: exit code 134, after every token is on disk).
    # The files are closed, so leave without running finalizers.
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
