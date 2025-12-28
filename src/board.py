import logging as log
from typing import Callable, Literal

from config import Config
from emojis import Emoji
from tools import get_state_file


class RecentGroup(Emoji):

    def __init__(self, recent_file: str):
        super().__init__(group="Recent List", char="⟲")
        self.recent_file = recent_file
        self.load()
        self.offset = 0

    def add(self, emoji: Emoji, no_sort: bool):
        if emoji.char not in [e.char for e in self.emojis]:
            emoji = emoji.clone()
            self.emojis.append(emoji)
        emoji = next(e for e in self.emojis if e.char == emoji.char)
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
        for e in self.emojis:
            if e != emoji and e.order < 100:
                if e.order > 0:
                    e.order -= 1
                if e.order > 0:
                    e.mark = str(e.order)
                else:
                    e.mark = ""
                    e.order = 0
        # sort and keep only top 100
        if not no_sort:
            self.emojis.sort(key=lambda e: e.order, reverse=True)
        # limit to 100 entries
        if len(self.emojis) > 100:
            del self.emojis[100:]
        self.save()

    def toggle_favorite(self, emoji: Emoji):
        if emoji:
            if emoji.order >= 100:
                emoji.order = 0
                emoji.mark = ""
            else:
                emoji.order = 100
                emoji.mark = "⭐️"
            self.save()

    def delete(self, emoji: Emoji):
        self.emojis.remove(emoji)
        self.save()

    def load(self):
        try:
            with open(self.recent_file, "r", encoding="utf-8") as f:
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
                self.emojis = recent_list
        except Exception as ex:
            log.error(f"Restoring recent emojis: {ex}")

    def save(self):
        try:
            with open(self.recent_file, "w", encoding="utf-8") as f:
                for e in self.emojis:
                    f.write(
                        f"{e.order};{e.char};{e.unicode};{e.name};{e.group};{e.subgroup};{e.tags}\n"
                    )
        except Exception as ex:
            log.error(f"Saving recent emojis: {ex}")


class SearchGroup(Emoji):
    def __init__(self):
        super().__init__(group="Search Results", char="🔎")
        self.offset = 0

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

    def search(self, emojis: list[Emoji], needle: str) -> int:
        self.emojis.clear()
        self.offset = 0
        if not needle:
            self.emojis.extend(emojis)
            return 0
        needle = needle.lower()
        # list of matches with (score: int, emoji: Emoji)
        matches: list[Emoji] = emojis
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
                name_matches = self.filter_emojis(matches, n, lambda e: e.name, 1)
                tag_matches = self.filter_emojis(matches, n, lambda e: e.tags, 1)
                matches = list(set(name_matches + tag_matches))
        if matches:
            # for e in matches:  # show match score for debugging
            #     e.mark = str(e.order)
            matches.sort(key=lambda e: e.order, reverse=True)
            # Remove duplicates while preserving order
            matches_dict = {e.char: e for e in reversed(matches)}
            matches = list(reversed(matches_dict.values()))
            self.emojis.extend(matches)
        else:
            if needle.startswith("+"):
                code = needle[1:].upper()
                char = chr(int(code, 16))
                e = Emoji(char=char, unicode=code, name="Generated Character")
                self.emojis.append(e)

        return len(self.emojis)


class SettingsGroup(Emoji):
    def __init__(self, config: Config, board: "Board"):
        super().__init__(group="Settings", char="⚙️")
        self.config = config
        self.board = board
        self.offset = 0
        for layout in config.layout:
            e = Emoji(
                char=layout.char,
                group="layout",
                name=layout.name,
            )
            if layout.name == config.board.layout:
                e.mark = "🟡"
            self.emojis.append(e)

    def act(self, emoji: Emoji):
        log.info(f"Called SettingsEmoji.act({emoji.char}).")
        if emoji.group == "layout":
            log.info(f"Changing layout to {emoji.name}")
            key_pos = self.board.get_key_pos()
            self.board.set_layout(self.config.get_layout(emoji.name))
            self.board._make_mapping()
            self.board.move_cursor(-100, -100)
            self.board.move_cursor(key_pos, 0)
            for e in self.emojis:
                if e.group == "layout":
                    if e.name == emoji.name:
                        e.mark = "🟡"
                    else:
                        e.mark = ""


type BoardEmoji = Emoji | RecentGroup | SearchGroup | SettingsGroup
type OffsetBoardEmoji = tuple[int, str, list[BoardEmoji]]


