#!/usr/bin/env python3
"""Draws the byte diagrams on the Postbag page.

Writes `_includes/postbag-full.svg` and `_includes/postbag-slim.svg`, which the
page inlines, so the colours come from the site's CSS variables and light and
dark mode work from the one file.

    python3 _tools/postbag_diagram.py

Both show the same struct with the same values, so the two pictures differ only
in what the format writes. The bytes are the ones `_tools/postbag-bytes` prints
and checks against Postbag itself, so they cannot drift away from the format.
"""

from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------- #
# What the pictures show                                                       #
# --------------------------------------------------------------------------- #

ID, LEN, DATA, HEAD = "--accent", "--ty", "--str", "--fg-muted"


@dataclass
class Part:
    """One run of bytes, and what it means."""

    bytes: list[str]
    label: str
    colour: str


@dataclass
class Row:
    """A field: its source lines, and its bytes in each column."""

    source: list[str]
    value_shown: str
    ident: list[Part] = field(default_factory=list)
    length: list[Part] = field(default_factory=list)
    value: list[Part] = field(default_factory=list)


@dataclass
class Diagram:
    """One encoding of the struct."""

    name: str
    columns: list[tuple[str, str]]
    header: list[Part]
    rows: list[Row]
    title_right: str
    svg_title: str
    svg_desc: str
    top: int = 124
    header_labels_right: bool = True
    # Room for a byte cell and the label under it. A listing whose lines carry
    # an attribute above them needs more.
    row_h: int = 74
    enum_lines: list[str] = field(default_factory=lambda: list(ENUM_NUMBERED))


SOURCE = [
    ['#[serde(rename = "_0")]', "sensor: u32,"],
    ['#[serde(rename = "_1")]', "label: String,"],
    ['#[serde(rename = "_2")]', "unit: Unit,"],
]

# Slim writes no identifiers, so numbering a field changes nothing there and
# showing the attributes would only suggest that it does.
PLAIN_SOURCE = [["sensor: u32,"], ["label: String,"], ["unit: Unit,"]]

SHOWN = ["= 300", '= "temp"', "= Celsius"]

ENUM_NUMBERED = [
    "enum Unit {",
    '    #[serde(rename = "_0")]',
    "    Celsius,",
    '    #[serde(rename = "_1")]',
    "    Other(String),",
    "}",
]
ENUM_PLAIN = ["enum Unit {", "    Celsius,", "    Other(String),", "}"]

FULL = Diagram(
    name="postbag-full",
    columns=[("ident", "identifier"), ("length", "length"), ("value", "value")],
    header=[Part(["03"], "three fields follow", HEAD)],
    rows=[
        Row(
            SOURCE[0],
            SHOWN[0],
            ident=[Part(["41"], "_0", ID)],
            length=[Part(["02"], "", LEN)],
            value=[Part(["ac", "02"], "300 as a varint", DATA)],
        ),
        Row(
            SOURCE[1],
            SHOWN[1],
            ident=[Part(["42"], "_1", ID)],
            length=[Part(["04"], "", LEN)],
            value=[Part(["74", "65", "6d", "70"], '"temp"', DATA)],
        ),
        Row(
            SOURCE[2],
            SHOWN[2],
            ident=[Part(["43"], "_2", ID)],
            length=[Part(["01"], "", LEN)],
            value=[Part(["41"], "variant _0", DATA)],
        ),
    ],
    title_right="14 bytes",
    svg_title="How Postbag encodes a struct with identifiers",
    svg_desc=(
        "A Rust struct with three fields on the left, and on the right the fourteen bytes Postbag "
        "writes for it in its Full format, in three columns: the identifier of each field, the "
        "length of its value in bytes, and the value. Every field is numbered, so each identifier "
        "takes a single byte."
    ),
)

SLIM = Diagram(
    name="postbag-slim",
    columns=[("value", "value")],
    header=[
        Part(["03"], "three fields", HEAD),
        Part(["08"], "8 bytes of values", HEAD),
    ],
    rows=[
        Row(PLAIN_SOURCE[0], SHOWN[0], value=[Part(["ac", "02"], "300 as a varint", DATA)]),
        Row(
            PLAIN_SOURCE[1],
            SHOWN[1],
            value=[Part(["04"], "4 bytes", LEN), Part(["74", "65", "6d", "70"], '"temp"', DATA)],
        ),
        Row(PLAIN_SOURCE[2], SHOWN[2], value=[Part(["00"], "variant number 0", DATA)]),
    ],
    enum_lines=ENUM_PLAIN,
    title_right="10 bytes",
    svg_title="How Postbag encodes the same struct without identifiers",
    svg_desc=(
        "The same Rust struct on the left, and on the right the ten bytes Postbag writes for it "
        "in its Slim format: a field count, the length of the whole struct, and then the three "
        "values one after another. Nothing names the fields, so they can only be read back in "
        "the order they are declared."
    ),
    header_labels_right=False,
    top=138,
    row_h=62,
)

DIAGRAMS = [FULL, SLIM]

DERIVE = "#[derive(Serialize, Deserialize)]"
STRUCT_HEAD = "struct Reading {"
STRUCT_TAIL = "}"
TITLE_LEFT = "Your types"

# --------------------------------------------------------------------------- #
# Drawing                                                                      #
# --------------------------------------------------------------------------- #

W = 960
LEFT_W = 330  # the source listing
VALUE_X = 182  # where the values line up beside it
GAP = 60  # between the listing and the bytes
COL_GAP = 30
BYTE_W, BYTE_H, BYTE_GAP = 34, 32, 5

SANS = "Inter, system-ui, sans-serif"
MONO = "'JetBrains Mono', ui-monospace, monospace"

BYTES_X = LEFT_W + GAP


