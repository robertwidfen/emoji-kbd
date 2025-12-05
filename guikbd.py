import sys
# import qdarktheme  # type: ignore
import qdarkstyle

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QLabel,
)
from PyQt6.QtGui import QKeyEvent, QMouseEvent, QPainter, QFont, QColor, QWheelEvent
from PyQt6.QtCore import Qt, QRect, QObject, QEvent

from boards import get_emojis_groups, Emoji

# TODO add more layouts
# TODO add config
# TODO add recent emojis
# TODO add skin tone support
# TODO add "scrollbar"

# DE QWERTZ keyboard layout
kbd = """
1234567890ß´
qwertzuiopü+
asdfghjklöä#
<yxcvbnm,.-
""".strip()

# Corne bone keyboard layout
kbd = """
jduax phlmw
ctieo bnrsg
?,vfq ykz.-
""".strip()

kbd_board = kbd.splitlines()


def make_mapping(objs: list[Emoji], offset: int = 0) -> dict[str, Emoji]:
    mapping: dict[str, Emoji] = {}
    i = offset
    for k in kbd:
        if k not in (" ", "\n"):
            if i < len(objs):
                mapping[k] = objs[i]
                i += 1
    return mapping


start_x = 10
start_y = 52
key_width = 40
key_height = 40
key_padding = 5


class KeyboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.max_chars = sum(1 for char in kbd if not char.isspace())
        (self.emojis, self.groups) = get_emojis_groups()
        self.recent_list = Emoji(name="Recent", char="⟲")
        self.recent_list.emojis = []
        self.load_recent()
        self.search_results = Emoji(name="Search Results", char="🔎")
        self.search_results.emojis = []
        self.groups.insert(0, self.recent_list)
        self.groups.insert(1, self.search_results)

        self.groups_path: list[list[Emoji]] = []
        self.mapping: dict[str, Emoji] = {}
        self.offset = 0
        self.push_group(self.groups)
        self.current_char = ""
        self.prefix_key = False

        board_cols = max(len(line) for line in kbd.splitlines())
        board_rows = len(kbd.splitlines())

        width = start_x + board_cols * (key_width + key_padding) + key_padding
        height = start_y + board_rows * (key_width + key_padding) + key_padding + 73
        self.setGeometry(100, 100, width, height)
        self.setMouseTracking(True)
        QApplication.instance().focusChanged.connect(self.handle_focus_change)  # type: ignore
        self.setWindowTitle("Emoji Keyboard")

        self.initUI()

    def initUI(self):
        self.installEventFilter(self)
        main_vbox = QVBoxLayout()

        self.emoji_input_field = QLineEdit(self)
        self.emoji_input_field.setFont(QFont("Noto Color Emoji", 16))
        self.emoji_input_field.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self.emoji_input_field.installEventFilter(self)

        self.search_field = QLineEdit(self)
        self.search_field.textChanged.connect(self.filter_emojis)  # type: ignore
        # self.search_field.setTextMargins(4, 14, 4, 0)
        self.search_field.setPlaceholderText("Search by category, name or tags...")
        self.search_field.installEventFilter(self)

        self.status_label = QLabel("Status: Ready", self)
        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.status_label.setFont(QFont("Arial", 9))
        self.status_label.setWordWrap(True)
        self.status_label.setFixedHeight(30)

        main_vbox.addWidget(self.emoji_input_field)
        main_vbox.addStretch(1)
        main_vbox.addWidget(self.search_field)
        main_vbox.addWidget(self.status_label)

        self.setLayout(main_vbox)

    def paintEvent(self, _event):  # type: ignore
        painter = QPainter(self)

        x = start_x
        y = start_y

        self.key_font = QFont("Arial", 8)
        self.emoji_font = QFont("Noto Color Emoji", 20)
        self.mark_font = QFont("Noto Color Emoji", 6)

        for row in kbd_board:
            for char in row:
                if char != " ":
                    rect = QRect(x, y, key_width, key_height)
                    if self.current_char == char:
                        painter.setPen(self.palette().link().color())
                    else:
                        painter.setPen(QColor(128, 128, 128))  # gray outline
                    painter.drawRoundedRect(rect, 5, 5)

                    # 3. Emoji (Emoji Font) zeichnen
                    if char in self.mapping:
                        e = self.mapping[char]
                        painter.setFont(self.emoji_font)
                        rect = QRect(x + 1, y, key_width, key_height)
                        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, e.char)  # type: ignore

                        if e.mark:
                            painter.setFont(self.mark_font)
                            rect = QRect(x, y + 4, key_width - 2, key_height)
                            painter.drawText(
                                rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop, e.mark  # type: ignore
                            )

                    if char != "ß" and char.isalpha():
                        char = char.upper()
                    painter.setFont(self.key_font)
                    rect = QRect(x + 2, y + 2, key_width, key_height)
                    painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, char)  # type: ignore

                x += key_width + key_padding

            x = start_x
            y += key_height + key_padding

    def match(self, haystack: str, needle: str) -> int:
        pos = haystack.find(needle)
        if pos == -1:
            return 0
        if pos == 0 or not haystack[pos - 1].isalpha():
            return 2
        return 1

    def filter_emojis(self, search_term: str):
        search_term = search_term.lower()
        if not search_term:
            self.groups = self.emojis
            self.mapping = make_mapping(self.groups)
        else:
            matches: list[Emoji] = []
            for e in self.emojis:
                match = self.match(e.name, search_term) or self.match(
                    e.tags, search_term
                )
                if match and e not in matches:
                    e.score = match  # type: ignore
                    matches.append(e)
                # TODO search in group and subgroup too when ","" is used?
                # TODO search for each term when multiple terms are given?
                # TODO fuzzy search?
            if matches:
                self.search_results.emojis.clear()
                matches.sort(key=lambda e: e.score)  # type: ignore
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
            self.current_char = ""
            self.show_status("Type to select category or insert emojis.")
        elif new == self.search_field:
            if self.search_field.text() != "":
                if self.groups != self.search_results.emojis:
                    self.push_group(self.search_results.emojis)
            elif self.groups != self.emojis:
                self.push_group(self.emojis)

            self.current_char = ""
            self.show_status(
                "Type to filter emojis by category, subcategory, name and tags."
            )
        elif new == self:
            self.show_status(
                "Select category/emoji by cursor movement, open/insert by Enter, scroll by PageUp/PageDown, go back by Esc/Backspace."
            )
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
        if emoji not in self.recent_list.emojis:
            self.recent_list.emojis.append(emoji)
        if emoji.order < 100:
            emoji.order += 10
        if emoji.order >= 100:
            emoji.order = 100
            emoji.mark = "⭐️"
        else:
            emoji.mark = str(emoji.order)
        self.recent_list.emojis.sort(key=lambda e: e.order, reverse=True)
        for e in self.recent_list.emojis:
            if e != emoji and e.order < 100:
                if e.order > -100:
                    e.order -= 1
                e.mark = str(e.order)

    def load_recent(self):
        try:
            with open("recent.txt", "r", encoding="utf-8") as f:
                for l in f.readlines():
                    (order, unicode, char) = l.strip().split(",", 2)
                    e = Emoji(char=char, unicode=unicode, order=int(order))
                    if e.order >= 100:
                        e.order = 100
                        e.mark = "⭐️"
                    self.recent_list.emojis.append(e)
        except Exception as ex:
            print(f"Error restoring recent emojis: {ex}")

    def save_recent(self):
        try:
            with open("recent.txt", "w", encoding="utf-8") as f:
                for e in self.recent_list.emojis:
                    f.write(f"{e.order},{e.unicode},{e.char}\n")
        except Exception as ex:
            print(f"Error saving recent emojis: {ex}")

    def insert_emoji(self, emoji: Emoji):
        self.emoji_input_field.insert(emoji.char)
        self.add_to_recent(emoji)
        self.copy_to_clipboard()
        self.show_status(f"{emoji.unicode}, {emoji.name}, {emoji.tags}")

    def push_group(self, emojis: list[Emoji]):
        self.mapping = make_mapping(emojis)
        self.groups_path.append(emojis)
        self.groups = emojis
        self.offset = 0
        self.update()

    def pop_group(self):
        if len(self.groups_path) > 1:
            self.groups_path.pop()
        emojis = self.groups_path[-1]
        self.mapping = make_mapping(emojis)
        self.groups = emojis
        self.update()

    def handle_key(self, key: str):
        self.prefix_key = key == " "
        if key not in self.mapping:
            return

        self.current_char = key
        e = self.mapping[key]
        if e.emojis:
            self.push_group(e.emojis)
        else:
            if not self.prefix_key and e.unicode:
                self.insert_emoji(e)
            elif e.emojis:
                self.push_group(e.emojis)
        if key in self.mapping:
            e = self.mapping[key]
            self.show_status(e)
        self.update()

    def handle_keyboard_press(self, source: QObject, event: QKeyEvent):
        key = event.key()
        key_text = event.text()

        if (
            source in (self, self.emoji_input_field)
            and len(key_text) == 1
            and ord(key_text[0]) >= 32  # space
            and ord(key_text[0]) != 127  # delete
            and ord(key_text[0]) <= 255  # latin-1
        ):
            if key_text in self.mapping or key_text == " ":
                self.handle_key(key_text)

        elif key == Qt.Key.Key_Tab:
            if source is self.emoji_input_field:
                if not self.current_char:
                    self.current_char = self.get_nearest_char(0, 0)
                self.setFocus()
            elif source is self:
                self.search_field.setFocus()
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
            self.pop_group()
            self.show_status(self.current_char)
            if source is self.search_field:
                self.emoji_input_field.setFocus()
            self.update()

        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if source is self.emoji_input_field:
                self.copy_to_clipboard()
                self.save_recent()
                print(self.emoji_input_field.text())
                self.close()
            if source is self and self.current_char:
                self.handle_key(self.current_char)

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
                self.mapping = make_mapping(self.groups, self.offset)
                self.update()

        if direction < 0:
            if self.offset < len(self.groups) - self.max_chars:
                self.offset += self.max_chars
                self.mapping = make_mapping(self.groups, self.offset)
                self.update()

        self.show_status(self.current_char)

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
        if key == Qt.Key.Key_Down and source is self.emoji_input_field:
            if not self.current_char:
                self.current_char = self.get_nearest_char(0, 0)
            self.setFocus()
            self.update()
            return True
        elif key == Qt.Key.Key_Up and source is self.search_field:
            if not self.current_char:
                self.current_char = self.get_nearest_char(0, 0)
            if self.current_char in self.mapping:
                self.setFocus()
            else:
                self.emoji_input_field.setFocus()
                self.current_char = ""
            self.update()
            return True
        elif source is self:
            pos = self.get_key_pos(self.current_char)
            if not pos:
                return False
            if key == Qt.Key.Key_Home:
                self.current_char = self.get_nearest_char(0, pos[1])
            elif key == Qt.Key.Key_End:
                self.current_char = self.get_nearest_char(-1, pos[1], True)
            elif key == Qt.Key.Key_Up:
                if pos[1] == 0:
                    self.emoji_input_field.setFocus()
                else:
                    self.current_char = self.get_nearest_char(pos[0], pos[1] - 1)
            elif key == Qt.Key.Key_Down:
                if pos[1] + 1 == len(kbd_board):
                    self.search_field.setFocus()
                else:
                    self.current_char = self.get_nearest_char(pos[0], pos[1] + 1)
            elif key == Qt.Key.Key_Left:
                if pos[0] > 0:
                    self.current_char = self.get_nearest_char(pos[0] - 1, pos[1], True)
                elif pos[1] > 0:
                    self.current_char = self.get_nearest_char(-1, pos[1] - 1, True)
            elif key == Qt.Key.Key_Right:
                if pos[0] + 1 < len(kbd_board[pos[1]]):
                    self.current_char = self.get_nearest_char(pos[0] + 1, pos[1])
                elif pos[1] + 1 < len(kbd_board):
                    self.current_char = self.get_nearest_char(0, pos[1] + 1)
            self.show_status(self.current_char)
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
                # print("On the padding area, ignoring.")
                self.prefix_key = True
            else:
                self.prefix_key = False
            return kbd_board[row][col]
        return None

    def mousePressEvent(self, event: QMouseEvent | None) -> None:  # type: ignore
        if event and event.button() == Qt.MouseButton.LeftButton:
            char = self.get_char_from_position(event.pos().x(), event.pos().y())
            if char:
                self.handle_key(char)
                self.current_char = char
        elif event and event.button() == Qt.MouseButton.RightButton:
            self.pop_group()
            char = self.get_char_from_position(event.pos().x(), event.pos().y())
            if char in self.mapping:
                self.show_status(self.mapping[char])
            self.update()

        self.setFocus()

        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:  # type: ignore
        if event:
            char = self.get_char_from_position(event.pos().x(), event.pos().y())
            if char and char != self.current_char:
                self.show_status(char)
                self.current_char = char
                self.update()
        return super().mouseMoveEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Use Fusion style instead of Kvantum to avoid plugin compatibility issues in venv
    app.setStyle("Fusion")
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyside2())
    window = KeyboardWidget()
    window.show()
    sys.exit(app.exec())
