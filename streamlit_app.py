import html
import json
import os
import tempfile

import requests
import streamlit as st
from faster_whisper import WhisperModel


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="MeetIQ",
    page_icon="🎙️",
    layout="wide"
)


# ============================================================
# CONFIGURATION
# ============================================================

WHISPER_MODEL = os.getenv(
    "MEETIQ_WHISPER_MODEL",
    "base"
)

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:3b"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        background-color: #f7f8fc;
    }

    .title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 0;
    }

    .subtitle {
        font-size: 18px;
        color: #666666;
        margin-bottom: 30px;
    }

    .section-title {
        font-size: 25px;
        font-weight: 650;
        margin-top: 25px;
        margin-bottom: 15px;
    }

    .card {
        background: white;
        padding: 22px;
        border-radius: 15px;
        border: 1px solid #e5e5e5;
        margin-bottom: 15px;
    }

    .topic {
        display: inline-block;
        padding: 8px 15px;
        margin: 4px;
        border-radius: 20px;
        background: #eef1f7;
        font-size: 14px;
    }

    .action {
        background: white;
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #e5e5e5;
        margin-bottom: 12px;
    }

    .issue {
        background: white;
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #e5e5e5;
        margin-bottom: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="title">🎙️ MeetIQ</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Turn conversations into insights.</div>',
    unsafe_allow_html=True
)


# ============================================================
# LOAD WHISPER MODEL
# ============================================================

@st.cache_resource
def load_whisper_model():

    return WhisperModel(
        WHISPER_MODEL,
        device="cpu",
        compute_type="int8"
    )


# ============================================================
# CHECK OLLAMA
# ============================================================

def check_ollama():

    try:

        response = requests.get(
            f"{OLLAMA_URL}/api/tags",
            timeout=5
        )

        response.raise_for_status()

        return True

    except Exception:

        return False


# ============================================================
# TRANSCRIPTION
# ============================================================

def transcribe_meeting(uploaded_file):

    with st.spinner("🎙️ Transcribing meeting..."):

        suffix = os.path.splitext(
            uploaded_file.name
        )[1]

        temp_path = None

        try:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix
            ) as temp_file:

                temp_file.write(
                    uploaded_file.getvalue()
                )

                temp_path = temp_file.name

            # Load Faster-Whisper
            model = load_whisper_model()

            # Transcribe
            segments, info = model.transcribe(
                temp_path,
                beam_size=5,
                vad_filter=True
            )

            transcript_parts = []

            for segment in segments:

                text = segment.text.strip()

                if text:

                    transcript_parts.append(text)

            transcript = " ".join(
                transcript_parts
            )

            if not transcript.strip():

                raise RuntimeError(
                    "No speech could be detected in the recording."
                )

            return transcript

        finally:

            if temp_path and os.path.exists(temp_path):

                os.remove(temp_path)


# ============================================================
# BUILD QWEN PROMPT
# ============================================================

def build_analysis_prompt(transcript):

    return f"""
You are MeetIQ, an AI Meeting Intelligence system.

Analyze the meeting transcript below.

IMPORTANT RULES:

1. Extract ONLY information actually present in the transcript.
2. Do NOT invent people.
3. Do NOT invent decisions.
4. Do NOT invent deadlines.
5. Do NOT invent action items.
6. Do NOT invent topics.
7. If an owner is not mentioned, use an empty string.
8. If a deadline is not mentioned, use an empty string.
9. If a category has no information, return an empty array.
10. Return ONLY valid JSON.
11. Do not include markdown.
12. Do not include ```json.
13. Keep the summary concise but informative.

Return exactly this structure:

{{
    "summary": "A concise summary of the meeting",

    "key_topics": [
        "topic 1",
        "topic 2"
    ],

    "decisions": [
        "decision 1",
        "decision 2"
    ],

    "action_items": [
        {{
            "task": "task description",
            "owner": "person responsible",
            "deadline": "deadline"
        }}
    ],

    "unresolved_issues": [
        "issue 1",
        "issue 2"
    ]
}}

MEETING TRANSCRIPT:

{transcript}
"""


# ============================================================
# ANALYZE MEETING WITH QWEN
# ============================================================

def analyze_meeting(transcript):

    if not check_ollama():

        raise RuntimeError(
            "Ollama is not running. "
            "Please start Ollama and make sure "
            "qwen2.5:3b is available."
        )

    prompt = build_analysis_prompt(
        transcript
    )

    with st.spinner("🧠 Analyzing meeting with Qwen..."):

        response = requests.post(

            f"{OLLAMA_URL}/api/generate",

            json={
                "model": OLLAMA_MODEL,

                "prompt": prompt,

                "stream": False,

                "format": "json",

                "options": {
                    "temperature": 0.2
                }
            },

            timeout=300
        )

        response.raise_for_status()

        result = response.json()

        content = result.get(
            "response",
            ""
        )

        if not content:

            raise RuntimeError(
                "Qwen returned an empty response."
            )

        try:

            analysis = json.loads(
                content
            )

        except json.JSONDecodeError:

            # Try to extract JSON if Qwen
            # accidentally added extra text.

            start = content.find("{")
            end = content.rfind("}")

            if start == -1 or end == -1:

                raise RuntimeError(
                    "Qwen returned invalid JSON."
                )

            json_text = content[
                start:end + 1
            ]

            analysis = json.loads(
                json_text
            )

        return analysis


