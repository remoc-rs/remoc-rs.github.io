#!/usr/bin/env python3
"""Draws the pipelining diagram on the home page.

Writes `_includes/diagram-pipelining.svg`, which the page inlines, so the colours
come from the site's CSS variables and light and dark mode work from the one file.

    python3 _tools/pipelining_diagram.py

Everything the picture says is in the block below; the rest is drawing.
"""

from dataclasses import dataclass, field
from math import atan2, degrees, hypot
from pathlib import Path

# --------------------------------------------------------------------------- #
# What the picture shows                                                       #
# --------------------------------------------------------------------------- #


@dataclass
class Frame:
    title: str  # the sentence above the frame
    calls: list[tuple[str, str]]  # the requests as (receiver, call), in the order made
    spread: float  # delay between two requests, in one-way trip times
    server_note: str  # what happens on the server when the first request lands
    span: str  # the label under the bracket measuring the exchange
    labelled: dict[int, str] = field(default_factory=dict)  # labels on replies
    bundle: tuple[str, str] | None = None  # labels for the outgoing and returning group


# The receiver is carried in the label because the first call is made on the directory
# and the rest on the counter it hands out, which the arrows alone do not say.
CALLS = [
    ("dir.", "open_counter(\"mine\")"),
    ("counter.", "increase(20)"),
    ("counter.", "increase(45)"),
    ("counter.", "value()"),
]

FRAMES = [
    Frame(
        title="Ordinarily: each call waits for the result of the one before it",
        calls=CALLS,
        spread=2.0,  # the next request leaves only once the previous reply is in
        server_note="counter created",
        span="4 round trips",
        labelled={0: "CounterClient"},
    ),
    Frame(
        title="Pipelined: every call is sent before any result is awaited",
        calls=CALLS,
        spread=0.14,  # one behind the other, as fast as they can be written
        server_note="counter attached, queued calls run",
        span="1 round trip",
        bundle=("all four requests", "all four results"),
    ),
]

CLIENT, SERVER = "Client", "Server"

TITLE = "What pipelining saves"
DESC = (
    "Two frames, each showing a client timeline above a server timeline with requests "
    "travelling down to the server and results back up. In the first, a call on the "
    "directory hands out a counter and three further calls are then made on that counter, "
    "each waiting for the previous result, so the exchange takes four round trips and fills "
    "the width of the picture. In the second, the same four calls leave together and their "
    "results come back together, so the exchange takes one round trip and occupies a "
    "quarter of the width."
)

# --------------------------------------------------------------------------- #
# Drawing                                                                      #
# --------------------------------------------------------------------------- #

W = 960
T0 = 96  # x of time zero; the lane labels sit to the left of it
RIGHT_PAD = 8
UNITS = 8  # one-way trip times spanned by the widest frame
UNIT = (W - T0 - RIGHT_PAD) / UNITS

# Baselines within a frame, relative to the client timeline.
TITLE_DY = -52
CALL_DY = -16
SERVER_DY = 96
NOTE_DY = SERVER_DY + 20
BRACKET_DY = SERVER_DY + 42
SPAN_DY = SERVER_DY + 63

FRAME_Y = [78, 347]
H = FRAME_Y[-1] + SPAN_DY + 18

REQ, REP = "--accent", "--ty"

HEAD = 8  # length of an arrowhead, measured back from its tip
TAIL_GAP = 6  # how far a message starts clear of where the previous one landed

SANS = "Inter, system-ui, sans-serif"
MONO = "'JetBrains Mono', ui-monospace, monospace"


def x_at(t: float) -> float:
    """x of time `t`, measured in one-way trip times."""
    return T0 + t * UNIT


def timeline(y: float, label: str) -> list[str]:
    """A labelled horizontal line, running the width of the picture."""
    return [
        f'  <line x1="{T0}" y1="{y}" x2="{W - RIGHT_PAD}" y2="{y}" stroke="var(--border)"'
        f' stroke-width="1.5"/>',
        f'  <text x="{T0 - 14}" y="{y + 5}" text-anchor="end" font-family="{SANS}"'
        f' font-size="14" font-weight="600" fill="var(--fg-muted)">{label}</text>',
    ]


