#!/usr/bin/env python3
"""Dispatch media jobs from this PC to the Alienware worker node (leo-ASM100).

Uses SFTP + the file job queue (no sudo, no samba). Submits an input file plus
a job JSON, polls /srv/jobs/done, and downloads results.

Usage:
  alienware_dispatch.py ffmpeg <local_input> [--args "-c:v h264_nvenc -preset p4"] [--out name.mp4]
  alienware_dispatch.py transcribe <local_input> [--model small]
  alienware_dispatch.py status

Job lifecycle:  input + job.json -> /srv/jobs/queue  ->  worker runs  ->  /srv/jobs/done|failed
"""
import json, os, sys, time, uuid, hashlib
from pathlib import Path

sys.path.insert(0, "/home/leo/.hermes/hermes-agent/venv/lib/python3.11/site-packages")
import paramiko

HOST = "100.99.62.20"  # Tailscale IP (2026-08-28) — was the LAN-only 192.168.0.224,
# which broke reachability whenever this machine wasn't on the same local
# network (the exact issue from the earlier wifi-extender SSH outage this
# session). Tailscale is boot-enabled on both machines and reconnects
# automatically after a reboot with no re-auth needed — this address stays
# reachable regardless of which network either machine is actually on.
# Fall back to the LAN IP below only if Tailscale itself is ever down.
LAN_FALLBACK_HOST = "192.168.0.224"
USER = "worker"
PASS = "worker"
QUEUE, DONE, FAILED = "/srv/jobs/queue", "/srv/jobs/done", "/srv/jobs/failed"
INPUTS = "/srv/media/clips"
OUTPUTS = "/srv/media/clips"

def connect():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        c.connect(HOST, username=USER, password=PASS, timeout=10,
                  look_for_keys=False, allow_agent=False)
        return c
    except Exception as e:
        print(f"Tailscale address ({HOST}) unreachable ({e}), trying LAN fallback ({LAN_FALLBACK_HOST})...", file=sys.stderr)
        c.connect(LAN_FALLBACK_HOST, username=USER, password=PASS, timeout=10,
                  look_for_keys=False, allow_agent=False)
        return c

def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:10]

def ensure_remote(c, path):
    _, out, _ = c.exec_command(f"test -e {path} && echo yes || echo no")
    return out.read().decode().strip() == "yes"

def upload_input(c, local: Path, tag: str):
    remote_in = f"{INPUTS}/{tag}_{local.name}"
    if ensure_remote(c, remote_in):
        return remote_in
    sftp = c.open_sftp()
    size = local.stat().st_size
    print(f"uploading {local.name} ({size/1e6:.1f} MB) ...", flush=True)
    sftp.put(str(local), remote_in)
    sftp.close()
    return remote_in

def submit(job: dict):
    job_id = job["id"]
    c = connect()
    blob = json.dumps(job)
    _, out, _ = c.exec_command(f"cat > {QUEUE}/{job_id}.json << 'JEOF'\n{blob}\nJEOF")
    out.channel.recv_exit_status()
    return c

def wait_result(c, job_id: str, timeout=1800):
    start = time.time()
    sftp = c.open_sftp()
    while time.time() - start < timeout:
        for state, d in (("done", DONE), ("failed", FAILED)):
            rp = f"{d}/{job_id}.json"
            if ensure_remote(c, rp):
                data = json.loads(sftp.open(rp).read())
                return state, data
        time.sleep(3)
    return "timeout", {}

def cmd_ffmpeg(local_in: str, extra_args: list, out_name: str | None, timeout=1800):
    local = Path(local_in)
    assert local.exists(), f"no such file: {local}"
    tag = sha1(local)
    c = connect()
    remote_in = upload_input(c, local, tag)
    out_name = out_name or f"{local.stem}_alienware.mp4"
    remote_out = f"{OUTPUTS}/{tag}_{out_name}"
    if not extra_args:
        extra_args = ["-c:v", "h264_nvenc", "-preset", "p4"]
    job = {"id": f"ff-{tag}-{uuid.uuid4().hex[:6]}", "type": "ffmpeg",
           "args": ["-i", remote_in] + extra_args + [remote_out, "-y"]}
    submit(job)
    print(f"submitted {job['id']} -> {HOST}", flush=True)
    state, data = wait_result(c, job["id"], timeout)
    if state == "done":
        local_out = Path("downloads_alienware") / out_name
        local_out.parent.mkdir(exist_ok=True)
        sftp = c.open_sftp()
        sftp.get(remote_out, str(local_out))
        sftp.close()
        c.exec_command(f"rm -f {remote_out} {remote_in}")
        print(f"OK: {local_out} ({local_out.stat().st_size/1e6:.1f} MB), "
              f"elapsed {data.get('elapsed_s')}s on {data.get('host')}")
        return 0
    print(f"FAILED ({state}): {json.dumps(data)[:800]}")
    return 1

def cmd_transcribe(local_in: str, model: str, timeout=1800):
    local = Path(local_in)
    assert local.exists(), f"no such file: {local}"
    tag = sha1(local)
    c = connect()
    remote_in = upload_input(c, local, tag)
    job = {"id": f"tr-{tag}-{uuid.uuid4().hex[:6]}", "type": "transcribe",
           "input": remote_in, "model": model}
    submit(job)
    print(f"submitted {job['id']} -> {HOST}", flush=True)
    state, data = wait_result(c, job["id"], timeout)
    if state == "done":
        out = Path("downloads_alienware") / f"{local.stem}.transcript.json"
        out.parent.mkdir(exist_ok=True)
        out.write_text(data.get("output", ""))
        print(f"OK: {out}, elapsed {data.get('elapsed_s')}s")
        return 0
    print(f"FAILED ({state}): {json.dumps(data)[:800]}")
    return 1

def cmd_status():
    c = connect()
    _, out, _ = c.exec_command(
        "pgrep -af job_worker.py | grep -v bash | head -2; "
        f"echo 'queued: '$(ls {QUEUE} 2>/dev/null | wc -l); "
        f"echo 'done: '$(ls {DONE} 2>/dev/null | wc -l); "
        f"echo 'failed: '$(ls {FAILED} 2>/dev/null | wc -l); "
        "nvidia-smi --query-gpu=name,utilization.gpu,memory.used --format=csv,noheader 2>/dev/null")
    print(out.read().decode())
    return 0

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "status":
        sys.exit(cmd_status())
    if a[0] == "ffmpeg":
        extra, out_name = [], None
        rest = a[2:]
        while rest:
            if rest[0] == "--args":
                extra = rest[1].split(); rest = rest[2:]
            elif rest[0] == "--out":
                out_name = rest[1]; rest = rest[2:]
            else:
                rest = rest[1:]
        sys.exit(cmd_ffmpeg(a[1], extra, out_name))
    if a[0] == "transcribe":
        model = "small"
        if "--model" in a:
            model = a[a.index("--model") + 1]
        sys.exit(cmd_transcribe(a[1], model))
    print(__doc__)
    sys.exit(2)
