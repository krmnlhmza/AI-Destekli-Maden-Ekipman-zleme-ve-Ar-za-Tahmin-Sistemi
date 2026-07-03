import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.database import init_db
from app.routers import sensors, anomalies, predict
from app.routers import dashboard
from app.routers import rag
from app.routers import reports
from app.routers import adapters as adapters_router
from data.simulator import EQUIPMENT_PROFILES

# Tek doğruluk kaynağı: simülatördeki ekipman profilleri.
# Ekipman eklemek/çıkarmak için sadece data/simulator.py'deki
# EQUIPMENT_PROFILES sözlüğü güncellenir; burası otomatik takip eder.
EQUIPMENT_IDS = list(EQUIPMENT_PROFILES.keys())
_stream_task  = None


async def _live_stream():
    """
    Saha sensörlerini taklit eden MQTT yayıncısı.
    Her 8 saniyede tüm ekipmanlar için okuma üretir ve MQTT broker'a yayınlar.
    Veriyi tüketip işleyen taraf app.services.mqtt_subscriber'dır.
    Akış:  simülatör → MQTT (maden/{eq}/sensor) → subscriber → DB/Redis/n8n/Qdrant
    """
    from data.mqtt_publisher import make_client, publish_reading
    import random

    # Yayıncı bağlanana kadar kısa bekleme
    await asyncio.sleep(2)
    client = await asyncio.get_event_loop().run_in_executor(None, make_client)
    client.loop_start()
    print("MQTT publisher başladı (canlı yayın).")

    cycle = 0
    try:
        while True:
            await asyncio.sleep(8)
            cycle += 1
            force_eq = random.choice(EQUIPMENT_IDS) if cycle % 15 == 0 else None
            # ~her 25 döngüde bir rastgele ekipmanda metan kaçağı (İSG demo)
            gas_eq = random.choice(EQUIPMENT_IDS) if cycle % 25 == 0 else None
            for eq_id in EQUIPMENT_IDS:
                publish_reading(client, eq_id,
                                force_anomaly=(eq_id == force_eq),
                                force_gas=(eq_id == gas_eq))
    except asyncio.CancelledError:
        pass
    finally:
        client.loop_stop()
        client.disconnect()


