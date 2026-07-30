import os
import json
import tempfile
import time
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from streamlit_mic_recorder import mic_recorder
import whisper

# Optional faster-whisper engine (CTranslate2) — much faster load + inference.
# Falls back gracefully to openai-whisper if it isn't installed.
try:
    from faster_whisper import WhisperModel as FasterWhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False

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
#  SESSION STATE
# =====================================================================

if "theme" not in st.session_state:
    st.session_state.theme = "light"
if "sidebar_expanded" not in st.session_state:
    st.session_state.sidebar_expanded = True

# =====================================================================
#  THEME PALETTES
#  amethyst #9D7FE0 · azure #6FA8DC · ink stays blue-tinted, never white
# =====================================================================

if st.session_state.theme == "light":
    PALETTE = {
        "ink": "#2E2A47",
        "muted": "#5B5578",
        "glass": "rgba(255,255,255,.55)",
        "glass_strong": "rgba(255,255,255,.80)",
        "border": "rgba(157,127,224,.30)",
        "bg": "linear-gradient(135deg, #E6D9F7 0%, #F3EAFB 22%, #FBF9FF 48%, #E9F2FC 72%, #D3E7FB 100%)",
        "bg_glow_1": "rgba(157,127,224,.35)",
        "bg_glow_2": "rgba(111,168,220,.35)",
        "sidebar_bg": "rgba(255,255,255,.55)",
        "input_bg": "rgba(255,255,255,.85)",
    }
else:
    PALETTE = {
        "ink": "#CBD6FA",
        "muted": "#9CA3D4",
        "glass": "rgba(30,24,58,.55)",
        "glass_strong": "rgba(30,24,58,.78)",
        "border": "rgba(157,127,224,.35)",
        "bg": "linear-gradient(135deg, #191529 0%, #221B3B 25%, #1B1730 50%, #1A2338 75%, #131A2B 100%)",
        "bg_glow_1": "rgba(157,127,224,.45)",
        "bg_glow_2": "rgba(111,168,220,.35)",
        "sidebar_bg": "rgba(20,16,38,.65)",
        "input_bg": "rgba(40,34,68,.85)",
    }

# =====================================================================
#  STYLE
# =====================================================================

st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

<style>

:root{{
    --amethyst:#9D7FE0;
    --azure:#6FA8DC;
    --ink:{PALETTE["ink"]};
    --muted:{PALETTE["muted"]};
    --glass:{PALETTE["glass"]};
    --glass-strong:{PALETTE["glass_strong"]};
    --border:{PALETTE["border"]};
    --input-bg:{PALETTE["input_bg"]};
}}

html, body, [class*="css"]{{
    font-family:'Inter', sans-serif;
    color:var(--ink) !important;
}}

.stApp{{
    background:
        radial-gradient(circle at 15% 10%, {PALETTE["bg_glow_1"]}, transparent 45%),
        radial-gradient(circle at 85% 90%, {PALETTE["bg_glow_2"]}, transparent 45%),
        {PALETTE["bg"]};
    background-size: 160% 160%, 160% 160%, 220% 220%;
    background-attachment: fixed;
    animation: crystalDrift 22s ease-in-out infinite alternate;
}}

@keyframes crystalDrift{{
    0%   {{ background-position: 10% 10%, 90% 90%, 0% 50%; }}
    100% {{ background-position: 25% 25%, 75% 75%, 100% 50%; }}
}}

/* keep Streamlit's header bar (it holds the sidebar toggle, critical on mobile)
   but strip out the deploy/menu toolbar clutter */
#MainMenu{{visibility:hidden;}}
footer{{visibility:hidden;}}
header{{background:transparent !important; box-shadow:none !important;}}
/* only hide the deploy button / running-status widget — leave the rest of the
   toolbar alone, since the sidebar open/close arrow lives in there too */
[data-testid="stAppDeployButton"]{{display:none !important;}}
[data-testid="stStatusWidget"]{{display:none !important;}}
[data-testid="collapsedControl"], [data-testid="stSidebarCollapseButton"]{{
    color:var(--ink) !important;
}}

/* ---------- Global text readability — everything blue/ink, never white ---------- */

.stMarkdown, .stMarkdown p, .stMarkdown li, .stText, label, p, span, div,
[data-testid="stWidgetLabel"] p, [data-testid="stCaptionContainer"], .stCaption,
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li{{
    color:var(--ink);
}}

.stCaption, [data-testid="stCaptionContainer"]{{
    color:var(--muted) !important;
}}

[data-baseweb="select"] *{{ color:var(--ink) !important; }}
[data-baseweb="popover"]{{ background:var(--glass-strong) !important; }}
[data-baseweb="popover"] li{{ color:var(--ink) !important; }}
[data-baseweb="popover"] li:hover{{ background:rgba(157,127,224,.18) !important; }}

