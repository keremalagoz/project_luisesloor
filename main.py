"""Streamlit uygulaması giriş noktası (main).
Step 1: PDF/TXT Upload & Extraction UI
Çalıştırma: streamlit run main.py
"""

import streamlit as st
from app.core import ingestion
from app.core.chunking import tokenize_and_chunk
from app.core.embeddings import get_or_compute_embeddings
from app.core.config import get_settings, get_validation
from app.core.logger import get_logger

st.set_page_config(page_title="AI Teaching Assistant", layout="wide")

logger = get_logger()
settings = get_settings()
validation = get_validation()

# Sidebar'da config & validation durumu
with st.sidebar.expander("⚙️ Config & Validation", expanded=not validation['is_valid']):
    st.write({
        'valid': validation['is_valid'],
        'errors': validation['errors'],
        'warnings': validation['warnings'],
    })
    if not validation['is_valid']:
        st.error("Config hataları mevcut. Lütfen düzeltin.")
    elif validation['warnings']:
        st.warning("Config uyarıları var. Ayrıntılar yukarıda.")

if not validation['is_valid']:
    st.warning("Config doğrulama hataları var; bazı analizler beklenmeyen sonuç verebilir.")

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
    col1, col2, col3, col4 = st.columns([1,1,1,1])
    with col1:
        max_tokens = st.number_input("Max tokens", min_value=100, max_value=1200, value=450, step=50)
    with col2:
        overlap = st.number_input("Overlap tokens", min_value=0, max_value=400, value=50, step=10)
    with col3:
        min_chunk_tokens = st.number_input("Min chunk tokens", min_value=5, max_value=200, value=20, step=5)
    with col4:
        use_real_embed = st.checkbox("Gerçek Embedding", value=False, help="Gemini API key tanımlıysa gerçek modeli çağırır, yoksa fake fallback.")
    model_name = st.text_input("Embedding Model", value="text-embedding-004", help="Gerekirse model adını değiştir.")

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
        if st.button("Embeddings Hesapla"):
            with st.spinner("Embedding hesaplanıyor / cache kontrol ediliyor..."):
                embedded = get_or_compute_embeddings(st.session_state['chunks'], model=model_name, use_real=use_real_embed)
                st.session_state['embedded_chunks'] = embedded
            if use_real_embed:
                st.success("Embeddings hazır (GERÇEK veya fallback).")
            else:
                st.success("Embeddings hazır (fake).")
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
        # --- STT / Audio Upload Bölümü ---
        with st.expander("🎤 Ses Dosyasından Transcribe (Opsiyonel)", expanded=False):
            st.caption("MP3/WAV yükle veya mikrofon kaydı (mikrofon entegrasyonu bir sonraki adımda eklenecek).")
            audio_file = st.file_uploader("Ses Dosyası Seç (mp3/wav/m4a)", type=["mp3","wav","m4a"], accept_multiple_files=False)
            stt_cols = st.columns([1,1,1])
            with stt_cols[0]:
                use_real_stt = st.checkbox("Gerçek STT", value=False, help="faster-whisper yüklüyse gerçek transcribe, yoksa fake.")
            with stt_cols[1]:
                lang_override = st.text_input("Dil Override", value="", help="Boş bırak otomatik tespit (ör: en, tr, de)")
            with stt_cols[2]:
                model_size = st.selectbox("Model Boyutu", ["tiny","base","small"], index=2)
            if audio_file and st.button("Transcribe Çalıştır"):
                from app.core.stt import transcribe_audio
                data = audio_file.read()
                with st.spinner("Ses çözümleniyor..."):
                    res = transcribe_audio(data, lang=lang_override or None, model_size=model_size, use_real=use_real_stt)
                st.session_state['transcript_text'] = res['text']
                # Süreyi set et (mevcut duration 0 ise veya kullanıcı henüz girmediyse)
                auto_minutes = (res.get('duration_seconds') or 0.0) / 60.0
                if auto_minutes > 0:
                    st.session_state['auto_duration_min'] = auto_minutes
                st.success(f"Transcribe tamamlandı (model={res['model']} cached={res['cached']}).")
                with st.expander("Transcribe Çıktısı", expanded=False):
                    st.text_area("Metin", value=res['text'][:5000], height=200)
                if res.get('segments'):
                    with st.expander("Segmentler", expanded=False):
                        import pandas as pd
                        seg_df = pd.DataFrame(res['segments'])
                        st.dataframe(seg_df.head(50), use_container_width=True)
            st.markdown("---")
            st.caption("Mikrofon Kaydı (Beta) - Tam kayıt veya deneysel canlı (streaming) partial transcript.")
            try:
                from streamlit_webrtc import webrtc_streamer, WebRtcMode
                import av, time, threading, queue
                from app.core.stt import transcribe_audio as _mic_transcribe
                from app.core.streaming_stt import StreamingTranscriber

                if 'mic_audio_chunks' not in st.session_state:
                    st.session_state['mic_audio_chunks'] = []
                if 'mic_recording' not in st.session_state:
                    st.session_state['mic_recording'] = False

                audio_q: "queue.Queue[bytes]" = queue.Queue()

                def audio_frame_callback(frame: 'av.AudioFrame'):
                    if not st.session_state.get('mic_recording'):
                        return frame
                    # PCM bytes elde et
                    pcm = frame.to_ndarray().tobytes()
                    audio_q.put(pcm)
                    return frame

                webrtc_ctx = webrtc_streamer(
                    key="mic",
                    mode=WebRtcMode.SENDONLY,
                    audio_receiver_size=256,
                    media_stream_constraints={"video": False, "audio": True},
                    async_processing=True,
                    audio_frame_callback=audio_frame_callback,
                )

                col_m1, col_m2, col_m3 = st.columns([1,1,2])
                with col_m1:
                    streaming_mode = st.checkbox("Canlı Streaming", value=False, help="Deneysel: belirli aralıklarla partial transcript üretir.")
                    if streaming_mode and 'stream_transcriber' not in st.session_state:
                        st.session_state['stream_transcriber'] = StreamingTranscriber(use_real=use_real_stt, model_size=model_size, lang=lang_override or None)
                    if not st.session_state['mic_recording']:
                        if st.button("Kaydı Başlat"):
                            st.session_state['mic_recording'] = True
                            st.session_state['mic_audio_chunks'] = []
                            st.session_state['mic_recording_started'] = time.time()
                            if streaming_mode:
                                st.session_state['stream_partial_text'] = ""
                            st.info("Kayıt başladı...")
                    else:
                        if st.button("Kaydı Bitir"):
                            st.session_state['mic_recording'] = False
                            # Kuyruktaki tüm veriyi topla
                            collected = []
                            while not audio_q.empty():
                                collected.append(audio_q.get())
                            raw_bytes = b"".join(collected)
                            if not raw_bytes:
                                st.warning("Kayıt boş görünüyor.")
                            else:
                                with st.spinner("Mikrofon kaydı işleniyor..."):
                                    res = _mic_transcribe(raw_bytes, lang=None, model_size=model_size, use_real=use_real_stt)
                                st.session_state['transcript_text'] = res['text'] or st.session_state.get('transcript_text', '')
                                dur_min = (res.get('duration_seconds') or 0.0) / 60.0
                                if dur_min > 0:
                                    st.session_state['auto_duration_min'] = dur_min
                                st.success("Mikrofon kaydı transcribe edildi.")
                                with st.expander("Mikrofon Transcribe Metni", expanded=False):
                                    st.text_area("Metin", value=res['text'][:5000], height=200)
                            # Streaming transcriber kapat
                            if streaming_mode and 'stream_transcriber' in st.session_state:
                                final_full = st.session_state['stream_transcriber'].close()
                                if final_full:
                                    st.session_state['transcript_text'] = final_full
                                st.session_state.pop('stream_transcriber', None)
                with col_m2:
                    if st.session_state.get('mic_recording'):
                        elapsed = time.time() - st.session_state.get('mic_recording_started', time.time())
                        st.write(f"Süre: {elapsed:.1f}s")
                        if streaming_mode and 'stream_transcriber' in st.session_state:
                            # Kuyruktaki veriyi al ve feed et
                            collected = []
                            while not audio_q.empty():
                                collected.append(audio_q.get())
                            if collected:
                                chunk_bytes = b"".join(collected)
                                partial = st.session_state['stream_transcriber'].feed(chunk_bytes)
                                if partial and partial.get('new_text'):
                                    existing = st.session_state.get('stream_partial_text','')
                                    st.session_state['stream_partial_text'] = existing + partial['new_text']
                with col_m3:
                    st.write("Durum: "+ ("Kayıt" if st.session_state.get('mic_recording') else "Hazır"))
                    if streaming_mode and st.session_state.get('mic_recording'):
                        st.markdown("**Canlı Partial:**")
                        st.text_area("Partial", value=st.session_state.get('stream_partial_text','')[-1000:], height=150)
            except Exception as e:
                st.info(f"Mikrofon modu kullanılamıyor: {e}")
        # --- /STT Bölümü ---
        with st.expander("Transkript giriş (manuel veya STT çıktısı yapıştır)", expanded=False):
            default_tx = st.session_state.get('transcript_text') or st.session_state['source_text'][:1000]
            transcript_text = st.text_area("Transkript", value=default_tx, height=200)
            st.session_state['transcript_text'] = transcript_text
        colA, colB = st.columns(2)
        with colA:
            prefill_dur = st.session_state.get('auto_duration_min', 0.0)
            duration_min = st.number_input("Süre (dakika)", min_value=0.0, value=prefill_dur, step=0.5, help="0 girersen tahmini süre (150 WPM varsayımı) kullanılır.")
        with colB:
            show_config = st.checkbox("Konfig detaylarını göster", value=False)
        if st.button("Delivery Hesapla", type="primary"):
            from app.core.delivery import compute_delivery_metrics
            # Yeni config modülü üzerinden al
            delivery_cfg = (settings.get('metrics') or {}).get('delivery', {}) or {}
            custom_cfg = dict(delivery_cfg)
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
                ped_cfg = (settings.get('metrics') or {}).get('pedagogy', {}) or {}
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
            # Öneriler
            from app.core.recommendations import generate_recommendations
            rec_obj = generate_recommendations(cov_obj, del_obj, ped_obj, agg)
            if rec_obj['recommendations']:
                with st.expander("Öneriler (Beta)", expanded=True):
                    sev_icons = {'high':'🔴','medium':'🟡','low':'🟢'}
                    for r in rec_obj['recommendations'][:10]:
                        icon = sev_icons.get(r['severity'],'•')
                        st.markdown(f"{icon} **[{r['category']}]** {r['message']}  ")
                        with st.popover("Detay", use_container_width=True):
                            st.write({
                                'severity': r['severity'],
                                'rationale': r['rationale'],
                                'meta': r.get('meta')
                            })
            else:
                st.info("Öneri üretilemedi (yeterince veri yok veya tüm skorlar yüksek).")
            with st.expander("Ağırlıklar ve Detay", expanded=False):
                st.write({
                    'weights_used': agg['weights_used'],
                    'raw_inputs': inputs,
                })
            st.caption("Renk Eşiği: >=0.80 yeşil, 0.60–0.79 sarı, <0.60 kırmızı")

            # Kalıcı kayıt (isteğe bağlı)
            st.divider()
            st.subheader("💾 Kalıcı Kayıt (SQLite)")
            st.caption("Bu çalışmayı veritabanına kaydedip geçmişte tekrar görüntüleyebilirsin.")
            save_col1, save_col2 = st.columns([1,2])
            db_path = None
            # config/settings.yaml içinden yol okunabilir; dinamik parse gerekirse burada yapılabilir.
            db_path = (settings.get('app') or {}).get('db_path')

            if st.button("Run Kaydet", type="primary"):
                try:
                    from app.core import storage
                    storage.init_db(db_path)
                    source_meta = st.session_state.get('source_meta') or {
                        'filename':'bilinmiyor.txt',
                        'size_mb': None,
                        'stats': {}
                    }
                    material_id = storage.insert_material(source_meta, db_path=db_path)
                    run_id = storage.insert_run(material_id, agg, coverage=cov_obj, delivery=del_obj, pedagogy=ped_obj, db_path=db_path)
                    if cov_obj:
                        storage.bulk_insert_topics(run_id, cov_obj, db_path=db_path)
                        storage.insert_coverage_metrics(run_id, cov_obj, db_path=db_path)
                    if del_obj:
                        storage.insert_delivery_metrics(run_id, del_obj, db_path=db_path)
                    if ped_obj:
                        storage.insert_pedagogy_metrics(run_id, ped_obj, db_path=db_path)
                    st.session_state['last_run_id'] = run_id
                    st.success(f"Run kaydedildi (ID={run_id}).")
                except Exception as e:
                    st.error(f"Kayıt başarısız: {e}")

            if 'last_run_id' in st.session_state:
                st.info(f"Son kaydedilen run ID: {st.session_state['last_run_id']}")

            with st.expander("Son Kayıtlar", expanded=False):
                try:
                    from app.core import storage as _stg
                    if db_path:
                        recent = _stg.fetch_recent_runs(db_path=db_path)
                    else:
                        recent = _stg.fetch_recent_runs()
                    if not recent:
                        st.write("Kayıt yok.")
                    else:
                        import pandas as pd
                        st.dataframe(pd.DataFrame(recent), use_container_width=True)
                except Exception as e:
                    st.warning(f"Geçmiş okunamadı: {e}")

            # Rapor oluşturma & indirme bölümü
            st.divider()
            st.subheader("📤 Rapor İndir (Beta)")
            st.caption("Mevcut üretilmiş modüllerden rapor derlenir. Eksik modüller atlanır.")
            colr1, colr2, colr3 = st.columns([1,1,2])
            with colr1:
                gen_btn = st.button("Raporu Oluştur", type="secondary")
            with colr2:
                auto_refresh = st.checkbox("Oto yenile", value=False, help="Her görüntülemede yeniden üret.")

            if gen_btn or auto_refresh:
                from app.core.report import build_report_data, render_markdown, export_json
                from datetime import datetime
                source_meta = st.session_state.get('source_meta') or {
                    'filename': 'bilinmiyor.txt',
                    'stats': {}
                }
                report_data = build_report_data(
                    source_meta=source_meta,
                    coverage=cov_obj,
                    delivery=del_obj,
                    pedagogy=ped_obj,
                    scoring=agg,
                )
                # Öneriler ekle (opsiyonel)
                try:
                    from app.core.recommendations import generate_recommendations as _gen_recs
                    recs_for_report = _gen_recs(cov_obj, del_obj, ped_obj, agg)
                    report_data['recommendations'] = recs_for_report
                except Exception as e:
                    logger.warning(f"Öneriler rapora eklenemedi: {e}")
                # RAG özeti ekle (varsa)
                try:
                    if 'rag_last_answer' in st.session_state:
                        rag_section = {
                            'question': st.session_state.get('rag_last_question'),
                            'answer': st.session_state['rag_last_answer'],
                        }
                        if 'rag_last_results' in st.session_state:
                            rag_section['sources'] = [
                                {'id': r.get('id'), 'similarity': r.get('similarity')}
                                for r in st.session_state['rag_last_results'][:5]
                            ]
                        mode = st.session_state.get('rag_last_retrieval_mode')
                        if mode:
                            rag_section['retrieval_mode'] = mode
                        report_data['rag'] = rag_section
                except Exception as e:
                    logger.warning(f"RAG bölümü rapora eklenemedi: {e}")
                md_text = render_markdown(report_data)
                json_text = export_json(report_data)
                st.session_state['report_data'] = report_data
                st.session_state['report_markdown'] = md_text
                st.session_state['report_json'] = json_text
                st.success("Rapor oluşturuldu.")

            if 'report_data' in st.session_state:
                with st.expander("Markdown Önizleme", expanded=False):
                    st.text_area("Markdown", st.session_state['report_markdown'], height=300)
                base_fn = (st.session_state.get('source_meta', {}) or {}).get('filename','rapor').rsplit('.',1)[0]
                from datetime import datetime
                ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                json_name = f"{base_fn}_rapor_{ts}.json"
                md_name = f"{base_fn}_rapor_{ts}.md"
                dcol1, dcol2, dcol3 = st.columns(3)
                with dcol1:
                    st.download_button(
                        "JSON İndir",
                        data=st.session_state['report_json'],
                        file_name=json_name,
                        mime="application/json",
                        type="primary"
                    )
                with dcol2:
                    st.download_button(
                        "Markdown İndir",
                        data=st.session_state['report_markdown'],
                        file_name=md_name,
                        mime="text/markdown",
                        type="secondary"
                    )
                with dcol3:
                    # HTML üretme (isteğe bağlı anlık)
                    from app.core.report import export_html
                    html_name = f"{base_fn}_rapor_{ts}.html"
                    try:
                        html_data = export_html(st.session_state['report_data'])
                        st.download_button(
                            "HTML İndir",
                            data=html_data,
                            file_name=html_name,
                            mime="text/html",
                            type="secondary"
                        )
                    except Exception as e:
                        st.warning(f"HTML üretimi başarısız: {e}")
                # PDF Export
                from app.core.report_pdf import export_pdf as export_pdf_bytes, PDFReportError
                pdf_col = st.container()
                try:
                    if st.button("PDF Oluştur & İndir", type="secondary"):
                        try:
                            pdf_bytes = export_pdf_bytes(st.session_state['report_data'])
                            pdf_name = f"{base_fn}_rapor_{ts}.pdf"
                            st.download_button(
                                "PDF İndir",
                                data=pdf_bytes,
                                file_name=pdf_name,
                                mime="application/pdf",
                                type="primary",
                                key="pdf_download_btn"
                            )
                            st.success("PDF üretildi.")
                        except PDFReportError as pe:
                            st.error(f"PDF üretim hatası: {pe}")
                        except Exception as e:
                            st.error(f"Beklenmeyen PDF hatası: {e}")
                except Exception as outer_e:
                    st.warning(f"PDF export kullanılamıyor: {outer_e}")

            # ------------------------------------------------------------------
            # Run History & Karşılaştırma
            st.divider()
            st.subheader("🕓 Run History ve Karşılaştırma")
            st.caption("Kaydedilmiş önceki analizleri incele ve iki run arasında metrik farklarını gör.")
            try:
                from app.core import storage as _stg
                # DB path belirle
                db_path = None
                db_path = (settings.get('app') or {}).get('db_path')
                recent_runs = _stg.fetch_recent_runs(db_path=db_path)
                if not recent_runs:
                    st.info("Kayıtlı run bulunamadı.")
                else:
                    import pandas as pd
                    # Liste görünümü
                    with st.expander("Son Run Listesi", expanded=False):
                        st.dataframe(pd.DataFrame(recent_runs), use_container_width=True)
                    # Seçim
                    run_ids = [r['id'] for r in recent_runs]
                    col_r1, col_r2, col_r3 = st.columns([1,1,2])
                    with col_r1:
                        sel_run = st.selectbox("Run Seç (A)", run_ids, key="run_select_a")
                    with col_r2:
                        sel_run_b = st.selectbox("Karşılaştır (B - opsiyonel)", [None] + run_ids, key="run_select_b")
                    load_btn = st.button("Run Detay Yükle", type="secondary")
                    if load_btn and sel_run:
                        try:
                            run_a = _stg.fetch_run_details(sel_run, db_path=db_path)
                            st.session_state['history_run_a'] = run_a
                            if sel_run_b:
                                run_b = _stg.fetch_run_details(sel_run_b, db_path=db_path)
                                st.session_state['history_run_b'] = run_b
                            else:
                                st.session_state.pop('history_run_b', None)
                            st.success("Run detay(ları) yüklendi.")
                        except Exception as e:
                            st.error(f"Detay yüklenemedi: {e}")

                    # Detay gösterimi
                    if 'history_run_a' in st.session_state:
                        run_a = st.session_state['history_run_a']
                        st.markdown(f"**Seçilen Run A:** ID={run_a.get('id')} | Toplam Skor={run_a.get('total_score')}")
                        with st.expander("Run A Metrik Detayları", expanded=False):
                            # Metrikleri tabloya dönüştür
                            m_rows = []
                            for m in run_a.get('metrics', []):
                                m_rows.append({
                                    'category': m.get('category'),
                                    'name': m.get('name'),
                                    'raw_value': m.get('raw_value'),
                                    'score': m.get('score'),
                                })
                            if m_rows:
                                st.dataframe(pd.DataFrame(m_rows), use_container_width=True)
                            else:
                                st.write("Metrik yok.")
                        if run_a.get('topics'):
                            with st.expander("Run A Coverage Topics", expanded=False):
                                t_df = pd.DataFrame(run_a['topics'])
                                st.dataframe(t_df, use_container_width=True)

                    # Karşılaştırma
                    if 'history_run_a' in st.session_state and 'history_run_b' in st.session_state:
                        run_a = st.session_state['history_run_a']
                        run_b = st.session_state['history_run_b']
                        st.markdown(f"**Karşılaştırma: A={run_a.get('id')} vs B={run_b.get('id')}**")
                        try:
                            from app.core.history import compare_runs
                            cmp = compare_runs(run_a, run_b)
                            summary = cmp['summary']
                            cols_cmp = st.columns(5)
                            cols_cmp[0].metric("Toplam A", f"{summary.get('total_score_a')}")
                            cols_cmp[1].metric("Toplam B", f"{summary.get('total_score_b')}")
                            delta_total = summary.get('total_score_delta')
                            cols_cmp[2].metric("Delta", f"{delta_total:+.3f}" if isinstance(delta_total,(int,float)) else str(delta_total))
                            cols_cmp[3].metric("İyileşen", summary.get('count_improved'))
                            cols_cmp[4].metric("Gerileyen", summary.get('count_declined'))

                            # Metrik delta tablosu
                            table_rows = []
                            for r in cmp['metrics']:
                                direction_symbol = {'up':'↑','down':'↓','flat':'→'}.get(r['direction'],'?')
                                table_rows.append({
                                    'category': r['category'],
                                    'name': r['name'],
                                    'A': r['a'],
                                    'B': r['b'],
                                    'delta': r['delta'],
                                    'trend': direction_symbol,
                                })
                            if table_rows:
                                import pandas as pd
                                df_cmp = pd.DataFrame(table_rows)
                                st.dataframe(df_cmp, use_container_width=True)
                        except Exception as e:
                            st.error(f"Karşılaştırma hatası: {e}")
            except Exception as e:
                st.warning(f"Run history yüklenemedi: {e}")

        # ------------------------------------------------------------------
        # Adım 7: Trend & Progress Dashboard
        st.divider()
        st.header("📉 Adım 7: Trend & Progress")
        st.caption("Run skorlarının zaman içindeki gelişimini incele.")
        from app.core import storage as _stg2
        from app.core.trends import prepare_run_dataframe, compute_basic_deltas, top_improvements
        db_path2 = (settings.get('app') or {}).get('db_path')
        try:
            all_runs = _stg2.fetch_recent_runs(limit=200, db_path=db_path2)
        except Exception as e:
            all_runs = []
            st.warning(f"Run sorgusu başarısız: {e}")
        run_count = len(all_runs)
        if run_count < 2:
            st.info("Trend analizi için en az 2 run gerekli.")
        else:
            # Slider min<max zorunluluğu nedeniyle run_count==2 özel durumu ele al
            min_allowed = 2
            max_allowed = min(50, run_count)
            if max_allowed <= min_allowed:
                # Tam olarak 2 run var; slider yerine sabit değer göster
                max_n = 2
                st.caption("2 run bulundu – tümü gösteriliyor.")
            else:
                default_val = min(10, max_allowed)
                max_n = st.slider(
                    "Kaç run gösterilsin?",
                    min_value=min_allowed,
                    max_value=max_allowed,
                    value=default_val,
                )
            subset = list(reversed(all_runs))[:max_n]
            subset = list(reversed(subset))  # kronolojik sıra
            df = prepare_run_dataframe(subset)
            import pandas as pd
            score_cols = ['total_score','coverage_score','delivery_score','pedagogy_score']
            # Line chart (Altair opsiyonel yoksa built-in)
            chart_df = df[['id'] + [c for c in score_cols if c in df.columns]].copy()
            chart_df = chart_df.melt(id_vars='id', var_name='metric', value_name='value')
            st.line_chart(chart_df, x='id', y='value', color='metric')
            deltas = compute_basic_deltas(df)
            if deltas:
                st.subheader("Delta (İlk vs Son Run)")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Δ", f"{deltas['total_score_delta']:+.3f}" if deltas['total_score_delta'] is not None else '-')
                c2.metric("Coverage Δ", f"{deltas['coverage_score_delta']:+.3f}" if deltas['coverage_score_delta'] is not None else '-')
                c3.metric("Delivery Δ", f"{deltas['delivery_score_delta']:+.3f}" if deltas['delivery_score_delta'] is not None else '-')
                c4.metric("Pedagogy Δ", f"{deltas['pedagogy_score_delta']:+.3f}" if deltas['pedagogy_score_delta'] is not None else '-')
            imp = top_improvements(df, score_cols, top_n=3)
            col_imp, col_dec = st.columns(2)
            with col_imp:
                st.markdown("**En Çok İyileşen**")
                if not imp['improved']:
                    st.write("Yok")
                else:
                    for m, d in imp['improved']:
                        st.write(f"{m}: +{d:.3f}")
            with col_dec:
                st.markdown("**En Çok Gerileyen**")
                if not imp['declined']:
                    st.write("Yok")
                else:
                    for m, d in imp['declined']:
                        st.write(f"{m}: {d:.3f}")
            with st.expander("Skor Tablosu", expanded=False):
                st.dataframe(df[['id'] + score_cols], use_container_width=True)

        # ------------------------------------------------------------------
        # Adım 8: RAG Soru-Cevap
        st.divider()
        st.header("🧠 Adım 8: Soru-Cevap (RAG)")
        st.caption("Chunk + Embedding üzerinden basit retrieval ve extractive cevap.")
        if 'embedded_chunks' not in st.session_state or not st.session_state['embedded_chunks']:
            st.info("Önce Adım 2'de embedding oluştur.")
        else:
            from app.core.rag import build_index, similarity_search, generate_answer
            rag_cfg = (settings.get('rag') or {})
            rret = (rag_cfg.get('retrieval') or {})
            default_hybrid = bool(rret.get('default_hybrid_enabled', False))
            default_alpha = float(rret.get('default_alpha', 1.0))
            default_topk = int(rret.get('default_top_k', 5))
            if 'rag_index' not in st.session_state:
                if st.button("RAG İndeksi Oluştur", type="secondary"):
                    try:
                        st.session_state['rag_index'] = build_index(st.session_state['embedded_chunks'])
                        st.success("İndeks hazır.")
                    except Exception as e:
                        st.error(f"İndeks oluşturulamadı: {e}")
            if 'rag_index' in st.session_state:
                q_col1, q_col2, q_col3, q_col4 = st.columns([3,1,1,2])
                with q_col1:
                    user_query = st.text_input("Soru", value="Bu materyalin ana konusu nedir?")
                with q_col2:
                    top_k = st.number_input("Top-K", min_value=1, max_value=10, value=default_topk, step=1)
                with q_col3:
                    use_llm = st.checkbox("LLM Placeholder", value=False)
                with q_col4:
                    use_hybrid = st.checkbox("Hibrit Retrieval", value=default_hybrid)
                    alpha = st.slider("Alpha (dense)", 0.0, 1.0, default_alpha, 0.05, disabled=not use_hybrid)
                if st.button("Sorgula", type="primary"):
                    if not user_query.strip():
                        st.warning("Soru boş.")
                    else:
                        with st.spinner("Aranıyor..."):
                            try:
                                if use_hybrid:
                                    results = similarity_search(st.session_state['rag_index'], user_query, use_real=False, top_k=top_k, hybrid_alpha=alpha)
                                else:
                                    results = similarity_search(st.session_state['rag_index'], user_query, use_real=False, top_k=top_k)
                                answer_obj = generate_answer(user_query, results, llm=use_llm)
                                st.session_state['rag_last_question'] = user_query
                                st.session_state['rag_last_results'] = results
                                st.session_state['rag_last_answer'] = answer_obj
                                st.session_state['rag_last_retrieval_mode'] = 'hybrid' if use_hybrid else 'dense'
                                st.success("Tamamlandı.")
                            except Exception as e:
                                st.error(f"Arama/cevap hatası: {e}")
                # LLM ile Cevaplama
                from app.core.llm import generate_llm_answer as _llm_answer
                from app.core.config import get_settings as _get_cfg
                if 'rag_last_results' in st.session_state and st.button("LLM ile Cevapla", type="secondary"):
                    cfg = _get_cfg()
                    with st.spinner("LLM cevabı üretiliyor..."):
                        try:
                            llm_ans = _llm_answer(user_query, st.session_state['rag_last_results'], settings=cfg)
                            st.session_state['rag_llm_answer'] = llm_ans
                            st.success("LLM cevabı hazır.")
                        except Exception as e:
                            st.error(f"LLM cevap hatası: {e}")
                if 'rag_last_answer' in st.session_state:
                    st.subheader("Cevap")
                    st.write(st.session_state['rag_last_answer']['answer'])
                    conf = st.session_state['rag_last_answer'].get('confidence')
                    if conf is not None:
                        # Confidence rozetini eşiklere göre göster
                        cthr = (rag_cfg.get('confidence') or {})
                        low = float(cthr.get('low', 0.5))
                        med = float(cthr.get('medium', 0.7))
                        if conf < low:
                            badge = '🔴 düşük'
                        elif conf < med:
                            badge = '🟡 orta'
                        else:
                            badge = '🟢 yüksek'
                        st.caption(f"Güven (avg similarity): {conf:.3f} — {badge}")
                if 'rag_llm_answer' in st.session_state:
                    st.subheader("LLM Cevabı")
                    st.write(st.session_state['rag_llm_answer']['answer'])
                if 'rag_last_results' in st.session_state:
                    with st.expander("Kaynak Chunk'lar", expanded=False):
                        import pandas as pd
                        df_r = pd.DataFrame([
                            {
                                'id': r.get('id'),
                                'similarity': round(r.get('similarity',0), 3),
                                'preview': (r.get('text','')[:180] + '...') if len(r.get('text',''))>200 else r.get('text','')
                            } for r in st.session_state.get('rag_last_results', [])
                        ])
                        st.dataframe(df_r, use_container_width=True)


