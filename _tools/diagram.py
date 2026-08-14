#!/usr/bin/env python3
"""Draws the connection diagram on the home page.

Writes `_includes/diagram.svg`, which the page inlines, so the colours come from
the site's CSS variables and light and dark mode work from the one file.

    python3 _tools/diagram.py

Everything the picture says is in the block below; the rest is drawing.
"""

from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------- #
# What the picture shows                                                       #
# --------------------------------------------------------------------------- #


@dataclass
class Lane:
    left: str  # label on the left endpoint
    right: str  # label on the right endpoint
    colour: str  # CSS custom property holding its colour
    flow: str  # "right", "left" or "both"
    queued: int  # messages drawn waiting in the channel, at each end


LANES = [
    Lane("mpsc::Sender", "mpsc::Receiver", "--ty", "right", 3),
    Lane("watch::Receiver", "watch::Sender", "--str", "left", 1),
    Lane("RPC client", "RPC server", "--accent", "both", 2),
]

LEFT_TITLE = "Local endpoint"
RIGHT_TITLE = "Remote endpoint"
ABOVE_WIRE = "chunks of every channel, interleaved"
BELOW_WIRE_STRONG = "one"  # set in bold
BELOW_WIRE = " connection"
BELOW_WIRE_2 = "TCP, TLS, a WebSocket or anything else that carries bytes"

TITLE = "How Remoc uses one connection"
DESC = (
    "Two programs, each holding senders and receivers with their own queue of messages: "
    "an mpsc sender sending to the right, "
    "a watch receiver fed from the right, and an RPC client calling an RPC server. All of them "
    "join into a single connection in the middle, which carries their chunks interleaved."
)

# --------------------------------------------------------------------------- #
# Drawing                                                                      #
# --------------------------------------------------------------------------- #

W, H = 960, 300
BOX_W, BOX_H, BOX_Y = 250, 240, 30
LEFT_BOX_X, RIGHT_BOX_X = 0, W - BOX_W
LANE_H, LANE_PAD, LANE_INSET = 38, 16, 16
MSG_W, MSG_H, MSG_GAP, MSG_PAD = 12, 18, 4, 10
WIRE_X0, WIRE_X1 = 360, 600
WIRE_H = 36
MID_Y = BOX_Y + BOX_H / 2

# Which lane each chunk on the wire belongs to, left to right.
CHUNKS = [0, 2, 1, 0, 0, 2, 1, 2, 0, 1, 1, 0, 2, 0]

SANS = "Inter, system-ui, sans-serif"
MONO = "'JetBrains Mono', ui-monospace, monospace"


def lane_y(i: int) -> float:
    """Vertical centre of lane `i`."""
    total = len(LANES) * LANE_H + (len(LANES) - 1) * LANE_PAD
    top = MID_Y - total / 2
    return top + i * (LANE_H + LANE_PAD) + LANE_H / 2


def arrow(x: float, y: float, facing: str, colour: str) -> str:
    """A small solid triangle at (x, y) pointing left or right."""
    d = 7 if facing == "right" else -7
    return (
        f'<path d="M {x},{y - 5} L {x + d},{y} L {x},{y + 5} Z" fill="var({colour})"/>'
    )


