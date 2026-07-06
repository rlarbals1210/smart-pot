# ============================================================
#  display.py  —  OLED 표정 렌더링 (루나로봇 스타일)
#  - 큰 동그란 눈 + 하이라이트
#  - 깜빡임 애니메이션
#  - 표정 전환 시 부드러운 모핑
# ============================================================
import math
import config

try:
    from luma.core.interface.serial import spi
    from luma.oled.device import ssd1309
    from luma.core.render import canvas
    _REAL_HW = True
except ImportError:
    _REAL_HW = False
    print("[display] luma 라이브러리 없음 — 시뮬레이션 모드")

W, H   = config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT
CX     = W // 2       # 64
CY     = H // 2       # 32

# ── 눈 기본 파라미터 ──────────────────────────────────────
EYE_R   = 14          # 눈 반지름 (크게)
EYE_LX  = CX - 17    # 왼쪽 눈 중심 X
EYE_RX  = CX + 17    # 오른쪽 눈 중심 X
EYE_Y   = CY - 4     # 눈 중심 Y
MOUTH_Y = CY + 16    # 입 Y

# ── 깜빡임 주기 설정 ──────────────────────────────────────
BLINK_INTERVAL = 90   # 틱: 이 간격마다 깜빡
BLINK_DURATION = 6    # 틱: 눈 감는 시간


def _blink_ratio(tick: int) -> float:
    """0.0=완전히 뜸, 1.0=완전히 감음. 깜빡임 사인 커브."""
    phase = tick % BLINK_INTERVAL
    if phase < BLINK_DURATION:
        return math.sin(math.pi * phase / BLINK_DURATION)
    return 0.0


