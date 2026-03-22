import random
from typing import Optional

# 각 피스의 회전 상태 (0~3). 4x4 행렬을 1D 리스트로 표현 (row-major)
SHAPES: dict[str, list[list[int]]] = {
    'I': [
        [0,0,0,0,
         1,1,1,1,
         0,0,0,0,
         0,0,0,0],
        [0,0,1,0,
         0,0,1,0,
         0,0,1,0,
         0,0,1,0],
        [0,0,0,0,
         0,0,0,0,
         1,1,1,1,
         0,0,0,0],
        [0,1,0,0,
         0,1,0,0,
         0,1,0,0,
         0,1,0,0],
    ],
    'O': [
        [0,1,1,0,
         0,1,1,0,
         0,0,0,0,
         0,0,0,0],
    ] * 4,
    'T': [
        [0,1,0,0,
         1,1,1,0,
         0,0,0,0,
         0,0,0,0],
        [0,1,0,0,
         0,1,1,0,
         0,1,0,0,
         0,0,0,0],
        [0,0,0,0,
         1,1,1,0,
         0,1,0,0,
         0,0,0,0],
        [0,1,0,0,
         1,1,0,0,
         0,1,0,0,
         0,0,0,0],
    ],
    'S': [
        [0,1,1,0,
         1,1,0,0,
         0,0,0,0,
         0,0,0,0],
        [0,1,0,0,
         0,1,1,0,
         0,0,1,0,
         0,0,0,0],
        [0,0,0,0,
         0,1,1,0,
         1,1,0,0,
         0,0,0,0],
        [1,0,0,0,
         1,1,0,0,
         0,1,0,0,
         0,0,0,0],
    ],
    'Z': [
        [1,1,0,0,
         0,1,1,0,
         0,0,0,0,
         0,0,0,0],
        [0,0,1,0,
         0,1,1,0,
         0,1,0,0,
         0,0,0,0],
        [0,0,0,0,
         1,1,0,0,
         0,1,1,0,
         0,0,0,0],
        [0,1,0,0,
         1,1,0,0,
         1,0,0,0,
         0,0,0,0],
    ],
    'J': [
        [1,0,0,0,
         1,1,1,0,
         0,0,0,0,
         0,0,0,0],
        [0,1,1,0,
         0,1,0,0,
         0,1,0,0,
         0,0,0,0],
        [0,0,0,0,
         1,1,1,0,
         0,0,1,0,
         0,0,0,0],
        [0,1,0,0,
         0,1,0,0,
         1,1,0,0,
         0,0,0,0],
    ],
    'L': [
        [0,0,1,0,
         1,1,1,0,
         0,0,0,0,
         0,0,0,0],
        [0,1,0,0,
         0,1,0,0,
         0,1,1,0,
         0,0,0,0],
        [0,0,0,0,
         1,1,1,0,
         1,0,0,0,
         0,0,0,0],
        [1,1,0,0,
         0,1,0,0,
         0,1,0,0,
         0,0,0,0],
    ],
}

PIECE_NAMES = ['I', 'O', 'T', 'S', 'Z', 'J', 'L']
PIECE_COLOR_ID = {'I': 1, 'O': 2, 'T': 3, 'S': 4, 'Z': 5, 'J': 6, 'L': 7}

# SRS 벽 킥 오프셋 (일반 피스)
WALL_KICK_NORMAL: dict[tuple[int, int], list[tuple[int, int]]] = {
    (0, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (1, 0): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (1, 2): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (2, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (2, 3): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (3, 2): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (3, 0): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (0, 3): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
}

# SRS 벽 킥 오프셋 (I 피스)
WALL_KICK_I: dict[tuple[int, int], list[tuple[int, int]]] = {
    (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
    (1, 0): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
    (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
    (2, 1): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    (2, 3): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
    (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
    (3, 0): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
}


class Tetromino:
    def __init__(self, name: str, row: int = 0, col: int = 3) -> None:
        self.name = name
        self.color_id = PIECE_COLOR_ID[name]
        self.rotation = 0
        self.row = row
        self.col = col

    def get_cells(self, row: Optional[int] = None, col: Optional[int] = None,
                  rotation: Optional[int] = None) -> list[tuple[int, int]]:
        r = self.row if row is None else row
        c = self.col if col is None else col
        rot = self.rotation if rotation is None else rotation
        matrix = SHAPES[self.name][rot % 4]
        cells = []
        for i in range(16):
            if matrix[i]:
                cells.append((r + i // 4, c + i % 4))
        return cells

    def get_wall_kicks(self, from_rot: int, to_rot: int) -> list[tuple[int, int]]:
        key = (from_rot % 4, to_rot % 4)
        if self.name == 'I':
            return WALL_KICK_I.get(key, [(0, 0)])
        return WALL_KICK_NORMAL.get(key, [(0, 0)])


class TetrominoBag:
    def __init__(self) -> None:
        self._queue: list[str] = []
        self._refill()

    def _refill(self) -> None:
        bag = PIECE_NAMES[:]
        random.shuffle(bag)
        self._queue.extend(bag)

    def next(self) -> str:
        if len(self._queue) < 7:
            self._refill()
        return self._queue.pop(0)

    def peek(self, count: int = 2) -> list[str]:
        while len(self._queue) < count + 7:
            self._refill()
        return self._queue[:count]
