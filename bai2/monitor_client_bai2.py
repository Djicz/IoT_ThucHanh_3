"""Bai 2: query sensor every 3 seconds until Ctrl+C."""
import asyncio
import csv
import math
import time
from pathlib import Path
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