def svg() -> str:
    out = [
        f'<svg viewBox="0 0 {W} {H}" role="img" aria-labelledby="diagram-title diagram-desc"',
        '     xmlns="http://www.w3.org/2000/svg" class="diagram-svg">',
        f"  <title id=\"diagram-title\">{TITLE}</title>",
        f"  <desc id=\"diagram-desc\">{DESC}</desc>",
    ]

    # The two endpoints.
    for x, title in ((LEFT_BOX_X, LEFT_TITLE), (RIGHT_BOX_X, RIGHT_TITLE)):
        out.append(
            f'  <rect x="{x + 0.5}" y="{BOX_Y + 0.5}" width="{BOX_W - 1}" height="{BOX_H - 1}" rx="12"'
            f' fill="var(--bg-alt)" stroke="var(--border)"/>'
        )
        out.append(
            f'  <text x="{x + BOX_W / 2}" y="{BOX_Y - 10}" text-anchor="middle"'
            f' font-family="{SANS}" font-size="16" font-weight="600" fill="var(--fg-muted)">{title}</text>'
        )

    # One row per lane: a labelled box in each endpoint, joined to the wire.
    for i, lane in enumerate(LANES):
        y = lane_y(i)
        top = y - LANE_H / 2
        for x, label in ((LEFT_BOX_X, lane.left), (RIGHT_BOX_X, lane.right)):
            rect_l, rect_r = x + LANE_INSET, x + BOX_W - LANE_INSET
            out.append(
                f'  <rect x="{rect_l}" y="{top}" width="{rect_r - rect_l}" height="{LANE_H}" rx="8"'
                f' fill="none" stroke="var({lane.colour})" stroke-width="1.5"/>'
            )

            # Waiting messages, queued at the end of the channel facing the connection.
            strip = lane.queued * MSG_W + (lane.queued - 1) * MSG_GAP
            if x == LEFT_BOX_X:
                strip_x = rect_r - MSG_PAD - strip
                label_x = (rect_l + strip_x) / 2
            else:
                strip_x = rect_l + MSG_PAD
                label_x = (strip_x + strip + rect_r) / 2
            for n in range(lane.queued):
                out.append(
                    f'  <rect x="{strip_x + n * (MSG_W + MSG_GAP)}" y="{y - MSG_H / 2}"'
                    f' width="{MSG_W}" height="{MSG_H}" rx="2" fill="var({lane.colour})"/>'
                )

            out.append(
                f'  <text x="{label_x}" y="{y + 5}" text-anchor="middle"'
                f' font-family="{MONO}" font-size="14" fill="var(--fg)">{label}</text>'
            )

        # Funnels: out of the left endpoint into the wire, and out again.
        left_edge = LEFT_BOX_X + BOX_W - LANE_INSET
        right_edge = RIGHT_BOX_X + LANE_INSET
        out.append(
            f'  <path d="M {left_edge},{y} C {left_edge + 75},{y}'
            f' {WIRE_X0 - 55},{MID_Y} {WIRE_X0},{MID_Y}" fill="none"'
            f' stroke="var({lane.colour})" stroke-width="2"/>'
        )
        out.append(
            f'  <path d="M {WIRE_X1},{MID_Y} C {WIRE_X1 + 55},{MID_Y}'
            f' {right_edge - 75},{y} {right_edge},{y}" fill="none"'
            f' stroke="var({lane.colour})" stroke-width="2"/>'
        )

        # Arrowheads land on the channel they feed.
        if lane.flow in ("right", "both"):
            out.append(arrow(right_edge - 7, y, "right", lane.colour))
        if lane.flow in ("left", "both"):
            out.append(arrow(left_edge + 7, y, "left", lane.colour))

    # The wire, carrying chunks of all channels one after another.
    out.append(
        f'  <rect x="{WIRE_X0}" y="{MID_Y - WIRE_H / 2}" width="{WIRE_X1 - WIRE_X0}" height="{WIRE_H}"'
        f' rx="6" fill="var(--bg-alt)" stroke="var(--border)"/>'
    )
    gap, inset = 4, 7
    chunk_w = (WIRE_X1 - WIRE_X0 - 2 * inset - (len(CHUNKS) - 1) * gap) / len(CHUNKS)
    for n, lane_index in enumerate(CHUNKS):
        cx = WIRE_X0 + inset + n * (chunk_w + gap)
        out.append(
            f'  <rect x="{cx:.1f}" y="{MID_Y - WIRE_H / 2 + 7}" width="{chunk_w:.1f}" height="{WIRE_H - 14}"'
            f' rx="2" fill="var({LANES[lane_index].colour})"/>'
        )

    mid_x = (WIRE_X0 + WIRE_X1) / 2
    out.append(
        f'  <text x="{mid_x}" y="{MID_Y - WIRE_H / 2 - 14}" text-anchor="middle"'
        f' font-family="{SANS}" font-size="14" fill="var(--fg-muted)">{ABOVE_WIRE}</text>'
    )
    out.append(
        f'  <text x="{mid_x}" y="{MID_Y + WIRE_H / 2 + 26}" text-anchor="middle"'
        f' font-family="{SANS}" font-size="15" fill="var(--fg-muted)">'
        f'<tspan font-weight="700" fill="var(--fg)">{BELOW_WIRE_STRONG}</tspan>{BELOW_WIRE}</text>'
    )
    out.append(
        f'  <text x="{mid_x}" y="{MID_Y + WIRE_H / 2 + 48}" text-anchor="middle"'
        f' font-family="{SANS}" font-size="13" fill="var(--fg-muted)">{BELOW_WIRE_2}</text>'
    )

    out.append("</svg>")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- #
