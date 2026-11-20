#!/usr/bin/env python3
"""Equalize horizontal (width) split ratios for all panes in the active Herdr tab."""

from __future__ import annotations

import json
import os
import socket
import sys


def get_socket_path() -> str:
    env_path = os.environ.get("HERDR_SOCKET_PATH")
    if env_path:
        return env_path
    return os.path.expanduser("~/.config/herdr/herdr.sock")


def rpc_call(sock_path: str, method: str, params: dict | None = None) -> dict:
    req: dict = {"id": f"equalize:{method}", "method": method}
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


def col_count(node: dict) -> int:
    if node.get("type") != "split":
        return 1
    first = col_count(node["first"])
    second = col_count(node["second"])
    if node.get("direction") == "right":
        return first + second
    return max(first, second)


def collect_width_updates(node: dict, path: tuple[bool, ...] = ()) -> list[tuple[list[bool], float]]:
    if node.get("type") != "split":
        return []
    updates: list[tuple[list[bool], float]] = []
    if node.get("direction") == "right":
        left = col_count(node["first"])
        right = col_count(node["second"])
        target = left / (left + right)
        current = float(node.get("ratio", 0.5))
        if abs(current - target) > 1e-4:
            updates.append((list(path), target))
    updates.extend(collect_width_updates(node["first"], path + (False,)))
    updates.extend(collect_width_updates(node["second"], path + (True,)))
    return updates


def main() -> int:
    sock_path = get_socket_path()
    resp = rpc_call(sock_path, "layout.export", {})
    if "error" in resp:
        print(f"equalize-panes: {resp['error']}", file=sys.stderr)
        return 1

    layout = resp.get("result", {}).get("layout")
    if not layout:
        return 0

    tab_id = layout["tab_id"]
    root = layout["root"]
    updates = collect_width_updates(root)
    for path, ratio in updates:
        res = rpc_call(
            sock_path,
            "layout.set_split_ratio",
            {"tab_id": tab_id, "path": path, "ratio": ratio},
        )
        if "error" in res:
            print(f"equalize-panes: {res['error']}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
