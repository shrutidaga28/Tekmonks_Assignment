from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.request
import html
import json
from urllib.parse import urljoin

BASE_URL = "https://time.com"

def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode("utf-8", errors="replace")

def strip_tags(text: str) -> str:
    while "<" in text and ">" in text:
        tag_start = text.find("<")
        tag_end = text.find(">", tag_start)
        if tag_end == -1:
            break
        text = text[:tag_start] + text[tag_end+1:]
    return html.unescape(text).strip()

def parse_latest_stories(html_text: str, max_items: int = 6):
    stories = []
    seen_links = set()
    start = 0

    while len(stories) < max_items:
        a_start = html_text.find("<a ", start)
        if a_start == -1:
            break
        a_end = html_text.find(">", a_start)
        if a_end == -1:
            break

        
        href_pos = html_text.find("href=", a_start, a_end)
        if href_pos != -1:
            quote_char = html_text[href_pos+5]
            link_start = href_pos + 6
            link_end = html_text.find(quote_char, link_start)
            href = html_text[link_start:link_end]

            
            if href.startswith("//"):
                href = "https:" + href
            elif href.startswith("/"):
                href = urljoin(BASE_URL, href)

            
            close_tag = html_text.find("</a>", a_end)
            link_text = html_text[a_end+1:close_tag]
            link_text = strip_tags(link_text)

            
            if (
                href.startswith("https://time.com") and
                "/20" in href and   # crude check for article year
                href not in seen_links and
                link_text
            ):
                stories.append({"title": link_text, "link": href})
                seen_links.add(href)

        start = a_end + 1

    return stories

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/getTimeStories":
            try:
                page_html = fetch_html(BASE_URL)
                items = parse_latest_stories(page_html)
                response = json.dumps(items, indent=2)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(response.encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Use /getTimeStories to fetch latest 6 stories.")

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8000), Handler)
    print("Server running on http://127.0.0.1:8000")
    server.serve_forever()
