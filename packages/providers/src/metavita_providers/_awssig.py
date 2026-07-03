"""Minimal AWS Signature Version 4 signer (stdlib only — no boto3).

Enough to sign a single JSON POST to a regional service endpoint (used by the
Bedrock adapter). Implements the documented SigV4 flow: canonical request →
string-to-sign → derived signing key → Authorization header.
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hmac(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _signing_key(secret: str, date_stamp: str, region: str, service: str) -> bytes:
    k_date = _hmac(f"AWS4{secret}".encode(), date_stamp)
    k_region = _hmac(k_date, region)
    k_service = _hmac(k_region, service)
    return _hmac(k_service, "aws4_request")


def sigv4_headers(
    *,
    method: str,
    host: str,
    path: str,
    region: str,
    service: str,
    payload: bytes,
    access_key: str,
    secret_key: str,
    session_token: str | None = None,
    content_type: str = "application/json",
    now: datetime | None = None,
) -> dict[str, str]:
    """Return the headers (incl. Authorization) needed to sign the request."""
    now = now or datetime.now(UTC)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    payload_hash = _sha256(payload)

    canonical_headers = (
        f"content-type:{content_type}\n"
        f"host:{host}\n"
        f"x-amz-content-sha256:{payload_hash}\n"
        f"x-amz-date:{amz_date}\n"
    )
    signed_headers = "content-type;host;x-amz-content-sha256;x-amz-date"
    canonical_request = "\n".join(
        [method, path, "", canonical_headers, signed_headers, payload_hash]
    )

    scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = "\n".join(
        ["AWS4-HMAC-SHA256", amz_date, scope, _sha256(canonical_request.encode("utf-8"))]
    )
    signature = hmac.new(
        _signing_key(secret_key, date_stamp, region, service),
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    authorization = (
        f"AWS4-HMAC-SHA256 Credential={access_key}/{scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )
    headers = {
        "Content-Type": content_type,
        "X-Amz-Date": amz_date,
        "X-Amz-Content-Sha256": payload_hash,
        "Authorization": authorization,
    }
    if session_token:
        headers["X-Amz-Security-Token"] = session_token
    return headers
