import datetime
import json
import mimetypes
import pathlib
import re
import socket
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

BASE_DIR = pathlib.Path()


class Website(BaseHTTPRequestHandler):
    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self, file):
        mt, _ = mimetypes.guess_type(self.path)
        if mt:
            self.send_response(200)
            self.send_header("Content-type", mt)
            self.end_headers()
            with open(file, 'rb') as fd:
                self.wfile.write(fd.read())
        else:
            self.send_response(404)
            self.send_html_file('error.html', 404)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(content_length)
        self.send_data_via_socket(data.decode())
        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()

    def do_GET(self):
        self.router()

    def router(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            file = BASE_DIR.joinpath(pr_url.path[1:])
            if file.exists():
                self.send_static(file)
            else:
                self.send_html_file('error.html', 404)

    def send_data_via_socket(self, message):
        HOST = (socket.gethostname(), 5000)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(HOST)
        client.send(message.encode())
        client.close()


def normalize(input):
    pattern = r'(\w+)=(\w+)'
    matches = re.findall(pattern, input)
    message = {
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f', ): {"username": matches[0][1],
                                                                     "message": matches[1][1]}}
    save_into_json(message)


def save_into_json(input_data):
    try:
        with open("storage/data.json", "r") as f:
            from_file = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        from_file = {}

    from_file.update(input_data)

    with open("storage/data.json", "w") as f:
        json.dump(from_file, f, indent=2)


def socket_serv():
    HOST = (socket.gethostname(), 5000)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(HOST)
    s.listen()
    print("server is listening")

    conn, address = s.accept()
    print(f"Accepted connection from {address}")
    try:
        message = ""
        while True:
            data = conn.recv(100).decode()
            message += data
            print(f"message: {message}")
            if not data:
                normalize(message)
                message = ""
                conn, addr = s.accept()
    finally:
        conn.close()


def run(server_class=HTTPServer, handler_class=Website):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        socket_server = Thread(target=socket_serv)
        socket_server.start()
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == "__main__":
    run()
