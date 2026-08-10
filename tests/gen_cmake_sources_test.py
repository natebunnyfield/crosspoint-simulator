#!/usr/bin/env python3
"""Guard tools/gen_cmake_sources.py against writing a source set nobody asked for.

cmake/CrossPointSources.cmake is the only thing telling the iOS build which
firmware sources to compile. The script that generates it used to resolve the
compile database's relative `file` paths against the PROCESS CWD rather than
against each entry's own `directory`, so running it from anywhere but the
firmware checkout filed all 125 firmware TUs as simulator sources, wrote an
empty CROSSPOINT_FW_SOURCES, and exited 0. This pins that fix and the guards
around it.

Every case builds a throwaway firmware tree and simulator tree, so nothing here
touches the real checkouts.

    python3 tests/gen_cmake_sources_test.py            # the committed script
    python3 tests/gen_cmake_sources_test.py <path>     # some other copy of it
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    REPO, "tools", "gen_cmake_sources.py"
)

SENTINEL = "# untouched\n"
N_FW = 130          # comfortably over the script's MIN_FIRMWARE_TUS floor
N_SIM = 20

failures = []


def check(name, ok, detail=""):
    print(f"{name:<34} {'PASS' if ok else 'FAIL'}")
    if not ok:
        failures.append(f"{name}: {detail}")
        if detail:
            for line in detail.splitlines()[:12]:
                print(f"    {line}")


def touch(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").close()


def make_trees(tmp, n_fw=N_FW, n_sim=N_SIM):
    """A fake firmware checkout and a fake simulator checkout, both populated."""
    fw = os.path.join(tmp, "fw")
    sim = os.path.join(tmp, "sim")
    for i in range(n_fw):
        touch(os.path.join(fw, "lib", f"fw{i:03d}.cpp"))
    for i in range(n_sim):
        touch(os.path.join(sim, "src", f"sim{i:02d}.cpp"))
    os.makedirs(os.path.join(fw, "include"), exist_ok=True)
    os.makedirs(os.path.join(sim, "cmake"), exist_ok=True)
    return fw, sim


def entry(directory, file_, extra=""):
    return {
        "directory": directory,
        "file": file_,
        "command": f"c++ -DSIMULATOR -Iinclude {extra} -c {file_}",
        "output": file_ + ".o",
    }


def healthy_db(fw, sim, n_fw=N_FW, n_sim=N_SIM):
    """What PlatformIO actually emits: firmware paths RELATIVE, sim paths absolute."""
    db = [entry(fw, os.path.join("lib", f"fw{i:03d}.cpp")) for i in range(n_fw)]
    db += [
        entry(fw, os.path.join(sim, "src", f"sim{i:02d}.cpp")) for i in range(n_sim)
    ]
    return db


def run(db, fw, sim, cwd, out):
    """Invoke the script under test; return (returncode, stdout+stderr)."""
    db_path = os.path.join(os.path.dirname(out), "compile_commands.json")
    with open(db_path, "w") as fh:
        json.dump(db, fh)
    proc = subprocess.run(
        [sys.executable, SCRIPT,
         "--firmware-dir", fw, "--simulator-dir", sim,
         "--compile-db", db_path, "--output", out],
        cwd=cwd, capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def fw_sources_of(path):
    text = open(path).read()
    block = text.split("set(CROSSPOINT_FW_SOURCES", 1)[1].split(")", 1)[0]
    return [l.strip() for l in block.splitlines() if l.strip()]


def case(fn):
    """Each case gets a clean tmp dir and a sentinel output file to protect."""
    def wrapper():
        tmp = tempfile.mkdtemp()
        try:
            out = os.path.join(tmp, "out", "CrossPointSources.cmake")
            os.makedirs(os.path.dirname(out))
            with open(out, "w") as fh:
                fh.write(SENTINEL)
            fn(tmp, out)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return wrapper


# --------------------------------------------------------------------------
# The happy path must keep working, from the documented cwd and from any other.
# --------------------------------------------------------------------------
@case
def test_happy_path_from_firmware_cwd(tmp, out):
    fw, sim = make_trees(tmp)
    rc, log = run(healthy_db(fw, sim), fw, sim, cwd=fw, out=out)
    listed = fw_sources_of(out) if rc == 0 else []
    check("happy path (cwd=firmware)",
          rc == 0 and len(listed) == N_FW and listed[0] == "lib/fw000.cpp",
          f"rc={rc} listed={len(listed)}\n{log}")


@case
def test_happy_path_is_cwd_independent(tmp, out):
    """THE regression test. Same database, run from the simulator repo.

    Pre-fix this exited 0 having written 0 firmware TUs and 150 simulator ones.
    """
    fw, sim = make_trees(tmp)
    rc, log = run(healthy_db(fw, sim), fw, sim, cwd=sim, out=out)
    listed = fw_sources_of(out) if rc == 0 else []
    check("cwd-independent (cwd=simulator)",
          rc == 0 and len(listed) == N_FW and listed[0] == "lib/fw000.cpp",
          f"rc={rc} listed={len(listed)}\n{log}")


@case
def test_happy_path_from_unrelated_cwd(tmp, out):
    """Pre-fix this wrote 130 firmware TUs whose paths were all `../../..` junk."""
    fw, sim = make_trees(tmp)
    rc, log = run(healthy_db(fw, sim), fw, sim, cwd=tempfile.gettempdir(), out=out)
    listed = fw_sources_of(out) if rc == 0 else []
    check("cwd-independent (cwd=elsewhere)",
          rc == 0 and len(listed) == N_FW and not any(p.startswith("..") for p in listed),
          f"rc={rc} listed={len(listed)}\n{log}")


# --------------------------------------------------------------------------
# Every bad database must fail LOUDLY and leave the previous file alone.
# --------------------------------------------------------------------------
def expect_refusal(name, tmp, out, db, fw, sim, needle, cwd=None):
    rc, log = run(db, fw, sim, cwd=cwd or fw, out=out)
    survived = open(out).read() == SENTINEL
    check(name,
          rc != 0 and needle in log and survived,
          f"rc={rc} sentinel_intact={survived} needle={needle!r}\n{log}")


@case
def test_zero_firmware_tus(tmp, out):
    """A database describing only simulator sources -- the 0-TU write itself."""
    fw, sim = make_trees(tmp)
    db = [entry(fw, os.path.join(sim, "src", f"sim{i:02d}.cpp")) for i in range(N_SIM)]
    expect_refusal("refuses 0 firmware TUs", tmp, out, db, fw, sim,
                   "0 firmware translation units")


@case
def test_empty_database(tmp, out):
    fw, sim = make_trees(tmp)
    expect_refusal("refuses an empty database", tmp, out, [], fw, sim,
                   "compile database is empty")


@case
def test_zero_simulator_tus(tmp, out):
    fw, sim = make_trees(tmp)
    db = [entry(fw, os.path.join("lib", f"fw{i:03d}.cpp")) for i in range(N_FW)]
    expect_refusal("refuses 0 simulator TUs", tmp, out, db, fw, sim,
                   "no simulator sources")


@case
def test_wrong_firmware_dir(tmp, out):
    """Database for tree A, --firmware-dir tree B: paths climb out of the tree."""
    fw, sim = make_trees(tmp)
    other = os.path.join(tmp, "other")
    os.makedirs(os.path.join(other, "include"), exist_ok=True)
    expect_refusal("refuses a mismatched tree", tmp, out,
                   healthy_db(fw, sim), other, sim, "OUTSIDE --firmware-dir")


@case
def test_stale_database(tmp, out):
    """Every path is under the tree, but one TU has since been deleted."""
    fw, sim = make_trees(tmp)
    db = healthy_db(fw, sim)
    os.remove(os.path.join(fw, "lib", "fw007.cpp"))
    expect_refusal("refuses a stale database", tmp, out, db, fw, sim,
                   "do not exist on disk")


@case
def test_partial_database(tmp, out):
    """All paths valid, count implausible -- an interrupted or half-built db."""
    fw, sim = make_trees(tmp)
    db = healthy_db(fw, sim)[:12] + healthy_db(fw, sim)[N_FW:]
    expect_refusal("refuses a partial database", tmp, out, db, fw, sim,
                   "firmware translation units (healthy is ~125")


@case
def test_no_include_dirs(tmp, out):
    """-I flags that resolve nowhere: the tree mismatch caught on another symptom."""
    fw, sim = make_trees(tmp)
    db = healthy_db(fw, sim)
    for e in db:
        e["command"] = e["command"].replace("-Iinclude", "")
    expect_refusal("refuses 0 include dirs", tmp, out, db, fw, sim,
                   "0 firmware include dirs")


@case
def test_malformed_database(tmp, out):
    fw, sim = make_trees(tmp)
    db_path = os.path.join(os.path.dirname(out), "compile_commands.json")
    with open(db_path, "w") as fh:
        fh.write("{ not json")
    proc = subprocess.run(
        [sys.executable, SCRIPT, "--firmware-dir", fw, "--simulator-dir", sim,
         "--compile-db", db_path, "--output", out],
        cwd=fw, capture_output=True, text=True,
    )
    log = proc.stdout + proc.stderr
    check("refuses malformed JSON",
          proc.returncode != 0 and "not valid JSON" in log
          and open(out).read() == SENTINEL,
          f"rc={proc.returncode}\n{log}")


@case
def test_error_names_the_fix(tmp, out):
    """House style: a guard says why it fired and the exact command to fix it."""
    fw, sim = make_trees(tmp)
    rc, log = run([], fw, sim, cwd=fw, out=out)
    check("error names the fix command",
          rc != 0 and "pio run -e simulator -t compiledb" in log
          and "gen_cmake_sources.py" in log and "Nothing was written" in log,
          f"rc={rc}\n{log}")


def main():
    print(f"gen_cmake_sources under test: {SCRIPT}\n")
    for fn in [
        test_happy_path_from_firmware_cwd,
        test_happy_path_is_cwd_independent,
        test_happy_path_from_unrelated_cwd,
        test_zero_firmware_tus,
        test_empty_database,
        test_zero_simulator_tus,
        test_wrong_firmware_dir,
        test_stale_database,
        test_partial_database,
        test_no_include_dirs,
        test_malformed_database,
        test_error_names_the_fix,
    ]:
        fn()

    print()
    if failures:
        print(f"{len(failures)} FAILED")
        return 1
    print("all passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
