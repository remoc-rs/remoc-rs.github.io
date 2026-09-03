#!/usr/bin/env python3
"""Renders the example programs from the remoc repository into HTML.

Writes one include per example, which the matching page inlines, so the listings
on the site are the files that are actually in the repository rather than copies
that drift away from them.

    python3 _tools/render_examples.py [path/to/remoc/checkout]

Re-run it whenever an example changes.

Colours come from the site's own syntax classes, the same ones the hand-written
snippets on the home page use, so light and dark mode work from the one file.
"""

import html
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from pygments.lexers import BashLexer, HtmlLexer, RustLexer, TOMLLexer
from pygments.token import Token

# --------------------------------------------------------------------------- #
# What the pages show                                                          #
# --------------------------------------------------------------------------- #


@dataclass
class File:
    path: str  # relative to the crate directory, and shown as the heading
    role: str  # what this file is for, in one line


@dataclass
class Crate:
    name: str  # directory name, shown as the heading of the group
    role: str  # what this crate is, in one line
    files: list[File]
    directory: str | None = None  # source directory when it differs from the heading


@dataclass
class Example:
    id: str  # names the include: `_includes/example-<id>.html`
    directory: str  # relative to the repository root
    crates: list[Crate]


MANIFEST = "Its dependencies."

EXAMPLES = [
    Example(
        id="channels",
        directory="examples/channels",
        crates=[
            Crate(
                "counting",
                "Defines the request type shared by the client and server.",
                [
                    File("Cargo.toml", MANIFEST),
                    File("src/lib.rs", "Defines a request containing a channel sender."),
                ],
            ),
            Crate(
                "counting-server",
                "Accepts TCP connections and counts into whatever channel arrives in the request.",
                [
                    File("Cargo.toml", MANIFEST),
                    File(
                        "src/main.rs",
                        "Receives requests and sends each sequence over the channel included in "
                        "the request.",
                    ),
                ],
            ),
            Crate(
                "counting-client",
                "Asks the server to count and prints the sequence as it arrives.",
                [
                    File("Cargo.toml", MANIFEST),
                    File(
                        "src/main.rs",
                        "Creates a channel, sends its sender in the request and reads from its "
                        "receiver.",
                    ),
                ],
            ),
        ],
    ),
    Example(
        id="rtc",
        directory="examples/rtc",
        crates=[
            Crate(
                "counter",
                "Defines the remote trait shared by the client and server.",
                [
                    File("Cargo.toml", MANIFEST),
                    File(
                        "src/lib.rs",
                        "Defines the trait carrying <code>#[rtc::remote]</code> and the error type "
                        "returned by its methods. Two methods return channel receivers.",
                    ),
                ],
            ),
            Crate(
                "counter-server",
                "Holds the counter and serves it over each accepted connection.",
                [
                    File("Cargo.toml", MANIFEST),
                    File(
                        "src/main.rs",
                        "Implements the trait on the counter state and runs a generated server for "
                        "each connection.",
                    ),
                ],
            ),
            Crate(
                "counter-client",
                "Exercises the counter: reads it, increases it, watches it and streams from it.",
                [
                    File("Cargo.toml", MANIFEST),
                    File(
                        "src/main.rs",
                        "Uses the generated client to call the trait methods and receive updates.",
                    ),
                ],
            ),
        ],
    ),
    Example(
        id="tracing",
        directory="examples/tracing",
        crates=[
            Crate(
                "pizzeria",
                "Defines the remote trait and the tracing setup shared by the client and server.",
                [
                    File("Cargo.toml", MANIFEST),
                    File(
                        "src/lib.rs",
                        "Defines the trait whose <code>tracing</code> argument makes the server "
                        "create a span for processing each call, the progress callback type and "
                        "the tracing subscriber with optional span export.",
                    ),
                ],
            ),
            Crate(
                "pizzeria-server",
                "Prepares each ordered pizza in instrumented steps, reporting progress to the client.",
                [
                    File("Cargo.toml", MANIFEST),
                    File(
                        "src/main.rs",
                        "Implements the trait with <code>#[instrument]</code> steps and calls "
                        "the progress callback of the client after each of them.",
                    ),
                ],
            ),
            Crate(
                "pizzeria-client",
                "Orders one of each pizza on the menu, all at once.",
                [
                    File("Cargo.toml", MANIFEST),
                    File(
                        "src/main.rs",
                        "Places the orders concurrently within one span, passing a traced "
                        "progress callback with each.",
                    ),
                ],
            ),
        ],
    ),
    Example(
        id="rtc-web",
        directory="examples/rtc-web",
        crates=[
            Crate(
                "build",
                "Builds the WebAssembly client before compiling the server that embeds it.",
                [
                    File(
                        "Cargo.toml",
                        "Uses a size-oriented release profile for the WebAssembly build.",
                    ),
                    File(
                        "build.sh",
                        "Runs the two target-specific builds in the required order.",
                    ),
                ],
                directory=".",
            ),
            Crate(
                "counter",
                "Defines the remote trait shared by the browser client and server.",
                [
                    File("Cargo.toml", MANIFEST),
                    File(
                        "src/lib.rs",
                        "Defines the increment, decrement and watch methods on the shared counter.",
                    ),
                ],
            ),
            Crate(
                "counter-server-web",
                "Keeps the shared counter and serves the page and Remoc WebSocket endpoint.",
                [
                    File("Cargo.toml", MANIFEST),
                    File(
                        "src/main.rs",
                        "Adapts an Axum WebSocket for Remoc and embeds the generated browser assets.",
                    ),
                    File(
                        "src/index.html",
                        "Provides the counter controls and calls the Rust client from JavaScript.",
                    ),
                ],
            ),
            Crate(
                "counter-client-web",
                "Runs the generated counter client in the browser.",
                [
                    File("Cargo.toml", MANIFEST),
                    File(
                        "src/lib.rs",
                        "Connects through the browser WebSocket API and exposes the counter to "
                        "JavaScript with <code>wasm-bindgen</code>.",
                    ),
                ],
            ),
        ],
    ),
]

