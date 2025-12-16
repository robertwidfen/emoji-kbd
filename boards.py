import logging as log
import csv
import re

import tools
from dataclasses import dataclass


class Emoji:

    def __init__(
        self,
        char: str,
        unicode: str = "",
        group: str = "",
        subgroup: str = "",
        name: str = "",
        tags: str = "",
        order: int = 0,
    ):
        self.char = char  # the emoji character
        self.unicode = unicode.upper()  # the unicode codepoint(s) as string
        self.group = group.lower()  # the emoji group
        self.subgroup = subgroup.lower()  # the emoji subgroup
        self.name = name.lower()  # the emoji name/annotation
        self.tags = tags.lower()  # the emoji tags
        self.emojis: list[Emoji] = []  # list of sub emjojis, e.g. skintone variants
        self.mark: str = ""  # mark for skintone variants, etc.
        self.order = order  # order for sorting and recently used

    def __repr__(self):
        return f"Emoji({self.char}, {self.unicode}, {self.name}, {self.group} > {self.subgroup}, tags={self.tags}, emojis={len(self.emojis) if self.emojis else 0}, order={self.order})"

    def add(self, emoji: "Emoji"):
        if not self.emojis:
            self.emojis = []
        if not self.char:
            self.char = emoji.char
        if emoji.subgroup not in self.subgroup:
            if self.subgroup:
                self.subgroup += ", "
            self.subgroup += emoji.subgroup
        self.emojis.append(emoji)

    def clone(self) -> "Emoji":
        e = Emoji(
            char=self.char,
            unicode=self.unicode,
            group=self.group,
            subgroup=self.subgroup,
            name=self.name,
            tags=self.tags,
            order=self.order,
        )
        e.emojis = self.emojis.copy()
        e.mark = self.mark
        return e


#             👍🏻        👍🏼        👍🏽        👍🏾        👍🏿
skintones = ("-1F3FB", "-1F3FC", "-1F3FD", "-1F3FE", "-1F3FF")


def make_emoji_from_row(row: list[str]) -> Emoji:
    return Emoji(
        char=row[0],
        unicode=row[1],
        group=row[2],
        subgroup=row[3],
        name=row[4],
        tags=row[5],
    )


