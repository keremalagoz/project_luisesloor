"""Streamlit uygulaması giriş noktası.
Step 1: PDF/TXT Upload & Extraction UI
"""

import streamlit as st
from app.core import ingestion

st.set_page_config(page_title="AI Teaching Assistant", layout="wide")

st.title("📘 Ders Materyali Yükleme")
st.caption("Adım 1: PDF veya TXT materyalini yükle, metni çıkar ve onayla.")

if "source_text" in st.session_state:
	st.success("Bir materyal yüklendi. Yeniden yüklemek istersen aşağıdan devam edebilirsin.")

uploaded = st.file_uploader("Materyal seç (PDF/TXT)", type=["pdf","txt"], accept_multiple_files=False)

MAX_MB = 5
if uploaded:
	size_mb = uploaded.size / (1024 * 1024)
	if size_mb > MAX_MB:
		st.error(f"Dosya {size_mb:.2f} MB (> {MAX_MB} MB limit). Demo sürüm limiti aşıldı.")
	else:
		raw_text = ""
		if uploaded.type == "application/pdf" or uploaded.name.lower().endswith(".pdf"):
			raw_text = ingestion.read_pdf(uploaded.read())
		else:
			raw_text = ingestion.read_txt(uploaded.read())

		normalized = ingestion.normalize_text(raw_text)
		stats = ingestion.basic_text_stats(normalized)

		if not normalized.strip():
			st.error("Metin çıkarılamadı (boş veya okunamadı). Farklı bir dosya deneyin.")
		else:
			if stats["chars"] < 300:
				st.warning("Metin çok kısa; analiz kalitesi düşük olabilir.")

			with st.expander("Önizleme (ilk 800 karakter)"):
				st.text(normalized[:800])
			st.write(
				f"**Karakter:** {stats['chars']} | **Kelime:** {stats['words']} | **Yaklaşık Token:** {stats['approx_tokens']} | **Satır:** {stats['lines']}"
			)
			confirm = st.button("Metni kabul et ve devam et", type="primary")
			if confirm:
				st.session_state["source_text"] = normalized
				st.session_state["source_meta"] = {
					"filename": uploaded.name,
					"size_mb": size_mb,
					"stats": stats,
				}
				st.success("Materyal kaydedildi. Sonraki adım: Chunking & Embeddings (hazırlanacak).")

# Placeholder for next steps
st.divider()
st.write("⏭ Sonraki gelecek adımlar: Chunk oluşturma, Embeddings ve Coverage analizi.")

