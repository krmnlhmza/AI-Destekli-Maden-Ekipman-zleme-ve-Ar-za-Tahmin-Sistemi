"""
Isolation Forest Tabanlı Anomali Tespiti  (Adım 4'te yenilendi)
-----------------------------------------------------------------
Sensör okumasını (sıcaklık, titreşim, basınç, akım, hız) ekipmanın KENDİ
Isolation Forest modeliyle değerlendirir ve KALİBRE edilmiş 0-1 skor üretir.

Eski halinden farkı (neden değişti?):
  • Eski: tüm makineler tek modeldi ve ham skor "0.5 - score_samples"
    formülüyle 0-1'e sıkıştırılıyordu → normal okumalar bile ~0.92 alıyor,
    0.6/0.7 eşikleri hiçbir şey ayırt etmiyordu.
  • Yeni: her makinenin kendi modeli var (ml/if_<ekipman>.pkl) ve skor,
    eğitim sırasında çıkarılan "normal şöyle puan alır / arızalı böyle"
    istatistiğine göre haritalanıyor (np.interp ile). Artık:
        sağlıklı makine  → ~0.10-0.30
        0.6 üzeri        → UYARI  (dashboard kırmızı "ANOMALİ")
        0.7 üzeri        → KRİTİK (n8n bildirim zinciri tetiklenir)
    Bu eşikler sunumdaki (Slayt 9) anlatıyla birebir aynıdır.

Model `ml/train.py` ile eğitilir; dosya yoksa ilk istekte otomatik eğitilir.
"""

import os
import pickle
from typing import Dict, Optional

import numpy as np

# Sunumla birebir eşikler — başka dosyalar da (dashboard, n8n filtresi) bunları
# referans alabilsin diye burada sabit olarak dururlar
UYARI_ESIGI  = 0.6   # dashboard karta kırmızı "ANOMALİ" basar
KRITIK_ESIGI = 0.7   # n8n bildirim + PDF + log zinciri tetiklenir

IF_BUNDLE_TMPL = "ml/if_{eq}.pkl"

FEATURES = ["temperature", "vibration", "pressure", "current", "speed"]

# Ekipman başına yüklenen model paketleri (bellek içi önbellek):
# {ekipman_id: {"model": IsolationForest, "scaler": StandardScaler, "calib": {...}}}
_bundles: Dict[str, dict] = {}

# ── 2/3 TEYİT KURALI (kararlılık) ─────────────────────────────────
# Kalibre modelin ~%1 tekil yanlış alarmı, 8 sn'lik akışta birkaç dakikada
# bir sahte uyarı üretiyordu. Kural: son 3 okumanın EN AZ 2'si uyarı eşiğini
# aşmadan anomali İLAN EDİLMEZ. Tekil sıçramalar elenir; gerçek arızalar
# 6-9 okuma sürdüğünden teyit 8-16 sn içinde gelir. Operasyonel karşılığı:
# "sistem tek okumayla panik yapmaz, teyit eder."
from collections import deque as _deque
_son_skorlar: Dict[str, "_deque"] = {}


def _teyitli_karar(eq_id: str, score: float) -> bool:
    d = _son_skorlar.setdefault(eq_id, _deque(maxlen=3))
    d.append(score)
    return score >= UYARI_ESIGI and sum(1 for x in d if x >= UYARI_ESIGI) >= 2


def _load_bundle(equipment_id: str) -> dict:
    """Ekipmanın model paketini getirir. Sıra: önbellek → disk → yerinde eğitim.
    (Yerinde eğitim yalnız 'model dosyası silinmiş' durumunun sigortasıdır;
    asıl eğitim her zaman `python ml/train.py` ile yapılmalıdır.)"""
    if equipment_id in _bundles:
        return _bundles[equipment_id]

    path = IF_BUNDLE_TMPL.format(eq=equipment_id)
    if os.path.exists(path):
        with open(path, "rb") as f:
            _bundles[equipment_id] = pickle.load(f)
    else:
        print(f"⚠  {path} yok — {equipment_id} için geçici model eğitiliyor "
              f"(kalıcısı için: python ml/train.py)")
        import sys
        sys.path.insert(0, os.getcwd())
        from ml.train import train_one_equipment
        _bundles[equipment_id] = train_one_equipment(equipment_id, save=True)
    return _bundles[equipment_id]


def _load() -> None:
    """Uygulama açılışında çağrılır: tüm ekipmanların modellerini önden yükle
    (ilk sensör mesajında bekleme olmasın)."""
    from data.simulator import EQUIPMENT_PROFILES
    for eq_id in EQUIPMENT_PROFILES:
        _load_bundle(eq_id)


# ─────────────────────────────────────────────────────────────────
# Anomali tespiti
# ─────────────────────────────────────────────────────────────────
def detect(reading: Dict, equipment_id: Optional[str] = None) -> Dict:
    """
    Tek bir sensör okumasını değerlendirir.

    Dönüş: {is_anomaly, anomaly_score, description}
      • anomaly_score : kalibre 0-1 skor (0.10-0.30 = sağlıklı bölge)
      • is_anomaly    : skor >= 0.6 (UYARI eşiği) — dashboard ve loglar
                        bu bayrağı kullanır; böylece rozet ile skor çubuğu
                        asla birbiriyle çelişmez (eski sürümdeki hata buydu)
      • description   : yalnız anomalide dolu; hangi sensörün ne kadar
                        saptığını ekipmanın kendi eşikleriyle anlatır
    """
    eq_id = equipment_id or reading.get("equipment_id")
    bundle = _load_bundle(eq_id) if eq_id else None
    if bundle is None:
        # Ekipman kimliği yoksa ilk profilin modeline düş (geriye dönük güven)
        from data.simulator import EQUIPMENT_PROFILES
        eq_id = next(iter(EQUIPMENT_PROFILES))
        bundle = _load_bundle(eq_id)

    x = np.array([[reading[k] for k in FEATURES]], dtype=float)

    # Ham skor → kalibre skor: eğitimde saklanan çapa noktalarıyla haritala.
    # (score_samples daha negatif = daha anormal; -raw ile yönü çeviriyoruz)
    raw = float(bundle["model"].score_samples(bundle["scaler"].transform(x))[0])
    score = float(np.clip(
        np.interp(-raw, bundle["calib"]["xp"], bundle["calib"]["fp"]), 0.0, 1.0))

    is_anomaly = _teyitli_karar(eq_id, score)

    return {
        "is_anomaly":    bool(is_anomaly),
        "anomaly_score": round(score, 4),
        "description":   _describe(reading, score, eq_id) if is_anomaly else None,
    }


# ─────────────────────────────────────────────────────────────────
# Açıklama üretimi — ekipmanın kendi eşikleriyle, çoklu sensör
# (Adım 4'te değişmedi; zaten doğru çalışıyordu)
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
    eşiğiyle karşılaştırarak listeler.

    Çıktı örneği:
        "Anomali (LH517i_001): KRİTİK Titreşim (12.5 mm/s ≥ 12.6 mm/s),
         yüksek sıcaklık (94.3 °C, kritiğe %45) — skor 0.823"
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
        issues.append("çoklu parametre sapması (tek sensör eşik aşmadı, "
                      "örüntü anormal)")

    return f"Anomali ({eq_id}): {', '.join(issues)} — skor {score:.3f}"
