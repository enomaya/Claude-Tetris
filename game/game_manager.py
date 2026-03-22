from enum import Enum
from typing import Optional

from constants import (
    BOARD_COLS, LOCK_DELAY, LOCK_RESET_MAX,
    SOFT_DROP_INTERVAL, get_fall_speed,
)
from game.board import Board
from game.tetromino import Tetromino, TetrominoBag
from game.score import ScoreKeeper


class GameState(Enum):
    MENU = 'menu'
    PLAYING = 'playing'
    PAUSED = 'paused'
    LINE_CLEAR_ANIM = 'line_clear_anim'
    GAME_OVER = 'game_over'
    NAME_INPUT = 'name_input'
    RANKING = 'ranking'
    HOW_TO_PLAY = 'how_to_play'


class GameManager:
    def __init__(self) -> None:
        self.board = Board()
        self.score_keeper = ScoreKeeper()
        self.bag = TetrominoBag()
        self.state = GameState.MENU

        self.current_piece: Optional[Tetromino] = None
        self.hold_piece: Optional[Tetromino] = None
        self.hold_used = False

        self._fall_timer = 0.0
        self._lock_timer: Optional[float] = None
        self._lock_resets = 0
        self._is_on_ground = False

        self._soft_dropping = False
        self._soft_drop_timer = 0.0

        self.clearing_lines: list[int] = []
        self._anim_timer = 0.0
        self.anim_flash = False
        self._pending_lines = 0

        self.name_input = ''
        self.scores_cache: list[dict] = []

    # ------------------------------------------------------------------ #
    #  공개 인터페이스                                                      #
    # ------------------------------------------------------------------ #

    def start_game(self) -> None:
        self.board.reset()
        self.score_keeper.reset()
        self.bag = TetrominoBag()
        self.hold_piece = None
        self.hold_used = False
        self._fall_timer = 0.0
        self._lock_timer = None
        self._lock_resets = 0
        self._is_on_ground = False
        self.clearing_lines = []
        self._spawn_piece()
        self.state = GameState.PLAYING

    def toggle_pause(self) -> None:
        if self.state == GameState.PLAYING:
            self.state = GameState.PAUSED
        elif self.state == GameState.PAUSED:
            self.state = GameState.PLAYING
            self._fall_timer = 0.0

    def move(self, dcol: int) -> bool:
        if self.state != GameState.PLAYING or self.current_piece is None:
            return False
        new_cells = self.current_piece.get_cells(
            col=self.current_piece.col + dcol)
        if self.board.is_valid(new_cells):
            self.current_piece.col += dcol
            self._try_reset_lock()
            return True
        return False

    def rotate(self, direction: int) -> bool:
        if self.state != GameState.PLAYING or self.current_piece is None:
            return False
        p = self.current_piece
        from_rot = p.rotation
        to_rot = (p.rotation + direction) % 4
        kicks = p.get_wall_kicks(from_rot, to_rot)
        for dr, dc in kicks:
            test_cells = p.get_cells(
                row=p.row + dr, col=p.col + dc, rotation=to_rot)
            if self.board.is_valid(test_cells):
                p.rotation = to_rot
                p.row += dr
                p.col += dc
                self._try_reset_lock()
                return True
        return False

    def start_soft_drop(self) -> None:
        self._soft_dropping = True
        self._soft_drop_timer = 0.0

    def stop_soft_drop(self) -> None:
        self._soft_dropping = False

    def hard_drop(self) -> None:
        if self.state != GameState.PLAYING or self.current_piece is None:
            return
        dropped = 0
        while True:
            next_cells = self.current_piece.get_cells(
                row=self.current_piece.row + 1)
            if self.board.is_valid(next_cells):
                self.current_piece.row += 1
                dropped += 1
            else:
                break
        self.score_keeper.add_hard_drop(dropped)
        self._lock_piece()

    def hold(self) -> None:
        if self.state != GameState.PLAYING or self.current_piece is None:
            return
        if self.hold_used:
            return
        held_name = self.current_piece.name
        if self.hold_piece is None:
            self.hold_piece = None
            next_name = self.bag.next()
            new_piece = Tetromino(next_name, row=0, col=BOARD_COLS // 2 - 2)
        else:
            new_piece = Tetromino(self.hold_piece.name, row=0, col=BOARD_COLS // 2 - 2)
        self.hold_piece = Tetromino(held_name)
        self.current_piece = new_piece
        self.hold_used = True
        self._lock_timer = None
        self._lock_resets = 0
        self._is_on_ground = False
        self._fall_timer = 0.0

    def get_ghost_cells(self) -> list[tuple[int, int]]:
        if self.current_piece is None:
            return []
        p = self.current_piece
        row = p.row
        while True:
            next_cells = p.get_cells(row=row + 1)
            if self.board.is_valid(next_cells):
                row += 1
            else:
                break
        return p.get_cells(row=row)

    def get_next_names(self) -> list[str]:
        return self.bag.peek(2)

    def update(self, dt: float) -> None:
        if self.state == GameState.LINE_CLEAR_ANIM:
            self._update_anim(dt)
            return
        if self.state != GameState.PLAYING:
            return
        self._update_fall(dt)
        self._update_lock(dt)

    def enter_ranking(self) -> None:
        from data.db import get_top_scores
        self.scores_cache = get_top_scores()
        self.state = GameState.RANKING

    # ------------------------------------------------------------------ #
    #  내부 헬퍼                                                           #
    # ------------------------------------------------------------------ #

    def _spawn_piece(self) -> None:
        name = self.bag.next()
        piece = Tetromino(name, row=0, col=BOARD_COLS // 2 - 2)
        if self.board.is_blocked_at_spawn(piece.get_cells()):
            self.current_piece = piece
            self.state = GameState.GAME_OVER
            return
        self.current_piece = piece
        self.hold_used = False
        self._fall_timer = 0.0
        self._lock_timer = None
        self._lock_resets = 0
        self._is_on_ground = False

    def _is_piece_on_ground(self) -> bool:
        if self.current_piece is None:
            return False
        next_cells = self.current_piece.get_cells(
            row=self.current_piece.row + 1)
        return not self.board.is_valid(next_cells)

    def _update_fall(self, dt: float) -> None:
        if self.current_piece is None:
            return

        if self._soft_dropping:
            self._soft_drop_timer += dt
            if self._soft_drop_timer >= SOFT_DROP_INTERVAL:
                self._soft_drop_timer = 0.0
                self._try_fall(soft=True)
            return

        self._fall_timer += dt
        fall_speed = get_fall_speed(self.score_keeper.level)
        if self._fall_timer >= fall_speed:
            self._fall_timer = 0.0
            self._try_fall(soft=False)

    def _try_fall(self, soft: bool) -> None:
        if self.current_piece is None:
            return
        next_cells = self.current_piece.get_cells(
            row=self.current_piece.row + 1)
        if self.board.is_valid(next_cells):
            self.current_piece.row += 1
            if soft:
                self.score_keeper.add_soft_drop(1)
            self._is_on_ground = False
        else:
            if not self._is_on_ground:
                self._is_on_ground = True
                self._lock_timer = 0.0

    def _update_lock(self, dt: float) -> None:
        if self._lock_timer is None:
            return
        if not self._is_piece_on_ground():
            self._lock_timer = None
            self._is_on_ground = False
            return
        self._lock_timer += dt
        if self._lock_timer >= LOCK_DELAY or self._lock_resets >= LOCK_RESET_MAX:
            self._lock_piece()

    def _try_reset_lock(self) -> None:
        if self._lock_timer is not None and self._lock_resets < LOCK_RESET_MAX:
            self._lock_timer = 0.0
            self._lock_resets += 1
        on_ground = self._is_piece_on_ground()
        if on_ground and self._lock_timer is None:
            self._lock_timer = 0.0
            self._is_on_ground = True

    def _lock_piece(self) -> None:
        if self.current_piece is None:
            return
        cells = self.current_piece.get_cells()
        self.board.lock(cells, self.current_piece.color_id)
        full_lines = self.board.get_full_lines()
        if full_lines:
            self.clearing_lines = full_lines
            self._anim_timer = 0.0
            self.anim_flash = True
            self.state = GameState.LINE_CLEAR_ANIM
            self._pending_lines = len(full_lines)
        else:
            self._spawn_piece()

    def _update_anim(self, dt: float) -> None:
        from constants import LINE_CLEAR_FLASH_DURATION, LINE_CLEAR_FLASH_CYCLES
        self._anim_timer += dt
        self.anim_flash = (self._anim_timer % (LINE_CLEAR_FLASH_DURATION * 2)) < LINE_CLEAR_FLASH_DURATION
        if self._anim_timer >= LINE_CLEAR_FLASH_DURATION * LINE_CLEAR_FLASH_CYCLES:
            self.board.clear_lines(self.clearing_lines)
            self.score_keeper.add_lines(self._pending_lines)
            self.clearing_lines = []
            self.anim_flash = False
            self.state = GameState.PLAYING
            self._spawn_piece()
