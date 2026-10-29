"""Bai 2: query sensor every 3 seconds until Ctrl+C."""
import asyncio
import csv
import math
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import aiocoap
from common import client_context, decode_json, exchange, now, parser, run, uri


def warnings(temperature, humidity):
    result = []
    if temperature > 35:
        result.append("CANH BAO: Nhiet do cao")
    if humidity < 40:
        result.append("CANH BAO: Do am thap")
    return result or ["Trang thai: Binh thuong"]


def display(response, device):
    data = decode_json(response)
    if data.get("device_id") != device:
        raise ValueError("Ma thiet bi khong khop")
    temperature, humidity = data["temperature"], data["humidity"]
    for value in (temperature, humidity):
        if type(value) not in (float, int) or not math.isfinite(value):
            raise ValueError("Du lieu cam bien phai la so huu han")
    if not 0 <= humidity <= 100:
        raise ValueError("Do am ngoai khoang 0..100")
    print(f"[{now()}] Received sensor data\nDevice: {device}\n"
          f"Temperature: {temperature} C\nHumidity: {humidity} %", flush=True)
    print("\n".join(warnings(temperature, humidity)), flush=True)
    print("------------------------------", flush=True)
    return data


async def main():
    cli = parser(__doc__)
    cli.add_argument("--device", default="sensor01")
    cli.add_argument("--count", type=int, default=0, help="0: chay den Ctrl+C")
    cli.add_argument("--csv", help="Duong dan file CSV de luu du lieu")
    args = cli.parse_args()
    if args.count < 0 or not args.device.isalnum():
        cli.error("--count >= 0; --device chi chua chu va so")
    context = await client_context()
    attempts = successes = 0
    elapsed = 0.0
    output = None
    try:
        if args.csv:
            path = Path(args.csv)
            path.parent.mkdir(parents=True, exist_ok=True)
            has_data = path.exists() and path.stat().st_size > 0
            output = path.open("a", newline="", encoding="utf-8")
            writer = csv.DictWriter(output, fieldnames=["received_at", "device_id", "temperature", "humidity"])
            if not has_data:
                writer.writeheader()
        while args.count == 0 or attempts < args.count:
            start = time.monotonic()
            attempts += 1
            response = await exchange(context, aiocoap.Message(code=aiocoap.GET,
                                      uri=uri(args, f"iot/lab/{args.device}/data")), args.timeout)
            if response is not None:
                elapsed += time.monotonic() - start
                successes += 1
                try:
                    data = display(response, args.device)
                    if output:
                        writer.writerow({"received_at": now(), **{key: data[key] for key in
                                         ("device_id", "temperature", "humidity")}})
                        output.flush()
                except (ValueError, KeyError, UnicodeError) as exc:
                    print(f"Du lieu khong hop le: {exc}", flush=True)
            if args.count == 0 or attempts < args.count:
                await asyncio.sleep(max(0, 3 - (time.monotonic() - start)))
    finally:
        if output:
            output.close()
        print(f"GET requests: {attempts}; responses: {successes}; "
              f"average response: {elapsed / successes if successes else 0:.4f} s", flush=True)
        await context.shutdown()


if __name__ == "__main__":
    run(main)
