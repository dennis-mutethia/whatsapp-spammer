import re
import requests
from flask import Flask, request, Response, render_template_string, redirect
from urllib.parse import urljoin, urlparse, urlencode, quote

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

HOME_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>ProxyGate</title>
  <link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap" rel="stylesheet"/>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg: #0a0a0f;
      --surface: #12121a;
      --border: #2a2a3a;
      --accent: #7c5cfc;
      --accent2: #fc5c7c;
      --text: #e8e8f0;
      --muted: #666680;
    }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'Syne', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2rem;
      position: relative;
      overflow: hidden;
    }

    body::before {
      content: '';
      position: fixed;
      inset: 0;
      background:
        radial-gradient(ellipse 60% 50% at 20% 20%, rgba(124,92,252,0.12) 0%, transparent 70%),
        radial-gradient(ellipse 50% 40% at 80% 80%, rgba(252,92,124,0.08) 0%, transparent 70%);
      pointer-events: none;
    }

    .grid-overlay {
      position: fixed;
      inset: 0;
      background-image:
        linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
      background-size: 60px 60px;
      pointer-events: none;
    }

    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 3rem;
      width: 100%;
      max-width: 560px;
      position: relative;
      z-index: 1;
      box-shadow: 0 0 80px rgba(124,92,252,0.08);
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(124,92,252,0.15);
      border: 1px solid rgba(124,92,252,0.3);
      border-radius: 999px;
      padding: 4px 12px;
      font-family: 'Space Mono', monospace;
      font-size: 0.7rem;
      color: var(--accent);
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 1.5rem;
    }

    .badge::before {
      content: '';
      width: 6px; height: 6px;
      background: var(--accent);
      border-radius: 50%;
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.3; }
    }

    h1 {
      font-size: 2.6rem;
      font-weight: 800;
      line-height: 1.1;
      margin-bottom: 0.5rem;
      background: linear-gradient(135deg, #fff 40%, var(--accent));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .subtitle {
      color: var(--muted);
      font-size: 0.95rem;
      margin-bottom: 2.5rem;
      line-height: 1.5;
    }

    .input-group {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .input-wrap {
      position: relative;
    }

    .input-wrap span {
      position: absolute;
      left: 14px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--muted);
      font-family: 'Space Mono', monospace;
      font-size: 0.75rem;
      pointer-events: none;
      white-space: nowrap;
    }

    input[type="text"] {
      width: 100%;
      background: rgba(255,255,255,0.04);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 0.9rem 1rem 0.9rem 6.5rem;
      color: var(--text);
      font-family: 'Space Mono', monospace;
      font-size: 0.9rem;
      outline: none;
      transition: border-color 0.2s, box-shadow 0.2s;
    }

    input[type="text"]:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(124,92,252,0.15);
    }

    input[type="text"]::placeholder { color: var(--muted); }

    button {
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      border: none;
      border-radius: 10px;
      padding: 0.9rem;
      color: #fff;
      font-family: 'Syne', sans-serif;
      font-weight: 700;
      font-size: 1rem;
      cursor: pointer;
      transition: opacity 0.2s, transform 0.1s;
      letter-spacing: 0.02em;
    }

    button:hover { opacity: 0.9; transform: translateY(-1px); }
    button:active { transform: translateY(0); }

    .examples {
      margin-top: 1.5rem;
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .ex-label {
      font-size: 0.75rem;
      color: var(--muted);
      width: 100%;
      font-family: 'Space Mono', monospace;
    }

    .chip {
      background: rgba(255,255,255,0.05);
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 4px 12px;
      font-size: 0.78rem;
      color: var(--muted);
      cursor: pointer;
      transition: all 0.15s;
      font-family: 'Space Mono', monospace;
    }

    .chip:hover {
      border-color: var(--accent);
      color: var(--accent);
      background: rgba(124,92,252,0.08);
    }

    .info {
      margin-top: 2rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--border);
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
    }

    .info-item { }
    .info-item dt {
      font-size: 0.7rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-family: 'Space Mono', monospace;
      margin-bottom: 2px;
    }
    .info-item dd {
      font-size: 0.85rem;
      color: var(--text);
      font-family: 'Space Mono', monospace;
    }
  </style>
</head>
<body>
  <div class="grid-overlay"></div>
  <div class="card">
    <div class="badge">Server-side Proxy</div>
    <h1>ProxyGate</h1>
    <p class="subtitle">Browse any URL through your server. The target site sees your server's IP, not yours.</p>

    <form action="/proxy" method="get" class="input-group">
      <div class="input-wrap">
        <span>https://</span>
        <input type="text" name="url" id="urlInput" placeholder="example.com/path" required autocomplete="off"/>
      </div>
      <button type="submit">→ Route Through Server</button>
    </form>

    <div class="examples">
      <span class="ex-label">// quick access</span>
      <span class="chip" onclick="setUrl('google.com')">google.com</span>
      <span class="chip" onclick="setUrl('wikipedia.org')">wikipedia.org</span>
      <span class="chip" onclick="setUrl('news.ycombinator.com')">HN</span>
      <span class="chip" onclick="setUrl('httpbin.org/ip')">httpbin.org/ip</span>
    </div>

    <dl class="info">
      <div class="info-item">
        <dt>How it works</dt>
        <dd>Flask fetches the URL server-side</dd>
      </div>
      <div class="info-item">
        <dt>Link rewriting</dt>
        <dd>Navigation stays proxied</dd>
      </div>
    </dl>
  </div>

  <script>
    function setUrl(url) {
      document.getElementById('urlInput').value = url;
    }

    // Also support ?link= param for backward compat
    const params = new URLSearchParams(window.location.search);
    const link = params.get('link');
    if (link) {
      window.location.href = '/proxy?url=' + encodeURIComponent(
        link.startsWith('http') ? link : 'https://' + link
      );
    }
  </script>
