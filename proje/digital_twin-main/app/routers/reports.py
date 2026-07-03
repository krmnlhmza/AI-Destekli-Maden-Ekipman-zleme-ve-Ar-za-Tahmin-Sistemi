"""
Raporlama Router'ı  —  /reports/...
------------------------------------
Son N saatteki sistem durumunun indirilebilir PDF raporu.

  GET /reports/pdf?saat=24   →  application/pdf indirme
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from datetime import datetime, timedelta, timezone
from io import BytesIO

from app.database import get_db
from app.models.sensor import SensorReading, AnomalyLog
from app.services.pdf_report import build_anomaly_report

router = APIRouter(prefix="/reports", tags=["Raporlama"])


@router.get("/pdf")
async def anomaly_pdf(
    saat: int = Query(default=24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """Son `saat` saatteki anomalileri içeren PDF rapor."""
    since = datetime.now(timezone.utc) - timedelta(hours=saat)

    # Özet
    total = await db.scalar(select(func.count()).select_from(SensorReading))
    anomalies_24h = await db.scalar(
        select(func.count()).select_from(AnomalyLog)
        .where(AnomalyLog.time >= datetime.now(timezone.utc) - timedelta(hours=24))
    )
    anomalies_1h = await db.scalar(
        select(func.count()).select_from(AnomalyLog)
        .where(AnomalyLog.time >= datetime.now(timezone.utc) - timedelta(hours=1))
    )

    # Anomali listesi
    rows = await db.execute(
        select(AnomalyLog)
        .where(AnomalyLog.time >= since)
        .order_by(desc(AnomalyLog.time))
        .limit(60)
    )
    logs = rows.scalars().all()
    items = [
        {
            "time":          l.time.isoformat() if l.time else "",
            "equipment_id":  l.equipment_id,
            "anomaly_score": l.anomaly_score,
            "description":   l.description,
            "resolved":      l.resolved,
        }
        for l in logs
    ]

    pdf_bytes = build_anomaly_report(
        rows=items,
        summary={
            "toplam_okuma": total or 0,
            "anomali_24h":  anomalies_24h or 0,
            "anomali_1h":   anomalies_1h or 0,
        },
        hours=saat,
    )

    filename = f"anomali_raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
