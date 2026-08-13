#!/usr/bin/env python3
"""
TLDL - Too Long, Didn't Localize

Lazy solutions for localization QA.
Checks a game strings file (JSON) across languages for:
  - Missing translations (keys present in the base language but absent elsewhere)
  - Placeholder mismatches (e.g. {player_name} present in one language but not another)
  - Text length overflow (translated string is much longer than the base -> may not fit UI)

Usage:
    python tldl.py sample_strings.json --base en --max-ratio 1.35
"""

import json
import re
import sys
import argparse
from collections import defaultdict

PLACEHOLDER_PATTERN = re.compile(r"\{[a-zA-Z0-9_]+\}")


def load_strings(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_placeholders(text):
    return set(PLACEHOLDER_PATTERN.findall(text))


def check_missing_keys(data, base_lang):
    """Return dict: lang -> list of missing keys (present in base, absent in lang)."""
    base_keys = set(data[base_lang].keys())
    missing = defaultdict(list)
    for lang, strings in data.items():
        if lang == base_lang:
            continue
        lang_keys = set(strings.keys())
        for key in sorted(base_keys - lang_keys):
            missing[lang].append(key)
    return missing


def check_placeholder_mismatches(data, base_lang):
    """Return dict: lang -> list of (key, base_placeholders, lang_placeholders)."""
    mismatches = defaultdict(list)
    base_strings = data[base_lang]
    for lang, strings in data.items():
        if lang == base_lang:
            continue
        for key, base_text in base_strings.items():
            if key not in strings:
                continue  # already reported as missing
            base_ph = get_placeholders(base_text)
            lang_ph = get_placeholders(strings[key])
            if base_ph != lang_ph:
                mismatches[lang].append((key, base_ph, lang_ph))
    return mismatches


def check_length_overflow(data, base_lang, max_ratio):
    """Return dict: lang -> list of (key, base_len, lang_len, ratio)."""
    overflow = defaultdict(list)
    base_strings = data[base_lang]
    for lang, strings in data.items():
        if lang == base_lang:
            continue
        for key, base_text in base_strings.items():
            if key not in strings:
                continue
            base_len = len(base_text)
            lang_len = len(strings[key])
            if base_len == 0:
                continue
            ratio = lang_len / base_len
            if ratio > max_ratio:
                overflow[lang].append((key, base_len, lang_len, round(ratio, 2)))
    return overflow


def print_report(missing, mismatches, overflow, max_ratio):
    total_issues = 0

    print("=" * 60)
    print("LOCALIZATION CHECK REPORT")
    print("=" * 60)

    print("\n[1] MISSING TRANSLATIONS")
    if not any(missing.values()):
        print("  None found. Nice.")
    else:
        for lang, keys in missing.items():
            for key in keys:
                print(f"  [{lang}] missing key: '{key}'")
                total_issues += 1

    print("\n[2] PLACEHOLDER MISMATCHES")
    if not any(mismatches.values()):
        print("  None found. Nice.")
    else:
        for lang, items in mismatches.items():
            for key, base_ph, lang_ph in items:
                missing_ph = base_ph - lang_ph
                extra_ph = lang_ph - base_ph
                detail = []
                if missing_ph:
                    detail.append(f"missing {sorted(missing_ph)}")
                if extra_ph:
                    detail.append(f"unexpected {sorted(extra_ph)}")
                print(f"  [{lang}] key '{key}': {', '.join(detail)}")
                total_issues += 1

    print(f"\n[3] LENGTH OVERFLOW (ratio > {max_ratio}x base length)")
    if not any(overflow.values()):
        print("  None found. Nice.")
    else:
        for lang, items in overflow.items():
            for key, base_len, lang_len, ratio in items:
                print(f"  [{lang}] key '{key}': {base_len} chars -> {lang_len} chars ({ratio}x) -- may overflow UI")
                total_issues += 1

    print("\n" + "=" * 60)
    if total_issues == 0:
        print("All clear. Ship it.")
    else:
        print(f"{total_issues} issue(s) found. Fix them before you ship it.")
    print("=" * 60)

    return total_issues


def main():
    parser = argparse.ArgumentParser(description="TLDL - Too Long, Didn't Localize. Checks game localization strings for common issues.")
    parser.add_argument("file", help="Path to JSON file of localized strings (lang -> {key: text})")
    parser.add_argument("--base", default="en", help="Base/source language code (default: en)")
    parser.add_argument("--max-ratio", type=float, default=1.4,
                         help="Max allowed length ratio (translated/base) before flagging overflow (default: 1.4)")
    args = parser.parse_args()

    try:
        data = load_strings(args.file)
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {args.file}: {e}")
        sys.exit(1)

    if args.base not in data:
        print(f"Error: base language '{args.base}' not found in file. Available: {list(data.keys())}")
        sys.exit(1)

    missing = check_missing_keys(data, args.base)
    mismatches = check_placeholder_mismatches(data, args.base)
    overflow = check_length_overflow(data, args.base, args.max_ratio)

    total_issues = print_report(missing, mismatches, overflow, args.max_ratio)

    sys.exit(1 if total_issues > 0 else 0)


if __name__ == "__main__":
    main()
