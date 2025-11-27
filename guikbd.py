import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QLabel,
)
from PyQt5.QtGui import QKeyEvent, QMouseEvent, QPainter, QFont, QColor
from PyQt5.QtCore import Qt, QRect, QObject, QEvent

from boards import get_emojis_groups, Group, Emoji

kbd = """
1234567890ß´
qwertzuiopü+
asdfghjklöä#
<yxcvbnm,.-
""".strip()

kbd_board = kbd.splitlines()


def make_top_mapping(groups: list[Group]) -> dict[str, Group]:
    mapping: dict[str, Group] = {}
    i = 0
    for k in kbd:
        if k not in (" ", "\n"):
            if i < len(groups):
                mapping[k] = groups[i]
                i += 1
    return mapping


def make_group_mapping(group: Group) -> dict[str, Emoji]:
    mapping: dict[str, Emoji] = {}
    i = 0
    for k in kbd:
        if k not in (" ", "\n"):
            if i < len(group.emojis):
                mapping[k] = group.emojis[i]
                i += 1
    return mapping


inputStyle = """
                color: white;
                background-color: black;
                border: 1px solid white;
                border-radius: 5px; 
                padding: 6px;
        """

searchStyle = """
                color: white;
                background-color: black;
                border: 1px solid white;
                border-radius: 5px; 
        """

start_x = 10
start_y = 90
key_width = 40
key_height = 40
key_padding = 5


