from __future__ import annotations

import argparse
import string
import tomllib
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from pybtex.backends.plaintext import Backend
from pybtex.database import parse_file
from pybtex.richtext import Text

if TYPE_CHECKING:
    from collections.abc import Mapping

# Unicode string for a globe emoji
URL_EMOJI = "\U0001f310"


def parse_args() -> argparse.Namespace:
    _base_dir = Path(__file__).parent

    parser = argparse.ArgumentParser(description="Convert a BibTeX file into markdown tables!")
    parser.add_argument(
        "--bib",
        type=Path,
        required=False,
        default=_base_dir / "SIGNuS.bib",
        help="Path to the .bib file"
    )
    parser.add_argument(
        "--groupings",
        type=Path,
        required=False,
        default=_base_dir / "tag-groups.toml",
        help="Path to the .toml file containing custom groupings"
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=False,
        default=_base_dir / "docs/_hidden_tables/",
        help="Folder to write tables to"
    )
    return parser.parse_args()

def load_custom_groupings(filepath: str | Path) -> dict[str,str]:
    with open(filepath, "rb") as file:
        data = tomllib.load(file)

    groupings = {}

    for category in data["categories"].values():
        for tag in category["tags"]:
            if tag in groupings:
                msg = f"Tag {tag!r} is in both {groupings[tag]!r} and {category['name']!r}"
                raise ValueError(msg)
            groupings[tag] = category["name"]

    return groupings


def format_filename(
    input: str,
) -> str:
    valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
    filename = "".join(c for c in input if c in valid_chars)
    filename = filename.replace(" ", "_").lower()  # I don't like spaces in filenames.
    return filename.replace("__", "_")


def parse_doi(
    doi: str | None,
) -> tuple[str, str] | None:
    """
    Converts a DOI input (bare DOI or full URL) into a standardized DOI and URL.

    Parameters
    ----------
    doi : str | None
        A DOI string or web URL.

    Returns
    -------
        If there is no string, returns None. If a string or URL present, ensures a tuple
        containing the raw doi string and the url link is output.
    """
    link_prefix = "https://doi.org/"

    if doi is None:
        return None

    # Strip whitespace
    doi = doi.strip()

    # If it a website link, then just return the https:// link for it
    if doi.startswith(("http://", "https://")):
        doi_link = doi.replace("http://", "https://", 1)
    else:
        doi_link = f"{link_prefix}{doi}"

    raw_doi = doi_link[len(link_prefix) :]

    return raw_doi, doi_link


def clean_bib_title(
    title: str,
) -> str:
    latex_text = Text.from_latex(title)
    return latex_text.render(Backend())


def doi_uri_to_markdown_link(
    doi: str | None,
    uri: str | None,
) -> str:
    if doi and doi.strip():
        parsed_doi, parsed_doi_link = parse_doi(doi)
        return f"{URL_EMOJI} [{parsed_doi}]({parsed_doi_link})"
    if uri and uri.strip():
        return f"{URL_EMOJI} [URL link]({uri})"
    return "N/A"


def parse_groups(
    groups: str,
    custom_groupings: Mapping[str, str],
) -> dict[str, str]:
    if not groups:
        return {}

    result: dict[str, list[str]] = defaultdict(list)

    for raw_item in groups.split(","):
        item = raw_item.strip()
        if not item:
            continue

        raw_category, _, raw_tag = item.partition(">")
        category = raw_category.strip()
        tag = raw_tag.strip()

        if grouped_category := custom_groupings.get(category):
            result[grouped_category].append(category)
        elif tag:
            result[category].append(tag)
        else:
            result.setdefault(category, [])

    return dict(result)

def main():
    io_paths = parse_args()
    io_paths.output.mkdir(parents=True, exist_ok=True)

    bib_file_path = io_paths.bib
    custom_groupings = load_custom_groupings(io_paths.groupings)

    parsed_file = parse_file(bib_file_path, "bibtex")
    rows_by_category = defaultdict(list)

    for entry in parsed_file.entries.values():
        fields = entry.fields

        raw_title = fields.get("title")
        raw_year = fields.get("year")

        title = clean_bib_title(raw_title)
        year = int(raw_year) if raw_year.isdigit() else None
        link = doi_uri_to_markdown_link(fields.get("doi"), fields.get("url"))
        groups = parse_groups(fields.get("groups"), custom_groupings)

        for category, tags in groups.items():
            rows_by_category[category].append(
                {
                    "Title": title,
                    "Year": year,
                    "URL or DOI link": link,
                    "Tags": ", ".join(tags),
                }
            )

    for category, rows in rows_by_category.items():
        df = pd.DataFrame.from_records(rows)

        df["Year"] = df["Year"].astype("Int64")
        df = df.sort_values(
            by=["Year"],
            ascending=[False],
            na_position="last",
        )
        df["Year"] = df["Year"].astype("string").fillna("")

        output_file_path = io_paths.output / f"{format_filename(category)}.md"
        output_file_path.write_text(df.to_markdown(index=False), encoding="utf-8")


if __name__ == "__main__":
    main()
