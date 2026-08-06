#!/usr/bin/env python3
"""Draws the two benchmark figures shown on the benchmarks page.

The benchmark suite lives in the Remoc repository, together with its own `plot.py`
that draws every layer and codec -- what an analysis needs, and what a web page
cannot carry. This script reduces the same report to one question, namely how close
a Remoc channel gets to a plain TCP connection doing the same work, and styles it to
match the site, in a light and a dark variant.

Usage:
    pip install matplotlib
    python3 _tools/plot_web.py path/to/results.json

The report comes from the benchmark suite:
    cd ../remoc/bench/perf && cargo run --release -- --out results.json
"""

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    sys.exit("matplotlib is required: pip install matplotlib")


# Where the figures go, relative to this script: the plots directory the site serves.
DEFAULT_OUTDIR = Path(__file__).resolve().parent.parent / "plots"

# Display names of the emulated links.
LINK_NAMES = {"lan": "LAN", "wifi": "Wi-Fi", "lte": "LTE", "wan": "WAN"}

# The layer sending records over a plain socket, and the Remoc channel shown next to
# it. The page explains what they are, so the legend stays this short.
REFERENCE_LAYER = "tcp_struct_{codec}"
REMOC_LAYER = "mpsc_struct_par4_{codec}"
REFERENCE_LABEL = "plain TCP"
REMOC_LABEL = "Remoc MPSC"

# The layer everything is measured against: a socket moving bytes and nothing else.
BASELINE_LAYER = "raw_tcp"
BASELINE_LABEL = "raw TCP, nothing serialized"

REMOC_PINK = "#ff3fa4"

# Font stack of the site. An SVG shown in an `img` element cannot load a web font, so
# these are resolved against what the reader has installed, with a fallback that any
# system provides.
FONT_STACK = "Inter, system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

# The two variants, following the page's own colours.
THEMES = {
    "light": dict(fg="#1b1a1f", muted="#5c5a66", grid="#d9d4da", reference="#9a95a3"),
    "dark": dict(fg="#ecebf0", muted="#a5a1b0", grid="#3a3742", reference="#78737f"),
}


def load(path):
    with open(path) as f:
        report = json.load(f)

    runs = report["runs"]
    links = list(OrderedDict.fromkeys(r["link"] for r in runs))
    sizes = sorted({r["msg_size"] for r in runs})
    return report, runs, links, sizes


def series(runs, link, layer, sizes, field):
    by_size = {r["msg_size"]: r[field] for r in runs if r["link"] == link and r["layer"] == layer}
    return [by_size.get(s) for s in sizes]


def link_title(runs, link):
    limit = next(r["mbytes_per_s_limit"] for r in runs if r["link"] == link)
    rtt = next(r["rtt_ms"] for r in runs if r["link"] == link)
    return f"{LINK_NAMES.get(link, link.upper())}  ·  {limit:.0f} MB/s  ·  {rtt:.0f} ms"


