import csv


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
        self.unicode = unicode  # the unicode codepoint(s) as string
        self.group = group  # the emoji group
        self.subgroup = subgroup  # the emoji subgroup
        self.name = name  # the emoji name/annotation
        self.tags = tags  # the emoji tags
        self.emojis: list[Emoji] = []  # list of sub emjojis, e.g. skintone variants
        self.mark: str = ""  # mark for skintone variants, etc.
        self.order = order  # order for sorting

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


#             👍🏻        👍🏼        👍🏽        👍🏾        👍🏿
skintones = ("-1F3FB", "-1F3FC", "-1F3FD", "-1F3FE", "-1F3FF")


# openmoji.csv format:
# emoji,hexcode,group,subgroups,annotation,tags,openmoji_tags
def read_openmoji_csv(file_path: str) -> list[Emoji]:
    emojis: list[Emoji] = []
    with open(file_path, mode="r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header
        for row in reader:
            if len(row) <= 3:
                continue  # Ensure there are enough columns
            if any(st in row[1] for st in skintones):
                e = Emoji(*row[0:6])
                if not emojis[-1].mark:
                    emojis[-1].mark = "🟤"
                emojis[-1].add(e)
                continue
            e = Emoji(*row[0:6])
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
            char = chr(int(row[0], 16))
            unicode = row[0]
            name = row[1].lower()
            if name.startswith("box drawings "):
                e = Emoji(char, unicode, "Box Drawing", "", name, "")
                emojis.append(e)
            elif name.find("arrow") > -1:
                e = Emoji(char, unicode, "Arrows", "", name, "")
                emojis.append(e)
    return emojis


def normalize_group(emoji: Emoji) -> str | None:
    g, sg = (emoji.group, emoji.subgroup)
    if g.startswith("extras-") or g == "component":
        return None
    if g == "smileys-emotion":
        if sg in ("face-costume", "cat-face", "monkey-face") or emoji.unicode in (
            "1F608",
            "1F47F",
            "1F480",
            "2620",
        ):
            return "🤡"
        if sg in ("face-neutral-skeptical"):
            return "😐️"
        if sg in ("face-hat", "face-glasses"):
            return "🥳"
        if sg in ("face-concerned", "face-negative", "face-unwell", "face-fearful"):
            return "☹️"
        if sg == "emotion" or sg == "heart":
            return "❤️"
        else:
            return "😀"
    if g == "people-body":
        if sg.startswith("hand"):
            return "👍️"
        else:
            return "🧑"
    if g == "animals-nature":
        if sg.startswith("animal-"):
            return "🐒"
        elif sg.startswith("plant-"):
            return "🌿"
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
        if sg.startswith("music") or sg in ("sound",):
            return "🎶"
        if sg in ("phone", "computer"):
            return "📱"
        # return g
    if g == "symbols":
        return "☯️"
    if emoji.group == "flags" and emoji.subgroup != "flag":
        return "🇦🇨"
    if g == "Box Drawing":
        return "╬"
    if g == "Arrows":
        return "➹"
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


def get_emojis_groups() -> tuple[list[Emoji], list[Emoji]]:
    emojis = read_openmoji_csv("openmoji.csv")
    emojis.extend(read_unicode_data("UnicodeData.txt"))
    groups = get_grouped_emojis(emojis)
    return (emojis, groups)


def main():
    (emojis, groups) = get_emojis_groups()
    print(f"{len(emojis)} emojis loaded.")
    print(f"{len(groups)} groups generated.")
    for g in groups:
        print(f"{g!r}")


if __name__ == "__main__":
    main()
