import logging as log
import csv
import re
from dataclasses import dataclass

from config import Config, load_config
from tools import get_cache_file, download_if_missing

# Map of special unicode codes to short names for display on keys
special_name_map = {
    "0020": "SP",  # SPACE
    "00A0": "NB",  # NO-BREAK SPACE
    "202F": "nNB",  # NARROW NO-BREAK SPACE
    "2000": "ENQ",  # EN QUAD
    "2001": "EMQ",  # EM QUAD
    "2002": "EN",  # EN SPACE
    "2003": "EM",  # EM SPACE
    "2004": "3EM",  # THREE-PER-EM SPACE
    "2005": "4EM",  # FOUR-PER-EM SPACE
    "2006": "6EM",  # SIX-PER-EM SPACE
    "2007": "FS",  # FIGURE SPACE
    "2008": "PS",  # PUNCTUATION SPACE
    "2009": "TS",  # THIN SPACE
    "200A": "HS",  # HAIR SPACE
}


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

    def append(self, emoji: "Emoji"):
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


unicode_exclude_ranges = (
    (0x000000, 0x00009F),  # Normal characters
    (0x000400, 0x001FFE),  # CJK and Hangul
    (0x0020D0, 0x0020F0),  # Combining Diacritical Marks for Symbols
    (0x002C00, 0x00FFDB),  # CJK and Hangul
    (0x010100, 0x01EEFE),  # Various scripts
    (0x01F1E6, 0x01F1FF),  # REGIONAL INDICATOR SYMBOL LETTERS
    (0x01F3FB, 0x01F3FF),  # Skintone modifiers
    (0x01F9B0, 0x01F9B3),  # Hair style modifiers
    (0x01FBFA, 0x033479),  # Tags
    (0x0E0001, 0xFFFFFF),  # Tags and private use
)

unicode_exclude_points = (0x00AD, 0x2028, 0x2029)


def exclude_unicode(unicode: int) -> bool:
    exclude_range = any([l <= unicode <= h for (l, h) in unicode_exclude_ranges])
    exclude_char = unicode in unicode_exclude_points
    return exclude_range or exclude_char


