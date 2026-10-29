"""Bai 3: interactive ON/OFF/STATUS/EXIT controller."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import aiocoap
from common import client_context, exchange, parser, run, uri


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
