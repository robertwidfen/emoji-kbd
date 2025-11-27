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
        self.annotation = annotation
        self.tags = tags
        self.skintone: list[Emoji] = []

    def __repr__(self):
        return f"Emoji({self.char}, {self.unicode}, {self.group} > {self.subgroup})"


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
                # if row[1].find("-200D-") > -1:
                #     continue
                # elif len(row[1]) != 5:
                #     continue
                e = Emoji(*row[0:6])
                emojis.append(e)
    return emojis


class Group:
    def __init__(self, group_name: str, subgroup_name: str):
        self.group_name = group_name
        self.subgroup_name = subgroup_name
        self.emojis: list[Emoji] = []

    def append(self, emoji: Emoji):
        self.emojis.append(emoji)

    def __repr__(self):
        return f"Group({self.group_name}, {self.subgroup_name}, {self.emojis[0]}[{len(self.emojis)}])"


def get_grouped_emojis(emojis: list[Emoji], max_count: int) -> list[Group]:
    groups: list[Group] = []
    g = None
    sg = None
    for e in emojis:
        if e.group != g or e.subgroup != sg or len(groups[-1].emojis) >= max_count:
            groups.append(Group(e.group, e.subgroup))
            g = e.group
            sg = e.subgroup
        groups[-1].append(e)
    return groups


def get_emojis_groups(max_count: int = 0) -> tuple[list[Emoji], list[Group]]:
    emojis = read_openmoji_csv("openmoji.csv")
    groups = get_grouped_emojis(emojis, max_count)

    # sqaush small groups together
    if max_count > 0:
        i = 0
        while i < len(groups) - 1:
            if (
                groups[i].group_name == groups[i + 1].group_name
                and len(groups[i].emojis) + len(groups[i + 1].emojis) < max_count
            ):
                groups[i].emojis.extend(groups[i + 1].emojis)
                groups[i].subgroup_name += ", " + groups[i + 1].subgroup_name
                del groups[i + 1]
            else:
                i += 1

    return (emojis, groups)


def main():
    (emojis, groups) = get_emojis_groups(12 * 4)
    print(f"Total emojis loaded: {len(emojis)}")
    for emoji in emojis[:50]:
        print(emoji)
    print(f"Total groups: {len(groups)}")
    for g in groups:
        print(f"{g.emojis[0].char}[{len(g.emojis)}] {g.group_name} > {g.subgroup_name}")


if __name__ == "__main__":
    main()
