import wave
import audioop
import os

audio_path = "uploads/ES2008a.Mix-Headset.wav"

print("Checking:", audio_path)

with wave.open(audio_path, "rb") as wav:
    channels = wav.getnchannels()
    sample_width = wav.getsampwidth()
    sample_rate = wav.getframerate()
    frames = wav.getnframes()
    duration = frames / sample_rate

    print("\n========== AUDIO INFO ==========")
    print("Channels:", channels)
    print("Sample width:", sample_width, "bytes")
    print("Sample rate:", sample_rate, "Hz")
    print("Frames:", frames)
    print("Duration:", round(duration, 2), "seconds")

    # Read the entire audio
    audio_data = wav.readframes(frames)

    # Measure signal volume
    rms = audioop.rms(audio_data, sample_width)

    print("RMS:", rms)

    print("\n========== RESULT ==========")

    if rms == 0:
        print("❌ SILENT AUDIO")
        print("The WAV contains no measurable audio signal.")
    elif rms < 100:
        print("⚠️ VERY LOW AUDIO SIGNAL")
    else:
        print("✅ AUDIO SIGNAL DETECTED")