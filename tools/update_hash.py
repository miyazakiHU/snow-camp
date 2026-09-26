"""Update the exact game.js digest in both CSP and Subresource Integrity."""
from pathlib import Path
import base64
import hashlib
import re

root = Path(__file__).resolve().parents[1]
js = (root / "game.js").read_bytes()
html_path = root / "index.html"
html = html_path.read_text(encoding="utf-8")
digest = base64.b64encode(hashlib.sha256(js).digest()).decode("ascii")
html, csp_count = re.subn(
    r"script-src 'sha256-[A-Za-z0-9+/=]+'",
    "script-src 'sha256-" + digest + "'",
    html,
)
html, sri_count = re.subn(
    r'integrity="sha256-[A-Za-z0-9+/=]+"',
    'integrity="sha256-' + digest + '"',
    html,
)
if csp_count != 1 or sri_count != 1:
    raise SystemExit("Expected exactly one script CSP hash and one SRI hash; no file was written.")
html_path.write_text(html, encoding="utf-8", newline="\n")
print("Updated CSP and SRI: sha256-" + digest)
