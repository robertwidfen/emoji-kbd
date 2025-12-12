import csv

import tools


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
                (unicode >= 0x0 and unicode < 0x20)
                or (unicode >= 0x7F and unicode < 0xA0)
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
                e = Emoji(char, unicode, "box drawing", "", name, "")
                emojis.append(e)
            elif name.find("arrow") > -1:
                e = Emoji(char, unicode, "arrows", "", name, "")
                emojis.append(e)
            elif name.find("greek") > -1:
                e = Emoji(char, unicode, "greek", "", name, "")
                emojis.append(e)
            elif category == "Sm":
                e = Emoji(char, unicode, "math", "", name, "")
                emojis.append(e)
            elif category == "Sc":
                e = Emoji(char, unicode, "objects", "money", name, "")
                emojis.append(e)
            elif category == "Zs" or category.startswith("P"):
                e = Emoji(char, unicode, "space & punctuation", category, name, "")
                emojis.append(e)
            else:
                # will be slow with all of them?
                e = Emoji(char, unicode, "all the rest", category, name, "")
                emojis.append(e)
                pass
    return emojis


def normalize_group(emoji: Emoji) -> str | None:
    g, sg = (emoji.group, emoji.subgroup)
    if g.startswith("extras-") or g == "component" or not g:
        return None
    if g == "smileys-emotion":
        if sg in ("face-costume", "cat-face", "monkey-face") or emoji.char in (
            "😈",
            "👿",
            "💀",
            "☠️",
        ):
            return "🤡"
        if sg in ("face-neutral-skeptical") or emoji.char in ("😔", "😪", "😴", "🫩"):
            return "😐️"
        if sg in ("face-hat", "face-glasses"):
            return "🥳"
        if sg in ("face-concerned", "face-negative", "face-unwell", "face-fearful"):
            return "☹️"
        if sg == "emotion" or sg == "heart":
            return "❤️"
        else:
            return "😀"
    if emoji.char in ("🫪",):
        return "😐️"
    if g == "people-body":
        if sg.startswith("hand"):
            return "👍️"
        else:
            return "👂️"
    if g == "animals-nature":
        if sg.startswith("animal-"):
            return "🐒"
        elif sg.startswith("plant-"):
            return "🌿"
    if emoji.char in ("🫈", "🫍"):
        return "🐒"
    if g == "food-drink":
        if sg == "dishware":
            return "🍽️"
        return "🍎"
    if g == "activities":
        if sg == "event":
            return "🎄"
    if g == "travel-places":
        if sg == "sky-weather":
            return "☀️"
        if sg.startswith("transport-"):
            return "🚂"
        if sg == "time":
            return "⌚️"
        return "🏖️"
    if g == "objects":
        if sg == "light-video":
            return "📸"
        if sg == "science":
            return "⚗️"
        if sg == "tool" or emoji.tags.find("tool") > -1:
            return "🔧"
        if sg == "clothing":
            return "👕"
        if sg == "money":
            return "💰️"
        if sg.startswith("music") or sg in ("sound",) or emoji.char in ("🪊", "🎼"):
            return "🎶"
        if sg in ("phone", "computer"):
            return "📱"
        if sg == "other-object" or emoji.char in ("🪎", "🫯"):
            return "🗿"
        # return g
    if g == "symbols":
        return "☯️"
    if emoji.group == "flags" and emoji.subgroup != "flag":
        return "🇦🇨"
    if g == "box drawing":
        return "⌧"
    if g == "arrows":
        return "➹"
    if g == "math":
        return "∛"
    if g == "greek":
        return "Ω"
    if g == "space & punctuation":
        return "␠"
    if g == "all the rest":
        return "…"
    return emoji.group + ">" + emoji.subgroup


def get_grouped_emojis(emojis: list[Emoji]) -> list[Emoji]:
    groups: list[Emoji] = []
    mapping: dict[str, Emoji] = {}
    for e in emojis:
        g = normalize_group(e)
        if g is None:
            continue
        if g not in mapping:
            char = g if len(g) < 5 else ""
            groups.append(Emoji(char, group=e.group, subgroup=e.subgroup))
            mapping[g] = groups[-1]
        mapping[g].add(e)
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


if __name__ == "__main__":
    main()
