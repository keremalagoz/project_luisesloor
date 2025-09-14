import pytest, sys, os
from pathlib import Path

# Proje kökünü sys.path'e ekle (tests klasörü altından çalışırken)
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

@pytest.fixture
def short_text():
    return "Bu kısa bir metindir. Analiz için yeterli olmayabilir."

@pytest.fixture
def medium_transcript():
    return (
        "Makine öğrenmesi veri üzerinden modeller oluşturur. "
        "Gözetimli öğrenme etiketli veriye dayanır. Gözetimsiz öğrenme gizli yapıları bulur. "
        "Derin öğrenme katmanlı yapılar kullanır. Bu yöntemler birçok alanda uygulanır."
    )
