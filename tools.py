import csv


def add_emoji_to_unicode_data(file_path: str):
    with (
        open(file_path, mode="r", encoding="utf-8") as csvfile,
        open(file_path + "c", mode="w", encoding="utf-8") as outfile,
    ):
        reader = csv.reader(csvfile, delimiter=";")
        for row in reader:
            if len(row) < 3:
                continue
            unicode = int(row[0], 16)
            if (
                (unicode >= 0x0 and unicode < 0x20)
                or (unicode >= 0x7F and unicode < 0xA0)
                or (unicode >= 0x400 and unicode < 0xF000)
                or unicode >= 0xF0000
                or unicode in (0x2029, 0x2029)
            ):
                continue
            char = chr(unicode)

            try:
                outfile.write(f"{char},{",".join(row)}\n")
            except:
                pass

if __name__ == "__main__":
    add_emoji_to_unicode_data("UnicodeData.txt")
