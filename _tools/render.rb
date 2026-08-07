#!/usr/bin/env ruby
# Renders the site the way GitHub Pages' Jekyll does, for checking it before pushing.
#
# Jekyll itself does not install everywhere (one of its dependencies needs Ruby headers),
# and this covers what the site actually uses: front matter, one layout, includes and the
# handful of Liquid tags in them. GitHub Pages remains the real build.
#
# Usage:
#   gem install --user-install liquid    # once
#   ruby _tools/render.rb
#   python3 -m http.server 8765 --directory _site

require "liquid"
require "yaml"
require "fileutils"

ROOT = File.expand_path("..", __dir__)
OUT = ARGV[0] || File.join(ROOT, "_site")

# Jekyll's own include syntax: an unquoted file name, resolved against _includes and
# rendered in the enclosing scope. Stock Liquid expects a quoted string instead.
class JekyllInclude < Liquid::Tag
  INCLUDES = File.join(ROOT, "_includes")

  def initialize(tag_name, markup, options)
    super
    @name = markup.strip
  end

  def render(context)
    Liquid::Template.parse(File.read(File.join(INCLUDES, @name))).render!(context)
  end
end

Liquid::Template.register_tag("include", JekyllInclude)

site = YAML.load_file(File.join(ROOT, "_config.yml"))
layouts = Dir[File.join(ROOT, "_layouts", "*.html")].to_h do |path|
  [File.basename(path, ".html"), File.read(path)]
end

FileUtils.rm_rf(OUT)
FileUtils.mkdir_p(OUT)

# Everything that is neither a template nor a repository file is copied unchanged.
Dir.children(ROOT).each do |name|
  next if name.start_with?("_", ".")

  path = File.join(ROOT, name)
  next if File.file?(path) && name.end_with?(".html")

  FileUtils.cp_r(path, File.join(OUT, name))
end

# Paths the site is configured not to publish, removed after copying so that a nested
# one is caught as well.
site.fetch("exclude", []).each { |name| FileUtils.rm_rf(File.join(OUT, name)) }

Dir[File.join(ROOT, "*.html")].sort.each do |path|
  source = File.read(path)
  unless source.start_with?("---\n")
    warn "#{File.basename(path)}: no front matter, copied unchanged"
    FileUtils.cp(path, File.join(OUT, File.basename(path)))
    next
  end

  _, front, body = source.split(/^---\s*$\n/, 3)
  page = YAML.safe_load(front)

  scope = { "site" => site, "page" => page }
  content = Liquid::Template.parse(body).render!(scope)
  layout = layouts.fetch(page.fetch("layout"))
  rendered = Liquid::Template.parse(layout).render!(scope.merge("content" => content))

  File.write(File.join(OUT, File.basename(path)), rendered)
  puts "Rendered #{File.basename(path)}"
end
