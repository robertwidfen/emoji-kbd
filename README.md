# Emoji Kbd
It is all about efficiency - the fewer keys you need to type the better.
Emoji Kbd is made for efficiency. Pick emojis and characters with three
key presses.

<img alt="Screenshot" src="screenshot.png" width="550" />

or for a custom keyboard

<img alt="Screenshot" src="screenshot-corne.png" width="500" />

Just three key presses should be enough to get an emoji from the recent list,
1. Open picker with a hot key
2. Select emoji with associated key
3. Close and insert with Enter

# UI and How To Use
Top left is the emoji input field, right the search field.
In the middle is a (key)board like overview of emojis. Each one has a key in the left upper corner.
At the bottom is a status field.

Press a `key` to insert a emoji or open a group.
`Space` is a prefix key to allow for opening variants, e.g. skin tones.
Use the `cursor` keys, `Tab`, `Home` and `End` to navigate around.
Use `PageUp`/`PageDown` to switch pages.
Use `Esc`/`Backspace` to go back to previous board.

In the input field, a `key` press will insert the associated emoji. `Enter` will copy the emojis to the clipboard and close the window.

In the board, a `key` press will select the associated emoji. `Enter` will insert the emoji in the input field.

In the search field, `key` presses will insert a search term.  `Enter` will insert the first match in the input field and set focus to it again.

With the mouse 🖱️ a `left click` inserts/opens, a `right click` is back to previous board and a `double click` inserts and closes the window.

When the windows closes it will copy the content of the input field to the clipboard and print it to stdout.

# Recent List ⟲
Used emojis will be put automatically to the recent list.
Every item has a score and items are sorted by the score. 
A score >=100 makes a item a favorite.
When using an item its score will increase by 10 and the score of all others decrease by 1.

`Shift-Left`/`Shift-Right` moves an item. Delete removes an item. `Shift-Enter` toggles favorite state.

# Search 🔎
When entering search without a pattern it will display all emojis.

With a pattern it will show matching items in the order of their score
and select the first result.
Cursor `Shift-Left` and `Shift-Right` (or `Right` when at end) change selected result.

Enter will insert the selected item and focus the input field again.

# Requirements
- Python 3.12+
- [Noto Color Emoji](https://github.com/google/fonts/raw/refs/heads/main/ofl/notocoloremoji/NotoColorEmoji-Regular.ttf) font
- For Windows 11+ [Autohotkey v2](https://autohotkey.com/)

# Alternatives
I started to use emojis with Windows 10 but disliked the new picker from Windows
11 as it had a much smaller recent list.

Looking for alternatives I found https://github.com/gilleswaeber/emoji-keyboard
from Gilles Weber and added the recent emojis board and was very happy with it
for years.

But when switching back to linux for the desktop I could not find a proper
alternative and thus made my own one - Emoji Kbd - inspired by Gilles.

# Building

```shell
python -m venv venv
. venv/Scripts/activate
pip install -r requirements.txt
python guikbd.py # for testing
```

# Installation
## Wayland/Hyprland
I like Walker, but not the emoji picker.

In `~/.config/hypr/bindings.conf` add
```toml
unbind = SUPER, period
bindd = SUPER, period, Emojis, exec, PATHTO/wtype-emoji
```
and in `~/.config/hypr/hyprland.conf` add
```toml
windowrulev2 = float, class:^emoji-kbd$
windowrule = float, title:^Emoji Kbd$
```

## Windows
Run
```
ahk-emoji.ahk
```
It will overwrite `Win-.`, i.e. the Windows emoji picker.
If you prefer another hot key edit the script.

## Terminal
In the terminal you may also use the stripped down terminal-only version
```shell
python termkbd.py
```
or the gui
```shell
python guikbd.py
```
or the gui via daemon
```shell
python guidmn.py get
```

# Customization
Fork and change the code 😉 or wait until it is added.

# Todos
- Make size resizable
- Add config file
- Store config and other files in proper locations
- Add more layouts

# Random link list
- https://raw.githubusercontent.com/hfg-gmuend/openmoji/refs/heads/master/data/openmoji.csv
- https://www.unicode.org/Public/UCD/latest/ucd/UnicodeData.txt
- https://github.com/googlefonts/noto-emoji/issues/90?utm_source=chatgpt.com
- https://debuggerboy.com/emoji-fonts-for-alacritty-in-debian-11/
- https://github.com/alacritty/alacritty/issues/3975 wcwidth issues