# Second picture: a channel travelling inside a message                        #
# --------------------------------------------------------------------------- #

# The channel that already exists, and the one that comes into being by being sent.
EXISTING = Lane("RPC client", "RPC server", "--accent", "right", 0)
CREATED = Lane("mpsc::Receiver", "mpsc::Sender", "--ty", "left", 0)

STEP_ONE = "1. A request travels over a channel that already exists, carrying the sender of a new one."
STEP_TWO = "2. The new channel is live, inside the same connection."
MSG_TITLE = "count(...)"
MSG_PLAIN = "up_to: 4"
MSG_CHANNEL_NAME = "seq_tx:"
MSG_CHANNEL_TYPE = "mpsc::Sender"
COUNTED = ["0", "1", "2", "3"]  # values coming back over the new channel

CH_TITLE = "How a channel is created by sending one"
CH_DESC = (
    "Two frames. In the first, a request travelling over an existing channel between the two "
    "endpoints contains a field holding the sender of a new channel. In the second, that channel "
    "is live between the endpoints, running inside the same connection as the first one."
)

CH_W = 960
END_W = 250
CONN_X0, CONN_X1 = 290, CH_W - 290
FRAME_TOP = (32, 258)  # top of the endpoint boxes of each frame
FRAME_H = 152
CH_LANE_H = 46
ANY_CHANNEL = "any channel can carry another"
CARRIER_ALT = ("or existing mpsc::Sender", "or existing mpsc::Receiver")  # the carrier is not special
CH_H = FRAME_TOP[1] + FRAME_H + 40


def ch_lane_y(frame_top: int, index: int) -> float:
    """Vertical centre of lane `index` within a frame."""
    return frame_top + 50 + index * 58


def ch_frame(
    frame_top: int, lanes: list[Lane], titles: bool, subs: dict[int, tuple[str, str]] | None = None
) -> list[str]:
    """One frame: two endpoints holding `lanes`, joined through the connection."""
    out = []

    for x in (0, CH_W - END_W):
        out.append(
            f'  <rect x="{x + 0.5}" y="{frame_top + 0.5}" width="{END_W - 1}" height="{FRAME_H - 1}"'
            f' rx="12" fill="var(--bg-alt)" stroke="var(--border)"/>'
        )
    if titles:
        for x, title in ((0, LEFT_TITLE), (CH_W - END_W, RIGHT_TITLE)):
            out.append(
                f'  <text x="{x + END_W / 2}" y="{frame_top - 12}" text-anchor="middle"'
                f' font-family="{SANS}" font-size="15" font-weight="600"'
                f' fill="var(--fg-muted)">{title}</text>'
            )

    # The connection carrying the channels.
    out.append(
        f'  <rect x="{CONN_X0}" y="{frame_top + 0.5}" width="{CONN_X1 - CONN_X0}" height="{FRAME_H - 1}"'
        f' rx="12" fill="var(--bg-alt)" stroke="var(--border)"/>'
    )
    if titles:
        out.append(
            f'  <text x="{(CONN_X0 + CONN_X1) / 2}" y="{frame_top - 12}" text-anchor="middle"'
            f' font-family="{SANS}" font-size="15" font-weight="600"'
            f' fill="var(--fg-muted)">One connection</text>'
        )

    for index, lane in enumerate(lanes):
        y = ch_lane_y(frame_top, index)
        sub = (subs or {}).get(index)
        for side, (x, label) in enumerate(((0, lane.left), (CH_W - END_W, lane.right))):
            out.append(
                f'  <rect x="{x + LANE_INSET}" y="{y - CH_LANE_H / 2}" width="{END_W - 2 * LANE_INSET}"'
                f' height="{CH_LANE_H}" rx="8" fill="none" stroke="var({lane.colour})" stroke-width="1.5"/>'
            )
            out.append(
                f'  <text x="{x + END_W / 2}" y="{y + (0 if sub else 5)}" text-anchor="middle"'
                f' font-family="{MONO}" font-size="14" fill="var(--fg)">{label}</text>'
            )
            if sub:
                out.append(
                    f'  <text x="{x + END_W / 2}" y="{y + 16}" text-anchor="middle"'
                    f' font-family="{MONO}" font-size="11" fill="var(--fg-muted)">{sub[side]}</text>'
                )

        left_edge = END_W - LANE_INSET
        right_edge = CH_W - END_W + LANE_INSET
        out.append(
            f'  <path d="M {left_edge},{y} L {right_edge},{y}" stroke="var({lane.colour})"'
            f' stroke-width="2"/>'
        )
        if lane.flow == "right":
            out.append(arrow(right_edge - 7, y, "right", lane.colour))
        else:
            out.append(arrow(left_edge + 7, y, "left", lane.colour))

    return out


