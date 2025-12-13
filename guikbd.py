import sys
from typing import Callable

import qdarkstyle

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QStyle,
)
from PyQt6.QtGui import (
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QFont,
    QColor,
    QWheelEvent,
    QIcon,
)
from PyQt6.QtCore import Qt, QRect, QObject, QEvent

import logging as log

from boards import get_emojis_boards, Emoji, make_mapping, kbd, kbd_board

# TODO change input field and search to be in one line
# TODO add "scrollbar"
# TODO add more layouts
# TODO add config


start_x = 10
start_y = 52
key_width = 40
key_height = 40
key_padding = 5


def winlin(windows_value: int, linus_value: int) -> int:
    if sys.platform.startswith("win"):
        return windows_value
    else:
        return linus_value

# Map of special unicode codes to short names for display on keys
special_name_map = {
    "0020": "SP",  # SPACE
    "00A0": "NBS",  # NO-BREAK SPACE
    "202F": "nNBS",  # NARROW NO-BREAK SPACE
    "2000": "ENQ",  # EN QUAD
    "2001": "EMQ",  # EM QUAD
    "2002": "ENS",  # EN SPACE
    "2003": "EMS",  # EM SPACE
    "2004": "3EMS",  # THREE-PER-EM SPACE
    "2005": "4EMS",  # FOUR-PER-EM SPACE
    "2006": "6EMS",  # SIX-PER-EM SPACE
    "2007": "FS",  # FIGURE SPACE
    "2008": "PS",  # PUNCTUATION SPACE
    "2009": "TS",  # THIN SPACE
    "200A": "HS",  # HAIR SPACE
}

class KeyboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        log.info("Creating main window...")
        self.setWindowIcon(QIcon("emoji-kbd.ico"))
        self.setWindowTitle("Emoji Kbd")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        # self.setWindowFlag(Qt.WindowType.Tool, True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.max_chars = sum(1 for char in kbd if not char.isspace())
        log.info(f"{self.max_chars} chars on board.")
        (self.emojis, self.board) = get_emojis_boards()
        log.info(f"{len(self.emojis)} emojis in {len(self.board)} groups loaded.")
        self.recent_list = Emoji(name="Recent", char="⟲")
        self.recent_list.emojis = []
        self.recent_offset = 0
        self.load_recent()
        self.search_results = Emoji(name="Search Results", char="🔎")
        self.search_results.emojis = []
        self.search_offset = 0
        self.board.insert(0, self.recent_list)
        self.board.insert(1, self.search_results)

        self.board_path: list[list[Emoji]] = []
        self.mapping: dict[str, Emoji] = {}  # mapping of key to Emoji
        self.offset = 0
        self.push_board(self.board)
        self.current_key = ""
        self.prefix_key = False

        self.initUI()
        log.info("Creating main window done.")

    def initUI(self):
        # Set up event handlers
        self.setMouseTracking(True)
        self.installEventFilter(self)
        QApplication.instance().focusChanged.connect(self.handle_focus_change)  # type: ignore

        # Set up fonts
        self.key_font = QFont("Arial", 8)
        self.emoji_font = QFont("Noto Color Emoji", winlin(19, 20))
        self.emoji_font2 = QFont("Noto Color Emoji", winlin(19 + 5, 20 + 5))
        self.mark_font = QFont("Noto Color Emoji", 6)

        # Set up the main layout and elements
        main_vbox = QVBoxLayout()

        # Create horizontal layout for input and search fields
        top_hbox = QHBoxLayout()
        top_hbox.setSpacing(key_padding - 1)

        font_size = QApplication.font().pointSize()
        w = QLineEdit(self)
        w.setFont(QFont("Noto Color Emoji", font_size + 4))
        w.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        w.installEventFilter(self)
        self.emoji_input_field = w

        w = QLineEdit(self)
        w.setFixedHeight(self.emoji_input_field.sizeHint().height())
        w.font().setPointSize(font_size)
        w.setPlaceholderText("Search...")
        w.textChanged.connect(self.search_emojis)
        w.installEventFilter(self)
        self.search_field = w

        top_hbox.addWidget(self.emoji_input_field)
        top_hbox.addWidget(self.search_field)

        w = QLabel("Status: Ready", self)
        w.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        w.setFont(QFont("Arial", 9))
        w.setWordWrap(True)
        w.setFixedHeight(35)
        self.status_label = w

        main_vbox.addLayout(top_hbox)
        main_vbox.addStretch(1)
        main_vbox.addWidget(self.status_label)

        self.setLayout(main_vbox)

        # Calculate board position and window size
        board_cols = max(len(line) for line in kbd.splitlines())
        board_rows = len(kbd.splitlines())

        style = QApplication.style()
        if style:
            default_spacing = style.pixelMetric(
                QStyle.PixelMetric.PM_LayoutHorizontalSpacing
            )
            log.info(f"Default spacing: {default_spacing}")
            global start_y, start_x
            # start_x = default_spacing * 2 + 1
            start_x = (
                top_hbox.geometry().x()
                + self.emoji_input_field.geometry().x()
                + default_spacing * 2
                + 1
            )
            start_y = self.emoji_input_field.sizeHint().height() + default_spacing * 4

        width = (
            start_x
            + board_cols * (key_width + key_padding)
            + key_padding
            - winlin(-2, 0)
        )
        height = (
            start_y
            + board_rows * (key_width + key_padding)
            + key_padding
            + winlin(10, -2)
            + self.status_label.sizeHint().height()
        )
        self.setFixedSize(width, height)

    def paintEvent(self, _event):  # type: ignore
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        x = start_x
        y = start_y

        for row in kbd_board:
            for key in row:
                if key != " ":
                    rect = QRect(x, y, key_width, key_height)
                    pen = painter.pen()
                    pen.setWidth(1)
                    if self.current_key == key:
                        pen.setColor(self.palette().link().color())
                    else:
                        pen.setColor(QColor(128, 128, 128))  # gray outline
                    painter.setPen(pen)
                    painter.drawRoundedRect(rect, 5, 5)

                    painter.setPen(self.palette().text().color())

                    if key in self.mapping:
                        e = self.mapping[key]
                        char = e.char
                        if e.unicode in special_name_map:
                            painter.setFont(self.key_font)
                            char = special_name_map[e.unicode]
                        elif self.current_key == key:
                            painter.setFont(self.emoji_font2)
                        else:
                            painter.setFont(self.emoji_font)
                        rect = QRect(x + 1, y, key_width, key_height)
                        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, char)  # type: ignore

                        if e.mark:
                            if not e.mark.isalnum():  # special mark
                                painter.setFont(self.mark_font)
                                rect = QRect(x, y + 4, key_width - 2, key_height)
                            else:
                                painter.setFont(self.key_font)
                                rect = QRect(x, y + 2, key_width - 2, key_height)
                            painter.drawText(
                                rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop, e.mark  # type: ignore
                            )

                    painter.setFont(self.key_font)
                    rect = QRect(x + 2, y + 2, key_width, key_height)
                    painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, key)  # type: ignore

                x += key_width + key_padding

            x = start_x
            y += key_height + key_padding

    def match(self, text: str, needle: str) -> int:
        pos = text.find(needle)
        if pos == -1:
            return 0
        score = 1
        while pos != -1:
            if pos == 0:
                score += 7  # score match at word start higher
            elif not text[pos - 1].isalnum():
                score += 4
            end_pos = pos + len(needle)
            if end_pos == len(text):
                score += 5  # score match at word end higher
            elif not text[end_pos].isalnum():
                score += 2
            pos = text.find(needle, end_pos + 1)
        return score

    def filter_emojis(
        self,
        emojis: list[Emoji],
        needle: str,
        key: Callable[[Emoji], str],  # ear
        score_bonus: int = 1,
    ) -> list[Emoji]:
        matches: list[Emoji] = []
        for e in emojis:
            match_score = self.match(key(e), needle)
            if match_score:
                e.order += match_score * score_bonus
                matches.append(e)
        return matches

    def search_emojis(self, needle: str):
        self.search_results.emojis.clear()
        self.search_offset = 0
        self.offset = 0
        if not needle:
            self.search_results.emojis.extend(self.emojis)
            self.mapping = make_mapping(self.search_results.emojis)
            self.show_status(f"All {len(self.emojis)} emojis.")
            self.update()
            return
        needle = needle.lower()
        # list of matches with (score: int, emoji: Emoji)
        matches: list[Emoji] = self.emojis
        for e in matches:
            e.order = 0
        for n in needle.split(" "):
            if not n:
                continue
            if "," in n:
                (group, subgroup) = n.split(",", 1)
                if group:
                    matches = self.filter_emojis(matches, group, lambda e: e.group)
                if subgroup:
                    matches = self.filter_emojis(
                        matches, subgroup, lambda e: e.subgroup
                    )
            elif n.startswith("+"):
                n = n[1:].upper()
                if n:
                    matches = self.filter_emojis(matches, n, lambda e: e.unicode)
            elif n.startswith("#"):
                n = n[1:]
                if n:
                    matches = self.filter_emojis(matches, n, lambda e: e.tags)
            else:
                nmatches = self.filter_emojis(matches, n, lambda e: e.name, 1)
                tmatches = self.filter_emojis(matches, n, lambda e: e.tags, 1)
                matches = list(set(nmatches + tmatches))
        if matches:
            # for e in matches:  # show match score for debugging
            #     e.mark = str(e.order)
            matches.sort(key=lambda e: e.order, reverse=True)
            # Remove duplicates while preserving order
            matches_dict = {e.char: e for e in reversed(matches)}
            matches = list(reversed(matches_dict.values()))
            self.search_results.emojis.extend(matches)
            self.mapping = make_mapping(self.search_results.emojis)
            self.show_status(f"Found {len(matches)} matching emojis.")
        else:
            self.mapping = {}
            self.show_status("No matching emojis found.")
        self.update()

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.emoji_input_field.text())

    def show_status(self, obj: str | Emoji):
        if isinstance(obj, str) and obj in self.mapping:
            obj = self.mapping[obj]
        if isinstance(obj, Emoji):
            msg: list[str] = []
            if obj.unicode:
                msg.append(f"{obj.unicode}")
            if obj.name:
                msg.append(f"{obj.name}")
            if obj.group:
                if obj.subgroup:
                    msg.append(f"{obj.group} > {obj.subgroup}")
                else:
                    msg.append(f"{obj.group}")
            if obj.tags:
                msg.append(f" \n{obj.tags}")
            obj = ", ".join(msg)
        if len(obj) == 1:
            obj = ""
        self.status_label.setText(obj)

    def handle_focus_change(self, old, new):  # type: ignore
        if new == self.emoji_input_field:
            self.current_key = ""
            if self.board == self.search_results.emojis:
                self.pop_board()
            self.show_status(
                "Type key to insert emoji or open sub board. Use Space as prefix key to open variants board.\n"
                "Use Enter to close board and insert into app."
            )
        elif new == self.search_field:
            self.current_key = ""
            if self.board != self.search_results.emojis:
                if not self.search_results.emojis:
                    self.search_emojis(self.search_field.text())
                self.push_board(self.search_results.emojis)
            self.show_status(
                "Search emojis by name and tag, with '#' prefix by tag and '+' prefix by code.\n"
                "Use ',' to search group and/or subgroup, e.g. 'animal,', ',mammal' or 'ani,mam'."
            )
        elif new == self:
            if len(self.board_path) == 1:
                self.show_status(
                    "Cursor movement to select emoji/group, Enter inserts emoji or opens group.\n"
                    "PageUp/PageDown to scroll board, Esc/Backspace to go back to previous board."
                )
            else:
                self.show_status(self.current_key)

        self.update()

    def eventFilter(self, source: QObject, event: QEvent):  # type: ignore
        if (
            event
            and event.type() == QEvent.Type.KeyPress
            and isinstance(event, QKeyEvent)
        ):
            if self.handle_keyboard_press(source, event):
                return True

        return super().eventFilter(source, event)

    def add_to_recent(self, emoji: Emoji):
        if emoji.char not in [e.char for e in self.recent_list.emojis]:
            emoji = emoji.clone()
            self.recent_list.emojis.append(emoji)
        emoji = next(e for e in self.recent_list.emojis if e.char == emoji.char)
        if emoji.order < 100:
            emoji.order += 10
            if emoji.order >= 100:
                emoji.order = 100
                emoji.mark = "⭐️"
            elif emoji.order > 0:
                emoji.mark = str(emoji.order)
            else:
                emoji.order = 0
                emoji.mark = ""
        for e in self.recent_list.emojis:
            if e != emoji and e.order < 100:
                if e.order > 0:
                    e.order -= 1
                if e.order > 0:
                    e.mark = str(e.order)
                else:
                    e.mark = ""
                    e.order = 0
        # sort and keep only top 100
        self.recent_list.emojis.sort(key=lambda e: e.order, reverse=True)
        self.recent_list.emojis = self.recent_list.emojis[:100]

    def load_recent(self):
        try:
            with open("recent.txt", "r", encoding="utf-8") as f:
                recent_list = []
                for l in f.readlines():
                    (order, char, unicode, name, group, subgroup, tags) = (
                        l.strip().split(";", 6)
                    )
                    order = int(order)
                    e = Emoji(*(char, unicode, group, subgroup, name, tags))
                    if order >= 100:
                        e.mark = "⭐️"
                    elif order > 0:
                        e.mark = str(order)
                    else:
                        e.mark = ""
                        order = 0
                    e.order = order
                    recent_list.append(e)
                # Remove duplicates while preserving order
                recent_list = {e.char: e for e in reversed(recent_list)}
                recent_list = list(reversed(recent_list.values()))
                # Ensure order
                recent_list.sort(key=lambda e: e.order, reverse=True)
                self.recent_list.emojis = recent_list
        except Exception as ex:
            log.error(f"Restoring recent emojis: {ex}")

    def save_recent(self):
        try:
            with open("recent.txt", "w", encoding="utf-8") as f:
                for e in self.recent_list.emojis:
                    f.write(
                        f"{e.order};{e.char};{e.unicode};{e.name};{e.group};{e.subgroup};{e.tags}\n"
                    )
        except Exception as ex:
            log.error(f"Saving recent emojis: {ex}")

    def insert_emoji(self, emoji: Emoji):
        self.emoji_input_field.insert(emoji.char)
        self.add_to_recent(emoji)
        self.copy_to_clipboard()
        self.show_status(f"{emoji.unicode}, {emoji.name}, {emoji.tags}")

    def push_board(self, emojis: list[Emoji]):
        self.board_path.append(emojis)
        self.board = emojis
        if self.recent_list.emojis == emojis:
            self.offset = self.recent_offset
        elif self.search_results.emojis == emojis:
            self.offset = self.search_offset
        else:
            self.offset = 0
        self.mapping = make_mapping(emojis, self.offset)
        self.update()

    def pop_board(self):
        if len(self.board_path) > 1:
            emojis = self.board_path.pop()
            if self.recent_list.emojis == emojis:
                self.recent_offset = self.offset
            elif self.search_results.emojis == emojis:
                self.search_offset = self.offset
        emojis = self.board_path[-1]
        self.board = emojis
        self.offset = 0
        self.mapping = make_mapping(emojis, self.offset)
        self.update()

    def handle_key(self, key: str):
        if key not in self.mapping:
            return
        self.current_key = key
        e = self.mapping[key]
        if not self.prefix_key and e.unicode:
            self.insert_emoji(e)
        elif e.emojis:
            self.push_board(e.emojis)
        if key in self.mapping:
            e = self.mapping[key]
            self.show_status(e)
        self.update()

    def handle_close(self):
        self.copy_to_clipboard()
        self.save_recent()
        try:
            print(self.emoji_input_field.text())
        except UnicodeEncodeError:
            log.error("Cannot print emoji to console due to encoding error.")
        self.quit()

    def quit(self):
        log.info("Quitting emoji keyboard...")
        self.close()
        QApplication.quit()

    def handle_keyboard_press(self, source: QObject, event: QKeyEvent):
        key = event.key()
        key_text = event.text()

        if (
            source in (self, self.emoji_input_field)
            and event.modifiers() == Qt.KeyboardModifier.NoModifier
            and len(key_text) == 1  # single character for safety
            and key >= 32  # space
            and key != 127  # delete
            and key <= 255  # latin-1
        ):
            if key_text == " ":
                self.prefix_key = key_text == " "
            elif key_text in self.mapping:
                self.handle_key(key_text)
                self.prefix_key = False
            elif key_text.upper() in self.mapping:
                self.handle_key(key_text.upper())
                self.prefix_key = False

        elif key == Qt.Key.Key_Backtab:
            if source is self.emoji_input_field:
                if not self.current_key:
                    self.current_key = self.get_nearest_char(0, 0)
                self.setFocus()
            elif source is self.search_field:
                self.emoji_input_field.setFocus()
            else:
                self.search_field.setFocus()
            self.update()

        elif key == Qt.Key.Key_Tab:
            if source is self.emoji_input_field:
                self.search_field.setFocus()
            elif source is self.search_field:
                if not self.current_key:
                    self.current_key = self.get_nearest_char(0, 0)
                self.setFocus()
            else:
                self.emoji_input_field.setFocus()
            self.update()

        elif key in (
            Qt.Key.Key_Left,
            Qt.Key.Key_Right,
            Qt.Key.Key_Up,
            Qt.Key.Key_Down,
            Qt.Key.Key_Home,
            Qt.Key.Key_End,
        ):
            return self.handle_cursor_navigation(source, key)

        elif key == Qt.Key.Key_Escape or (
            key == Qt.Key.Key_Backspace and source == self
        ):
            self.pop_board()
            self.show_status(self.current_key)
            if source is self.search_field:
                self.emoji_input_field.setFocus()
            self.update()

        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if source is self.emoji_input_field:
                self.handle_close()
            elif source is self.search_field:
                self.current_key = self.get_nearest_char(0, 0)
                self.insert_emoji(self.mapping[self.current_key])
                self.emoji_input_field.setFocus()
                self.update()
            elif source is self and self.current_key:
                self.handle_key(self.current_key)

        elif key == Qt.Key.Key_PageUp:
            self.scroll_board(1)

        elif key == Qt.Key.Key_PageDown:
            self.scroll_board(-1)

        else:
            return False

        return True

    def scroll_board(self, direction: int):
        if direction > 0:
            if self.offset > 0:
                self.offset -= self.max_chars
                self.mapping = make_mapping(self.board, self.offset)
                self.update()

        if direction < 0:
            if self.offset < len(self.board) - self.max_chars:
                self.offset += self.max_chars
                self.mapping = make_mapping(self.board, self.offset)
                self.update()

        self.show_status(self.current_key)

    def wheelEvent(self, event: QWheelEvent | None) -> None:  # type: ignore
        if event:
            self.scroll_board(event.angleDelta().y())
        return super().wheelEvent(event)

    def get_nearest_char(self, col: int, row: int, left_only: bool = False) -> str:
        kbrow = kbd_board[row]
        if col < 0:
            col = len(kbrow) - 1
        elif col >= len(kbrow):
            col = len(kbrow) - 1
        if kbrow[col] != " ":
            return kbrow[col]
        for i in range(len(kbrow)):
            if not left_only and col + i < len(kbrow) and kbrow[col + i] != " ":
                return kbrow[col + i]
            if col - i >= 0 and kbrow[col - i] != " ":
                return kbrow[col - i]
        return ""

    def get_key_pos(self, char: str) -> tuple[int, int] | None:
        for row, line in enumerate(kbd_board):
            col = line.find(char)
            if col > -1:
                return (col, row)
        return None

    def handle_cursor_navigation(self, source: QObject, key: int):
        if key == Qt.Key.Key_Down and source is not self:
            if not self.current_key:
                self.current_key = self.get_nearest_char(0, 0)
            self.setFocus()
            self.update()
            return True
        elif key == Qt.Key.Key_Right and source is self.emoji_input_field:
            s = self.emoji_input_field.text()
            if (
                self.emoji_input_field.cursorPosition()
                == len(s.encode("utf-16-le")) // 2
            ):
                self.search_field.setFocus()
        elif key == Qt.Key.Key_Left and source is self.search_field:
            if self.search_field.cursorPosition() == 0:
                self.emoji_input_field.setFocus()
        elif source is self:
            pos = self.get_key_pos(self.current_key)
            if not pos:
                return False
            if key == Qt.Key.Key_Home:
                self.current_key = self.get_nearest_char(0, pos[1])
            elif key == Qt.Key.Key_End:
                self.current_key = self.get_nearest_char(-1, pos[1], True)
            elif key == Qt.Key.Key_Up:
                if pos[1] == 0:
                    self.emoji_input_field.setFocus()
                else:
                    self.current_key = self.get_nearest_char(pos[0], pos[1] - 1)
            elif key == Qt.Key.Key_Down:
                if pos[1] + 1 < len(kbd_board):
                    self.current_key = self.get_nearest_char(pos[0], pos[1] + 1)
            elif key == Qt.Key.Key_Left:
                if pos[0] > 0:
                    self.current_key = self.get_nearest_char(pos[0] - 1, pos[1], True)
                elif pos[1] > 0:
                    self.current_key = self.get_nearest_char(-1, pos[1] - 1, True)
            elif key == Qt.Key.Key_Right:
                if pos[0] + 1 < len(kbd_board[pos[1]]):
                    self.current_key = self.get_nearest_char(pos[0] + 1, pos[1])
                elif pos[1] + 1 < len(kbd_board):
                    self.current_key = self.get_nearest_char(0, pos[1] + 1)
            self.show_status(self.current_key)
            self.update()
            return True
        return False

    def get_char_from_position(self, x: int, y: int) -> str | None:
        col = (x - start_x) // (key_width + key_padding)
        row = (y - start_y) // (key_height + key_padding)
        if row >= 0 and col >= 0 and row < len(kbd_board) and col < len(kbd_board[row]):
            xp = start_x + col * (key_width + key_padding) + key_width - 2 * key_padding
            yp = start_y + row * (key_height + key_padding) + 2 * key_padding
            # print(f"Mouse at row {row}, col {col} {x},{y} vs {xp},{yp}")
            if x >= xp and y <= yp:
                self.prefix_key = True
            else:
                self.prefix_key = False
            return kbd_board[row][col]
        return None

    def mousePressEvent(self, event: QMouseEvent | None) -> None:  # type: ignore
        if not event:
            return super().mousePressEvent(event)

        if event.type() == QEvent.Type.MouseButtonDblClick:
            self.handle_close()
        elif self.underMouse() and event.type() == QEvent.Type.MouseButtonPress:
            button = event.button()
            self.setFocus()
            (x, y) = (event.pos().x(), event.pos().y())
            if button == Qt.MouseButton.LeftButton:
                char = self.get_char_from_position(x, y)
                if char:
                    self.handle_key(char)
                    self.current_key = char
            elif button == Qt.MouseButton.RightButton:
                self.pop_board()
                char = self.get_char_from_position(x, y)
                if char in self.mapping:
                    self.show_status(self.mapping[char])
                self.update()

        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:  # type: ignore
        if event:
            char = self.get_char_from_position(event.pos().x(), event.pos().y())
            if char and char != self.current_key:
                self.show_status(char)
                self.current_key = char
                self.update()
        return super().mouseMoveEvent(event)


if __name__ == "__main__":
    log.basicConfig(
        # filename='app.log',
        # filemode='a',
        level=log.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    log.info(f"Starting Emoji Keyboard on {sys.platform}...")
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("emoji-kbd.ico"))
    app.setQuitOnLastWindowClosed(True)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())
    window = KeyboardWidget()
    log.info("Starting main window...")
    window.show()
    # for t in ("ear", "ear ", " ear", " ear "):
    #     log.info(f"Testing match function with '{t}': {window.match(t, 'ear')}")
    # for t in ("ears", " ears", "ears ", " ears ", " ears "):
    #     log.info(f"Testing match function with '{t}': {window.match(t, 'ear')}")
    # for t in ("hear", " hear", "hear ", " hear ", " hear"):
    #     log.info(f"Testing match function with '{t}': {window.match(t, 'ear')}")
    # for t in (" ear, hear", " ear, hear ", "hear ", " hear ", " hear"):
    #     log.info(f"Testing match function with '{t}': {window.match(t, 'ear')}")
    sys.exit(app.exec())
