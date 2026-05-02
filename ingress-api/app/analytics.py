"""
Analytics engine for Acron — OEE trend aggregation and downtime summary.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from . import models


def get_oee_trend(db: Session, hours: int = 24, bucket_hours: int = 1):
    """Return hourly OEE averages over the specified window."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    telemetry = db.query(models.Telemetry).filter(
        models.Telemetry.time >= cutoff,
        models.Telemetry.metric_name == "cycle_time",
    ).all()

    # Bucket by hour
    buckets = {}
    for t in telemetry:
        key = t.time.replace(minute=0, second=0, microsecond=0)
        if key not in buckets:
            buckets[key] = []
        buckets[key].append(t.metric_value)

    trend = []
    for ts in sorted(buckets.keys()):
        values = buckets[ts]
        avg_cycle = sum(values) / len(values) if values else 35.0
        perf = min(1.0, 35.0 / avg_cycle) if avg_cycle > 0 else 1.0
        oee = perf * 0.92 * 0.98 * 100  # simplified with avg avail and quality
        trend.append({"time": ts.isoformat(), "oee": round(oee, 2), "samples": len(values)})

    return trend


def get_downtime_summary(db: Session, hours: int = 24):
    """Aggregate downtime events by category."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    events = db.query(
        models.DowntimeEvent.category,
        func.count(models.DowntimeEvent.id).label("count"),
        func.sum(models.DowntimeEvent.minutes).label("total_minutes"),
    ).filter(
        models.DowntimeEvent.started_at >= cutoff
    ).group_by(
        models.DowntimeEvent.category
    ).all()

    return [
        {
            "category": e.category,
            "count": e.count,
            "total_minutes": round(float(e.total_minutes or 0), 1),
        }
        for e in events
    ]


def get_dashboard_stats(db: Session):
    """Consolidated stats for dashboard KPIs."""
    equipment = db.query(models.Equipment).filter_by(active=True).all()
    total = len(equipment)
    cutoff = datetime.utcnow() - timedelta(hours=1)
    recent = db.query(func.count(func.distinct(models.Telemetry.equipment_id))).filter(
        models.Telemetry.time >= cutoff
    ).scalar() or 0

    downtime_24h = db.query(func.sum(models.DowntimeEvent.minutes)).filter(
        models.DowntimeEvent.started_at >= datetime.utcnow() - timedelta(hours=24)
    ).scalar() or 0

    return {
        "total_assets": total,
        "live_assets": recent,
        "downtime_24h_minutes": round(float(downtime_24h), 1),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