</body>
</html>
"""


def normalize_url(url: str) -> str:
    """Ensure URL has a scheme."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def rewrite_html(content: str, base_url: str) -> str:
    """Rewrite absolute and relative links to go through the proxy."""
    parsed_base = urlparse(base_url)
    base_origin = f"{parsed_base.scheme}://{parsed_base.netloc}"

    def make_proxy_url(href: str) -> str:
        if not href or href.startswith(("#", "javascript:", "mailto:", "data:", "blob:")):
            return href
        absolute = urljoin(base_url, href)
        return f"/proxy?url={quote(absolute, safe='')}"

    # Rewrite href attributes — separate replacers per quote style (each pattern has only 1 group)
    content = re.sub(r'href="([^"]*)"',
                     lambda m: f'href="{make_proxy_url(m.group(1))}"', content)
    content = re.sub(r"href='([^']*)'",
                     lambda m: f"href='{make_proxy_url(m.group(1))}'", content)

    # Rewrite action attributes (forms)
    content = re.sub(r'action="([^"]*)"',
                     lambda m: f'action="{make_proxy_url(m.group(1))}"', content)
    content = re.sub(r"action='([^']*)'",
                     lambda m: f"action='{make_proxy_url(m.group(1))}'", content)

    # Rewrite src for iframes
    def replace_iframe_src(m):
        absolute = urljoin(base_url, m.group(1))
        return f'src="/proxy?url={quote(absolute, safe="")}"'

    content = re.sub(r'(?<=<iframe\s)(?:[^>]*?\s)?src="([^"]*)"', replace_iframe_src, content)
    content = re.sub(r'<iframe([^>]+)src="([^"]*)"',
                     lambda m: f'<iframe{m.group(1)}src="/proxy?url={quote(urljoin(base_url, m.group(2)), safe="")}"',
                     content)

    # Make relative src absolute for scripts/images so they load correctly
    def make_src_absolute(m):
        tag_open = m.group(1)
        src = m.group(2)
        quote_char = '"' if '"' in tag_open else "'"
        if src.startswith(("http://", "https://", "//", "data:")):
            return m.group(0)
        absolute = urljoin(base_url, src)
        return f'{tag_open}src={quote_char}{absolute}{quote_char}'

    content = re.sub(r'(<(?:script|img|source)[^>]+)src="([^"]*)"', make_src_absolute, content)

    return content


@app.route("/")
@app.route("/home")
def index():
    # Support ?link= shortcut from the address bar
    link = request.args.get("link")
    if link:
        url = normalize_url(link)
        return redirect(f"/proxy?url={quote(url, safe='')}")
    return render_template_string(HOME_HTML)


@app.route("/proxy")
def proxy():
    url = request.args.get("url", "").strip()
    if not url:
        return redirect("/")

    url = normalize_url(url)

    # Forward some safe request headers
    forward_headers = dict(HEADERS)
    for h in ("Accept", "Accept-Language"):
        if h in request.headers:
            forward_headers[h] = request.headers[h]

    try:
        resp = requests.get(
            url,
            headers=forward_headers,
            timeout=20,
            allow_redirects=True,
            stream=True,
        )
    except requests.exceptions.SSLError:
        # Retry with http
        try:
            url = url.replace("https://", "http://", 1)
            resp = requests.get(url, headers=forward_headers, timeout=20, allow_redirects=True, stream=True)
        except Exception as e:
            return f"<pre>Connection error: {e}</pre>", 502
    except requests.exceptions.ConnectionError as e:
        return f"<pre>Connection error: {e}</pre>", 502
    except requests.exceptions.Timeout:
        return "<pre>Request timed out.</pre>", 504
    except Exception as e:
        return f"<pre>Error: {e}</pre>", 500

    content_type = resp.headers.get("Content-Type", "")
    final_url = resp.url  # after redirects

    if "text/html" in content_type:
        body = resp.content.decode(resp.apparent_encoding or "utf-8", errors="replace")
        body = rewrite_html(body, final_url)

        # Inject a small toolbar at the top
        toolbar = f"""
<div id="__proxy_bar__" style="
  position:fixed;top:0;left:0;right:0;z-index:2147483647;
  background:linear-gradient(90deg,#7c5cfc,#fc5c7c);
  color:#fff;font-family:monospace;font-size:12px;
  padding:6px 14px;display:flex;align-items:center;gap:12px;
  box-shadow:0 2px 12px rgba(0,0,0,0.4);
">
  <strong>ProxyGate</strong>
  <span style="opacity:0.7">→</span>
  <span style="opacity:0.85;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:60vw">{final_url}</span>
  <a href="/" style="margin-left:auto;color:#fff;text-decoration:none;opacity:0.8;font-size:11px">✕ exit</a>
</div>
<div style="height:32px"></div>
"""
        body = body.replace("<body", toolbar + "<body", 1) if "<body" not in body else \
               re.sub(r"(<body[^>]*>)", r"\1" + toolbar, body, count=1)

        return Response(body, status=resp.status_code, content_type="text/html; charset=utf-8")

    # For non-HTML (images, CSS, JS, JSON, etc.) stream it through transparently
    excluded = {"content-encoding", "content-length", "transfer-encoding", "connection"}
    headers = {k: v for k, v in resp.headers.items() if k.lower() not in excluded}

    return Response(
        resp.iter_content(chunk_size=8192),
        status=resp.status_code,
        headers=headers,
        content_type=content_type,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)