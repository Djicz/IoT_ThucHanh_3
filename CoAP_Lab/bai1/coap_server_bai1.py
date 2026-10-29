"""Bai 1: GET greeting and receive student messages with POST."""
import aiocoap
from aiocoap import resource
import argparse
import asyncio
from datetime import datetime


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def positive(value):
    result = float(value)
    if not 0 < result < float("inf"):
        raise argparse.ArgumentTypeError("Gia tri phai la so duong huu han")
    return result


def parser(description, server=False):
    result = argparse.ArgumentParser(description=description)
    result.add_argument("--host", default="127.0.0.1",
                        help="IPv4 cua server; server dung dia chi IP cua may de nghe LAN")
    result.add_argument("--port", type=int, default=5683, choices=range(1, 65536),
                        metavar="PORT")
    if not server:
        result.add_argument("--timeout", type=positive, default=5.0)
    return result


async def serve(site, args):
    context = await aiocoap.Context.create_server_context(
        site, bind=(args.host, args.port), transports=["simplesocketserver"])
    print(f"CoAP Server started on {args.host}:{args.port} (UDP)", flush=True)
    try:
        await asyncio.get_running_loop().create_future()
    finally:
        await context.shutdown()


def run(main):
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, EOFError):
        print("\nDa dung chuong trinh.")
    except (OSError, aiocoap.error.Error) as exc:
        raise SystemExit(f"Khong the khoi tao/giao tiep CoAP: {exc}") from exc


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
