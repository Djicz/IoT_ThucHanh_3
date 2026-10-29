"""Bai 3: smart light with GET, PUT and real CoAP Observe."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import aiocoap
from aiocoap import resource
from common import json_response, now, parser, run, serve


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
