import sys

from faster_whisper import WhisperModel
from pathlib import Path

# ============================================================
# SETTINGS
# ============================================================

AUDIO_FILE = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else Path("uploads/ES2008a.Mix-Headset.wav")
)

OUTPUT_FOLDER = Path("transcripts")

OUTPUT_FILE = OUTPUT_FOLDER / "transcript.txt"

# Model options:
# tiny  = fastest, lowest accuracy
# base  = fast, good starting point
# small = better accuracy, slower
# medium = better accuracy, much slower

MODEL_SIZE = "small"

# ============================================================
# TRANSCRIPTION
# ============================================================

def transcribe_audio():

    print("\n========================================")
    print("       MeetIQ - LOCAL TRANSCRIPTION")
    print("========================================")

    if not AUDIO_FILE.exists():
        raise FileNotFoundError(
            f"Audio file not found: {AUDIO_FILE}"
        )

    print("\nAudio file:")
    print("Audio file loaded successfully.")

    print("\nLoading Whisper model...")
    print(f"Model: {MODEL_SIZE}")
    print("Device: CPU")
    print("Compute type: int8")

    model = WhisperModel(
        MODEL_SIZE,
        device="cpu",
        compute_type="int8"
    )

    print("\nModel loaded successfully.")

    print("\nStarting transcription...")
    print("Please wait. This may take some time.")

    segments, info = model.transcribe(
        str(AUDIO_FILE),
        beam_size=5,
        vad_filter=True
    )

    OUTPUT_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    transcript_lines = []

    print("\n========================================")
    print("          TRANSCRIPT")
    print("========================================\n")

    for segment in segments:

        start = segment.start
        end = segment.end
        text = segment.text.strip()

        line = (
            f"[{start:.2f}s - {end:.2f}s] {text}"
        )

        print(line)

        transcript_lines.append(line)

    # ========================================================
    # SAVE TRANSCRIPT
    # ========================================================

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write("\n".join(transcript_lines))

    print("\n========================================")
    print("       TRANSCRIPTION COMPLETE")
    print("========================================")

    print(f"\nSaved transcript to:")
    print(OUTPUT_FILE)

# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    transcribe_audio()