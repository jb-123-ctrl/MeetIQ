import json
import os
import tempfile

import streamlit as st
from openai import OpenAI


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="MeetIQ",
    page_icon="🎙️",
    layout="wide"
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
# OPENAI CLIENT
# ============================================================

def get_client():

    # Streamlit Cloud
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:

        st.error(
            "OpenAI API key is missing. "
            "Add OPENAI_API_KEY to Streamlit Secrets."
        )

        st.stop()

    return OpenAI(api_key=api_key)


# ============================================================
# TRANSCRIPTION
# ============================================================

def transcribe_meeting(client, uploaded_file):

    with st.spinner("🎙️ Transcribing meeting..."):

        # Create temporary file
        suffix = os.path.splitext(
            uploaded_file.name
        )[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp_file:

            temp_file.write(
                uploaded_file.getvalue()
            )

            temp_path = temp_file.name

        try:

            with open(
                temp_path,
                "rb"
            ) as audio_file:

                result = client.audio.transcriptions.create(
                    model="gpt-4o-transcribe",
                    file=audio_file
                )

            transcript = result.text

        finally:

            if os.path.exists(temp_path):
                os.remove(temp_path)

    return transcript


# ============================================================
# AI MEETING ANALYSIS
# ============================================================

def analyze_meeting(client, transcript):

    prompt = f"""
You are MeetIQ, an AI Meeting Intelligence system.

Analyze the meeting transcript below.

Extract ONLY information that is actually present.

Do NOT invent:
- people
- decisions
- deadlines
- action items
- topics

If an owner or deadline is not mentioned,
use an empty string.

If a category has no information,
return an empty array.

Return ONLY valid JSON.

Required format:

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

    with st.spinner("🧠 Analyzing meeting..."):

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a meeting intelligence "
                        "assistant. Return only valid JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={
                "type": "json_object"
            },
            temperature=0.2
        )

    content = response.choices[0].message.content

    return json.loads(content)


# ============================================================
# DISPLAY SUMMARY
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
            {summary}
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
                f'<span class="topic">{topic}</span>'
            )

        st.markdown(
            topic_html,
            unsafe_allow_html=True
        )

    else:

        st.info("No key topics identified.")


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
                    ✓ {decision}
                </div>
                """,
                unsafe_allow_html=True
            )

    else:

        st.info("No decisions identified.")


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

                <b>Task:</b> {task}<br><br>

                <b>Owner:</b>
                {owner if owner else "Not specified"}<br><br>

                <b>Deadline:</b>
                {deadline if deadline else "Not specified"}

                </div>
                """,
                unsafe_allow_html=True
            )

    else:

        st.info("No action items identified.")


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
                    ⚠️ {issue}
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
        "mpga"
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

        client = get_client()

        try:

            # STEP 1
            transcript = transcribe_meeting(
                client,
                uploaded_file
            )

            st.session_state[
                "transcript"
            ] = transcript


            # STEP 2
            analysis = analyze_meeting(
                client,
                transcript
            )

            st.session_state[
                "analysis"
            ] = analysis

            st.success(
                "✅ Meeting analysis completed!"
            )

        except Exception as error:

            st.error(
                f"Error while processing meeting: {error}"
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
    "MeetIQ • AI Meeting Intelligence Platform"
)
