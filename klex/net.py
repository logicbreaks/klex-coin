"""Minimal P2P block sync: newline-delimited JSON over TCP.

Server: `klex serve` — answers GET_CHAIN(height) with blocks beyond that height.
Client: `klex sync host:port` — fetches, validates, extends the local chain.
"""

import json
import socket

from . import chain

MSG_HELLO = {"proto": "klex", "version": 1}


def _recv_line(sock) -> dict:
    buf = b""
    while not buf.endswith(b"\n"):
        chunk = sock.recv(65536)
        if not chunk:
            raise ConnectionError("peer closed connection")
        buf += chunk
        if len(buf) > 16 * 1024 * 1024:
            raise ValueError("message too large")
    return json.loads(buf.decode("utf-8"))


def _send_line(sock, obj) -> None:
    sock.sendall(json.dumps(obj).encode("utf-8") + b"\n")


def serve(node, host: str = "127.0.0.1", port: int = 9333) -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(4)
    print(f"serving blocks on {host}:{port} (Ctrl-C to stop)")
    try:
        while True:
            conn, addr = srv.accept()
            try:
                request = _recv_line(conn)
                if request.get("cmd") != "GET_CHAIN":
                    _send_line(conn, {"error": "unknown command"})
                    continue
                peer_height = int(request.get("height", 0))
                if peer_height < 0 or peer_height > len(node.blocks):
                    _send_line(conn, {"error": "height out of range"})
                    continue
                _send_line(conn, {"cmd": "CHAIN", "blocks": node.blocks[peer_height:]})
            except Exception as exc:
                try:
                    _send_line(conn, {"error": str(exc)})
                except Exception:
                    pass
            finally:
                conn.close()
    finally:
        srv.close()


def sync(node, peer: str) -> int:
    host, _, port = peer.partition(":")
    port = int(port or 9333)
    with socket.create_connection((host, port), timeout=10) as sock:
        _send_line(sock, {"cmd": "GET_CHAIN", "height": len(node.blocks)})
        reply = _recv_line(sock)
    if "error" in reply:
        raise ValueError(f"peer error: {reply['error']}")
    blocks = reply.get("blocks", [])
    added = 0
    for block in blocks:
        try:
            node.add_block(block)
            added += 1
        except ValueError as exc:
            raise ValueError(f"peer sent invalid block {block.get('index')}: {exc}") from exc
    return added