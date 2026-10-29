"""Bai 2: simulated temperature and humidity, updated every 3 seconds."""
import asyncio
import random
import sys
from contextlib import suppress
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aiocoap import resource
from common import json_response, now, parser, run, serve


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
