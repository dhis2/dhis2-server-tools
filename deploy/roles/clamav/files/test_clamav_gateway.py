"""Gateway unit tests with a mock unix-socket clamd. No CVD download."""

from __future__ import annotations

import os
import socket
import struct
import sys
import tempfile
import threading
import time
import unittest
from http.client import HTTPConnection
from pathlib import Path

_FILES_DIR = str(Path(__file__).resolve().parent)
if _FILES_DIR not in sys.path:
    sys.path.insert(0, _FILES_DIR)

import clamav_gateway as gw  # noqa: E402

EICAR = (
    "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
)


class MockClamd(threading.Thread):
    def __init__(self, socket_path: str) -> None:
        super().__init__(daemon=True)
        self.socket_path = socket_path
        self._stop = threading.Event()
        self.down = False
        self._server: socket.socket | None = None

    def run(self) -> None:
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._server = server
        server.bind(self.socket_path)
        server.listen(8)
        server.settimeout(0.2)
        while not self._stop.is_set():
            try:
                conn, _ = server.accept()
            except socket.timeout:
                continue
            with conn:
                if self.down:
                    continue
                self._handle(conn)

    def _handle(self, conn: socket.socket) -> None:
        conn.settimeout(2)
        header = b""
        while not header.endswith(b"\n") and not header.endswith(b"\0"):
            chunk = conn.recv(1)
            if not chunk:
                return
            header += chunk
        command = header.decode("utf-8", "replace").strip("\n\0")
        if command.startswith("n") or command.startswith("z"):
            command = command[1:]
        if command == "PING":
            conn.sendall(b"PONG\n")
            return
        if command.startswith("SCAN "):
            path = command.split(" ", 1)[1]
            payload = Path(path).read_bytes()
            conn.sendall(self._verdict(path, payload))
            return
        if command == "INSTREAM":
            data = bytearray()
            while True:
                size_raw = b""
                while len(size_raw) < 4:
                    piece = conn.recv(4 - len(size_raw))
                    if not piece:
                        return
                    size_raw += piece
                size = struct.unpack(">I", size_raw)[0]
                if size == 0:
                    break
                remaining = size
                while remaining:
                    piece = conn.recv(min(8192, remaining))
                    if not piece:
                        return
                    data.extend(piece)
                    remaining -= len(piece)
            conn.sendall(self._verdict("stream", bytes(data)))

    def _verdict(self, label: str, payload: bytes) -> bytes:
        # Match real clamd: EICAR is a whole-file signature, not a substring.
        if payload == EICAR.encode():
            return f"{label}: Eicar-Signature FOUND\n".encode()
        return f"{label}: OK\n".encode()

    def stop(self) -> None:
        self._stop.set()
        if self._server is not None:
            try:
                self._server.close()
            except OSError:
                pass
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)


class MockUpstream(threading.Thread):
    def __init__(self, host: str, port: int) -> None:
        super().__init__(daemon=True)
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        self.requests: list[dict] = []
        parent = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt: str, *args) -> None:
                return

            def _capture(self) -> None:
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                parent.requests.append(
                    {
                        "method": self.command,
                        "path": self.path,
                        "headers": {k.lower(): v for k, v in self.headers.items()},
                        "body": body,
                    }
                )
                payload = b'{"status":"ok"}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(payload)

            def do_GET(self) -> None:
                self._capture()

            def do_POST(self) -> None:
                self._capture()

            def do_PUT(self) -> None:
                self._capture()

        self.server = ThreadingHTTPServer((host, port), Handler)

    def run(self) -> None:
        self.server.serve_forever()

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()


class GatewayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.spool = root / "spool"
        self.spool.mkdir()
        self.db_dir = root / "clamav"
        self.db_dir.mkdir()
        (self.db_dir / "daily.cvd").write_bytes(b"db")
        os.utime(self.db_dir / "daily.cvd", (time.time() - 3600, time.time() - 3600))
        self.clamd_sock = str(root / "clamd.ctl")
        self.clamd = MockClamd(self.clamd_sock)
        self.clamd.start()
        self._wait_socket(self.clamd_sock)

        self.upstream = MockUpstream("127.0.0.1", 0)
        self.upstream.start()
        self.upstream_port = self.upstream.server.server_address[1]

        self.config = gw.GatewayConfig(
            listen_host="127.0.0.1",
            listen_port=0,
            clamd_socket=self.clamd_sock,
            spool_dir=str(self.spool),
            fail_open=False,
            upstreams=frozenset({f"127.0.0.1:{self.upstream_port}"}),
            max_body=1024 * 1024,
            db_dir=str(self.db_dir),
            scan_timeout=5.0,
            forward_timeout=5.0,
        )
        self.metrics = gw.Metrics()
        handler = gw.make_handler(self.config, self.metrics)
        from http.server import ThreadingHTTPServer

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.gw_port = self.httpd.server_address[1]

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.upstream.stop()
        self.clamd.stop()
        self.tmp.cleanup()

    def _wait_socket(self, path: str) -> None:
        for _ in range(50):
            if os.path.exists(path):
                return
            time.sleep(0.05)
        self.fail(f"mock clamd socket missing: {path}")

    def _request(
        self,
        method: str,
        path: str,
        body: bytes | None = None,
        upstream: str | None = "auto",
        extra_headers: dict | None = None,
    ):
        headers = {"Host": "dhis.example.org"}
        if upstream == "auto":
            headers["X-DHIS2-Upstream"] = f"http://127.0.0.1:{self.upstream_port}"
        elif upstream:
            headers["X-DHIS2-Upstream"] = upstream
        if extra_headers:
            headers.update(extra_headers)
        conn = HTTPConnection("127.0.0.1", self.gw_port, timeout=5)
        try:
            conn.request(method, path, body=body, headers=headers)
            response = conn.getresponse()
            return response.status, response.read(), dict(response.getheaders())
        finally:
            conn.close()

    def test_eicar_is_blocked_and_not_forwarded(self) -> None:
        status, body, _ = self._request(
            "POST", "/api/fileResources", body=EICAR.encode()
        )
        self.assertEqual(status, 403)
        self.assertIn(b"malware_detected", body)
        self.assertIn(b"Eicar-Signature", body)
        self.assertEqual(self.upstream.requests, [])

    def test_clean_post_is_forwarded_unchanged(self) -> None:
        payload = b"clean-upload-bytes"
        status, body, _ = self._request("POST", "/api/fileResources", body=payload)
        self.assertEqual(status, 200)
        self.assertEqual(body, b'{"status":"ok"}')
        self.assertEqual(len(self.upstream.requests), 1)
        seen = self.upstream.requests[0]
        self.assertEqual(seen["method"], "POST")
        self.assertEqual(seen["path"], "/api/fileResources")
        self.assertEqual(seen["body"], payload)
        self.assertEqual(seen["headers"]["host"], "dhis.example.org")

    def test_get_is_not_scanned(self) -> None:
        status, _, _ = self._request("GET", "/api/fileResources")
        self.assertEqual(status, 200)
        self.assertEqual(self.upstream.requests[0]["method"], "GET")
        self.assertEqual(self.metrics.scans, 0)

    def test_missing_upstream_is_502(self) -> None:
        status, body, _ = self._request(
            "GET", "/api/fileResources", upstream=None
        )
        self.assertEqual(status, 502)
        self.assertIn(b"invalid_upstream", body)
        self.assertEqual(self.upstream.requests, [])

    def test_unknown_upstream_is_502(self) -> None:
        status, body, _ = self._request(
            "POST",
            "/api/fileResources",
            body=b"x",
            upstream="http://10.1.2.3:8080",
        )
        self.assertEqual(status, 502)
        self.assertIn(b"invalid_upstream", body)
        self.assertEqual(self.upstream.requests, [])

    def test_clamd_down_fail_closed(self) -> None:
        self.clamd.down = True
        os.unlink(self.clamd_sock)
        status, body, _ = self._request("POST", "/api/fileResources", body=b"x")
        self.assertEqual(status, 503)
        self.assertIn(b"scanner_unavailable", body)
        self.assertEqual(self.upstream.requests, [])

    def test_clamd_down_fail_open_forwards(self) -> None:
        self.config.fail_open = True
        self.clamd.down = True
        os.unlink(self.clamd_sock)
        status, _, _ = self._request("POST", "/api/fileResources", body=b"x")
        self.assertEqual(status, 200)
        self.assertEqual(self.upstream.requests[0]["body"], b"x")

    def test_healthz_ping_only(self) -> None:
        status, body, _ = self._request("GET", "/healthz", upstream=None)
        self.assertEqual(status, 200)
        self.assertEqual(body, b"ok\n")

    def test_healthz_down(self) -> None:
        self.clamd.down = True
        os.unlink(self.clamd_sock)
        status, body, _ = self._request("GET", "/healthz", upstream=None)
        self.assertEqual(status, 503)
        self.assertIn(b"scanner_unavailable", body)

    def test_metrics_include_signature_age_and_clamd(self) -> None:
        self._request("POST", "/api/fileResources", body=b"ok")
        status, body, _ = self._request("GET", "/metrics", upstream=None)
        self.assertEqual(status, 200)
        text = body.decode()
        self.assertIn("clamav_scans_total 1", text)
        self.assertIn("clamav_infected_total 0", text)
        self.assertIn("clamav_clamd_up 1", text)
        self.assertIn("clamav_signature_age_seconds", text)
        age = int(
            [line for line in text.splitlines() if line.startswith("clamav_signature_age_seconds ")][0].split()[1]
        )
        self.assertGreaterEqual(age, 1)

    def test_copy_limited_reports_short_read(self) -> None:
        import io

        dest = io.BytesIO()
        leftover = gw.copy_limited(io.BytesIO(b"ab"), dest, 10)
        self.assertEqual(leftover, 8)
        self.assertEqual(dest.getvalue(), b"ab")

    def test_invalid_content_length_is_400(self) -> None:
        status, body, _ = self._request(
            "POST",
            "/api/fileResources",
            body=b"x",
            extra_headers={"Content-Length": "nope"},
        )
        self.assertEqual(status, 400)
        self.assertIn(b"invalid_content_length", body)
        self.assertEqual(self.upstream.requests, [])

    def _multipart(self, filename: str, payload: bytes) -> tuple[bytes, str]:
        boundary = "----GatewayTestBoundary"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            "Content-Type: application/octet-stream\r\n"
            "\r\n"
        ).encode() + payload + f"\r\n--{boundary}--\r\n".encode()
        return body, f"multipart/form-data; boundary={boundary}"

    def test_multipart_eicar_is_blocked_and_not_forwarded(self) -> None:
        body, content_type = self._multipart("eicar.com", EICAR.encode())
        status, resp, _ = self._request(
            "POST",
            "/api/fileResources",
            body=body,
            extra_headers={"Content-Type": content_type},
        )
        self.assertEqual(status, 403)
        self.assertIn(b"malware_detected", resp)
        self.assertEqual(self.upstream.requests, [])

    def test_multipart_clean_is_forwarded_unchanged(self) -> None:
        payload = b"clean-upload-bytes"
        body, content_type = self._multipart("clean.txt", payload)
        status, _, _ = self._request(
            "POST",
            "/api/fileResources",
            body=body,
            extra_headers={"Content-Type": content_type},
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(self.upstream.requests), 1)
        self.assertEqual(self.upstream.requests[0]["body"], body)

    def test_parse_upstream_header(self) -> None:
        self.assertEqual(gw.parse_upstream_header("http://10.0.0.4:8080"), "10.0.0.4:8080")
        self.assertEqual(gw.parse_upstream_header("10.0.0.4:8080"), "10.0.0.4:8080")
        self.assertEqual(
            gw.parse_upstream_header("http://[2001:db8::1]:8080"), "[2001:db8::1]:8080"
        )
        self.assertIsNone(gw.parse_upstream_header(""))
        self.assertIsNone(gw.parse_upstream_header(None))


if __name__ == "__main__":
    unittest.main()
