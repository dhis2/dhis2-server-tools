#!/usr/bin/env python3
"""Scan-and-forward gateway for DHIS2 file uploads.

POST/PUT bodies are spooled and scanned via clamd's unix socket.
multipart/form-data file parts are extracted and scanned as raw bytes so
file-hash signatures (including EICAR) match; the original request is
forwarded unchanged so DHIS2's MD5 still matches. Non-mutating
methods on the same URLs are proxied with no scan. The reverse proxy
overwrites X-DHIS2-Upstream; this process only connects to allowlisted
instance addresses.
"""

from __future__ import annotations

import http.client
import json
import os
import socket
import struct
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Iterable
from urllib.parse import urlsplit

HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "proxy-connection",
}

SCAN_METHODS = {"POST", "PUT"}
DEFAULT_MAX_BODY = 104857600
DEFAULT_SCAN_TIMEOUT = 120.0
DEFAULT_FORWARD_TIMEOUT = 300.0
SIGNATURE_FILES = (
    "daily.cvd",
    "daily.cld",
    "main.cvd",
    "main.cld",
    "bytecode.cvd",
    "bytecode.cld",
)


class ScannerDown(Exception):
    """clamd is unreachable or returned an error."""


class Infected(Exception):
    def __init__(self, signature: str) -> None:
        super().__init__(signature)
        self.signature = signature


@dataclass
class GatewayConfig:
    listen_host: str = "0.0.0.0"
    listen_port: int = 8081
    clamd_socket: str = "/var/run/clamav/clamd.ctl"
    spool_dir: str = "/var/spool/clamav-gateway"
    fail_open: bool = False
    upstreams: frozenset[str] = field(default_factory=frozenset)
    max_body: int = DEFAULT_MAX_BODY
    db_dir: str = "/var/lib/clamav"
    scan_timeout: float = DEFAULT_SCAN_TIMEOUT
    forward_timeout: float = DEFAULT_FORWARD_TIMEOUT


@dataclass
class Metrics:
    scans: int = 0
    infected: int = 0
    scan_seconds_sum: float = 0.0
    lock: threading.Lock = field(default_factory=threading.Lock)

    def record_scan(self, duration: float, infected: bool) -> None:
        with self.lock:
            self.scans += 1
            self.scan_seconds_sum += duration
            if infected:
                self.infected += 1


def config_from_env(env: dict[str, str] | None = None) -> GatewayConfig:
    src = env if env is not None else os.environ
    raw_upstreams = src.get("CLAMAV_UPSTREAMS", "")
    upstreams = frozenset(
        part.strip() for part in raw_upstreams.split(",") if part.strip()
    )
    return GatewayConfig(
        listen_host=src.get("CLAMAV_LISTEN_HOST", "0.0.0.0"),
        listen_port=int(src.get("CLAMAV_LISTEN_PORT", "8081")),
        clamd_socket=src.get("CLAMAV_SOCKET", "/var/run/clamav/clamd.ctl"),
        spool_dir=src.get("CLAMAV_SPOOL_DIR", "/var/spool/clamav-gateway"),
        fail_open=src.get("CLAMAV_FAIL_OPEN", "false").lower() in ("1", "true", "yes"),
        upstreams=upstreams,
        max_body=int(src.get("CLAMAV_MAX_BODY", str(DEFAULT_MAX_BODY))),
        db_dir=src.get("CLAMAV_DB_DIR", "/var/lib/clamav"),
        scan_timeout=float(src.get("CLAMAV_SCAN_TIMEOUT", str(DEFAULT_SCAN_TIMEOUT))),
        forward_timeout=float(
            src.get("CLAMAV_FORWARD_TIMEOUT", str(DEFAULT_FORWARD_TIMEOUT))
        ),
    )


def parse_upstream_header(value: str | None) -> str | None:
    """Return host:port from X-DHIS2-Upstream, or None if missing/unusable."""
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    if "://" not in raw:
        raw = "http://" + raw
    parts = urlsplit(raw)
    if not parts.hostname:
        return None
    port = parts.port or (443 if parts.scheme == "https" else 80)
    host = parts.hostname
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    return f"{host}:{port}"


def allowlisted(upstream: str | None, allowed: Iterable[str]) -> bool:
    if not upstream:
        return False
    return upstream in set(allowed)


