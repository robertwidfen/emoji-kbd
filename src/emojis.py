import csv
import logging as log
import os
import re
from dataclasses import dataclass

from config import Config, load_config
from tools import download_if_missing, get_cache_file

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
        self.group = group  # the emoji group
        self.subgroup = subgroup  # the emoji subgroup
        self.name = name  # the emoji name/annotation
        self.tags = tags  # the emoji tags
        self.emojis: list[Emoji] = []  # list of sub emojis, e.g. group, skintone variants
        self.mark: str = ""  # mark for skintone variants, favorites, etc.
        self.order = order  # optional order for sorting and recently used

    def __repr__(self):
        return f"Emoji({self.char}, {self.unicode}, {self.name}, {self.group} > {self.subgroup}, tags={self.tags}, emojis={len(self.emojis) if self.emojis else 0}, order={self.order})"

    def append(self, emoji: "Emoji"):
        if not self.emojis:
            self.emojis = []
        if not self.char:
            self.char = emoji.char
        if not self.group:
            self.group = emoji.group
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


def read_emojibase_data(file_path) -> tuple[list[Emoji], dict[str, str], dict[str, str]]:
    import json

    with open(file_path + "/messages.raw.json", encoding="utf-8") as f:
        messages = json.load(f)
    groups = {}
    for g in messages["groups"]:
        groups[g["key"]] = g["message"]
        groups[g["order"]] = g["key"]
    subgroups = {}
    for sg in messages["subgroups"]:
        subgroups[sg["key"]] = sg["message"]
        subgroups[sg["order"]] = sg["key"]

    with open(file_path + "/data.raw.json", encoding="utf-8") as f:
        data = json.load(f)

    emojis = []
    for item in data:
        if item["hexcode"].find("-") == -1:
            unicode = int(item["hexcode"], 16)
            if exclude_unicode(unicode):
                continue
        emoji = Emoji(
            char=item["emoji"],
            unicode=item["hexcode"],
            group=groups.get(item["group"], ""),
            subgroup=subgroups.get(item["subgroup"], ""),
            name=item["label"],
            tags=", ".join(item["tags"]),
        )
        if "skins" in item:
            emoji.mark = "🟤"
            for skin in item["skins"]:
                skin_emoji = Emoji(
                    char=skin["emoji"],
                    unicode=skin["hexcode"],
                    group=emoji.group,
                    subgroup=emoji.subgroup,
                    name=skin["label"],
                    tags=emoji.tags,
                )
                emoji.append(skin_emoji)
        emojis.append(emoji)

    return (emojis, groups, subgroups)


# A list of patterns to group UnicodeData.txt.
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
    with open(file_path, encoding="utf-8") as csvfile:
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

    return emojis


