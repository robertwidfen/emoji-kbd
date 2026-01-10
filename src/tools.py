import csv
import logging as log
import os
import shutil
import subprocess
import requests
from pathlib import Path


def add_emoji_to_unicode_data(file_path: str):
    with (
        open(file_path, encoding="utf-8") as csvfile,
        open(
            os.path.dirname(file_path) + f"/e{os.path.basename(file_path)}",
            mode="w",
            encoding="utf-8",
        ) as outfile,
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
            except UnicodeEncodeError:
                log.error(f"Encoding error at '{unicode}'.")


def download(url, local_filename):
    try:
        log.info(f"Downloading '{url}'...")
        file_dir = Path(local_filename).parent
        file_dir.mkdir(parents=True, exist_ok=True)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()

        with open(local_filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        log.info(f"Saved download successfully to '{local_filename}'.")
    except Exception as e:
        log.error(f"Error downloading the file: {e}")
        raise e


def download_if_missing(url: str, local_filename: str) -> bool:
    if not os.path.exists(local_filename):
        try:
            download(url, local_filename)
        except Exception as e:
            raise ValueError(f"Failed to download '{url}' to '{local_filename}'.") from e
    return os.path.exists(local_filename)


def run_command(command: list[str], input: str | None = None):
    try:
        encoded_input = input.encode() if input is not None else None
        subprocess.run(command, input=encoded_input, check=True)
    except FileNotFoundError:
        log.warning(f"{command} not found.")
    except Exception as e:
        log.error(f"{command} failed with: {e}")


def get_conf_file(filename: str) -> str:
    if os.environ.get("EMOJI_KBD_DEV"):
        return str(Path("res") / filename)
    config_dir = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "emoji-kbd"
    config_dir.mkdir(parents=True, exist_ok=True)
    default_config = Path(__file__).parent.parent / "res" / filename
    if not (config_dir / filename).exists() and default_config.exists():
        shutil.copy(default_config, config_dir / filename)
        log.info(f"Copied default config from {default_config}")
    path = str(config_dir / filename)
    log.info(f"Config file: {path}")
    return path


def get_state_file(filename: str) -> str:
    if os.environ.get("EMOJI_KBD_DEV"):
        path = str(Path(".local") / filename)
    else:
        state_home = os.getenv("XDG_STATE_HOME", Path.home() / ".local" / "state")
        state_dir = Path(state_home) / "emoji-kbd"
        state_dir.mkdir(parents=True, exist_ok=True)
        path = str(state_dir / filename)
    log.info(f"State file: {path}")
    return path

cache_file_set = set()

def get_cache_file(filename: str) -> str:
    if os.environ.get("EMOJI_KBD_DEV"):
        path = str(Path(".local") / filename)
    else:
        cache_home = os.getenv("XDG_CACHE_HOME", Path.home() / ".cache")
        cache_dir = Path(cache_home) / "emoji-kbd"
        cache_dir.mkdir(parents=True, exist_ok=True)
        path = str(cache_dir / filename)
    cache_file_set.add(path)
    log.info(f"Cache file: {path}")
    return path


if __name__ == "__main__":
    log.basicConfig(
        level=log.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    add_emoji_to_unicode_data(".local/UnicodeData.txt")