def channels_svg() -> str:
    out = [
        f'<svg viewBox="0 0 {CH_W} {CH_H}" role="img" aria-labelledby="channels-title channels-desc"',
        '     xmlns="http://www.w3.org/2000/svg" class="diagram-svg">',
        f'  <title id="channels-title">{CH_TITLE}</title>',
        f'  <desc id="channels-desc">{CH_DESC}</desc>',
    ]

    for step, top in zip((STEP_ONE, STEP_TWO), FRAME_TOP):
        out.append(
            f'  <text x="0" y="{top + FRAME_H + 26}" font-family="{SANS}" font-size="15"'
            f' font-weight="600" fill="var(--fg)">{step}</text>'
        )

    # First frame: only the existing channel, with the request on its way along it.
    out += ch_frame(FRAME_TOP[0], [EXISTING], titles=True, subs={0: CARRIER_ALT})

    line = ch_lane_y(FRAME_TOP[0], 0)
    box_w, box_h = 250, 58
    box_x, box_y = (CH_W - box_w) / 2, line - box_h / 2
    out.append(
        f'  <rect x="{box_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="6"'
        f' fill="var(--bg)" stroke="var({EXISTING.colour})"/>'
    )
    out.append(
        f'  <text x="{box_x}" y="{box_y - 8}" font-family="{MONO}" font-size="12"'
        f' fill="var(--fg-muted)">{MSG_TITLE}</text>'
    )
    out.append(
        f'  <text x="{box_x + 14}" y="{box_y + 22}" font-family="{MONO}" font-size="12.5"'
        f' fill="var(--fg-muted)">{MSG_PLAIN}</text>'
    )
    out.append(
        f'  <text x="{box_x + 14}" y="{box_y + 45}" font-family="{MONO}" font-size="12.5"'
        f' fill="var(--fg-muted)">{MSG_CHANNEL_NAME}</text>'
    )
    # The channel half inside the message, drawn like the channel it becomes.
    half_x, half_w = box_x + 66, 108
    out.append(
        f'  <rect x="{half_x}" y="{box_y + 29}" width="{half_w}" height="22" rx="5"'
        f' fill="none" stroke="var({CREATED.colour})" stroke-width="1.5"/>'
    )
    out.append(
        f'  <text x="{half_x + half_w / 2}" y="{box_y + 45}" text-anchor="middle"'
        f' font-family="{MONO}" font-size="12.5" fill="var({CREATED.colour})">{MSG_CHANNEL_TYPE}</text>'
    )

    out.append(
        f'  <text x="{(CONN_X0 + CONN_X1) / 2}" y="{box_y + box_h + 20}" text-anchor="middle"'
        f' font-family="{SANS}" font-size="12.5" fill="var(--fg-muted)">{ANY_CHANNEL}</text>'
    )

    # Second frame: the same channel, and the one that arrived inside the request.
    out += ch_frame(FRAME_TOP[1], [EXISTING, CREATED], titles=False, subs={0: CARRIER_ALT})

    # Values counted by the remote endpoint, travelling back over the new channel.
    y = ch_lane_y(FRAME_TOP[1], 1)
    size, gap = 24, 18
    total = len(COUNTED) * size + (len(COUNTED) - 1) * gap
    start = (CONN_X0 + CONN_X1 - total) / 2
    for n, value in enumerate(COUNTED):
        vx = start + n * (size + gap)
        out.append(
            f'  <rect x="{vx}" y="{y - size / 2}" width="{size}" height="{size}" rx="4"'
            f' fill="var({CREATED.colour})"/>'
        )
        out.append(
            f'  <text x="{vx + size / 2}" y="{y + 5}" text-anchor="middle" font-family="{MONO}"'
            f' font-size="12.5" fill="var(--bg)">{value}</text>'
        )

    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    includes = Path(__file__).resolve().parent.parent / "_includes"
    for name, content in (("diagram.svg", svg()), ("diagram-channels.svg", channels_svg())):
        (includes / name).write_text(content)
        print(f"wrote {includes / name}")