# The manifests in the repository depend on Remoc by path, which is an artefact of
# living next to it. The listings show what a reader would actually write, so that
# one dependency is rewritten to the published version. Everything else, including
# the path dependencies between the example's own crates, is shown as it is.
PATH_DEPENDENCY = re.compile(
    r'^remoc = \{ path = "[^"]*"(?P<options>, [^}]*)? \}$', re.M
)

# --------------------------------------------------------------------------- #
# Rendering                                                                    #
# --------------------------------------------------------------------------- #

# Pygments token types onto the syntax classes the site already defines. Longest
# prefix wins, so a specific entry overrides the general one above it.
CLASSES = {
    Token.Comment: "c",
    Token.Comment.Preproc: "a",  # the Rust lexer reports attributes here
    Token.Literal.String: "s",
    Token.Literal.String.Doc: "c",  # `///` and `//!` are comments, not strings
    Token.Literal.Number: "n",
    Token.Keyword: "k",
    Token.Keyword.Type: "t",
    Token.Name.Builtin: "t",
    Token.Name.Builtin.Pseudo: "k",  # `self` and `Self`
    Token.Name.Class: "t",
    Token.Name.Function: "f",
    Token.Name.Function.Magic: "m",  # macro invocations
}

# TOML is a different language and wants its own reading of the same classes.
TOML_CLASSES = {
    Token.Comment: "c",
    Token.Keyword: "t",  # `[package]` and friends are the structure of the file
    Token.Literal.String: "s",
}

HTML_CLASSES = {
    **CLASSES,
    Token.Name.Tag: "k",
    Token.Name.Attribute: "a",
}

SHELL_CLASSES = {
    **CLASSES,
    Token.Name.Builtin: "f",
    Token.Name.Variable: "n",
}

LEXERS = {
    ".html": (HtmlLexer, HTML_CLASSES),
    ".rs": (RustLexer, CLASSES),
    ".sh": (BashLexer, SHELL_CLASSES),
    ".toml": (TOMLLexer, TOML_CLASSES),
}


