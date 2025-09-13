"""Basit delivery metrik test scripti.
Farklı senaryoları çalıştırır ve metrik çıktılarını yazdırır.

Çalıştırma:
  python scripts/test_delivery.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from app.core.delivery import compute_delivery_metrics  # noqa

SCENARIOS = {
    "normal": {
        "text": """Bugün yapay zeka sistemlerinin temel bileşenlerini ele alıyoruz. Önce veri toplama sonra modelleme ve değerlendirme aşamalarını inceleyeceğiz. Bu süreçte bazı etik konulara da değineceğim.""",
        "minutes": 0.8,  # yaklaşık 48 saniye
    },
    "cok_hizli": {
        "text": " ".join(["model veri eğitim değerlendirme"] * 40),  # çok kısa tekrarlar
        "minutes": 0.3,
    },
    "filler_agir": {
        "text": """Yani bugün aslında şey derse başlarken yani önce şey veri toplama yani sonra aslında şey model seçimi yani hani değerlendirme.""",
        "minutes": 0.9,
    },
    "uzun_cumleler": {
        "text": """Makine öğrenmesi projelerinde karşılaşılan en büyük zorluklardan biri, toplanan verinin tutarlılığını ve kalite standartlarını sürdürürken aynı zamanda modelin genelleme kabiliyetini optimize etmektir; çünkü süreç boyunca farklı paydaşların beklentileri sürekli değişebilir.""",
        "minutes": 1.2,
    },
    "duraklamali": {
        "text": """Bugün veri analizi konuşacağız... Önce toplama -- sonra temizlik. \n\n Ardından modelleme. Sonra... değerlendirme.""",
        "minutes": 1.0,
    },
}


def run():
    for name, cfg in SCENARIOS.items():
        print(f"===== Senaryo: {name} =====")
        res = compute_delivery_metrics(cfg["text"], duration_minutes=cfg["minutes"])
        raw = res["raw"]
        scores = res["scores"]
        print(f"Words: {raw['words']} | WPM: {raw['wpm']:.1f} | Filler Ratio: {raw['filler_ratio']:.3f} | Avg Sent Len: {raw['avg_sentence_len']:.1f} | Pause Density: {raw['pause_density']:.3f}")
        print("Alt skorlar:")
        for k in ['wpm','filler','repetition','sentence_length','pause']:
            print(f"  {k:16s}: {scores[k]:.3f}")
        print(f"Toplam Delivery Skoru: {scores['delivery_score']:.3f}")
        print()


if __name__ == "__main__":
    run()
