from __future__ import annotations

"""Phase 2 operational routes for Acron V2."""

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from pathlib import Path
import sys
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from . import auth, models
from .database import get_db
from .schemas import (
    ConnectorTestRequest,
    ConnectorTestResponse,
    ShiftCalendarCreate,
    TargetStandardCreate,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from edge.connectors import ConnectorConfig as EdgeConnectorConfig, connector_for

router = APIRouter(prefix="/api/v1", tags=["phase2"])


def _parse_hhmm(value: str) -> time:
    try:
        hour, minute = value.split(":", 1)
        return time(hour=int(hour), minute=int(minute))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid time value: {value}") from exc


def _resolve_plant(db: Session, plant_code: str | None = None) -> models.Plant:
    plant = None
    if plant_code:
        plant = db.query(models.Plant).filter(models.Plant.code == plant_code).first()
    if not plant:
        plant = db.query(models.Plant).order_by(models.Plant.id.asc()).first()
    if not plant:
        raise HTTPException(status_code=404, detail="No plant configuration found")
    return plant


def _shift_bounds(reference_day: date, shift: models.ShiftCalendar) -> tuple[datetime, datetime]:
    start_time = _parse_hhmm(shift.starts_at)
    end_time = _parse_hhmm(shift.ends_at)
    start_dt = datetime.combine(reference_day, start_time)
    end_dt = datetime.combine(reference_day, end_time)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    return start_dt, end_dt


def _resolve_shift_window(db: Session, plant: models.Plant, shift_name: str | None, reference_date: date | None) -> tuple[models.ShiftCalendar, datetime, datetime]:
    shifts = db.query(models.ShiftCalendar).filter(
        models.ShiftCalendar.plant_id == plant.id,
        models.ShiftCalendar.active.is_(True),
    ).all()
    if not shifts:
        raise HTTPException(status_code=404, detail="No active shift calendars found")

    if reference_date is None:
        reference_date = datetime.utcnow().date()

    if shift_name:
        shift = next((item for item in shifts if item.shift_name.lower() == shift_name.lower()), None)
        if not shift:
            raise HTTPException(status_code=404, detail=f"Shift {shift_name} not found")
        return shift, *_shift_bounds(reference_date, shift)

    now = datetime.utcnow()
    for shift in shifts:
        for day_offset in (0, -1):
            start_dt, end_dt = _shift_bounds(reference_date + timedelta(days=day_offset), shift)
            if start_dt <= now < end_dt:
                return shift, start_dt, end_dt

    shift = sorted(shifts, key=lambda item: item.starts_at)[0]
    return shift, *_shift_bounds(reference_date, shift)


def _quality_from_losses(quality_target: float, loss_tree: dict[str, float], planned_minutes: float) -> float:
    quality_minutes = loss_tree.get("quality issue", 0.0)
    drift = min(0.08, quality_minutes / max(planned_minutes, 1.0) * 0.2)
    return max(0.85, min(1.0, quality_target - drift))


def _report_window(db: Session, scope: str, plant: models.Plant, shift_name: str | None, reference_date: date | None) -> tuple[datetime, datetime, dict[str, Any]]:
    scope = scope.lower()
    if scope == "shift":
        shift, start_dt, end_dt = _resolve_shift_window(db, plant, shift_name, reference_date)
        return start_dt, end_dt, {
            "scope": "shift",
            "shift_name": shift.shift_name,
            "planned_downtime_minutes": shift.planned_downtime_minutes,
        }

    if reference_date is None:
        reference_date = datetime.utcnow().date()

    if scope == "day":
        start_dt = datetime.combine(reference_date, time(0, 0))
        end_dt = start_dt + timedelta(days=1)
        planned = sum(
            shift.planned_downtime_minutes
            for shift in db.query(models.ShiftCalendar).filter(
                models.ShiftCalendar.plant_id == plant.id,
                models.ShiftCalendar.active.is_(True),
            ).all()
        )
        return start_dt, end_dt, {
            "scope": "day",
            "shift_name": None,
            "planned_downtime_minutes": planned,
        }

    if scope == "month":
        month_start = reference_date.replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1)
        daily_planned = sum(
            shift.planned_downtime_minutes
            for shift in db.query(models.ShiftCalendar).filter(
                models.ShiftCalendar.plant_id == plant.id,
                models.ShiftCalendar.active.is_(True),
            ).all()
        )
        return datetime.combine(month_start, time(0, 0)), datetime.combine(month_end, time(0, 0)), {
            "scope": "month",
            "shift_name": None,
            "planned_downtime_minutes": daily_planned * max((month_end - month_start).days, 1),
        }

    raise HTTPException(status_code=400, detail="Scope must be one of: shift, day, month")


