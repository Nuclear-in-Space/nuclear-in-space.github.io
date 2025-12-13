import re
from pathlib import Path

import pandas as pd
from pybtex.backends.plaintext import Backend
from pybtex.database import parse_file
from pybtex.richtext import Text


def parse_doi(doi: str | None) -> str | None:
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


def clean_bib_title(title: str) -> str:
    latex_text = Text.from_latex(title)
    return latex_text.render(Backend())


def doi_uri_to_markdown_link(doi: str | None, uri: str | None) -> str:
    if doi is not None:
        PARSED_doi, PARSED_doi_link = parse_doi(doi)
        return f"\U0001f310 [{PARSED_doi}]({PARSED_doi_link})"

    return f"\U0001f310 [URL link]({uri})"


BIB_FILE_PATH = Path("SIGNuS.bib").resolve()
OUTPUT_FILE_PATH = Path("docs/_library/table.md").resolve()
PARSED = parse_file(BIB_FILE_PATH, "bibtex")

ROWS = []

for entry in PARSED.entries.values():
    raw_title = entry.fields.get("title")
    raw_year = entry.fields.get("year")
    raw_url = entry.fields.get("url")
    raw_doi = entry.fields.get("doi")
    raw_groups = entry.fields.get("groups")

    fixed_title = clean_bib_title(raw_title)
    fixed_year = int(raw_year)
    fixed_link = doi_uri_to_markdown_link(raw_doi, raw_url)
    fixed_groups = re.sub(r"\s*(>|,)\s*", r"\1", raw_groups)

    ROWS.append(
        {
            "Title": fixed_title,
            "Year": fixed_year,
            "URL or DOI link": fixed_link,
            "Group": fixed_groups,
        }
    )

df = pd.DataFrame(ROWS)

OUTPUT_FILE_PATH.write_text(df.to_markdown(index=False), encoding="utf-8")