def parts_width(parts: list[Part]) -> float:
    """How wide a run of parts is, including the gaps between its cells."""
    cells = sum(len(part.bytes) for part in parts)
    if not cells:
        return 0
    return cells * BYTE_W + (cells - 1) * BYTE_GAP + 12 * (len(parts) - 1)


def column_x(diagram: Diagram) -> list[float]:
    """Left edge of each column, sized by its widest row."""
    xs, x = [], BYTES_X
    for attribute, _ in diagram.columns:
        xs.append(x)
        x += max(parts_width(getattr(row, attribute)) for row in diagram.rows) + COL_GAP
    return xs


def draw_parts(parts: list[Part], x: float, y: float, label_right: bool = False) -> list[str]:
    """Byte cells with their meaning underneath, or beside them, starting at `x`."""
    out = []
    for part in parts:
        width = parts_width([part])
        for n, value in enumerate(part.bytes):
            bx = x + n * (BYTE_W + BYTE_GAP)
            out.append(
                f'  <rect x="{bx}" y="{y}" width="{BYTE_W}" height="{BYTE_H}" rx="5"'
                f' fill="var({part.colour})"/>'
            )
            out.append(
                f'  <text x="{bx + BYTE_W / 2}" y="{y + 21}" text-anchor="middle"'
                f' font-family="{MONO}" font-size="13" fill="var(--bg)">{value}</text>'
            )
        if part.label and label_right:
            out.append(
                f'  <text x="{x + width + 12}" y="{y + 21}" font-family="{SANS}" font-size="12"'
                f' fill="var({part.colour})">{part.label}</text>'
            )
        elif part.label:
            out.append(
                f'  <text x="{x + width / 2}" y="{y + BYTE_H + 16}" text-anchor="middle"'
                f' font-family="{SANS}" font-size="12" fill="var({part.colour})">{part.label}</text>'
            )
        x += width + 12
    return out


def svg(diagram: Diagram) -> str:
    xs = column_x(diagram)
    height = diagram.top + len(diagram.rows) * diagram.row_h + 30 + len(diagram.enum_lines) * 20
    title_id, desc_id = f"{diagram.name}-title", f"{diagram.name}-desc"
    out = [
        f'<svg viewBox="0 0 {W} {height}" role="img" aria-labelledby="{title_id} {desc_id}"',
        '     xmlns="http://www.w3.org/2000/svg" class="diagram-svg">',
        f'  <title id="{title_id}">{diagram.svg_title}</title>',
        f'  <desc id="{desc_id}">{diagram.svg_desc}</desc>',
    ]

    for x, title in ((0, TITLE_LEFT), (BYTES_X, diagram.title_right)):
        out.append(
            f'  <text x="{x}" y="26" font-family="{SANS}" font-size="15" font-weight="600"'
            f' fill="var(--fg-muted)">{title}</text>'
        )

    # What comes before the fields belongs to none of the columns. Side by side
    # when each needs a label of its own, since one label per line would put
    # the second one over the first.
    if diagram.header_labels_right:
        out += draw_parts(diagram.header, BYTES_X, 52, label_right=True)
    else:
        x = BYTES_X
        for part in diagram.header:
            out += draw_parts([part], x, 52)
            x += max(parts_width([part]), len(part.label) * 6.2) + 24

    # Column headings, so the shape of a field can be read without a legend.
    for x, (_, heading) in zip(xs, diagram.columns):
        out.append(
            f'  <text x="{x}" y="{diagram.top - 14}" font-family="{SANS}" font-size="13"'
            f' font-weight="600" fill="var(--fg-muted)">{heading}</text>'
        )

    out.append(
        f'  <text x="0" y="46" font-family="{MONO}" font-size="13" fill="var(--com)">{DERIVE}</text>'
    )
    out.append(
        f'  <text x="0" y="68" font-family="{MONO}" font-size="14"'
        f' fill="var(--fg)">{STRUCT_HEAD}</text>'
    )

    for index, row in enumerate(diagram.rows):
        y = diagram.top + index * diagram.row_h
        # The declaration lines up with the bytes; its attribute hangs above it.
        decl_y = y + 22
        for line_no, line in enumerate(reversed(row.source)):
            out.append(
                f'  <text x="16" y="{decl_y - line_no * 20}" font-family="{MONO}" font-size="13"'
                f' fill="var({"--com" if line.startswith("#") else "--fg"})">{line}</text>'
            )
        out.append(
            f'  <text x="{VALUE_X}" y="{decl_y}" font-family="{MONO}" font-size="13"'
            f' fill="var(--fg-muted)">{row.value_shown}</text>'
        )
        for x, (attribute, _) in zip(xs, diagram.columns):
            out += draw_parts(getattr(row, attribute), x, y)

    tail_y = diagram.top + len(diagram.rows) * diagram.row_h - 8
    out.append(
        f'  <text x="0" y="{tail_y}" font-family="{MONO}" font-size="14"'
        f' fill="var(--fg)">{STRUCT_TAIL}</text>'
    )
    for line_no, line in enumerate(diagram.enum_lines):
        # SVG collapses leading spaces, so indentation becomes an offset.
        indent = (len(line) - len(line.lstrip())) * 7.8
        out.append(
            f'  <text x="{indent:.0f}" y="{tail_y + 34 + line_no * 20}" font-family="{MONO}"'
            f' font-size="13" fill="var({"--com" if line.strip().startswith("#") else "--fg"})">'
            f"{line.strip()}</text>"
        )

    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    includes = Path(__file__).resolve().parent.parent / "_includes"
    for diagram in DIAGRAMS:
        target = includes / f"{diagram.name}.svg"
        target.write_text(svg(diagram))
        print(f"wrote {target}")