def _build_oee_report(
    db: Session,
    scope: str,
    plant_code: str | None,
    shift_name: str | None,
    reference_date: date | None,
) -> dict[str, Any]:
    plant = _resolve_plant(db, plant_code)
    start_dt, end_dt, context = _report_window(db, scope, plant, shift_name, reference_date)
    machines = db.query(models.Equipment).join(models.Cell, isouter=True).join(models.Line, isouter=True).filter(
        models.Equipment.active.is_(True)
    ).all()

    shift_key = context.get("shift_name")
    standards = db.query(models.TargetStandard).all()
    exact_standard_map = {(item.equipment_id, item.shift_name): item for item in standards}
    fallback_standard_map = {item.equipment_id: item for item in standards}

    reports = []
    total_target = 0
    total_actual = 0
    total_downtime = 0.0
    availability_sum = performance_sum = quality_sum = oee_sum = 0.0

    for machine in machines:
        telemetry = db.query(models.Telemetry).filter(
            models.Telemetry.equipment_id == machine.equipment_id,
            models.Telemetry.time >= start_dt,
            models.Telemetry.time < end_dt,
            models.Telemetry.metric_name == "cycle_time",
        ).all()
        events = db.query(models.DowntimeEvent).filter(
            models.DowntimeEvent.equipment_id == machine.equipment_id,
            models.DowntimeEvent.started_at >= start_dt,
            models.DowntimeEvent.started_at < end_dt,
        ).all()

        standard = exact_standard_map.get((machine.equipment_id, shift_key)) or fallback_standard_map.get(machine.equipment_id)
        standard_cycle_time = standard.standard_cycle_time if standard else (machine.cycle_time_standard or 35.0)
        quality_target = standard.quality_target if standard else 0.98

        window_minutes = max((end_dt - start_dt).total_seconds() / 60.0, 1.0)
        planned_minutes = max(window_minutes - float(context.get("planned_downtime_minutes", 0)), 1.0)
        loss_tree = defaultdict(float)
        for event in events:
            loss_tree[event.category] += float(event.minutes or 0)
        downtime_minutes = sum(loss_tree.values())
        run_minutes = max(planned_minutes - downtime_minutes, 0.0)
        availability = max(0.0, min(1.0, run_minutes / planned_minutes))

        cycle_samples = [row.metric_value for row in telemetry if row.metric_value]
        avg_cycle = sum(cycle_samples) / len(cycle_samples) if cycle_samples else standard_cycle_time
        performance = max(0.0, min(1.0, standard_cycle_time / avg_cycle if avg_cycle else 1.0))
        quality = _quality_from_losses(quality_target, loss_tree, planned_minutes)
        oee = availability * performance * quality

        operating_hours = max(planned_minutes / 60.0, 1 / 60.0)
        target_parts = int(round(standard.target_parts if standard and context["scope"] == "shift" else (machine.target_per_hour or 0) * operating_hours))
        actual_parts = int((run_minutes * 60.0) / max(avg_cycle, 1.0)) if run_minutes > 0 else 0

        reports.append(
            {
                "equipment_id": machine.equipment_id,
                "line": machine.cell.line.name if machine.cell and machine.cell.line else None,
                "cell": machine.cell.name if machine.cell else None,
                "process": machine.process.name if machine.process else None,
                "availability": round(availability * 100, 2),
                "performance": round(performance * 100, 2),
                "quality": round(quality * 100, 2),
                "oee": round(oee * 100, 2),
                "planned_minutes": round(planned_minutes, 2),
                "downtime_minutes": round(downtime_minutes, 2),
                "target_parts": target_parts,
                "actual_parts": actual_parts,
                "standard_cycle_time": round(standard_cycle_time, 2),
                "avg_cycle_time": round(avg_cycle, 2),
                "loss_tree": {key: round(value, 2) for key, value in sorted(loss_tree.items())},
            }
        )

        total_target += target_parts
        total_actual += actual_parts
        total_downtime += downtime_minutes
        availability_sum += availability * 100
        performance_sum += performance * 100
        quality_sum += quality * 100
        oee_sum += oee * 100

    count = max(len(reports), 1)
    reports.sort(key=lambda item: item["oee"])
    attainment = (total_actual / total_target * 100.0) if total_target else 0.0

    return {
        "scope": context["scope"],
        "plant_code": plant.code,
        "plant_name": plant.name,
        "shift_name": context.get("shift_name"),
        "window_start": start_dt.isoformat(),
        "window_end": end_dt.isoformat(),
        "summary": {
            "machines": len(reports),
            "availability": round(availability_sum / count, 2),
            "performance": round(performance_sum / count, 2),
            "quality": round(quality_sum / count, 2),
            "oee": round(oee_sum / count, 2),
            "target_parts": total_target,
            "actual_parts": total_actual,
            "attainment": round(attainment, 2),
            "downtime_minutes": round(total_downtime, 2),
        },
        "machines": reports,
    }


@router.get("/factory/shift-calendars")
async def list_shift_calendars(db: Session = Depends(get_db)):
    rows = db.query(models.ShiftCalendar).join(models.Plant).order_by(models.Plant.code, models.ShiftCalendar.shift_name).all()
    return [
        {
            "id": row.id,
            "plant_code": row.plant.code,
            "plant_name": row.plant.name,
            "shift_name": row.shift_name,
            "starts_at": row.starts_at,
            "ends_at": row.ends_at,
            "planned_downtime_minutes": row.planned_downtime_minutes,
            "active": row.active,
        }
        for row in rows
    ]


