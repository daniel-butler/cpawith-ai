#!/usr/bin/env python3
"""
cpawith.ai — Static site generator
Markdown in, clean HTML out. No frameworks.

Usage: python build.py
"""

import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).parent
CONTENT_DIR = ROOT / "content"
POSTS_DIR = CONTENT_DIR / "posts"
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
OUT_DIR = ROOT / "out"


def load_template(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text()


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and markdown body."""
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        meta = yaml.safe_load(fm)
        return meta or {}, body.strip()
    return {}, text


def render_markdown(text: str) -> str:
    """Convert markdown to HTML with extensions."""
    return markdown.markdown(
        text,
        extensions=[
            "fenced_code",
            "codehilite",
            "tables",
            "toc",
            "attr_list",
            "md_in_html",
            "smarty",
        ],
        extension_configs={
            "codehilite": {"css_class": "code-block", "guess_lang": False},
        },
    )


def render_template(template: str, **kwargs) -> str:
    """Simple {{ var }} template rendering."""
    # Inject global vars
    kwargs.setdefault("posthog_key", os.environ.get("POSTHOG_KEY", ""))
    for key, value in kwargs.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))
    return template


def build_post(md_path: Path, base_template: str, post_template: str) -> dict:
    """Build a single post. Returns metadata dict."""
    raw = md_path.read_text()
    meta, body = parse_frontmatter(raw)

    slug = meta.get("slug", md_path.stem)
    title = meta.get("title", slug.replace("-", " ").title())
    date = meta.get("date", "")
    description = meta.get("description", "")
    tags = meta.get("tags", [])
    reading_time = max(1, len(body.split()) // 200)

    html_body = render_markdown(body)

    # Render tags
    tags_html = " ".join(
        f'<span class="tag">{t}</span>' for t in tags
    )

    # Render post content
    post_html = render_template(
        post_template,
        title=title,
        date=date,
        description=description,
        tags=tags_html,
        reading_time=f"{reading_time} min read",
        content=html_body,
    )

    # Wrap in base template
    page_html = render_template(
        base_template,
        title=f"{title} — CPA with AI",
        description=description,
        content=post_html,
        url=f"https://cpawith.ai/posts/{slug}/",
    )

    # Write output
    out_path = OUT_DIR / "posts" / slug
    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / "index.html").write_text(page_html)

    return {
        "title": title,
        "slug": slug,
        "date": str(date),
        "description": description,
        "tags": tags,
        "reading_time": reading_time,
    }


def build_index(posts: list[dict], base_template: str, index_template: str):
    """Build the homepage."""
    # Sort by date descending
    posts = sorted(posts, key=lambda p: p["date"], reverse=True)

    posts_html = ""
    for p in posts:
        tags_html = " ".join(f'<span class="tag">{t}</span>' for t in p["tags"])
        posts_html += f"""
        <article class="post-card">
            <div class="post-meta">
                <time>{p['date']}</time>
                <span class="separator">·</span>
                <span>{p['reading_time']} min read</span>
            </div>
            <h2><a href="/posts/{p['slug']}/">{p['title']}</a></h2>
            <p class="post-description">{p['description']}</p>
            <div class="post-tags">{tags_html}</div>
        </article>
        """

    index_html = render_template(index_template, posts=posts_html)
    page_html = render_template(
        base_template,
        title="CPA with AI — Earn CPE credits building real automation",
        description="Tutorials, courses, and CPE credits for accountants who want to build with Python and AI. Written by a CPA turned software engineer at Amazon.",
        content=index_html,
        url="https://cpawith.ai/",
    )
    (OUT_DIR / "index.html").write_text(page_html)


def build_404(base_template: str):
    """Build custom 404 page with logging."""
    template_404 = load_template("404.html")
    page_html = render_template(
        base_template,
        title="Page Not Found — CPA with AI",
        description="",
        content=template_404,
        url="https://cpawith.ai/404",
    )
    (OUT_DIR / "404.html").write_text(page_html)


def build_llms_txt(posts: list[dict]):
    """Generate llms.txt for LLM discoverability."""
    lines = [
        "# CPA with AI",
        "",
        "> Tutorials, courses, and CPE credits for accountants who build with Python and AI.",
        "> Written by Daniel Butler — CPA turned software engineer at Amazon.",
        "",
        "## Posts",
        "",
    ]
    posts_sorted = sorted(posts, key=lambda p: p["date"], reverse=True)
    for p in posts_sorted:
        lines.append(f"- [{p['title']}](https://cpawith.ai/posts/{p['slug']}/): {p['description']}")
    lines.append("")
    (OUT_DIR / "llms.txt").write_text("\n".join(lines))


def build_sitemap(posts: list[dict]):
    """Generate sitemap.xml."""
    urls = ['  <url><loc>https://cpawith.ai/</loc></url>']
    for p in sorted(posts, key=lambda p: p["date"], reverse=True):
        urls.append(f'  <url><loc>https://cpawith.ai/posts/{p["slug"]}/</loc><lastmod>{p["date"]}</lastmod></url>')

    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemapindex.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>"""
    (OUT_DIR / "sitemap.xml").write_text(sitemap)


def build_rss(posts: list[dict]):
    """Generate RSS feed."""
    posts_sorted = sorted(posts, key=lambda p: p["date"], reverse=True)[:20]
    items = ""
    for p in posts_sorted:
        items += f"""
    <item>
      <title>{p['title']}</title>
      <link>https://cpawith.ai/posts/{p['slug']}/</link>
      <description>{p['description']}</description>
      <pubDate>{p['date']}</pubDate>
      <guid>https://cpawith.ai/posts/{p['slug']}/</guid>
    </item>"""

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>CPA with AI</title>
    <link>https://cpawith.ai</link>
    <description>Tutorials and CPE credits for accountants who build with Python and AI.</description>
    <atom:link href="https://cpawith.ai/feed.xml" rel="self" type="application/rss+xml"/>
    {items}
  </channel>
</rss>"""
    (OUT_DIR / "feed.xml").write_text(rss)


def copy_static():
    """Copy static assets to output."""
    dest = OUT_DIR / "static"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(STATIC_DIR, dest)


def main():
    # Clean output
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir()

    # Load templates
    base_template = load_template("base.html")
    post_template = load_template("post.html")
    index_template = load_template("index.html")

    # Build all posts
    posts = []
    if POSTS_DIR.exists():
        for md_file in sorted(POSTS_DIR.glob("*.md")):
            meta = build_post(md_file, base_template, post_template)
            posts.append(meta)
            print(f"  ✅ {meta['title']}")

    # Build index
    build_index(posts, base_template, index_template)
    print(f"  ✅ index ({len(posts)} posts)")

    # Build 404
    build_404(base_template)
    print("  ✅ 404")

    # Build llms.txt
    build_llms_txt(posts)
    print("  ✅ llms.txt")

    # Build sitemap
    build_sitemap(posts)
    print("  ✅ sitemap.xml")

    # Build RSS
    build_rss(posts)
    print("  ✅ feed.xml")

    # Copy static
    copy_static()
    print("  ✅ static assets")

    # CNAME for GitHub Pages custom domain
    (OUT_DIR / "CNAME").write_text("cpawith.ai")
    print("  ✅ CNAME")

    print(f"\n🦀 Built {len(posts)} posts → out/")


if __name__ == "__main__":
    main()
