import logging as log
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, get_args, get_origin

from tools import get_conf_file


@dataclass
class BoardConfig:
    layout: str = "US"
    default: str = "⟲"
    locale: str = "en"


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
    noto_color_emoji: str = "https://github.com/googlefonts/noto-emoji/raw/refs/heads/main/fonts/NotoColorEmoji.ttf"  # fmt: skip
    noto_color_emoji_win32: str = "https://github.com/googlefonts/noto-emoji/raw/refs/heads/main/fonts/NotoColorEmoji_WindowsCompatible.ttf"  # fmt: skip
    emojibase: str = "https://github.com/milesj/emojibase/raw/refs/heads/master/packages/data"  # fmt: skip
    unicode_data: str = "https://www.unicode.org/Public/UCD/latest/ucd/UnicodeData.txt"  # fmt: skip
    unicode_annotations: str = "https://raw.githubusercontent.com/unicode-org/cldr/refs/heads/main/common/annotations/"  # fmt: skip


@dataclass
class LoggingConfig:
    log_mode: Literal["w", "a"] = "w"
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
        for layout in self.layout:
            if layout.name.lower() == name.lower():
                return layout.kbd
        raise ValueError(f"Layout '{name}' not found in configuration.")


default_path = get_conf_file("emoji-kbd.toml")


def __load_config(config_path: str = default_path) -> Config:
    """Load configuration from TOML file.

    Raises:
        FileNotFoundError: If config file does not exist
        tomllib.TOMLDecodeError: If config file is malformed
        KeyError: If section/key does not exit
        ValueError: If field type does not match
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "rb") as f:
        data = tomllib.load(f)

    config = Config()

    for key, value in data.items():
        if key not in Config.__dataclass_fields__:
            raise KeyError(f"Unknown config section '{key}'")
        field_type = Config.__dataclass_fields__[key].type
        if callable(field_type):  # dataclass
            if get_origin(field_type) is list:
                item_type = get_args(field_type)[0]
                items = []
                for item in value:
                    items.append(item_type(**item))
                config.__setattr__(key, items)
            else:  # single dataclass
                for sub_key in value:
                    if sub_key not in field_type.__annotations__:
                        raise KeyError(f"Unknown key '{sub_key}' in section '{key}'")
                    expected_type = field_type.__annotations__[sub_key]
                    actual_value = value[sub_key]
                    origin = get_origin(expected_type)
                    if origin is Literal:
                        # For Literal types, check if value is one of the allowed values
                        allowed_values = get_args(expected_type)
                        if actual_value not in allowed_values:
                            raise ValueError(
                                f"Invalid value for key '{sub_key}' in section '{key}'. "
                                f"Expected one of {allowed_values}, got {actual_value}."
                            )
                    else:
                        if not isinstance(actual_value, expected_type):
                            raise ValueError(
                                f"Invalid type for key '{sub_key}' in section '{key}'. "
                                f"Expected {expected_type.__name__}, got {type(actual_value).__name__}."
                            )
                config.__setattr__(key, field_type(**value))
        else:
            config.__setattr__(key, value)

    return config

def load_config(config_path: str = default_path) -> Config:
    try:
        return __load_config(config_path)
    except Exception as e:
        log.error(f"Failed to load configuration from {config_path}: {e}")
        raise

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
        except (AttributeError, IndexError, KeyError):
            print(f"Error: Invalid query path '{query}'", file=sys.stderr)
            sys.exit(1)
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
