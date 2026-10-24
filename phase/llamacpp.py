"""Run one llama-bench phase and return its throughput and compute time."""

import json
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class BenchRun:
    tokens_per_s: float
    compute_s: float
    build: str
    model_type: str


def run_phase(model: str, phase: str, tokens: int, reps: int, extra: list[str]) -> BenchRun:
    n_prompt, n_gen = (tokens, 0) if phase == "prefill" else (0, tokens)
    cmd = ["llama-bench", "-m", model, "-p", str(n_prompt), "-n", str(n_gen),
           "-r", str(reps), "-o", "json", *extra]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    return parse(out)


def parse(stdout: str) -> BenchRun:
    rows = json.loads(stdout)
    if len(rows) != 1:
        raise ValueError(f"expected one llama-bench test, got {len(rows)}")
    row = rows[0]
    return BenchRun(
        tokens_per_s=row["avg_ts"],
        compute_s=sum(row["samples_ns"]) / 1e9,
        build=f"{row['build_commit']} ({row['build_number']})",
        model_type=row["model_type"],
    )
