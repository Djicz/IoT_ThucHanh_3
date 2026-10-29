"""Bai 2: simulated temperature and humidity, updated every 3 seconds."""
import asyncio
import random
from contextlib import suppress
from aiocoap import resource
import argparse
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


class SensorResource(resource.Resource):
    def __init__(self, device_id="sensor01"):
        super().__init__()
        self.device_id = device_id
        self.update()

    def update(self):
        self.data = {"device_id": self.device_id,
                     "temperature": round(random.uniform(20, 40), 1),
                     "humidity": round(random.uniform(30, 80), 1), "timestamp": now()}
        print(f"Sensor updated: {self.data}", flush=True)

    async def render_get(self, request):
        print(f"GET {self.device_id}: {now()}", flush=True)
        return json_response(self.data)


async def update_sensors(sensors):
    while True:
        await asyncio.sleep(3)
        for sensor in sensors:
            sensor.update()


async def main():
    cli = parser(__doc__, server=True)
    cli.add_argument("--devices", nargs="+", default=["sensor01"])
    args = cli.parse_args()
    if any(not name.isalnum() for name in args.devices):
        cli.error("Ma cam bien chi chua chu va so")
    site = resource.Site()
    sensors = [SensorResource(name) for name in dict.fromkeys(args.devices)]
    for sensor in sensors:
        site.add_resource(["iot", "lab", sensor.device_id, "data"], sensor)
    updater = asyncio.create_task(update_sensors(sensors))
    try:
        await serve(site, args)
    finally:
        updater.cancel()
        with suppress(asyncio.CancelledError):
            await updater


if __name__ == "__main__":
    run(main)
