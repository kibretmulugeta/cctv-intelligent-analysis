"""
Prometheus MLOps Observability & Metrics Exporter.
Tracks p95/p99 inference latency, system memory usage, and detection confidence drift.
"""
import time
import psutil
from prometheus_client import Histogram, Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

# MLOps Metrics Definitions
INFERENCE_LATENCY = Histogram(
    "cctv_inference_latency_seconds",
    "Time spent in AI object detection & tracking inference per frame",
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

CONFIDENCE_DRIFT = Histogram(
    "cctv_detection_confidence_score",
    "Object detection confidence score distribution to monitor drift",
    buckets=[0.1, 0.3, 0.45, 0.6, 0.75, 0.9, 0.99],
)

ACTIVE_JOBS = Gauge("cctv_active_processing_jobs", "Current number of active Celery/Background video tasks")

CPU_MEMORY_USAGE = Gauge("cctv_cpu_memory_usage_bytes", "CPU RAM usage of backend process")
CPU_PERCENT = Gauge("cctv_cpu_utilization_percent", "CPU utilization percentage")

TOTAL_FRAMES_PROCESSED = Counter("cctv_total_frames_processed", "Total video frames processed by AI pipeline")
TOTAL_EVENTS_DETECTED = Counter("cctv_total_events_detected", "Total security events generated")


def update_system_metrics():
    """Updates system resource utilization gauges."""
    try:
        mem = psutil.virtual_memory()
        CPU_MEMORY_USAGE.set(mem.used)
        CPU_PERCENT.set(psutil.cpu_percent(interval=None))
    except Exception:
        pass


def get_prometheus_metrics():
    """Generates latest Prometheus scrape output."""
    update_system_metrics()
    return generate_latest(), CONTENT_TYPE_LATEST
