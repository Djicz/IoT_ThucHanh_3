"""End-to-end checks over real UDP. Run from any working directory."""
import asyncio
from contextlib import suppress
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import aiocoap
from common import client_context, decode_json
from bai2.monitor_client_bai2 import warnings

LOGS = ROOT / "evidence"
LOGS.mkdir(exist_ok=True)
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"}


class Process:
    def __init__(self, script, name, *args):
        self.path = LOGS / name
        self.log = self.path.open("w", encoding="utf-8")
        self.proc = subprocess.Popen([sys.executable, "-u", str(ROOT / script), *args],
                                     stdout=self.log, stderr=subprocess.STDOUT, env=ENV)

    async def wait_for(self, text, timeout=8):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            content = self.path.read_text(encoding="utf-8")
            if text in content:
                return content
            if self.proc.poll() is not None:
                raise AssertionError(f"Process ended early: {content}")
            await asyncio.sleep(0.05)
        raise AssertionError(f"Missing {text}: {self.path.read_text(encoding='utf-8')}")

    def close(self):
        if self.proc.poll() is None:
            self.proc.terminate()
        self.proc.wait(timeout=5)
        self.log.close()


async def cli(script, name, *args):
    process = await asyncio.create_subprocess_exec(sys.executable, "-u", str(ROOT / script), *args,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT, env=ENV)
    output, _ = await asyncio.wait_for(process.communicate(), 20)
    text = "\n".join(line.rstrip() for line in output.decode("utf-8").splitlines()) + "\n"
    (LOGS / name).write_text(text, encoding="utf-8")
    assert process.returncode == 0, text
    return text


