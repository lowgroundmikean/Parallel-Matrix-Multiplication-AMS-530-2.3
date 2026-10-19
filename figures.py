"""
Figures for AMS 530 Project 2, Problem 2.3.

Four figures, each regenerable from data.py alone:

  fig1_speedup.png     speedup against process count, with the ideal bound
  fig2_efficiency.png  parallel efficiency against process count
  fig3_amdahl.png      Karp-Flatt serial fraction, both ways
  fig4_cache.png       per-rank throughput against L3 occupancy

Categorical palette: slots 1-4 of the validated reference order
(blue, orange, aqua, yellow).  Validated light-mode, adjacent pairlist:
worst CVD dE 9.1, worst normal-vision dE 22.9, all checks PASS.  Two
slots fall below 3:1 contrast on white, so the relief rule applies and
every series is additionally carried by a distinct marker, a distinct
dash pattern and a direct label; the paper's tables are the table view.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter, FuncFormatter

import data as d

# --- validated categorical slots 1-4 ---------------------------------
SERIES = {
    64:   "#2a78d6",   # slot 1 blue
    256:  "#eb6834",   # slot 2 orange
    1024: "#1baf7a",   # slot 3 aqua
    4096: "#eda100",   # slot 4 yellow
}
MARKER = {64: "o", 256: "s", 1024: "^", 4096: "D"}
DASH   = {64: (None, None), 256: (6, 2), 1024: (2, 1.6), 4096: (7, 2, 1.5, 2)}

INK      = "#0b0b0b"
INK_2    = "#52514e"
INK_MUTE = "#8a8984"
GRID     = "#e3e2de"
SURFACE  = "#ffffff"

plt.rcParams.update({
    "font.family":      "serif",
    "font.serif":       ["Liberation Serif", "DejaVu Serif"],
    "font.size":        9.5,
    "axes.edgecolor":   INK_MUTE,
    "axes.labelcolor":  INK,
    "axes.titlecolor":  INK,
    "xtick.color":      INK_2,
    "ytick.color":      INK_2,
    "axes.linewidth":   0.8,
    "figure.facecolor": SURFACE,
    "axes.facecolor":   SURFACE,
    "savefig.facecolor": SURFACE,
    "legend.frameon":   False,
})


def _style(ax, grid_axis="both"):
    ax.grid(True, axis=grid_axis, color=GRID, linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def _plot_series(ax, n, xs, ys, label=None, lw=1.8, ms=6.5):
    ax.plot(xs, ys,
            color=SERIES[n], marker=MARKER[n], markersize=ms,
            linewidth=lw, dashes=DASH[n],
            markeredgecolor=SURFACE, markeredgewidth=0.8,
            label=label if label else f"N = {n}", zorder=3)


# =====================================================================
def fig_speedup(path):
    fig, ax = plt.subplots(figsize=(6.3, 4.0))
    _style(ax)

    ps = [1] + d.PCOLS
    ax.plot(ps, ps, color=INK_MUTE, linewidth=1.1, dashes=(3, 3),
            zorder=2, label="ideal  S = P")

    for n in d.SIZES:
        ys = [1.0] + [d.speedup(n, p) for p in d.PCOLS]
        _plot_series(ax, n, ps, ys)
        ax.annotate(f"{ys[-1]:.2f}", (16, ys[-1]),
                    textcoords="offset points", xytext=(7, -1),
                    fontsize=8.5, color=INK_2, va="center")

    ax.set_xscale("log", base=2)
    ax.set_yscale("log", base=2)
    ax.xaxis.set_major_locator(FixedLocator(ps))
    ax.xaxis.set_major_formatter(FixedFormatter([str(p) for p in ps]))
    ax.yaxis.set_major_locator(FixedLocator([0.5, 1, 2, 4, 8, 16]))
    ax.yaxis.set_major_formatter(FixedFormatter(["0.5", "1", "2", "4", "8", "16"]))
    ax.set_xlim(0.9, 24)
    ax.set_ylim(0.45, 20)
    ax.set_xlabel("processes  P")
    ax.set_ylabel("speedup  S(P) = $T_1 / T_P$")
    ax.set_title("Speedup against the single-rank baseline", pad=9, fontsize=10.5)
    ax.legend(loc="upper left", fontsize=8.5, labelcolor=INK_2,
              handlelength=2.8, borderaxespad=0.6)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


# =====================================================================
def fig_efficiency(path):
    fig, ax = plt.subplots(figsize=(6.3, 4.0))
    _style(ax)

    ax.axhline(1.0, color=INK_MUTE, linewidth=1.1, dashes=(3, 3), zorder=2)
    ax.annotate("ideal  E = 1", (1.05, 1.0), textcoords="offset points",
                xytext=(2, 5), fontsize=8.5, color=INK_2)

    for n in d.SIZES:
        ys = [1.0] + [d.efficiency(n, p) for p in d.PCOLS]
        _plot_series(ax, n, [1] + d.PCOLS, ys)
        ax.annotate(f"{ys[-1]:.3f}", (16, ys[-1]),
                    textcoords="offset points", xytext=(7, -1),
                    fontsize=8.5, color=INK_2, va="center")

    ax.set_xscale("log", base=2)
    ax.xaxis.set_major_locator(FixedLocator([1] + d.PCOLS))
    ax.xaxis.set_major_formatter(FixedFormatter(["1", "4", "8", "16"]))
    ax.set_xlim(0.9, 24)
    ax.set_ylim(0, 1.15)
    ax.set_xlabel("processes  P")
    ax.set_ylabel("efficiency  E(P) = S(P) / P")
    ax.set_title("Parallel efficiency; the decline steepens as N falls",
                 pad=9, fontsize=10.5)
    ax.legend(loc="lower left", fontsize=8.5, labelcolor=INK_2,
              handlelength=2.8, borderaxespad=0.6)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


# =====================================================================
def fig_amdahl(path):
    """Karp-Flatt read both ways: down a column, and along a row."""
    fig, (axa, axb) = plt.subplots(1, 2, figsize=(7.2, 3.5))
    for ax in (axa, axb):
        _style(ax)

    # (a) e against N, one line per P.  Constant-f Amdahl predicts flat.
    pcol = {4: "#2a78d6", 8: "#eb6834", 16: "#1baf7a"}
    pmk  = {4: "o", 8: "s", 16: "^"}
    pdash = {4: (None, None), 8: (6, 2), 16: (2, 1.6)}
    for p in d.PCOLS:
        ys = [d.karp_flatt(n, p) for n in d.SIZES]
        axa.plot(d.SIZES, ys, color=pcol[p], marker=pmk[p], markersize=6.5,
                 linewidth=1.8, dashes=pdash[p], markeredgecolor=SURFACE,
                 markeredgewidth=0.8, label=f"P = {p}", zorder=3)
    axa.axhline(0, color=INK_MUTE, linewidth=0.8, zorder=1)
    axa.set_xscale("log", base=2)
    axa.xaxis.set_major_locator(FixedLocator(d.SIZES))
    axa.xaxis.set_major_formatter(FixedFormatter([f"$2^{{{n.bit_length()-1}}}$"
                                                  for n in d.SIZES]))
    axa.set_xlabel("matrix dimension  N")
    axa.set_ylabel("Karp-Flatt  e")
    axa.set_title("(a)  e collapses as N grows", pad=7, fontsize=10)
    axa.legend(loc="upper right", fontsize=8.5, labelcolor=INK_2,
               handlelength=2.6)

    # (b) e against P at fixed N.  A true serial section would be flat.
    for n in d.SIZES:
        ys = [d.karp_flatt(n, p) for p in d.PCOLS]
        axb.plot(d.PCOLS, ys, color=SERIES[n], marker=MARKER[n], markersize=6.5,
                 linewidth=1.8, dashes=DASH[n], markeredgecolor=SURFACE,
                 markeredgewidth=0.8, label=f"N = {n}", zorder=3)
    axb.axhline(0, color=INK_MUTE, linewidth=0.8, zorder=1)
    axb.set_xscale("log", base=2)
    axb.set_yscale("symlog", linthresh=0.01)
    axb.xaxis.set_major_locator(FixedLocator(d.PCOLS))
    axb.xaxis.set_major_formatter(FixedFormatter(["4", "8", "16"]))
    axb.set_xlim(3.4, 19)
    axb.set_xlabel("processes  P")
    axb.set_ylabel("Karp-Flatt  e   (symlog)")
    axb.set_title("(b)  e rises with P at every N", pad=7, fontsize=10)
    axb.legend(loc="lower right", fontsize=8.5, labelcolor=INK_2,
               handlelength=2.6)

    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


# =====================================================================
def fig_cache(path):
    """Per-rank throughput against the L3 pressure the replication creates."""
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    _style(ax)

    ax.axvline(1.0, color="#e34948", linewidth=1.3, dashes=(4, 2.5), zorder=2)
    ax.annotate("L3 capacity\n(35 MiB per socket)", (1.0, 9.6),
                textcoords="offset points", xytext=(6, 0),
                fontsize=8.5, color="#e34948", va="top")

    for n in d.SIZES:
        xs = [d.l3_occupancy(n, p) for p in [1] + d.PCOLS]
        ys = [d.gflops_rank(n, p) for p in [1] + d.PCOLS]
        _plot_series(ax, n, xs, ys, ms=7)
        for p, x, y in zip([1] + d.PCOLS, xs, ys):
            # P = 1 and P = 4 land on the same abscissa whenever
            # 3N^2 == 2 * 1.5N^2; label P = 1 below to keep them apart.
            dy, va = (-11.5, "top") if p == 1 else (8.5, "bottom")
            ax.annotate(f"{p}", (x, y), textcoords="offset points",
                        xytext=(0, dy), fontsize=7.5, color=INK_MUTE,
                        ha="center", va=va)

    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(
        lambda v, _: f"{v:g}" if v >= 0.01 else ""))
    ax.set_xlim(2e-3, 90)
    ax.set_ylim(0, 10.6)
    ax.set_xlabel("L3 occupancy per socket   "
                  r"$P_{\rm sock}\,(N^2 + 2N^2/P)\cdot 8\,$B $/$ 35 MiB")
    ax.set_ylabel("per-rank throughput  (GFLOP/s)")
    ax.set_title("Throughput against cache pressure; point labels give P",
                 pad=9, fontsize=10.5)
    ax.legend(loc="lower left", fontsize=8.5, labelcolor=INK_2,
              handlelength=2.8, borderaxespad=0.6)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


# =====================================================================
if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    fig_speedup(os.path.join(here, "fig1_speedup.png"))
    fig_efficiency(os.path.join(here, "fig2_efficiency.png"))
    fig_amdahl(os.path.join(here, "fig3_amdahl.png"))
    fig_cache(os.path.join(here, "fig4_cache.png"))
    print("figures written")