# ============================================================
# CLEAN HTML
# ============================================================

def clean(value):

    return html.escape(
        str(value or "")
    )


# ============================================================
# DISPLAY RESULTS
# ============================================================

def display_results(analysis):

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">📋 Meeting Summary</div>',
        unsafe_allow_html=True
    )

    summary = analysis.get(
        "summary",
        "No summary available."
    )

    st.markdown(
        f"""
        <div class="card">
            {clean(summary)}
        </div>
        """,
        unsafe_allow_html=True
    )


    # --------------------------------------------------------
    # KEY TOPICS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">🔑 Key Topics</div>',
        unsafe_allow_html=True
    )

    topics = analysis.get(
        "key_topics",
        []
    )

    if topics:

        topic_html = ""

        for topic in topics:

            topic_html += (
                f'<span class="topic">'
                f'{clean(topic)}'
                f'</span>'
            )

        st.markdown(
            topic_html,
            unsafe_allow_html=True
        )

    else:

        st.info(
            "No key topics identified."
        )


    # --------------------------------------------------------
    # DECISIONS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">✅ Decisions</div>',
        unsafe_allow_html=True
    )

    decisions = analysis.get(
        "decisions",
        []
    )

    if decisions:

        for decision in decisions:

            st.markdown(
                f"""
                <div class="card">
                    ✓ {clean(decision)}
                </div>
                """,
                unsafe_allow_html=True
            )

    else:

        st.info(
            "No decisions identified."
        )


    # --------------------------------------------------------
    # ACTION ITEMS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">📌 Action Items</div>',
        unsafe_allow_html=True
    )

    actions = analysis.get(
        "action_items",
        []
    )

    if actions:

        for action in actions:

            task = action.get(
                "task",
                ""
            )

            owner = action.get(
                "owner",
                ""
            )

            deadline = action.get(
                "deadline",
                ""
            )

            st.markdown(
                f"""
                <div class="action">

                <b>Task:</b>
                {clean(task)}
                <br><br>

                <b>Owner:</b>
                {clean(owner) if owner else "Not specified"}
                <br><br>

                <b>Deadline:</b>
                {clean(deadline) if deadline else "Not specified"}

                </div>
                """,
                unsafe_allow_html=True
            )

    else:

        st.info(
            "No action items identified."
        )


    # --------------------------------------------------------
    # UNRESOLVED ISSUES
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">⚠️ Unresolved Issues</div>',
        unsafe_allow_html=True
    )

    issues = analysis.get(
        "unresolved_issues",
        []
    )

    if issues:

        for issue in issues:

            st.markdown(
                f"""
                <div class="issue">
                    ⚠️ {clean(issue)}
                </div>
                """,
                unsafe_allow_html=True
            )

    else:

        st.success(
            "No unresolved issues identified."
        )


# ============================================================
# UPLOAD SECTION
# ============================================================

st.markdown(
    '<div class="section-title">🎙️ Add Your Meeting</div>',
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader(

    "Upload your meeting recording",

    type=[
        "wav",
        "mp3",
        "m4a",
        "mp4",
        "webm",
        "mpeg",
        "mpga",
        "ogg"
    ]
)


# ============================================================
# PROCESS UPLOADED MEETING
# ============================================================

if uploaded_file:

    st.success(
        f"Uploaded: {uploaded_file.name}"
    )

    st.audio(
        uploaded_file
    )

    if st.button(
        "🚀 Analyze Meeting",
        use_container_width=True
    ):

        try:

            # =================================================
            # STEP 1: SPEECH → TEXT
            # =================================================

            transcript = transcribe_meeting(
                uploaded_file
            )

            st.session_state[
                "transcript"
            ] = transcript


            # =================================================
            # STEP 2: TEXT → MEETING INTELLIGENCE
            # =================================================

            analysis = analyze_meeting(
                transcript
            )

            st.session_state[
                "analysis"
            ] = analysis

            st.success(
                "✅ Meeting analysis completed!"
            )

        except requests.exceptions.ConnectionError:

            st.error(
                "❌ Cannot connect to Ollama. "
                "Please make sure Ollama is running."
            )

        except requests.exceptions.Timeout:

            st.error(
                "❌ Ollama took too long to respond. "
                "Please try again."
            )

        except Exception as error:

            st.error(
                f"❌ Error while processing meeting: {error}"
            )


# ============================================================
# SHOW ANALYSIS
# ============================================================

if "analysis" in st.session_state:

    st.divider()

    display_results(
        st.session_state["analysis"]
    )


# ============================================================
# SHOW TRANSCRIPT
# ============================================================

if "transcript" in st.session_state:

    st.divider()

    with st.expander(
        "📝 View Full Transcript"
    ):

        st.text_area(
            "Meeting Transcript",
            st.session_state["transcript"],
            height=400
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "MeetIQ • AI Meeting Intelligence Platform • "
    "Local AI with Faster-Whisper + Ollama + Qwen"
)
