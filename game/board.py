from constants import BOARD_COLS, BOARD_ROWS


class Board:
    def __init__(self) -> None:
        self.grid: list[list[int]] = [[0] * BOARD_COLS for _ in range(BOARD_ROWS)]

    def reset(self) -> None:
        self.grid = [[0] * BOARD_COLS for _ in range(BOARD_ROWS)]

    def is_valid(self, cells: list[tuple[int, int]]) -> bool:
        for row, col in cells:
            if col < 0 or col >= BOARD_COLS:
                return False
            if row >= BOARD_ROWS:
                return False
            if row >= 0 and self.grid[row][col] != 0:
                return False
        return True

    def lock(self, cells: list[tuple[int, int]], color_id: int) -> None:
        for row, col in cells:
            if 0 <= row < BOARD_ROWS and 0 <= col < BOARD_COLS:
                self.grid[row][col] = color_id

    def get_full_lines(self) -> list[int]:
        return [r for r in range(BOARD_ROWS) if all(self.grid[r])]

    def clear_lines(self, lines: list[int]) -> None:
        for r in sorted(lines, reverse=True):
            del self.grid[r]
            self.grid.insert(0, [0] * BOARD_COLS)

    def is_blocked_at_spawn(self, cells: list[tuple[int, int]]) -> bool:
        for row, col in cells:
            if row >= 0 and self.grid[row][col] != 0:
                return True
        return False
