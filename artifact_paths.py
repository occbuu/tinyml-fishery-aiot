"""Keep generated LaTeX fragments outside the two-file submission directory."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ASSETS=ROOT/'results/manuscript_assets'
(ASSETS/'tables').mkdir(parents=True,exist_ok=True)
