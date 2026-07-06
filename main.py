# ============================================================
#  main.py  —  스마트 화분 메인 루프
# ============================================================
import time
import threading
import config
from sensors import SensorManager
from display import DisplayManager
from speaker import SpeakerManager

# ── 버튼 (AI 스피커 트리거) ───────────────────────────────
BUTTON_PIN = 17   # GPIO17
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    _GPIO_OK = True
except ImportError:
    _GPIO_OK = False
    print("[main] RPi.GPIO 없음 — 키보드로 버튼 시뮬레이션 (Enter)")


def main():
    sensor_mgr  = SensorManager()
    display_mgr = DisplayManager()
    speaker_mgr = SpeakerManager()

    current_state = "happy"
    last_sensor_time = 0

    # 말하는 동안 표정을 "gift"로 바꾸는 콜백
    def on_speaking():
        display_mgr.draw("gift")
    speaker_mgr.on_speaking(on_speaking)

    print("[main] 스마트 화분 시작!")

    def button_listener():
        """별도 스레드에서 버튼 감지"""
        while True:
            if _GPIO_OK:
                if GPIO.input(BUTTON_PIN) == GPIO.LOW:
                    speaker_mgr.handle_interaction(current_state)
                    time.sleep(0.5)
            else:
                input()   # Enter 키 대기
                speaker_mgr.handle_interaction(current_state)

    btn_thread = threading.Thread(target=button_listener, daemon=True)
    btn_thread.start()

    # ── 메인 루프 ─────────────────────────────────────────
    try:
        while True:
            now = time.time()

            # 센서 주기적으로 읽기
            if now - last_sensor_time >= config.SENSOR_INTERVAL:
                data = sensor_mgr.read()
                current_state = sensor_mgr.get_state(data)
                print(f"[main] 센서: {data}  →  상태: {current_state}")
                last_sensor_time = now

            # 표정 업데이트
            display_mgr.draw(current_state)
            time.sleep(1 / config.DISPLAY_FPS)

    except KeyboardInterrupt:
        print("\n[main] 종료")
        display_mgr.clear()
        if _GPIO_OK:
            GPIO.cleanup()


if __name__ == "__main__":
    main()
