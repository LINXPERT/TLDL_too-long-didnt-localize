# TLDL — Too Long, Didn't Localize

Lazy solutions for game localization QA.

A small Python script that scans a game strings file (JSON, keyed by language) and flags the usual localization headaches before they ship:

- **Missing translations** — keys present in the base language but missing in another
- **Placeholder mismatches** — e.g. `{player_name}` present in English but dropped (or added) in another language
- **Length overflow** — translated text that's way longer than the source, which is a common cause of UI text getting cut off or overflowing boxes

## Why

Localization bugs are sneaky: a translator drops a `{variable}` by accident, a string balloons in length in French or German and blows out a dialogue box, or a whole key just never gets translated. TLDL catches these automatically so you don't have to eyeball every string by hand.

## Usage

```bash
python tldl.py sample_strings.json --base en --max-ratio 1.4
```

- `file` — path to your JSON strings file
- `--base` — the source/reference language code (default: `en`)
- `--max-ratio` — how much longer a translation can be than the base before it's flagged (default: `1.4`, i.e. 40% longer)

### Input format

```json
{
  "en": {
    "welcome_message": "Welcome, {player_name}!",
    "menu_start": "Start Game"
  },
  "fr": {
    "welcome_message": "Bienvenue, {player_name} !",
    "menu_start": "Commencer"
  }
}
```

### Example output

```
[1] MISSING TRANSLATIONS
  [fr] missing key: 'menu_quit'

[2] PLACEHOLDER MISMATCHES
  [fr] key 'quest_complete': missing ['{xp_amount}']

[3] LENGTH OVERFLOW (ratio > 1.4x base length)
  [fr] key 'item_sword_desc': 33 chars -> 105 chars (3.18x) -- may overflow UI

4 issue(s) found. Fix them before you ship it.
```

Exits with code `1` if any issues are found (handy for CI), `0` if everything's clean.

## Ideas for later

- Support CSV input, not just JSON
- Per-key max-length overrides (e.g. UI buttons need to be much shorter than dialogue)
- HTML report output instead of console text