# A list of patterns to build new groups.
# First match defines the group.
# Either match by group & subgroup or char in char_list.
# Item format:
#   order on board, char, group_regex, subgroup_regex, char_list
group_patterns = (
    # normalized groups
    (0x040, "🤡", "smileys-emotion", "costume|cat|monkey", "😈👿💀☠️🗿🪬🫈"),
    (0x030, "😐️", "smileys-emotion", "face-neutral-skeptical", "🤔🫡😔😪😴🫩🫪🥸🧐"),
    (0x020, "☹️", "smileys-emotion", "negative|concerned|unwell", ""),
    (0x060, "❤️", "smileys-emotion", "emotion|heart", ""),
    (0x010, "😀", "smileys-emotion", "", ""),
    (0x050, "👍️", "people-body", "hand|body", "👣🫆"),
    (0x080, "💃", "people-body", "sport|activity|game|award-medal", ""),
    (0x081, "⚽️", "activities", "sport|activity|game|award-medal", "🎭️🖼️"),
    (0x070, "🧑", "people-body", "", ""),
    (0x090, "🐒", "animals-nature", "animal", "🫍"),
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


def normalize_group(emoji: Emoji) -> GroupPattern:
    group_patterns_compiled: list[GroupPattern] = []
    for p in group_patterns:
        p = list(p)
        p[2] = re.compile(p[2]) if p[2] else None  # type: ignore
        p[3] = re.compile(p[3]) if p[3] else None  # type: ignore
        group_patterns_compiled.append(GroupPattern(*p))  # type: ignore

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
            groups.append(Emoji(g.char, "", e.group, e.subgroup, "Group", "", g.order))
            group_map[g.char] = groups[-1]
        group_map[g.char].append(e)
    groups.sort(key=lambda e: e.order)
    return groups


def get_cached_emojis_groups(config: Config) -> tuple[list[Emoji], list[Emoji]]:
    groups: list[Emoji] = []
    group_map: dict[str, Emoji] = {}
    group_cache_file = get_cache_file("emoji-kbd-cache-groups.txt")
    with open(group_cache_file, encoding="utf-8") as f:
        for line in f:
            (char, emojis_str) = line.strip().split(";")
            g = Emoji(char, "", name="Group")
            groups.append(g)
            for e in emojis_str.split(","):
                group_map[e] = g
    log.info(f"Emoji group cache file '{group_cache_file}' loaded.")

    emojis: list[Emoji] = []
    emoji_cache_file = get_cache_file("emoji-kbd-cache-emojis.txt")
    with open(emoji_cache_file, encoding="utf-8") as f:
        for line in f:
            is_skin_tone = line.startswith("\t")
            (char, unicode, name, group, subgroup, tags) = line.strip().split(";")
            e = Emoji(char, unicode, group, subgroup, name, tags)
            if is_skin_tone:
                if not emojis[-1].mark:
                    emojis[-1].mark = "🟤"
                emojis[-1].append(e)
            else:
                emojis.append(e)
                group_map[e.unicode].append(e)
    log.info(f"Emoji cache file '{emoji_cache_file}' loaded.")

    return (emojis, groups)


def get_emojis_groups_build_cache(config: Config) -> tuple[list[Emoji], list[Emoji]]:
    emojibase_data = get_cache_file("emojibase")
    os.makedirs(emojibase_data, exist_ok=True)

    for f in ("/data.raw.json", "/messages.raw.json"):
        download_if_missing(config.sources.emojibase + f, emojibase_data + f)

    (emojis, lc_groups, lc_subgroups) = read_emojibase_data(emojibase_data)
    log.info(f"Emojibase file '{emojibase_data}' with {len(emojis)} emojis loaded.")
    skin_tones = 0
    for e in emojis:
        if e.emojis:
            skin_tones += len(e.emojis)
    log.info(f"{skin_tones} skin tone variants found.")
    log.info(f"A total of {len(emojis) + skin_tones} emojis.")

    unicode_data = get_cache_file("UnicodeData.txt")
    download_if_missing(config.sources.unicode_data, unicode_data)
    unicode_emojis = read_unicode_data(unicode_data)
    log.info(f"UnicodeData file '{unicode_data}' with {len(unicode_emojis)} symbols loaded.")

    # duplicate checking
    emojis_set = set(e.unicode for e in emojis)
    duplicates = 0
    for e in unicode_emojis:
        if e.unicode not in emojis_set:
            emojis.append(e)
        else:
            duplicates += 1
    log.info(f"Skipped {duplicates} duplicate symbols from UnicodeData.txt.")
    log.info(f"{len(unicode_emojis) - duplicates} symbols remain.")
    log.info(f"{len(emojis)} emojis and symbols collected.")

    groups = get_grouped_emojis(emojis)
    log.info(f"Grouped into {len(groups)} groups.")

    # change group and subgroup to locale names
    for e in emojis:
        e.group = lc_groups.get(e.group, e.group)
        e.subgroup = lc_subgroups.get(e.subgroup, e.subgroup)
        for e in e.emojis:
            e.group = lc_groups.get(e.group, e.group)
            e.subgroup = lc_subgroups.get(e.subgroup, e.subgroup)

    emoji_cache_file = get_cache_file("emoji-kbd-cache-emojis.txt")
    with open(emoji_cache_file, "w", encoding="utf-8") as f:
        for e in emojis:
            f.write(f"{e.char};{e.unicode};{e.name};{e.group};{e.subgroup};{e.tags}\n")
            for e in e.emojis:
                f.write(f"\t{e.char};{e.unicode};{e.name};{e.group};{e.subgroup};{e.tags}\n")

    group_cache_file = get_cache_file("emoji-kbd-cache-groups.txt")
    with open(group_cache_file, "w", encoding="utf-8") as f:
        for g in groups:
            emojis_in_group = ",".join(e.unicode for e in g.emojis)
            f.write(f"{g.char};{emojis_in_group}\n")

    log.info(f"Caches written to '{emoji_cache_file}' and '{group_cache_file}'.")

    return (emojis, groups)


def get_emojis_groups(config: Config) -> tuple[list[Emoji], list[Emoji]]:
    emoji_cache_file = get_cache_file("emoji-kbd-cache-emojis.txt")
    group_cache_file = get_cache_file("emoji-kbd-cache-groups.txt")

    if not (os.path.exists(emoji_cache_file) and os.path.exists(group_cache_file)):
        get_emojis_groups_build_cache(config)

    return get_cached_emojis_groups(config)


def main():
    log.basicConfig(
        level=log.INFO,
        format="%(asctime)s.%(msecs)03d %(message)s",
        datefmt="%M:%S",
    )
    log.info("Loading emojis...")
    config = load_config()
    (emojis, groups) = get_emojis_groups(config)
    for g in groups:
        print(f"{g!r}")
        print(f"\t {''.join(e.char for e in g.emojis)}")


if __name__ == "__main__":
    main()
