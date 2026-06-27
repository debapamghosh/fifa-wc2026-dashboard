"""
patch_og_tags.py
----------------
Injects proper Open Graph + Twitter Card meta tags into Claude Design
bundled HTML articles for the Dugout / Beyond The Scoreline dashboard.

Usage:
  python3 patch_og_tags.py <input.html> <output.html> \
      --title "Beyond The Scoreline: The Ronaldo Problem" \
      --description "Is Cristiano Ronaldo the problem for Portugal, or is Roberto Martinez building the wrong system?" \
      --url "https://debapamghosh.github.io/fifa-wc2026-dashboard/articles/the-ronaldo-problem.html" \
      --slug "the-ronaldo-problem"

The script also auto-extracts title/series text from the bundler SVG thumbnail
if --title / --description are omitted.

The og:image is set to the article thumbnail at:
  https://debapamghosh.github.io/fifa-wc2026-dashboard/articles/thumbs/<slug>.jpg
"""

import argparse, re, sys, os

BASE_URL     = "https://debapamghosh.github.io/fifa-wc2026-dashboard"
THUMB_BASE   = f"{BASE_URL}/articles/thumbs"
SITE_NAME    = "The Dugout — FIFA WC 2026"
TWITTER_SITE = "@debapamghosh"    # update if you have a Twitter handle

def extract_from_svg(html: str):
    """Pull title lines and series label out of the bundler SVG thumbnail."""
    texts = re.findall(r'<text[^>]*>([^<]+)</text>', html)
    # First text is usually the kicker (BEYOND THE SCORELINE), rest are title lines
    kicker = ""
    title_lines = []
    for t in texts:
        t = t.strip()
        if not t or t in ("—",) or re.match(r'[🇦-🇿\d\s—–\-]+$', t):
            continue
        if t.upper() == t and len(t) < 40:
            kicker = t.title()
        else:
            title_lines.append(t)
    title = " ".join(title_lines) if title_lines else "Beyond The Scoreline"
    if kicker and title:
        full = f"{kicker}: {title}"
    else:
        full = title
    return full

def extract_score_line(html: str):
    """Extract score context for description fallback."""
    texts = re.findall(r'<text[^>]*>([^<]+)</text>', html)
    parts = [t.strip() for t in texts if re.search(r'[\d—–]', t)]
    return " ".join(parts).strip()

def build_og_block(title, description, url, image_url, site_name, twitter_site):
    return f"""
  <!-- Open Graph / Social sharing -->
  <meta property="og:type"        content="article" />
  <meta property="og:site_name"   content="{site_name}" />
  <meta property="og:title"       content="{title}" />
  <meta property="og:description" content="{description}" />
  <meta property="og:url"         content="{url}" />
  <meta property="og:image"       content="{image_url}" />
  <meta property="og:image:width"  content="1200" />
  <meta property="og:image:height" content="630" />
  <!-- Twitter Card -->
  <meta name="twitter:card"        content="summary_large_image" />
  <meta name="twitter:site"        content="{twitter_site}" />
  <meta name="twitter:title"       content="{title}" />
  <meta name="twitter:description" content="{description}" />
  <meta name="twitter:image"       content="{image_url}" />
  <!-- Standard -->
  <meta name="description"         content="{description}" />"""

def patch(input_path, output_path, title, description, url, slug):
    with open(input_path, encoding="utf-8") as f:
        html = f.read()

    # Auto-extract from SVG if not provided
    if not title:
        title = extract_from_svg(html)
    if not description:
        score = extract_score_line(html)
        description = f"Tactical analysis · {score}" if score else "Tactical analysis — Beyond The Scoreline"

    # Build image URL
    image_url = f"{THUMB_BASE}/{slug}.jpg"

    # Fix the generic <title>
    current_title = re.search(r'<title>(.*?)</title>', html)
    if current_title and current_title.group(1).strip().lower() in ("bundled page", ""):
        html = html.replace(current_title.group(0), f"<title>{title}</title>")

    # Inject OG block just before </head>
    og_block = build_og_block(title, description, url, image_url, SITE_NAME, TWITTER_SITE)
    if "og:title" in html:
        print("⚠️  OG tags already present — skipping injection.")
    else:
        html = html.replace("</head>", og_block + "\n</head>", 1)
        print(f"✅ OG tags injected.")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Written: {output_path}")
    print(f"   Title:       {title}")
    print(f"   Description: {description}")
    print(f"   OG image:    {image_url}")
    print(f"   URL:         {url}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Patch OG tags into bundled article HTML")
    parser.add_argument("input",       help="Input bundled HTML file")
    parser.add_argument("output",      help="Output HTML file")
    parser.add_argument("--title",       default="", help="Article title (auto-extracted if omitted)")
    parser.add_argument("--description", default="", help="Article description (auto-extracted if omitted)")
    parser.add_argument("--url",         default="", help="Canonical URL of the article")
    parser.add_argument("--slug",        default="", help="Slug used for thumbnail filename (e.g. scotland-brazil)")
    args = parser.parse_args()

    slug = args.slug or os.path.basename(args.output).replace(".html", "")
    url  = args.url  or f"{BASE_URL}/articles/{slug}.html"

    patch(args.input, args.output, args.title, args.description, url, slug)
