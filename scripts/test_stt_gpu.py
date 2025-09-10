import os
import sys

# Basit GPU STT smoke test: model yükler ve kısa bir dosyada ilk 200 karakteri basar.
# Kullanım:
#   python scripts\test_stt_gpu.py sample_data\your_audio.wav

# Proje kökünü sys.path'e ekle (farklı çalışma dizinlerinden çalıştırma güvenliği)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def main():
    if len(sys.argv) < 2:
        print("Kullanım: python scripts/test_stt_gpu.py <audio_path>")
        sys.exit(1)
    audio_path = sys.argv[1]

    from app.core.transcript import transcribe
    from yaml import safe_load

    # settings.yaml oku
    with open(os.path.join("config", "settings.yaml"), "r", encoding="utf-8") as f:
        settings = safe_load(f)

    out = transcribe(audio_path, provider=settings.get("models", {}).get("stt_provider", "local"), settings=settings)
    print("Text:", out.get("text", "")[:200])
    print("Segments:", len(out.get("segments", [])))
    print("Duration:", out.get("duration_sec", 0.0))

if __name__ == "__main__":
    main()