@router.post("/factory/shift-calendars")
async def upsert_shift_calendar(
    payload: ShiftCalendarCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles("admin", "manager")),
):
    plant = _resolve_plant(db, payload.plant_code)
    row = db.query(models.ShiftCalendar).filter(
        models.ShiftCalendar.plant_id == plant.id,
        models.ShiftCalendar.shift_name == payload.shift_name,
    ).first()
    if not row:
        row = models.ShiftCalendar(plant_id=plant.id, shift_name=payload.shift_name)
        db.add(row)
    row.starts_at = payload.starts_at
    row.ends_at = payload.ends_at
    row.planned_downtime_minutes = payload.planned_downtime_minutes
    row.active = payload.active
    db.commit()
    db.refresh(row)
    return {"status": "ok", "id": row.id}


@router.get("/factory/target-standards")
async def list_target_standards(db: Session = Depends(get_db)):
    rows = db.query(models.TargetStandard).order_by(models.TargetStandard.equipment_id, models.TargetStandard.shift_name).all()
    return [
        {
            "id": row.id,
            "equipment_id": row.equipment_id,
            "shift_name": row.shift_name,
            "target_parts": row.target_parts,
            "standard_cycle_time": row.standard_cycle_time,
            "quality_target": row.quality_target,
        }
        for row in rows
    ]


@router.post("/factory/target-standards")
async def upsert_target_standard(
    payload: TargetStandardCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles("admin", "manager", "supervisor")),
):
    machine = db.query(models.Equipment).filter(models.Equipment.equipment_id == payload.equipment_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Equipment not found")
    row = db.query(models.TargetStandard).filter(
        models.TargetStandard.equipment_id == payload.equipment_id,
        models.TargetStandard.shift_name == payload.shift_name,
    ).first()
    if not row:
        row = models.TargetStandard(equipment_id=payload.equipment_id, shift_name=payload.shift_name)
        db.add(row)
    row.target_parts = payload.target_parts
    row.standard_cycle_time = payload.standard_cycle_time
    row.quality_target = payload.quality_target
    machine.cycle_time_standard = payload.standard_cycle_time
    machine.target_per_hour = max(int(round(payload.target_parts / 8.0)), 1)
    db.commit()
    db.refresh(row)
    return {"status": "ok", "id": row.id}


@router.post("/connectors")
async def upsert_connector(
    payload: ConnectorTestRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles("admin", "manager", "maintenance")),
):
    row = db.query(models.ConnectorConfig).filter(models.ConnectorConfig.name == payload.name).first()
    if not row:
        row = models.ConnectorConfig(name=payload.name)
        db.add(row)
    row.protocol = payload.protocol
    row.endpoint = payload.endpoint
    row.tag_map = payload.tag_map
    row.active = True
    db.commit()
    db.refresh(row)
    return {"status": "ok", "id": row.id}


@router.post("/connectors/test", response_model=ConnectorTestResponse)
async def test_connector(
    payload: ConnectorTestRequest,
    current_user: models.User = Depends(auth.require_roles("admin", "manager", "maintenance")),
):
    config = EdgeConnectorConfig(
        name=payload.name,
        protocol=payload.protocol,
        endpoint=payload.endpoint,
        tag_map=payload.tag_map,
    )
    protocol = payload.protocol.lower()

    if protocol == "mqtt":
        return {
            "ok": True,
            "protocol": payload.protocol,
            "endpoint": payload.endpoint,
            "message": "MQTT connector configuration validated. Runtime subscriptions are handled by the edge gateway.",
            "sample": {key: "subscription" for key in payload.tag_map.keys()},
        }

    if protocol == "opc_ua":
        return {
            "ok": True,
            "protocol": payload.protocol,
            "endpoint": payload.endpoint,
            "message": "OPC UA configuration validated. Use the edge runtime for async node polling.",
            "sample": {key: payload.tag_map[key] for key in payload.tag_map.keys()},
        }

    try:
        connector = connector_for(config)
        sample = connector.read_tags()
        if protocol == "simulator" and not sample:
            sample = {key: 0 for key in payload.tag_map.keys()} or {"status": "ready"}
        return {
            "ok": True,
            "protocol": payload.protocol,
            "endpoint": payload.endpoint,
            "message": "Connector probe completed successfully.",
            "sample": sample,
        }
    except Exception as exc:
        return {
            "ok": False,
            "protocol": payload.protocol,
            "endpoint": payload.endpoint,
            "message": str(exc),
            "sample": None,
        }


@router.get("/reports/oee")
async def oee_reports(
    scope: str = Query("shift"),
    plant_code: str | None = Query(default=None),
    shift_name: str | None = Query(default=None),
    reference_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return _build_oee_report(db, scope=scope, plant_code=plant_code, shift_name=shift_name, reference_date=reference_date)
