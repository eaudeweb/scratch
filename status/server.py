import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from multiprocessing import Process

hostName = "0.0.0.0"
serverPort = 8080


class StatusServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<p>Docker container running</p>", "utf-8"))


def func():
    if os.fork() != 0:  # <--
        return  # <--
    print('sub process is running')
    server = HTTPServer((hostName, serverPort), StatusServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

    server.server_close()
    print("Server stopped.")
    print('sub process finished')


if __name__ == '__main__':
    p = Process(target=func)
    p.start()
    p.join()
    print('done')