# openmoji.csv format:
# emoji,hexcode,group,subgroups,annotation,tags,openmoji_tags
def read_openmoji_csv(file_path: str) -> list[Emoji]:
    emojis: list[Emoji] = []
    with open(file_path, mode="r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header
        for row in reader:
            # Skip invalid or extra emojis
            if len(row) <= 3 or row[2] == "extras-openmoji":
                continue
            if any(st in row[1] for st in skintones):
                e = make_emoji_from_row(row)
                if not emojis[-1].mark:
                    emojis[-1].mark = "🟤"
                emojis[-1].add(e)
                continue
            e = make_emoji_from_row(row)
            emojis.append(e)
    return emojis


# UnicodeData.txt format:
# hexcode;name;category;...
def read_unicode_data(file_path: str) -> list[Emoji]:
    emojis: list[Emoji] = []
    with open(file_path, mode="r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=";")
        for row in reader:
            if len(row) < 3:
                continue
            unicode = int(row[0], 16)
            if (
                (unicode < 0xA0)
                or (unicode >= 0x400 and unicode < 0x1FFF)
                or (unicode >= 0x2C00 and unicode < 0xFFDC)
                or (unicode >= 0x10100 and unicode < 0x1EEFF)
                or unicode >= 0xF0000
                or unicode in (0x2029, 0x2029)
            ):
                continue

            char = chr(unicode)
            unicode = row[0]
            name = row[1].lower()
            category = row[2]

            if name.startswith("box drawings "):
                e = Emoji(char, unicode, "box drawing", category, name)
                emojis.append(e)
            elif name.find("arrow") > -1:
                e = Emoji(char, unicode, "arrows", category, name)
                emojis.append(e)
            elif name.find("greek") > -1:
                e = Emoji(char, unicode, "greek", category, name)
                emojis.append(e)
            elif category == "Sm":
                e = Emoji(char, unicode, "math", category, name)
                emojis.append(e)
            elif category == "Sc":
                e = Emoji(char, unicode, "objects", "money", name)
                emojis.append(e)
            elif category == "Zs" or category.startswith("P"):
                e = Emoji(char, unicode, "space & punctuation", category, name)
                emojis.append(e)
            else:
                # will be slow with all of them?
                e = Emoji(char, unicode, "all the rest", category, name)
                emojis.append(e)
                pass
    return emojis


# A list of patterns to normalize groups.
# First match defines the normalized group.
# Either match of group & subgroup or char in char_list.
# Item format:
#   order on board, char, group_regex, subgroup_regex, char_list
group_patterns = (
    # ignored ones
    (0, "", "^(extras-unicode|component|)$", "", ""),
    # normalized groups
    (0x04, "🤡", "smileys-emotion", "costume|cat|monkey", "😈👿💀☠️🗿🪬"),
    (0x03, "😐️", "smileys-emotion", "face-neutral-skeptical", "😔😪😴🫩🫪🥸🧐"),
    (0x02, "☹️", "smileys-emotion", "negative|concerned|unwell", ""),
    (0x06, "❤️", "smileys-emotion", "emotion|heart", ""),
    (0x01, "😀", "smileys-emotion", "", ""),
    (0x05, "👍️", "people-body", "hand|body", "👣🫆"),
    (0x08, "⚽️", "people-body|activities", "sport|activity|game|award-medal", "🎭️🖼️"),
    (0x07, "💁‍♂️", "people-body", "", ""),
    (0x09, "🐒", "animals-nature", "animal", "🫈🫍"),
    (0x10, "🌿", "animals-nature", "plant", ""),
    (0x12, "🍽️", "food-drink", "dishware", ""),
    (0x11, "🍎", "food-drink", "", ""),
    (0x13, "☀️", "travel-places", "sky-weather", ""),
    (0x14, "🚂", "travel-places|symbols", "transport-", ""),
    (0x16, "⌚️", "travel-places", "time", ""),
    (0x15, "🏖️", "travel-places", "", "🪧"),
    (0x17, "🎄", "activities", "event", ""),
    (0x19, "📸", "objects", "light-video", ""),
    (0x18, "🔧", "objects|activities", "tool|science", "🎨🪢"),
    (0x20, "👕", "objects", "clothing", "🧵🪡🧶"),
    (0x21, "💰️", "objects", "money", ""),
    (0x22, "🎶", "objects", "music|sound", "🪊🎼"),
    (0x23, "🖥️", "objects", "phone|computer|mail", "📶🛜📳📴"),
    (0x24, "✏️", "objects", "writing|office|book-paper|lock", "🚬🪪"),
    (0x25, "🚪", "objects", "household", ""),
    (0x26, "🩺", "objects", "medical|other", ""),
    (0x27, "☯️", "symbols", "", "🗣️👤👥🫂"),
    (0x28, "🏳️‍🌈", "flags", "", ""),
    (0x29, "➹", "arrows", "", ""),
    (0x30, "∛", "math", "", ""),
    (0x31, "Ω", "greek", "", ""),
    (0x32, "╚", "box drawing", "", ""),
    (0x33, "␠", "space & punctuation", "", ""),
    # catch all
    (0x50, "…", "all the rest", "", ""),
)


@dataclass
class GroupPattern:
    order: int
    char: str
    group: re.Pattern | None
    subgroup: re.Pattern | None
    chars: str

    def __hash__(self) -> int:
        return self.char.__hash__()


group_patterns_compiled: list[GroupPattern] = []
for p in group_patterns:
    p = list(p)
    p[2] = re.compile(p[2]) if p[2] else None  # type: ignore
    p[3] = re.compile(p[3]) if p[3] else None  # type: ignore
    group_patterns_compiled.append(GroupPattern(*p))  # type: ignore


def normalize_group(emoji: Emoji) -> GroupPattern:
    for p in group_patterns_compiled:
        if emoji.char == "🐵" and p.char == "🐒":
            pass
        if p.chars and emoji.char in p.chars:
            return p
        if p.group and not p.group.search(emoji.group):
            continue
        if p.subgroup and not p.subgroup.search(emoji.subgroup):
            continue
        return p
    log.warning(
        f"No group for: '{emoji.char}': '{emoji.name}', '{emoji.group}' > '{emoji.subgroup}'"
    )
    return group_patterns_compiled[-1]  # catch all


def get_grouped_emojis(emojis: list[Emoji]) -> list[Emoji]:
    groups: list[Emoji] = []
    group_map: dict[str, Emoji] = {}
    for e in emojis:
        g = normalize_group(e)
        if g.order == 0:
            continue
        if g.char not in group_map:
            groups.append(
                Emoji(g.char, group=e.group, subgroup=e.subgroup, order=g.order)
            )
            group_map[g.char] = groups[-1]
        group_map[g.char].add(e)
    groups.sort(key=lambda e: e.order)
    return groups


omenmoji_src = "https://raw.githubusercontent.com/hfg-gmuend/openmoji/refs/heads/master/data/openmoji.csv"
unicodedata_src = "https://www.unicode.org/Public/UCD/latest/ucd/UnicodeData.txt"


def get_emojis_boards() -> tuple[list[Emoji], list[Emoji]]:
    tools.download_if_missing(omenmoji_src, "openmoji.csv")
    emojis = read_openmoji_csv("openmoji.csv")
    open_emojis_set = set(e.unicode for e in emojis)  # for duplicate checking
    tools.download_if_missing(unicodedata_src, "UnicodeData.txt")
    unicode_emojis = read_unicode_data("UnicodeData.txt")
    for e in unicode_emojis:
        if e.unicode not in open_emojis_set:
            emojis.append(e)
    groups = get_grouped_emojis(emojis)
    return (emojis, groups)


# DE QWERTZ keyboard layout
kbd = """
1234567890ß´
QWERTZUIOPÜ+
ASDFGHJKLÖÄ#
<YXCVBNM,.-
""".strip()

# US QWERTY keyboard layout
# kbd = """
# `1234567890-=
# QWERTYUIOP[]\
# ASDFGHJKL;'"
# ZXCVBNM,./
# """.strip()

# Corne bone keyboard layout
# kbd = """
# jduax phlmw
# ctieo bnrsg
# ?,vfq ykz.-
# """.strip()

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


def main():
    (emojis, groups) = get_emojis_boards()
    print(f"{len(emojis)} emojis loaded.")
    print(f"{len(groups)} groups generated.")
    for g in groups:
        print(f"{g!r}")
        print("\t", end="")
        for e in g.emojis[:70]:
            print(e.char, end="")
        print()


if __name__ == "__main__":
    main()
