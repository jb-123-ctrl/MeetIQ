from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

os.environ["PYTHONUTF8"] = "1"


app = FastAPI(
    title="MeetIQ API",
    description="AI Meeting Intelligence Backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_FOLDER = BASE_DIR / "uploads"

OUTPUT_FOLDER = BASE_DIR / "meeting_output"

ANALYSIS_FILE = OUTPUT_FOLDER / "meeting_analysis.json"

TRANSCRIPT_FILE = BASE_DIR / "transcripts" / "transcript.txt"

UPLOAD_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "application": "MeetIQ",
        "status": "running",
        "message": "MeetIQ AI Meeting Intelligence API"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ============================================================
# GET ANALYSIS
# ============================================================

@app.get("/analysis")
def get_analysis():

    if not ANALYSIS_FILE.exists():

        return {
            "message": "No meeting has been processed yet."
        }

    with open(
        ANALYSIS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# GET TRANSCRIPT
# ============================================================

@app.get("/transcript")
def get_transcript():

    if not TRANSCRIPT_FILE.exists():

        return {
            "message": "No transcript available."
        }

    with open(
        TRANSCRIPT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        transcript = file.read()

    return {
        "transcript": transcript
    }


# ============================================================
# PROCESS MEETING
# ============================================================

@app.post("/process-meeting")
async def process_meeting(
    file: UploadFile = File(...)
):

    try:

        if not file.filename:

            return {
                "success": False,
                "error": "No file selected."
            }

        extension = Path(
            file.filename
        ).suffix.lower()

        allowed_extensions = [
            ".wav",
            ".mp3",
            ".m4a",
            ".mp4",
            ".webm",
            ".ogg"
        ]

        if extension not in allowed_extensions:

            return {
                "success": False,
                "error": (
                    "Unsupported audio format. "
                    "Use WAV, MP3, M4A, MP4, WEBM or OGG."
                )
            }

        uploaded_file = (
            UPLOAD_FOLDER / f"current_meeting{extension}"
        )

        with open(
            uploaded_file,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        print(
            f"\nReceived meeting: "
            f"{uploaded_file.name}"
        )

        print("\nStarting transcription...")

        transcription_process = subprocess.run(
            [
                sys.executable,
                str(BASE_DIR / "transcription.py"),
                str(uploaded_file)
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(BASE_DIR)
        )

        if transcription_process.returncode != 0:

            print("========== TRANSCRIPTION ERROR ==========")
            print("Return code:", transcription_process.returncode)
            print("Transcription process failed.")
            print("=========================================\n")

            return {
                "success": False,
                "error": "Transcription failed.",
                "details": transcription_process.stderr[-2000:]
            }

        print("\nTranscription completed.")
        print("\nStarting AI meeting analysis...")

        analysis_process = subprocess.run(
            [
                sys.executable,
                str(BASE_DIR / "meeting_analyzer.py")
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            cwd=str(BASE_DIR)
        )

        if analysis_process.returncode != 0:

            print(
                analysis_process.stderr
            )

            return {
                "success": False,
                "error": "Meeting analysis failed.",
                "details": analysis_process.stderr
            }

        print("\nMeeting analysis completed.")

        if not ANALYSIS_FILE.exists():

            return {
                "success": False,
                "error": (
                    "Analysis completed but "
                    "JSON result was not created."
                )
            }

        with open(
            ANALYSIS_FILE,
            "r",
            encoding="utf-8"
        ) as analysis_file:

            analysis = json.load(analysis_file)

        return {
            "success": True,
            "filename": file.filename,
            "analysis": analysis
        }

    except Exception as error:

        print("\nPROCESSING ERROR:")
        print(error)

        return {
            "success": False,
            "error": str(error)
        }