def items(size, record_bytes):
    """Records that a message of `size` encoded bytes carries."""
    return max(1, size // record_bytes)


def count(value):
    """A large number as it would be read out, rather than in full."""
    if value >= 1e6:
        text = f"{value / 1e6:.1f}".rstrip("0").rstrip(".")
        return f"{text}M"
    if value >= 1e3:
        return f"{value / 1e3:.0f}k"
    return f"{value:.0f}"


def panels(links, theme):
    fig, axes = plt.subplots(2, 2, figsize=(10.0, 6.6), squeeze=False)
    flat = [axes[i // 2][i % 2] for i in range(len(links))]

    for ax in flat:
        ax.set_facecolor("none")
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(theme["grid"])
        ax.tick_params(colors=theme["muted"], length=0)

    fig.patch.set_alpha(0.0)
    return fig, flat


def finish(fig, axes, theme, out, handles=None):
    handles = handles or axes[0].get_legend_handles_labels()[0]
    labels = [h.get_label() for h in handles]
    legend = fig.legend(handles, labels, loc="lower center", ncol=len(labels), frameon=False,
                        handletextpad=0.6, columnspacing=2.0)
    for text in legend.get_texts():
        text.set_color(theme["fg"])

    fig.tight_layout(rect=(0, 0.06, 1, 1), h_pad=2.5, w_pad=3.0)
    fig.savefig(out, transparent=True)
    if out.suffix == ".svg":
        restyle(out)
    print(f"Wrote {out}")


def restyle(path):
    """Replaces the font matplotlib measured with the stack the site asks for.

    The metrics come from whatever font was available while plotting, so the text may
    sit a little loosely, which is preferable to shipping a font inside every figure.
    """
    svg = path.read_text()
    svg = re.sub(r"font-family:[^;\"]*(?=[;\"])", f"font-family:{FONT_STACK}", svg)
    path.write_text(svg)


def plot_records(runs, links, sizes, reference, remoc, record_bytes, theme, out):
    """Records per second against the number of records per message."""
    fig, axes = panels(links, theme)
    x = [items(s, record_bytes) for s in sizes]

    for ax, link in zip(axes, links):
        ax.plot(x, series(runs, link, reference, sizes, "records_per_s"),
                label=REFERENCE_LABEL, color=theme["reference"], linestyle="--", marker="s",
                markersize=5, linewidth=1.6)
        ax.plot(x, series(runs, link, remoc, sizes, "records_per_s"),
                label=REMOC_LABEL, color=REMOC_PINK, marker="o", markersize=5.5, linewidth=2.2)

        top = max(v for v in series(runs, link, reference, sizes, "records_per_s") if v)
        ax.set_ylim(0, top * 1.18)
        ax.set_yticks([t for t in ax.get_yticks() if 0 <= t <= top * 1.18])
        ax.set_yticklabels([count(t) for t in ax.get_yticks()])
        ax.set_ylabel("records/s", color=theme["muted"])

        ax.set_xscale("log", base=2)
        ax.set_xlim(x[0] / 1.3, x[-1] * 1.3)
        ax.set_xticks(x)
        ax.set_xticklabels([str(v) for v in x])
        ax.set_xticks([], minor=True)
        ax.set_xlabel("records per message", color=theme["muted"])

        ax.set_title(link_title(runs, link), color=theme["fg"], fontsize=11, pad=10)
        ax.grid(True, axis="y", color=theme["grid"], alpha=0.6, linewidth=0.8)
        ax.set_axisbelow(True)

    finish(fig, axes, theme, out)


def plot_share(runs, links, sizes, reference, remoc, record_bytes, theme, out):
    """Throughput as a share of what a raw TCP transfer reaches on the same link."""
    fig, axes = panels(links, theme)
    labels = [str(items(s, record_bytes)) for s in sizes]
    positions = range(len(sizes))
    width = 0.38
    handles = None

    for ax, link in zip(axes, links):
        drawn = [(reference, REFERENCE_LABEL, theme["reference"], -0.5),
                 (remoc, REMOC_LABEL, REMOC_PINK, 0.5)]
        bars = []
        for layer, label, color, offset in drawn:
            values = [(v or 0) * 100 for v in series(runs, link, layer, sizes, "fraction_of_baseline")]
            bars.append(ax.bar([p + offset * width for p in positions], values, width=width,
                               label=label, color=color))

        line = ax.axhline(100, color=theme["muted"], linestyle=":", linewidth=1,
                          label=BASELINE_LABEL)
        handles = handles or [*bars, line]

        ax.set_ylim(0, 112)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.set_yticklabels(["0", "25", "50", "75", "100"])
        ax.set_ylabel("% of raw TCP", color=theme["muted"])

        ax.set_xticks(list(positions))
        ax.set_xticklabels(labels)
        ax.set_xlabel("records per message", color=theme["muted"])

        ax.set_title(link_title(runs, link), color=theme["fg"], fontsize=11, pad=10)
        ax.grid(True, axis="y", color=theme["grid"], alpha=0.6, linewidth=0.8)
        ax.set_axisbelow(True)

    finish(fig, axes, theme, out, handles)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path, help="JSON written by the benchmark")
    parser.add_argument("--codec", default="postbag", help="codec to show")
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    args = parser.parse_args()

    report, runs, links, sizes = load(args.results)
    record_bytes = report.get("sample_bytes", {}).get(args.codec)
    if not record_bytes:
        sys.exit(f"the report has no {args.codec} results")

    reference = REFERENCE_LAYER.format(codec=args.codec)
    remoc = REMOC_LAYER.format(codec=args.codec)
    for layer in (BASELINE_LAYER, reference, remoc):
        if not any(r["layer"] == layer for r in runs):
            sys.exit(f"the report has no {layer} results")

    args.outdir.mkdir(parents=True, exist_ok=True)

    for name, theme in THEMES.items():
        suffix = "" if name == "light" else "-dark"
        with plt.rc_context({"svg.fonttype": "none", "font.size": 10,
                             "text.color": theme["fg"], "axes.labelcolor": theme["muted"]}):
            plot_records(runs, links, sizes, reference, remoc, record_bytes, theme,
                         args.outdir / f"records{suffix}.svg")
            plot_share(runs, links, sizes, reference, remoc, record_bytes, theme,
                       args.outdir / f"share{suffix}.svg")


if __name__ == "__main__":
    main()