def copy_limited(reader, handle, remaining: int, chunk_size: int = 65536) -> int:
    while remaining > 0:
        chunk = reader.read(min(chunk_size, remaining))
        if not chunk:
            break
        handle.write(chunk)
        remaining -= len(chunk)
    return remaining


def _clamd_session(socket_path: str, timeout: float) -> socket.socket:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(socket_path)
    except OSError:
        sock.close()
        raise
    return sock


def _recv_all(sock: socket.socket, limit: int = 65536) -> bytes:
    chunks = []
    received = 0
    while received < limit:
        data = sock.recv(4096)
        if not data:
            break
        chunks.append(data)
        received += len(data)
        if data.endswith(b"\x00") or data.endswith(b"\n"):
            break
    return b"".join(chunks)


def clamd_ping(socket_path: str, timeout: float = 5.0) -> bool:
    try:
        sock = _clamd_session(socket_path, timeout)
    except OSError:
        return False
    try:
        sock.sendall(b"zPING\0")
        reply = _recv_all(sock).decode("utf-8", "replace")
        return "PONG" in reply
    except OSError:
        return False
    finally:
        sock.close()


def _parse_scan_reply(reply: str) -> None:
    text = reply.strip().rstrip("\x00")
    if text.endswith("OK") and "FOUND" not in text:
        return
    if "FOUND" in text:
        # /path: Eicar-Signature FOUND
        signature = text.rsplit("FOUND", 1)[0].split(":", 1)[-1].strip()
        raise Infected(signature or "unknown")
    raise ScannerDown(text or "empty clamd reply")


def clamd_scan_path(socket_path: str, path: str, timeout: float) -> None:
    sock = _clamd_session(socket_path, timeout)
    try:
        sock.sendall(b"zSCAN " + path.encode("utf-8", "surrogateescape") + b"\0")
        reply = _recv_all(sock).decode("utf-8", "replace")
        if "Access denied" in reply or "lstat() failed" in reply:
            raise PermissionError(reply)
        _parse_scan_reply(reply)
    finally:
        sock.close()


def clamd_instream(socket_path: str, path: str, timeout: float) -> None:
    sock = _clamd_session(socket_path, timeout)
    try:
        sock.sendall(b"zINSTREAM\0")
        with open(path, "rb") as handle:
            while True:
                chunk = handle.read(8192)
                if not chunk:
                    break
                sock.sendall(struct.pack(">I", len(chunk)) + chunk)
        sock.sendall(struct.pack(">I", 0))
        reply = _recv_all(sock).decode("utf-8", "replace")
        _parse_scan_reply(reply)
    finally:
        sock.close()


def scan_spool(socket_path: str, path: str, timeout: float) -> None:
    try:
        clamd_scan_path(socket_path, path, timeout)
    except PermissionError:
        clamd_instream(socket_path, path, timeout)


def _header_boundary(content_type: str | None) -> str | None:
    if not content_type:
        return None
    for item in content_type.split(";"):
        item = item.strip()
        if item.lower().startswith("boundary="):
            value = item.split("=", 1)[1].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            return value or None
    return None


def multipart_filename_bodies(data: bytes, content_type: str | None) -> list[bytes]:
    """Return file-part payloads from multipart/form-data, else []."""
    ctype = (content_type or "").split(";", 1)[0].strip().lower()
    boundary = _header_boundary(content_type)
    if ctype != "multipart/form-data" or not boundary:
        return []
    delim = b"--" + boundary.encode("ascii", "surrogateescape")
    bodies: list[bytes] = []
    for chunk in data.split(delim)[1:]:
        if chunk.startswith(b"--"):
            break
        if chunk.startswith(b"\r\n"):
            chunk = chunk[2:]
        elif chunk.startswith(b"\n"):
            chunk = chunk[1:]
        header_end = chunk.find(b"\r\n\r\n")
        sep = 4
        if header_end < 0:
            header_end = chunk.find(b"\n\n")
            sep = 2
        if header_end < 0:
            continue
        headers = chunk[:header_end].decode("latin-1", "replace").lower()
        body = chunk[header_end + sep :]
        if body.endswith(b"\r\n"):
            body = body[:-2]
        elif body.endswith(b"\n"):
            body = body[:-1]
        if "content-disposition:" in headers and "filename=" in headers:
            bodies.append(body)
    return bodies


