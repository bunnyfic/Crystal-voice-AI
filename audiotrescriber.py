import os
import tempfile
import time
from datetime import datetime

import streamlit as st
from streamlit_mic_recorder import mic_recorder
import whisper

# =====================================================================
#  PAGE CONFIG
# =====================================================================

st.set_page_config(
    page_title="Crystal Voice AI",
    page_icon="💎",
    layout="centered",
    initial_sidebar_state="expanded",
)

# =====================================================================
#  STYLE  —  palette drawn from the crystal lavender/sky-blue backdrop
#  amethyst #9D7FE0 · azure #6FA8DC · pearl #FBF9FF · ink #2E2A47
# =====================================================================

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

<style>

:root{
    --amethyst:#9D7FE0;
    --azure:#6FA8DC;
    --pearl:#FBF9FF;
    --ink:#2E2A47;
    --muted:#6B6483;
    --glass:rgba(255,255,255,.55);
    --glass-strong:rgba(255,255,255,.75);
    --border:rgba(157,127,224,.25);
}

html, body, [class*="css"]{
    font-family:'Inter', sans-serif;
    color:var(--ink);
}

.stApp{
    background:
        radial-gradient(circle at 15% 10%, rgba(157,127,224,.35), transparent 45%),
        radial-gradient(circle at 85% 90%, rgba(111,168,220,.35), transparent 45%),
        linear-gradient(135deg, #E6D9F7 0%, #F3EAFB 22%, #FBF9FF 48%, #E9F2FC 72%, #D3E7FB 100%);
    background-attachment: fixed;
}

#MainMenu{visibility:hidden;}
footer{visibility:hidden;}
header{visibility:hidden;}

/* ---------- Hero ---------- */

.hero-wrap{
    text-align:center;
    padding-top:18px;
    margin-bottom:6px;
    position:relative;
}

.orb{
    position:absolute;
    top:-40px; left:50%;
    transform:translateX(-50%);
    width:220px; height:220px;
    background:radial-gradient(circle, rgba(157,127,224,.45), rgba(111,168,220,.15) 60%, transparent 75%);
    filter:blur(18px);
    z-index:0;
}

.title{
    position:relative;
    z-index:1;
    font-family:'Poppins', sans-serif;
    font-weight:800;
    font-size:46px;
    letter-spacing:-.5px;
    background:linear-gradient(90deg,#7C5CD6,#6FA8DC,#9D7FE0);
    background-size:200% auto;
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    margin-bottom:2px;
}

.subtitle{
    position:relative;
    z-index:1;
    color:var(--muted);
    font-size:15.5px;
    font-weight:500;
    letter-spacing:.3px;
    margin-bottom:22px;
}

/* faceted divider — echoes the diagonal streaks in the backdrop */
.facet-divider{
    position:relative;
    height:22px;
    margin:0 auto 28px auto;
    max-width:520px;
    background:
        repeating-linear-gradient(
            100deg,
            rgba(157,127,224,.55) 0px,
            rgba(157,127,224,.55) 1px,
            transparent 1px,
            transparent 14px
        );
    -webkit-mask-image:linear-gradient(90deg, transparent, black 20%, black 80%, transparent);
    mask-image:linear-gradient(90deg, transparent, black 20%, black 80%, transparent);
    opacity:.7;
}

/* ---------- Glass card ---------- */

.card{
    background:var(--glass);
    backdrop-filter:blur(20px);
    -webkit-backdrop-filter:blur(20px);
    border-radius:24px;
    padding:30px 32px;
    border:1px solid var(--border);
    box-shadow:
        0 8px 32px rgba(120,100,190,.18),
        0 2px 8px rgba(120,100,190,.10);
    margin-bottom:22px;
}

.card h3{
    font-family:'Poppins', sans-serif;
    font-weight:700;
    font-size:19px;
    margin-top:0;
    margin-bottom:4px;
    color:var(--ink);
}

.card .hint{
    color:var(--muted);
    font-size:13.5px;
    margin-bottom:18px;
}

/* ---------- Tabs ---------- */

.stTabs [data-baseweb="tab-list"]{
    gap:6px;
    background:rgba(255,255,255,.35);
    padding:6px;
    border-radius:16px;
    border:1px solid var(--border);
}

.stTabs [data-baseweb="tab"]{
    border-radius:12px;
    padding:10px 18px;
    font-weight:600;
    color:var(--muted);
}

.stTabs [aria-selected="true"]{
    background:linear-gradient(90deg,var(--amethyst),var(--azure));
    color:white !important;
}

/* ---------- Buttons ---------- */

.stButton>button, .stDownloadButton>button{
    width:100%;
    padding:13px;
    font-size:16px;
    font-weight:600;
    font-family:'Inter', sans-serif;
    border:none;
    border-radius:14px;
    background:linear-gradient(90deg,var(--amethyst),var(--azure));
    color:white;
    box-shadow:0 6px 18px rgba(157,127,224,.35);
    transition:transform .15s ease, box-shadow .15s ease;
}

.stButton>button:hover, .stDownloadButton>button:hover{
    transform:translateY(-2px);
    box-shadow:0 10px 24px rgba(157,127,224,.45);
    color:white;
}

/* ---------- Inputs ---------- */

textarea, .stTextArea textarea{
    background:var(--glass-strong) !important;
    color:var(--ink) !important;
    border-radius:14px !important;
    border:1px solid var(--border) !important;
    font-size:16px !important;
    font-family:'Inter', sans-serif !important;
}

[data-testid="stFileUploaderDropzone"]{
    background:var(--glass-strong);
    border-radius:14px;
    border:1.5px dashed var(--border);
}

/* ---------- Badges / status pills ---------- */

.pill{
    display:inline-block;
    padding:5px 14px;
    border-radius:999px;
    font-size:12.5px;
    font-weight:600;
    background:rgba(157,127,224,.15);
    color:var(--amethyst);
    border:1px solid var(--border);
    margin-bottom:14px;
}

/* ---------- Sidebar ---------- */

section[data-testid="stSidebar"]{
    background:rgba(255,255,255,.45);
    backdrop-filter:blur(16px);
    border-right:1px solid var(--border);
}

/* ---------- Metric strip ---------- */

.stat-strip{
    display:flex;
    gap:14px;
    margin-top:14px;
}
.stat-box{
    flex:1;
    background:var(--glass-strong);
    border:1px solid var(--border);
    border-radius:14px;
    padding:12px 14px;
    text-align:center;
}
.stat-box .num{
    font-family:'Poppins', sans-serif;
    font-weight:700;
    font-size:20px;
    color:var(--amethyst);
}
.stat-box .lbl{
    font-size:12px;
    color:var(--muted);
    font-weight:500;
}

</style>
""", unsafe_allow_html=True)

# =====================================================================
#  HERO
# =====================================================================

st.markdown("""
<div class="hero-wrap">
    <div class="orb"></div>
    <div class="title">💎 Crystal Voice AI</div>
    <div class="subtitle">Speak it, upload it, read it — instant AI transcription</div>
</div>
<div class="facet-divider"></div>
""", unsafe_allow_html=True)

# =====================================================================
#  SIDEBAR — MODEL SETTINGS
# =====================================================================

with st.sidebar:
    st.markdown("### ⚙️ Transcription Settings")

    model_size = st.selectbox(
        "Model accuracy",
        options=["tiny", "base", "small", "medium"],
        index=1,
        help="Larger models are more accurate but slower to load and run.",
    )

    language_mode = st.selectbox(
        "Language",
        options=["Auto-detect", "English", "Hindi", "Spanish", "French", "German"],
        index=0,
    )

    st.markdown("---")
    st.markdown(
        "<span style='color:#6B6483;font-size:13px;'>"
        "💡 <b>tiny</b>/<b>base</b> are fastest — good for quick notes. "
        "<b>small</b>/<b>medium</b> are more accurate for longer or noisy audio."
        "</span>",
        unsafe_allow_html=True,
    )

LANG_CODES = {
    "Auto-detect": None,
    "English": "en",
    "Hindi": "hi",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
}

# =====================================================================
#  MODEL LOADING (cached so it only loads once per size)
# =====================================================================

@st.cache_resource(show_spinner=False)
def load_whisper_model(size: str):
    return whisper.load_model(size)


def transcribe_audio(file_path: str, size: str, lang_code):
    model = load_whisper_model(size)
    options = {}
    if lang_code:
        options["language"] = lang_code
    return model.transcribe(file_path, **options)


def save_temp_audio(raw_bytes: bytes, suffix: str) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(raw_bytes)
        return f.name


def render_result(result: dict, source_label: str):
    st.toast("Transcription complete", icon="✨")
    st.success(f"✅ Transcribed successfully from {source_label}")

    text = result.get("text", "").strip()
    detected_lang = result.get("language", "—")
    word_count = len(text.split()) if text else 0

    st.markdown(f"""
    <div class="stat-strip">
        <div class="stat-box"><div class="num">{word_count}</div><div class="lbl">Words</div></div>
        <div class="stat-box"><div class="num">{detected_lang.upper()}</div><div class="lbl">Detected Language</div></div>
        <div class="stat-box"><div class="num">{time.strftime('%H:%M')}</div><div class="lbl">Transcribed At</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    st.text_area("📝 Recognized Speech", value=text, height=240, key=f"txt_{source_label}_{time.time()}")

    st.download_button(
        label="⬇️ Download Transcript (.txt)",
        data=text,
        file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
        use_container_width=True,
    )


# =====================================================================
#  MAIN CARD — RECORD / UPLOAD TABS
# =====================================================================

st.markdown('<div class="card">', unsafe_allow_html=True)

tab_record, tab_upload = st.tabs(["🎙️  Record Audio", "📁  Upload Audio File"])

# ---------------------- TAB 1: RECORD ----------------------
with tab_record:
    st.markdown("<h3>Record your voice</h3>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hint'>Click start, speak clearly, then stop when you're done.</div>",
        unsafe_allow_html=True,
    )

    audio = mic_recorder(
        start_prompt="🎙️ Start Recording",
        stop_prompt="⏹️ Stop Recording",
        just_once=False,
        use_container_width=True,
        format="wav",
        key="recorder",
    )

    if audio:
        st.markdown("<span class='pill'>🎧 Recording ready</span>", unsafe_allow_html=True)
        st.audio(audio["bytes"])

        if st.button("📨 Transcribe Recording", key="btn_record_send"):
            with st.spinner("💎 Crystal AI is listening..."):
                path = save_temp_audio(audio["bytes"], ".wav")
                try:
                    result = transcribe_audio(
                        path, model_size, LANG_CODES[language_mode]
                    )
                finally:
                    os.remove(path)

            render_result(result, "microphone")

# ---------------------- TAB 2: UPLOAD ----------------------
with tab_upload:
    st.markdown("<h3>Upload an audio file</h3>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hint'>Supports MP3, WAV, M4A, OGG, FLAC and WEBM files.</div>",
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Drop your audio file here",
        type=["mp3", "wav", "m4a", "ogg", "flac", "webm"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        st.markdown("<span class='pill'>📁 File ready</span>", unsafe_allow_html=True)
        st.audio(uploaded_file)

        size_mb = uploaded_file.size / (1024 * 1024)
        st.caption(f"**{uploaded_file.name}** · {size_mb:.2f} MB")

        if size_mb > 200:
            st.warning("⚠️ File is quite large — transcription may take a while.")

        if st.button("📨 Transcribe File", key="btn_upload_send"):
            suffix = os.path.splitext(uploaded_file.name)[1] or ".wav"
            with st.spinner("💎 Crystal AI is processing your file..."):
                path = save_temp_audio(uploaded_file.getvalue(), suffix)
                try:
                    result = transcribe_audio(
                        path, model_size, LANG_CODES[language_mode]
                    )
                finally:
                    os.remove(path)

            render_result(result, "uploaded file")

st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
#  FOOTER
# =====================================================================

st.markdown(
    "<div style='text-align:center;color:#6B6483;font-size:12.5px;padding-top:6px;'>"
    "Built with 💎 Crystal Voice AI · Powered by OpenAI Whisper"
    "</div>",
    unsafe_allow_html=True,
)