import requests
import csv


def add_emoji_to_unicode_data(file_path: str):
    with (
        open(file_path, mode="r", encoding="utf-8") as csvfile,
        open("e" + file_path, mode="w", encoding="utf-8") as outfile,
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
                outfile.write(f"{char},{','.join(row)}\n")
            except:
                pass


def download(url):
    filename = url.split("/")[-1]
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, "wb") as file:
            file.write(response.content)
            print(f"'{filename}' downloaded")
    else:
        print(f"Error '{response.status_code}' while downloading {url}")


if __name__ == "__main__":
    download("https://www.unicode.org/Public/UCD/latest/ucd/UnicodeData.txt")
    download(
        "https://raw.githubusercontent.com/hfg-gmuend/openmoji/refs/heads/master/data/openmoji.csv"
    )
    add_emoji_to_unicode_data("UnicodeData.txt")