.stAlert, .stAlert p, .stAlert div{{ color:var(--ink) !important; }}

/* ---------- Hero ---------- */

.hero-wrap{{
    text-align:center;
    padding-top:18px;
    margin-bottom:6px;
    position:relative;
}}

.orb{{
    position:absolute;
    top:-40px; left:50%;
    transform:translateX(-50%);
    width:220px; height:220px;
    background:radial-gradient(circle, rgba(157,127,224,.45), rgba(111,168,220,.15) 60%, transparent 75%);
    filter:blur(18px);
    z-index:0;
    animation: orbPulse 5s ease-in-out infinite;
}}

@keyframes orbPulse{{
    0%,100%{{ opacity:.7; transform:translateX(-50%) scale(1); }}
    50%{{ opacity:1; transform:translateX(-50%) scale(1.08); }}
}}

.title{{
    position:relative;
    z-index:1;
    font-family:'Poppins', sans-serif;
    font-weight:800;
    font-size:46px;
    letter-spacing:-.5px;
    background:linear-gradient(90deg,#7C5CD6,#6FA8DC,#9D7FE0,#7C5CD6);
    background-size:300% auto;
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    margin-bottom:2px;
    animation: shimmerTitle 6s linear infinite;
}}

@keyframes shimmerTitle{{
    0%{{ background-position:0% center; }}
    100%{{ background-position:300% center; }}
}}

.subtitle{{
    position:relative;
    z-index:1;
    color:var(--muted);
    font-size:15.5px;
    font-weight:500;
    letter-spacing:.3px;
    margin-bottom:22px;
}}

.facet-divider{{
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
}}

/* ---------- Glass card (floating) ---------- */

.card{{
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
    animation: floatCard 6s ease-in-out infinite;
}}

@keyframes floatCard{{
    0%,100%{{ transform:translateY(0px); }}
    50%{{ transform:translateY(-7px); }}
}}

.card h3{{
    font-family:'Poppins', sans-serif;
    font-weight:700;
    font-size:19px;
    margin-top:0;
    margin-bottom:4px;
    color:var(--ink);
}}

.card .hint{{
    color:var(--muted);
    font-size:13.5px;
    margin-bottom:18px;
}}

/* ---------- Tabs ---------- */

.stTabs [data-baseweb="tab-list"]{{
    gap:6px;
    background:var(--glass);
    padding:6px;
    border-radius:16px;
    border:1px solid var(--border);
}}

.stTabs [data-baseweb="tab"]{{
    border-radius:12px;
    padding:10px 18px;
    font-weight:600;
    color:var(--muted);
}}

.stTabs [data-baseweb="tab"] p{{ color:inherit !important; }}

.stTabs [aria-selected="true"]{{
    background:linear-gradient(90deg,var(--amethyst),var(--azure));
}}
.stTabs [aria-selected="true"] p{{ color:white !important; }}

/* ---------- Buttons (intentionally white text — high-contrast on gradient) ---------- */

.stButton>button, .stDownloadButton>button{{
    width:100%;
    padding:13px;
    font-size:16px;
    font-weight:600;
    font-family:'Inter', sans-serif;
    border:none;
    border-radius:14px;
    background:linear-gradient(90deg,var(--amethyst),var(--azure));
    color:white !important;
    box-shadow:0 6px 18px rgba(157,127,224,.35);
    transition:transform .15s ease, box-shadow .15s ease;
}}
.stButton>button p, .stDownloadButton>button p{{ color:white !important; }}

.stButton>button:hover, .stDownloadButton>button:hover{{
    transform:translateY(-2px);
    box-shadow:0 10px 24px rgba(157,127,224,.45);
    color:white;
}}

/* ---------- Inputs ---------- */

textarea, .stTextArea textarea{{
    background:var(--input-bg) !important;
    color:var(--ink) !important;
    border-radius:14px !important;
    border:1px solid var(--border) !important;
    font-size:16px !important;
    font-family:'Inter', sans-serif !important;
}}

[data-testid="stFileUploaderDropzone"]{{
    background:var(--input-bg);
    border-radius:14px;
    border:1.5px dashed var(--border);
}}
[data-testid="stFileUploaderDropzone"] *{{ color:var(--ink) !important; }}
[data-testid="stFileUploaderDropzone"] svg{{ fill:var(--amethyst) !important; }}
[data-testid="stFileUploader"] small{{ color:var(--muted) !important; }}

/* uploaded-file chip */
[data-testid="stFileUploaderFile"]{{
    background:var(--glass-strong);
    border-radius:12px;
    border:1px solid var(--border);
    color:var(--ink) !important;
}}
[data-testid="stFileUploaderFile"] *{{ color:var(--ink) !important; }}

.stSelectbox div[data-baseweb="select"] > div{{
    background:var(--input-bg) !important;
    border-radius:12px !important;
    border:1px solid var(--border) !important;
    color:var(--ink) !important;
}}

/* ---------- Badges / status pills ---------- */

.pill{{
    display:inline-block;
    padding:5px 14px;
    border-radius:999px;
    font-size:12.5px;
    font-weight:600;
    background:rgba(157,127,224,.15);
    color:var(--amethyst) !important;
    border:1px solid var(--border);
    margin-bottom:14px;
}}

/* ---------- Sidebar ---------- */

section[data-testid="stSidebar"]{{
    background:{PALETTE["sidebar_bg"]};
    backdrop-filter:blur(16px);
    border-right:1px solid var(--border);
}}
section[data-testid="stSidebar"] *{{ color:var(--ink) !important; }}
section[data-testid="stSidebar"] [data-baseweb="select"] > div{{
    background:var(--input-bg) !important;
    border:1px solid var(--border) !important;
}}

/* ---------- Metric strip ---------- */

.stat-strip{{
    display:flex;
    gap:14px;
    margin-top:14px;
}}
.stat-box{{
    flex:1;
    background:var(--glass-strong);
    border:1px solid var(--border);
    border-radius:14px;
    padding:12px 14px;
    text-align:center;
}}
.stat-box .num{{
    font-family:'Poppins', sans-serif;
    font-weight:700;
    font-size:20px;
    color:var(--amethyst);
}}
.stat-box .lbl{{
    font-size:12px;
    color:var(--muted);
    font-weight:500;
}}

/* ---------- Instant pop-in for "ready" panels & results ---------- */
/* fires the moment Streamlit renders the block, so the reveal itself feels
   immediate even while the mic component is still handing off audio data */

[class*="st-key-record_ready_block"],
[class*="st-key-upload_ready_block"],
[class*="st-key-result_block_"]{{
    animation: popIn .32s cubic-bezier(.22,1,.36,1) both;
}}

@keyframes popIn{{
    0%{{ opacity:0; transform:translateY(10px) scale(.97); }}
    60%{{ opacity:1; transform:translateY(-1px) scale(1.005); }}
    100%{{ opacity:1; transform:translateY(0) scale(1); }}
}}

.pill-pop{{
    animation: pillPop .4s cubic-bezier(.34,1.56,.64,1) both;
}}

@keyframes pillPop{{
    0%{{ opacity:0; transform:scale(.6); }}
    70%{{ opacity:1; transform:scale(1.08); }}
    100%{{ opacity:1; transform:scale(1); }}
}}

/* ---------- Live waveform (ambient listening indicator) ---------- */

.waveform{{
    display:flex;
    gap:5px;
    align-items:center;
    justify-content:center;
    height:44px;
    margin:16px 0 6px 0;
}}
.waveform span{{
    width:6px;
    border-radius:3px;
    background:linear-gradient(180deg,var(--amethyst),var(--azure));
    animation:waveformBounce 1.1s ease-in-out infinite;
}}
.waveform span:nth-child(1){{ height:14px; animation-delay:0s; }}
.waveform span:nth-child(2){{ height:26px; animation-delay:.12s; }}
.waveform span:nth-child(3){{ height:38px; animation-delay:.24s; }}
.waveform span:nth-child(4){{ height:26px; animation-delay:.36s; }}
.waveform span:nth-child(5){{ height:14px; animation-delay:.48s; }}
.waveform span:nth-child(6){{ height:30px; animation-delay:.24s; }}
.waveform span:nth-child(7){{ height:18px; animation-delay:.12s; }}

@keyframes waveformBounce{{
    0%,100%{{ transform:scaleY(.45); opacity:.75; }}
    50%{{ transform:scaleY(1); opacity:1; }}
}}

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
#  SIDEBAR — MODEL SETTINGS (persistent across reruns)
# =====================================================================

with st.sidebar:
    st.markdown("### ⚙️ Transcription Settings")

    theme_choice = st.radio(
        "🌙 Crystal Mode",
        options=["Light", "Dark"],
        index=0 if st.session_state.theme == "light" else 1,
        horizontal=True,
    )
    new_theme = theme_choice.lower()
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()

    st.markdown("---")

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

    use_faster_whisper = st.checkbox(
        "⚡ Use faster-whisper engine",
        value=FASTER_WHISPER_AVAILABLE,
        disabled=not FASTER_WHISPER_AVAILABLE,
        help="CTranslate2-based engine — loads and transcribes several times faster than openai-whisper. "
             "Install with `pip install faster-whisper` if this is greyed out.",
    )

    st.markdown("---")
    st.markdown(
        "<span style='font-size:13px;color:var(--muted);'>"
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
#  MODEL LOADING (cached so it only loads once per size/engine)
# =====================================================================

@st.cache_resource(show_spinner=False)
def load_whisper_model(size: str):
    return whisper.load_model(size)


@st.cache_resource(show_spinner=False)
def load_faster_whisper_model(size: str):
    # int8 compute keeps CPU inference fast without sacrificing much accuracy
    return FasterWhisperModel(size, device="cpu", compute_type="int8")


def transcribe_audio(file_path: str, size: str, lang_code, use_faster: bool):
    if use_faster and FASTER_WHISPER_AVAILABLE:
        model = load_faster_whisper_model(size)
        segments, info = model.transcribe(file_path, language=lang_code)
        text = "".join(seg.text for seg in segments)
        return {"text": text.strip(), "language": info.language or "—"}

    model = load_whisper_model(size)
    options = {}
    if lang_code:
        options["language"] = lang_code
    return model.transcribe(file_path, **options)


def save_temp_audio(raw_bytes: bytes, suffix: str) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(raw_bytes)
        return f.name


def copy_to_clipboard_button(text: str, key: str):
    safe_text = json.dumps(text)
    html_code = f"""
    <button id="copy-btn-{key}" style="
        width:100%;
        padding:13px;
        font-size:16px;
        font-weight:600;
        font-family:'Inter', sans-serif;
        border:none;
        border-radius:14px;
        background:linear-gradient(90deg,#9D7FE0,#6FA8DC);
        color:white;
        cursor:pointer;
        box-shadow:0 6px 18px rgba(157,127,224,.35);
    ">📋 Copy Transcript</button>
    <script>
    const btn = document.getElementById("copy-btn-{key}");
    btn.addEventListener("click", function() {{
        navigator.clipboard.writeText({safe_text}).then(function() {{
            btn.innerText = "✅ Copied!";
            setTimeout(function() {{ btn.innerText = "📋 Copy Transcript"; }}, 1800);
        }});
    }});
    </script>
    """
    components.html(html_code, height=56)


def render_result(result: dict, source_label: str):
    st.toast("Transcription complete", icon="✨")
    result_key = f"{source_label}_{int(time.time())}"

    with st.container(key=f"result_block_{result_key}"):
        st.success(f"✅ Transcribed successfully from {source_label}")

        text = result.get("text", "").strip()
        detected_lang = (result.get("language") or "—").upper()
        word_count = len(text.split()) if text else 0

        st.markdown(f"""
        <div class="stat-strip">
            <div class="stat-box"><div class="num">{word_count}</div><div class="lbl">Words</div></div>
            <div class="stat-box"><div class="num">{detected_lang}</div><div class="lbl">Detected Language</div></div>
            <div class="stat-box"><div class="num">{time.strftime('%H:%M')}</div><div class="lbl">Transcribed At</div></div>
        </div>
        """, unsafe_allow_html=True)

        st.write("")
        st.text_area("📝 Recognized Speech", value=text, height=240, key=f"txt_{result_key}")

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="⬇️ Download (.txt)",
                data=text,
                file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col2:
            copy_to_clipboard_button(text, key=result_key)


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

    st.markdown("""
    <div class="waveform">
        <span></span><span></span><span></span><span></span><span></span><span></span><span></span>
    </div>
    """, unsafe_allow_html=True)

    audio = mic_recorder(
        start_prompt="🎙️ Start Recording",
        stop_prompt="⏹️ Stop Recording",
        just_once=False,
        use_container_width=True,
        format="wav",
        key="recorder",
    )

    if audio:
        with st.container(key="record_ready_block"):
            st.markdown("<span class='pill pill-pop'>🎧 Recording ready</span>", unsafe_allow_html=True)
            st.audio(audio["bytes"])

        if st.button("📨 Transcribe Recording", key="btn_record_send"):
            with st.spinner("💎 Crystal AI is listening..."):
                path = save_temp_audio(audio["bytes"], ".wav")
                try:
                    result = transcribe_audio(
                        path, model_size, LANG_CODES[language_mode], use_faster_whisper
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
        with st.container(key="upload_ready_block"):
            st.markdown("<span class='pill pill-pop'>📁 File ready</span>", unsafe_allow_html=True)
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
                        path, model_size, LANG_CODES[language_mode], use_faster_whisper
                    )
                finally:
                    os.remove(path)

            render_result(result, "uploaded file")

st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
#  FOOTER
# =====================================================================

engine_label = "faster-whisper ⚡" if (use_faster_whisper and FASTER_WHISPER_AVAILABLE) else "OpenAI Whisper"
st.markdown(
    f"<div style='text-align:center;color:var(--muted);font-size:12.5px;padding-top:6px;'>"
    f"Built with 💎 Crystal Voice AI · Powered by {engine_label}"
    f"</div>",
    unsafe_allow_html=True,
)
