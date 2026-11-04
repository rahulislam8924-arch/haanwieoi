#!/usr/bin/env python3
"""Tiny static player server for the Pace video deliverables.

Why this exists instead of `python3 -m http.server`:
  * it survives /tmp getting wiped (pages live in the repo),
  * it sends real HTTP Range responses, so seeking/scrubbing in the browser
    video player works properly,
  * it only exposes this folder + the mp4s in `out/`, nothing else.

Usage:
    python3 players/serve.py --port 8100
"""
from __future__ import annotations

import argparse
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "out")

PAGES = {"": "index.html", "/": "index.html", "/index.html": "index.html"}
VIDEO_DIRS = [OUT, HERE]
TYPES = {".html": "text/html; charset=utf-8", ".mp4": "video/mp4",
         ".mp3": "audio/mpeg", ".png": "image/png", ".jpg": "image/jpeg",
         ".css": "text/css; charset=utf-8", ".js": "application/javascript"}


def resolve(path: str):
    path = path.split("?", 1)[0].split("#", 1)[0]
    if path in PAGES:
        return os.path.join(HERE, PAGES[path])
    name = os.path.basename(path)
    if not re.fullmatch(r"[A-Za-z0-9._-]+\.(mp4|mp3|png|jpg|css|js)", name):
        return None
    for d in VIDEO_DIRS:
        cand = os.path.join(d, name)
        if os.path.isfile(cand) and os.path.realpath(cand).startswith(
                (os.path.realpath(OUT), os.path.realpath(HERE))):
            return cand
    return None


class Handler(BaseHTTPRequestHandler):
    server_version = "PacePlayer/1.0"

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Range")
        self.send_header("Access-Control-Expose-Headers",
                         "Content-Range, Content-Length, Accept-Ranges")

    def do_HEAD(self):
        self._serve(head_only=True)

    def do_GET(self):
        self._serve(head_only=False)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def _serve(self, head_only: bool):
        target = resolve(self.path)
        if not target or not os.path.isfile(target):
            body = b"not found\n"
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self._cors()
            self.end_headers()
            if not head_only:
                self.wfile.write(body)
            return

        size = os.path.getsize(target)
        ctype = TYPES.get(os.path.splitext(target)[1].lower(),
                          "application/octet-stream")
        start, end = 0, size - 1
        rng = self.headers.get("Range", "")
        partial = False
        m = re.match(r"bytes=(\d*)-(\d*)$", rng.strip())
        if m and size:
            partial = True
            if m.group(1):
                start = int(m.group(1))
                end = int(m.group(2)) if m.group(2) else size - 1
            else:  # suffix range: bytes=-N
                start = max(0, size - int(m.group(2) or 0))
            end = min(end, size - 1)
            if start > end:
                self.send_response(416)
                self.send_header("Content-Range", "bytes */%d" % size)
                self._cors()
                self.end_headers()
                return

        length = end - start + 1
        self.send_response(206 if partial else 200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")
        if partial:
            self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, size))
        self._cors()
        self.end_headers()
        if head_only:
            return
        with open(target, "rb") as fh:
            fh.seek(start)
            left = length
            while left > 0:
                chunk = fh.read(min(256 * 1024, left))
                if not chunk:
                    break
                self.wfile.write(chunk)
                left -= len(chunk)

    def log_message(self, fmt, *args):  # keep the log short
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8100)
    ap.add_argument("--host", default="0.0.0.0")
    args = ap.parse_args()
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    srv.daemon_threads = True
    print("serving %s on http://%s:%d" % (HERE, args.host, args.port), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
