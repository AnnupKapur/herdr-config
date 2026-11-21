#!/usr/bin/env python3
"""Publish each agent's and workspace's 1-based sidebar position as an `idx` metadata token.

The expanded sidebar renders it via `$idx` in [ui.sidebar.*] rows (see config.toml),
matching the numbers shown in the collapsed sidebar and used by focus_agent / switch_workspace.
"""

from __future__ import annotations

import fcntl
import json
import os
import socket
import sys
import tempfile

SOURCE = "sidebar-numbers"
TOKEN = "idx"


def get_socket_path() -> str:
    env_path = os.environ.get("HERDR_SOCKET_PATH")
    if env_path:
        return env_path
    return os.path.expanduser("~/.config/herdr/herdr.sock")


def rpc_call(sock_path: str, method: str, params: dict | None = None) -> dict:
    req: dict = {"id": f"{SOURCE}:{method}", "method": method}
    if params is not None:
        req["params"] = params
    payload = (json.dumps(req) + "\n").encode("utf-8")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.settimeout(3.0)
        s.connect(sock_path)
        s.sendall(payload)
        chunks: list[bytes] = []
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
            if b"\n" in chunk:
                break
    raw = b"".join(chunks).split(b"\n", 1)[0]
    if not raw:
        raise RuntimeError(f"empty response from herdr for {method}")
    return json.loads(raw.decode("utf-8"))


def result(sock_path: str, method: str, key: str, params: dict | None = None) -> list[dict]:
    resp = rpc_call(sock_path, method, params)
    if "error" in resp:
        raise RuntimeError(f"{method}: {resp['error']}")
    return resp.get("result", {}).get(key, [])


def sync(sock_path: str) -> int:
    errors = 0

    def report(method: str, params: dict) -> None:
        nonlocal errors
        res = rpc_call(sock_path, method, params)
        if "error" in res:
            errors += 1
            print(f"{SOURCE}: {method}: {res['error']}", file=sys.stderr)

    # Workspaces: use herdr's own workspace number.
    for ws in result(sock_path, "workspace.list", "workspaces", {}):
        want = str(ws.get("number", ""))
        if (ws.get("tokens") or {}).get(TOKEN) != want:
            report("workspace.report_metadata",
                   {"workspace_id": ws["workspace_id"], "source": SOURCE, "tokens": {TOKEN: want}})

    # Agents: position in agent.list (same order as the agent panel / focus_agent).
    agents = result(sock_path, "agent.list", "agents", {})
    wanted = {a["pane_id"]: str(i) for i, a in enumerate(agents, start=1)}
    for a in agents:
        if (a.get("tokens") or {}).get(TOKEN) != wanted[a["pane_id"]]:
            report("pane.report_metadata",
                   {"pane_id": a["pane_id"], "source": SOURCE, "tokens": {TOKEN: wanted[a["pane_id"]]}})

    # Clear stale numbers from panes that are no longer agents.
    for pane in result(sock_path, "pane.list", "panes", {}):
        if pane["pane_id"] not in wanted and TOKEN in (pane.get("tokens") or {}):
            report("pane.report_metadata",
                   {"pane_id": pane["pane_id"], "source": SOURCE, "tokens": {TOKEN: None}})

    return 1 if errors else 0


def main() -> int:
    lock_path = os.path.join(tempfile.gettempdir(), f"herdr-{SOURCE}-{os.getuid()}.lock")
    with open(lock_path, "w") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            return sync(get_socket_path())
        except Exception as exc:  # noqa: BLE001
            print(f"{SOURCE}: {exc}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