def message(t0: float, y0: float, t1: float, y1: float, colour: str) -> list[str]:
    """A message in flight: a line from (t0, y0) to (t1, y1), tipped with an arrowhead.

    The tip lands on the timeline rather than crossing it, and the tail starts a little
    way along, so that a message and the one it triggers do not meet at a point.
    """
    x0, x1 = x_at(t0), x_at(t1)
    dx, dy = x1 - x0, y1 - y0
    ux, uy = dx / hypot(dx, dy), dy / hypot(dx, dy)
    tail_x, tail_y = x0 + ux * TAIL_GAP, y0 + uy * TAIL_GAP
    angle = degrees(atan2(dy, dx))
    return [
        f'  <line x1="{tail_x:.1f}" y1="{tail_y:.1f}" x2="{x1:.1f}" y2="{y1}"'
        f' stroke="var({colour})" stroke-width="2"/>',
        f'  <path d="M {x1 - HEAD:.1f},{y1 - 4.5} L {x1:.1f},{y1} L {x1 - HEAD:.1f},{y1 + 4.5} Z"'
        f' fill="var({colour})" transform="rotate({angle:.1f} {x1:.1f} {y1})"/>',
    ]


def bracket(t0: float, t1: float, y: float, label: str) -> list[str]:
    """A span measuring how long the exchange took, with its label centred under it."""
    x0, x1 = x_at(t0), x_at(t1)
    return [
        f'  <path d="M {x0:.1f},{y - 5} L {x0:.1f},{y + 5} M {x0:.1f},{y} L {x1:.1f},{y}'
        f' M {x1:.1f},{y - 5} L {x1:.1f},{y + 5}" stroke="var(--fg-muted)" stroke-width="1.5"'
        f' fill="none"/>',
        f'  <text x="{(x0 + x1) / 2:.1f}" y="{y + 21}" text-anchor="middle" font-family="{SANS}"'
        f' font-size="14" font-weight="600" fill="var(--fg)">{label}</text>',
    ]


def frame(top: float, f: Frame) -> list[str]:
    """One exchange: the two timelines, the messages between them and the span below."""
    client_y, server_y = top, top + SERVER_DY
    out = [
        f'  <text x="0" y="{top + TITLE_DY}" font-family="{SANS}" font-size="15"'
        f' font-weight="600" fill="var(--fg)">{f.title}</text>'
    ]
    out += timeline(client_y, CLIENT)
    out += timeline(server_y, SERVER)

    # Each call leaves `spread` after the one before it and is answered on arrival.
    for i, (receiver, call) in enumerate(f.calls):
        sent = i * f.spread
        out += message(sent, client_y, sent + 1, server_y, REQ)
        out += message(sent + 1, server_y, sent + 2, client_y, REP)

        if f.bundle is None:
            out.append(
                f'  <text x="{x_at(sent):.1f}" y="{client_y + CALL_DY}" font-family="{MONO}"'
                f' font-size="12.5" fill="var(--fg)">'
                f'<tspan font-size="11" fill="var(--fg-muted)">{receiver}</tspan>{call}</text>'
            )

        # A reply worth naming: the one the following calls are waiting for. It sits
        # below the midpoint, in the clear triangle between this reply and the next
        # request, rather than on the line it names.
        if label := f.labelled.get(i):
            out.append(
                f'  <text x="{x_at(sent + 2):.1f}" y="{(client_y + server_y) / 2 + 30}"'
                f' text-anchor="middle" font-family="{MONO}" font-size="12.5"'
                f' fill="var({REP})">{label}</text>'
            )

    last = (len(f.calls) - 1) * f.spread

    # When the messages are too close together to label one by one, name the group.
    if f.bundle is not None:
        going, coming = f.bundle
        out.append(
            f'  <text x="{x_at(last + 0.25):.1f}" y="{client_y + CALL_DY}" font-family="{SANS}"'
            f' font-size="13.5" fill="var({REQ})">{going}</text>'
        )
        out.append(
            f'  <text x="{x_at(last + 2) + 14:.1f}" y="{client_y + 5}" font-family="{SANS}"'
            f' font-size="13.5" fill="var({REP})">{coming}</text>'
        )

    out.append(
        f'  <text x="{x_at(1):.1f}" y="{top + NOTE_DY}" font-family="{SANS}" font-size="12.5"'
        f' fill="var(--fg-muted)">{f.server_note}</text>'
    )
    out += bracket(0, last + 2, top + BRACKET_DY, f.span)
    return out


def svg() -> str:
    out = [
        f'<svg viewBox="0 0 {W} {H:.0f}" role="img" aria-labelledby="pipelining-title pipelining-desc"',
        '     xmlns="http://www.w3.org/2000/svg" class="diagram-svg">',
        f'  <title id="pipelining-title">{TITLE}</title>',
        f'  <desc id="pipelining-desc">{DESC}</desc>',
    ]
    for top, f in zip(FRAME_Y, FRAMES):
        out += frame(top, f)
    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    target = Path(__file__).resolve().parent.parent / "_includes" / "diagram-pipelining.svg"
    target.write_text(svg())
    print(f"wrote {target}")
