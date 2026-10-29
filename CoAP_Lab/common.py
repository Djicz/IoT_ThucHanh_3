"""Shared IPv4 UDP transport, CLI options and safe CoAP requests."""
import argparse
import asyncio
import json
from datetime import datetime

import aiocoap


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


def json_response(data, code=aiocoap.CONTENT):
    return aiocoap.Message(code=code, payload=json.dumps(data, ensure_ascii=False).encode("utf-8"),
                          content_format=50)


async def client_context():
    # These UDP transports also work on Windows, where udp6 is unavailable.
    return await aiocoap.Context.create_client_context(transports=["simple6"])


async def serve(site, args):
    context = await aiocoap.Context.create_server_context(
        site, bind=(args.host, args.port), transports=["simplesocketserver"])
    print(f"CoAP Server started on {args.host}:{args.port} (UDP)", flush=True)
    try:
        await asyncio.get_running_loop().create_future()
    finally:
        await context.shutdown()


async def exchange(context, message, timeout):
    request = context.request(message)
    try:
        response = await asyncio.wait_for(request.response, timeout)
    except (asyncio.TimeoutError, aiocoap.error.Error, OSError) as exc:
        if not request.response.done():
            request.response.cancel()
        print(f"Loi ket noi/timeout: {type(exc).__name__}: {exc}", flush=True)
        return None
    print(f"Code: {response.code}\nPayload: {response.payload.decode('utf-8', errors='replace')}", flush=True)
    if not response.code.is_successful():
        print("Server tra ve loi CoAP", flush=True)
        return None
    return response


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