async def _setup_n8n():
    """n8n'de anomali alarm workflow'unu otomatik oluşturur."""
    import urllib.request, json, base64, time
    await asyncio.sleep(5)

    # ÇankaYazılım - Anomali Bildirim Akışı
    # Webhook → Filter → 4 paralel kanal: Log + PDF Trigger + Slack + Email
    # (Slack/Email node'ları kullanıcı kendi credentials'ını verince aktifleşir)
    workflow = {
        "name": "Anomali Alarm",
        "active": True,
        "nodes": [
            # 1) Webhook girişi — backend tarafı anomalide buraya POST atar
            {
                "id": "1", "name": "Anomali Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 2, "position": [200, 300],
                "parameters": {
                    "path": "anomali-alarm",
                    "responseMode": "onReceived",
                    "httpMethod": "POST",
                }
            },
            # 2) Filtre — sadece skor >= 0.7 olan kritik anomaliler bildirim alır
            {
                "id": "2", "name": "Kritik Filtre",
                "type": "n8n-nodes-base.if",
                "typeVersion": 2, "position": [420, 300],
                "parameters": {
                    "conditions": {"conditions": [{
                        "leftValue": "={{ $json.anomaly_score }}",
                        "rightValue": 0.7,
                        "operator": {"type": "number", "operation": "gte"},
                    }]}
                }
            },
            # 3a) Log — her kritik anomali için sistem log'una yaz
            {
                "id": "3", "name": "Sistem Log",
                "type": "n8n-nodes-base.set",
                "typeVersion": 3, "position": [680, 160],
                "parameters": {
                    "mode": "manual",
                    "assignments": {"assignments": [
                        {"id": "1", "name": "log_mesaji", "type": "string",
                         "value": "={{ '[KRITIK] ' + $json.equipment_id + ' | skor=' + $json.anomaly_score + ' | ' + $json.description }}"},
                    ]}
                }
            },
            # 3b) PDF Rapor Tetikleyici — backend'ten rapor oluşturmasını ister
            {
                "id": "4", "name": "PDF Rapor Uret",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4, "position": [680, 280],
                "parameters": {
                    "url": "http://host.docker.internal:8000/reports/pdf?saat=1",
                    "method": "GET",
                    "options": {"response": {"response": {"responseFormat": "file"}}},
                }
            },
            # 3c) Slack Bildirimi — kullanıcı Slack webhook URL'ini ayarlamalı
            {
                "id": "5", "name": "Slack Bildirim (KONF GEREK)",
                "type": "n8n-nodes-base.slack",
                "typeVersion": 2, "position": [680, 400],
                "disabled": True,   # credentials yokken pasif
                "parameters": {
                    "channel": "#bakim-alarm",
                    "text": "={{ '🚨 *Maden Ekipman Alarmı*\\nEkipman: ' + $json.equipment_id + '\\nSkor: ' + $json.anomaly_score + '\\n' + $json.description }}",
                }
            },
            # 3d) E-posta Bildirimi — kullanıcı SMTP/Gmail credentials ayarlamalı
            {
                "id": "6", "name": "E-posta Bildirim (KONF GEREK)",
                "type": "n8n-nodes-base.emailSend",
                "typeVersion": 2.1, "position": [680, 520],
                "disabled": True,
                "parameters": {
                    "fromEmail": "alarm@cankayazilim.tr",
                    "toEmail":   "bakim@madenisletmesi.tr",
                    "subject":   "=[KRITIK] {{ $json.equipment_id }} - Anomali",
                    "text":      "={{ 'Ekipman ID: ' + $json.equipment_id + '\\n\\nAnomali Skoru: ' + $json.anomaly_score + '\\n\\nAciklama:\\n' + $json.description + '\\n\\nDetayli rapor: http://localhost:8000/reports/pdf' }}",
                }
            },
        ],
        # Webhook → Filter → 4 paralel çıkış (Log + PDF + Slack + Email)
        "connections": {
            "Anomali Webhook": {"main": [[{"node": "Kritik Filtre", "type": "main", "index": 0}]]},
            "Kritik Filtre":   {"main": [[
                {"node": "Sistem Log",                  "type": "main", "index": 0},
                {"node": "PDF Rapor Uret",              "type": "main", "index": 0},
                {"node": "Slack Bildirim (KONF GEREK)", "type": "main", "index": 0},
                {"node": "E-posta Bildirim (KONF GEREK)","type": "main", "index": 0},
            ]]},
        },
    }

    try:
        cred = base64.b64encode(b"admin:admin123").decode()
        req  = urllib.request.Request(
            "http://localhost:5678/api/v1/workflows",
            data=json.dumps(workflow).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Basic {cred}",
                     "X-N8N-API-KEY": ""},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)
        print("n8n workflow oluşturuldu.")
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Modelleri ön yükle (ilk istek yavaş olmasın)
    from app.services.anomaly_detector import _load
    from app.services.embedding_service import _get_encoder, _get_qdrant
    from app.services.rag_service import index_knowledge
    from app.services import mqtt_subscriber
    _load()
    await asyncio.get_event_loop().run_in_executor(None, _get_encoder)
    await asyncio.get_event_loop().run_in_executor(None, _get_qdrant)
    await asyncio.get_event_loop().run_in_executor(None, index_knowledge)

    # MQTT abonesini başlat (veri giriş katmanı), ardından yayıncıyı
    mqtt_subscriber.start(asyncio.get_event_loop())

    global _stream_task
    _stream_task = asyncio.create_task(_live_stream())
    yield
    if _stream_task:
        _stream_task.cancel()
    mqtt_subscriber.stop()


app = FastAPI(
    title="Maden Dijital İkiz API",
    description="Maden ekipmanları için anomali tespiti ve tahmin sistemi",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sensors.router)
app.include_router(anomalies.router)
app.include_router(predict.router)
app.include_router(dashboard.router)
app.include_router(rag.router)
app.include_router(reports.router)
app.include_router(adapters_router.router)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return {
        "proje":         "Maden Dijital İkiz",
        "versiyon":      "1.0.0",
        "durum":         "çalışıyor",
        "dokümantasyon": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
