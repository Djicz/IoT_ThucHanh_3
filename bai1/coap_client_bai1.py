"""Bai 1: GET and POST student information."""
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
    cli.add_argument("--name", help="Ho ten sinh vien")
    cli.add_argument("--student-id", help="Ma sinh vien")
    cli.add_argument("--message", default="Xin chao tu CoAP Client")
    cli.add_argument("--count", type=int, default=1, help="So thong diep POST")
    args = cli.parse_args()
    if args.count < 1:
        cli.error("--count phai >= 1")
    name = (args.name or input("Ho ten sinh vien: ")).strip()
    student_id = (args.student_id or input("Ma sinh vien: ")).strip()
    if not name or not student_id or not args.message.strip():
        cli.error("Ho ten, ma sinh vien va noi dung khong duoc rong")
    target = uri(args, "iot/lab/message")
    context = await client_context()
    try:
        print(f"Sending GET request...\nURI: {target}", flush=True)
        await exchange(context, aiocoap.Message(code=aiocoap.GET, uri=target), args.timeout)
        for _ in range(args.count):
            payload = f"{args.message} - {student_id} - {name}"
            print(f"Sending POST request...\nPayload: {payload}", flush=True)
            await exchange(context, aiocoap.Message(code=aiocoap.POST, uri=target,
                           payload=payload.encode("utf-8"), content_format=0), args.timeout)
    finally:
        await context.shutdown()


if __name__ == "__main__":
    run(main)
