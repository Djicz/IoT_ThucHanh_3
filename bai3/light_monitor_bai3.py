"""Bai 3: one Observe registration; no periodic GET requests."""
import asyncio
import aiocoap
import argparse
import json
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


def uri(args, path):
    return f"coap://{args.host}:{args.port}/{path}"


async def client_context():
    # These UDP transports also work on Windows, where udp6 is unavailable.
    return await aiocoap.Context.create_client_context(transports=["simple6"])


def decode_json(response):
    if response.opt.content_format != 50:
        raise ValueError("Content-Format phai la application/json (50)")
    data = json.loads(response.payload.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Payload phai la JSON object")
    return data


def run(main):
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, EOFError):
        print("\nDa dung chuong trinh.")
    except (OSError, aiocoap.error.Error) as exc:
        raise SystemExit(f"Khong the khoi tao/giao tiep CoAP: {exc}") from exc


def display(response, initial=False):
    if not response.code.is_successful():
        raise ValueError(f"Server tra ve {response.code}")
    data = decode_json(response)
    if data.get("device_id") != "light01" or data.get("status") not in ("ON", "OFF"):
        raise ValueError("Trang thai den khong hop le")
    print(f"[{now()}] {'Initial State' if initial else 'State Updated'}\n"
          f"Device: {data['device_id']}\nStatus: {data['status']}", flush=True)


async def main():
    args = parser(__doc__).parse_args()
    context = await client_context()
    request = context.request(aiocoap.Message(code=aiocoap.GET,
                              uri=uri(args, "iot/lab/light01/status"), observe=0))
    try:
        print("Registering CoAP Observe...", flush=True)
        response = await asyncio.wait_for(request.response, args.timeout)
        display(response, initial=True)
        if response.opt.observe is None:
            raise ValueError("Server khong chap nhan CoAP Observe")
        print("Observe registration successful", flush=True)
        async for notification in request.observation:
            display(notification)
        print("Server da ket thuc Observe. Chay lai client de dang ky lai.", flush=True)
    except (asyncio.TimeoutError, aiocoap.error.Error, OSError, ValueError, KeyError, UnicodeError) as exc:
        print(f"Loi Observe/ket noi: {type(exc).__name__}: {exc}", flush=True)
    finally:
        if not request.observation.cancelled:
            request.observation.cancel()
        if not request.response.done():
            request.response.cancel()
        await context.shutdown()


if __name__ == "__main__":
    run(main)
