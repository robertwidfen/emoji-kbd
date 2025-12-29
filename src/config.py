from typing import Literal, get_origin, get_args
from dataclasses import dataclass, field, fields
from pathlib import Path
import tomllib

from tools import get_conf_file


@dataclass
class BoardConfig:
    layout: str = "US"
    default: str = "⟲"


@dataclass
class TerminalConfig:
    width: int = 47
    height: int = 12
    font_size: int = 20
    close_cmd: str = "./scripts/emoji-kbd-term-hl-close"


@dataclass
class GuiConfig:
    width: int = 600
    height: int = 280
    key_font_size: float = 0.2
    mark_font_size: float = 0.2
    emoji_font_size: float = 0.56
    emoji_font_size2: float = 0.8


@dataclass
class LayoutConfig:
    name: str
    char: str
    kbd: str


@dataclass
class SourcesConfig:
    noto_color_emoji: str = (
        "https://github.com/googlefonts/noto-emoji/raw/refs/heads/main/fonts/NotoColorEmoji.ttf"
    )
    noto_color_emoji_win32: str = (
        "https://github.com/googlefonts/noto-emoji/raw/refs/heads/main/fonts/NotoColorEmoji_WindowsCompatible.ttf"
    )
    openmoji: str = (
        "https://raw.githubusercontent.com/hfg-gmuend/openmoji/refs/heads/master/"
        "data/openmoji.csv"
    )
    unicode_data: str = "https://www.unicode.org/Public/UCD/latest/ucd/UnicodeData.txt"


@dataclass
class LoggingConfig:
    log_mode: str = "w"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"


default_layouts = [
    LayoutConfig(
        name="US",
        char="🇺🇸",
        kbd="""
1234567890-=
QWERTYUIOP[]
ASDFGHJKL;'
ZXCVBNM,./
""",
    ),
    LayoutConfig(
        name="DE",
        char="🇩🇪",
        kbd="""
1234567890ß´
QWERTZUIOPÜ+
ASDFGHJKLÖÄ#
<YXCVBNM,.-
""",
    ),
    LayoutConfig(
        name="Bone Corne",
        char="🦴",
        kbd="""
JDUAX PHLMW
CTIEO BNRSG
?,VFQ YKZ.-
""",
    ),
]


@dataclass
class Config:
    board: BoardConfig = field(default_factory=BoardConfig)
    terminal: TerminalConfig = field(default_factory=TerminalConfig)
    gui: GuiConfig = field(default_factory=GuiConfig)
    layout: list[LayoutConfig] = field(default_factory=lambda: default_layouts.copy())
    sources: SourcesConfig = field(default_factory=SourcesConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    def get_layout(self, name: str | None = None) -> str:
        if name is None:
            name = self.board.layout
        for l in self.layout:
            if l.name.lower() == name.lower():
                return l.kbd
        raise ValueError(f"Layout '{name}' not found in configuration.")


default_path = get_conf_file("emoji-kbd.toml")


def load_config(config_path: str = default_path) -> Config:
    """Load configuration from TOML file.

    Raises:
        FileNotFoundError: If config file doesn't exist
        tomllib.TOMLDecodeError: If config file is malformed
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "rb") as f:
        data = tomllib.load(f)

    config = Config()

    for key, value in data.items():
        if key not in Config.__dataclass_fields__:
            raise ValueError(f"Unknown config section: {key}")
        field_type = Config.__dataclass_fields__[key].type
        if callable(field_type):  # dataclass
            if get_origin(field_type) == list:
                item_type = get_args(field_type)[0]
                items = []
                for item in value:
                    items.append(item_type(**item))
                config.__setattr__(key, items)
            else:  # single dataclass
                config.__setattr__(key, field_type(**value))
        else:
            config.__setattr__(key, value)

    return config


if __name__ == "__main__":
    import sys
    from pprint import pprint

    if len(sys.argv) < 2:
        # Pretty print entire config when no args
        config = load_config()
        pprint(config, width=100, sort_dicts=False)
    else:
        # Query mode: python config.py <path.to.value> [config_file]
        # Example: python config.py terminal.width
        # Example: python config.py layout[0].name
        query = sys.argv[1]
        config_file = sys.argv[2] if len(sys.argv) > 2 else default_path

        try:
            config = load_config(config_file)

            # Parse query path like "terminal.width" or "layout[0].name"
            parts = query.replace("[", ".").replace("]", "").split(".")
            value = config

            for part in parts:
                if part.isdigit():
                    value = value[int(part)]  # type: ignore
                else:
                    value = getattr(value, part)

            print(value)
        except (AttributeError, IndexError, KeyError) as e:
            print(f"Error: Invalid query path '{query}'", file=sys.stderr)
            sys.exit(1)
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
