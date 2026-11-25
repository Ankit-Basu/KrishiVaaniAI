"""Quick end-to-end check of a running KrishiVaani server.

Usage:
    python scripts/smoke_test.py                       # http://localhost:5000
    python scripts/smoke_test.py https://you.hf.space  # deployed app
    python scripts/smoke_test.py URL path/to/leaf.jpg  # also test /api/analyze
"""
import sys

import requests

base = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000").rstrip("/")
leaf = sys.argv[2] if len(sys.argv) > 2 else None


def check(name, resp):
    ok = resp.ok
    print(f"[{'OK ' if ok else 'ERR'}] {name}: HTTP {resp.status_code} {resp.text[:160]!r}")
    return ok


results = [
    check("health", requests.get(f"{base}/healthz", timeout=30)),
    check("weather", requests.get(f"{base}/api/weather", params={"city": "Delhi"}, timeout=30)),
    check("mandi", requests.get(f"{base}/api/mandi", params={"market": "DELHI", "commodity": "Wheat"}, timeout=30)),
    check("chat", requests.post(f"{base}/api/chat", json={"query": "hello", "lang": "en"}, timeout=60)),
]
if leaf:
    with open(leaf, "rb") as f:
        results.append(check("analyze", requests.post(f"{base}/api/analyze", files={"image": f}, timeout=60)))

sys.exit(0 if all(results) else 1)
