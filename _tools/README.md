# Site tooling

Two scripts, neither of which GitHub Pages runs: the site is built from the committed
HTML by Jekyll, and these only exist to produce that input.

## `render.rb` — preview the site locally

GitHub Pages builds the site with Jekyll, resolving the layout in `_layouts` and the
shared header and footer in `_includes`. Jekyll is awkward to install (one of its
dependencies needs Ruby headers), so this script renders the same thing with Liquid
alone, which installs anywhere.

```
gem install --user-install liquid    # once
ruby _tools/render.rb
python3 -m http.server 8765 --directory _site
```

Then open <http://localhost:8765/>. Re-run the script after each edit; `_site/` is
ignored by git. If you do have Jekyll, `jekyll serve` works as well and rebuilds by
itself.

## `plot_web.py` — draw the benchmark figures

Draws the two figures on the benchmarks page into `plots/`, in a light and a dark
variant each. The data comes from the benchmark suite in the Remoc repository, which
writes a JSON report.

The suite sweeps every layer, codec and link, which takes well over an hour. The
website shows one codec and one channel configuration, so the run it needs is much
smaller — three layers, and the default links and message sizes:

```
cd ../remoc/bench/perf
cargo run --release -- \
    --layer raw_tcp,tcp_struct_postbag,mpsc_struct_par4_postbag \
    --out results.json
```

That is about ten minutes. The three layers are the raw TCP transfer every result is
reported against, the plain TCP connection that serializes the same records, and the
`rch::mpsc` channel with four extra transfer channels. Then:

```
cd ../../../remoc-rs.github.io
pip install matplotlib
python3 _tools/plot_web.py ../remoc/bench/perf/results.json
```

Commit the changed SVGs in `plots/` together with any caption you had to update, and
check the numbers quoted on the page still match the plots.

Use `--quick` while iterating on the plots themselves: it shortens every transfer from
five seconds to one, which is noisy but takes about two minutes.

`plot.py`, next to the suite, draws every layer and codec instead and is the one to
use for analysis rather than for the site.