def css_class(token, classes: dict) -> str | None:
    """The site's class for `token`, falling back along the token hierarchy."""
    while token is not None:
        if token in classes:
            return classes[token]
        token = token.parent
    return None


def highlight(source: str, suffix: str) -> str:
    """`source` as HTML, with the site's syntax classes on it.

    Neighbouring tokens that land on the same class are merged, so a string or a
    comment is one span rather than one per lexed piece of it.
    """
    lexer, classes = LEXERS[suffix]

    runs: list[tuple[str | None, list[str]]] = []
    for token, value in lexer().get_tokens(source):
        if not value:
            continue
        cls = css_class(token, classes)
        if runs and runs[-1][0] == cls:
            runs[-1][1].append(value)
        else:
            runs.append((cls, [value]))

    out = []
    for cls, values in runs:
        escaped = html.escape("".join(values), quote=False)
        out.append(f'<span class="{cls}">{escaped}</span>' if cls else escaped)
    return "".join(out).rstrip("\n")


def published(source: str, version: str) -> str:
    """A manifest as the reader would write it, depending on a released Remoc."""
    source, count = PATH_DEPENDENCY.subn(
        lambda match: (
            f'remoc = {{ version = "{version}"{match.group("options") or ""} }}'
        ),
        source,
    )
    if count != 1:
        sys.exit("a manifest no longer has the expected `remoc` path dependency")
    return source


def render(example: Example, repo: Path, version: str) -> str:
    """The include for one example: every crate, and within it every file."""
    base = repo / example.directory
    out = []
    for crate in example.crates:
        crate_directory = crate.directory or crate.name
        out.append('<section class="example-crate">')
        out.append(f"    <h3>{html.escape(crate.name)}</h3>")
        out.append(f'    <p class="example-crate-role">{crate.role}</p>')

        for entry in crate.files:
            path = entry.path if crate_directory == "." else f"{crate.name}/{entry.path}"
            source = (base / crate_directory / entry.path).read_text()
            if entry.path == "Cargo.toml" and PATH_DEPENDENCY.search(source):
                source = published(source, version)

            anchor = path.replace("/", "-").replace(".", "-")
            out.append(f'    <article class="example-file" id="{anchor}">')
            out.append(f"        <h4><code>{html.escape(path)}</code></h4>")
            out.append(f"        <p>{entry.role}</p>")
            out.append(
                f"        <pre><code>{highlight(source, Path(entry.path).suffix)}</code></pre>"
            )
            out.append("    </article>")

        out.append("</section>")
    return "\n".join(out) + "\n"


def remoc_version(repo: Path) -> str:
    """The published version to depend on: the workspace version, without its patch."""
    manifest = (repo / "Cargo.toml").read_text()
    match = re.search(r'^version = "(\d+)\.(\d+)\.', manifest, re.M)
    if not match:
        sys.exit(f"no workspace version found in {repo / 'Cargo.toml'}")
    return f"{match[1]}.{match[2]}"


def revision(repo: Path, directories: list[str]) -> str:
    """The commit the listings were taken from, recorded in the generated file.

    Warns when the examples have uncommitted changes, because the listings then
    show something that is not in any commit, while the pages link to `master`.
    """
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    dirty = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain", "--", *directories],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    if dirty:
        print(
            f"warning: the examples have uncommitted changes, so they are not in {head}.\n"
            "         The pages link to master, so commit and push before publishing.",
            file=sys.stderr,
        )

    return head


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    repo = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else root.parent / "remoc"
    if not (repo / "examples").is_dir():
        sys.exit(f"no remoc checkout at {repo}; pass its path as an argument")

    rev = revision(repo, [e.directory for e in EXAMPLES])
    version = remoc_version(repo)

    for example in EXAMPLES:
        target = root / "_includes" / f"example-{example.id}.html"
        target.write_text(
            f"<!-- generated from remoc {rev} by _tools/render_examples.py -->\n"
            + render(example, repo, version)
        )
        print(f"wrote {target} from remoc {rev}")
