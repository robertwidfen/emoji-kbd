import sys
from typing import LiteralString
from blessed import Terminal
from blessed.keyboard import Keystroke
from wcwidth import wcswidth
import textwrap
import logging as log

from src.emojis import get_emojis_boards, Emoji, kbd, kbd_board


def make_board(
    emojis: list[Emoji], offset: int = 0
) -> tuple[list[str], dict[str, Emoji]]:
    board: list[str] = [""]
    mapping: dict[str, Emoji] = {}
    i = offset
    row = 0
    for k in kbd:
        if k == " ":
            board[row] += "   "
        elif k == "\n":
            row += 1
            board.append("")
        elif i < len(emojis):
            e = emojis[i]
            mapping[k] = e
            board[row] += k
            board[row] += e.char
            board[row] += " " * (3 - wcswidth(e.char))
            i += 1
        else:
            board[row] += k + "   "
    return (board, mapping)


board_path: list[list[Emoji]] = []


def push_board(emojis: list[Emoji]):
    board_path.append(emojis)
    return make_board(board_path[-1])


def pop_board():
    if len(board_path) > 1:
        board_path.pop()
    return make_board(board_path[-1])


def clear_status_row(term: Terminal, status_row: int):
    with term.location(0, status_row):
        print(term.clear_eol)
        print(term.clear_eol)
        print(term.clear_eol)


def show_status(term: Terminal, status_row: int, emoji: Emoji | None):
    if emoji is None:
        clear_status_row(term, status_row)
        return
    with term.location(0, status_row):
        if emoji.unicode:
            print(f"{emoji.char}, +{emoji.unicode}, {emoji.name}" + term.clear_eol)
            print(f"{emoji.group} > {emoji.subgroup}" + term.clear_eol)
        else:
            group = f"{len(emoji.emojis)} emojis, {emoji.group}"
            print(f"{group}" + term.clear_eol)
            subgroup = textwrap.wrap(emoji.subgroup, width=term.width - 2)
            print(f"{"\n".join(subgroup)}" + term.clear_eol)
        if emoji.tags:
            tags = textwrap.wrap(emoji.tags, width=term.width - 2)
            for line in tags:
                print(f"{line}" + term.clear_eol)
        print(term.clear_eol)
        print(term.clear_eol)
        print(term.clear_eol)


def show_board(term: Terminal, board: list[str]):
    with term.location(0, 2):
        for line in board:
            print(line + term.clear_eol)


def get_cursor_x(row: int, col: int, board: list[str]) -> int:
    key = kbd_board[row][col]
    pos = board[row].find(key)
    return wcswidth(board[row][:pos])


def get_key_pos(key: str, board: list[LiteralString]) -> tuple[int, int]:
    for r, line in enumerate(board):
        c = line.find(key)
        if c != -1:
            return (r, c)
    raise ValueError(f"Key '{key}' not found on board")


def get_emoji(key: str, mapping: dict[str, Emoji]) -> Emoji | None:
    e = mapping.get(key, mapping.get(key.upper(), None))
    return e


