from pathlib import Path

import pandas as pd
from pybtex.database import parse_file

file_path = Path("SIGNuS.bib").resolve()
parsed = parse_file(file_path, "bibtex")

for entry in parsed.entries.values():
    print(entry.fields.get("url"))
