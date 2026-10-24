"""Fine-tune Qwen2.5 0.5B Instruct to imitate Qwen2.5 7B: the Spliced drafter.

Every training example is a user prompt and the 7B model's own greedy answer. The prompt is
masked out of the loss, so the model learns only to reproduce the 7B's answers. Full
fine-tune with MLX (a 0.5B model fits easily in 24 GB), 5% of examples held back for
validation loss.

    python experiments/drafter/train.py results/drafter/train-answers.jsonl models/drafter-0.5b
"""

import json
import random
import subprocess
import sys
from pathlib import Path

BASE = "models/hf-0.5b"


def main():
    answers, out = Path(sys.argv[1]), Path(sys.argv[2])
    rows = [json.loads(l) for l in answers.read_text().splitlines()]
    rows = [r for r in rows if r["answer"].strip()]
    random.seed(3)
    random.shuffle(rows)
    n_valid = max(50, len(rows) // 20)
    data = out.parent / (out.name + "-data")
    data.mkdir(parents=True, exist_ok=True)
    for name, part in (("valid", rows[:n_valid]), ("train", rows[n_valid:])):
        with open(data / f"{name}.jsonl", "w") as f:
            for r in part:
                f.write(json.dumps({"messages": [{"role": "user", "content": r["prompt"]},
                                                 {"role": "assistant", "content": r["answer"]}]}) + "\n")
    n_train = len(rows) - n_valid
    batch = 8
    iters = 2 * n_train // batch  # two epochs
    print(f"{n_train} train, {n_valid} valid, {iters} iterations", flush=True)
    subprocess.run([sys.executable, "-m", "mlx_lm", "lora", "--model", BASE, "--train", "--data", str(data),
                    "--fine-tune-type", "full", "--mask-prompt", "--batch-size", str(batch), "--iters", str(iters),
                    "--learning-rate", "1e-5", "--optimizer", "adamw", "--max-seq-length", "1536",
                    "--steps-per-eval", "200", "--val-batches", "20", "--save-every", "400",
                    "--grad-checkpoint", "--adapter-path", str(out)], check=True)


if __name__ == "__main__":
    main()
