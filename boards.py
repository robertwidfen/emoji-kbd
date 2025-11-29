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
        if sg in ("face-neutral-skeptical", "face-concerned", "face-negative"):
            return "☹️"
        if sg in ("face-costume", "cat-face", "monkey-face"):
            return "😺"
        if sg == "heart":
            return "❤️"
        else:
            return "😀"
    if g == "animals-nature":
        if sg.startswith("animal-"):
            return "🐒"
        elif sg.startswith("plant-"):
            return "🌸"
        else:
            return "🌲"
    if g == "food-drink":
        if sg == "dishware":
            return "🍽️"
        return "🍎"
    if g == "objects":
        if sg.startswith("tool-"):
            return "🔧"
        if sg.startswith("music") or sg in ("sound",):
            return "🎶"
        return g
    if g == "travel-places":
        if sg == "sky-weather":
            return "☀️"
        if sg == "time":
            return "⌚️"
        return "🏠"
    if g == "symbols":
        return ""
    if g == "people-body":
        if sg.startswith("hand"):
            return "👍️"
        else:
            return "🧑"
    if emoji.group == "flags" and emoji.subgroup != "flag":
        return "🏳️‍🌈"
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
        groups[-1].append(e)
    return groups


def get_emojis_groups() -> tuple[list[Emoji], list[Group]]:
    emojis = read_openmoji_csv("openmoji.csv")
    groups = get_grouped_emojis(emojis)
    return (emojis, groups)


def main():
    (emojis, groups) = get_emojis_groups()
    print(f"Total emojis loaded: {len(emojis)}")
    for emoji in emojis[:50]:
        print(emoji)
    print(f"Total groups: {len(groups)}")
    for g in groups:
        print(f"{g.emojis[0].char}[{len(g.emojis)}] {g.group_name} > {g.subgroup_name}")


if __name__ == "__main__":
    main()
