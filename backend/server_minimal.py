
import http.server
import socketserver
import os

# Port aus Environment holen (Cloud Run Standard)
PORT = int(os.environ.get('PORT', 8080))

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h1>Minimal Server: ONLINE!</h1><p>Wenn du das siehst, ist Cloud Run OK. Der Fehler liegt in Flask/Dependencies.</p>")

print(f"Starting minimal server on port {PORT}...")
with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    httpd.serve_forever()
