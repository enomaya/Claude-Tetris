from constants import SCORE_TABLE


class ScoreKeeper:
    def __init__(self) -> None:
        self.score = 0
        self.level = 1
        self.lines = 0

    def reset(self) -> None:
        self.score = 0
        self.level = 1
        self.lines = 0

    def add_lines(self, count: int) -> int:
        points = SCORE_TABLE.get(count, 0) * self.level
        self.score += points
        self.lines += count
        new_level = self.lines // 10 + 1
        self.level = min(new_level, 15)
        return points

    def add_soft_drop(self, cells: int) -> None:
        self.score += cells

    def add_hard_drop(self, cells: int) -> None:
        self.score += cells * 2
