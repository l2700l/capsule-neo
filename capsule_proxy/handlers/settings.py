from ..config import TIMEZONE_NAME

def get_reminders(handler, body=b""):
    """список напоминаний, пример:
{
    "qid": uuid,
    "result": [
        {
            "id": uuid,
            "revision": int, # вероятно отвечает за порядок отображения
            "key": str,
            "text": str,
            "timestamp": timestamp (int),
            "is_done": True,
            "is_read": False,
            "regular_time": 0,
            "weekdays": [],
        }
    ],
}
    """

    return {"result": []}


def _device_id(handler):
    # просто мок
    return "capsula-neo-test-device"


def get_night_mode(handler, body=b""):
    """Информация о ночном режиме
enabled - bool, включен сейчас или нет
scheduled - bool, наличие расписания
start_at - int, время начала расписания, секунды с полуночи 
stop_at - int, время конца расписания, секунды с полуночи 
    """
    return {"result": [{
        "id": _device_id(handler), "revision": 1, "enabled": True,
        "scheduled": True, "start_at": 0, "stop_at": 36000,
    }]}


def get_night_mode_item(handler, body=b""):
    return get_night_mode(handler, body)


def get_content_privacy(handler, body=b""):
    """Настройка "Личный контент на колонке"
telegram - вероятно отголоски прошлого
    """
    return {"result": [{
        "id": _device_id(handler), "revision": 1, "mail": False,
        "calendar": False, "vk_messages": False, "telegram": True,
        "vk_messages_notifications": False,
    }]}


def get_safe_mode(handler, body=b""):
    """Настройка "Огранчение контента"""
    return {"result": [{"id": _device_id(handler), "revision": 1, "enabled": False}]}


def update_general(handler, body=b""):
    # просто мок
    return {"result": {"success": True}}


def get_general(handler, body=b""):
    """Настройки колонки
home_id, room_id, groups - умный дом
coordinates - геолокация
keyword_sound - либо настройка "Откликаться на Маруся", либо "Звук активации", вероятнее всего 2
children_mode - настройка "Узнавать детей"
alarm_volume - громкость будильника
master_volume - громкость колонки
clock_enabled - включена функция будильников (мастер выключатель)
demomode_enabled_at - режим демонстрации
is_blocked - блокировка колонки
speaker_calls_available и baby_monitor_calls_available - звонки через колонку
"""
    return {"result": [{
        "home_id": "test-home", "room_id": "", "groups": [],
        "id": _device_id(handler), "revision": 1, "name": "Capsule Neo",
        "coordinates": [0.0, 0.0], "timezone": TIMEZONE_NAME,
        "keyword_sound": True, "children_mode": False,
        "alarm_volume": 40, "master_volume": 35,
        "skillserver_type": "", "reminder_sync": True,
        "allow_music_from_app": True, "upnp_discovery": False,
        "bt_handsfree": False, "blackbox_depth": 30,
        "clock_brightness": -1, "clock_night_brightness": -1,
        "clock_enabled": True, "demomode_enabled_at": None,
        "is_blocked": False, "speaker_calls_available": False,
        "baby_monitor_calls_available": False,
    }]}


def get_alarm_music(handler, body=b""):
    # не нашел способа получить что-то помимо пустого массива
    return {"result": []}


def get_alarms(handler, body=b""):
    """список будильников, пример:
{
    "qid": uuid,
    "result": [
        {
            "id": uuid
            "revision": int, # вероятно отвечает за порядок отображения
            "enabled": bool,
            "alarm_time": int, # время срабатывания будильника, в секундах с полуночи
            "weekdays": [], # повторение будильника
            "first_time": timestamp (int), # дата создания/первого срабатывания
        },
    ],
}

"""
    return {"result": []}
