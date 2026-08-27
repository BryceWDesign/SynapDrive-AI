from __future__ import annotations

import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable
from wsgiref.simple_server import make_server
from wsgiref.types import StartResponse, WSGIEnvironment
from wsgiref.util import setup_testing_defaults

from synapdrive_ai.pipeline import SynapDrivePipeline

_TEMPLATE = Path(__file__).with_name("templates") / "index.html"


@dataclass(frozen=True)
class DashboardResponse:
    status_code: int
    data: bytes
    content_type: str

    def get_json(self) -> Any:
        if "application/json" not in self.content_type:
            return None
        return json.loads(self.data.decode("utf-8"))


class DashboardTestClient:
    """In-process WSGI client used by the repository's route tests."""

    def __init__(self, application: "DashboardApplication") -> None:
        self.application = application

    def get(self, path: str) -> DashboardResponse:
        return self._request("GET", path, None)

    def post(self, path: str, json: Any = None) -> DashboardResponse:
        return self._request("POST", path, json)

    def _request(self, method: str, path: str, payload: Any) -> DashboardResponse:
        body = b"" if payload is None else json.dumps(payload).encode("utf-8")
        environ: dict[str, Any] = {}
        setup_testing_defaults(environ)
        environ.update(
            {
                "REQUEST_METHOD": method,
                "PATH_INFO": path,
                "CONTENT_TYPE": "application/json" if body else "",
                "CONTENT_LENGTH": str(len(body)),
                "wsgi.input": io.BytesIO(body),
            }
        )
        captured: dict[str, Any] = {}

        def start_response(
            status: str,
            headers: list[tuple[str, str]],
            exc_info: object = None,
        ) -> Callable[[bytes], object]:
            del exc_info
            captured["status"] = status
            captured["headers"] = dict(headers)
            return lambda data: len(data)

        chunks = self.application(environ, start_response)
        data = b"".join(chunks)
        status_code = int(str(captured["status"]).split()[0])
        headers = captured.get("headers", {})
        return DashboardResponse(
            status_code=status_code,
            data=data,
            content_type=str(headers.get("Content-Type", "application/octet-stream")),
        )


class DashboardApplication:
    """Small localhost-only WSGI dashboard over the canonical governed pipeline."""

    def __init__(self, pipeline: SynapDrivePipeline | None = None) -> None:
        self.pipeline = pipeline or SynapDrivePipeline(simulate_delay=False)

    def test_client(self) -> DashboardTestClient:
        return DashboardTestClient(self)

    def __call__(
        self,
        environ: WSGIEnvironment,
        start_response: StartResponse,
    ) -> Iterable[bytes]:
        method = str(environ.get("REQUEST_METHOD", "GET")).upper()
        path = str(environ.get("PATH_INFO", "/"))
        try:
            status, content_type, payload = self._dispatch(method, path, environ)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            status, content_type, payload = (
                "400 Bad Request",
                "application/json; charset=utf-8",
                self._json_bytes({"error": "invalid-request", "detail": str(exc)}),
            )
        except Exception:
            status, content_type, payload = (
                "500 Internal Server Error",
                "application/json; charset=utf-8",
                self._json_bytes({"error": "internal-server-error"}),
            )
        start_response(
            status,
            [
                ("Content-Type", content_type),
                ("Content-Length", str(len(payload))),
                ("Cache-Control", "no-store"),
                ("X-Content-Type-Options", "nosniff"),
            ],
        )
        return [payload]

    def _dispatch(
        self,
        method: str,
        path: str,
        environ: WSGIEnvironment
    ) -> tuple[str, str, bytes]:
        if method == "GET" and path == "/":
            return "200 OK", "text/html; charset=utf-8", _TEMPLATE.read_bytes()
        if method == "GET" and path == "/api/log":
            log = self.pipeline.get_action_log()
            return self._json_response({"count": len(log), "log": log[-50:]})
        if method == "GET" and path == "/api/assurance":
            return self._json_response(
                {
                    "report": self.pipeline.get_assurance_report(),
                    "receipts": self.pipeline.get_assurance_log()[-50:],
                }
            )
        if method == "POST" and path == "/api/run/text":
            data = self._read_json(environ)
            command = str(data.get("text") or "").strip()
            image = data.get("image")
            return self._json_response(
                self.pipeline.run_text_command(command, image_label=image)
            )
        if method == "POST" and path == "/api/run/signal":
            data = self._read_json(environ)
            label = data.get("label")
            image = data.get("image")
            return self._json_response(
                self.pipeline.run_signal_event(label=label, image_label=image)
            )
        if path.startswith("/api/"):
            return self._json_response({"error": "not-found"}, status="404 Not Found")
        return "404 Not Found", "text/plain; charset=utf-8", b"Not Found\n"

    @staticmethod
    def _read_json(environ: dict[str, Any]) -> dict[str, Any]:
        raw_length = str(environ.get("CONTENT_LENGTH") or "0")
        length = int(raw_length) if raw_length.isdigit() else 0
        raw = environ["wsgi.input"].read(length) if length else b"{}"
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

    @staticmethod
    def _json_bytes(payload: Any) -> bytes:
        return json.dumps(payload, default=str, separators=(",", ":")).encode("utf-8")

    def _json_response(
        self,
        payload: Any,
        *,
        status: str = "200 OK",
    ) -> tuple[str, str, bytes]:
        return status, "application/json; charset=utf-8", self._json_bytes(payload)


app = DashboardApplication()


def main() -> None:
    host = "127.0.0.1"
    port = 5055
    print(f"SynapDrive-AI dashboard listening on http://{host}:{port}")
    with make_server(host, port, app) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
