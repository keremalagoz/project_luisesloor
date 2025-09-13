"""Streamlit uygulaması giriş noktası (main).
Step 1: PDF/TXT Upload & Extraction UI
Çalıştırma: streamlit run main.py
"""

import streamlit as st
from app.core import ingestion
from app.core.chunking import tokenize_and_chunk
from app.core.embeddings import get_or_compute_embeddings

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

st.divider()
st.write("⏭ Sonraki gelecek adımlar: Chunk oluşturma, Embeddings ve Coverage analizi.")

st.divider()
st.header("🔗 Adım 2: Chunking & Embeddings")
if 'source_text' not in st.session_state:
    st.info("Önce Adım 1'de materyal yükleyip onayla.")
else:
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        max_tokens = st.number_input("Max tokens", min_value=100, max_value=1200, value=450, step=50)
    with col2:
        overlap = st.number_input("Overlap tokens", min_value=0, max_value=400, value=50, step=10)
    with col3:
        min_chunk_tokens = st.number_input("Min chunk tokens", min_value=5, max_value=200, value=20, step=5)

    if st.button("Chunk Oluştur", type="primary"):
        chunks = tokenize_and_chunk(
            st.session_state['source_text'],
            max_tokens=max_tokens,
            overlap=overlap,
            min_chunk_tokens=min_chunk_tokens,
        )
        st.session_state['chunks'] = chunks
        st.success(f"{len(chunks)} chunk üretildi.")

    if 'chunks' in st.session_state:
        show = st.checkbox("Chunk önizleme (ilk 5)", value=True)
        if show:
            for ch in st.session_state['chunks'][:5]:
                st.code(f"{ch['id']} | tokens={ch['token_count']}\n" + ch['text'][:300] + ('...' if len(ch['text'])>300 else ''))
        if st.button("Embeddings Hesapla (placeholder)"):
            with st.spinner("Embedding hesaplanıyor / cache kontrol ediliyor..."):
                embedded = get_or_compute_embeddings(st.session_state['chunks'], model='text-embedding-004', use_real=False)
                st.session_state['embedded_chunks'] = embedded
            st.success("Embeddings hazır (fake). Gerçek API entegrasyonu TODO.")
    if 'embedded_chunks' in st.session_state:
        emb_list = st.session_state['embedded_chunks']
        if not emb_list:
            st.warning("Embedding üretilemedi (boş içerik veya tüm chunk'lar elendi).")
        else:
            first = emb_list[0].get('embedding') or []
            st.write(f"Örnek vektör boyutu: {len(first)} (placeholder)")
            st.info("Coverage skoru için bir sonraki aşamada hedef içerik karşılaştırması eklenecek.")

st.divider()
st.header("📊 Adım 3: Coverage Analizi")
if 'embedded_chunks' not in st.session_state or not st.session_state.get('embedded_chunks'):
    st.info("Önce Adım 2'de chunk ve embedding üret.")
else:
    st.caption("Her satır bir konu / başlık. Boş satırlar atlanır.")
    default_topics = """Giriş
Tanımlar
Örnekler
Uygulama Alanları
Sonuç""".strip()
    topics_text = st.text_area("Konu Listesi", value=default_topics, height=160)
    cthr, pthr = st.columns(2)
    with cthr:
        covered_thr = st.slider("Covered Eşiği", 0.5, 0.95, 0.78, 0.01)
    with pthr:
        partial_thr = st.slider("Partial Eşiği", 0.3, 0.9, 0.60, 0.01)
    if st.button("Coverage Hesapla"):
        from app.core.coverage import compute_coverage
        with st.spinner("Coverage hesaplanıyor..."):
            cov = compute_coverage(
                st.session_state['embedded_chunks'],
                topics_text,
                covered_thr=covered_thr,
                partial_thr=partial_thr,
                model='text-embedding-004',
                use_real=False,
            )
            st.session_state['coverage'] = cov
        st.success("Coverage hesaplandı.")
    if 'coverage' in st.session_state:
        cov = st.session_state['coverage']
        summ = cov['summary']
        st.subheader("Özet")
        st.write(f"Covered: {summ['covered']} | Partial: {summ['partial']} | Missing: {summ['missing']} | Coverage Ratio: {summ['coverage_ratio']:.2f}")
        st.subheader("Detay")
        import pandas as pd
        df = pd.DataFrame(cov['topics'])
        st.dataframe(df, use_container_width=True)
