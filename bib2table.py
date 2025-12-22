from __future__ import annotations

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

_BASE_DIRECTORY = Path(__file__).parent
BIB_FILE_PATH = _BASE_DIRECTORY / "SIGNuS.bib"
OUTPUT_FILE_PATH = _BASE_DIRECTORY / "docs/_library/table.md"

# Add names to categories you would like to group into:
#     - Materials
#     - Mission Operations and Policy
MATERIALS = {
    "Beryllium",
    "Calcium",
    "Composite Moderators",
    "Magnesium Oxide",
    "Metal Hydrides",
    "Radiators",
    "Uranium Ceramics",
    "Zirconium",
}
MISSION_OPERATIONS_AND_POLICY = {"Mission Operations", "Policy"}

CUSTOM_GROUPINGS: dict[str, str] = {
    **dict.fromkeys(MATERIALS, "Materials"),
    **dict.fromkeys(MISSION_OPERATIONS_AND_POLICY, "Mission Operations & Policy"),
}


def parse_doi(
    doi: str | None,
) -> str | None:
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
    if doi is not None:
        PARSED_doi, PARSED_doi_link = parse_doi(doi)
        return f"{URL_EMOJI} [{PARSED_doi}]({PARSED_doi_link})"

    return f"{URL_EMOJI} [URL link]({uri})"


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


if __name__ == "__main__":
    # rows = []
    parsed_file = parse_file(BIB_FILE_PATH, "bibtex")

    for entry in parsed_file.entries.values():
        raw_title = entry.fields.get("title")
        raw_year = entry.fields.get("year")
        raw_url = entry.fields.get("url")
        raw_doi = entry.fields.get("doi")
        raw_groups = entry.fields.get("groups")

        title = clean_bib_title(raw_title)
        year = int(raw_year)
        link = doi_uri_to_markdown_link(raw_doi, raw_url)
        groups = parse_groups(raw_groups, CUSTOM_GROUPINGS)

    #     rows.append(
    #         {
    #             "Title": title,
    #             "Year": year,
    #             "URL or DOI link": link,
    #             "Group": groups,
    #         }
    #     )

    # df = pd.DataFrame(rows)

    # OUTPUT_FILE_PATH.write_text(df.to_markdown(index=False), encoding="utf-8")
