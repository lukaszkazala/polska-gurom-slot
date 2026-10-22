"""Download an immutable, unmodified subset of the official Stake math SDK."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
API = "https://api.github.com/repos/engineio/math-sdk/commits/main"
FILES = (
    "utils/rgs_verification.py",
    "utils/analysis/distribution_functions.py",
    "src/write_data/write_data.py",
    "LICENSE",
)


def get(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "Polska-Gurom-local-math-audit/0.4"})
    with urlopen(request, timeout=45) as response:
        return response.read()


def main() -> None:
    commit = json.loads(get(API))
    sha = commit["sha"]
    if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
        raise ValueError("Unexpected GitHub commit SHA")
    manifest = {
        "repository": "https://github.com/engineio/math-sdk",
        "resolved_ref": "main",
        "commit_sha": sha,
        "commit_url": commit["html_url"],
        "commit_time": commit["commit"]["committer"]["date"],
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "code_modified": False,
        "files": [],
    }
    for relative in FILES:
        url = f"https://raw.githubusercontent.com/engineio/math-sdk/{sha}/{relative}"
        data = get(url)
        destination = HERE / "vendor" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        manifest["files"].append({
            "path": "vendor/" + relative,
            "source_url": url,
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
        })
    (HERE / "source_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"commit_sha": sha, "files": len(FILES)}))


if __name__ == "__main__":
    main()
