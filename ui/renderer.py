import pygame
from typing import Optional

from constants import (
    BLOCK_SIZE, BOARD_COLS, BOARD_ROWS,
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BOARD_OFFSET_X, BOARD_OFFSET_Y,
    PANEL_LEFT_X, PANEL_RIGHT_X,
    COLORS, BG_COLOR, PANEL_BG_COLOR, BOARD_BG_COLOR,
    BORDER_COLOR, TEXT_COLOR, DIM_TEXT_COLOR, HIGHLIGHT_COLOR, GHOST_OUTLINE,
    BLOCK_PADDING, BLOCK_RADIUS, BLOCK_SHINE_Y, BLOCK_SHINE_X,
    BLOCK_SHINE_ALPHA, BLOCK_SPEC_ALPHA,
    BLOCK_SHADOW_DIM, BLOCK_SHADOW_ALPHA, BLOCK_SHADOW_OFFSET,
    GHOST_FILL_ALPHA, GHOST_BORDER_ALPHA,
    BORDER_WIDTH, MINI_BLOCK_SIZE,
    HOLD_PANEL_W, HOLD_PANEL_H, NEXT_PANEL_W, NEXT_PANEL_H,
    PANEL_RADIUS, BOARD_RADIUS,
    FLASH_COLOR,
)
from game.game_manager import GameManager, GameState
from game.tetromino import SHAPES, PIECE_COLOR_ID


class Renderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.menu_cursor = 0
        self._font_large = self._load_font(34, bold=True)
        self._font_med   = self._load_font(22, bold=True)
        self._font_small = self._load_font(17)
        self._font_title = self._load_font(42, bold=True)
        # 블록 서피스 캐시 (color tuple → pygame.Surface)
        self._block_cache: dict[tuple, pygame.Surface] = {}
        self._precompute_blocks()

    # ------------------------------------------------------------------ #
    #  초기화 헬퍼                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _load_font(size: int, bold: bool = False) -> pygame.font.Font:
        for name in ('Bahnschrift', 'Segoe UI', 'Arial Rounded MT Bold', 'consolas'):
            font = pygame.font.SysFont(name, size, bold=bold)
            if font:
                return font
        return pygame.font.SysFont('consolas', size, bold=bold)

    def _precompute_blocks(self) -> None:
        for cid, color in COLORS.items():
            if cid != 0:
                self._make_block_surf(color)

    def _make_block_surf(self, color: tuple) -> pygame.Surface:
        if color in self._block_cache:
            return self._block_cache[color]
        bs = BLOCK_SIZE - BLOCK_PADDING * 2
        surf = pygame.Surface((bs, bs), pygame.SRCALPHA)

        # ① 메인 몸통
        pygame.draw.rect(surf, color, (0, 0, bs, bs), border_radius=BLOCK_RADIUS)

        # ② 상단 광택 (젤리 하이라이트)
        hl_w = bs - BLOCK_SHINE_X * 2
        hl_h = bs // 2 - 1
        hl_col = tuple(min(255, c + 65) for c in color)
        hl_surf = pygame.Surface((hl_w, hl_h), pygame.SRCALPHA)
        pygame.draw.rect(hl_surf, (*hl_col, BLOCK_SHINE_ALPHA),
                         (0, 0, hl_w, hl_h),
                         border_radius=max(1, BLOCK_RADIUS - 2))
        surf.blit(hl_surf, (BLOCK_SHINE_X, BLOCK_SHINE_Y))

        # ③ 스페큘러 반점 (작은 흰 타원)
        sw, sh = 8, 5
        spec = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.ellipse(spec, (255, 255, 255, BLOCK_SPEC_ALPHA), (0, 0, sw, sh))
        surf.blit(spec, (BLOCK_SHINE_X + 1, BLOCK_SHINE_Y + 1))

        self._block_cache[color] = surf
        return surf

    # ------------------------------------------------------------------ #
    #  메인 드로우                                                          #
    # ------------------------------------------------------------------ #

    def draw(self, gm: GameManager) -> None:
        self.screen.fill(BG_COLOR)

        if gm.state == GameState.MENU:
            self._draw_menu()
        elif gm.state in (GameState.PLAYING, GameState.PAUSED,
                          GameState.LINE_CLEAR_ANIM, GameState.GAME_OVER,
                          GameState.NAME_INPUT):
            self._draw_game(gm)
            if gm.state == GameState.PAUSED:
                self._draw_paused_overlay()
            elif gm.state == GameState.GAME_OVER:
                self._draw_game_over(gm)
            elif gm.state == GameState.NAME_INPUT:
                self._draw_name_input(gm)
        elif gm.state == GameState.RANKING:
            self._draw_ranking(gm)
        elif gm.state == GameState.HOW_TO_PLAY:
            self._draw_how_to_play()

        pygame.display.flip()

    # ------------------------------------------------------------------ #
    #  게임 화면                                                            #
    # ------------------------------------------------------------------ #

    def _draw_game(self, gm: GameManager) -> None:
        self._draw_board(gm)
        self._draw_hold(gm)
        self._draw_side_panel(gm)

    def _draw_board(self, gm: GameManager) -> None:
        ox, oy = BOARD_OFFSET_X, BOARD_OFFSET_Y
        bw = BOARD_COLS * BLOCK_SIZE
        bh = BOARD_ROWS * BLOCK_SIZE

        # 보드 배경 (둥근 패널)
        bg_rect = pygame.Rect(ox - 6, oy - 6, bw + 12, bh + 12)
        pygame.draw.rect(self.screen, BOARD_BG_COLOR, bg_rect, border_radius=BOARD_RADIUS)
        pygame.draw.rect(self.screen, BORDER_COLOR, bg_rect, BORDER_WIDTH, border_radius=BOARD_RADIUS)

        # 셀 렌더링
        for r in range(BOARD_ROWS):
            for c in range(BOARD_COLS):
                cid = gm.board.grid[r][c]
                cx = ox + c * BLOCK_SIZE
                cy = oy + r * BLOCK_SIZE
                if r in gm.clearing_lines and gm.anim_flash:
                    self._draw_flash_cell(cx, cy)
                elif cid != 0:
                    self._draw_filled_block(cx, cy, COLORS[cid])
                else:
                    self._draw_empty_cell(cx, cy)

        # 고스트 피스
        if gm.state in (GameState.PLAYING, GameState.LINE_CLEAR_ANIM) and gm.current_piece:
            ghost_color = COLORS.get(gm.current_piece.color_id, (200, 200, 200))
            for gr, gc in gm.get_ghost_cells():
                if 0 <= gr < BOARD_ROWS:
                    self._draw_ghost_cell(ox + gc * BLOCK_SIZE, oy + gr * BLOCK_SIZE, ghost_color)

        # 현재 피스
        if gm.current_piece and gm.state in (GameState.PLAYING, GameState.LINE_CLEAR_ANIM):
            color = COLORS.get(gm.current_piece.color_id, (200, 200, 200))
            for pr, pc in gm.current_piece.get_cells():
                if 0 <= pr < BOARD_ROWS:
                    self._draw_filled_block(ox + pc * BLOCK_SIZE, oy + pr * BLOCK_SIZE, color)

    # ── 블록 드로우 원자 함수들 ──────────────────────────────────────────

    def _draw_filled_block(self, x: int, y: int, color: tuple) -> None:
        pad = BLOCK_PADDING
        bs  = BLOCK_SIZE - pad * 2

        # 그림자 (오프셋 반투명)
        shadow_col = tuple(max(0, c - BLOCK_SHADOW_DIM) for c in color)
        sh_surf = pygame.Surface((bs, bs), pygame.SRCALPHA)
        pygame.draw.rect(sh_surf, (*shadow_col, BLOCK_SHADOW_ALPHA),
                         (0, 0, bs, bs), border_radius=BLOCK_RADIUS)
        self.screen.blit(sh_surf, (x + pad + BLOCK_SHADOW_OFFSET,
                                   y + pad + BLOCK_SHADOW_OFFSET))

        # 메인 블록 (캐시된 서피스)
        self.screen.blit(self._make_block_surf(color), (x + pad, y + pad))

    def _draw_empty_cell(self, x: int, y: int) -> None:
        pad = BLOCK_PADDING
        bs  = BLOCK_SIZE - pad * 2
        rect = pygame.Rect(x + pad, y + pad, bs, bs)
        pygame.draw.rect(self.screen, COLORS[0], rect, border_radius=BLOCK_RADIUS)
        # 안쪽 테두리로 오목한 느낌
        inner = tuple(max(0, v - 12) for v in COLORS[0])
        pygame.draw.rect(self.screen, inner, rect, 1, border_radius=BLOCK_RADIUS)

    def _draw_ghost_cell(self, x: int, y: int, color: tuple) -> None:
        pad = BLOCK_PADDING
        bs  = BLOCK_SIZE - pad * 2
        rect = pygame.Rect(x + pad, y + pad, bs, bs)
        ghost_surf = pygame.Surface((bs, bs), pygame.SRCALPHA)
        # 연한 내부 채우기
        pygame.draw.rect(ghost_surf, (*color, GHOST_FILL_ALPHA),
                         (0, 0, bs, bs), border_radius=BLOCK_RADIUS)
        # 점선 느낌의 테두리
        pygame.draw.rect(ghost_surf, (*GHOST_OUTLINE, GHOST_BORDER_ALPHA),
                         (0, 0, bs, bs), 2, border_radius=BLOCK_RADIUS)
        self.screen.blit(ghost_surf, rect)

    def _draw_flash_cell(self, x: int, y: int) -> None:
        pad = BLOCK_PADDING
        bs  = BLOCK_SIZE - pad * 2
        rect = pygame.Rect(x + pad, y + pad, bs, bs)
        pygame.draw.rect(self.screen, FLASH_COLOR, rect, border_radius=BLOCK_RADIUS)

    # ── 사이드 패널들 ────────────────────────────────────────────────────

    def _draw_hold(self, gm: GameManager) -> None:
        x, y = PANEL_LEFT_X, BOARD_OFFSET_Y
        self._render_label('HOLD', x, y)
        box_y = y + 28
        self._draw_panel_bg(x, box_y, HOLD_PANEL_W, HOLD_PANEL_H)
        if gm.hold_piece:
            color = COLORS.get(gm.hold_piece.color_id, (200, 200, 200))
            alpha = 110 if gm.hold_used else 255
            self._draw_mini_piece(gm.hold_piece.name, x + 12, box_y + 12, color, alpha)

    def _draw_side_panel(self, gm: GameManager) -> None:
        x  = PANEL_RIGHT_X
        y  = BOARD_OFFSET_Y
        sk = gm.score_keeper

        # SCORE
        self._render_label('SCORE', x, y)
        self._draw_value_box(x, y + 25, 148, 38, str(sk.score))

        # LEVEL
        self._render_label('LEVEL', x, y + 80)
        self._draw_value_box(x, y + 105, 148, 38, str(sk.level))

        # LINES
        self._render_label('LINES', x, y + 160)
        self._draw_value_box(x, y + 185, 148, 38, str(sk.lines))

        # NEXT
        self._render_label('NEXT', x, y + 240)
        for i, name in enumerate(gm.get_next_names()):
            color = COLORS.get(PIECE_COLOR_ID[name], (200, 200, 200))
            ny = y + 265 + i * 82
            self._draw_panel_bg(x, ny, NEXT_PANEL_W, NEXT_PANEL_H)
            self._draw_mini_piece(name, x + 12, ny + 10, color, 255)

    def _draw_panel_bg(self, x: int, y: int, w: int, h: int) -> None:
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, PANEL_BG_COLOR, rect, border_radius=PANEL_RADIUS)
        pygame.draw.rect(self.screen, BORDER_COLOR, rect, BORDER_WIDTH, border_radius=PANEL_RADIUS)

    def _draw_value_box(self, x: int, y: int, w: int, h: int, value: str) -> None:
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, PANEL_BG_COLOR, rect, border_radius=10)
        pygame.draw.rect(self.screen, BORDER_COLOR, rect, BORDER_WIDTH, border_radius=10)
        surf = self._font_med.render(value, True, HIGHLIGHT_COLOR)
        self.screen.blit(surf, (x + w // 2 - surf.get_width() // 2,
                                y + h // 2 - surf.get_height() // 2))

    def _draw_mini_piece(self, name: str, x: int, y: int,
                         color: tuple, alpha: int) -> None:
        matrix = SHAPES[name][0]
        bs     = MINI_BLOCK_SIZE
        inner  = bs - BLOCK_PADDING * 2
        for i in range(16):
            if not matrix[i]:
                continue
            bx = x + (i % 4) * bs
            by = y + (i // 4) * bs
            if alpha == 255:
                # 미니 버전도 광택 효과 적용
                rect = pygame.Rect(bx + BLOCK_PADDING, by + BLOCK_PADDING, inner, inner)
                pygame.draw.rect(self.screen, color, rect, border_radius=5)
                hl = tuple(min(255, c + 55) for c in color)
                hl_surf = pygame.Surface((inner - 4, inner // 2), pygame.SRCALPHA)
                pygame.draw.rect(hl_surf, (*hl, 130),
                                 (0, 0, inner - 4, inner // 2), border_radius=3)
                self.screen.blit(hl_surf, (bx + BLOCK_PADDING + 2, by + BLOCK_PADDING + 2))
            else:
                surf = pygame.Surface((inner, inner), pygame.SRCALPHA)
                pygame.draw.rect(surf, (*color, alpha), (0, 0, inner, inner), border_radius=5)
                self.screen.blit(surf, (bx + BLOCK_PADDING, by + BLOCK_PADDING))

    def _render_label(self, text: str, x: int, y: int) -> None:
        surf = self._font_small.render(text, True, DIM_TEXT_COLOR)
        self.screen.blit(surf, (x, y))

    # ------------------------------------------------------------------ #
    #  오버레이 화면들                                                       #
    # ------------------------------------------------------------------ #

    def _draw_paused_overlay(self) -> None:
        self._draw_modal_overlay()
        cx = SCREEN_WIDTH // 2
        self._render_centered('PAUSED', cx, SCREEN_HEIGHT // 2 - 45,
                              self._font_title, HIGHLIGHT_COLOR)
        self._render_centered('P  to resume', cx, SCREEN_HEIGHT // 2 + 20,
                              self._font_small, DIM_TEXT_COLOR)

    def _draw_game_over(self, gm: GameManager) -> None:
        self._draw_modal_overlay()
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        sk = gm.score_keeper

        self._render_centered('GAME  OVER', cx, cy - 110,
                              self._font_title, (232, 108, 142))

        # 결과 카드
        card = pygame.Rect(cx - 160, cy - 55, 320, 100)
        pygame.draw.rect(self.screen, PANEL_BG_COLOR, card, border_radius=16)
        pygame.draw.rect(self.screen, BORDER_COLOR, card, BORDER_WIDTH, border_radius=16)
        self._render_centered(f'{sk.score:,}', cx, cy - 42, self._font_title, HIGHLIGHT_COLOR)
        self._render_centered(
            f'Level  {sk.level}      Lines  {sk.lines}',
            cx, cy + 18, self._font_small, TEXT_COLOR,
        )

        self._render_centered('ENTER  to save score', cx, cy + 72,
                              self._font_small, DIM_TEXT_COLOR)
        self._render_centered('R  restart      ESC  menu', cx, cy + 98,
                              self._font_small, DIM_TEXT_COLOR)

    def _draw_name_input(self, gm: GameManager) -> None:
        self._draw_modal_overlay()
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        self._render_centered('YOUR  NAME', cx, cy - 100,
                              self._font_large, HIGHLIGHT_COLOR)
        self._render_centered('A – Z  /  0 – 9  |  max 10 chars', cx, cy - 58,
                              self._font_small, DIM_TEXT_COLOR)

        # 입력창
        box = pygame.Rect(cx - 160, cy - 28, 320, 56)
        pygame.draw.rect(self.screen, PANEL_BG_COLOR, box, border_radius=14)
        pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, box, 2, border_radius=14)
        display = (gm.name_input or '') + '_'
        self._render_centered(display, cx, cy - 12, self._font_large, TEXT_COLOR)

        self._render_centered('ENTER  confirm      BSP  delete', cx, cy + 50,
                              self._font_small, DIM_TEXT_COLOR)

    def _draw_modal_overlay(self) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((210, 200, 230, 175))
        self.screen.blit(overlay, (0, 0))

    # ------------------------------------------------------------------ #
    #  독립 화면들                                                          #
    # ------------------------------------------------------------------ #

    def _draw_menu(self) -> None:
        cx = SCREEN_WIDTH // 2

        # 배경 장식 원들 (말랑한 느낌)
        for (dx, dy, r, col) in (
            (120, 80,  90, (235, 215, 252)),
            (660, 580, 70, (215, 240, 252)),
            (700, 120, 55, (252, 230, 215)),
            (80,  580, 65, (215, 252, 230)),
        ):
            pygame.draw.circle(self.screen, col, (dx, dy), r)

        self._render_centered('PyTetris', cx, 130, self._font_title, HIGHLIGHT_COLOR)
        self._render_centered('✦  ✦  ✦', cx, 178, self._font_small, BORDER_COLOR)

        items = ['START  GAME', 'RANKING', 'HOW  TO  PLAY', 'QUIT']
        for i, label in enumerate(items):
            iy = 248 + i * 68
            is_sel = (i == self.menu_cursor)
            btn_w, btn_h = 280, 48
            btn_x = cx - btn_w // 2
            btn_bg = HIGHLIGHT_COLOR if is_sel else PANEL_BG_COLOR
            btn_border = HIGHLIGHT_COLOR if is_sel else BORDER_COLOR
            pygame.draw.rect(self.screen, btn_bg,
                             (btn_x, iy, btn_w, btn_h), border_radius=24)
            pygame.draw.rect(self.screen, btn_border,
                             (btn_x, iy, btn_w, btn_h), BORDER_WIDTH, border_radius=24)
            text_col = (255, 255, 255) if is_sel else TEXT_COLOR
            self._render_centered(label, cx, iy + 12, self._font_med, text_col)

        self._render_centered('↑ ↓  navigate      ENTER  select',
                              cx, 548, self._font_small, DIM_TEXT_COLOR)

    def _draw_ranking(self, gm: GameManager) -> None:
        scores = gm.scores_cache
        cx = SCREEN_WIDTH // 2

        self._render_centered('RANKING', cx, 30, self._font_title, HIGHLIGHT_COLOR)

        # 헤더
        hdr_rect = pygame.Rect(50, 90, SCREEN_WIDTH - 100, 34)
        pygame.draw.rect(self.screen, PANEL_BG_COLOR, hdr_rect, border_radius=8)
        hdr = f"{'#':<4}{'NAME':<13}{'SCORE':>9}  {'LV':>3}  {'LINES':>5}  DATE"
        self._render_text(hdr, 62, 99, self._font_small, DIM_TEXT_COLOR)

        for i, row in enumerate(scores):
            row_rect = pygame.Rect(50, 130 + i * 36, SCREEN_WIDTH - 100, 32)
            row_bg = (248, 243, 255) if i % 2 == 0 else PANEL_BG_COLOR
            pygame.draw.rect(self.screen, row_bg, row_rect, border_radius=8)
            if i == 0:
                pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, row_rect, 2, border_radius=8)

            date_str = str(row.get('played_at', ''))[:10]
            line = (f"{i+1:<4}{row['player_name']:<13}{row['score']:>9}  "
                    f"{row['level']:>3}  {row['lines']:>5}  {date_str}")
            color = HIGHLIGHT_COLOR if i == 0 else TEXT_COLOR
            self._render_text(line, 62, 138 + i * 36, self._font_small, color)

        if not scores:
            self._render_centered('No records yet  ✦', cx, 320, self._font_med, DIM_TEXT_COLOR)

        self._render_centered('ESC  back      DEL  clear all',
                              cx, 648, self._font_small, DIM_TEXT_COLOR)

    def _draw_how_to_play(self) -> None:
        cx = SCREEN_WIDTH // 2
        self._render_centered('HOW  TO  PLAY', cx, 30, self._font_title, HIGHLIGHT_COLOR)

        sections = [
            ('CONTROLS', [
                ('← →',             'Move'),
                ('↑',               'Rotate clockwise'),
                ('Z',               'Rotate counter-clockwise'),
                ('↓',               'Soft drop'),
                ('SPACE',           'Hard drop'),
                ('C',               'Hold piece'),
                ('P / ESC',         'Pause'),
                ('M',               'Mute BGM'),
            ]),
            ('SCORING', [
                ('1 line',          '100 × level'),
                ('2 lines',         '300 × level'),
                ('3 lines',         '500 × level'),
                ('4 lines TETRIS!', '800 × level'),
            ]),
        ]

        y = 105
        for title, rows in sections:
            self._render_centered(f'— {title} —', cx, y, self._font_small, HIGHLIGHT_COLOR)
            y += 28
            for key, desc in rows:
                self._render_text(f'{key:<28} {desc}', 120, y, self._font_small, TEXT_COLOR)
                y += 28
            y += 14

        self._render_centered('ESC  back', cx, 640, self._font_small, DIM_TEXT_COLOR)

    # ------------------------------------------------------------------ #
    #  텍스트 헬퍼                                                          #
    # ------------------------------------------------------------------ #

    def _render_text(self, text: str, x: int, y: int,
                     font: pygame.font.Font, color: tuple) -> None:
        self.screen.blit(font.render(text, True, color), (x, y))

    def _render_centered(self, text: str, cx: int, y: int,
                         font: pygame.font.Font, color: tuple) -> None:
        surf = font.render(text, True, color)
        self.screen.blit(surf, (cx - surf.get_width() // 2, y))
