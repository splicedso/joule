"""Turn a benchmark run and the power samples around it into joules per token.

llama-bench prints only when it finishes, and its timed repetitions are the
last thing it does, so the compute window is [end - compute_s, end]. The first
quarter of that window is dropped: the sys reading lags by about a second and
the clocks are still ramping.
"""

import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from . import llamacpp
from .power import Sampler, mean_power

TRIM = 0.25
MIN_STEADY_S = 4.0


@dataclass(frozen=True)
class Result:
    model: str
    model_type: str
    phase: str
    tokens: int
    tokens_per_s: float
    soc_w: float
    sys_w: float
    soc_j_per_tok: float
    sys_j_per_tok: float
    soc_net_j_per_tok: float
    sys_net_j_per_tok: float
    steady_s: float
    samples: int
    reps: int
    build: str

    def as_dict(self) -> dict:
        return asdict(self)


def energy(power_w: float, idle_w: float, tokens_per_s: float) -> tuple[float, float]:
    return power_w / tokens_per_s, max(power_w - idle_w, 0.0) / tokens_per_s


def reps_for(target_s: float, per_rep_s: float) -> int:
    return max(3, math.ceil(target_s / per_rep_s))


def measure(sampler: Sampler, idle: tuple[float, float], model: str, phase: str,
            tokens: int, target_s: float, extra: list[str]) -> Result:
    probe = llamacpp.run_phase(model, phase, tokens, 3, extra)
    reps = reps_for(target_s, probe.compute_s / 3)
    run = llamacpp.run_phase(model, phase, tokens, reps, extra)
    end = time.monotonic()
    start = end - run.compute_s * (1 - TRIM)
    if end - start < MIN_STEADY_S:
        raise ValueError(
            f"{phase} steady window was {end - start:.1f}s, under {MIN_STEADY_S}s; raise --seconds")
    window = sampler.window(start, end)
    soc_w, sys_w = mean_power(window)
    soc_j, soc_net = energy(soc_w, idle[0], run.tokens_per_s)
    sys_j, sys_net = energy(sys_w, idle[1], run.tokens_per_s)
    return Result(
        model=Path(model).name, model_type=run.model_type, phase=phase,
        tokens=tokens, tokens_per_s=run.tokens_per_s, soc_w=soc_w, sys_w=sys_w,
        soc_j_per_tok=soc_j, sys_j_per_tok=sys_j,
        soc_net_j_per_tok=soc_net, sys_net_j_per_tok=sys_net,
        steady_s=end - start, samples=len(window), reps=reps, build=run.build,
    )
