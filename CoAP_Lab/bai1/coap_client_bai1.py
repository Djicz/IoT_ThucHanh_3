"""Bai 1: GET and POST student information."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import aiocoap
from common import client_context, exchange, parser, run, uri


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
