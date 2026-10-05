import json
import sys
from pathlib import Path
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ============================================================
# SETTINGS
# ============================================================

TRANSCRIPT_FILE = Path("transcripts/transcript.txt")

OUTPUT_FOLDER = Path("meeting_output")
OUTPUT_FILE = OUTPUT_FOLDER / "meeting_analysis.json"

OLLAMA_URL = "http://localhost:11434/api/generate"

MODEL_NAME = "qwen2.5:3b"


# ============================================================
# LOAD TRANSCRIPT
# ============================================================

def load_transcript():

    if not TRANSCRIPT_FILE.exists():
        raise FileNotFoundError(
            f"Transcript not found: {TRANSCRIPT_FILE}"
        )

    with open(
        TRANSCRIPT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()


# ============================================================
# ANALYZE MEETING
# ============================================================

def analyze_meeting(transcript):

    prompt = f"""
You are MeetIQ, an AI meeting intelligence assistant.

Analyze the following meeting transcript.

Extract ONLY information that is actually present in the transcript.

IMPORTANT:
- Return structured JSON.
- Do not return markdown.
- Do not put JSON inside a string.
- Do not create extra fields.
- Do not invent names, decisions, deadlines, or tasks.
- If information is not present, use an empty array.
- Keep the summary as normal human-readable text.

The required structure is:

summary:
A short paragraph describing what the meeting was mainly about.

key_topics:
The main subjects discussed.

decisions:
Decisions that participants actually agreed upon.

action_items:
Tasks that participants agreed someone should do.

unresolved_issues:
Problems or questions that were left unresolved.

MEETING TRANSCRIPT:

{transcript}
"""

    # ========================================================
    # JSON SCHEMA
    # ========================================================

    schema = {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string"
            },

            "key_topics": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },

            "decisions": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },

            "action_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string"
                        },
                        "owner": {
                            "type": "string"
                        },
                        "deadline": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "task",
                        "owner",
                        "deadline"
                    ]
                }
            },

            "unresolved_issues": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            }
        },

        "required": [
            "summary",
            "key_topics",
            "decisions",
            "action_items",
            "unresolved_issues"
        ]
    }

    # ========================================================
    # CALL LOCAL QWEN
    # ========================================================

    response = requests.post(
        OLLAMA_URL,

        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,

            # IMPORTANT:
            # Tell Ollama exactly what JSON structure to produce.
            "format": schema,

            "options": {
                "temperature": 0
            }
        },

        timeout=600
    )

    response.raise_for_status()

    result = response.json()

    return result["response"]


# ============================================================
# VALIDATE JSON
# ============================================================

def validate_analysis(analysis):

    required_fields = [
        "summary",
        "key_topics",
        "decisions",
        "action_items",
        "unresolved_issues"
    ]

    for field in required_fields:

        if field not in analysis:
            raise ValueError(
                f"Missing required field: {field}"
            )

    return True


# ============================================================
# SAVE JSON
# ============================================================

def save_analysis(raw_result):

    try:
        analysis = json.loads(raw_result)

    except json.JSONDecodeError:

        print("\n❌ Qwen returned invalid JSON.")
        print(raw_result)

        return None

    # ========================================================
    # VALIDATE REQUIRED FIELDS
    # ========================================================

    required_fields = [
        "summary",
        "key_topics",
        "decisions",
        "action_items",
        "unresolved_issues"
    ]

    for field in required_fields:

        if field not in analysis:

            print(
                f"\n❌ Missing field: {field}"
            )

            print("\nRaw response:")
            print(raw_result)

            return None

    # ========================================================
    # SAVE
    # ========================================================

    OUTPUT_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            analysis,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(
        "\n✅ MeetIQ analysis saved successfully."
    )

    return analysis


# ============================================================
# DISPLAY RESULTS
# ============================================================

def display_analysis(analysis):

    print("\n")
    print("=" * 60)
    print("             MeetIQ MEETING ANALYSIS")
    print("=" * 60)

    print("\n📋 SUMMARY")
    print("-" * 60)

    print(analysis["summary"])

    print("\n🔑 KEY TOPICS")
    print("-" * 60)

    for topic in analysis["key_topics"]:
        print(f"• {topic}")

    print("\n✅ DECISIONS")
    print("-" * 60)

    if analysis["decisions"]:

        for decision in analysis["decisions"]:
            print(f"• {decision}")

    else:
        print("No decisions identified.")

    print("\n🎯 ACTION ITEMS")
    print("-" * 60)

    if analysis["action_items"]:

        for item in analysis["action_items"]:

            print(
                f"• Task: {item.get('task', 'Unknown')}"
            )

            print(
                f"  Owner: {item.get('owner', 'Unknown')}"
            )

            print(
                f"  Deadline: "
                f"{item.get('deadline', 'Unknown')}"
            )

    else:

        print("No action items identified.")

    print("\n⚠️ UNRESOLVED ISSUES")
    print("-" * 60)

    if analysis["unresolved_issues"]:

        for issue in analysis["unresolved_issues"]:
            print(f"• {issue}")

    else:

        print("No unresolved issues identified.")

    print("\n")
    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n")
    print("=" * 60)
    print("              MeetIQ AI ANALYZER")
    print("=" * 60)

    print("\nLoading transcript...")

    transcript = load_transcript()

    print(
        f"Transcript loaded: "
        f"{len(transcript)} characters"
    )

    print("\nSending transcript to local Qwen model...")

    raw_result = analyze_meeting(
        transcript
    )

    print("\nAnalysis received.")

    print("\n========== RAW QWEN RESPONSE ==========\n")
    print(raw_result)
    print("\n========================================\n")

    analysis = save_analysis(
        raw_result
    )

    if analysis is not None:

        display_analysis(
            analysis
        )

        print(
            f"\nSaved to: {OUTPUT_FILE}"
        )

    else:

        print(
            "\n❌ Analysis was not saved because "
            "the JSON structure was invalid."
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()