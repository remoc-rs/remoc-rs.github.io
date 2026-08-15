#!/usr/bin/env python3
"""Draws the aggregation diagram on the Aggligator page.

Writes `_includes/aggligator-diagram.svg`, which the page inlines, so the colours
come from the site's CSS variables and light and dark mode work from the one file.

    python3 _tools/aggligator_diagram.py

Everything the picture says is in the block below; the rest is drawing.
"""

from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------- #
# What the picture shows                                                       #
# --------------------------------------------------------------------------- #


@dataclass
class Link:
    label: str  # what the link is
    chunks: int  # pieces of the stream it is carrying, so how much of the load it takes
    note: str = ""  # shown instead of the chunks when the link carries nothing
    down: bool = False  # drawn as a link that has failed


LINKS = [
    Link("Ethernet", 9),
    Link("Wi-Fi", 5),
    Link("USB", 7),
    Link("Bluetooth", 0, note="gone — its share moved to the others", down=True),
]

LEFT_TITLE = "Local endpoint"
RIGHT_TITLE = "Remote endpoint"
LINKS_TITLE = "Many links"

ENDPOINT_TYPE = "alc::Stream"
ENDPOINT_SUB = "AsyncRead + AsyncWrite"

BELOW_STRONG_1 = "one"
BELOW_MID = " connection, carried by "
BELOW_STRONG_2 = "every"
BELOW_END = " link that works"
BELOW_2 = "TCP, TLS, WebSockets, USB or Bluetooth, mixed freely and changed while it runs"

TITLE = "How Aggligator aggregates links"
DESC = (
    "Two programs, each holding one byte stream. Between them run four links: Ethernet, "
    "Wi-Fi and USB, each carrying part of the same stream, and a Bluetooth link that has "
    "failed and carries nothing, its share taken over by the others."
)

# --------------------------------------------------------------------------- #
# Drawing                                                                      #
# --------------------------------------------------------------------------- #

W, H = 960, 330
BOX_W, BOX_H, BOX_Y = 210, 232, 44
LEFT_BOX_X, RIGHT_BOX_X = 0, W - BOX_W
MID_Y = BOX_Y + BOX_H / 2

END_INSET, END_H = 16, 64  # the stream box inside an endpoint

LANE_X0, LANE_X1 = 250, W - 250
LANE_H, LANE_PAD = 34, 22
LABEL_W = 118  # room for the link's name at the left of its lane
LANE_PAD_X = 12

CHUNK_W, CHUNK_H, CHUNK_GAP = 12, 16, 6

SANS = "Inter, system-ui, sans-serif"
MONO = "'JetBrains Mono', ui-monospace, monospace"


def lane_y(i: int) -> float:
    """Vertical centre of lane `i`."""
    total = len(LINKS) * LANE_H + (len(LINKS) - 1) * LANE_PAD
    top = MID_Y - total / 2
    return top + i * (LANE_H + LANE_PAD) + LANE_H / 2


