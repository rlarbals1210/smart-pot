# ============================================================
#  sensors.py  —  수분 / 조도 / 온습도 센서
# ============================================================
import time
import config

# ── 라즈베리파이 실제 환경에서만 임포트 ──────────────────
try:
    import board, busio
    import adafruit_dht
    import adafruit_bh1750
    import spidev
    _REAL_HW = True
except ImportError:
    _REAL_HW = False
    print("[sensors] 하드웨어 라이브러리 없음 — 시뮬레이션 모드")


class SensorManager:
    def __init__(self):
        if _REAL_HW:
            # DHT22 온습도
            self.dht = adafruit_dht.DHT22(getattr(board, f"D{config.TEMP_GPIO_PIN}"))
            # BH1750 조도 (I2C)
            i2c = busio.I2C(board.SCL, board.SDA)
            self.light = adafruit_bh1750.BH1750(i2c, address=config.LIGHT_I2C_ADDR)
            # MCP3008 수분 (SPI)
            self.spi = spidev.SpiDev()
            self.spi.open(config.DISPLAY_SPI_PORT, 1)  # CE1
            self.spi.max_speed_hz = 1_000_000
        self._sim_tick = 0  # 시뮬레이션용

    def _read_mcp3008(self, channel):
        r = self.spi.xfer2([1, (8 + channel) << 4, 0])
        return ((r[1] & 3) << 8) | r[2]

    def read(self) -> dict:
        """모든 센서 값을 dict로 반환"""
        if _REAL_HW:
            try:
                temp     = self.dht.temperature
                humidity = self.dht.humidity
            except RuntimeError:
                temp, humidity = None, None
            moisture = self._read_mcp3008(config.MOISTURE_ADC_CHANNEL)
            lux      = self.light.lux
        else:
            # 시뮬레이션: 시간 흐름에 따라 값 변화
            self._sim_tick += 1
            moisture = 400 + (self._sim_tick * 3 % 400)
            lux      = 300 - (self._sim_tick * 2 % 300)
            temp     = 25 + (self._sim_tick % 10)
            humidity = 60.0

        return {
            "moisture": moisture,
            "lux":      lux,
            "temp":     temp,
            "humidity": humidity,
        }

    def get_state(self, data: dict) -> str:
        """센서 값으로 식물 상태 결정 → 표정 이름 반환"""
        if data["moisture"] is not None and data["moisture"] > config.MOISTURE_DRY:
            return "thirsty"
        if data["temp"] is not None and data["temp"] > config.TEMP_HOT:
            return "hot"
        if data["lux"] is not None and data["lux"] < config.LIGHT_LOW_LUX:
            return "dark"
        return "happy"
