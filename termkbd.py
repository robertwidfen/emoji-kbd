from blessed import Terminal
from blessed.keyboard import Keystroke
import textwrap
import wcwidth  # type: ignore

from boards import get_emojis_groups, Emoji, make_mapping, kbd, kbd_board


def termwidth(s: str) -> int:
    return wcwidth.wcswidth(s)  # type: ignore


def make_board(emojis: list[Emoji]) -> tuple[str, dict[str, Emoji]]:
    board: list[str] = []
    mapping: dict[str, Emoji] = {}
    i = 0
    for k in kbd:
        board.append(k)
        if k not in (" ", "\n"):
            if i < len(emojis):
                e = emojis[i]
                board.append(e.char)
                board.append(" ")
                # print(f"{e.char} {termwidth(e.char)}")
                # if termwidth(e.char) < 2:
                #     board.append(" ")
                mapping[k] = e
                i += 1
            else:
                board.append("  ")
    return ("".join(board), mapping)


group_path: list[list[Emoji]] = []


def push_group(emojis: list[Emoji]):
    group_path.append(emojis)
    return make_board(group_path[-1])


def pop_group():
    if len(group_path) > 1:
        group_path.pop()
    return make_board(group_path[-1])


def clear_satus_row(term: Terminal, status_row: int):
    with term.location(0, status_row):
        print(term.clear_eol)
        print(term.clear_eol)
        print(term.clear_eol)


def show_status(term: Terminal, status_row: int, emoji: Emoji):
    with term.location(0, status_row):
        if emoji.unicode:
            print(f"{emoji.char}, {emoji.unicode}, {emoji.name}" + term.clear_eol)
        else:
            print(f"{emoji.group} > {emoji.subgroup}" + term.clear_eol)
        if emoji.tags:
            tags = textwrap.wrap(emoji.tags, width=term.width - 2)
            for line in tags:
                print(f"{line}" + term.clear_eol)
        print(term.clear_eol)
        print(term.clear_eol)


def show_board(term: Terminal, board: str):
    with term.location(0, 2):
        for line in board.splitlines():
            print(line + term.clear_eol)


def main():
    # Initialize the terminal object
    term = Terminal()

    # Application state variables
    text_buffer: str = ""
    cursor_x: int = 2
    cursor_y: int = 0

    # Context manager clears the screen on entry/exit
    with term.cbreak(), term.fullscreen():
        print(term.home + term.clear + "> " + text_buffer)

        max_chars = sum(1 for char in kbd if not char.isspace())

        (emojis, groups) = get_emojis_groups()
        (board, mapping) = push_group(groups)

        board_cols = max(len(line) for line in board.splitlines())
        board_rows = len(board.splitlines())
        status_row = 2 + board_rows + 1

        show_board(term, board)

        while True:
            with term.location(0, 0):
                print("> " + text_buffer + term.clear_eol, end="", flush=True)

            # Move physical cursor to current logical position in buffer
            print(term.move_xy(cursor_x, cursor_y), end="", flush=True)

            key: Keystroke = term.inkey()

            if key:
                if key.name == "KEY_ENTER" or key.name == "KEY_RETURN":
                    break

                # Check for specific modifier keys using key.is_modifier
                # print(f"Key pressed: {key.name}, Ctrl={key.is_ctrl}, Alt={key.is_alt}") # Debug info
                # if key.is_shift("a"):
                #     print("Shift + A was pressed!")

                if key.name == "KEY_LEFT":
                    if cursor_y == 0 and cursor_x > 2:
                        cursor_x -= 2
                    elif cursor_y > 1 and cursor_y < 6 and cursor_x:
                        cursor_x -= 5
                elif key.name == "KEY_RIGHT":
                    if cursor_y == 0 and cursor_x < len(text_buffer) / 2 + 5:
                        cursor_x += 2
                    elif cursor_y > 1 and cursor_y < 6 and cursor_x <= board_cols + 5:
                        cursor_x += 5
                elif key.name == "KEY_UP":
                    if cursor_y > 0:
                        cursor_y -= 1
                    if cursor_y == 1:
                        cursor_y = 0
                elif key.name == "KEY_DOWN":
                    if cursor_y < 5:
                        cursor_y += 1
                    if cursor_y == 1:
                        cursor_y = 2
                    if cursor_y > 1:
                        cursor_x = int(cursor_x / 5) * 5

                # --- Handling Tab (key.code is the ASCII value) ---
                elif key.code == 9:
                    pass

                elif key.name == "KEY_BACKSPACE":
                    if cursor_x > 2:
                        p = int((cursor_x - 2) / 2)
                        text_buffer = text_buffer[: p - 1] + text_buffer[p:]
                        cursor_x -= 2

                elif key.name == "KEY_DELETE":
                    if cursor_x < len(text_buffer) + 2:
                        p = int((cursor_x - 2) / 2)
                        text_buffer = text_buffer[:p] + text_buffer[p + 1 :]

                elif key.name == "KEY_ESCAPE":
                    (board, mapping) = pop_group()
                    show_board(term, board)
                    clear_satus_row(term, status_row)
                    continue

                # --- Handling Printable Characters ---
                elif key.is_sequence and key.code is None:
                    # Filter out strange terminal sequences we don't care about
                    pass
                elif key.isprintable():
                    pos = board.find(key)
                    if pos == -1:
                        continue
                    if key not in mapping:
                        continue
                    e = mapping[key]
                    if not e.unicode:
                        (board, mapping) = push_group(e.emojis)
                        show_board(term, board)
                        show_status(term, status_row, e)
                        continue
                    # it must be an Emoji
                    show_status(term, status_row, e)
                    ipos = int((cursor_x - 2) / 2)
                    text_buffer = text_buffer[:ipos] + e.char + text_buffer[ipos:]
                    cursor_x += 2

                # Handling Ctrl+C exit explicitly (standard interrupt still works)
                elif key.name == "KEY_CTRL_C":
                    break

            # In blessed, we print immediately rather than calling a single refresh()
            # We use flush=True on prints to ensure immediate display

    print(text_buffer, end="")


if __name__ == "__main__":
    main()
