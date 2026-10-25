#!/usr/bin/env python3
"""Embed local report screenshots into report.html without external assets.

Usage:
    python build_report.py              # update report.html in place
    python build_report.py --check      # report missing screenshot files

Screenshots belong in Final Project/report/screenshots/. A figure declares its
filename with data-screenshot="name.png". Missing files stay as explicit
[ADD SCREENSHOT] placeholders; this script never invents evidence.
"""

from __future__ import annotations

import argparse
import base64
import mimetypes
import re
from pathlib import Path


REPORT_DIR = Path(__file__).resolve().parent
REPORT_PATH = REPORT_DIR / "report.html"
SCREENSHOT_DIR = REPORT_DIR / "screenshots"
FIGURE_RE = re.compile(
    r'<figure class="evidence-placeholder" data-screenshot="(?P<name>[^"]+)">'
    r'(?P<body>.*?)</figure>',
    re.DOTALL,
)


def image_data_url(path: Path) -> str:
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def embed_screenshots(html: str, *, strict: bool = False) -> tuple[str, list[str]]:
    missing: list[str] = []

    def replace(match: re.Match[str]) -> str:
        name = match.group("name")
        path = SCREENSHOT_DIR / name
        if not path.is_file():
            missing.append(name)
            return match.group(0)
        alt = Path(name).stem.replace("-", " ")
        return (
            '<figure class="embedded-evidence">'
            f'<img src="{image_data_url(path)}" alt="{alt} screenshot">'
            f'<figcaption class="caption">{alt.capitalize()} — local screenshot embedded by build_report.py.</figcaption>'
            "</figure>"
        )

    result = FIGURE_RE.sub(replace, html)
    if strict and missing:
        raise FileNotFoundError("Missing screenshot(s): " + ", ".join(missing))
    return result, missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report missing screenshots without writing")
    args = parser.parse_args()

    source = REPORT_PATH.read_text(encoding="utf-8")
    rendered, missing = embed_screenshots(source)
    if args.check:
        if missing:
            print("Missing screenshots (placeholders retained):")
            for name in missing:
                print(f"- {name}")
        else:
            print("All declared screenshots are available.")
        return 0

    REPORT_PATH.write_text(rendered, encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    if missing:
        print("Retained explicit placeholders for: " + ", ".join(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