class Board:

    def __init__(
        self, config: Config, all_emojis: list[Emoji], emoji_groups: list[Emoji]
    ):
        self._cursor_x: int = 0
        self._cursor_y: int = 0
        self._current_key: str = ""
        self.set_layout(config.get_layout())
        self.move_cursor(-100, -100)

        self._all_emojis: list[Emoji] = all_emojis
        self._main_emojis: list[BoardEmoji] = emoji_groups
        self._recent = RecentGroup(get_state_file("recent.txt"))
        self._main_emojis.insert(0, self._recent)
        self._search_group = SearchGroup()
        self._main_emojis.insert(1, self._search_group)
        self._settings_group = SettingsGroup(config, self)
        self._main_emojis.insert(2, self._settings_group)

        self._emojis: list[BoardEmoji] = self._main_emojis
        self._offset: int = 0
        self._mapping: dict[str, Emoji] = {}
        self._make_mapping()
        self._board_path: list[OffsetBoardEmoji] = []

        if config.board.default:
            for e in self.emojis:
                if e.char == config.board.default:
                    self.push_board(e.emojis)
                    break

    def set_layout(self, layout: str):
        self._layout = layout
        self._rows = self._layout.splitlines()
        self._key_count = sum(1 for char in self._layout if not char.isspace())
        self._height = len(self._rows)
        self._width = max(len(row) for row in self._rows)

    def get_key_pos(self, key: str | None = None) -> int:
        if key is None:
            key = self.current_key
        key = self.has_key(key)
        pos = self._layout.replace(" ", "").replace("\n", "").find(key)
        if pos >= 0:
            return pos
        raise ValueError(f"Key '{key}' not found on board.")

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def cursor_x(self) -> int:
        return self._cursor_x

    @property
    def cursor_y(self) -> int:
        return self._cursor_y

    @property
    def rows(self) -> list[str]:
        return self._rows

    @property
    def current_key(self) -> str:
        return self._current_key

    @property
    def offset(self) -> int:
        return self._offset

    @property
    def emojis(self) -> list[BoardEmoji]:
        return self._emojis

    @property
    def emoji_count(self) -> int:
        return len(self._emojis)

    @property
    def path_len(self) -> int:
        return len(self._board_path)

    @property
    def is_search(self) -> bool:
        return self._emojis == self._search_group.emojis

    @property
    def is_recent(self) -> bool:
        return self._emojis == self._recent.emojis

    @property
    def is_settings(self) -> bool:
        return self._emojis == self._settings_group.emojis

    @property
    def page_of_pages(self) -> tuple[int, int]:
        if self.emoji_count <= self._key_count:
            return (1, 1)
        pages = (self.emoji_count - 1) // self._key_count + 1
        page = self._offset // self._key_count + 1
        return (page, pages)

    def push_key(self, key: str):
        key = self.has_key(key)
        emoji = self._mapping[key]
        if self.is_settings and emoji:
            self._settings_group.act(emoji)
            return None
        self.push_board(emoji.emojis)

    def push_board(self, emojis: list[Emoji]):
        self._board_path.append((self._offset, self._current_key, self._emojis))
        self._emojis = emojis
        self._offset = 0
        self.move_cursor(-100, -100)
        self._mapping = self._make_mapping()

    def pop_board(self):
        if len(self._board_path) > 0:
            self._offset, self._current_key, self._emojis = self._board_path.pop()
            self.set_cursor_to_key(self._current_key)
            self._mapping = self._make_mapping()

    def _make_mapping(self):
        self._mapping.clear()
        i = self._offset
        for k in self._layout:
            if k not in (" ", "\n"):
                if i < len(self._emojis):
                    self._mapping[k] = self._emojis[i]
                    i += 1
        return self._mapping

    def recent_add(self):
        e = self.get_emoji()
        if e:
            self._recent.add(e, self.is_recent)
            self._mapping = self._make_mapping()

    def recent_delete(self):
        e = self.get_emoji()
        if e:
            self._recent.delete(e)
            self._mapping = self._make_mapping()
            return True
        return False

    def recent_toggle_favorite(self):
        e = self.get_emoji()
        if e:
            self._recent.toggle_favorite(e)
            self._mapping = self._make_mapping()

    def search(self, needle: str) -> int:
        if self._emojis != self._search_group.emojis:
            self.push_board(self._search_group.emojis)
        self.move_cursor(-100, -100)
        self._offset = 0
        self._search_group.search(self._all_emojis, needle)
        self._mapping = self._make_mapping()
        return len(self._search_group.emojis)

    def has_key(self, key: str) -> str:
        """Return the given key if mapped to an emoji.
        Return uppercase key if that is mapped.
        Return empty string if not found."""
        if key in self._mapping:
            return key
        if key.upper() in self._mapping:
            return key.upper()
        log.warning(f"Key '{key}' not found on board.")
        return ""

    def get_emoji(self) -> Emoji | None:
        """Return the emoji at the current cursor position or None."""
        return self._mapping.get(self._current_key, None)

    def get_emoji_for_key(self, key: str) -> Emoji | None:
        """Return the emoji for the given key or None."""
        key = self.has_key(key)
        return self._mapping.get(key, None)

    def set_cursor_to_key(self, key: str) -> tuple[int, int]:
        """Return the (x, y) position of the given key on the board.
        If key not found, move cursor to first key."""
        key = self.has_key(key)
        if key:
            for y, row in enumerate(self._rows):
                x = row.find(key)
                if x >= 0:
                    self._current_key = key
                    (self._cursor_x, self._cursor_y) = (x, y)
                    return (x, y)
        log.error(f"Key '{key}' not found on board.")
        return self.move_cursor(-100, -100)

    def get_key_at_pos(self, x: int, y: int) -> str:
        if 0 <= y < self._height:
            row = self._rows[y]
        else:
            raise IndexError(
                f"Position y:{y} out of board {self._width}x{self._height}"
            )
        if 0 <= x < len(row):
            return row[x]
        else:
            raise IndexError(
                f"Position x:{x} out of board {self._width}x{self._height}"
            )

    def move_cursor(
        self, dx: int, dy: int, cx: int | None = None, cy: int | None = None
    ) -> tuple[int, int]:
        """Move the cursor by (dx, dy) and return the new (x, y) position.
        100/-100 jumps to end/start of row/column.
        Left/right moves at line start/end go to previous/next line."""
        if cx is None:
            cx = self._cursor_x
        if cy is None:
            cy = self._cursor_y
        x = cx + dx
        y = cy + dy

        if dy <= -100:
            y = 0
        elif dy >= 100:
            y = self._height - 1
        elif y < 0:
            y = 0
        elif y > self._height - 1:
            y = self._height - 1

        if dx <= -100:
            x = 0
            dx = 1
        elif dx >= 100:
            x = len(self._rows[y]) - 1
            dx = -1
        elif x < 0:
            if y > 0:
                y -= 1
                x = len(self._rows[y]) - 1
                dx = -1
            else:
                x = 0
                dx = 1
        elif x > len(self._rows[y]) - 1:
            if y < self._height - 1:
                y += 1
                x = 0
                dx = 1
            else:
                x = len(self._rows[y]) - 1
                dx = -1

        key = self._rows[y][x]

        # find next valid key in row
        if key == " ":
            if dy and 0 < y < self._height - 1:
                return self.move_cursor(dx, dy, x, y)
            if (dy or dx < 0) and x > 0:
                return self.move_cursor(-1, 0, x, y)
            if (dy or dx > 0) and x < len(self._rows[y]):
                return self.move_cursor(1, 0, x, y)
            return (self._cursor_x, self._cursor_y)

        self._cursor_x = x
        self._cursor_y = y
        self._current_key = key
        return (x, y)

    def scroll(self, offset: int):
        new_offset = self._offset + self._key_count * offset
        if new_offset < 0:
            new_offset = 0
        if new_offset >= len(self._emojis):
            new_offset = self._offset
        self._offset = new_offset
        self._mapping = self._make_mapping()

    def move_recent_emoji(self, direction: Literal[-1, 1]):
        e = self.get_emoji()
        if not e:
            return
        i = self._recent.emojis.index(e)
        if (direction == -1 and i == 0) or (
            direction == 1 and i + 1 == len(self._recent.emojis)
        ):
            return
        r = self._recent.emojis
        r[i], r[i + direction] = r[i + direction], r[i]
        self._recent.save()
        self.move_cursor(direction, 0)
        self._mapping = self._make_mapping()


def make_board(
    config: Config, all_emojis: list[Emoji], emoji_groups: list[Emoji]
) -> Board:
    board = Board(config, all_emojis, emoji_groups)
    return board
