# ============================================================
#  speaker.py  —  AI 스피커 (Whisper 로컬 STT + Ollama LLM + pyttsx3 TTS)
# ============================================================
import os
import tempfile
import subprocess
import config

try:
    import whisper
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
    _AUDIO_OK = True
except ImportError:
    _AUDIO_OK = False
    print("[speaker] 오디오 라이브러리 없음 — 시뮬레이션 모드")

try:
    import requests
    _REQUESTS_OK = True
except ImportError:
    _REQUESTS_OK = False

try:
    import pyttsx3
    _TTS_OK = True
except ImportError:
    _TTS_OK = False
    print("[speaker] pyttsx3 없음 — TTS 텍스트 출력으로 대체")

SAMPLE_RATE    = 16000
RECORD_SECONDS = 5


class SpeakerManager:
    def __init__(self):
        self._on_speaking_cb = None
        # Whisper 모델 로드 (최초 1회, 로컬 실행)
        if _AUDIO_OK:
            print("[speaker] Whisper 모델 로딩 중...")
            self._whisper = whisper.load_model(config.WHISPER_MODEL)
            print("[speaker] Whisper 준비 완료")
        # TTS 엔진
        if _TTS_OK:
            self._tts = pyttsx3.init()
            self._tts.setProperty("rate", 160)

    def on_speaking(self, callback):
        self._on_speaking_cb = callback

    def listen(self) -> str:
        """마이크 녹음 → Whisper로 텍스트 변환 (완전 로컬)"""
        if not _AUDIO_OK:
            return input("[speaker] 텍스트 입력 (시뮬레이션): ")

        print("[speaker] 듣는 중... (5초)")
        audio = sd.rec(int(RECORD_SECONDS * SAMPLE_RATE),
                       samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        sd.wait()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, audio, SAMPLE_RATE)
            tmp_path = f.name

        result = self._whisper.transcribe(tmp_path, language="ko")
        os.unlink(tmp_path)
        text = result["text"].strip()
        print(f"[speaker] 인식: {text}")
        return text

    def think(self, user_text: str, plant_state: str) -> str:
        """Ollama로 답변 생성 (로컬 LLM)"""
        if not _REQUESTS_OK:
            return f"안녕! 지금 식물 상태는 '{plant_state}'야."

        system = config.GPT_SYSTEM_PROMPT + f" 현재 식물 상태: {plant_state}."
        try:
            resp = requests.post(
                f"{config.OLLAMA_HOST}/api/chat",
                json={
                    "model": config.OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user",   "content": user_text},
                    ],
                    "stream": False,
                },
                timeout=30,
            )
            answer = resp.json()["message"]["content"].strip()
        except Exception as e:
            answer = "지금 잠깐 생각이 안 나네요. 다시 말해줄래요?"
            print(f"[speaker] Ollama 오류: {e}")
        print(f"[speaker] 답변: {answer}")
        return answer

    def speak(self, text: str):
        """pyttsx3으로 텍스트 음성 출력 (로컬 TTS)"""
        if self._on_speaking_cb:
            self._on_speaking_cb()

        if not _TTS_OK:
            print(f"[speaker] TTS: {text}")
            return

        self._tts.say(text)
        self._tts.runAndWait()

    def handle_interaction(self, plant_state: str):
        """듣기 → 생각 → 말하기 전체 흐름"""
        user_text = self.listen()
        if not user_text:
            return
        answer = self.think(user_text, plant_state)
        self.speak(answer)