class KeyboardWidget(QWidget):
    """
    Das Haupt-Widget, das die Tastatur und Emojis zeichnet.
    In PyQt zeichnet man in der paintEvent-Methode mit QPainter.
    """

    def __init__(self):
        super().__init__()
        self.max_chars = sum(1 for char in kbd if not char.isspace())
        (self.emojis, self.groups) = get_emojis_groups(self.max_chars)
        self.mapping = make_top_mapping(self.groups)
        self.top_mapping = self.mapping

        board_cols = max(len(line.replace(" ", "")) for line in kbd.splitlines())
        board_rows = len(kbd.splitlines())

        self.setWindowTitle("Emoji Keyboard")
        width = start_x + board_cols * (key_width + key_padding) + key_padding
        height = start_y + board_rows * (key_width + key_padding) + key_padding + 38
        self.setGeometry(100, 100, width, height)
        self.setStyleSheet("background-color: black;")
        self.setMouseTracking(True)

        self.initUI()

        # self.setMinimumHeight(450)
        # self.setMaximumSize

    def initUI(self):
        main_vbox = QVBoxLayout()

        self.emoji_input_field = QLineEdit(self)
        self.emoji_input_field.setFont(QFont("Noto Color Emoji", 16))
        self.emoji_input_field.setStyleSheet(inputStyle)
        self.emoji_input_field.setAlignment(Qt.AlignTop | Qt.AlignLeft)  # type: ignore
        self.emoji_input_field.installEventFilter(self)

        self.search_field = QLineEdit(self)
        font = QFont()
        font.setPointSize(10)
        self.search_field.setFont(font)
        self.search_field.setPlaceholderText("Search emojis by name and tags...")
        self.search_field.textChanged.connect(self.filter_emojis_by_name)
        self.search_field.setStyleSheet(searchStyle)
        # self.search_field.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.search_field.setTextMargins(4, 8, 4, 0)

        self.status_label = QLabel("Status: Ready", self)
        self.status_label.setStyleSheet("color: white;")
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # type: ignore
        self.status_label.setFont(QFont("Arial", 9))
        self.status_label.setWordWrap(True)

        main_vbox.addWidget(self.emoji_input_field)
        main_vbox.addWidget(self.search_field)
        main_vbox.addStretch(1)
        main_vbox.addWidget(self.status_label)

        self.setLayout(main_vbox)

    def eventFilter(self, source: QObject, event: QEvent):  # type: ignore
        if (
            event
            and event.type() == event.KeyPress  # type: ignore
            and isinstance(event, QKeyEvent)
            and source is self.emoji_input_field
        ):
            key_text = event.text()

            if key_text in self.mapping or event.key() in (
                Qt.Key_Escape,  # type: ignore
                Qt.Key_Return,  # type: ignore
                Qt.Key_Enter,  # type: ignore
            ):
                self.handle_keyboard_action(event)
                return True

        return super().eventFilter(source, event)

    def paintEvent(self, _event):  # type: ignore
        painter = QPainter(self)

        current_x = start_x
        current_y = start_y

        self.key_font = QFont("Arial", 9)
        self.emoji_font = QFont("Noto Color Emoji", 22)

        for row in kbd_board:
            for char in row:
                if char != " ":
                    rect = QRect(current_x, current_y, key_width, key_height)
                    painter.setPen(QColor(128, 128, 128))  # gray outline
                    painter.drawRoundedRect(rect, 5, 5)

                    # 3. Emoji (Emoji Font) zeichnen
                    if char in self.mapping:
                        e = self.mapping[char]
                        emoji_char = (
                            e.emojis[0].char if isinstance(e, Group) else e.char
                        )
                        painter.setFont(self.emoji_font)
                        rect = QRect(
                            current_x + 2, current_y + 2, key_width, key_height
                        )
                        painter.drawText(rect, Qt.AlignCenter, emoji_char)  # type: ignore

                    if char != "ß" and char.isalpha():
                        char = char.upper()
                    painter.setFont(self.key_font)
                    rect = QRect(current_x + 2, current_y + 2, key_width, key_height)
                    painter.drawText(rect, Qt.AlignLeft | Qt.AlignTop, char)  # type: ignore

                current_x += key_width + key_padding

            # Nächste Zeile beginnen
            current_x = start_x
            current_y += key_height + key_padding

    def filter_emojis_by_name(self, search_term: str):
        search_term = search_term.lower()
        if not search_term:
            self.mapping = self.top_mapping
            self.update()
        else:
            # TODO implement filtering logic
            pass

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.emoji_input_field.text())

    def set_status(self, text: str):
        self.status_label.setText(text)

    def handle_keyboard_action(self, event: QKeyEvent):
        key_text = event.text()

        if key_text in self.mapping:
            e = self.mapping[key_text]

            if isinstance(e, Group):
                self.mapping = make_group_mapping(e)
                self.set_status(f"Group: {e.group_name} - {e.subgroup_name}")
                self.update()

            elif isinstance(e, Emoji):  # type: ignore
                self.emoji_input_field.insert(e.char)
                self.copy_to_clipboard()
                self.set_status(f"{e.unicode}, {e.annotation}, {e.tags}")

        elif event.key() == Qt.Key_Escape:  # type: ignore
            self.mapping = self.top_mapping
            self.update()

        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):  # type: ignore
            self.copy_to_clipboard()
            print(self.emoji_input_field.text())
            self.close()

    def getCharByPosition(self, x: int, y: int) -> str | None:
        row = (y - start_y) // (key_height + key_padding)
        col = (x - start_x) // (key_width + key_padding)
        if row >= 0 and col >= 0 and row < len(kbd_board) and col < len(kbd_board[row]):
            return kbd_board[row][col]
        return None

    def handleCharPress(self, char: str):
        if char in self.mapping:
            e = self.mapping[char]

            if isinstance(e, Group):
                self.mapping = make_group_mapping(e)
                self.update()

            elif isinstance(e, Emoji):  # type: ignore
                self.emoji_input_field.insert(e.char)
                self.copy_to_clipboard()

    def handleCharStatus(self, char: str):
        if char in self.mapping:
            e = self.mapping[char]
            if isinstance(e, Group):
                self.set_status(f"Group: {e.group_name} - {e.subgroup_name}")
                self.update()
            elif isinstance(e, Emoji):  # type: ignore
                self.set_status(f"{e.unicode}, {e.annotation}, {e.tags}")
            else:
                self.set_status(f"Error: Unknown type {type(e)}")

    def mousePressEvent(self, event: QMouseEvent | None) -> None:  # type: ignore
        if event and event.button() == Qt.LeftButton:  # type: ignore
            char = self.getCharByPosition(event.x(), event.y())
            if char:
                self.handleCharPress(char)
                self.handleCharStatus(char)
        elif event and event.button() == Qt.RightButton:  # type: ignore
            self.mapping = self.top_mapping
            self.update()

        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:  # type: ignore
        if event:
            char = self.getCharByPosition(event.x(), event.y())
            if char:
                self.handleCharStatus(char)
        return super().mouseMoveEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KeyboardWidget()
    window.show()
    sys.exit(app.exec_())
