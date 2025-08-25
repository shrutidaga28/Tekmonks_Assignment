from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import urlopen, Request
from urllib.parse import urljoin
import json
import html

TIME_URL = "https://time.com/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def fetch_homepage():
   
    req = Request(TIME_URL, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"})
    with urlopen(req, timeout=10) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def strip_tags(text):
    
    while "<" in text and ">" in text:
        start = text.find("<")
        end = text.find(">", start)
        if end == -1:
            break
        text = text[:start] + text[end + 1 :]
    text = html.unescape(text)
    return " ".join(text.split()).strip()


def extract_stories(html_text, limit=6):
    stories, seen = [], set()
    start = 0

    while len(stories) < limit:
        a_start = html_text.find("<a ", start)
        if a_start == -1:
            break
        a_end = html_text.find(">", a_start)
        if a_end == -1:
            break

        
        href_pos = html_text.find("href=", a_start, a_end)
        if href_pos != -1:
            quote_char = html_text[href_pos + 5]
            link_start = href_pos + 6
            link_end = html_text.find(quote_char, link_start)
            href = html_text[link_start:link_end].strip()

            link = urljoin(TIME_URL, href)

            
            close_tag = html_text.find("</a>", a_end)
            inner_text = html_text[a_end + 1 : close_tag]
            title = strip_tags(inner_text)

            if (
                link.startswith("https://time.com")
                and any(c.isdigit() for c in link)
                and title
                and link not in seen
            ):
                stories.append({"title": title, "link": link})
                seen.add(link)

        start = a_end + 1

    return stories


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, obj, status=200):
        body = json.dumps(obj, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/getTimeStories"):
            try:
                html_text = fetch_homepage()
                stories = extract_stories(html_text, 6)
                self._send_json(stories, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        else:
            self.send_error(404, "Not Found")


def run(port=8000):
    server = HTTPServer(("", port), Handler)
    print(f"Server running at http://localhost:{port}/getTimeStories")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()


if __name__ == "__main__":
    run()

