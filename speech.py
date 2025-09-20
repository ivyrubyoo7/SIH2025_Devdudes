# My rice crop leaves are turning yellow, is it due to lack of nitrogen? i
import queue
import sounddevice as sd
import numpy as np
import torch
from faster_whisper import WhisperModel
import vosk
import json
import datetime
import spacy

SAMPLE_RATE = 16000
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print("Loading Whisper model (for audio preprocessing)...")
whisper_model = WhisperModel("base", device=DEVICE, compute_type="int8")

print("Loading Vosk model (for transcription)...")
vosk_model = vosk.Model(r"D:\\Download\\vosk-model-small-en-us-0.15\\vosk-model-small-en-us-0.15")
vosk_recognizer = vosk.KaldiRecognizer(vosk_model, SAMPLE_RATE)

print("Loading spaCy model (for tokenization)...")
nlp = spacy.load("en_core_web_sm")

# Queue for audio chunks
q = queue.Queue()

# Store transcripts
transcript_log = {
    "session_start": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "transcriptions": []
}

# AUDIO CALLBACK
def audio_callback(indata, frames, time, status):
    if status:
        print(status, flush=True)
    q.put(bytes(indata))

# Custom entity extraction
def extract_entities(text: str):
    text_lower = text.lower()
    entities = []

    # Crop detection
    if "rice" in text_lower:
        entities.append("crop: rice")
    if "wheat" in text_lower:
        entities.append("crop: wheat")
    if "maize" in text_lower or "corn" in text_lower:
        entities.append("crop: maize")

    # Plant part detection
    if "leaf" in text_lower or "leaves" in text_lower:
        entities.append("plant_part: leaves")
    if "stem" in text_lower:
        entities.append("plant_part: stem")
    if "root" in text_lower or "roots" in text_lower:
        entities.append("plant_part: roots")

    # Symptom detection
    if "yellow" in text_lower or "yellowing" in text_lower:
        entities.append("symptom: yellowing")
    if "brown" in text_lower or "spot" in text_lower:
        entities.append("symptom: brown spots")
    if "wilting" in text_lower:
        entities.append("symptom: wilting")

    # Cause detection
    if "nitrogen" in text_lower:
        entities.append("cause: nitrogen deficiency")
    if "pest" in text_lower or "insect" in text_lower:
        entities.append("cause: pest attack")
    if "fungus" in text_lower or "fungal" in text_lower:
        entities.append("cause: fungal infection")

    return entities

# REALTIME TRANSCRIPTION
def real_time_transcribe():
    print("🎤 Speak into your microphone... (Ctrl+C to stop)")
    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000, dtype="int16",
                           channels=1, callback=audio_callback):

        while True:
            data = q.get()

            # ---------- Preprocess with Whisper ----------
            audio_array = np.frombuffer(data, np.int16).astype(np.float32) / 32768.0
            _ = whisper_model.transcribe(audio_array, language="en")

            # ---------- Send to Vosk ----------
            if vosk_recognizer.AcceptWaveform(data):
                vosk_result = json.loads(vosk_recognizer.Result())
                if vosk_result.get("text"):
                    text = vosk_result["text"]
                    print(f"[Transcription] {text}")

                    # Run domain-specific entity extraction
                    entities = extract_entities(text)
                    if entities:
                        print(f"🔎 Entities found: {entities}")

                    # Save into JSON log
                    transcript_log["transcriptions"].append({
                        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                        "text": text,
                        "entities": entities
                    })

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    try:
        real_time_transcribe()
    except KeyboardInterrupt:
        print("\n🛑 Stopping... Saving transcript.")
        transcript_log["session_end"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save JSON
        with open("transcript_log.json", "w", encoding="utf-8") as f:
            json.dump(transcript_log, f, indent=4, ensure_ascii=False)

        print("💾 Transcript saved as transcript_log.json")
