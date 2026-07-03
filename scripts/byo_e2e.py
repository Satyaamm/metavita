#!/usr/bin/env python3
"""End-to-end BYO smoke against a running MetaVita API.

Proves the pure bring-your-own loop with YOUR real keys:
  add connections (embeddings + LLM) → upload a doc → ask a question → grounded answer.

Prereqs:
  1. Stack running:  ./run.sh        (API on http://localhost:8000)
  2. Export your keys:
       export OPENAI_API_KEY=sk-...        # embeddings (+ chat if --llm openai)
       export ANTHROPIC_API_KEY=sk-ant-... # chat (default --llm anthropic)

Run:
  python scripts/byo_e2e.py
  python scripts/byo_e2e.py --llm openai --base http://localhost:8000
"""

from __future__ import annotations

import argparse
import os
import sys
import urllib.request
import json
import io

DOC = (
    "MetaVita is a bring-your-own agentic RAG platform. Users connect their own "
    "LLMs, embedding models, and vector databases. The capital of the demo corpus is Lyra."
)


def _req(method: str, url: str, *, json_body=None, files=None, headers=None):
    headers = dict(headers or {})
    data = None
    if files is not None:
        boundary = "----metavitae2e"
        body = io.BytesIO()
        for name, (fn, content, ctype) in files.items():
            body.write(f"--{boundary}\r\n".encode())
            body.write(
                f'Content-Disposition: form-data; name="{name}"; filename="{fn}"\r\n'.encode()
            )
            body.write(f"Content-Type: {ctype}\r\n\r\n".encode())
            body.write(content if isinstance(content, bytes) else content.encode())
            body.write(b"\r\n")
        body.write(f"--{boundary}--\r\n".encode())
        data = body.getvalue()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif json_body is not None:
        data = json.dumps(json_body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--llm", choices=["anthropic", "openai"], default="anthropic")
    args = ap.parse_args()
    base = args.base.rstrip("/")

    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        print("✗ OPENAI_API_KEY is required (embeddings).", file=sys.stderr)
        return 1
    llm_key = openai_key if args.llm == "openai" else os.environ.get("ANTHROPIC_API_KEY")
    if not llm_key:
        print(f"✗ A key for --llm {args.llm} is required.", file=sys.stderr)
        return 1

    print(f"▸ Adding embeddings connection (openai) …")
    st, _ = _req("POST", f"{base}/connections", json_body={
        "name": "E2E Embeddings", "capability": "embeddings", "provider": "openai",
        "values": {"api_key": openai_key, "model": "text-embedding-3-small"},
    })
    assert st == 201, f"embeddings connection failed: {st}"

    print(f"▸ Adding LLM connection ({args.llm}) …")
    llm_vals = ({"api_key": llm_key, "model": "gpt-4o"} if args.llm == "openai"
                else {"api_key": llm_key, "model": "claude-opus-4-8"})
    st, _ = _req("POST", f"{base}/connections", json_body={
        "name": "E2E LLM", "capability": "llm", "provider": args.llm, "values": llm_vals,
    })
    assert st == 201, f"llm connection failed: {st}"

    print("▸ Uploading a document …")
    st, ing = _req("POST", f"{base}/ingest", files={"file": ("demo.txt", DOC, "text/plain")})
    assert st in (200, 201), f"ingest failed: {st} {ing}"
    print(f"  indexed {ing.get('chunks')} chunk(s) into the vector store")

    print("▸ Asking a grounded question …")
    st, ans = _req("POST", f"{base}/query", json_body={"question": "What is the capital of the demo corpus?", "k": 3})
    assert st == 200, f"query failed: {st} {ans}"
    print("\n=== ANSWER ===")
    print(ans.get("answer"))
    print("=== CITATIONS ===", [c.get("snippet", "")[:60] for c in ans.get("citations", [])])
    print("\n✓ Pure-BYO end-to-end worked: your keys + your vector store produced a grounded answer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
