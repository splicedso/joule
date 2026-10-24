"""A physical model of decode energy, fitted and validated on the format sweep.

First attempt (kept in the note): board energy = P_static * t + e_byte * bytes, both fitted.
It returned P_static = 110 W and a negative cost per byte: impossible. Decode is memory
bound, so time per token and bytes per token rise together, and least squares cannot tell
the two terms apart. The fix is to measure what can be measured instead of fitting it.

    board energy per token - P_idle * t = e_byte * bytes + e_tok

P_idle is the idle board power measured before each sweep. Every format holds the same
1.5 billion weights, so the arithmetic per token is roughly the same for all of them and
enters as a constant e_tok. Checked by leave-one-out: fit on seven formats, predict the eighth.
"""

import json
import sys

import numpy as np

P_IDLE = np.mean([json.load(open(f))["idle_w"]["sys"]
                  for f in ("results/quant-energy-1.5b.json", "results/quant-energy-1.5b-run2.json")])
rows = json.load(open("results/roofline-1.5b.json"))["rows"]
t = np.array([1 / r["tok_s"] for r in rows])
b = np.array([r["gb_per_token"] for r in rows])
y = np.array([r["board_mj"] / 1e3 for r in rows])
X = np.column_stack([b, np.ones_like(b)])
target = y - P_IDLE * t


def fit(X, z):
    return np.linalg.lstsq(X, z, rcond=None)[0]


coef = fit(X, target)
pred = X @ coef + P_IDLE * t
loo = np.array([X[i] @ fit(np.delete(X, i, 0), np.delete(target, i)) + P_IDLE * t[i] for i in range(len(y))])
r2 = 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
mape = float(np.mean(np.abs(loo - y) / y))
print(f"P_idle = {P_IDLE:.2f} W (measured), e_byte = {coef[0]:.3f} nJ/byte, e_tok = {coef[1] * 1e3:.1f} mJ, R^2 = {r2:.3f}")
print(f"{'format':7} {'measured':>8} {'fit':>6} {'held-out':>8} {'error':>6}")
for r, m, p, l in zip(rows, y, pred, loo):
    print(f"{r['format']:7} {m * 1e3:8.1f} {p * 1e3:6.1f} {l * 1e3:8.1f} {100 * (l - m) / m:+5.1f}%")
print(f"leave-one-out mean absolute error: {mape:.1%}")
json.dump({"p_idle_w": P_IDLE, "e_byte_nj": coef[0], "e_tok_mj": coef[1] * 1e3, "r2": r2, "loo_mape": mape,
           "rows": [{"format": r["format"], "measured_mj": m * 1e3, "fit_mj": p * 1e3, "loo_mj": l * 1e3}
                    for r, m, p, l in zip(rows, y, pred, loo)]}, open(sys.argv[1], "w"), indent=2)
