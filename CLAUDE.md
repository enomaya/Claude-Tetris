# PyTetris 개발 가이드

## 프로젝트 개요

Python + pygame으로 구현하는 클래식 테트리스 게임. 로컬 랭킹 시스템 포함.

---

## 기술 스택

| 역할 | 기술 | 버전 |
|---|---|---|
| 언어 | Python | 3.10+ |
| 게임 엔진 | pygame | 2.x |
| DB | sqlite3 | 내장 모듈 |
| 패키징 | PyInstaller | 최신 |

의존성 설치:
```bash
pip install pygame
```

---

## 프로젝트 구조

```
tetris/
├── main.py                  # 진입점, 메인 게임 루프
├── constants.py             # 전역 상수 (크기, 색상, 키 매핑)
├── game/
│   ├── board.py             # 보드 상태 관리 (2D 배열)
│   ├── tetromino.py         # 피스 정의, 이동, 회전
│   ├── game_manager.py      # 게임 상태 머신
│   └── score.py             # 점수/레벨 계산
├── ui/
│   ├── renderer.py          # pygame 렌더링 전담
│   ├── menu.py              # 메뉴 화면
│   └── ranking_screen.py    # 랭킹 화면
├── data/
│   ├── db.py                # SQLite CRUD 래퍼
│   └── scores.db            # 런타임 자동 생성
└── assets/
    ├── sounds/              # .wav / .ogg
    └── fonts/               # .ttf
```

**원칙**: 렌더링 로직은 반드시 `ui/renderer.py`에만 위치. `game/` 모듈은 pygame에 의존하지 않아야 함.

---

## 핵심 상수 (constants.py)

```python
BOARD_COLS = 10
BOARD_ROWS = 20
BLOCK_SIZE = 30          # 픽셀 단위

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
FPS = 60

# 낙하 속도: 레벨별 (0.8 - (level-1)*0.007)^(level-1) 초
DAS_DELAY = 0.17         # 키 자동반복 대기 시간 (초)
ARR_INTERVAL = 0.05      # 키 자동반복 간격 (초)
LOCK_DELAY = 0.5         # 착지 후 고정 유예 시간 (초)
LOCK_RESET_MAX = 15      # Lock Delay 리셋 최대 횟수

# 색상 (R, G, B)
COLORS = {
    0: (40, 40, 40),     # 빈 셀
    1: (0, 240, 240),    # I
    2: (240, 240, 0),    # O
    3: (160, 0, 240),    # T
    4: (0, 240, 0),      # S
    5: (240, 0, 0),      # Z
    6: (0, 0, 240),      # J
    7: (240, 160, 0),    # L
}
```

---

## 게임 로직 규칙

### 테트로미노

- 7종 피스(I, O, T, S, Z, J, L)는 각각 고유 색상 ID(1~7)로 구분
- **7-bag 랜덤라이저** 필수: `random.shuffle`로 7종 피스를 한 세트씩 소비
- 회전은 4x4 행렬 기반, 시계/반시계 방향 모두 지원
- SRS(Super Rotation System) 간소화 버전 적용 — I피스 벽 킥은 별도 처리

### 점수 계산 (Nintendo 스코어링)

```
싱글 (1줄) = 100 × level
더블 (2줄) = 300 × level
트리플 (3줄) = 500 × level
테트리스 (4줄) = 800 × level
소프트 드롭 = 1점 / 셀
하드 드롭 = 2점 / 셀
```

레벨업: 클리어 줄 누적 10줄마다 +1 레벨 (최대 레벨 15)

### Lock Delay

피스가 바닥 또는 다른 블록에 닿은 시점부터 0.5초 유예.
유예 시간 내 이동/회전 시 타이머 리셋 (최대 15회).
15회 초과 또는 0.5초 경과 시 즉시 고정.

### 게임오버 조건

새 피스 생성 위치(보드 상단 중앙, row=0 기준)에 기존 블록이 존재할 때.

---

## 랭킹 시스템

### DB 스키마

```sql
CREATE TABLE IF NOT EXISTS scores (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT    NOT NULL CHECK(length(player_name) <= 10),
    score       INTEGER NOT NULL,
    level       INTEGER NOT NULL,
    lines       INTEGER NOT NULL,
    played_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### db.py 공개 인터페이스

```python
def insert_score(name: str, score: int, level: int, lines: int) -> None
def get_top_scores(limit: int = 10) -> list[dict]
def clear_scores() -> None
```

- DB 파일 경로: `os.path.dirname(os.path.abspath(__file__))` 기준으로 고정
  → PyInstaller 패키징 후에도 경로 깨지지 않도록
- `get_top_scores()`는 `score DESC` 정렬 보장
- `insert_score()` 호출 전 상위 10위 여부를 게임 매니저에서 판단하지 않음 — 항상 저장하고 조회 시 상위 10개만 반환

### 이름 입력 규칙

- 영문/숫자만 허용, 최대 10자
- 빈 문자열 제출 시 "PLAYER"로 자동 치환
- 백스페이스 지원

---

## 코드 스타일

### 기본 규칙

- 들여쓰기: 스페이스 4칸
- 문자열: 작은따옴표(`'`) 우선
- 타입 힌트: 모든 함수 시그니처에 작성
- 최대 줄 길이: 100자

