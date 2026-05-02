"""
Acron AI/ML Module — Equipment Health Scoring
Composite health score (0-100) based on OEE, anomaly frequency, and trend stability.
"""
from datetime import datetime, timedelta


def compute_health_scores(db, hours=8):
    """Compute composite health scores for all active equipment."""
    from app import models

    cutoff = datetime.utcnow() - timedelta(hours=hours)
    equipment = db.query(models.Equipment).filter_by(active=True).all()
    scores = []

    for eq in equipment:
        telemetry = db.query(models.Telemetry).filter(
            models.Telemetry.equipment_id == eq.equipment_id,
            models.Telemetry.time >= cutoff,
        ).all()

        # OEE component (40% weight)
        cycle_values = [t.metric_value for t in telemetry if t.metric_name == "cycle_time" and t.metric_value]
        if cycle_values:
            avg_cycle = sum(cycle_values) / len(cycle_values)
            standard = eq.cycle_time_standard or 35.0
            perf_ratio = min(1.0, standard / avg_cycle) if avg_cycle > 0 else 1.0
        else:
            perf_ratio = 0.85

        oee_score = perf_ratio * 100

        # Stability component (30% weight) — coefficient of variation
        if cycle_values and len(cycle_values) >= 3:
            mean = sum(cycle_values) / len(cycle_values)
            variance = sum((v - mean) ** 2 for v in cycle_values) / len(cycle_values)
            cv = (variance ** 0.5) / mean if mean > 0 else 0
            stability_score = max(0, 100 - cv * 200)  # Lower CV = higher score
        else:
            stability_score = 70

        # Downtime component (30% weight)
        downtime_minutes = sum(
            event.minutes for event in db.query(models.DowntimeEvent).filter(
                models.DowntimeEvent.equipment_id == eq.equipment_id,
                models.DowntimeEvent.started_at >= cutoff,
            ).all()
        )
        max_downtime = hours * 60
        downtime_score = max(0, 100 - (downtime_minutes / max_downtime) * 100)

        # Composite
        health = (oee_score * 0.4) + (stability_score * 0.3) + (downtime_score * 0.3)
        health = max(0, min(100, health))

        scores.append({
            "equipment_id": eq.equipment_id,
            "health_score": round(health, 1),
            "oee_component": round(oee_score, 1),
            "stability_component": round(stability_score, 1),
            "downtime_component": round(downtime_score, 1),
            "data_points": len(telemetry),
        })

    return scores