def _draw_eye(draw, ex: int, ey: int, r: int, blink: float,
              style: str = "normal", sw: int = 2):
    """
    단일 눈 렌더링.
    style: normal / sad / angry / half / heart
    blink: 0.0~1.0 (깜빡임 정도)
    """
    # 깜빡임: 눈 위에 검은 사각형으로 덮어서 감는 효과
    squish = blink  # 0=뜸, 1=완전히 감음

    if style == "heart":
        # 하트 눈
        hr = r - 3
        draw.ellipse([ex-hr-2, ey-hr, ex,      ey+hr//2], fill="white")
        draw.ellipse([ex,      ey-hr, ex+hr+2, ey+hr//2], fill="white")
        draw.polygon([(ex-hr-2, ey), (ex+hr+2, ey), (ex, ey+hr+5)], fill="white")
        return

    if style == "half":
        # 반감긴 눈 (햇빛부족/졸림)
        open_h = int(r * (1 - squish * 0.5))
        draw.arc([ex-r, ey-open_h, ex+r, ey+open_h],
                 start=180, end=360, fill="white", width=sw)
        draw.line([ex-r, ey, ex+r, ey], fill="white", width=sw)
        return

    if style == "angry":
        # 찡그린 눈 (뒤집힌 반원)
        draw.arc([ex-r, ey-r, ex+r, ey+r],
                 start=0, end=180, fill="white", width=sw)
        draw.line([ex-r, ey, ex+r, ey], fill="white", width=sw)
        return

    # ── 기본/슬픈 눈: 동그란 눈 ──────────────────────────
    top_cut = int(r * squish)  # 깜빡임 시 위쪽 잘라냄

    if squish > 0.85:
        # 완전히 감긴 상태: 가로선만
        draw.line([ex-r, ey, ex+r, ey], fill="white", width=sw)
        return

    # 눈 테두리
    draw.ellipse([ex-r, ey-r+top_cut, ex+r, ey+r], outline="white", width=sw)

    # 위쪽 잘라내기 (깜빡임)
    if top_cut > 0:
        draw.rectangle([ex-r-1, ey-r, ex+r+1, ey-r+top_cut], fill="black")

    # sad 스타일: 눈 살짝 아래로
    if style == "sad":
        return

    # 하이라이트 (루나로봇 느낌)
    hl_x = ex + r // 3
    hl_y = ey - r // 3
    hl_r = max(r // 5, 2)
    draw.ellipse([hl_x-hl_r, hl_y-hl_r, hl_x+hl_r, hl_y+hl_r], fill="white")


# ── 전환 애니메이션 ───────────────────────────────────────
TRANSITION_TICKS = 8   # 표정 전환 시 눈 감는 틱 수

def _transition_blink(trans_tick: int) -> float:
    """전환 중 눈 감김 비율. trans_tick=0~TRANSITION_TICKS"""
    if trans_tick <= 0:
        return 0.0
    half = TRANSITION_TICKS // 2
    if trans_tick <= half:
        return trans_tick / half
    else:
        return 1.0 - (trans_tick - half) / half


# ── 각 표정 그리기 함수 ───────────────────────────────────

def _draw_happy(draw, tick=0, blink=0.0):
    for ex in (EYE_LX, EYE_RX):
        _draw_eye(draw, ex, EYE_Y, EYE_R, blink, "normal")
    draw.arc([CX-22, MOUTH_Y-7, CX+22, MOUTH_Y+7],
             start=0, end=180, fill="white", width=2)


def _draw_thirsty(draw, tick=0, blink=0.0):
    for ex in (EYE_LX, EYE_RX):
        _draw_eye(draw, ex, EYE_Y+3, EYE_R, blink, "sad")
    draw.line([CX-16, MOUTH_Y+2, CX+16, MOUTH_Y+2], fill="white", width=2)
    # 눈물 깜빡
    if (tick // 8) % 6 < 3:
        draw.ellipse([EYE_RX+EYE_R, EYE_Y+EYE_R+2,
                      EYE_RX+EYE_R+5, EYE_Y+EYE_R+9], fill="white")


def _draw_dark(draw, tick=0, blink=0.0):
    for ex in (EYE_LX, EYE_RX):
        _draw_eye(draw, ex, EYE_Y, EYE_R, max(blink, 0.5), "half")
    draw.arc([CX-16, MOUTH_Y-4, CX+16, MOUTH_Y+4],
             start=180, end=360, fill="white", width=2)


def _draw_hot(draw, tick=0, blink=0.0):
    for i, ex in enumerate((EYE_LX, EYE_RX)):
        _draw_eye(draw, ex, EYE_Y, EYE_R, blink, "angry")
        if i == 0:
            draw.line([ex-EYE_R, EYE_Y-EYE_R-4, ex+EYE_R//2, EYE_Y-EYE_R],
                      fill="white", width=2)
        else:
            draw.line([ex-EYE_R//2, EYE_Y-EYE_R, ex+EYE_R, EYE_Y-EYE_R-4],
                      fill="white", width=2)
    draw.line([CX-14, MOUTH_Y+2, CX+14, MOUTH_Y+2], fill="white", width=2)
    if (tick // 6) % 2 == 0:
        draw.ellipse([EYE_RX+EYE_R+2, EYE_Y-8,
                      EYE_RX+EYE_R+8, EYE_Y], fill="white")


def _draw_sleepy(draw, tick=0, blink=0.0):
    sleepy_b = max(blink, 0.4 + 0.2 * math.sin(tick * 0.05))
    for ex in (EYE_LX, EYE_RX):
        _draw_eye(draw, ex, EYE_Y, EYE_R, sleepy_b, "half")
    draw.line([CX-12, MOUTH_Y+1, CX+12, MOUTH_Y+1], fill="white", width=2)
    z_x = EYE_RX + EYE_R + 3
    if (tick // 10) % 3 > 0:
        draw.text((z_x,   EYE_Y-10), "z", fill="white")
    if (tick // 10) % 3 > 1:
        draw.text((z_x+6, EYE_Y-18), "z", fill="white")


def _draw_gift(draw, tick=0, blink=0.0):
    if blink < 0.5:
        for ex in (EYE_LX, EYE_RX):
            _draw_eye(draw, ex, EYE_Y, EYE_R, 0.0, "heart")
    draw.arc([CX-24, MOUTH_Y-9, CX+24, MOUTH_Y+9],
             start=0, end=180, fill="white", width=3)


EXPRESSIONS = {
    "happy":   _draw_happy,
    "thirsty": _draw_thirsty,
    "dark":    _draw_dark,
    "hot":     _draw_hot,
    "sleepy":  _draw_sleepy,
    "gift":    _draw_gift,
}


class DisplayManager:
    def __init__(self):
        if _REAL_HW:
            serial = spi(port=config.DISPLAY_SPI_PORT,
                         device=config.DISPLAY_SPI_DEVICE,
                         gpio_DC=config.DISPLAY_DC_PIN,
                         gpio_RST=config.DISPLAY_RESET_PIN)
            self.device = ssd1309(serial,
                                  width=config.DISPLAY_WIDTH,
                                  height=config.DISPLAY_HEIGHT)
        else:
            self.device = None

        self.tick        = 0
        self._prev_state = None
        self._trans_tick = 0   # 전환 애니메이션 카운터

    def draw(self, state: str):
        draw_fn = EXPRESSIONS.get(state, _draw_happy)
        self.tick += 1

        # 표정 전환 감지
        if state != self._prev_state:
            self._trans_tick = TRANSITION_TICKS
            self._prev_state = state

        if self._trans_tick > 0:
            self._trans_tick -= 1

        # 깜빡임 비율
        blink = _blink_ratio(self.tick)
        # 전환 중이면 전환 깜빡임 우선
        if self._trans_tick > 0:
            blink = max(blink, _transition_blink(self._trans_tick))

        if _REAL_HW:
            with canvas(self.device) as draw:
                draw_fn(draw, self.tick, blink)
        else:
            if self.tick % 50 == 1:
                print(f"[display] 표정: {state}  (tick={self.tick})")

    def clear(self):
        if _REAL_HW:
            self.device.clear()
