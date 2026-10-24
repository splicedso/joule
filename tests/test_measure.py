import json

import pytest

from joule.llamacpp import parse
from joule.measure import energy
from joule.power import Sample, mean_power


def test_parse_reads_throughput_and_compute_time():
    out = json.dumps([{"avg_ts": 100.0, "samples_ns": [1_000_000_000, 2_000_000_000],
                       "build_commit": "abc", "build_number": 7, "model_type": "qwen2 1B Q4_K"}])
    run = parse(out)
    assert run.tokens_per_s == 100.0
    assert run.compute_s == 3.0
    assert run.build == "abc (7)"


def test_parse_refuses_more_than_one_test():
    with pytest.raises(ValueError):
        parse(json.dumps([{}, {}]))


def test_energy_is_watts_over_throughput_and_net_subtracts_idle():
    gross, net = energy(20.0, 5.0, 100.0)
    assert gross == pytest.approx(0.2)
    assert net == pytest.approx(0.15)


def test_net_energy_never_goes_negative():
    assert energy(3.0, 5.0, 10.0)[1] == 0.0


def test_mean_power_refuses_an_empty_window():
    with pytest.raises(ValueError):
        mean_power([])
    assert mean_power([Sample(0, 2, 10), Sample(1, 4, 12)]) == (3, 11)
