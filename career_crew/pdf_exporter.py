import markdown as md_lib
from weasyprint import HTML


_CSS = """
body {
    font-family: Arial, DejaVu Sans, sans-serif;
    max-width: 820px;
    margin: 40px auto;
    color: #1a1a2e;
    line-height: 1.7;
    font-size: 14px;
}
h1 { font-size: 22px; color: #16213e; border-bottom: 2px solid #4a90e2; padding-bottom: 8px; margin-bottom: 16px; }
h2 { font-size: 17px; color: #16213e; margin-top: 28px; margin-bottom: 8px; }
h3 { font-size: 15px; color: #333; margin-top: 16px; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; }
th { background: #4a90e2; color: #fff; padding: 8px 10px; text-align: left; }
td { border: 1px solid #dde; padding: 7px 10px; }
tr:nth-child(even) td { background: #f4f7fd; }
code { background: #f0f4ff; padding: 2px 5px; border-radius: 3px; font-size: 12px; font-family: monospace; }
pre { background: #f0f4ff; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 12px; }
blockquote { border-left: 4px solid #4a90e2; margin: 0; padding: 6px 14px; color: #555; background: #f8faff; }
hr { border: none; border-top: 1px solid #dde; margin: 24px 0; }
ul { padding-left: 20px; }
ol { padding-left: 20px; }
li { margin-bottom: 4px; }
strong { color: #16213e; }
.dot-green  { color: #16a34a; font-weight: bold; }
.dot-yellow { color: #ca8a04; font-weight: bold; }
.dot-red    { color: #dc2626; font-weight: bold; }
.dot-blue   { color: #2563eb; font-weight: bold; }
"""

_EMOJI_REPLACEMENTS = [
    # Status circles — replace with colored CSS spans
    ('🟢', '<span class="dot-green">&#9679;</span>'),
    ('🟡', '<span class="dot-yellow">&#9679;</span>'),
    ('🔴', '<span class="dot-red">&#9679;</span>'),
    # Decorative emojis — replace with text symbols
    ('📋', '&#9656;'),   # right-pointing triangle
    ('🎯', '&#9670;'),   # diamond
    ('✅', '<span class="dot-green">&#10003;</span>'),
    ('❌', '<span class="dot-red">&#10007;</span>'),
    ('⚠️', '<span class="dot-yellow">&#9888;</span>'),
    ('⚠', '<span class="dot-yellow">&#9888;</span>'),
    ('💡', '&#9654;'),
    ('🔑', '&#9654;'),
    ('📌', '&#9654;'),
    ('👉', '&#9658;'),
    ('✓', '<span class="dot-green">&#10003;</span>'),
    ('✗', '<span class="dot-red">&#10007;</span>'),
]


def _replace_emojis(html: str) -> str:
    for emoji, replacement in _EMOJI_REPLACEMENTS:
        html = html.replace(emoji, replacement)
    return html


def markdown_to_pdf(md_content: str, output_path: str) -> None:
    html_body = md_lib.markdown(
        md_content,
        extensions=["tables", "fenced_code", "nl2br"],
    )
    html_body = _replace_emojis(html_body)

    full_html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <style>{_CSS}</style>
</head>
<body>{html_body}</body>
</html>"""
    HTML(string=full_html).write_pdf(output_path)
