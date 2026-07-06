# ============================================================
#  config.py  —  스마트 화분 설정값 모음
# ============================================================

# ── OLED 디스플레이 (SPI) ──────────────────────────────────
DISPLAY_WIDTH      = 128
DISPLAY_HEIGHT     = 64
DISPLAY_SPI_PORT   = 0
DISPLAY_SPI_DEVICE = 0
DISPLAY_DC_PIN     = 24   # GPIO24
DISPLAY_RESET_PIN  = 25   # GPIO25

# ── 센서 ──────────────────────────────────────────────────
MOISTURE_ADC_CHANNEL = 0  # MCP3008 CH0
MOISTURE_DRY   = 600      # 이 값 이상이면 "건조"
MOISTURE_WET   = 300      # 이 값 이하면 "과습"

LIGHT_I2C_ADDR = 0x23     # BH1750 기본 주소
LIGHT_LOW_LUX  = 200      # 이 값 이하면 햇빛 부족

TEMP_GPIO_PIN  = 4        # DHT22 데이터 핀 (GPIO4)
TEMP_HOT       = 32       # 이 값 이상이면 "너무 더움"

# ── AI 스피커 (Ollama 로컬 LLM + Whisper 로컬 STT + Piper TTS) ──
OLLAMA_HOST    = "http://localhost:11434"  # Ollama 서버 주소
OLLAMA_MODEL   = "gemma4"                 # 설치한 모델명
WHISPER_MODEL  = "base"                   # tiny / base / small / medium
TTS_MODEL      = "piper"                  # 로컬 TTS
GPT_SYSTEM_PROMPT = (
    "너는 스마트 화분 안에 사는 식물 요정이야. "
    "사용자의 식물을 돌봐주고, 친근하고 귀엽게 대화해줘. "
    "항상 짧고 따뜻하게 두 문장 이내로 답변해."
)

# ── LED 조명 (WS2812B) ────────────────────────────────────
LED_PIN   = 18   # GPIO18 (PWM)
LED_COUNT = 12   # LED 개수

# ── 업데이트 주기 ─────────────────────────────────────────
SENSOR_INTERVAL = 30   # 초: 센서 읽기 주기
DISPLAY_FPS     = 10   # 표정 애니메이션 FPS