async def main():
    report = [f"Python: {sys.version}", f"aiocoap: {importlib.metadata.version('aiocoap')}",
              "Transport: IPv4 UDP, 127.0.0.1:5683"]
    context = await client_context()
    async def request(path, code=aiocoap.GET, payload=None, fmt=50):
        options = {}
        if payload is not None:
            options = {"payload": payload if isinstance(payload, bytes) else json.dumps(payload).encode(),
                       "content_format": fmt}
        return await asyncio.wait_for(context.request(aiocoap.Message(
            code=code, uri=f"coap://127.0.0.1:5683/{path}", **options)).response, 4)

    try:
        server = Process("bai1/coap_server_bai1.py", "bai1_server.log")
        try:
            await server.wait_for("CoAP Server started")
            path = "iot/lab/message"
            response = await request(path)
            assert response.code == aiocoap.CONTENT and response.payload == b"Xin chao tu CoAP Server"
            output = await cli("bai1/coap_client_bai1.py", "bai1_client.log", "--name", "Sinh vien kiem thu",
                               "--student-id", "TEST001", "--count", "2")
            assert output.count("2.04 Changed") == 2
            assert b"TEST001" in (await request(path)).payload
            assert (await request("iot/lab/missing")).code == aiocoap.NOT_FOUND
            assert (await request(path, aiocoap.POST, b"\xff", 0)).code == aiocoap.BAD_REQUEST
            assert (await request(path, aiocoap.POST, b"", 0)).code == aiocoap.BAD_REQUEST
            report.append("PASS bai1: GET greeting, repeated POST, latest message, 4.04, invalid UTF-8/empty POST")
        finally:
            server.close()

        server = Process("bai2/sensor_server_bai2.py", "bai2_server.log", "--devices", "sensor01", "sensor02")
        try:
            await server.wait_for("CoAP Server started")
            before = decode_json(await request("iot/lab/sensor01/data"))
            output = await cli("bai2/monitor_client_bai2.py", "bai2_client.log", "--count", "3",
                               "--csv", str(LOGS / "sensor_data.csv"))
            assert output.count("Received sensor data") == 3
            after = decode_json(await request("iot/lab/sensor01/data"))
            assert before["timestamp"] != after["timestamp"]
            assert decode_json(await request("iot/lab/sensor02/data"))["device_id"] == "sensor02"
            assert 20 <= after["temperature"] <= 40 and 30 <= after["humidity"] <= 80
            assert len(warnings(36.1, 38.7)) == 2
            assert warnings(35, 40) == ["Trang thai: Binh thuong"]
            assert warnings(35.1, 40) == ["CANH BAO: Nhiet do cao"]
            assert warnings(35, 39.9) == ["CANH BAO: Do am thap"]
            report.append("PASS bai2: 3-second updates/polling, JSON format 50, two sensors, CSV, strict alert boundaries")
        finally:
            server.close()

        server = Process("bai3/light_server_bai3.py", "bai3_server.log", "--log", str(LOGS / "light_changes.jsonl"))
        monitors = []
        observations = []
        consumers = []
        try:
            await server.wait_for("CoAP Server started")
            path = "iot/lab/light01/status"
            assert decode_json(await request(path))["status"] == "OFF"
            for index in range(2):
                monitor = Process("bai3/light_monitor_bai3.py", f"bai3_monitor_{index + 1}.log")
                monitors.append(monitor)
                await monitor.wait_for("Observe registration successful")
            # An independent Observe consumer verifies absence of duplicate notifications.
            observer = context.request(aiocoap.Message(code=aiocoap.GET,
                       uri=f"coap://127.0.0.1:5683/{path}", observe=0))
            observations.append(observer)
            initial = await asyncio.wait_for(observer.response, 3)
            assert initial.opt.observe is not None
            queue = asyncio.Queue()
            async def collect():
                async for notification in observer.observation:
                    queue.put_nowait(notification)
            consumers.append(asyncio.create_task(collect()))
            for command in ("ON", "OFF"):
                output = await cli("bai3/light_controller_bai3.py", f"bai3_controller_{command}.log",
                                   "--commands", "INVALID", command, "STATUS", "EXIT")
                assert "2.04 Changed" in output and '"status": "' + command + '"' in output
                notification = await asyncio.wait_for(queue.get(), 3)
                assert decode_json(notification)["status"] == command
                for monitor in monitors:
                    await monitor.wait_for(f"Status: {command}")
                assert (await request(path, aiocoap.PUT, {"device_id": "light01", "command": command})).code == aiocoap.CHANGED
                try:
                    await asyncio.wait_for(queue.get(), 0.5)
                    raise AssertionError("Unchanged status generated a notification")
                except asyncio.TimeoutError:
                    pass
            for payload in (b"{", b"[]", b"\xff", {"device_id": "wrong", "command": "ON"},
                            {"device_id": "light01", "command": "TOGGLE"}, {"device_id": "light01", "command": []}):
                assert (await request(path, aiocoap.PUT, payload)).code == aiocoap.BAD_REQUEST
            assert (await request(path, aiocoap.PUT, b"ON", 0)).code == aiocoap.UNSUPPORTED_CONTENT_FORMAT
            assert decode_json(await request(path))["status"] == "OFF"
            output = await cli("bai3/light_controller_bai3.py", "bai3_non.log", "--non", "--commands", "STATUS", "EXIT")
            assert "2.05 Content" in output
            report.append("PASS bai3: initial OFF, GET/PUT ON/OFF, real Observe to two monitors, no duplicate notification, invalid JSON/device/command/format, NON")
        finally:
            for consumer in consumers:
                consumer.cancel()
                with suppress(asyncio.CancelledError):
                    await consumer
            for observer in observations:
                if not observer.observation.cancelled:
                    observer.observation.cancel()
            for monitor in monitors:
                monitor.close()
            server.close()

        for script, name, args in (
            ("bai1/coap_client_bai1.py", "timeout_bai1.log", ["--name", "Test", "--student-id", "TEST001"]),
            ("bai2/monitor_client_bai2.py", "timeout_bai2.log", ["--count", "1"]),
            ("bai3/light_controller_bai3.py", "timeout_controller.log", ["--commands", "STATUS", "EXIT"]),
            ("bai3/light_monitor_bai3.py", "timeout_observe.log", [])):
            output = await cli(script, name, "--port", "5689", "--timeout", "0.5", *args)
            assert "Loi" in output
            assert "Traceback" not in output
        report.append("PASS connection errors: all four clients exit cleanly when server is absent")
    finally:
        await context.shutdown()
        (LOGS / "verification.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    asyncio.run(main())