def write_scan_copy(spool_dir: str, data: bytes) -> str:
    fd, path = tempfile.mkstemp(prefix="part-", dir=spool_dir)
    try:
        os.fchmod(fd, 0o640)
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        os.unlink(path)
        raise
    return path


def signature_age_seconds(db_dir: str, now: float | None = None) -> float:
    newest = None
    for name in SIGNATURE_FILES:
        candidate = os.path.join(db_dir, name)
        try:
            mtime = os.path.getmtime(candidate)
        except OSError:
            continue
        if newest is None or mtime > newest:
            newest = mtime
    if newest is None:
        return -1.0
    return max(0.0, (now if now is not None else time.time()) - newest)


def render_metrics(metrics: Metrics, config: GatewayConfig) -> str:
    clamd_up = 1 if clamd_ping(config.clamd_socket) else 0
    age = signature_age_seconds(config.db_dir)
    with metrics.lock:
        scans = metrics.scans
        infected = metrics.infected
        duration_sum = metrics.scan_seconds_sum
    lines = [
        "# HELP clamav_scans_total Uploads submitted to clamd",
        "# TYPE clamav_scans_total counter",
        f"clamav_scans_total {scans}",
        "# HELP clamav_infected_total Uploads that matched a signature",
        "# TYPE clamav_infected_total counter",
        f"clamav_infected_total {infected}",
        "# HELP clamav_scan_duration_seconds Time spent in clamd SCAN/INSTREAM",
        "# TYPE clamav_scan_duration_seconds summary",
        f"clamav_scan_duration_seconds_sum {duration_sum:.6f}",
        f"clamav_scan_duration_seconds_count {scans}",
        "# HELP clamav_signature_age_seconds Age of the newest official CVD/CLD",
        "# TYPE clamav_signature_age_seconds gauge",
        f"clamav_signature_age_seconds {age:.0f}",
        "# HELP clamav_clamd_up Whether clamd answered PING",
        "# TYPE clamav_clamd_up gauge",
        f"clamav_clamd_up {clamd_up}",
        "",
    ]
    return "\n".join(lines)


def _filter_request_headers(headers) -> list[tuple[str, str]]:
    forwarded = []
    for key, value in headers.items():
        if key.lower() in HOP_BY_HOP:
            continue
        if key.lower() == "x-dhis2-upstream":
            continue
        forwarded.append((key, value))
    return forwarded


def _filter_response_headers(headers) -> list[tuple[str, str]]:
    return [
        (key, value)
        for key, value in headers.items()
        if key.lower() not in HOP_BY_HOP
    ]


def forward_request(
    config: GatewayConfig,
    method: str,
    path: str,
    headers,
    body_path: str | None,
) -> tuple[int, list[tuple[str, str]], bytes]:
    upstream = parse_upstream_header(headers.get("X-DHIS2-Upstream"))
    if not allowlisted(upstream, config.upstreams):
        return 502, [("Content-Type", "application/json")], json.dumps(
            {"error": "invalid_upstream"}
        ).encode()

    host, port_s = upstream.rsplit(":", 1)
    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]
    port = int(port_s)
    fwd_headers = _filter_request_headers(headers)
    body_file = None
    if body_path is not None:
        size = os.path.getsize(body_path)
        body_file = open(body_path, "rb")
        fwd_headers = [
            (key, value)
            for key, value in fwd_headers
            if key.lower() != "content-length"
        ]
        fwd_headers.append(("Content-Length", str(size)))

    conn = http.client.HTTPConnection(host, port, timeout=config.forward_timeout)
    try:
        conn.request(method, path, body=body_file, headers=dict(fwd_headers))
        response = conn.getresponse()
        payload = response.read()
        return response.status, _filter_response_headers(response.headers), payload
    finally:
        if body_file is not None:
            body_file.close()
        conn.close()


