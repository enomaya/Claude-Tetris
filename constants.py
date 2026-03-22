BOARD_COLS = 10
BOARD_ROWS = 20
BLOCK_SIZE = 30

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
FPS = 60

DAS_DELAY = 0.17
ARR_INTERVAL = 0.05
LOCK_DELAY = 0.5
LOCK_RESET_MAX = 15

SOFT_DROP_INTERVAL = 0.05

# 낙하 속도: (0.8 - (level-1)*0.007)^(level-1) 초
def get_fall_speed(level: int) -> float:
    lv = max(1, min(level, 15))
    return (0.8 - (lv - 1) * 0.007) ** (lv - 1)

# ── 파스텔 블록 색상 ──────────────────────────────────────────────────────
COLORS = {
    0: (228, 221, 242),   # 빈 셀 - 연보라 안개
    1: (138, 215, 232),   # I - 파우더 블루
    2: (255, 228, 138),   # O - 버터 옐로우
    3: (198, 165, 232),   # T - 라벤더
    4: (158, 224, 180),   # S - 민트 그린
    5: (248, 170, 178),   # Z - 로즈 핑크
    6: (158, 188, 248),   # J - 페리윙클 블루
    7: (252, 198, 148),   # L - 소프트 피치
}

# ── 배경 / UI 색상 ────────────────────────────────────────────────────────
BG_COLOR         = (250, 246, 255)   # 거의 흰 라벤더
PANEL_BG_COLOR   = (240, 235, 252)   # 소프트 패널 배경
BOARD_BG_COLOR   = (236, 230, 248)   # 보드 배경
BORDER_COLOR     = (198, 188, 220)   # 라벤더 테두리
TEXT_COLOR       = (105, 88, 135)    # 딥 라벤더 텍스트
DIM_TEXT_COLOR   = (175, 162, 200)   # 흐린 텍스트
HIGHLIGHT_COLOR  = (228, 105, 145)   # 라즈베리 핑크 강조
GHOST_OUTLINE    = (188, 175, 215)   # 고스트 피스 테두리

# ── 블록 렌더링 상수 ──────────────────────────────────────────────────────
BLOCK_PADDING    = 3                 # 셀 경계에서 블록까지 여백 (px)
BLOCK_RADIUS     = 8                 # 블록 모서리 둥근 반경 (px)
BLOCK_SHINE_Y    = 3                 # 상단 광택 시작 Y 오프셋 (px)
BLOCK_SHINE_X    = 3                 # 상단 광택 시작 X 오프셋 (px)
BLOCK_SHINE_ALPHA = 148              # 광택 레이어 알파
BLOCK_SPEC_ALPHA = 195               # 스페큘러 반점 알파
BLOCK_SHADOW_DIM = 28                # 그림자 어두움 정도
BLOCK_SHADOW_ALPHA = 90              # 그림자 알파
BLOCK_SHADOW_OFFSET = 2              # 그림자 오프셋 (px)
GHOST_FILL_ALPHA = 45                # 고스트 피스 내부 알파
GHOST_BORDER_ALPHA = 130             # 고스트 피스 테두리 알파

# ── 패널 레이아웃 상수 ────────────────────────────────────────────────────
BORDER_WIDTH     = 2
MINI_BLOCK_SIZE  = 22
HOLD_PANEL_W     = 130
HOLD_PANEL_H     = 95
NEXT_PANEL_W     = 130
NEXT_PANEL_H     = 75
PANEL_RADIUS     = 14                # 패널 모서리 둥근 반경 (px)
BOARD_RADIUS     = 14                # 보드 배경 모서리 둥근 반경 (px)

PANEL_LEFT_X     = 22
BOARD_OFFSET_X   = 185
BOARD_OFFSET_Y   = 40
PANEL_RIGHT_X    = BOARD_OFFSET_X + BOARD_COLS * BLOCK_SIZE + 18

# ── 애니메이션 ───────────────────────────────────────────────────────────
LINE_CLEAR_FLASH_DURATION = 0.1
LINE_CLEAR_FLASH_CYCLES   = 4
FLASH_COLOR               = (255, 255, 255)

# ── 게임 규칙 ────────────────────────────────────────────────────────────
SCORE_TABLE = {1: 100, 2: 300, 3: 500, 4: 800}
