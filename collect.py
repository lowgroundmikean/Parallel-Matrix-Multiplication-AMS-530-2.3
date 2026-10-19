#!/usr/bin/env python3
"""
collect.py -- AMS 530 Project 2, Problem 2.3

Reads the RESULT lines emitted by matmul_mpi and prints

  (1) the timing table in the shape required by the assignment,
  (2) speedup and efficiency against the P = 1 baseline,
  (3) the Karp-Flatt metric, which is the quantity that makes the
      Amdahl's-law discussion quantitative rather than hand-waved,
  (4) a markdown version of each table, ready to paste into the report.

Usage:  python3 collect.py matmul23_<jobid>.out
        python3 collect.py *.out
"""

import re
import sys
from collections import defaultdict

LINE = re.compile(
    r"RESULT\s+N=(\d+)\s+P=(\d+)\s+t_par=([\d.eE+-]+)\s+t_dist=([\d.eE+-]+)"
    r"\s+t_comp=([\d.eE+-]+)\s+t_gath=([\d.eE+-]+)\s+t_serlocal=([\d.eE+-]+)"
    r"\s+relerr=([\d.eE+-]+)\s+verify=(\w+)"
)

PCOLS = [4, 8, 16]          # the columns the assignment asks for


def parse(paths):
    runs = {}
    for path in paths:
        with open(path) as fh:
            for line in fh:
                m = LINE.search(line)
                if not m:
                    continue
                n, p = int(m.group(1)), int(m.group(2))
                runs[(n, p)] = {
                    "t_par":   float(m.group(3)),
                    "t_dist":  float(m.group(4)),
                    "t_comp":  float(m.group(5)),
                    "t_gath":  float(m.group(6)),
                    "t_ser":   float(m.group(7)),
                    "relerr":  float(m.group(8)),
                    "verify":  m.group(9),
                }
    return runs


def rule(width=78):
    print("-" * width)


def table(title, header, rows, md_name=None):
    print()
    print(title)
    rule()
    print(header)
    rule()
    for r in rows:
        print(r)
    rule()
    if md_name:
        print(f"\n[markdown: {md_name}]")


