"""Pedagogy metrik test scripti.
Çeşitli transkript senaryoları üzerinde heuristic skorları gösterir.
Çalıştırma: python scripts/test_pedagogy.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from app.core.pedagogy import compute_pedagogy_metrics  # noqa

SCENARIOS = {
    "dengeli": """Önce veri kavramını tanımlayalım. Veri nedir? Örneğin küçük bir sensör çıktısı olabilir. Şimdi bir sonraki aşamaya geçiyoruz. Ardından modeli eğiteceğiz. Sonuç olarak genel resmi özetleyeceğiz. Mesela sıcaklık ölçümü örnek olarak alınabilir. Peki neden bu farklı? Kısaca bu bölümde veri toplama ve hazırlığı işledik. Şimdi sonuç olarak toparlarsak veri kalitesi kritiktir.""",
    "sorusuz": """Veri işleme hattı üç aşamadan oluşur. İlk aşamada ham veri temizlenir. Sonra özellik çıkarımı yapılır. Ardından model eğitilir. Bu süreçte optimizasyon uygulanır. Sonuç olarak performans artar.""",
    "örnek_agir": """Örneğin bir kullanıcı isteği. Örnek olarak bir API çağrısı. Mesela bir sensör kaydı. Örneğin bir log satırı. Örnek veri sürekli akar. Örneğin sonuçlar depolanır. Mesela çıktı rapora girer. Örneğin gösterge paneli güncellenir. Örnekler çoğalır.""",
    "tanım_agir": """Makine öğrenmesi nedir. Denetimli öğrenme nedir. Denetimsiz öğrenme nedir. Derin öğrenme nedir. Yapay sinir ağı nedir. Aktivasyon fonksiyonu nedir. Ağırlık güncellemesi nedir. Geri yayılım nedir. Optimizasyon nedir. Düzenlileştirme nedir. Öğrenme oranı nedir.""",
    "kisa_yetersiz": """Örnek nedir. Neden önemli.""",
}


def run():
    for name, text in SCENARIOS.items():
        print(f"===== Senaryo: {name} =====")
        res = compute_pedagogy_metrics(text)
        raw = res['raw']
        scores = res['scores']
        print(f"Sentences: {raw['sentence_count']} | insufficient={raw['insufficient_data']}")
        print("Counts:", raw['counts'])
        print("Ratios:", {k: f"{v:.3f}" for k,v in raw['ratios'].items()})
        view_keys = ['examples','questions','signposting','definitions','summary','balance_bonus','pedagogy_score']
        print("Scores:")
        for k in view_keys:
            print(f"  {k:15s}: {scores.get(k,0):.3f}")
        print()


if __name__ == '__main__':
    run()
