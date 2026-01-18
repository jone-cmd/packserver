"""
A simple MC resource pack server
"""
import contextlib
import hashlib
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
import websocket
import click

MC_SERVER_MANAGEMENT_ENDPOINT: str = ""
MC_SERVER_MANAGEMENT_TOKEN: str = ""
pack: bytes = b""
pack_hash: str = ""
pack_size: int = 0
pack_size_str: str = ""
pack_content_type: str = ""
pack_path: str = ""
four04_response: bytes = b""
four04_response_size: int = 0
four04_response_size_str: str = ""
four04_response_content_type: str = ""

def player_online(username: str, uuid: str) -> bool:
    """
    Check if player with the given USERNAME and UUID is online on MC_SERVER_MANAGEMENT_ENDPOINT using Minecraft Server Management Protocol.
    """
    if not MC_SERVER_MANAGEMENT_ENDPOINT:
        raise RuntimeError(f"MC_SERVER_MANAGEMENT_ENDPOINT not defined")
    if not MC_SERVER_MANAGEMENT_TOKEN:
        raise RuntimeError(f"MC_SERVER_MANAGEMENT_TOKEN not defined")
    payload = {
        "jsonrpc": "2.0",
        "method": "minecraft:players",
        "id": 0
    }
    with contextlib.closing(websocket.create_connection(MC_SERVER_MANAGEMENT_ENDPOINT, header=[f"Authorization: Bearer {MC_SERVER_MANAGEMENT_TOKEN}"])) as connection:
        connection.send(json.dumps(payload))
        result = json.loads(connection.recv())
    result = result.get("result")
    return result and len([player for player in result if player["name"] == username and player["id"] == uuid]) > 0



class RequestHandler(SimpleHTTPRequestHandler):
    """
    Main class to serve server resource packs.
    """
    server_version = "PackServer"

    def send_common_headers(self):
        """
        Send the common headers.
        """
        self.send_header("Server", self.server_version)

    def send_200(self, head_only=False):
        """
        Send a 200 response.
        """
        self.send_response(200)
        self.send_common_headers()
        self.send_header("Content-Type", pack_content_type)
        self.send_header("Content-Length", pack_size_str)
        self.end_headers()
        if head_only:
            return
        self.wfile.write(pack)

    def send_404(self, head_only=False):
        """
        Send a 404 response.
        """
        self.send_response(404)
        self.send_header("Content-Type", four04_response_content_type)
        self.send_header("Content-Length", four04_response_size_str)
        self.send_common_headers()
        self.end_headers()
        if head_only:
            return
        self.wfile.write(four04_response)

    def do_GET(self, head_only=False):
        """
        Serve pack
        """
        if (self.path == pack_path and self.headers.get("X-Minecraft-Version-ID") and self.headers.get(
                "X-Minecraft-Pack-Format") and self.headers.get("X-Minecraft-Pack-Version") and self.headers.get(
            "X-Minecraft-Pack-Version-ID") and self.headers.get("User-Agent", "").startswith(
            "Minecraft Java/") and self.headers.get("X-Minecraft-Username") and self.headers.get("X-Minecraft-UUID")):
            username = self.headers.get("X-Minecraft-Username")
            uuid = self.headers.get("X-Minecraft-UUID")
            if player_online(username, uuid):
                self.send_200(head_only=head_only)
        self.send_404(head_only=head_only)

    def do_HEAD(self):
        """
        Do a HEAD request.
        """
        return self.do_GET(head_only=True)


@click.command()
@click.argument("server_management_endpoint")
@click.argument("token")
@click.option("--host", "--bind", "-h", "-b", default="0.0.0.0")
@click.option("--port", "-p", type=int, default=8000)
@click.option("--pack-file", "-P", type=click.Path(exists=True), default="resourcepack.zip")
def main(server_management_endpoint: str, token: str, host: str, port: int, pack_file: str):
    """A simple MC resource pack server"""
    global MC_SERVER_MANAGEMENT_ENDPOINT, MC_SERVER_MANAGEMENT_TOKEN,\
        pack, pack_hash, pack_size, pack_size_str, pack_content_type, pack_path,\
        four04_response, four04_response_size, four04_response_size_str, four04_response_content_type
    MC_SERVER_MANAGEMENT_ENDPOINT = server_management_endpoint
    MC_SERVER_MANAGEMENT_TOKEN = token
    with open(pack_file, "rb") as file:
        pack = file.read()
    pack_hash = hashlib.sha256(pack).hexdigest()
    pack_size = len(pack)
    pack_size_str = str(pack_size)
    pack_content_type = "application/zip"
    pack_path = f"/{pack_hash[:2]}/{pack_hash}.zip"
    four04_response = b"404 - Not Found"
    four04_response_size = len(four04_response)
    four04_response_size_str = str(four04_response_size)
    four04_response_content_type = f"text/plain; charset=utf-8"
    server_address = (host, port)
    httpd = HTTPServer(server_address, RequestHandler)
    try:
        click.echo(f"Serving pack on http://{host}:{port}{pack_path} (Ctrl+C to stop)...")
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
