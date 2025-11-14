#!/usr/bin/env python3
"""
Read a JSON file that contains \uXXXX escapes and rewrite it using UTF-8
so non-ASCII characters (e.g. Vietnamese) are preserved as readable characters.

Usage:
  python scripts/convert_unicode_json.py ../placesAPI.json

This will overwrite the input file with a pretty-printed UTF-8 encoded version.
"""
import json
import sys
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: python convert_unicode_json.py <path-to-json>")
    sys.exit(1)

path = Path(sys.argv[1])
if not path.exists():
    print(f"File not found: {path}")
    sys.exit(2)

# Read as UTF-8 (JSON parser will decode any \u escapes into characters)
text = path.read_text(encoding='utf-8')
try:
    data = json.loads(text)
except json.JSONDecodeError as e:
    print('JSON parse error:', e)
    sys.exit(3)

# Write back using ensure_ascii=False to keep non-ASCII characters
path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False), encoding='utf-8')
print(f'Overwrote {path} with UTF-8 characters (ensure_ascii=False).')
