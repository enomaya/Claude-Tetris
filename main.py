import sys
import pygame

from constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, DAS_DELAY, ARR_INTERVAL
from game.game_manager import GameManager, GameState
from data.db import init_db, insert_score, clear_scores
from ui.renderer import Renderer


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('PyTetris')
    clock = pygame.time.Clock()

    init_db()

    gm = GameManager()
    renderer = Renderer(screen)

    # DAS/ARR 상태
    das_key: int | None = None
    das_timer = 0.0
    arr_timer = 0.0
    das_active = False

    # 메뉴 커서
    menu_items = ['start', 'ranking', 'how', 'quit']
    menu_cursor = 0

    # BGM (파일 없으면 무음)
    bgm_muted = False
    _try_play_bgm()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # ---------------------------------------------------------------- #
        #  이벤트 처리                                                       #
        # ---------------------------------------------------------------- #
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                key = event.key
                state = gm.state

                # ── 공통 ──
                if key == pygame.K_m:
                    bgm_muted = _toggle_bgm(bgm_muted)

                # ── 메뉴 ──
                if state == GameState.MENU:
                    if key == pygame.K_UP:
                        menu_cursor = (menu_cursor - 1) % len(menu_items)
                    elif key == pygame.K_DOWN:
                        menu_cursor = (menu_cursor + 1) % len(menu_items)
                    elif key in (pygame.K_RETURN, pygame.K_SPACE):
                        selected = menu_items[menu_cursor]
                        if selected == 'start':
                            gm.start_game()
                        elif selected == 'ranking':
                            gm.enter_ranking()
                        elif selected == 'how':
                            gm.state = GameState.HOW_TO_PLAY
                        elif selected == 'quit':
                            running = False

                # ── PLAYING ──
                elif state == GameState.PLAYING:
                    if key in (pygame.K_p, pygame.K_ESCAPE):
                        gm.toggle_pause()
                    elif key == pygame.K_UP:
                        gm.rotate(1)
                    elif key == pygame.K_z:
                        gm.rotate(-1)
                    elif key == pygame.K_SPACE:
                        gm.hard_drop()
                    elif key == pygame.K_c:
                        gm.hold()
                    elif key == pygame.K_DOWN:
                        gm.start_soft_drop()
                    elif key in (pygame.K_LEFT, pygame.K_RIGHT):
                        dcol = -1 if key == pygame.K_LEFT else 1
                        gm.move(dcol)
                        das_key = key
                        das_timer = 0.0
                        arr_timer = 0.0
                        das_active = False

                # ── PAUSED ──
                elif state == GameState.PAUSED:
                    if key in (pygame.K_p, pygame.K_ESCAPE):
                        gm.toggle_pause()

                # ── GAME_OVER ──
                elif state == GameState.GAME_OVER:
                    if key == pygame.K_r:
                        gm.start_game()
                    elif key == pygame.K_ESCAPE:
                        gm.state = GameState.MENU
                        menu_cursor = 0
                    elif key == pygame.K_RETURN:
                        gm.name_input = ''
                        gm.state = GameState.NAME_INPUT

                # ── NAME_INPUT ──
                elif state == GameState.NAME_INPUT:
                    if key == pygame.K_RETURN:
                        name = gm.name_input.strip() or 'PLAYER'
                        insert_score(name, gm.score_keeper.score,
                                     gm.score_keeper.level, gm.score_keeper.lines)
                        gm.enter_ranking()
                    elif key == pygame.K_BACKSPACE:
                        gm.name_input = gm.name_input[:-1]
                    elif key == pygame.K_ESCAPE:
                        gm.state = GameState.GAME_OVER
                    else:
                        ch = event.unicode
                        if ch.isalnum() and len(gm.name_input) < 10:
                            gm.name_input += ch.upper()

                # ── RANKING ──
                elif state == GameState.RANKING:
                    if key == pygame.K_ESCAPE:
                        gm.state = GameState.MENU
                        menu_cursor = 0
                    elif key == pygame.K_DELETE:
                        clear_scores()
                        gm.scores_cache = []

                # ── HOW_TO_PLAY ──
                elif state == GameState.HOW_TO_PLAY:
                    if key == pygame.K_ESCAPE:
                        gm.state = GameState.MENU
                        menu_cursor = 0

            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    if event.key == das_key:
                        das_key = None
                        das_active = False
                if event.key == pygame.K_DOWN:
                    gm.stop_soft_drop()

        # ---------------------------------------------------------------- #
        #  DAS / ARR                                                        #
        # ---------------------------------------------------------------- #
        if das_key is not None and gm.state == GameState.PLAYING:
            das_timer += dt
            if not das_active:
                if das_timer >= DAS_DELAY:
                    das_active = True
                    arr_timer = ARR_INTERVAL  # 즉시 첫 반복 이동
            else:
                arr_timer += dt
                if arr_timer >= ARR_INTERVAL:
                    arr_timer = 0.0
                    dcol = -1 if das_key == pygame.K_LEFT else 1
                    gm.move(dcol)

        # ---------------------------------------------------------------- #
        #  게임 업데이트                                                     #
        # ---------------------------------------------------------------- #
        gm.update(dt)

        # ---------------------------------------------------------------- #
        #  렌더링 — 메뉴 커서 주입                                           #
        # ---------------------------------------------------------------- #
        renderer.menu_cursor = menu_cursor
        renderer.draw(gm)

    pygame.quit()
    sys.exit()


def _try_play_bgm() -> None:
    try:
        import os
        bgm_path = os.path.join('assets', 'sounds', 'bgm.ogg')
        if os.path.exists(bgm_path):
            pygame.mixer.music.load(bgm_path)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
    except Exception:
        pass


def _toggle_bgm(muted: bool) -> bool:
    try:
        if muted:
            pygame.mixer.music.set_volume(0.5)
        else:
            pygame.mixer.music.set_volume(0.0)
    except Exception:
        pass
    return not muted


if __name__ == '__main__':
    main()
