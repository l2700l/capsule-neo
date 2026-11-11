
import json
import os
import tempfile
import time
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from copy import deepcopy
from pathlib import Path
from threading import RLock


DEVICE_ID = "capsula-neo-test-device"


class DeviceState:
    def __init__(self, timezone_name: str, storage_path):
        self._lock = RLock()
        self._storage_path = Path(storage_path)
        self._alarm_refresh_pending = set()
        self._alarm_refresh_done = set()
        self._settings = {
            "general": {
                "home_id": "test-home",
                "room_id": "",
                "groups": [],
                "id": DEVICE_ID,
                "revision": 1,
                "name": "Capsule Neo",
                "coordinates": [0.0, 0.0],
                "timezone": timezone_name,
                "keyword_sound": True,
                "children_mode": False,
                "alarm_volume": 40,
                "master_volume": 35,
                "skillserver_type": "",
                "reminder_sync": True,
                "allow_music_from_app": True,
                "upnp_discovery": False,
                "bt_handsfree": False,
                "blackbox_depth": 30,
                "clock_brightness": -1,
                "clock_night_brightness": -1,
                "clock_enabled": True,
                "demomode_enabled_at": None,
                "is_blocked": False,
                "speaker_calls_available": False,
                "baby_monitor_calls_available": False,
            },
            "night_mode": {
                "id": DEVICE_ID,
                "revision": 1,
                "enabled": True,
                "scheduled": True,
                "start_at": 0,
                "stop_at": 36000,
            },
            "content_privacy": {
                "id": DEVICE_ID,
                "revision": 1,
                "mail": False,
                "calendar": False,
                "vk_messages": False,
                "telegram": True,
                "vk_messages_notifications": False,
            },
            "safe_mode": {
                "id": DEVICE_ID,
                "revision": 1,
                "enabled": False,
            },
        }

        self._alarms = []
        self._reminders = []

        self._load()

    def _load(self):
        try:
            with self._storage_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            return
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[STATE] Cannot load {self._storage_path}: {exc}")
            return

        if not isinstance(data, dict):
            print(f"[STATE] Invalid state file: {self._storage_path}")
            return

        with self._lock:
            settings = data.get("settings", {})

            if isinstance(settings, dict):
                for name, saved in settings.items():
                    current = self._settings.get(name)
                    if not isinstance(current, dict) or not isinstance(saved, dict):
                        continue

                    # Принимаем только известные поля, сохраняя новые
                    # значения по умолчанию для полей будущих версий.
                    for key, value in saved.items():
                        if key in current and key not in {"id"}:
                            current[key] = value

            for name in ("alarms", "reminders"):
                saved = data.get(name)
                if isinstance(saved, list):
                    setattr(self, f"_{name}", saved)

    def save(self):
        with self._lock:
            data = {
                "settings": deepcopy(self._settings),
                "alarms": deepcopy(self._alarms),
                "reminders": deepcopy(self._reminders),
            }

            path = self._storage_path
            path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = None

            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=path.parent,
                    prefix=f".{path.name}.",
                    suffix=".tmp",
                    delete=False,
                ) as file:
                    temp_path = Path(file.name)
                    json.dump(
                        data,
                        file,
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    )
                    file.write("\n")
                    file.flush()
                    os.fsync(file.fileno())

                os.replace(temp_path, path)
            finally:
                if temp_path is not None:
                    try:
                        temp_path.unlink(missing_ok=True)
                    except OSError:
                        pass

    def get_settings(self, name: str) -> dict:
        with self._lock:
            return deepcopy(self._settings[name])

    def update_settings(self, name: str, changes: dict) -> dict:
        with self._lock:
            current = self._settings[name]

            changes = {
                key: value
                for key, value in changes.items()
                if key not in {"id", "revision"}
                and key in current
            }

            if changes:
                current.update(deepcopy(changes))
                current["revision"] += 1
                self.save()

            return deepcopy(current)

    def get_collection(self, name: str) -> list:
        if name not in {"alarms", "reminders"}:
            raise ValueError(f"Unknown collection: {name}")

        with self._lock:
            return deepcopy(getattr(self, f"_{name}"))

    def replace_collection(self, name: str, items: list):
        if name not in {"alarms", "reminders"}:
            raise ValueError(f"Unknown collection: {name}")
        if not isinstance(items, list):
            raise TypeError("Collection must be a list")

        with self._lock:
            setattr(self, f"_{name}", deepcopy(items))
            self.save()

    def add_alarm(self, item: dict) -> dict:
        if not isinstance(item, dict):
            raise TypeError("Alarm must be a dictionary")

        with self._lock:
            alarm = {
                "enabled": item.get("enabled", True),
                "alarm_time": item["alarm_time"],
                "weekdays": deepcopy(item.get("weekdays", [])),
                "first_time": item.get("first_time", 0),
                "id": str(uuid.uuid4()),
                "revision": 1,
                "updated": time.time(),
            }

            self._alarms.append(alarm)
            self.save()

            return deepcopy(alarm)

    def update_alarm(self, alarm_id: str, changes: dict) -> dict | None:
        if not isinstance(changes, dict):
            raise TypeError("Changes must be a dictionary")

        allowed = {
            "enabled",
            "alarm_time",
            "weekdays",
            "first_time",
        }

        changes = {
            key: value
            for key, value in changes.items()
            if key in allowed
        }

        with self._lock:
            for alarm in self._alarms:
                if alarm["id"] != alarm_id:
                    continue

                if changes:
                    alarm.update(deepcopy(changes))
                    alarm["revision"] += 1
                    alarm["updated"] = time.time()
                    self.save()

                return deepcopy(alarm)

        return None

    def disable_alarm(self, alarm_id: str) -> dict | None:
        return self.update_alarm(
            alarm_id,
            {"enabled": False},
        )
    def disable_all_alarms(self) -> list:
        with self._lock:
            now = time.time()
            changed = False

            for alarm in self._alarms:
                if alarm["enabled"]:
                    alarm["enabled"] = False
                    alarm["revision"] += 1
                    alarm["updated"] = now
                    changed = True

            if changed:
                self.save()

            return deepcopy(self._alarms)
    def sync_alarms(self) -> tuple[list, list]:
        with self._lock:
            now = time.time()

            timezone_name = self._settings["general"]["timezone"]
            local_now = datetime.now(ZoneInfo(timezone_name))

            today = local_now.date().isoformat()
            current_midnight = local_now.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            alarms = deepcopy(self._alarms)
            refreshes = []
            changed = False

            for index, alarm in enumerate(self._alarms):
                if not alarm.get("enabled", False):
                    continue

                weekdays = alarm.get("weekdays", [])
                first_time = alarm.get("first_time", 0)

                # Одноразовый будильник.
                if not weekdays:
                    if (
                        isinstance(first_time, (int, float))
                        and not isinstance(first_time, bool)
                        and first_time > 0
                        and first_time + 5 <= now
                    ):
                        alarm["enabled"] = False
                        alarm["revision"] += 1
                        alarm["updated"] = now

                        alarms[index]["enabled"] = False
                        changed = True

                    continue

                # Повторяющийся будильник.
                if local_now.isoweekday() not in weekdays:
                    continue

                alarm_time = alarm.get("alarm_time")

                if (
                    isinstance(alarm_time, bool)
                    or not isinstance(alarm_time, int)
                    or not 0 <= alarm_time < 86400
                ):
                    continue

                scheduled_at = current_midnight + timedelta(
                    seconds=alarm_time + 5
                )

                if local_now < scheduled_at:
                    continue

                alarm_id = alarm["id"]
                key = (alarm_id, today)

                if key in self._alarm_refresh_done:
                    # Уже прошло срабатывание, расписание снова активно.
                    continue

                # Временно выключаем будильник только в ответе колонке.
                alarms[index]["enabled"] = False

                if key not in self._alarm_refresh_pending:
                    self._alarm_refresh_pending.add(key)
                    refreshes.append(key)

            if changed:
                self.save()

            return alarms, refreshes


    def complete_alarm_refresh(self, refreshes: list):
        with self._lock:
            for key in refreshes:
                self._alarm_refresh_pending.discard(key)
                self._alarm_refresh_done.add(key)


    def retry_alarm_refresh(self, refreshes: list):
        with self._lock:
            for key in refreshes:
                self._alarm_refresh_done.discard(key)
                self._alarm_refresh_pending.discard(key)