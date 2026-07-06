# ============================================================
#  simulator.py  —  이미지 프레임 방식 시뮬레이터
#  실행: uv run python simulator.py
# ============================================================
import sys, math, random
try:
    import pygame
except ImportError:
    print("pygame이 없어요."); sys.exit(1)

import config
from display import TRANSITION_TICKS, _blink_ratio, _transition_blink
from pathlib import Path

SW, SH = 760, 427   # 이미지 비율 (16:9)
WIN_H  = SH + 56

ASSETS = Path(__file__).parent / "assets"

# ── 이미지 매핑 ───────────────────────────────────────────
IMAGES = {
    "neutral":       "01_neutral.png",
    "bashful":       "02_bashful.png",
    "curious":       "03_curious.png",
    "excited":       "04_excited.png",
    "sleepy":        "05_sleepy.png",
    "question":      "06_question.png",
    "content":       "07_content.png",
    "moody":         "08_moody.png",
    "playful":       "09_playful.png",
    "thirsty":       "10_thirsty.png",
    "love":          "11_love.png",
    "asleep":        "12_asleep.png",
    "gift":          "13_gift.png",
    "low_light":     "14_low-light.png",
    "too_hot":       "15_too-hot.png",
    "too_cold":      "16_too-cold.png",
    "overwatered":   "17_overwatered.png",
    "low_humidity":  "18_low-humidity.png",
    "night":         "19_night.png",
}

LABELS = {
    "neutral":      "기본  (1)",
    "bashful":      "수줍  (2)",
    "curious":      "호기심 (3)",
    "excited":      "신남  (4)",
    "sleepy":       "멍함  (5)",
    "question":     "궁금  (6)",
    "content":      "흐뭇  (7)",
    "moody":        "삐짐  (8)",
    "playful":      "장난  (9)",
    "thirsty":      "목마름 (T)",
    "love":         "사랑  (L)",
    "asleep":       "수면  (A)",
    "gift":         "선물  (G)",
    "low_light":    "햇빛부족 (F)",
    "too_hot":      "너무더움 (H)",
    "too_cold":     "너무추움 (C)",
    "overwatered":  "과습  (O)",
    "low_humidity": "건조  (D)",
    "night":        "밤   (N)",
}

KEY_MAP = {
    pygame.K_1:"neutral",   pygame.K_2:"bashful",   pygame.K_3:"curious",
    pygame.K_4:"excited",   pygame.K_5:"sleepy",    pygame.K_6:"question",
    pygame.K_7:"content",   pygame.K_8:"moody",     pygame.K_9:"playful",
    pygame.K_t:"thirsty",   pygame.K_l:"love",      pygame.K_a:"asleep",
    pygame.K_g:"gift",      pygame.K_f:"low_light", pygame.K_h:"too_hot",
    pygame.K_c:"too_cold",  pygame.K_o:"overwatered", pygame.K_d:"low_humidity",
    pygame.K_n:"night",
}

# ── 전환 경로 정의 ─────────────────────────────────────────
# 특정 조합은 중간 이미지를 경유
# { (from, to): [중간이미지, ...] }
COLORED_BG = {"too_hot", "too_cold", "moody", "playful", "overwatered", "night"}
TRANS_MID = {
    # 컬러 배경 진입
    ("*",          "too_hot"):     ["trans_to_hot"],
    ("*",          "too_cold"):    ["trans_to_cold"],
    ("*",          "moody"):       ["trans_to_moody"],
    ("*",          "playful"):     ["trans_to_playful"],
    ("*",          "overwatered"): ["trans_to_overwatered"],
    ("*",          "night"):       ["trans_to_night"],
    # 컬러 배경 이탈 (역방향)
    ("too_hot",    "*"):           ["trans_to_hot"],
    ("too_cold",   "*"):           ["trans_to_cold"],
    ("moody",      "*"):           ["trans_to_moody"],
    ("playful",    "*"):           ["trans_to_playful"],
    ("overwatered","*"):           ["trans_to_overwatered"],
    ("night",      "*"):           ["trans_to_night"],
    # 눈 모양 전환
    ("excited",    "sleepy"):      ["trans_excited_to_sleepy"],
    ("sleepy",     "excited"):     ["trans_excited_to_sleepy"],
    ("excited",    "moody"):       ["trans_excited_to_neutral", "trans_neutral_to_moody"],
    ("moody",      "excited"):     ["trans_neutral_to_moody",   "trans_excited_to_neutral"],
}

TRANS_IMAGES = {
    "trans_to_hot":              "trans_to_hot.png",
    "trans_to_cold":             "trans_to_cold.png",
    "trans_to_moody":            "trans_to_moody.png",
    "trans_to_playful":          "trans_to_playful.png",
    "trans_to_overwatered":      "trans_to_overwatered.png",
    "trans_to_night":            "trans_to_night.png",
    "trans_excited_to_sleepy":   "trans_excited_to_sleepy.png",
    "trans_excited_to_neutral":  "trans_excited_to_neutral.png",
    "trans_neutral_to_moody":    "trans_neutral_to_moody.png",
}

