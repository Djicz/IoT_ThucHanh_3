"""Bai 3: smart light with GET, PUT and real CoAP Observe."""
import json
from pathlib import Path
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


def json_response(data, code=aiocoap.CONTENT):
    return aiocoap.Message(code=code, payload=json.dumps(data, ensure_ascii=False).encode("utf-8"),
                          content_format=50)


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


class LightResource(resource.ObservableResource):
    def __init__(self, log_path=None):
        super().__init__()
        self.status = "OFF"
        self.log_path = log_path

    def update_observation_count(self, count):
        print(f"Observe clients: {count}", flush=True)

    async def render_get(self, request):
        return json_response({"device_id": "light01", "status": self.status})

    async def render_put(self, request):
        if request.opt.content_format != 50:
            return json_response({"error": "Use application/json (50)"}, aiocoap.UNSUPPORTED_CONTENT_FORMAT)
        try:
            data = json.loads(request.payload.decode("utf-8"))
        except (ValueError, UnicodeError):
            return json_response({"error": "Invalid UTF-8 JSON"}, aiocoap.BAD_REQUEST)
        if not isinstance(data, dict) or data.get("device_id") != "light01":
            return json_response({"error": "device_id must be light01"}, aiocoap.BAD_REQUEST)
        command = data.get("command")
        if command not in ("ON", "OFF"):
            return json_response({"error": "command must be ON or OFF"}, aiocoap.BAD_REQUEST)
        print(f"PUT request received:\nDevice: light01\nCommand: {command}", flush=True)
        previous = self.status
        if previous != command:
            if self.log_path:
                try:
                    self.log_path.parent.mkdir(parents=True, exist_ok=True)
                    with self.log_path.open("a", encoding="utf-8") as log:
                        log.write(json.dumps({"timestamp": now(), "device_id": "light01",
                                             "previous": previous, "status": command}) + "\n")
                except OSError as exc:
                    print(f"Cannot write state log: {exc}", flush=True)
                    return json_response({"error": "Cannot write state log"}, aiocoap.INTERNAL_SERVER_ERROR)
            self.status = command
            print(f"Light state changed: {previous} -> {command}\nNotify observers: {command}", flush=True)
            self.updated_state()
        return json_response({"device_id": "light01", "status": self.status}, aiocoap.CHANGED)


async def main():
    cli = parser(__doc__, server=True)
    cli.add_argument("--log", type=Path, help="Ghi thay doi trang thai vao JSON Lines")
    args = cli.parse_args()
    site = resource.Site()
    site.add_resource(["iot", "lab", "light01", "status"], LightResource(args.log))
    print("Resource: /iot/lab/light01/status; initial state: OFF", flush=True)
    await serve(site, args)


if __name__ == "__main__":
    run(main)