# openmoji.csv format:
# emoji,hexcode,group,subgroups,annotation,tags,openmoji_tags
def read_openmoji_csv(file_path: str) -> list[Emoji]:
    emojis: list[Emoji] = []
    with open(file_path, mode="r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header
        for row in reader:
            # Skip invalid or extra emojis
            if len(row) <= 3 or row[2].startswith("extras-"):
                continue
            if row[1].find("-") == -1:
                unicode = int(row[1], 16)
                if exclude_unicode(unicode):
                    continue
            if any(st in row[1] for st in skintones):
                e = make_emoji_from_row(row)
                if not emojis[-1].mark:
                    emojis[-1].mark = "🟤"
                emojis[-1].append(e)
                continue
            e = make_emoji_from_row(row)
            emojis.append(e)
    return emojis


# group_name, subgroup|None, name_regex|None, category_regex|None
unicode_grouping = (
    ("box drawing", "", re.compile("box drawings "), None),
    ("arrows", "", re.compile("arrow"), None),
    ("greek", "", re.compile("greek"), None),
    ("math", "", None, re.compile("^Sm$")),
    ("objects", "money", None, re.compile("^Sc$")),
    ("space & punctuation", "", None, re.compile("^(Zs|P)")),
    ("all the rest", "", re.compile("."), None),
)


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
            if exclude_unicode(unicode):
                continue

            char = chr(unicode)
            unicode = row[0]
            name = row[1].lower()
            category = row[2]

            for group, subgroup, name_re, category_re in unicode_grouping:
                if (
                    isinstance(name_re, re.Pattern)
                    and name_re.search(name)
                    or isinstance(category_re, re.Pattern)
                    and category_re.search(category)
                ):
                    e = Emoji(char, unicode, group, subgroup or category, name)
                    emojis.append(e)
                    break
    log.info(f"UnicodeData: {len(emojis)} emojis loaded.")
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
    (0x040, "🤡", "smileys-emotion", "costume|cat|monkey", "😈👿💀☠️🗿🪬"),
    (0x030, "😐️", "smileys-emotion", "face-neutral-skeptical", "🤔🫡😔😪😴🫩🫪🥸🧐"),
    (0x020, "☹️", "smileys-emotion", "negative|concerned|unwell", ""),
    (0x060, "❤️", "smileys-emotion", "emotion|heart", ""),
    (0x010, "😀", "smileys-emotion", "", ""),
    (0x050, "👍️", "people-body", "hand|body", "👣🫆"),
    (0x080, "💃", "people-body", "sport|activity|game|award-medal", ""),
    (0x081, "⚽️", "activities", "sport|activity|game|award-medal", "🎭️🖼️"),
    (0x070, "💁‍♂️", "people-body", "", ""),
    (0x090, "🐒", "animals-nature", "animal", "🫈🫍"),
    (0x100, "🌿", "animals-nature", "plant", ""),
    (0x120, "🍽️", "food-drink", "dishware", ""),
    (0x110, "🍎", "food-drink", "", ""),
    (0x130, "☀️", "travel-places", "sky-weather", ""),
    (0x140, "🚂", "travel-places|symbols", "transport-", ""),
    (0x160, "⌚️", "travel-places", "time", ""),
    (0x150, "🏖️", "travel-places", "", "🪧"),
    (0x170, "🎄", "activities", "event", ""),
    (0x190, "📸", "objects", "light-video", ""),
    (0x180, "🔧", "objects|activities", "tool|science", "🎨🪢"),
    (0x200, "👕", "objects", "clothing", "🧵🪡🧶"),
    (0x210, "💰️", "objects", "money", ""),
    (0x220, "🎶", "objects", "music|sound", "🪊🎼"),
    (0x230, "🖥️", "objects", "phone|computer|mail", "📶🛜📳📴"),
    (0x240, "✏️", "objects", "writing|office|book-paper|lock", "🚬🪪"),
    (0x250, "🚪", "objects", "household", ""),
    (0x260, "🩺", "objects", "medical|other", ""),
    (0x270, "☯️", "symbols", "", "🗣️👤👥🫂"),
    (0x280, "🏳️‍🌈", "flags", "", ""),
    (0x290, "➹", "arrows", "", ""),
    (0x300, "∛", "math", "", ""),
    (0x310, "Ω", "greek", "", ""),
    (0x320, "╚", "box drawing", "", ""),
    (0x330, "␠", "space & punctuation", "", ""),
    # catch all
    (0x500, "…", "all the rest", "", ""),
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
            groups.append(Emoji(g.char, "", e.group, e.subgroup, "group", "", g.order))
            group_map[g.char] = groups[-1]
        group_map[g.char].append(e)
    groups.sort(key=lambda e: e.order)
    return groups


openmoji_src = "https://raw.githubusercontent.com/hfg-gmuend/openmoji/refs/heads/master/data/openmoji.csv"
unicodedata_src = "https://www.unicode.org/Public/UCD/latest/ucd/UnicodeData.txt"


def get_emojis_groups(config: Config) -> tuple[list[Emoji], list[Emoji]]:
    openmoji = get_cache_file("openmoji.csv")
    download_if_missing(config.sources.openmoji, openmoji)
    emojis = read_openmoji_csv(openmoji)

    unicode_data = get_cache_file("UnicodeData.txt")
    download_if_missing(config.sources.unicode_data, unicode_data)
    unicode_emojis = read_unicode_data(unicode_data)

    open_emojis_set = set(e.unicode for e in emojis)  # for duplicate checking
    for e in unicode_emojis:
        if e.unicode not in open_emojis_set:
            emojis.append(e)

    groups = get_grouped_emojis(emojis)

    log.info(f"{len(emojis)} emojis in {len(groups)} groups loaded.")
    return (emojis, groups)


def main():
    log.basicConfig(
        level=log.ERROR,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    config = load_config()
    (emojis, groups) = get_emojis_groups(config)
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
