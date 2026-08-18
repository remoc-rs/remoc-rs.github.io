# Site tooling

## Preview the site locally

GitHub Pages builds the site with Jekyll, resolving the layout in `_layouts` and the
shared header and footer in `_includes`. Run the same thing locally:

```
jekyll serve --livereload
```

Then open <http://localhost:4000/>. It rebuilds on every save and reloads the open
tab by itself; `_site/` is ignored by git.

Installing it needs Ruby headers, because two of its dependencies are native. On
Fedora, once:

```
sudo dnf install ruby-devel
gem install --user-install jekyll
```

The site uses no plugins, so plain Jekyll renders exactly what GitHub Pages publishes.

## Social cards

The three 1200 by 630 social preview images are rendered from editable SVG sources:

```
mkdir -p social
magick _tools/social-remoc.svg \( logo.png -resize 230x238 \) \
    -gravity northwest -geometry +90+170 -composite social/remoc.png
magick _tools/social-postbag.svg \( postbag/logo.png -resize 230x230 \) \
    -gravity northwest -geometry +90+170 -composite social/postbag.png
magick _tools/social-aggligator.svg \( aggligator/logo.png -resize 230x238 \) \
    -gravity northwest -geometry +90+170 -composite social/aggligator.png
```

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
