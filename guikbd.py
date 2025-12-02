import sys
import qdarktheme  # type: ignore
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QLabel,
)
from PyQt5.QtGui import QKeyEvent, QMouseEvent, QPainter, QFont, QColor, QWheelEvent
from PyQt5.QtCore import Qt, QRect, QObject, QEvent

from boards import get_emojis_groups, Group, Emoji

# TODO add more layouts
# TODO add config
# TODO add recent emojis
# TODO add skin tone support
# TODO add "scrollbar"

kbd = """
1234567890ß´
qwertzuiopü+
asdfghjklöä#
<yxcvbnm,.-
""".strip()

kbd_board = kbd.splitlines()


def make_mapping(
    objs: list[Group] | list[Emoji], offset: int = 0
) -> dict[str, Group | Emoji]:
    mapping: dict[str, Group | Emoji] = {}
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
        self.mapping: dict[str, Group | Emoji] = make_mapping(self.groups)
        self.offset = 0
        self.top_groups = self.groups
        self.top_mapping = self.mapping
        self.search_results = Group("Search Results", "Matches")
        self.in_search = False
        self.current_char = ""

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
        self.emoji_input_field.setAlignment(Qt.AlignTop | Qt.AlignLeft)  # type: ignore
        self.emoji_input_field.installEventFilter(self)

        self.search_field = QLineEdit(self)
        self.search_field.textChanged.connect(self.filter_emojis)
        # self.search_field.setTextMargins(4, 14, 4, 0)
        self.search_field.setPlaceholderText("Search emojis by name or tags...")
        self.search_field.installEventFilter(self)

        self.status_label = QLabel("Status: Ready", self)
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # type: ignore
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

        self.key_font = QFont("Arial", 9)
        self.emoji_font = QFont("Noto Color Emoji", 22)

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
                        rect = QRect(x + 2, y + 2, key_width, key_height)
                        painter.drawText(rect, Qt.AlignCenter, e.char)  # type: ignore

                    if char != "ß" and char.isalpha():
                        char = char.upper()
                    painter.setFont(self.key_font)
                    rect = QRect(x + 2, y + 2, key_width, key_height)
                    painter.drawText(rect, Qt.AlignLeft | Qt.AlignTop, char)  # type: ignore

                x += key_width + key_padding

            x = start_x
            y += key_height + key_padding

    def restore_top_mapping(self):
        self.groups = self.top_groups
        self.offset = 0
        self.mapping = make_mapping(self.top_groups, offset=self.offset)

    def filter_emojis(self, search_term: str):
        search_term = search_term.lower()
        if not search_term:
            self.groups = self.emojis
            self.mapping = make_mapping(self.groups)
        else:
            matches: list[Emoji] = []
            for e in self.emojis:
                if search_term in e.name.lower() or search_term in e.tags.lower():
                    matches.append(e)
                # TODO search in group and subgroup too when ","" is used?
                # TODO search for each term when multiple terms are given?
                # TODO fuzzy search?
                # TODO rank by relevance?
            if matches:
                self.search_results.emojis.clear()
                for e in matches:
                    self.search_results.append(e)
                self.mapping = make_mapping(self.search_results.emojis)
                self.set_status(f"Found {len(matches)} matching emojis.")
            else:
                self.mapping = {}
                self.set_status("No matching emojis found.")
        self.update()

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.emoji_input_field.text())

    def set_status(self, obj: str | Group | Emoji):
        if isinstance(obj, Group):
            obj = f"Group: {obj.group_name}\nSubgroup: {obj.subgroup_name}"
        elif isinstance(obj, Emoji):
            obj = f"{obj.unicode}, {obj.name}, {obj.group} > {obj.subgroup} \nTags: {obj.tags}"
        self.status_label.setText(obj)

    def handle_focus_change(self, old, new):  # type: ignore
        if new == self.emoji_input_field:
            self.restore_top_mapping()
            self.in_search = False
            self.current_char = ""
            self.set_status("Type to select category or insert emojis.")
        elif new == self.search_field:
            if self.search_field.text() != "":
                if self.groups != self.search_results.emojis:
                    self.groups = self.search_results.emojis
                    self.offset = 0
                    self.mapping = make_mapping(self.groups)
            elif self.groups != self.emojis:
                self.groups = self.emojis
                self.offset = 0
                self.mapping = make_mapping(self.groups)

            self.in_search = True
            self.current_char = ""
            self.set_status("Type to filter emojis by category, name and tags.")
        elif new == self:
            self.set_status(
                "Select an emoji by cursor movement, insert/open by Enter, go back by Backspace."
            )
        self.update()

    def eventFilter(self, source: QObject, event: QEvent):  # type: ignore
        if (
            event
            and event.type() == event.KeyPress  # type: ignore
            and isinstance(event, QKeyEvent)
        ):
            if self.handle_keyboard_press(source, event):
                return True

        return super().eventFilter(source, event)

    def insert_emoji(self, emoji: Emoji):
        self.emoji_input_field.insert(emoji.char)
        self.copy_to_clipboard()
        self.set_status(f"{emoji.unicode}, {emoji.name}, {emoji.tags}")

    def handle_key(self, key: str):
        if key not in self.mapping:
            return
        self.current_char = key
        e = self.mapping[key]

        if isinstance(e, Group):
            self.mapping = make_mapping(e.emojis)
            self.groups = e.emojis
            self.update()
        elif isinstance(e, Emoji):  # type: ignore
            self.insert_emoji(e)

        self.set_status(e)

    def handle_keyboard_press(self, source: QObject, event: QKeyEvent):
        key = event.key()
        key_text = event.text()

        if (
            source is self.emoji_input_field or source is self
        ) and key_text in self.mapping:
            self.handle_key(key_text)

        elif key == Qt.Key_Tab:  # type: ignore
            if source is self.emoji_input_field:
                self.search_field.setFocus()
            elif source is self.search_field:
                self.setFocus()
            else:
                self.emoji_input_field.setFocus()
            self.update()

        elif key in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down, Qt.Key_Home, Qt.Key_End):  # type: ignore
            return self.handle_cursor_navigation(source, key)

        elif key == Qt.Key_Escape or (key == Qt.Key_Backspace and source == self):  # type: ignore
            self.restore_top_mapping()
            self.in_search = False
            if source is self.search_field:
                self.emoji_input_field.setFocus()
            self.update()

        elif key in (Qt.Key_Return, Qt.Key_Enter):  # type: ignore
            if source is self.emoji_input_field:
                self.copy_to_clipboard()
                print(self.emoji_input_field.text())
                self.close()
            if source is self and self.current_char:
                self.handle_key(self.current_char)

        elif key == Qt.Key_PageUp:  # type: ignore
            self.scroll_board(1)

        elif key == Qt.Key_PageDown:  # type: ignore
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

    def wheelEvent(self, event: QWheelEvent | None) -> None:  # type: ignore
        if event:
            self.scroll_board(event.angleDelta().y())
        return super().wheelEvent(event)

    def get_nearest_char(self, row: str, col: int, left_only: bool = False) -> str:
        if col < 0:
            col = 0
        elif col >= len(row):
            col = len(row) - 1
        if row[col] != " ":
            return row[col]
        for i in range(len(row)):
            if not left_only and col + i < len(row) and row[col + i] != " ":
                return row[col + i]
            if col - i >= 0 and row[col - i] != " ":
                return row[col - i]
        return ""

    def handle_cursor_navigation(self, source: QObject, key: int):
        (left, right, up, down, home, end) = (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down, Qt.Key_Home, Qt.Key_End)  # type: ignore
        if key == down and source is self.emoji_input_field:
            self.current_char = self.get_nearest_char(kbd_board[0], 0)
            self.setFocus()
            self.update()
            return True
        elif key == up and source is self.search_field:
            self.current_char = self.get_nearest_char(kbd_board[0], 0)
            if self.current_char in self.mapping:
                self.setFocus()
            else:
                self.emoji_input_field.setFocus()
                self.current_char = ""
            self.update()
            return True
        elif source is self:
            if key == home and self.current_char:
                for i, row in enumerate(kbd_board):
                    col = row.find(self.current_char)
                    if col > -1:
                        self.current_char = self.get_nearest_char(kbd_board[i], 0)
                        break
            elif key == end and self.current_char:
                for i, row in enumerate(kbd_board):
                    col = row.find(self.current_char)
                    if col > -1:
                        self.current_char = self.get_nearest_char(
                            kbd_board[i], len(kbd_board[i])
                        )
                        break
            elif key == up and self.current_char:
                for i, row in enumerate(kbd_board):
                    col = row.find(self.current_char)
                    if col > -1 and i == 0:
                        self.emoji_input_field.setFocus()
                        self.current_char = ""
                        break
                    if col > -1 and i > 0:
                        self.current_char = self.get_nearest_char(kbd_board[i - 1], col)
                        break
            elif key == down and self.current_char:
                for i, row in enumerate(kbd_board):
                    col = row.find(self.current_char)
                    if col > -1 and i + 1 < len(kbd_board):
                        self.current_char = self.get_nearest_char(kbd_board[i + 1], col)
                        if self.current_char in self.mapping:
                            break
                else:
                    self.current_char = ""
                    self.search_field.setFocus()
            elif key == left and self.current_char:
                for i, row in enumerate(kbd_board):
                    col = row.find(self.current_char)
                    if col > 0:
                        self.current_char = self.get_nearest_char(row, col - 1, True)
                        break
            elif key == right and self.current_char:
                for i, row in enumerate(kbd_board):
                    col = row.find(self.current_char)
                    if col > -1 and col + 1 < len(row):
                        self.current_char = self.get_nearest_char(row, col + 1)
                        break
            self.show_char_props_in_status(self.current_char)
            self.update()
            return True
        return False

    def get_char_from_position(self, x: int, y: int) -> str | None:
        row = (y - start_y) // (key_height + key_padding)
        col = (x - start_x) // (key_width + key_padding)
        if row >= 0 and col >= 0 and row < len(kbd_board) and col < len(kbd_board[row]):
            return kbd_board[row][col]
        return None

    def handle_char_press(self, char: str):
        if char in self.mapping:
            e = self.mapping[char]

            if isinstance(e, Group):
                self.mapping = make_mapping(e.emojis)
                self.groups = e.emojis
                self.update()

            elif isinstance(e, Emoji):  # type: ignore
                self.emoji_input_field.insert(e.char)
                self.copy_to_clipboard()

        self.show_char_props_in_status(char)

    def show_char_props_in_status(self, char: str):
        if char in self.mapping:
            e = self.mapping[char]
            self.set_status(e)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:  # type: ignore
        if event and event.button() == Qt.LeftButton:  # type: ignore
            char = self.get_char_from_position(event.x(), event.y())
            if char:
                self.handle_char_press(char)
                self.current_char = char
        elif event and event.button() == Qt.RightButton:  # type: ignore
            self.restore_top_mapping()
            self.update()

        self.setFocus()

        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:  # type: ignore
        if event:
            char = self.get_char_from_position(event.x(), event.y())
            if char and char != self.current_char:
                self.show_char_props_in_status(char)
                self.current_char = char
                self.update()
        return super().mouseMoveEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    qdarktheme.setup_theme()  # type: ignore
    window = KeyboardWidget()
    window.show()
    sys.exit(app.exec_())
