import os
import time
from pathlib import Path

import psutil
import requests

TEMP_PATH = Path("/sys/class/thermal/thermal_zone0/temp")

# interval (10 min)
STATUS_INTERVAL = 10 * 60


def get_pi_temperature() -> float | None:
    try:
        if TEMP_PATH.exists():
            raw = TEMP_PATH.read_text().strip()
            milli_c = int(raw)
            return milli_c / 1000.0
        else:
            return None
    except Exception:
        return None


def get_cpu_usage() -> float:
    return psutil.cpu_percent(interval=None)


def get_ram_usage() -> float:
    mem = psutil.virtual_memory()
    return mem.percent


def build_status_text() -> str:
    t = get_pi_temperature()
    cpu = get_cpu_usage()
    ram = get_ram_usage()

    lines = []
    if t is None:
        lines.append(
            "🌡 Can't read temperature "
            "(/sys/class/thermal/thermal_zone0/temp unavailable)"
        )
    else:
        lines.append(f"🌡 Temperature of Raspberry Pi: {t:.1f} °C")

    lines.append(f"🧠 CPU Load: {cpu:.0f} %")
    lines.append(f"💾 Using RAM: {ram:.0f} %")

    return "\n".join(lines)


def send_message(base_url: str, chat_id: int, text: str):
    try:
        requests.post(
            base_url + "/sendMessage",
            data={"chat_id": chat_id, "text": text},
            timeout=30,
        )
    except Exception as e:
        print("⚠ Error sendMessage:", e)


def main():
    token = os.getenv("TG_BOT_TOKEN")
    if not token:
        print("ERROR: TG_BOT_TOKEN hasn't set")
        time.sleep(5)
        return

    base_url = f"https://api.telegram.org/bot{token}"
    print("Bot is running (simple_bot). Commands: /start, /stop, /temp")

    offset = None

    # who subscribed: chat_id -> next send time (unix time)
    subscribers: dict[int, float] = {}

    while True:
        now = time.time()

        # 1) long polling getUpdates
        try:
            params = {"timeout": 50}
            if offset is not None:
                params["offset"] = offset

            resp = requests.get(
                base_url + "/getUpdates",
                params=params,
                timeout=60,
            )
            data = resp.json()

            if not data.get("ok"):
                print("⚠ getUpdates returns error:", data)
                time.sleep(3)
                continue

            updates = data.get("result", [])
            for upd in updates:
                offset = upd["update_id"] + 1

                message = upd.get("message")
                if not message:
                    continue

                chat_id = message["chat"]["id"]
                text = (message.get("text") or "").strip()

                if text == "/start":
                    subscribers[chat_id] = now + STATUS_INTERVAL
                    send_message(
                        base_url,
                        chat_id,
                        "subscribed for autostatus every 10 min.\n"
                        "Команды:\n"
                        "/temp — get status now\n"
                        "/stop — cancel autupdate",
                    )
                    # show current status
                    send_message(base_url, chat_id, build_status_text())

                elif text == "/stop":
                    if chat_id in subscribers:
                        del subscribers[chat_id]
                        send_message(base_url, chat_id, "Update disabled.")
                    else:
                        send_message(base_url, chat_id, "You're not subscribe for updates.")

                elif text == "/temp":
                    send_message(base_url, chat_id, build_status_text())

                # ignore the rest
        except Exception as e:
            print("⚠ Error in getUpdates cicle:", e)
            time.sleep(5)

        # 2) check where to send auto status
        now = time.time()
        for chat_id, next_ts in list(subscribers.items()):
            if now >= next_ts:
                send_message(base_url, chat_id, build_status_text())
                subscribers[chat_id] = now + STATUS_INTERVAL


if __name__ == "__main__":
    main()
