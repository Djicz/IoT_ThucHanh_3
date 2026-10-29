"""Bai 1: GET greeting and receive student messages with POST."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import aiocoap
from aiocoap import resource
from common import now, parser, run, serve


class MessageResource(resource.Resource):
    def __init__(self):
        super().__init__()
        self.message = "Xin chao tu CoAP Server"

    async def render_get(self, request):
        print("GET request received: /iot/lab/message", flush=True)
        return aiocoap.Message(code=aiocoap.CONTENT, payload=self.message.encode("utf-8"), content_format=0)

    async def render_post(self, request):
        try:
            message = request.payload.decode("utf-8").strip()
        except UnicodeDecodeError:
            return aiocoap.Message(code=aiocoap.BAD_REQUEST, payload=b"Payload must be UTF-8")
        if not message:
            return aiocoap.Message(code=aiocoap.BAD_REQUEST, payload=b"Message must not be empty")
        self.message = message
        print(f"POST request received:\nPayload: {message}\nTime: {now()}", flush=True)
        return aiocoap.Message(code=aiocoap.CHANGED, payload=b"Server da nhan thong diep", content_format=0)


async def main():
    args = parser(__doc__, server=True).parse_args()
    site = resource.Site()
    site.add_resource(["iot", "lab", "message"], MessageResource())
    await serve(site, args)


if __name__ == "__main__":
    run(main)
