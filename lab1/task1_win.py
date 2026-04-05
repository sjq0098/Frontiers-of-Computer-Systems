"""
task1_win.py - Task 1: Windows Basic Performance Test Driver
Usage: python task1_win.py

Prerequisites:
  1. fio installed and in PATH (https://github.com/axboe/fio/releases)
  2. Run from a directory with >5GB free space
  3. Run CMD/PowerShell as Administrator
"""

import subprocess
import json
import os

# ---- Global Parameters ----
BS = "4k"
IOENGINE = "pvsync"
NUMJOBS = 1
IODEPTH = 1
SIZE = "1G"
RUNTIME = 60
FILENAME = "fio_test_file"
JSON_TMP = "_fio_out.json"
CSV_FILE = "task1_results_win.csv"

# Note: Windows pvsync does NOT support --direct=1
# So this test may include OS cache effects.

RW_MODES = [
    ("read",      "Sequential Read"),
    ("write",     "Sequential Write"),
    ("randread",  "Random Read"),
    ("randwrite", "Random Write"),
]


def load_fio_json(path):
    """Load fio JSON even if warning lines are prepended."""
    with open(path, encoding="utf-8", errors="replace") as f:
        raw = f.read().strip()

    if not raw:
        raise ValueError("fio output file is empty")

    # fio on Windows may prepend warning text before JSON.
    json_start = raw.find("{")
    if json_start < 0:
        raise ValueError("no JSON object found in fio output")

    return json.loads(raw[json_start:])


def run_fio(rw, bs, ioengine, numjobs, iodepth, direct=False):
    """Run one fio test, parse JSON output, return (iops, bw_KB, lat_us) or None."""
    cmd = [
        "fio", "--name=test",
        f"--rw={rw}", f"--bs={bs}",
        f"--ioengine={ioengine}",
        f"--numjobs={numjobs}", f"--iodepth={iodepth}",
        f"--size={SIZE}", f"--runtime={RUNTIME}",
        "--time_based", "--group_reporting",
        "--output-format=json",
        f"--filename={FILENAME}",
        f"--output={JSON_TMP}",
        "--thread",
    ]
    if direct:
        cmd.append("--direct=1")

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=RUNTIME + 60
        )
    except Exception as e:
        print(f"    -> fio error: {e}")
        return None

    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        stdout = (proc.stdout or "").strip()
        msg = stderr or stdout or f"exit code {proc.returncode}"
        print(f"    -> fio failed: {msg}")
        return None

    try:
        data = load_fio_json(JSON_TMP)
        rw_field = "read" if "read" in rw else "write"
        job = data["jobs"][0][rw_field]
        return (job["iops"], job["bw"], job["lat_ns"]["mean"] / 1000)
    except Exception as e:
        print(f"    -> Parse error: {e}")
        return None


def cleanup():
    for f in [FILENAME, JSON_TMP]:
        try:
            os.remove(f)
        except OSError:
            pass


def main():
    print("=" * 50)
    print(" Task 1: Basic Performance Test (Windows)")
    print(f" Params: bs={BS}, ioengine={IOENGINE}, numjobs={NUMJOBS}, iodepth={IODEPTH}")
    print(" Note: pvsync on Windows does not support direct I/O")
    print("=" * 50)

    with open(CSV_FILE, "w") as csvf:
        csvf.write("rw,iops,bw_KBps,lat_us\n")

        for i, (rw, name) in enumerate(RW_MODES, 1):
            print(f"\n[{i}/4] {name} ({rw}) ...")
            result = run_fio(rw, BS, IOENGINE, NUMJOBS, IODEPTH)

            if result:
                iops, bw, lat = result
                print(f"    -> IOPS={iops:.0f}, BW={bw:.0f} KB/s, Lat={lat:.1f} us")
                csvf.write(f"{rw},{iops},{bw},{lat}\n")
                csvf.flush()
            else:
                print("    -> FAILED")

    cleanup()
    print("\n" + "=" * 50)
    print(f" Done! Results saved to: {CSV_FILE}")
    print("=" * 50)

    # Preview
    with open(CSV_FILE) as f:
        print(f.read())


if __name__ == "__main__":
    main()
