import logging as log
import sys
from blessed import Terminal
from blessed.keyboard import Keystroke
from wcwidth import wcswidth
import textwrap

from config import load_config, Config
from emojis import special_name_map, get_emojis_groups, Emoji
from board import Board, make_board
from tools import get_state_file, run_command


class DoneException(Exception):
    pass


missing_key_names = {
    # by sequence
    # which kitty_protocol enabled these are note mapped to names
    "\x1b[1;129A": "KEY_UP",
    "\x1b[1;129B": "KEY_DOWN",
    "\x1b[1;129C": "KEY_RIGHT",
    "\x1b[1;129D": "KEY_LEFT",
    "\x1b[5;129~'": "KEY_PGUP",
    "\x1b[6;129~'": "KEY_PGDOWN",
    # ghostty
    "\x1b[3;129~": "KEY_DELETE",
    # by code
    262: "KEY_HOME",
    333: "KEY_DELETE",
    360: "KEY_END",
    339: "KEY_PGUP",
    338: "KEY_PGDOWN",
    " ": "KEY_SPACE",
}


class TerminalKeyboard:

    def __init__(self, config: Config, daemon: bool = False):
        self.config = config
        self.daemon = daemon
        # use list instead of str to keep graphemes together -
        # makes deletion and cursor movement easier
        self.emoji_input: list[str] = []
        self.emoji_input_cursor: int = 0
        # search field
        self.search_input: str = ""
        self.search_input_cursor: int = 0
        self.search_input_selection: bool = False
        # cursor position on the terminal
        self.cursor_x: int = 2
        self.cursor_y: int = 0
        self.prefix_key: bool = False

        (self.all_emojis, self.emoji_groups) = get_emojis_groups(self.config)
        self.board: Board = make_board(self.config, self.all_emojis, self.emoji_groups)

        self.term_board: list[list[tuple[str, Emoji | None]]] = []
        self.term = Terminal()
        self.make_term_board(self.board._emojis)

    def make_term_board(self, emojis: list[Emoji]):
        log.info("Making terminal board...")
        term_board: list[list[tuple[str, Emoji | None]]] = []
        i = self.board._offset
        for row in self.board._rows:
            term_row = []
            for key in row:
                if key == " ":
                    term_row.append((" ", None))
                elif key == "\n":
                    pass
                elif i < len(emojis):
                    term_row.append((key, emojis[i]))
                    i += 1
                else:
                    term_row.append((key, None))
            term_board.append(term_row)
        log.info("Terminal board made.")
        self.term_board = term_board

    def pad_emoji(self, emoji: Emoji | None) -> str:
        if not emoji:
            return "   "
        if emoji.unicode in special_name_map:
            e_char = special_name_map[emoji.unicode]
            pad = 3 - len(e_char)
            e_char = self.term.cyan(e_char)
        else:
            e_char = emoji.char
            pad = 3 - wcswidth(e_char)
        return f"{e_char}{' ' * pad}"

    def show_board(self):
        log.info("Displaying board...")
        current_key = self.board._current_key
        for i, line in enumerate(self.term_board):
            with self.term.location(0, 2 + i):
                term_line = ""
                for k, e in line:
                    if k == current_key:
                        if self.cursor_y == 0:
                            k = self.term.on_bright_black(k)
                        else:
                            k = self.term.reverse(k)
                    if e and e.mark in ("⭐️", "🟡"):
                        k = self.term.yellow(k)
                    if e and e.mark in ("🟤",):
                        k = self.term.lightsalmon(k)
                    term_line += f"{k}{self.pad_emoji(e)}"
                print(term_line + self.term.clear_eol, end="")
        log.info("Board displayed.")

    def hide_and_insert(self, text: str):
        run_command([self.config.terminal.close_cmd], input=text)
        self.emoji_input.clear()
        self.emoji_input_cursor = 0

    def run(self):
        result = ""
        print("\033]2;Emoji Kbd\007", end="", flush=True)  # Set terminal title

        # Context manager clears the screen on entry/exit
        with self.term.cbreak(), self.term.fullscreen(), self.term.enable_kitty_keyboard():
            while True:
                try:
                    self.paint_and_handle_key_press()
                except DoneException:
                    # output final text
                    result = "".join(self.emoji_input)
                    log.info(f"Final emoji text: {result} ({result!r})")
                    if not self.daemon:
                        break
                    self.hide_and_insert(result)
        print(result, end="", flush=True)

    def get_cursor_x(self) -> int:
        key = self.board._current_key
        line_str = ""
        for i, (k, e) in enumerate(self.term_board[self.board.cursor_y]):
            if k == key:
                return wcswidth(line_str)
            line_str += k + self.pad_emoji(e)
        return 0

    def paint_and_handle_key_press(self):
        log.info("Painting board...")
        term = self.term
        board = self.board
        col = self.board.cursor_x
        row = self.board.cursor_y
        cursor_x = self.cursor_x
        cursor_y = self.cursor_y
        is_emoji_input = cursor_y == 0 and cursor_x < term.width // 2
        is_search_input = cursor_y == 0 and cursor_x > term.width // 2
        is_board = cursor_y > 0

        required_width = board.width * 4 - 1
        required_height = 2 + board._height
        log.info(f"Terminal size {term.width}x{term.height}.")
        log.info(f"Required size {required_width}x{required_height}")
        if required_width > term.width or required_height > term.height:
            print(term.clear, end="")
            print(f"Terminal too small with {term.width}x{term.height}.")
            print(f"Minimum size is {required_width}x{required_height}!")
            print("Please resize and press any key again.")
            term.inkey()
            return

        input_width = required_width // 2 - 2
        emoji_str = "".join(self.emoji_input)
        emoji_field = f"{emoji_str}" + " " * (input_width - wcswidth(emoji_str))
        input_width = required_width // 2 - 3
        search_str = self.search_input
        if self.search_input_selection:
            search_str = term.reverse(search_str)
            input_width += len(search_str) - len(self.search_input)
        search_str = f"{search_str:<{input_width+1}}"
        inputs = f"> {term.on_bright_black(emoji_field)}   ⌕ {term.on_bright_black(search_str)}"

        # determine cursor position
        if is_emoji_input:
            cursor_x = 2 + wcswidth(
                "".join(self.emoji_input[: self.emoji_input_cursor])
            )
        elif is_search_input:
            cursor_x = (
                wcswidth(emoji_field)
                + 7
                + wcswidth(self.search_input[: self.search_input_cursor])
            )
        elif is_board:
            cursor_y = 2 + self.board.cursor_y
            cursor_x = self.get_cursor_x()

        log.info(f"Terminal cursor at x={cursor_x}, y={cursor_y}")
        log.info(f"Board cursor at col={col}, row={row}")

        self.make_term_board(self.board._emojis)

        # draw everything
        with term.hidden_cursor():
            with term.location(0, 0):
                print(inputs + term.clear_eol, end="")
            with term.location(0, 1):
                print(term.clear_eol, end="")
            self.show_board()
            if term.height > 2 + board._height:
                with term.location(0, 2 + board._height):
                    print(term.clear_eol, end="")
            self.show_status(self.board.get_emoji())

        if is_emoji_input or is_search_input:
            print(term.normal_cursor + "\x1b[5 q", end="")
            print(term.move_xy(cursor_x, cursor_y), end="")
        else:
            print(term.hide_cursor, end="")
        print(end="", flush=True)

        log.info("Waiting for a keypress ......................")
        key: Keystroke | str | None = None
        while not key:
            key = term.inkey(timeout=0.1, esc_delay=0.05)
        log.info(f"Key pressed: '{key.name}' '{key.code}' {key!r}")

        is_printable = key.isprintable()
        key = missing_key_names.get(
            key, missing_key_names.get(key.code, key.name or key)
        )
        if key == None:
            return
        log.info(f"Handling key: '{key}' {is_printable}...")

        if key == "KEY_RESIZE":
            log.info(f"Terminal resized to {term.width}x{term.height}")
            return

        if key == "KEY_CTRL_C":
            raise KeyboardInterrupt

        is_enter = key in ("KEY_ENTER", "KEY_SHIFT_ENTER")
        is_cursor = key in (
            "KEY_UP",
            "KEY_DOWN",
            "KEY_LEFT",
            "KEY_RIGHT",
            "KEY_HOME",
            "KEY_END",
        )

        if is_emoji_input and is_enter:
            raise DoneException()
        elif key == "KEY_TAB":
            if is_board:
                self.cursor_y = 0
                self.cursor_x = 0
                if board.is_search:
                    board.pop_board()
            else:
                self.cursor_y = 2 + row
            return
        elif key == "KEY_CTRL_I":
            self.cursor_y = 0
            self.cursor_x = 0
            if board.is_search:
                board.pop_board()
            return
        elif key == "KEY_CTRL_F":
            self.cursor_y = 0
            self.cursor_x = term.width
            self.search_input_selection = True
            board.search(self.search_input)
            return

        if is_search_input and not is_cursor and self.search_input_selection:
            self.search_input = ""
            self.search_input_cursor = 0
        self.search_input_selection = False

        if key == "KEY_ESCAPE":
            board.pop_board()
            if is_search_input:
                self.cursor_x = 0
            return
        elif key == "KEY_BACKSPACE":
            if is_emoji_input or is_board:
                c = self.emoji_input_cursor
                s = self.emoji_input
                s = s[: c - 1] + s[c:]
                self.emoji_input = s
                if c > 0:
                    self.emoji_input_cursor -= 1
            elif is_search_input:
                c = self.search_input_cursor
                if c > 0:
                    s = self.search_input
                    s = s[: c - 1] + s[c:]
                    self.search_input = s
                    self.search_input_cursor -= 1
                board.search(self.search_input)
            return
        elif key == "KEY_DELETE":
            if is_emoji_input or is_board:
                s = self.emoji_input
                c = self.emoji_input_cursor
                s = s[:c] + s[c + 1 :]
                self.emoji_input = s
            elif is_search_input:
                s = self.search_input
                c = self.search_input_cursor
                s = s[:c] + s[c + 1 :]
                self.search_input = s
                board.search(self.search_input)
            return
        elif key == "KEY_PGUP":
            board.scroll(-1)
            return
        elif key == "KEY_PGDOWN":
            board.scroll(1)
            return
        elif key == "KEY_HOME":
            if is_emoji_input:
                self.emoji_input_cursor = 0
            elif is_search_input:
                self.search_input_cursor = 0
            elif is_board:
                board.move_cursor(-100, 0)
        elif key == "KEY_END":
            if is_emoji_input:
                self.emoji_input_cursor = len(self.emoji_input)
            elif is_search_input:
                self.search_input_cursor = len(self.search_input)
            elif is_board:
                board.move_cursor(100, 0)
        elif key == "KEY_LEFT":
            if is_emoji_input and self.emoji_input_cursor > 0:
                self.emoji_input_cursor -= 1
            elif is_search_input:
                if self.search_input_cursor > 0:
                    self.search_input_cursor -= 1
                else:
                    self.cursor_x = 0
                    board.pop_board()
            elif is_board:
                board.move_cursor(-1, 0)
        elif key == "KEY_RIGHT":
            if is_emoji_input:
                if self.emoji_input_cursor < len(self.emoji_input):
                    self.emoji_input_cursor += 1
                else:
                    self.cursor_x = term.width
                    self.search_input_selection = True
                    board.search(self.search_input)
            elif is_search_input:
                if self.search_input_cursor < len(self.search_input):
                    self.search_input_cursor += 1
                else:
                    board.move_cursor(1, 0)
            elif is_board:
                board.move_cursor(1, 0)
        elif key == "KEY_DOWN":
            if is_emoji_input or is_search_input:
                self.cursor_y = 2
            elif is_board:
                board.move_cursor(0, 1)
        elif key == "KEY_UP":
            if is_board:
                if cursor_y == 2:
                    self.cursor_x = 0
                    self.cursor_y = 0
                    if board.is_search:
                        board.pop_board()
                else:
                    board.move_cursor(0, -1)
        elif is_search_input and is_printable:
            s = self.search_input
            c = self.search_input_cursor
            s = s[:c] + key + s[c:]
            self.search_input = s
            self.search_input_cursor += 1
            board.search(self.search_input)
            self.make_term_board(board._emojis)
            return
        elif is_board and board.is_recent:
            if key == "KEY_SHIFT_ENTER":
                board.recent_toggle_favorite()
                return
            elif key == "KEY_SHIFT_LEFT":
                board.move_recent_emoji(-1)
                return
            elif key == "KEY_SHIFT_RIGHT":
                board.move_recent_emoji(1)
                return
            elif key == "KEY_SHIFT_DELETE":
                board.recent_delete()
                return
        elif key == "KEY_SPACE":
            self.prefix_key = True
            return

        if is_printable:
            if not board.get_emoji_for_key(key):
                return
            board.set_cursor_to_key(key)

        e = board.get_emoji()
        if not e:
            return

        if is_board and is_cursor:
            return
        if is_cursor or (not is_printable and not is_enter):
            return

        # enter a sub board
        if e.emojis and (not e.unicode or self.prefix_key):
            self.prefix_key = False
            board.push_board(e.emojis)
            self.make_term_board(board._emojis)
            return
        if board.is_settings:
            board.push_key(board.current_key)
            self.make_term_board(board._emojis)
            return
        self.prefix_key = False

        # it must be an Emoji so insert it
        self.emoji_input.insert(self.emoji_input_cursor, e.char)
        self.emoji_input_cursor += 1
        board.recent_add()

        if is_search_input:
            self.cursor_x = 0
            if board.is_search:
                board.pop_board()

    def show_status(self, emoji: Emoji | None):
        term = self.term
        status_row: int = 2 + self.board._height + 1

        if status_row >= term.height:
            return

        msgs: list[str] = []

        page_of_pages = self.board.page_of_pages
        if page_of_pages[1] > 1:
            msgs.append("{}/{}".format(*page_of_pages))

        if emoji:
            if emoji.emojis:
                msgs.append(f"{len(emoji.emojis)} emojis")
            msgs.append(emoji.char)
            if emoji.unicode:
                msgs.append(emoji.unicode)
            if emoji.name:
                msgs.append(emoji.name)
            if emoji.subgroup:
                msgs.append(f"{emoji.group} > {emoji.subgroup}")
            else:
                msgs.append(f"{emoji.group}")
            if emoji.tags:
                msgs.append(emoji.tags)

        msgs = "; ".join(msgs).split("\n")
        msgs = [m.strip() for m in msgs if m.strip()]
        wrapped_msgs: list[str] = []
        for line in msgs:
            wrapped = textwrap.wrap(line, width=term.width - 1)
            wrapped_msgs.extend(wrapped)
        wrapped_msgs.extend([""] * 4)  # clear old lines
        for i in range(min(len(wrapped_msgs), term.height - status_row)):
            with term.location(0, status_row + i):
                print(wrapped_msgs[i] + term.clear_eol, end="")


if __name__ == "__main__":
    config = load_config()
    log.basicConfig(
        force=True,
        filename=get_state_file("termkbd.log"),
        filemode=config.logging.log_mode,
        level=config.logging.log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    log.info(f"Starting terminal Emoji Keyboard on {sys.platform}...")
    try:
        daemon = False
        if len(sys.argv) >= 2 and sys.argv[1] == "--daemon":
            daemon = True
        term_keyboard = TerminalKeyboard(config, daemon)
        term_keyboard.run()
    except KeyboardInterrupt:
        pass
