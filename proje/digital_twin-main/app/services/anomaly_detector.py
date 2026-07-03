"""
Isolation Forest Tabanlı Anomali Tespiti
-----------------------------------------
Sensör okumasını (sıcaklık, titreşim, basınç, akım, hız) Isolation Forest
ile değerlendirir; anormalse, ekipmanın kendi normal aralığına göre
hangi sensörün ne kadar saptığını açıklayan bir özet üretir.

Model `ml/train.py` ile eğitilir, buradan yüklenir.
Eğitilmiş model yoksa simülatör verisiyle hızlı bir bootstrap yapılır —
ama doğruluk için her zaman `python ml/train.py` çağrılması önerilir.
"""

import numpy as np
import pickle
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Dict, Optional

IF_PATH     = "ml/isolation_forest.pkl"
SCALER_PATH = "ml/scaler.pkl"

_model:  IsolationForest = None
_scaler: StandardScaler  = None


# ─────────────────────────────────────────────────────────────────
# Model yükleme
# ─────────────────────────────────────────────────────────────────
def _load() -> None:
    global _model, _scaler
    if _model is None:
        if os.path.exists(IF_PATH) and os.path.exists(SCALER_PATH):
            with open(IF_PATH,     "rb") as f: _model  = pickle.load(f)
            with open(SCALER_PATH, "rb") as f: _scaler = pickle.load(f)
        else:
            _bootstrap()


def _bootstrap() -> None:
    """
    Eğitilmiş model dosyaları yoksa, simülatör verisiyle hızlı eğitim yapar.
    `ml/train.py` ile aynı veri kaynağını kullanır (birim tutarlılığı için
    kritik) — sadece daha az örnek, daha hızlı.

    Önemli: kullanıcı uyarılır → asıl eğitim `python ml/train.py` ile.
    """
    global _model, _scaler
    from data.simulator import generate_training_data

    print("⚠  ml/isolation_forest.pkl bulunamadı — simülatör verisiyle "
          "geçici model üretiliyor. Doğruluk için: python ml/train.py")

    df = generate_training_data(n_samples=2000)
    features = ["temperature", "vibration", "pressure", "current", "speed"]
    X = df[features].values

    _scaler = StandardScaler()
    X_s = _scaler.fit_transform(X)

    _model = IsolationForest(
        n_estimators=200,
        contamination=0.05,   # simülatörün ~%5 anomali oranıyla hizalı
        random_state=42,
    )
    _model.fit(X_s)

    os.makedirs("ml", exist_ok=True)
    with open(IF_PATH,     "wb") as f: pickle.dump(_model,  f)
    with open(SCALER_PATH, "wb") as f: pickle.dump(_scaler, f)


# ─────────────────────────────────────────────────────────────────
# Anomali tespiti
# ─────────────────────────────────────────────────────────────────
def detect(reading: Dict, equipment_id: Optional[str] = None) -> Dict:
    """
    Tek bir sensör okumasını değerlendirir.

    Parametreler:
        reading: {temperature, vibration, pressure, current, speed,
                  [equipment_id, equipment_type, gas, ...]} dict.
        equipment_id: açıkça verilirse kullanılır; verilmezse reading'den
                      okunur. Bu, açıklama (description) üretirken
                      ekipmanın kendi kritik eşiklerini kullanmamızı sağlar.

    Dönüş:
        {is_anomaly, anomaly_score, description}.
        description sadece anomali ise dolu; ekipmanın profiline göre
        sapan tüm sensörleri ölçü değerleriyle birlikte listeler.
    """
    _load()

    x = np.array([[
        reading["temperature"],
        reading["vibration"],
        reading["pressure"],
        reading["current"],
        reading["speed"],
    ]])
    x_scaled = _scaler.transform(x)
    prediction = _model.predict(x_scaled)[0]
    raw_score  = float(_model.score_samples(x_scaled)[0])

    # score_samples negatif → daha küçük (daha negatif) = daha anormal.
    # 0-1 aralığına normalize: -0.5'i merkez al, 1'e kadar tara.
    normalized = float(np.clip(1 - (raw_score + 0.5), 0.0, 1.0))
    is_anomaly = prediction == -1

    eq_id = equipment_id or reading.get("equipment_id")

    return {
        "is_anomaly":    bool(is_anomaly),
        "anomaly_score": round(normalized, 4),
        "description":   _describe(reading, normalized, eq_id) if is_anomaly else None,
    }


# ─────────────────────────────────────────────────────────────────
# Açıklama üretimi — ekipmanın kendi eşikleriyle, çoklu sensör
# ─────────────────────────────────────────────────────────────────
_SENSOR_LABELS = {
    "temperature": ("Sıcaklık", "°C"),
    "vibration":   ("Titreşim", "mm/s"),
    "current":     ("Akım",     "A"),
    "pressure":    ("Basınç",   "bar"),
}


def _describe(r: Dict, score: float, equipment_id: Optional[str]) -> str:
    """
    Sapan tüm sensörleri ekipmanın **kendi** normal aralığı ve kritik
    eşiğiyle karşılaştırarak listeler. Eğer ekipman tanınmıyorsa,
    simülatörün ilk profilini varsayılan alır (geriye dönük güven).

    Çıktı örneği:
        "Anomali (LH517i_001): KRİTİK Titreşim (12.5 mm/s ≥ 12.6 mm/s),
         yüksek Sıcaklık (94.3 °C, kritiğe %45) — skor 0.823"
    """
    from data.simulator import EQUIPMENT_PROFILES, critical_thresholds

    eq_id = equipment_id if equipment_id in EQUIPMENT_PROFILES \
            else next(iter(EQUIPMENT_PROFILES))
    profile = EQUIPMENT_PROFILES[eq_id]
    crit    = critical_thresholds(eq_id)

    issues = []

    # Yukarı yönlü sapmalar (sıcaklık, titreşim, akım, basınç yükselişi)
    for key, (label, unit) in _SENSOR_LABELS.items():
        val = r.get(key)
        if val is None:
            continue
        hi      = profile[key][1]          # normal üst sınır
        crit_v  = crit[key]                # arıza/kritik eşik
        if val >= crit_v:
            issues.append(f"KRİTİK {label} ({val:.1f} {unit} ≥ {crit_v:.1f} {unit})")
        elif val > hi:
            pct = (val - hi) / (crit_v - hi) * 100 if crit_v > hi else 0.0
            issues.append(f"yüksek {label.lower()} ({val:.1f} {unit}, "
                          f"kritiğe %{pct:.0f})")

    # Aşağı yönlü basınç kaybı — hidrolik kayıp/pompa arızası işareti
    p_val = r.get("pressure")
    if p_val is not None:
        p_lo = profile["pressure"][0]
        if p_val < p_lo * 0.6:
            issues.append(f"düşük basınç ({p_val:.1f} bar, normal ≥ {p_lo:.1f})")

    if not issues:
        issues.append("çoklu parametre sapması (model tespit etti, eşik altı)")

    return f"Anomali ({eq_id}): {', '.join(issues)} — skor {score:.3f}"