def svg() -> str:
    out = [
        f'<svg viewBox="0 0 {W} {H}" role="img" aria-labelledby="agg-title agg-desc"',
        '     xmlns="http://www.w3.org/2000/svg" class="diagram-svg">',
        f'  <title id="agg-title">{TITLE}</title>',
        f'  <desc id="agg-desc">{DESC}</desc>',
    ]

    # The two endpoints, each holding the single stream the links add up to.
    for x, title in ((LEFT_BOX_X, LEFT_TITLE), (RIGHT_BOX_X, RIGHT_TITLE)):
        out.append(
            f'  <rect x="{x + 0.5}" y="{BOX_Y + 0.5}" width="{BOX_W - 1}" height="{BOX_H - 1}" rx="12"'
            f' fill="var(--bg-alt)" stroke="var(--border)"/>'
        )
        out.append(
            f'  <text x="{x + BOX_W / 2}" y="{BOX_Y - 10}" text-anchor="middle"'
            f' font-family="{SANS}" font-size="16" font-weight="600" fill="var(--fg-muted)">{title}</text>'
        )
        out.append(
            f'  <rect x="{x + END_INSET}" y="{MID_Y - END_H / 2}" width="{BOX_W - 2 * END_INSET}"'
            f' height="{END_H}" rx="8" fill="none" stroke="var(--accent)" stroke-width="1.5"/>'
        )
        out.append(
            f'  <text x="{x + BOX_W / 2}" y="{MID_Y - 4}" text-anchor="middle"'
            f' font-family="{MONO}" font-size="14" fill="var(--fg)">{ENDPOINT_TYPE}</text>'
        )
        out.append(
            f'  <text x="{x + BOX_W / 2}" y="{MID_Y + 17}" text-anchor="middle"'
            f' font-family="{MONO}" font-size="11" fill="var(--fg-muted)">{ENDPOINT_SUB}</text>'
        )

    out.append(
        f'  <text x="{(LANE_X0 + LANE_X1) / 2}" y="{BOX_Y - 10}" text-anchor="middle"'
        f' font-family="{SANS}" font-size="16" font-weight="600" fill="var(--fg-muted)">{LINKS_TITLE}</text>'
    )

    # One lane per link, joined to the stream box at each end.
    left_edge = LEFT_BOX_X + BOX_W - END_INSET
    right_edge = RIGHT_BOX_X + END_INSET
    for i, link in enumerate(LINKS):
        y = lane_y(i)
        colour = "--border" if link.down else "--accent"
        dash = ' stroke-dasharray="5 5"' if link.down else ""

        out.append(
            f'  <rect x="{LANE_X0}" y="{y - LANE_H / 2}" width="{LANE_X1 - LANE_X0}" height="{LANE_H}"'
            f' rx="8" fill="{"none" if link.down else "var(--bg-alt)"}" stroke="var({colour})"'
            f' stroke-width="1.5"{dash}/>'
        )
        out.append(
            f'  <text x="{LANE_X0 + LANE_PAD_X}" y="{y + 5}" font-family="{SANS}" font-size="14"'
            f' fill="var({"--fg-muted" if link.down else "--fg"})">{link.label}</text>'
        )

        chunk_x = LANE_X0 + LANE_PAD_X + LABEL_W
        for n in range(link.chunks):
            out.append(
                f'  <rect x="{chunk_x + n * (CHUNK_W + CHUNK_GAP)}" y="{y - CHUNK_H / 2}"'
                f' width="{CHUNK_W}" height="{CHUNK_H}" rx="2" fill="var(--accent)"/>'
            )
        if link.note:
            out.append(
                f'  <text x="{chunk_x}" y="{y + 4}" font-family="{SANS}" font-size="12.5"'
                f' fill="var(--fg-muted)">{link.note}</text>'
            )

        # Both ends of the lane run back into the one stream.
        out.append(
            f'  <path d="M {left_edge},{MID_Y} C {left_edge + 30},{MID_Y}'
            f' {LANE_X0 - 30},{y} {LANE_X0},{y}" fill="none" stroke="var({colour})"'
            f' stroke-width="2"{dash}/>'
        )
        out.append(
            f'  <path d="M {LANE_X1},{y} C {LANE_X1 + 30},{y}'
            f' {right_edge - 30},{MID_Y} {right_edge},{MID_Y}" fill="none" stroke="var({colour})"'
            f' stroke-width="2"{dash}/>'
        )

    mid_x = W / 2
    out.append(
        f'  <text x="{mid_x}" y="{BOX_Y + BOX_H + 26}" text-anchor="middle" font-family="{SANS}"'
        f' font-size="15" fill="var(--fg-muted)">'
        f'<tspan font-weight="700" fill="var(--fg)">{BELOW_STRONG_1}</tspan>{BELOW_MID}'
        f'<tspan font-weight="700" fill="var(--fg)">{BELOW_STRONG_2}</tspan>{BELOW_END}</text>'
    )
    out.append(
        f'  <text x="{mid_x}" y="{BOX_Y + BOX_H + 48}" text-anchor="middle" font-family="{SANS}"'
        f' font-size="13" fill="var(--fg-muted)">{BELOW_2}</text>'
    )

    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    includes = Path(__file__).resolve().parent.parent / "_includes"
    path = includes / "aggligator-diagram.svg"
    path.write_text(svg())
    print(f"wrote {path}")
