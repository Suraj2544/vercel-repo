from pathlib import Path

from api.latency import LatencyRequest, compute_metrics, load_samples


def test_compute_metrics_threshold_counts():
    samples = load_samples()
    metrics = compute_metrics(samples, threshold=162)

    apac = metrics["apac"]
    amer = metrics["amer"]

    assert apac.avg_latency is not None
    assert amer.avg_latency is not None

    assert apac.breaches == sum(sample.latency_ms > 162 for sample in samples if sample.region.lower() == "apac")
    assert amer.breaches == sum(sample.latency_ms > 162 for sample in samples if sample.region.lower() == "amer")


def test_request_validation():
    request = LatencyRequest(regions=["apac", "amer"], threshold_ms=162)
    assert request.threshold_ms == 162
    assert request.regions == ["apac", "amer"]


if __name__ == "__main__":
    # simple smoke test when running the module directly
    samples = load_samples()
    metrics = compute_metrics(samples, threshold=162)
    print(metrics["apac"])
    print(metrics["amer"])