def main(paths):
    runs = parse(paths)
    if not runs:
        sys.exit("no RESULT lines found in: " + " ".join(paths))

    sizes = sorted({n for n, _ in runs})

    # ---- correctness first.  A speedup number from a wrong answer is noise.
    bad = [(n, p, d["verify"], d["relerr"])
           for (n, p), d in sorted(runs.items()) if d["verify"] == "FAIL"]
    skipped = [(n, p) for (n, p), d in sorted(runs.items())
               if d["verify"] == "SKIP"]
    print("VERIFICATION")
    rule()
    if bad:
        for n, p, v, e in bad:
            print(f"  FAILED  N={n:<6} P={p:<3} relative error {e:.3e}")
    else:
        checked = sum(1 for d in runs.values() if d["verify"] == "PASS")
        worst = max((d["relerr"] for d in runs.values()
                     if d["verify"] == "PASS"), default=0.0)
        print(f"  all {checked} verified runs agree with the serial result")
        print(f"  largest relative error observed: {worst:.3e}")
        if worst == 0.0:
            print("  (exactly zero: the row decomposition preserves the order")
            print("   of the k-summation, so the results agree bit for bit)")
    if skipped:
        print(f"  verification skipped for {len(skipped)} run(s)")

    # ---- Table 1: wall-clock time, the shape the assignment asks for.
    hdr = f"{'N':>8} | " + " | ".join(f"P = 2^{p.bit_length()-1:<2} ".rjust(12)
                                      for p in PCOLS)
    rows = []
    for n in sizes:
        cells = []
        for p in PCOLS:
            d = runs.get((n, p))
            cells.append(f"{d['t_par']:12.6f}" if d else f"{'--':>12}")
        rows.append(f"{n:>8} | " + " | ".join(cells))
    table("TABLE 1.  Parallel wall-clock time, seconds "
          "(max over ranks, best of the timed repetitions)",
          hdr, rows)

    # ---- Table 2: speedup against the P = 1 run.
    hdr = (f"{'N':>8} | {'T_1 (s)':>12} | "
           + " | ".join(f"S(P={p})".rjust(10) for p in PCOLS))
    rows = []
    for n in sizes:
        base = runs.get((n, 1))
        if not base:
            rows.append(f"{n:>8} | {'no P=1 run':>12} | "
                        + " | ".join(f"{'--':>10}" for _ in PCOLS))
            continue
        t1 = base["t_par"]
        cells = []
        for p in PCOLS:
            d = runs.get((n, p))
            cells.append(f"{t1 / d['t_par']:10.3f}" if d else f"{'--':>10}")
        rows.append(f"{n:>8} | {t1:12.6f} | " + " | ".join(cells))
    table("TABLE 2.  Speedup  S(P) = T_1 / T_P", hdr, rows)

    # ---- Table 3: efficiency.
    hdr = f"{'N':>8} | " + " | ".join(f"E(P={p})".rjust(10) for p in PCOLS)
    rows = []
    for n in sizes:
        base = runs.get((n, 1))
        if not base:
            continue
        t1 = base["t_par"]
        cells = []
        for p in PCOLS:
            d = runs.get((n, p))
            cells.append(f"{t1 / d['t_par'] / p:10.3f}" if d else f"{'--':>10}")
        rows.append(f"{n:>8} | " + " | ".join(cells))
    table("TABLE 3.  Efficiency  E(P) = S(P) / P", hdr, rows)

    # ---- Table 4: Karp-Flatt.  The experimentally determined serial fraction.
    #
    #   Amdahl:      S(P) <= 1 / ( f + (1-f)/P )
    #   Karp-Flatt:  e    = (1/S - 1/P) / (1 - 1/P)
    #
    # e is Amdahl's f solved for from the measured speedup.  If the only
    # obstacle to scaling were a genuinely serial section of fixed size, e
    # would come out the same at every P.  Where e climbs with P the extra
    # cost is parallel overhead, not a serial section, and Amdahl's law with
    # a constant f is simply the wrong model.
    hdr = f"{'N':>8} | " + " | ".join(f"e(P={p})".rjust(10) for p in PCOLS)
    rows = []
    for n in sizes:
        base = runs.get((n, 1))
        if not base:
            continue
        t1 = base["t_par"]
        cells = []
        for p in PCOLS:
            d = runs.get((n, p))
            if not d or p == 1:
                cells.append(f"{'--':>10}")
                continue
            s = t1 / d["t_par"]
            e = (1.0 / s - 1.0 / p) / (1.0 - 1.0 / p)
            cells.append(f"{e:10.4f}")
        rows.append(f"{n:>8} | " + " | ".join(cells))
    table("TABLE 4.  Karp-Flatt metric  e = (1/S - 1/P) / (1 - 1/P)\n"
          "          the serial fraction implied by the measured speedup",
          hdr, rows)

    # ---- Table 5: where the time actually goes.
    hdr = (f"{'N':>7} {'P':>4} | {'distribute':>11} {'compute':>11} "
           f"{'gather':>11} | {'comm %':>8}")
    rows = []
    for n in sizes:
        for p in [1] + PCOLS:
            d = runs.get((n, p))
            if not d:
                continue
            comm = d["t_dist"] + d["t_gath"]
            frac = 100.0 * comm / d["t_par"] if d["t_par"] > 0 else 0.0
            rows.append(f"{n:>7} {p:>4} | {d['t_dist']:11.6f} "
                        f"{d['t_comp']:11.6f} {d['t_gath']:11.6f} | "
                        f"{frac:7.1f}%")
    table("TABLE 5.  Breakdown of the parallel phase, seconds", hdr, rows)

    # ---- Markdown for the report.
    print()
    print("=" * 78)
    print("MARKDOWN FOR THE REPORT")
    print("=" * 78)
    print()
    print("Table: parallel wall-clock time in seconds, with speedup in "
          "parentheses.")
    print()
    print("| N | " + " | ".join(f"P = 2^{p.bit_length()-1}" for p in PCOLS)
          + " |")
    print("|---|" + "|".join("---" for _ in PCOLS) + "|")
    for n in sizes:
        base = runs.get((n, 1))
        t1 = base["t_par"] if base else None
        cells = []
        for p in PCOLS:
            d = runs.get((n, p))
            if not d:
                cells.append("--")
            elif t1:
                cells.append(f"{d['t_par']:.4f} ({t1 / d['t_par']:.2f}x)")
            else:
                cells.append(f"{d['t_par']:.4f}")
        print(f"| 2^{n.bit_length()-1} | " + " | ".join(cells) + " |")

    # ---- The sentences that Table 4 licenses.
    print()
    print("=" * 78)
    print("WHAT THE NUMBERS SAY ABOUT AMDAHL'S LAW")
    print("=" * 78)
    for n in sizes:
        base = runs.get((n, 1))
        if not base:
            continue
        t1 = base["t_par"]
        es = []
        for p in PCOLS:
            d = runs.get((n, p))
            if d:
                s = t1 / d["t_par"]
                es.append((p, (1.0 / s - 1.0 / p) / (1.0 - 1.0 / p)))
        if not es:
            continue
        lo, hi = min(e for _, e in es), max(e for _, e in es)
        trend = ("rises with P"   if es[-1][1] > es[0][1] * 1.3 else
                 "falls with P"   if es[-1][1] < es[0][1] * 0.7 else
                 "flat in P")
        ceiling = (1.0 / lo) if lo > 0 else float("inf")
        print(f"\n  N = {n}")
        print(f"    e ranges {lo:.4f} to {hi:.4f}, {trend}")
        if lo > 0:
            print(f"    implied Amdahl ceiling at e = {lo:.4f}: "
                  f"S_inf = 1/e = {ceiling:.1f}x")
        else:
            print("    e <= 0: measured speedup exceeds P "
                  "(check cache effects in the P=1 baseline)")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
