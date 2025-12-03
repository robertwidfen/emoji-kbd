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
            char = chr(int(row[0], 16))

            try:
                outfile.write(f"{char},{",".join(row)}\n")
            except:
                pass

if __name__ == "__main__":
    add_emoji_to_unicode_data("UnicodeData.txt")
