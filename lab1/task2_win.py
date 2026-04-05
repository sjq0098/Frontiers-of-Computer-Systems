"""
task2_win.py - Task 2: Multi-parameter Analysis (Windows)
Usage: python task2_win.py

Output files:
  task2_bs_win.csv          - Experiment A: block size impact
  task2_jobs_depth_win.csv  - Experiment B: concurrency impact
  task2_ioengine_win.csv    - Experiment C: I/O engine comparison

Key differences from Linux version:
  - libaio  -> windowsaio (Windows native async I/O)
  - io_uring -> not available on Windows
  - psync/mmap do NOT support --direct=1 on Windows
  - windowsaio DOES support --direct=1
"""

import subprocess
import json
import os

# ---- Global Parameters ----
SIZE = "1G"
RUNTIME = 60
FILENAME = "fio_test_file"
JSON_TMP = "_fio_out.json"

RW_MODES = ["randread", "randwrite"]


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
    """Run one fio test, return (iops, bw_KB, lat_us) or None."""
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


def experiment_a():
    """Block size impact. Fixed: psync, numjobs=1, iodepth=1."""
    csv_file = "task2_bs_win.csv"
    bs_values = ["4k", "16k", "64k", "256k", "1m"]

    print("=" * 50)
    print(" Experiment A: Block Size Impact")
    print(" Fixed: ioengine=psync, numjobs=1, iodepth=1")
    print(" Note: psync on Windows does not support direct I/O")
    print("=" * 50)

    with open(csv_file, "w") as f:
        f.write("rw,bs,iops,bw_KBps,lat_us\n")
        for rw in RW_MODES:
            for bs in bs_values:
                print(f"  Testing: rw={rw}, bs={bs} ...")
                result = run_fio(rw, bs, "psync", 1, 1, direct=False)
                if result:
                    f.write(f"{rw},{bs},{result[0]},{result[1]},{result[2]}\n")
                    f.flush()
                    print(f"    -> IOPS={result[0]:.0f}, BW={result[1]:.0f} KB/s")
                else:
                    print("    -> FAILED")

    cleanup()
    print(f"Experiment A done -> {csv_file}\n")


def experiment_b():
    """Concurrency impact. Fixed: bs=4k, ioengine=windowsaio, direct=1."""
    csv_file = "task2_jobs_depth_win.csv"
    nj_values = [1, 4, 8]
    id_values = [1, 16, 64]

    print("=" * 50)
    print(" Experiment B: numjobs x iodepth Impact")
    print(" Fixed: bs=4k, ioengine=windowsaio, direct=1")
    print("=" * 50)

    with open(csv_file, "w") as f:
        f.write("rw,numjobs,iodepth,iops,bw_KBps,lat_us\n")
        for rw in RW_MODES:
            for nj in nj_values:
                for iod in id_values:
                    print(f"  Testing: rw={rw}, numjobs={nj}, iodepth={iod} ...")
                    result = run_fio(rw, "4k", "windowsaio", nj, iod, direct=True)
                    if result:
                        f.write(f"{rw},{nj},{iod},{result[0]},{result[1]},{result[2]}\n")
                        f.flush()
                        print(f"    -> IOPS={result[0]:.0f}")
                    else:
                        print("    -> FAILED")

    cleanup()
    print(f"Experiment B done -> {csv_file}\n")


def experiment_c():
    """I/O engine comparison. Fixed: bs=4k, numjobs=1."""
    csv_file = "task2_ioengine_win.csv"

    # (engine, iodepth, use_direct)
    # psync:      sync, no direct on Windows
    # windowsaio: async, supports direct -> test depth=1 and depth=32
    # mmap:       sync-like, no direct on Windows
    # io_uring:   NOT available on Windows
    configs = [
        ("psync",      1,  False),
        ("windowsaio", 1,  True),
        ("windowsaio", 32, True),
        ("mmap",       1,  False),
    ]

    print("=" * 50)
    print(" Experiment C: I/O Engine Comparison")
    print(" Fixed: bs=4k, numjobs=1")
    print(" Windows engines: psync, windowsaio, mmap (no libaio/io_uring)")
    print("=" * 50)

    with open(csv_file, "w") as f:
        f.write("rw,ioengine,iodepth,direct,iops,bw_KBps,lat_us\n")
        for rw in RW_MODES:
            for eng, depth, use_d in configs:
                d_label = 1 if use_d else 0
                print(f"  Testing: rw={rw}, engine={eng}, iodepth={depth}, direct={d_label} ...")
                result = run_fio(rw, "4k", eng, 1, depth, direct=use_d)
                if result:
                    f.write(f"{rw},{eng},{depth},{d_label},{result[0]},{result[1]},{result[2]}\n")
                    f.flush()
                    print(f"    -> IOPS={result[0]:.0f}")
                else:
                    print("    -> Engine not supported, skipped")

    cleanup()
    print(f"Experiment C done -> {csv_file}\n")


def main():
    print("\n" + "=" * 50)
    print(" Task 2: Multi-parameter Analysis (Windows)")
    print(" This will take ~30 minutes.")
    print("=" * 50 + "\n")

    experiment_a()
    experiment_b()
    experiment_c()

    print("=" * 50)
    print(" All tests complete! Output files:")
    print("   task2_bs_win.csv")
    print("   task2_jobs_depth_win.csv")
    print("   task2_ioengine_win.csv")
    print("=" * 50)


if __name__ == "__main__":
    main()