### 네이밍 컨벤션

| 대상 | 규칙 | 예시 |
|---|---|---|
| 함수/변수 | snake_case | `clear_lines`, `current_piece` |
| 클래스 | PascalCase | `GameManager`, `Tetromino` |
| 상수 | UPPER_SNAKE_CASE | `BOARD_ROWS`, `LOCK_DELAY` |
| 파일 | snake_case | `game_manager.py` |

### 모듈 분리 원칙

- `game/` 모듈: 순수 로직만. pygame import 금지
- `ui/` 모듈: 렌더링만. 게임 상태를 직접 변경하지 않음
- `data/` 모듈: DB 접근만. 게임 로직 금지
- 상수는 모두 `constants.py`에서 import — 매직 넘버 금지

### 게임 상태

`GameManager`가 단일 진실의 원천(SSOT). 허용되는 상태:

```python
class GameState(Enum):
    MENU = 'menu'
    PLAYING = 'playing'
    PAUSED = 'paused'
    GAME_OVER = 'game_over'
    RANKING = 'ranking'
    HOW_TO_PLAY = 'how_to_play'
```

---

## 렌더링 규칙

- 타겟 프레임레이트: **60 FPS** (`clock.tick(FPS)`)
- 전체 화면 `fill()` 대신 dirty rect 방식 권장 (성능 최적화)
- Ghost Piece: 실제 피스와 동일 색상, 알파값 70 적용
- 라인 클리어 애니메이션: 완성 줄 흰색 깜빡임 0.1초 후 제거

### 레이아웃

```
[홀드 패널 (좌)] [게임보드 (중앙)] [사이드 패널 (우)]
                                   - SCORE
                                   - LEVEL
                                   - LINES
                                   - NEXT × 2
```

---

## 키 매핑

| 키 | 동작 |
|---|---|
| ← → | 좌우 이동 (DAS/ARR 적용) |
| ↑ | 시계 방향 회전 |
| Z | 반시계 방향 회전 |
| ↓ | 소프트 드롭 |
| Space | 하드 드롭 |
| C | Hold |
| P / ESC | 일시정지 |
| M | 배경음악 토글 |
| R | 재시작 (게임오버 화면에서만) |

---

## 개발 원칙

1. **단계적 구현**: Phase 1(MVP) 완전 동작 확인 후 Phase 2 시작. 기능 추가마다 즉시 플레이 테스트.
2. **매직 넘버 금지**: 숫자 리터럴은 `constants.py`에 상수로 정의.
3. **렌더링/로직 분리**: `game/` 모듈이 pygame을 직접 다루지 않으면 단독 단위 테스트 가능.
4. **사운드 에셋 없어도 실행 가능**: `pygame.mixer` 초기화 실패 또는 파일 누락 시 무음으로 정상 실행.
5. **DB 경로는 절대경로**: `os.path.abspath`로 항상 고정. 상대경로 사용 금지.
6. **락 조건 엄격 처리**: Lock Delay 리셋 횟수를 반드시 추적. 무한 리셋으로 게임이 멈추는 버그 방지.

---

## Phase별 구현 순서

### Phase 1 — MVP (2주)
1. `constants.py` 정의
2. pygame 윈도우 초기화 + 게임 루프 뼈대
3. `board.py` — 2D 배열 보드 + 렌더링
4. `tetromino.py` — 7종 피스 정의 + 7-bag + 이동/회전
5. 충돌 감지 + 피스 고정 로직
6. 소프트/하드 드롭
7. 라인 클리어 + 점수 + 레벨
8. 게임오버 감지
9. `data/db.py` + 랭킹 저장/조회
10. 메인 메뉴 + 랭킹 화면

### Phase 2 — 완성 기능 (2주)
- Ghost Piece
- Hold 기능
- Next Piece 2개 미리보기
- Lock Delay
- 사운드 시스템
- 라인 클리어 애니메이션
- 도움말 화면

### Phase 3 — Polish (1~2주)
- 설정 화면 (볼륨, Ghost ON/OFF) → `config.json` 저장
- DAS/ARR 파라미터 실전 조정
- PyInstaller `.exe` 빌드
- README 작성
