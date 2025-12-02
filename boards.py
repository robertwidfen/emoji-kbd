import csv


class Emoji:
    def __init__(
        self,
        char: str,
        unicode: str,
        group: str,
        subgroup: str,
        annotation: str,
        tags: str,
    ):
        self.char = char
        self.unicode = unicode
        self.group = group
        self.subgroup = subgroup
        self.name = annotation
        self.tags = tags
        self.skintone: list[Emoji] = []

    def __repr__(self):
        return f"Emoji({self.char}, {self.unicode}, {self.name}, {self.group} > {self.subgroup})"


skintones = ("-1F3FB", "-1F3FC", "-1F3FD", "-1F3FE", "-1F3FF")


# emoji,hexcode,group,subgroups,annotation,tags,openmoji_tags
def read_openmoji_csv(file_path: str) -> list[Emoji]:
    emojis: list[Emoji] = []
    with open(file_path, mode="r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        # Skip header
        next(reader)
        for row in reader:
            if len(row) >= 3:  # Ensure there are enough columns
                if any(st in row[1] for st in skintones):
                    e = Emoji(*row[0:6])
                    emojis[-1].skintone.append(e)
                    continue
                e = Emoji(*row[0:6])
                emojis.append(e)
    return emojis


# hexcode;name;category;...
def read_unicode_data(file_path: str) -> list[Emoji]:
    emojis: list[Emoji] = []
    with open(file_path, mode="r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=";")
        for row in reader:
            if len(row) >= 3 and row[1].startswith("BOX DRAWINGS "):
                e = Emoji(
                    chr(int(row[0], 16)), row[0], "Box Drawing", "", row[1].lower(), ""
                )
                emojis.append(e)
            if len(row) >= 3 and row[1].find("ARROW") > -1:
                e = Emoji(
                    chr(int(row[0], 16)), row[0], "Arrows", "", row[1].lower(), ""
                )
                emojis.append(e)
    return emojis


class Group:

    def __init__(self, group_name: str, char: str = ""):
        self.group_name = group_name
        self.subgroup_name = ""
        self.char = char
        self.emojis: list[Emoji] = []

    def append(self, emoji: Emoji):
        if not self.char:
            self.char = emoji.char
        if emoji.subgroup not in self.subgroup_name:
            if self.subgroup_name:
                self.subgroup_name += ", "
            self.subgroup_name += emoji.subgroup
        self.emojis.append(emoji)

    def __repr__(self):
        return f"Group({self.group_name} {self.char})"


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
        if sg in ("face-concerned", "face-negative"):
            return "☹️"
        if sg == "heart":
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


def get_grouped_emojis(emojis: list[Emoji]) -> list[Group]:
    groups: list[Group] = []
    mapping: dict[str, Group] = {}
    for e in emojis:
        g = normalize_group(e)
        if g is None:
            continue
        if g not in mapping:
            groups.append(Group(e.group, g if len(g) < 5 else ""))
            mapping[g] = groups[-1]
        mapping[g].append(e)
    return groups


def get_emojis_groups() -> tuple[list[Emoji], list[Group]]:
    emojis = read_openmoji_csv("openmoji.csv")
    emojis.extend(read_unicode_data("UnicodeData.txt"))
    groups = get_grouped_emojis(emojis)
    return (emojis, groups)


def main():
    (emojis, groups) = get_emojis_groups()
    print(f"Total emojis loaded: {len(emojis)}")
    for emoji in emojis[:50]:
        print(emoji)
    print(f"Total groups: {len(groups)}")
    for g in groups:
        print(f"{g.char}[{len(g.emojis)}] {g.group_name} > {g.subgroup_name}")


if __name__ == "__main__":
    main()
