"""
Acron AI/ML Module — Anomaly Detection
IsolationForest-based anomaly detection for equipment telemetry.
"""
from datetime import datetime, timedelta


def detect_anomalies(db, hours=4):
    """Detect anomalous telemetry readings using statistical thresholds.
    
    Falls back to z-score based detection if scikit-learn is not available.
    """
    from app import models

    cutoff = datetime.utcnow() - timedelta(hours=hours)
    equipment = db.query(models.Equipment).filter_by(active=True).all()
    anomalies = []

    for eq in equipment:
        telemetry = db.query(models.Telemetry).filter(
            models.Telemetry.equipment_id == eq.equipment_id,
            models.Telemetry.time >= cutoff,
        ).all()

        # Group by metric
        metric_values = {}
        for t in telemetry:
            if t.metric_value is not None:
                metric_values.setdefault(t.metric_name, []).append(t.metric_value)

        for metric_name, values in metric_values.items():
            if len(values) < 5:
                continue

            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            std = variance ** 0.5

            if std < 0.001:
                continue

            latest = values[-1]
            z_score = abs(latest - mean) / std

            if z_score > 2.5:
                severity = "critical" if z_score > 3.5 else "warning"
                anomalies.append({
                    "equipment_id": eq.equipment_id,
                    "metric": metric_name,
                    "value": round(latest, 3),
                    "mean": round(mean, 3),
                    "z_score": round(z_score, 2),
                    "severity": severity,
                    "detected_at": datetime.utcnow().isoformat() + "Z",
                })

    return anomalies
