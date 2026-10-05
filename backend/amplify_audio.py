import wave
import struct

INPUT_FILE = "uploads/ES2008a.Mix-Headset.wav"
OUTPUT_FILE = "uploads/ES2008a.Mix-Headset-amplified.wav"

TARGET_PEAK = 30000
MAX_INT16 = 32767


def find_peak():
    with wave.open(INPUT_FILE, "rb") as wav:
        if wav.getsampwidth() != 2:
            raise ValueError("This script expects 16-bit audio.")

        peak = 0

        while True:
            data = wav.readframes(8192)

            if not data:
                break

            samples = struct.unpack(
                "<" + "h" * (len(data) // 2),
                data
            )

            chunk_peak = max(abs(x) for x in samples)

            if chunk_peak > peak:
                peak = chunk_peak

    return peak


def amplify(peak):

    if peak == 0:
        raise ValueError("Audio is completely silent.")

    gain = TARGET_PEAK / peak

    # Maximum 10x amplification
    gain = min(gain, 10)

    print("Original peak:", peak)
    print(f"Amplification: {gain:.2f}x")

    with wave.open(INPUT_FILE, "rb") as source:

        params = source.getparams()

        with wave.open(OUTPUT_FILE, "wb") as output:

            output.setparams(params)

            while True:

                data = source.readframes(8192)

                if not data:
                    break

                samples = struct.unpack(
                    "<" + "h" * (len(data) // 2),
                    data
                )

                amplified = []

                for sample in samples:

                    value = int(sample * gain)

                    value = max(
                        -MAX_INT16,
                        min(MAX_INT16, value)
                    )

                    amplified.append(value)

                output.writeframes(
                    struct.pack(
                        "<" + "h" * len(amplified),
                        *amplified
                    )
                )

    print("\nDone!")
    print("Created:", OUTPUT_FILE)


if __name__ == "__main__":

    peak = find_peak()
    amplify(peak)