def make_handler(config: GatewayConfig, metrics: Metrics):
    class GatewayHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt: str, *args) -> None:
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

        def _write(self, status: int, headers: list[tuple[str, str]], body: bytes) -> None:
            self.send_response(status)
            has_length = False
            for key, value in headers:
                if key.lower() == "content-length":
                    has_length = True
                self.send_header(key, value)
            if not has_length:
                self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _json(self, status: int, payload: dict) -> None:
            body = json.dumps(payload).encode()
            self._write(status, [("Content-Type", "application/json")], body)

        def _full_path(self) -> str:
            return self.path

        def do_GET(self) -> None:  # noqa: N802
            if self.path.split("?", 1)[0] == "/healthz":
                if clamd_ping(config.clamd_socket):
                    self._write(200, [("Content-Type", "text/plain")], b"ok\n")
                else:
                    self._json(503, {"error": "scanner_unavailable"})
                return
            if self.path.split("?", 1)[0] == "/metrics":
                body = render_metrics(metrics, config).encode()
                self._write(200, [("Content-Type", "text/plain; version=0.0.4")], body)
                return
            self._proxy(scan=False)

        def do_HEAD(self) -> None:  # noqa: N802
            self._proxy(scan=False)

        def do_POST(self) -> None:  # noqa: N802
            self._proxy(scan=True)

        def do_PUT(self) -> None:  # noqa: N802
            self._proxy(scan=True)

        def do_DELETE(self) -> None:  # noqa: N802
            self._proxy(scan=False)

        def do_OPTIONS(self) -> None:  # noqa: N802
            self._proxy(scan=False)

        def do_PATCH(self) -> None:  # noqa: N802
            self._proxy(scan=False)

        def _spool_body(self) -> str | None:
            length_s = self.headers.get("Content-Length")
            if length_s is None:
                return None
            try:
                length = int(length_s)
            except ValueError as exc:
                raise ValueError("invalid_content_length") from exc
            if length < 0:
                raise ValueError("invalid_content_length")
            if length > config.max_body:
                raise ValueError("body_too_large")
            fd, path = tempfile.mkstemp(prefix="scan-", dir=config.spool_dir)
            try:
                os.fchmod(fd, 0o640)
                with os.fdopen(fd, "wb") as handle:
                    leftover = copy_limited(self.rfile, handle, length)
            except Exception:
                try:
                    os.close(fd)
                except OSError:
                    pass
                os.unlink(path)
                raise
            if leftover:
                os.unlink(path)
                raise ValueError("incomplete_body")
            return path

        def _proxy(self, scan: bool) -> None:
            method = self.command
            should_scan = scan and method in SCAN_METHODS
            spool = None
            part_paths: list[str] = []
            try:
                if should_scan or (self.headers.get("Content-Length") and method in SCAN_METHODS):
                    try:
                        spool = self._spool_body()
                    except ValueError as exc:
                        if str(exc) == "body_too_large":
                            self._json(413, {"error": "body_too_large"})
                        else:
                            self._json(400, {"error": str(exc)})
                        return
                if should_scan:
                    if spool is None:
                        self._json(400, {"error": "missing_body"})
                        return
                    with open(spool, "rb") as handle:
                        spool_bytes = handle.read()
                    parts = multipart_filename_bodies(
                        spool_bytes, self.headers.get("Content-Type")
                    )
                    scan_paths = [spool]
                    if parts:
                        part_paths = [
                            write_scan_copy(config.spool_dir, part) for part in parts
                        ]
                        scan_paths = part_paths
                    started = time.monotonic()
                    try:
                        for scan_path in scan_paths:
                            scan_spool(
                                config.clamd_socket, scan_path, config.scan_timeout
                            )
                    except Infected as exc:
                        metrics.record_scan(time.monotonic() - started, True)
                        self._json(
                            403,
                            {"error": "malware_detected", "signature": exc.signature},
                        )
                        return
                    except (ScannerDown, OSError, TimeoutError):
                        metrics.record_scan(time.monotonic() - started, False)
                        if config.fail_open:
                            pass
                        else:
                            self._json(503, {"error": "scanner_unavailable"})
                            return
                    else:
                        metrics.record_scan(time.monotonic() - started, False)

                status, headers, body = forward_request(
                    config, method, self._full_path(), self.headers, spool
                )
                self._write(status, headers, body)
            finally:
                for part_path in part_paths:
                    try:
                        os.unlink(part_path)
                    except OSError:
                        pass
                if spool is not None:
                    try:
                        os.unlink(spool)
                    except OSError:
                        pass

    return GatewayHandler


def serve(config: GatewayConfig | None = None) -> None:
    cfg = config or config_from_env()
    os.makedirs(cfg.spool_dir, exist_ok=True)
    metrics = Metrics()
    handler = make_handler(cfg, metrics)
    server = ThreadingHTTPServer((cfg.listen_host, cfg.listen_port), handler)
    server.serve_forever()


if __name__ == "__main__":
    serve()
