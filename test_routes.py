
import requests

BASE = "http://localhost:8082"
DEVICE_ID = "capsula-neo-test-device"

passed = 0
failed = 0


def check(name, method, path, expected_status=200, **kwargs):
    global passed, failed

    try:
        response = requests.request(
            method,
            BASE + path,
            timeout=10,
            **kwargs,
        )

        assert response.status_code == expected_status, (
            f"HTTP {response.status_code}: {response.text[:300]}"
        )

        try:
            data = response.json()
        except ValueError:
            data = response.text

        passed += 1
        print(f"[PASS] {name}")
        return data

    except Exception as exc:
        failed += 1
        print(f"[FAIL] {name}: {exc}")
        return None


print("\n=== DEVICE ROUTES TEST ===\n")


# Firmware
firmware = check(
    "GET firmware",
    "GET",
    "/device/firmware",
)

if firmware:
    result = firmware.get("result", {})
    assert result.get("platform") == "capsula-neo-1"
    assert result.get("version") == "3.5"
    print("       firmware payload OK")


# Device stat
check(
    "POST device stat",
    "POST",
    "/device/stat",
    json={},
)


# Reminders
reminders = check(
    "GET reminders",
    "GET",
    "/account/settings/v1/reminders",
)

if reminders:
    assert isinstance(reminders.get("result"), list)


# Night mode GET
night = check(
    "GET night mode",
    "GET",
    f"/device/settings/v1/{DEVICE_ID}/night_mode",
)

if night:
    assert isinstance(night.get("result"), list)
    assert night["result"][0]["enabled"] in (True, False)


# Night mode PUT
updated_night = check(
    "PUT night mode",
    "PUT",
    f"/device/settings/v1/{DEVICE_ID}/night_mode/test",
    json={"enabled": False},
)

if updated_night:
    assert updated_night["result"][0]["enabled"] is False

night = check(
    "GET night mode after update",
    "GET",
    f"/device/settings/v1/{DEVICE_ID}/night_mode",
)

if night:
    assert night["result"][0]["enabled"] is False


# Content privacy
privacy = check(
    "GET content privacy",
    "GET",
    f"/device/settings/v1/{DEVICE_ID}/content_privacy",
)

if privacy:
    assert isinstance(privacy.get("result"), list)


# Safe mode
safe = check(
    "GET safe mode",
    "GET",
    f"/device/settings/v1/{DEVICE_ID}/safe_mode",
)

if safe:
    assert isinstance(safe.get("result"), list)


# General settings
general = check(
    "GET general",
    "GET",
    f"/device/settings/v1/{DEVICE_ID}/general",
)

if general:
    assert isinstance(general.get("result"), list)
    assert "master_volume" in general["result"][0]


# General settings PUT
updated_general = check(
    "PUT general master_volume",
    "PUT",
    f"/device/settings/v1/{DEVICE_ID}/general/master_volume",
    json={"master_volume": 60},
)

general = check(
    "GET general after update",
    "GET",
    f"/device/settings/v1/{DEVICE_ID}/general",
)

if general:
    assert general["result"][0]["master_volume"] == 60


# Alarm music
alarm_music = check(
    "GET alarm music",
    "GET",
    f"/device/settings/v1/{DEVICE_ID}/alarm_music",
)

if alarm_music:
    assert alarm_music.get("result") == []


# Alarms
alarms = check(
    "GET alarms",
    "GET",
    f"/device/settings/v1/{DEVICE_ID}/alarms",
)

if alarms:
    assert isinstance(alarms.get("result"), list)


# Runtime logs
check(
    "POST runtime logs",
    "POST",
    "/rt_logs/send",
    headers={"Content-Type": "application/x-msgpack"},
    data=b"",
)

print("\n=== SUMMARY ===")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Total:  {passed + failed}")
