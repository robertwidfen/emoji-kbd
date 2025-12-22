import sys
import time
import re
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
from PyQt6.QtCore import Qt, QRect, QRectF, QObject, QEvent

import logging as log

from emojis import get_emojis_groups, Emoji
from board import make_board


focus_color = QColor("#3399FF")  # default focus color

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
        self.setWindowIcon(QIcon("res/emoji-kbd.svg"))
        self.setWindowTitle("Emoji Kbd")
        self.setWindowFlag(Qt.WindowType.Tool, True)
        self.setWindowFlag(Qt.WindowType.Dialog, True)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)

        (self.all_emojis, self.emoji_groups) = get_emojis_groups()
        self.board = make_board("de_qwertz", self.all_emojis, self.emoji_groups)
        self.prefix_key = False

        self.last_scroll_time = 0

        self.initUI()
        log.info("Creating main window done.")

    def initUI(self):
        # collect some metrics from the style
        style = QApplication.style()
        if style:
            self.padding = style.pixelMetric(
                QStyle.PixelMetric.PM_LayoutHorizontalSpacing
            )
        else:
            self.padding = 5

        # Set up event handlers
        self.setMouseTracking(True)
        self.installEventFilter(self)
        QApplication.instance().focusChanged.connect(self.handle_focus_change)  # type: ignore

        # Set up fonts
        self.key_font = QFont("Arial")
        self.emoji_font = QFont("Noto Color Emoji")
        self.emoji_font.setFamilies(
            ["Noto Color Emoji", "Apple Color Emoji", "Segoe UI Emoji"]
        )
        self.emoji_font2 = QFont("Noto Color Emoji")
        self.emoji_font2.setFamilies(
            ["Noto Color Emoji", "Apple Color Emoji", "Segoe UI Emoji"]
        )
        self.mark_font = QFont("Noto Color Emoji")
        self.mark_font.setFamilies(
            ["Noto Color Emoji", "Apple Color Emoji", "Segoe UI Emoji"]
        )

        # Set up the main layout and elements
        main_vbox = QVBoxLayout()

        # Create horizontal layout for input and search fields
        top_hbox = QHBoxLayout()

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
        self.top_box = top_hbox

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

        self.setMinimumSize(300, 160)
        self.resize(600, 280)

    def paintEvent(self, _event):  # type: ignore
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # adapt window size
        tb = self.top_box
        eif = self.emoji_input_field
        sf = self.search_field
        sl = self.status_label
        start_x = tb.geometry().x()
        x = start_x
        padding = sf.pos().x() - eif.pos().x() - eif.width() + 1
        y = 2 * eif.pos().y() + tb.geometry().height()
        key_width = (
            sf.pos().x() + sf.width() - padding + 2
        ) / self.board.width - padding
        key_height = (
            self.height() - y - sl.height() - padding
        ) / self.board.height - padding
        size = int(min(key_width, key_height))
        emoji_size = int(size * 0.56)
        if emoji_size != self.emoji_font.pointSize():
            self.emoji_font.setPointSize(emoji_size)
            self.emoji_font2.setPointSize(int(size * 0.8))
            self.mark_font.setPointSize(int(size * 0.2))
            self.key_font.setPointSize(int(size * 0.2))

        self.start_x = start_x
        self.start_y = y
        self.key_width = key_width
        self.key_height = key_height

        for row in self.board.rows:
            for key in row:
                if key != " ":
                    # Draw key outline
                    rect = QRectF(
                        int(x) + 0.5, int(y) + 0.5, int(key_width), int(key_height)
                    )
                    pen = painter.pen()
                    pen.setWidth(1)
                    if self.board.current_key == key:
                        if self.hasFocus():
                            pen.setColor(focus_color)
                        else:
                            pen.setColor(self.palette().highlight().color())
                    else:
                        pen.setColor(QColor(128, 128, 128))  # gray outline
                    painter.setPen(pen)
                    painter.drawRoundedRect(rect, 3, 3)

                    # Draw key content
                    painter.setPen(self.palette().text().color())

                    e = self.board.get_emoji_for_key(key)
                    if e:
                        # Draw emoji
                        char = e.char
                        if e.unicode in special_name_map:
                            painter.setFont(self.key_font)
                            char = special_name_map[e.unicode]
                        elif self.board.current_key == key:
                            painter.setFont(self.emoji_font2)
                            rect = QRectF(
                                x - 10 + 1,
                                y - 10 + 1,
                                key_width + 20,
                                key_height + 20,
                            )
                        else:
                            painter.setFont(self.emoji_font)
                            rect = QRectF(
                                x - 10 + 1,
                                y - 10 + 1.5,
                                key_width + 20,
                                key_height + 20,
                            )
                        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, char)  # type: ignore

                        # Draw mark if any
                        if e.mark:
                            if not e.mark.isalnum():  # special mark
                                painter.setFont(self.mark_font)
                                rect = QRectF(x, y + 4, key_width - 2, key_height)
                            else:
                                painter.setFont(self.key_font)
                                rect = QRectF(x, y + 2, key_width - 2, key_height)
                            painter.drawText(
                                rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop, e.mark  # type: ignore
                            )

                    # Draw key label
                    painter.setFont(self.key_font)
                    rect = QRectF(x + 2, y + 2, key_width, key_height)
                    painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, key)  # type: ignore

                x += key_width + padding

            x = start_x
            y += key_height + padding

    def search_emojis(self, needle: str):
        self.board.search(needle)
        self.update()

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.emoji_input_field.text())

    def show_status(self, obj: str | Emoji | None):
        msgs: list[str] = []
        page_of_pages = self.board.page_of_pages
        if page_of_pages[1] > 1:
            msgs.append("Page {}/{}".format(*page_of_pages))
        if isinstance(obj, str):
            msgs.append(obj)
        if isinstance(obj, str) and self.board.has_key(obj):
            obj = self.board.get_emoji_for_key(obj)
        if isinstance(obj, Emoji):
            if obj.emojis:
                msgs.append(f"{len(obj.emojis)} emojis")
            msgs.append(f"{obj.char}")
            if obj.unicode:
                msgs.append(obj.unicode)
            if obj.name:
                msgs.append(obj.name)
            if obj.group:
                if obj.subgroup:
                    msgs.append(f"{obj.group} > {obj.subgroup}")
                else:
                    msgs.append(obj.group)
            if obj.tags:
                msgs.append(obj.tags)
        self.status_label.setText("; ".join(msgs))

    def handle_focus_change(self, old, new):  # type: ignore
        if new == self.emoji_input_field:
            if self.board.is_search:
                self.board.pop_board()
            self.show_status(
                "Type key to insert emoji or open sub board. Use Space as prefix key to open variants board. "
                "Use Enter to close board and insert into app."
            )
        elif new == self.search_field:
            self.search_field.selectAll()
            self.board.search(self.search_field.text())
            self.show_status(
                "Search emojis by name and tag, with '#' prefix by tag and '+' prefix by code. "
                "Use ',' to search group and/or subgroup, e.g. 'animal,', ',mammal' or 'ani,mam'."
            )
        elif new == self:
            if self.board.path_len == 1:
                self.show_status(
                    "Cursor movement to select emoji/group, Enter inserts emoji or opens group. "
                    "PageUp/PageDown to scroll board, Esc/Backspace to go back to previous board."
                )
            elif self.board.is_recent:
                self.show_status(
                    "Use Shift-Left/Right to reorder recent emojis. Delete to remove. "
                    "Shift+Enter to toggle favorite (star) status."
                )
            else:
                self.show_status(self.board.current_key)

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

    def insert_emoji(self, emoji: Emoji):
        self.emoji_input_field.insert(emoji.char)
        self.board.recent_add()
        self.copy_to_clipboard()
        self.show_status(f"{emoji.unicode}, {emoji.name}, {emoji.tags}")

    def handle_key(self, key: str):
        e = self.board.get_emoji_for_key(key)
        if not e:
            return
        self.board.set_cursor_to_key(key)
        if not self.prefix_key and e.unicode:
            self.insert_emoji(e)
        elif e.emojis:
            self.board.push_board(e.emojis)
        self.show_status(key)
        self.update()

    def handle_close(self):
        self.copy_to_clipboard()
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
            else:
                self.handle_key(key_text)
                self.prefix_key = False

        elif key == Qt.Key.Key_Tab:
            if source in (self.emoji_input_field, self.search_field):
                self.setFocus()
            elif self.board.is_search:
                self.search_field.setFocus()
            else:
                self.emoji_input_field.setFocus()
            self.update()

        elif (
            key == Qt.Key.Key_F
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            self.search_field.setFocus()
            self.update()

        elif key in (
            Qt.Key.Key_Left,
            Qt.Key.Key_Right,
            Qt.Key.Key_Up,
            Qt.Key.Key_Down,
            Qt.Key.Key_Home,
            Qt.Key.Key_End,
        ):
            return self.handle_cursor_navigation(source, event, key)

        elif key == Qt.Key.Key_Escape or (
            key == Qt.Key.Key_Backspace and source == self
        ):
            self.board.pop_board()
            self.show_status(self.board.current_key)
            if source is self.search_field:
                self.emoji_input_field.setFocus()
            self.update()

        elif key == Qt.Key.Key_Delete and source == self:
            if self.board.recent_delete():
                self.show_status("Deleted from recent.")
                self.update()

        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if source is self.emoji_input_field:
                self.handle_close()
            elif source is self.search_field:
                e = self.board.get_emoji()
                if e:
                    self.insert_emoji(e)
                self.emoji_input_field.setFocus()
                self.update()
            elif source is self:
                isShift = event.modifiers() == Qt.KeyboardModifier.ShiftModifier
                if isShift and self.board.is_recent:
                    self.board.recent_toggle_favorite()
                    self.update()
                else:
                    self.handle_key(self.board.current_key)
                    if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                        self.handle_close()

        elif key == Qt.Key.Key_PageUp:
            self.scroll_board(-1)

        elif key == Qt.Key.Key_PageDown:
            self.scroll_board(1)

        else:
            return False

        return True

    def scroll_board(self, direction: int):
        self.board.scroll(direction)
        self.update()
        self.show_status(self.board.get_emoji())

    def wheelEvent(self, event: QWheelEvent | None) -> None:  # type: ignore
        if event:
            current_time = time.time()
            delta = event.angleDelta().y()
            log.debug(f"Wheel event delta: {delta}")
            # Only allow scrolling only if delta is big enough and every this seconds
            # TODO Config
            if abs(delta) > 5 and current_time - self.last_scroll_time > 0.1:
                self.scroll_board(-1 if delta > 0 else 1)
                self.last_scroll_time = current_time
        return super().wheelEvent(event)

    def handle_cursor_navigation(self, source: QObject, event: QKeyEvent, key: int):
        isSelf = source is self
        isInput = source is self.emoji_input_field
        isSearch = source is self.search_field
        isRecent = self.board.is_recent
        isLeft = key == Qt.Key.Key_Left
        isRight = key == Qt.Key.Key_Right
        isUp = key == Qt.Key.Key_Up
        isDown = key == Qt.Key.Key_Down
        isHome = key == Qt.Key.Key_Home
        isEnd = key == Qt.Key.Key_End
        isShift = event.modifiers() == Qt.KeyboardModifier.ShiftModifier
        search_field = self.search_field
        search_field_pos = search_field.cursorPosition()
        search_field_at_end = len(search_field.text()) == search_field_pos
        emoji_input_field = self.emoji_input_field

        if not isSelf and isDown:
            self.setFocus()
            self.update()
            return True
        elif isInput and isRight:
            s = emoji_input_field.text()
            if emoji_input_field.cursorPosition() == len(s.encode("utf-16-le")) // 2:
                search_field.setFocus()
            return True
        elif isSearch and isLeft and search_field_pos == 0:
            emoji_input_field.setFocus()
            return True
        elif isSearch and isLeft and isShift:
            self.board.move_cursor(-1, 0)
            self.update()
            return True
        elif isSearch and isRight and (search_field_at_end | isShift):
            self.board.move_cursor(1, 0)
            self.update()
            return True
        elif isRecent and isLeft and isShift:
            self.board.move_recent_emoji(-1)
            self.update()
            return True
        elif isRecent and isRight and isShift:
            self.board.move_recent_emoji(1)
            self.update()
            return True
        elif isSelf:
            if isHome:
                self.board.move_cursor(-100, 0)
            elif isEnd:
                self.board.move_cursor(100, 0)
            elif isUp:
                if self.board.cursor_y == 0:
                    self.emoji_input_field.setFocus()
                else:
                    self.board.move_cursor(0, -1)
            elif isDown:
                self.board.move_cursor(0, 1)
            elif isLeft:
                self.board.move_cursor(-1, 0)
            elif isRight:
                self.board.move_cursor(1, 0)
            self.show_status(self.board.current_key)
            self.update()
            return True
        return False

    def get_char_from_position(self, x: int, y: int) -> str | None:
        (start_x, start_y) = (self.start_x, self.start_y)
        (key_width, key_height) = (self.key_width, self.key_height)
        key_padding = self.padding
        col = int((x - start_x) // (key_width + key_padding))
        row = int((y - start_y) // (key_height + key_padding))
        if row >= 0 and col >= 0 and row < self.board.height and col < self.board.width:
            xp = start_x + col * (key_width + key_padding) + key_width - 2 * key_padding
            yp = start_y + row * (key_height + key_padding) + 2 * key_padding
            # print(f"Mouse at row {row}, col {col} {x},{y} vs {xp},{yp}")
            if x >= xp and y <= yp:
                self.prefix_key = True
            else:
                self.prefix_key = False
            try:
                return self.board.get_key_at_pos(col, row)
            except IndexError:
                pass
        return None

    def mousePressEvent(self, event: QMouseEvent | None) -> None:  # type: ignore
        if not event:
            return super().mousePressEvent(event)
        if self.status_label.underMouse():
            if event.pos().x() < self.width() / 2:
                self.windowHandle().startSystemMove()  # type: ignore
            else:
                self.windowHandle().startSystemResize(  # type: ignore
                    Qt.Edge.BottomEdge | Qt.Edge.RightEdge
                )
        elif event.type() == QEvent.Type.MouseButtonDblClick:
            self.handle_close()
        elif self.underMouse() and event.type() == QEvent.Type.MouseButtonPress:
            button = event.button()
            self.setFocus()
            (x, y) = (event.pos().x(), event.pos().y())
            if button == Qt.MouseButton.LeftButton:
                char = self.get_char_from_position(x, y)
                if char:
                    self.handle_key(char)
            elif button == Qt.MouseButton.RightButton:
                self.board.pop_board()
                char = self.get_char_from_position(x, y)
                self.show_status(char)
                self.update()

        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:  # type: ignore
        if event:
            char = self.get_char_from_position(event.pos().x(), event.pos().y())
            if char and char != self.board.current_key:
                self.show_status(char)
                self.update()

            # Change cursor based on position over status label
            if self.status_label.underMouse():
                label_rect = self.status_label.geometry()
                mouse_x = event.pos().x()
                label_center = label_rect.left() + label_rect.width() // 2

                if mouse_x < label_center:
                    # Left half: move cursor
                    self.setCursor(Qt.CursorShape.SizeAllCursor)
                else:
                    # Right half: resize cursor
                    self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            else:
                # Not over status label: normal cursor
                self.setCursor(Qt.CursorShape.ArrowCursor)

        return super().mouseMoveEvent(event)


def setup_app() -> QApplication:
    app = QApplication(sys.argv)
    app.setApplicationName("emoji-kbd")
    app.setDesktopFileName("emoji-kbd")
    app.setWindowIcon(QIcon("res/emoji-kbd.svg"))
    stylesheet = qdarkstyle.load_stylesheet_pyqt6()
    app.setStyleSheet(stylesheet)
    try:
        matches = re.findall(
            r"QLineEdit[^}]*:focus[^}]*border[^;]*#[0-9A-Fa-f]{6}", stylesheet
        )
        if matches:
            m = "\n".join(set(matches))
            c = m.split("border: ")[1].split(" ")[2].strip()
            global focus_color
            focus_color = QColor(c)
            log.info(f"Found focus color {c} in {m}")
        else:
            log.info("No focus border found")
    except Exception as e:
        log.error(f"Error finding focus border color: {e}")
    return app


if __name__ == "__main__":
    log.basicConfig(
        # filename='.local/guikbd.log',
        # filemode='a',
        level=log.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    log.info(f"Starting Qt6 Emoji Keyboard on {sys.platform}...")
    app = setup_app()
    app.setQuitOnLastWindowClosed(True)
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
