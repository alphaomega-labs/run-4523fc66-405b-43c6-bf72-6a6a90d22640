from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .mcp_adapter import call_tool, list_tools


def _response_ok(result: Any, request_id: Any | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": True, "result": result}
    if request_id is not None:
        payload["id"] = request_id
    return payload


def _response_error(message: str, request_id: Any | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": False, "error": message}
    if request_id is not None:
        payload["id"] = request_id
    return payload


def _handle_request(request: dict[str, Any]) -> dict[str, Any]:
    request_id = request.get("id")

    if request.get("method") == "tools/list":
        return _response_ok({"tools": list_tools()}, request_id=request_id)

    if request.get("method") == "tools/call":
        params = request.get("params", {})
        if not isinstance(params, dict):
            return _response_error("params must be an object", request_id=request_id)
        name = params.get("name")
        arguments = params.get("arguments", {})
        if not isinstance(name, str):
            return _response_error("params.name must be a string", request_id=request_id)
        if not isinstance(arguments, dict):
            return _response_error("params.arguments must be an object", request_id=request_id)
        try:
            return _response_ok(call_tool(name, arguments), request_id=request_id)
        except Exception as exc:  # noqa: BLE001
            return _response_error(str(exc), request_id=request_id)

    if "tool" in request:
        name = request.get("tool")
        arguments = request.get("input", {})
        if not isinstance(name, str):
            return _response_error("tool must be a string", request_id=request_id)
        if not isinstance(arguments, dict):
            return _response_error("input must be an object", request_id=request_id)
        try:
            return _response_ok(call_tool(name, arguments), request_id=request_id)
        except Exception as exc:  # noqa: BLE001
            return _response_error(str(exc), request_id=request_id)

    return _response_error("Unsupported request shape", request_id=request_id)


def serve_stdio(pretty: bool) -> int:
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            request = json.loads(raw)
        except json.JSONDecodeError as exc:
            response = _response_error(f"Invalid JSON request: {exc}")
        else:
            if not isinstance(request, dict):
                response = _response_error("Request must be a JSON object")
            else:
                response = _handle_request(request)

        text = json.dumps(response, indent=2 if pretty else None, sort_keys=True)
        sys.stdout.write(text + "\n")
        sys.stdout.flush()
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stdio MCP companion server for antineutrino safeguards package."
    )
    parser.add_argument("--serve", action="store_true", help="Run line-delimited stdio server mode.")
    parser.add_argument("--tool", type=str, default=None, help="Run one MCP tool once and exit.")
    parser.add_argument(
        "--input",
        type=str,
        default="{}",
        help="JSON object for --tool execution; ignored in --serve mode.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON responses.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.serve:
        return serve_stdio(pretty=args.pretty)

    if args.tool is not None:
        try:
            payload = json.loads(args.input)
        except json.JSONDecodeError as exc:
            sys.stderr.write(f"Invalid --input JSON: {exc}\n")
            return 2
        if not isinstance(payload, dict):
            sys.stderr.write("--input JSON must decode to an object.\n")
            return 2
        try:
            result = call_tool(args.tool, payload)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"Tool execution failed: {exc}\n")
            return 1
        text = json.dumps({"ok": True, "result": result}, indent=2 if args.pretty else None)
        sys.stdout.write(text + "\n")
        return 0

    tools = ", ".join(tool["name"] for tool in list_tools())
    sys.stdout.write(f"Available tools: {tools}\n")
    sys.stdout.write("Use --serve for stdio mode or --tool <name> for one-shot mode.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
