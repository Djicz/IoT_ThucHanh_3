"""Bai 3: one Observe registration; no periodic GET requests."""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import aiocoap
from common import client_context, decode_json, now, parser, run, uri


def display(response, initial=False):
    if not response.code.is_successful():
        raise ValueError(f"Server tra ve {response.code}")
    data = decode_json(response)
    if data.get("device_id") != "light01" or data.get("status") not in ("ON", "OFF"):
        raise ValueError("Trang thai den khong hop le")
    print(f"[{now()}] {'Initial State' if initial else 'State Updated'}\n"
          f"Device: {data['device_id']}\nStatus: {data['status']}", flush=True)


async def main():
    args = parser(__doc__).parse_args()
    context = await client_context()
    request = context.request(aiocoap.Message(code=aiocoap.GET,
                              uri=uri(args, "iot/lab/light01/status"), observe=0))
    try:
        print("Registering CoAP Observe...", flush=True)
        response = await asyncio.wait_for(request.response, args.timeout)
        display(response, initial=True)
        if response.opt.observe is None:
            raise ValueError("Server khong chap nhan CoAP Observe")
        print("Observe registration successful", flush=True)
        async for notification in request.observation:
            display(notification)
        print("Server da ket thuc Observe. Chay lai client de dang ky lai.", flush=True)
    except (asyncio.TimeoutError, aiocoap.error.Error, OSError, ValueError, KeyError, UnicodeError) as exc:
        print(f"Loi Observe/ket noi: {type(exc).__name__}: {exc}", flush=True)
    finally:
        if not request.observation.cancelled:
            request.observation.cancel()
        if not request.response.done():
            request.response.cancel()
        await context.shutdown()


if __name__ == "__main__":
    run(main)
