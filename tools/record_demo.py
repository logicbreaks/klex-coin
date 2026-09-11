"""Record a real terminal session into asciinema .cast format.

Runs commands in a genuine pty against a real shell — outputs are live, not
simulated. Usage:

    python tools/record_demo.py --out site/casts/01.cast --klex-home /tmp/klex-demo \\
        --commands script.txt

Script file format: one command per line, blank lines ignored, lines starting
with `#` are comments. Optional directive lines:
    :sleep 3        wait 3 seconds before the next command
"""

import argparse
import fcntl
import json
import os
import pty
import select
import signal
import struct
import sys
import termios
import time


def parse_script(path: str) -> list:
    steps = []
    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip("\n")
        if not line.strip() or line.startswith("#"):
            continue
        if line.startswith(":sleep"):
            steps.append(("sleep", float(line.split()[1])))
        else:
            steps.append(("cmd", line))
    return steps


def record(script_path: str, out_path: str, width: int = 96, height: int = 30, cwd: str = None) -> float:
    steps = parse_script(script_path)
    pid, master = pty.fork()
    if pid == 0:
        env = dict(os.environ)
        env.setdefault("TERM", "xterm-256color")
        env["KLEX_WALLET_PASS"] = env.get("KLEX_WALLET_PASS") or "demo-pass"
        if cwd:
            env["PWD"] = cwd
            os.chdir(cwd)
        os.execvpe("bash", ["bash", "--noprofile", "--norc", "-i"], env)
    fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack("HHHH", height, width, 0, 0))

    events: list = []
    started = time.time()

    def emit(data: str) -> None:
        events.append([round(time.time() - started, 3), "o", data])

    pending = b""
    alive = True

    def drain(duration: float) -> None:
        nonlocal alive
        deadline = time.time() + duration
        while time.time() < deadline and alive:
            r, _, _ = select.select([master], [], [], 0.05)
            if master in r:
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    alive = False
                    break
                if not chunk:
                    alive = False
                    break
                emit(chunk.decode("utf-8", "replace"))

    for kind, value in steps:
        if not alive:
            break
        if kind == "sleep":
            drain(value)
            continue
        # type the command visibly, then commit it
        for ch in value + "\n":
            try:
                os.write(master, ch.encode("utf-8"))
            except OSError:
                alive = False
                break
            time.sleep(0.012)
            drain(0.012)
        drain(1.4)

    deadline = time.time() + 1.2
    while time.time() < deadline and alive:
        drain(0.1)
    try:
        os.write(master, b"exit\n")
    except OSError:
        pass
    time.sleep(0.3)
    while alive:
        try:
            r, _, _ = select.select([master], [], [], 0.2)
            if master in r:
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    break
                if not chunk:
                    break
                emit(chunk.decode("utf-8", "ignore"))
        except (OSError, select.error):
            break
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    os.close(master)
    duration = round(time.time() - started, 3)
    header = {
        "version": 2,
        "width": width,
        "height": height,
        "duration": duration,
        "command": "bash --noprofile --norc -i",
        "title": "KLEX demo session",
        "env": {"SHELL": "/bin/bash", "TERM": "xterm-256color"},
    }
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(header) + "\n")
        for t, kind, data in events:
            f.write(json.dumps([t, kind, data], ensure_ascii=False) + "\n")
    return duration


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--klex-home", required=True, help="scratch data dir for KLEX_HOME")
    ap.add_argument("--script", required=True, help="script file with commands")
    ap.add_argument("--cwd", default=None)
    ap.add_argument("--width", type=int, default=96)
    ap.add_argument("--height", type=int, default=30)
    args = ap.parse_args()
    os.environ["KLEX_HOME"] = args.klex_home
    os.environ["PATH"] = os.path.join(os.getcwd(), ".venv", "bin") + os.pathsep + os.environ["PATH"]
    import shutil

    assert shutil.which("klex"), "klex not found — run from repo root with .venv present"
    duration = record(args.script, args.out, width=args.width, height=args.height, cwd=args.cwd)
    print(f"recorded {args.out} · {duration:.1f}s")


if __name__ == "__main__":
    main()