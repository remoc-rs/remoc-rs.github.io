#!/usr/bin/env python3
"""Draws the two diagrams on the Aggligator per-flow-limits page.

Writes:
  - `_includes/aggligator-per-flow-tcp.svg`
  - `_includes/aggligator-per-flow-socks.svg`

Colours come from the site's CSS variables so light and dark mode work from
the same SVG files.

    python3 _tools/per_flow_diagrams.py
"""

from pathlib import Path

W, H = 960, 296
BOX_W, BOX_H, BOX_Y = 200, 224, 44
LEFT_BOX_X, RIGHT_BOX_X = 0, W - BOX_W
MID_Y = BOX_Y + BOX_H / 2

END_INSET, END_H = 16, 62
LANE_H, LANE_PAD = 34, 18
CHUNK_W, CHUNK_H, CHUNK_GAP = 12, 16, 6

SANS = "Inter, system-ui, sans-serif"
MONO = "'JetBrains Mono', ui-monospace, monospace"


def lane_y(i: int, n_lanes: int = 4) -> float:
    total = n_lanes * LANE_H + (n_lanes - 1) * LANE_PAD
    top = MID_Y - total / 2
    return top + i * (LANE_H + LANE_PAD) + LANE_H / 2


def draw_endpoints(out: list[str], left_title: str, right_title: str, right_sub: str) -> tuple[float, float]:
    for x, title, top_text, sub_text in (
        (LEFT_BOX_X, left_title, "alc::Stream", "1 byte stream"),
        (RIGHT_BOX_X, right_title, "alc::Stream", right_sub),
    ):
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
            f' font-family="{MONO}" font-size="14" fill="var(--fg)">{top_text}</text>'
        )
        out.append(
            f'  <text x="{x + BOX_W / 2}" y="{MID_Y + 17}" text-anchor="middle"'
            f' font-family="{MONO}" font-size="11" fill="var(--fg-muted)">{sub_text}</text>'
        )
    return LEFT_BOX_X + BOX_W - END_INSET, RIGHT_BOX_X + END_INSET


def svg_tcp() -> str:
    lane_x0, lane_x1 = 246, W - 246
    out = [
        f'<svg viewBox="0 0 {W} {H}" role="img" aria-labelledby="pf-tcp-title pf-tcp-desc"',
        '     xmlns="http://www.w3.org/2000/svg" class="diagram-svg">',
        '  <title id="pf-tcp-title">Parallel TCP links over one path</title>',
        '  <desc id="pf-tcp-desc">A client and a server each hold one byte stream. Between them run four separate TCP connections over the same network path, each subject to a per-flow limit, combining their bandwidth into one stream.</desc>',
    ]

    left_edge, right_edge = draw_endpoints(out, "Client", "Server", "server.example:5800")

    out.append(
        f'  <text x="{(lane_x0 + lane_x1) / 2}" y="{BOX_Y - 10}" text-anchor="middle"'
        f' font-family="{SANS}" font-size="16" font-weight="600" fill="var(--fg-muted)">'
        'Same network path — 4 separate TCP flows</text>'
    )

    flows = [
        ("TCP link #0", ":50338 → :5800", 7),
        ("TCP link #1", ":50348 → :5800", 7),
        ("TCP link #2", ":50360 → :5800", 7),
        ("TCP link #3", ":50366 → :5800", 7),
    ]

    for i, (label, ports, chunks) in enumerate(flows):
        y = lane_y(i, len(flows))
        out.append(
            f'  <rect x="{lane_x0}" y="{y - LANE_H / 2}" width="{lane_x1 - lane_x0}" height="{LANE_H}"'
            ' rx="8" fill="var(--bg-alt)" stroke="var(--accent)" stroke-width="1.5"/>'
        )
        out.append(
            f'  <text x="{lane_x0 + 12}" y="{y + 5}" font-family="{SANS}" font-size="13.5"'
            f' fill="var(--fg)">{label}</text>'
        )
        out.append(
            f'  <text x="{lane_x0 + 104}" y="{y + 4.5}" font-family="{MONO}" font-size="11.5"'
            f' fill="var(--fg-muted)">{ports}</text>'
        )
        chunk_x = lane_x0 + 232
        for n in range(chunks):
            out.append(
                f'  <rect x="{chunk_x + n * (CHUNK_W + CHUNK_GAP)}" y="{y - CHUNK_H / 2}"'
                f' width="{CHUNK_W}" height="{CHUNK_H}" rx="2" fill="var(--accent)"/>'
            )

        out.append(
            f'  <path d="M {left_edge},{MID_Y} C {left_edge + 30},{MID_Y}'
            f' {lane_x0 - 30},{y} {lane_x0},{y}" fill="none" stroke="var(--accent)" stroke-width="2"/>'
        )
        out.append(
            f'  <path d="M {lane_x1},{y} C {lane_x1 + 30},{y}'
            f' {right_edge - 30},{MID_Y} {right_edge},{MID_Y}" fill="none" stroke="var(--accent)" stroke-width="2"/>'
        )

    out.append("</svg>")
    return "\n".join(out) + "\n"


