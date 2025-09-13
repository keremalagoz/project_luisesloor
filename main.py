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

    st.divider()
    st.header("🗣️ Adım 4: Delivery Analizi")
    st.caption("Transkript süresine göre konuşma hızı, filler oranı, çeşitlilik ve duraklamalar.")
    if 'source_text' not in st.session_state:
        st.info("Önce materyali yükleyin (Adım 1).")
    else:
        with st.expander("Transkript giriş (manuel veya STT çıktısı yapıştır)", expanded=False):
            default_tx = st.session_state.get('transcript_text') or st.session_state['source_text'][:1000]
            transcript_text = st.text_area("Transkript", value=default_tx, height=200)
            st.session_state['transcript_text'] = transcript_text
        colA, colB = st.columns(2)
        with colA:
            duration_min = st.number_input("Süre (dakika)", min_value=0.0, value=0.0, step=0.5, help="0 girersen tahmini süre (150 WPM varsayımı) kullanılır.")
        with colB:
            show_config = st.checkbox("Konfig detaylarını göster", value=False)
        if st.button("Delivery Hesapla", type="primary"):
            from app.core.delivery import compute_delivery_metrics
            import yaml, os
            cfg_path = os.path.join('config','settings.yaml')
            custom_cfg = {}
            if os.path.exists(cfg_path):
                try:
                    with open(cfg_path, 'r', encoding='utf-8') as f:
                        y = yaml.safe_load(f) or {}
                        delivery_cfg = y.get('metrics', {}).get('delivery', {})
                        # weights alt yapısını compute fonksiyonundaki beklenen forma uydur.
                        custom_cfg.update(delivery_cfg)
                except Exception:
                    pass
            with st.spinner("Delivery metrikleri hesaplanıyor..."):
                res = compute_delivery_metrics(transcript_text, duration_minutes=duration_min, config=custom_cfg)
                st.session_state['delivery'] = res
            st.success("Delivery analizi tamam.")
        if 'delivery' in st.session_state:
            res = st.session_state['delivery']
            raw = res['raw']
            scores = res['scores']
            st.subheader("Skorlar")
            cols = st.columns(5)
            metric_map = [
                ('WPM', 'wpm'),
                ('Filler', 'filler'),
                ('Repetition', 'repetition'),
                ('Sentence Len', 'sentence_length'),
                ('Pause', 'pause'),
            ]
            for (label, key), c in zip(metric_map, cols):
                c.metric(label, f"{scores[key]:.2f}")
            st.metric("Delivery Toplam", f"{scores['delivery_score']:.2f}")
            with st.expander("Ham Değerler", expanded=False):
                st.write({k: v for k, v in raw.items() if k != 'insufficient_data'})
                if raw['insufficient_data']:
                    st.warning("Kelime sayısı çok düşük: Normalizasyon devre dışı (0 skor). Daha uzun transkript sağlayın.")
            if show_config:
                with st.expander("Kullanılan Konfig", expanded=False):
                    st.write(res['config_used'])

        st.divider()
        st.header("🧭 Adım 5: Pedagogy Analizi")
        st.caption("Örnekler, sorular, signposting, tanımlar ve özet heuristikleri.")
        if 'transcript_text' not in st.session_state:
            st.info("Delivery adımında veya transkript girişinde metin kaydedin.")
        else:
            ped_col1, ped_col2 = st.columns([2,1])
            with ped_col1:
                show_ped_cfg = st.checkbox("Pedagogy konfig detayları", value=False)
            with ped_col2:
                limit_preview = st.checkbox("Transkript önizle (ilk 600 char)", value=False)
            if limit_preview:
                st.code(st.session_state['transcript_text'][:600])
            if st.button("Pedagogy Hesapla", type="primary"):
                from app.core.pedagogy import compute_pedagogy_metrics
                import yaml, os
                ped_cfg = {}
                cfg_path = os.path.join('config','settings.yaml')
                if os.path.exists(cfg_path):
                    try:
                        with open(cfg_path, 'r', encoding='utf-8') as f:
                            y = yaml.safe_load(f) or {}
                            ped_cfg = y.get('metrics', {}).get('pedagogy', {})
                    except Exception:
                        pass
                with st.spinner("Pedagogy metrikleri hesaplanıyor..."):
                    ped = compute_pedagogy_metrics(st.session_state['transcript_text'], config=ped_cfg)
                    st.session_state['pedagogy'] = ped
                st.success("Pedagogy analizi tamam.")
            if 'pedagogy' in st.session_state:
                ped = st.session_state['pedagogy']
                pscores = ped['scores']
                praw = ped['raw']
                st.subheader("Pedagogy Skorları")
                cols = st.columns(6)
                metric_keys = ['examples','questions','signposting','definitions','summary','balance_bonus']
                for key, c in zip(metric_keys, cols):
                    c.metric(key.capitalize(), f"{pscores.get(key,0):.2f}")
                st.metric("Pedagogy Toplam", f"{pscores['pedagogy_score']:.2f}")
                with st.expander("Ham Sayımlar / Oranlar", expanded=False):
                    st.write(praw)
                    if praw['insufficient_data']:
                        st.warning("Cümle sayısı yetersiz (< min_sentences). Skorlar 0.")
                if show_ped_cfg:
                    with st.expander("Konfig", expanded=False):
                        st.write(ped['config_used'])

        st.divider()
        st.header("📈 Adım 6: Genel Skor Dashboard")
        from app.core.scoring import aggregate_scores
        cov_obj = st.session_state.get('coverage')
        del_obj = st.session_state.get('delivery')
        ped_obj = st.session_state.get('pedagogy')
        if not (cov_obj or del_obj or ped_obj):
            st.info("Önce en az bir analiz (coverage / delivery / pedagogy) üretin.")
        else:
            agg = aggregate_scores(cov_obj, del_obj, ped_obj)
            total = agg['total_score']
            inputs = agg['inputs']
            # renk seçimi
            if total >= 0.8:
                color = '🟢'
            elif total >= 0.6:
                color = '🟡'
            else:
                color = '🔴'
            st.subheader(f"Toplam Skor: {color} {total:.2f}")
            colA, colB, colC = st.columns(3)
            colA.metric("Coverage", f"{inputs['coverage']:.2f}")
            colB.metric("Delivery", f"{inputs['delivery']:.2f}")
            colC.metric("Pedagogy", f"{inputs['pedagogy']:.2f}")
            with st.expander("Ağırlıklar ve Detay", expanded=False):
                st.write({
                    'weights_used': agg['weights_used'],
                    'raw_inputs': inputs,
                })
            st.caption("Renk Eşiği: >=0.80 yeşil, 0.60–0.79 sarı, <0.60 kırmızı")