def get_trans_path(src, dst):
    """전환 경로 반환 — 중간 이미지 키 리스트"""
    if (src, dst) in TRANS_MID:
        return TRANS_MID[(src, dst)]
    if ("*", dst) in TRANS_MID:
        return TRANS_MID[("*", dst)]
    if (src, "*") in TRANS_MID:
        return TRANS_MID[(src, "*")]
    return []

STATE_ORDER = list(IMAGES.keys())


def main():
    pygame.init()
    screen = pygame.display.set_mode((SW, WIN_H))
    pygame.display.set_caption("스마트 화분 — 표정 시뮬레이터")
    clock  = pygame.time.Clock()
    font   = pygame.font.SysFont("malgun gothic", 18)
    font_s = pygame.font.SysFont("malgun gothic", 13)

    # 표정 이미지 로드
    surfaces = {}
    for key, fname in IMAGES.items():
        path = ASSETS / fname
        if path.exists():
            img = pygame.image.load(str(path)).convert_alpha()
            surfaces[key] = pygame.transform.scale(img, (SW, SH))
        else:
            print(f"[경고] 이미지 없음: {fname}")

    # 중간 전환 이미지 로드
    trans_surfaces = {}
    for key, fname in TRANS_IMAGES.items():
        path = ASSETS / fname
        if path.exists():
            img = pygame.image.load(str(path)).convert_alpha()
            trans_surfaces[key] = pygame.transform.scale(img, (SW, SH))

    # 깜빡임 이미지
    blink_path = ASSETS / "00_blink.png"
    blink_surf = pygame.transform.scale(
        pygame.image.load(str(blink_path)).convert_alpha(), (SW, SH)
    ) if blink_path.exists() else None

    state        = "neutral"
    next_state   = None
    trans_queue  = []   # 중간 이미지 큐
    tick         = 0
    blink_phase  = 0    # 0=없음 1=감는중 2=감김(중간이미지) 3=뜨는중
    blink_t      = 0.0
    mid_idx      = 0    # 현재 중간 이미지 인덱스
    BLINK_CLOSE  = 0.07
    BLINK_HOLD   = 0.06
    BLINK_OPEN   = 0.09
    ANIM_FPS     = 60

    # ── idle 둥둥 애니메이션 ──────────────────────────────────
    idle_time    = 0.0      # 누적 시간 (초)
    IDLE_AMP     = 5        # 픽셀 진폭
    IDLE_SPEED   = 0.5      # 주기 (Hz)

    # ── 전환 바운스 ───────────────────────────────────────────
    bounce_t     = 0.0      # 0.0 → 1.0
    BOUNCE_DUR   = 0.18     # 바운스 지속 시간 (초)
    bounce_active = False

    # ── 자동 눈 깜빡임 ────────────────────────────────────────
    auto_blink_timer = random.uniform(2.5, 5.0)  # 다음 깜빡임까지 남은 시간

    print("=" * 50)
    print("표정 시뮬레이터 시작!")
    print("1~9: 기본감정  T:목마름 L:사랑 A:수면 G:선물")
    print("F:햇빛부족 H:더움 C:추움 O:과습 D:건조 N:밤")
    print("←→ 방향키로 순서대로 변경  |  ESC 종료")
    print("=" * 50)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in KEY_MAP:
                    new = KEY_MAP[event.key]
                    if new != state and blink_phase == 0:
                        next_state  = new
                        trans_queue = get_trans_path(state, new)
                        mid_idx     = 0
                        blink_phase = 1
                        blink_t     = 0.0
                    print(f"표정: {LABELS.get(new, new)}")
                elif event.key == pygame.K_RIGHT:
                    idx = (STATE_ORDER.index(state) + 1) % len(STATE_ORDER)
                    new = STATE_ORDER[idx]
                    if blink_phase == 0:
                        next_state  = new
                        trans_queue = get_trans_path(state, new)
                        mid_idx     = 0
                        blink_phase = 1
                        blink_t     = 0.0
                    print(f"표정: {LABELS.get(new, new)}")
                elif event.key == pygame.K_LEFT:
                    idx = (STATE_ORDER.index(state) - 1) % len(STATE_ORDER)
                    new = STATE_ORDER[idx]
                    if blink_phase == 0:
                        next_state  = new
                        trans_queue = get_trans_path(state, new)
                        mid_idx     = 0
                        blink_phase = 1
                        blink_t     = 0.0
                    print(f"표정: {LABELS.get(new, new)}")

        # ── dt 계산 ───────────────────────────────────────────
        dt_idle = 1.0 / ANIM_FPS

        tick += 1
        current_fps = ANIM_FPS
        dt = 1.0 / current_fps

        # ── 자동 깜빡임 타이머 ────────────────────────────────
        if blink_phase == 0:
            auto_blink_timer -= dt
            if auto_blink_timer <= 0:
                blink_phase = 1
                blink_t     = 0.0
                next_state  = state   # 표정 유지 (깜빡임만)
                trans_queue = []
                mid_idx     = 0
                auto_blink_timer = random.uniform(2.5, 5.0)

        # ── idle 둥둥 타이머 ──────────────────────────────────
        idle_time += dt

        # ── 바운스 타이머 ─────────────────────────────────────
        if bounce_active:
            bounce_t += dt / BOUNCE_DUR
            if bounce_t >= 1.0:
                bounce_t     = 1.0
                bounce_active = False

        def ease(t):
            t = max(0.0, min(1.0, t))
            return t * t * (3 - 2 * t)

        # 현재 보여줄 중간 이미지
        mid_surf = None
        if trans_queue and mid_idx < len(trans_queue):
            mid_surf = trans_surfaces.get(trans_queue[mid_idx])

        # 중간 이미지가 없으면 blink 사용
        hold_surf = mid_surf if mid_surf else blink_surf

        # ── 깜빡임 전환 상태머신 ─────────────────────────
        if blink_phase == 1:
            blink_t += dt / BLINK_CLOSE
            if blink_t >= 1.0:
                blink_phase = 2
                blink_t     = 0.0
        elif blink_phase == 2:
            blink_t += dt / BLINK_HOLD
            if blink_t >= 1.0:
                # 다음 중간 이미지가 있으면 계속, 없으면 새 표정으로
                mid_idx += 1
                if mid_idx < len(trans_queue):
                    blink_t = 0.0  # 다음 중간 이미지로
                else:
                    prev_state  = state
                    state       = next_state
                    blink_phase = 3
                    blink_t     = 0.0
                    # 표정이 바뀐 경우에만 바운스
                    if state != prev_state:
                        bounce_t      = 0.0
                        bounce_active = True
        elif blink_phase == 3:
            blink_t += dt / BLINK_OPEN
            if blink_t >= 1.0:
                blink_phase = 0
                blink_t     = 0.0
                next_state  = None
                trans_queue = []

        # ── idle 오프셋 계산 ─────────────────────────────────
        idle_y = int(math.sin(idle_time * IDLE_SPEED * 2 * math.pi) * IDLE_AMP)

        # ── 바운스 스케일 계산 ────────────────────────────────
        # 0→1 진행: 살짝 커졌다가 원래 크기로 (overshoot)
        def bounce_scale(t):
            t = max(0.0, min(1.0, t))
            # ease-out elastic 느낌 (간단 버전)
            return 1.0 + 0.06 * math.sin(t * math.pi) * (1 - t)

        bscale = bounce_scale(bounce_t) if bounce_active else 1.0

        def blit_with_fx(surf, alpha, scale, y_off):
            """alpha, scale, y_off 적용해서 blit"""
            if not surf:
                return
            surf.set_alpha(alpha)
            if abs(scale - 1.0) > 0.001:
                w = int(SW * scale)
                h = int(SH * scale)
                scaled = pygame.transform.smoothscale(surf, (w, h))
                x = (SW - w) // 2
                y = (SH - h) // 2 + y_off
                screen.blit(scaled, (x, y))
            else:
                screen.blit(surf, (0, y_off))

        # ── 렌더 ─────────────────────────────────────────────
        screen.fill((0, 0, 0))
        curr = surfaces.get(state)

        if blink_phase == 0:
            blit_with_fx(curr, 255, bscale, idle_y)

        elif blink_phase == 1:
            t = ease(blink_t)
            blit_with_fx(curr,      int(255 * (1 - t)), 1.0, idle_y)
            blit_with_fx(hold_surf, int(255 * t),       1.0, idle_y)

        elif blink_phase == 2:
            blit_with_fx(hold_surf, 255, 1.0, idle_y)

        elif blink_phase == 3:
            t = ease(blink_t)
            blit_with_fx(hold_surf, int(255 * (1 - t)), 1.0,    idle_y)
            blit_with_fx(curr,      int(255 * t),       bscale, idle_y)

        # 하단 바
        bar_y = SH + 8
        label = LABELS.get(state, state)
        screen.blit(font.render(f"현재 상태: {label}", True, (220, 220, 100)), (12, bar_y))
        screen.blit(font_s.render("←→ 키로 변경  |  단축키: 1~9 T L A G F H C O D N  |  ESC 종료",
                                  True, (60, 60, 60)), (12, bar_y + 24))

        pygame.display.flip()
        clock.tick(current_fps)

    pygame.quit()


if __name__ == "__main__":
    main()