def svg_socks() -> str:
    proxy_x, proxy_w = 240, 146
    lane_x0, lane_x1 = 420, W - 240

    out = [
        f'<svg viewBox="0 0 {W} {H}" role="img" aria-labelledby="pf-socks-title pf-socks-desc"',
        '     xmlns="http://www.w3.org/2000/svg" class="diagram-svg">',
        '  <title id="pf-socks-title">Aggregating links through SOCKS5 proxies</title>',
        '  <desc id="pf-socks-desc">A client distributes one stream across four SOCKS5 proxy endpoints. Each proxy establishes its own independent outer TCP connection to the server, where the packets are reassembled into one stream.</desc>',
    ]

    left_edge, right_edge = draw_endpoints(out, "Client", "Server", "server.example:5800")

    out.append(
        f'  <text x="{proxy_x + proxy_w / 2}" y="{BOX_Y - 10}" text-anchor="middle"'
        f' font-family="{SANS}" font-size="16" font-weight="600" fill="var(--fg-muted)">'
        'SOCKS5 proxies</text>'
    )
    out.append(
        f'  <text x="{(lane_x0 + lane_x1) / 2}" y="{BOX_Y - 10}" text-anchor="middle"'
        f' font-family="{SANS}" font-size="16" font-weight="600" fill="var(--fg-muted)">'
        'Independent outer TCP flows</text>'
    )

    proxies = [
        ("127.0.0.1:1081", "Outer flow #1", 7),
        ("127.0.0.1:1082", "Outer flow #2", 7),
        ("127.0.0.1:1083", "Outer flow #3", 7),
        ("127.0.0.1:1084", "Outer flow #4", 7),
    ]

    for i, (proxy_addr, flow_label, chunks) in enumerate(proxies):
        y = lane_y(i, len(proxies))

        # Proxy box
        out.append(
            f'  <rect x="{proxy_x}" y="{y - LANE_H / 2}" width="{proxy_w}" height="{LANE_H}"'
            ' rx="8" fill="var(--bg-alt)" stroke="var(--border)" stroke-width="1.5"/>'
        )
        out.append(
            f'  <text x="{proxy_x + proxy_w / 2}" y="{y + 4.5}" text-anchor="middle"'
            f' font-family="{MONO}" font-size="12" fill="var(--fg)">{proxy_addr}</text>'
        )

        # Outer flow lane
        out.append(
            f'  <rect x="{lane_x0}" y="{y - LANE_H / 2}" width="{lane_x1 - lane_x0}" height="{LANE_H}"'
            ' rx="8" fill="var(--bg-alt)" stroke="var(--accent)" stroke-width="1.5"/>'
        )
        out.append(
            f'  <text x="{lane_x0 + 12}" y="{y + 5}" font-family="{SANS}" font-size="13.5"'
            f' fill="var(--fg)">{flow_label}</text>'
        )
        chunk_x = lane_x0 + 132
        for n in range(chunks):
            out.append(
                f'  <rect x="{chunk_x + n * (CHUNK_W + CHUNK_GAP)}" y="{y - CHUNK_H / 2}"'
                f' width="{CHUNK_W}" height="{CHUNK_H}" rx="2" fill="var(--accent)"/>'
            )

        # Connectors: Client -> Proxy -> Outer flow -> Server
        out.append(
            f'  <path d="M {left_edge},{MID_Y} C {left_edge + 26},{MID_Y}'
            f' {proxy_x - 26},{y} {proxy_x},{y}" fill="none" stroke="var(--accent)" stroke-width="2"/>'
        )
        out.append(
            f'  <path d="M {proxy_x + proxy_w},{y} L {lane_x0},{y}"'
            ' fill="none" stroke="var(--accent)" stroke-width="2"/>'
        )
        out.append(
            f'  <path d="M {lane_x1},{y} C {lane_x1 + 26},{y}'
            f' {right_edge - 26},{MID_Y} {right_edge},{MID_Y}" fill="none" stroke="var(--accent)" stroke-width="2"/>'
        )

    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    includes = Path(__file__).resolve().parent.parent / "_includes"
    tcp_path = includes / "aggligator-per-flow-tcp.svg"
    socks_path = includes / "aggligator-per-flow-socks.svg"
    tcp_path.write_text(svg_tcp())
    socks_path.write_text(svg_socks())
    print(f"wrote {tcp_path}")
    print(f"wrote {socks_path}")
