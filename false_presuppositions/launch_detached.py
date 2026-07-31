"""
Launch one command in its own session (setsid), fully detached, and exit immediately.

nohup + disown is not enough here: both leave the child in the launcher's process
group, so a group-level kill (or the shell going away) takes the run down with it.
start_new_session=True calls setsid(2), which puts the child in a brand-new session
with no controlling terminal, so it survives.

Usage:
    python3 launch_detached.py <logfile> <command> [args...]
"""
from __future__ import annotations

import os
import subprocess
import sys


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2

    log_path = sys.argv[1]
    command = sys.argv[2:]
    os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)

    # Append so a relaunch of the same question keeps the earlier attempt's output.
    with open(log_path, "ab", buffering=0) as log_file:
        process = subprocess.Popen(
            command,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,   # setsid: survives a process-group kill
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
    print(f"pid {process.pid} -> {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
