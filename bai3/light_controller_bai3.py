"""Bai 3: interactive ON/OFF/STATUS/EXIT controller."""
import json
import aiocoap
import argparse
import asyncio


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


def run(main):
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, EOFError):
        print("\nDa dung chuong trinh.")
    except (OSError, aiocoap.error.Error) as exc:
        raise SystemExit(f"Khong the khoi tao/giao tiep CoAP: {exc}") from exc


async def main():
    cli = parser(__doc__)
    cli.add_argument("--commands", nargs="+", help="Chay chuoi lenh thay cho nhap ban phim")
    cli.add_argument("--non", action="store_true", help="Gui NON thay cho CON (mac dinh)")
    args = cli.parse_args()
    context = await client_context()
    commands = iter(args.commands) if args.commands else None
    try:
        while True:
            # input is deliberately synchronous: no other job runs in this controller.
            # This also lets Ctrl+C stop input immediately on Windows.
            command = (next(commands, "EXIT") if commands is not None else
                       input("Nhap lenh (ON/OFF/STATUS/EXIT): ")).strip().upper()
            if command == "EXIT":
                break
            if command not in ("ON", "OFF", "STATUS"):
                print("Lenh khong hop le. Chi dung ON/OFF/STATUS/EXIT.", flush=True)
                continue
            options = {"uri": uri(args, "iot/lab/light01/status"),
                       "transport_tuning": aiocoap.Unreliable() if args.non else aiocoap.Reliable()}
            if command == "STATUS":
                message = aiocoap.Message(code=aiocoap.GET, **options)
            else:
                message = aiocoap.Message(code=aiocoap.PUT, content_format=50,
                    payload=json.dumps({"device_id": "light01", "command": command}).encode(), **options)
            print(f"Sending {message.code} request...", flush=True)
            response = await exchange(context, message, args.timeout)
            if response is not None and command in ("ON", "OFF"):
                print("Da bat den light01" if command == "ON" else "Da tat den light01", flush=True)
    finally:
        await context.shutdown()


if __name__ == "__main__":
    run(main)