def main():
    term = Terminal()

    # use list instead of str to keep graphemes together -
    # makes deletion and cursor movement easier
    text_buffer: list[str] = []
    # cursor position
    cursor_x: int = 2
    cursor_y: int = 0
    # board position
    offset = 0
    col = 0
    row = 0

    chars_on_board = sum(1 for char in kbd if not char.isspace())

    # Context manager clears the screen on entry/exit
    with term.cbreak(), term.fullscreen():
        (emojis, groups) = get_emojis_boards()
        (board, mapping) = push_board(groups)
        status_row = 2 + len(board) + 1
        text_cursor = 0
        current_key = ""

        show_board(term, board)

        while True:
            with term.location(0, 0):
                print("> " + "".join(text_buffer) + term.clear_eol, end="", flush=True)

            print(term.move_xy(cursor_x, cursor_y), end="", flush=True)

            key: Keystroke = term.inkey()

            if not key:
                continue

            if key.name == "KEY_CTRL_C":
                break

            isInput = cursor_y == 0
            isBoard = cursor_y > 0
            isEnter = key.name in ("KEY_ENTER", "KEY_RETURN")
            isCursor = key.name in (
                "KEY_UP",
                "KEY_DOWN",
                "KEY_LEFT",
                "KEY_RIGHT",
                "KEY_HOME",
                "KEY_END",
            )

            if cursor_y == 0 and isEnter:
                break
            elif key.name == "KEY_TAB":  # Tab key
                if cursor_y == 0:
                    cursor_y = 2 + row
                    cursor_x = get_cursor_x(row, col, board)
                else:
                    cursor_y = 0
                    cursor_x = 2 + wcswidth("".join(text_buffer[:text_cursor]))
                continue
            elif key.name == "KEY_ESCAPE":
                (board, mapping) = pop_board()
                show_board(term, board)
                clear_status_row(term, status_row)
                continue
            elif key.name == "KEY_BACKSPACE":
                if isInput:
                    text_buffer = (
                        text_buffer[: text_cursor - 1] + text_buffer[text_cursor:]
                    )
                    if text_cursor > 0:
                        text_cursor -= 1
                    cursor_x = 2 + wcswidth("".join(text_buffer[:text_cursor]))
                else:
                    (board, mapping) = pop_board()
                    show_board(term, board)
                    e = get_emoji(current_key, mapping)
                    if e:
                        show_status(term, status_row, e)
                continue
            elif key.name == "KEY_DELETE" and isInput:
                text_buffer = text_buffer[:text_cursor] + text_buffer[text_cursor + 1 :]
                cursor_x = 2 + wcswidth("".join(text_buffer[:text_cursor]))
                continue
            elif key.name == "KEY_HOME" and isInput:
                text_cursor = 0
                cursor_x = 2 + wcswidth("".join(text_buffer[:text_cursor]))
            elif key.name == "KEY_END" and isInput:
                text_cursor = len(text_buffer)
                cursor_x = 2 + wcswidth("".join(text_buffer[:text_cursor]))
            elif key.name == "KEY_PGUP":
                offset -= chars_on_board
                if offset < 0:
                    offset = 0
                (board, mapping) = make_board(board_path[-1], offset)
                show_board(term, board)
            elif key.name == "KEY_PGDOWN":
                if offset + chars_on_board < len(board_path[-1]):
                    offset += chars_on_board
                    (board, mapping) = make_board(board_path[-1], offset)
                    show_board(term, board)
            elif isCursor and isInput:
                if key.name == "KEY_LEFT" and text_cursor > 0:
                    text_cursor -= 1
                    cursor_x = 2 + wcswidth("".join(text_buffer[:text_cursor]))
                elif key.name == "KEY_RIGHT" and text_cursor < len(text_buffer):
                    text_cursor += 1
                    cursor_x = 2 + wcswidth("".join(text_buffer[:text_cursor]))
                elif key.name == "KEY_DOWN":
                    cursor_y = 2
                    cursor_x = get_cursor_x(row, col, board)
                    current_key = kbd_board[row][col]
                    show_status(term, status_row, mapping.get(current_key))
                continue
            elif key.name == "KEY_HOME" and isBoard:
                col = 0
                cursor_x = get_cursor_x(row, col, board)
            elif key.name == "KEY_END" and isBoard:
                col = len(kbd_board[row]) - 1
                cursor_x = get_cursor_x(row, col, board)
            elif key.name == "KEY_LEFT" and isBoard:
                col -= 1
                cursor_x = get_cursor_x(row, col, board)
            elif key.name == "KEY_RIGHT" and isBoard and col + 1 < len(kbd_board[row]):
                col += 1
                cursor_x = get_cursor_x(row, col, board)
            elif key.name == "KEY_UP" and isBoard:
                if cursor_y == 2:
                    cursor_y = 0
                    cursor_x = 2 + wcswidth("".join(text_buffer[:text_cursor]))
                else:
                    cursor_y -= 1
                    row -= 1
                    if col >= len(kbd_board[row]):
                        col = len(kbd_board[row]) - 1
                    cursor_x = get_cursor_x(row, col, board)
            elif key.name == "KEY_DOWN" and isBoard and cursor_y < 2 + len(board) - 1:
                cursor_y += 1
                row += 1
                if col >= len(kbd_board[row]):
                    col = len(kbd_board[row]) - 1
                cursor_x = get_cursor_x(row, col, board)

            if isCursor or isEnter:
                current_key = kbd_board[row][col]
            elif key.isprintable():
                current_key = key
                old_row = row
                old_col = col
                try:
                    (row, col) = get_key_pos(current_key, kbd_board)
                except ValueError:
                    try:
                        (row, col) = get_key_pos(current_key.upper(), kbd_board)
                    except ValueError:
                        pass
            e = get_emoji(current_key, mapping)
            if e:
                for r, line in enumerate(kbd_board):
                    c = line.find(current_key)
                    if c != -1:
                        (col, row) = (c, r)
                        break
            else:
                clear_status_row(term, status_row)
                continue

            show_status(term, status_row, e)

            if isInput and not key.isprintable() and not isEnter:
                continue
            if isCursor or len(key) > 1:
                continue

            if not e.unicode and e.emojis:
                (board, mapping) = push_board(e.emojis)
                show_board(term, board)
                show_status(term, status_row, mapping.get(current_key))
                continue

            # it must be an Emoji so insert it
            show_status(term, status_row, e)
            text_buffer.insert(text_cursor, e.char)
            text_cursor += 1
            # update text cursor
            if isInput:
                cursor_x = 2 + wcswidth("".join(text_buffer[:text_cursor]))

    # output final text
    print("".join(text_buffer), end="")


if __name__ == "__main__":
    log.basicConfig(
        filename=".local/termkbd.log",
        # filemode='a',
        level=log.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    log.info(f"Starting terminal Emoji Keyboard on {sys.platform}...")
    try:
        main()
    except KeyboardInterrupt:
        pass
