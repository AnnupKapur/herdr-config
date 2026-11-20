#!/usr/bin/env python3
"""Keep Herdr tab labels prefixed with their 1-based tab bar position (e.g. 1:dev, 2:git)."""

from __future__ import annotations

import fcntl
import json
import os
import re
import socket
import sys
import tempfile

PREFIX_RE = re.compile(r"^(?:\d+:)+")


def get_socket_path() -> str:
    env_path = os.environ.get("HERDR_SOCKET_PATH")
    if env_path:
        return env_path
    return os.path.expanduser("~/.config/herdr/herdr.sock")


def rpc_call(sock_path: str, method: str, params: dict | None = None) -> dict:
    req: dict = {"id": f"tab-numbers:{method}", "method": method}
    if params is not None:
        req["params"] = params
    payload = (json.dumps(req) + "\n").encode("utf-8")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.settimeout(3.0)
        s.connect(sock_path)
        s.sendall(payload)
        chunks: list[bytes] = []
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
            if b"\n" in chunk:
                break
    raw = b"".join(chunks).split(b"\n", 1)[0]
    if not raw:
        raise RuntimeError(f"empty response from herdr for {method}")
    return json.loads(raw.decode("utf-8"))


def desired_label(tab: dict, pos: int, strip_only: bool) -> str:
    label = str(tab.get("label", ""))
    base = PREFIX_RE.sub("", label)
    if strip_only:
        return base if base else str(tab.get("number", pos))
    tab_num = str(tab.get("number", ""))
    if not base or base == str(pos) or base == tab_num:
        return str(pos)
    return f"{pos}:{base}"


def sync_tabs(sock_path: str, workspace_id: str | None = None, strip_only: bool = False) -> int:
    params = {"workspace_id": workspace_id} if workspace_id else {}
    resp = rpc_call(sock_path, "tab.list", params)
    if "error" in resp:
        print(f"tab-numbers: {resp['error']}", file=sys.stderr)
        return 1

    tabs = resp.get("result", {}).get("tabs", [])
    by_workspace: dict[str, list[dict]] = {}
    for tab in tabs:
        ws = tab["workspace_id"]
        by_workspace.setdefault(ws, []).append(tab)

    for ws_tabs in by_workspace.values():
        for pos, tab in enumerate(ws_tabs, start=1):
            current = str(tab.get("label", ""))
            target = desired_label(tab, pos, strip_only=strip_only)
            if current != target:
                res = rpc_call(
                    sock_path,
                    "tab.rename",
                    {"tab_id": tab["tab_id"], "label": target},
                )
                if "error" in res:
                    print(f"tab-numbers: {res['error']}", file=sys.stderr)
    return 0


def main() -> int:
    strip_only = "--strip" in sys.argv[1:]
    all_workspaces = "--all" in sys.argv[1:]
    sock_path = get_socket_path()

    # Scope to the triggering workspace when invoked by a workspace/tab event,
    # and sync all workspaces on startup or manual invocation without a workspace ID.
    event = os.environ.get("HERDR_PLUGIN_EVENT", "")
    workspace_id = None if (all_workspaces or not event or event == "startup") else os.environ.get("HERDR_WORKSPACE_ID")

    lock_name = f"herdr-tab-numbers-{os.getuid()}.lock"
    lock_path = os.path.join(tempfile.gettempdir(), lock_name)
    with open(lock_path, "w") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        return sync_tabs(sock_path, workspace_id=workspace_id, strip_only=strip_only)


if __name__ == "__main__":
    raise SystemExit(main())
