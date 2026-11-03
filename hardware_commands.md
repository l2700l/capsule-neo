# Описание разобранных типов команд, которые принимает прошивка

## led_digits_animation

Включение сигментов дисплея

Пример (выводит 4PDA на 15 секунд):
```json
{
  "qid": "e99c4a7a33864542a10b55586f05627b",
  "result": {
    "commands": [
     {
        "frames": [
          {
            "brightness": [
0,
255,
255,
0,
0,
255,
255,
255,
255,
0,
0,
255,
255,
255,
0,
0,
255,
255,
255,
255,
255,
255,
0,
255,
255,
255,
0,
255,
255,
255
          ],
            "seconds": null,
            "duration": 15.0
        }
      ],
      "iteration_count": 1,
      "blocking": false,
      "action_text": "Включаю анимацию дисплея",
      "type": "led_digits_animation"
  }
```

### Маппинг сегментов

Список состоит из двух первых цифр, верхней и нижней точки, двух последних цифр, маппинг для каждой цифры одинаков (индекс относительно цифры):
1 - верхний сегмент
2 - правый сегмент сверху
3 - правый сегмент снизу
4 - нижний сегмент
5 - левый сегмент снизу
6 - левый сегмент сверху
7 - средний сегмент

Условное расположение:
```text
 1    1        1    1
6 2  6 2  15  6 2  6 2
 7    7        7    7
5 3  5 3  16  5 3  5 3
 4    4        4    4
```
Смещение элементов:
1 цифра - 0 (0..6 индексы)
2 цифра - 7 (7..13 индексы)
Верхняя точка - 14 (14 индекс)
Нижняя точка - 15 (15 индекс)
3 цифра - 16 (16..22 индексы)
4 цифра - 23 (23..29 индексы)

## alarms_settings_v1

Управление будильниками

Пример (добавление будильника):
```json
{
  "qid": "ab9c0e1609a14f388ab9879c8252f475",
  "result": {
    "commands": [
      {
        "alarms": [
          {
            "enabled": true,
            "alarm_time": 68400,
            "weekdays": [
              1,
              2,
              3,
              4,
              5
            ],
            "first_time": 0,
            "id": "fba62ee3-5c70-4d65-b4f1-f9a1fa1c1609",
            "revision": 24,
            "updated": 1793675945.977877
          },
          {
            "enabled": true,
            "alarm_time": 28800,
            "weekdays": [],
            "first_time": 1794196800,
            "id": "617ada2c-3e02-4243-b726-921b071fe698",
            "revision": 23,
            "updated": 1793675945.977883
          },
          {
            "enabled": true,
            "alarm_time": 64800,
            "weekdays": [],
            "first_time": 1793714400,
            "id": "fb59627a-7135-4ed9-b8f7-0d4ce2256c52",
            "revision": 22,
            "updated": 1793675945.977886
          },
          {
            "enabled": false,
            "alarm_time": 23400,
            "weekdays": [],
            "first_time": 1708396200,
            "id": "0c2ebeb6-9d72-487a-a05f-b5afac5dfb76",
            "revision": 19,
            "updated": 1793675945.977888
          },
          {
            "enabled": false,
            "alarm_time": 25200,
            "weekdays": [],
            "first_time": 1707015600,
            "id": "10a57db3-a02f-40e4-80e0-41d544f3f179",
            "revision": 18,
            "updated": 1793675945.97789
          },
          {
            "enabled": false,
            "alarm_time": 28800,
            "weekdays": [],
            "first_time": 1704772800,
            "id": "db6886f5-7bba-4a8d-abee-afd126ce81f1",
            "revision": 21,
            "updated": 1793675945.977893
          },
          {
            "enabled": false,
            "alarm_time": 39600,
            "weekdays": [],
            "first_time": 1704870000,
            "id": "da54afec-129e-4dc4-9c8c-ad67d4c6af1a",
            "revision": 15,
            "updated": 1793675945.977895
          }
        ],
        "type": "alarms_settings_v1"
      },
    ],
    "controls": [],
    "skill": "alarm_ds",
    "asr_text": "поставь будильник на понедельник на восемь утра",
    "secure": false,
    "intent": "alarm_ds.set_alarm"
  }
}
```

Исходя из запросов сервер отдает сразу измененный список всех доступных будильников, запросы на удаление/добавление отдают весь массив.

## bluetooth_pair

Управление bluetooth

Пример (включение bluetooth):
```json
{
  "qid": "dc930d93e3a94d57b6668e2c50e82ec7",
  "result": {
    "commands": [
      {
        "turn_on": true,
        "type": "bluetooth_pair"
      },
    ],
    "controls": [],
    "skill": "bluetooth_pair",
    "asr_text": "включи bluetooth",
    "secure": false,
    "intent": "bluetooth_pair.activate"
  }
}
```

## pretty_mode

Управление режимом "ми-ми-ми" (мордашка вместо часов)

Пример:
```json
{
  "qid": "2fe48f7b5dac450e949b39ddc7e176da",
  "result": {
    "commands": [
      {
        "turn_on": true,
        "type": "pretty_mode"
      }
    ],
    "controls": [],
    "skill": "pretty_mode",
    "asr_text": "сделай ми ми ми",
    "secure": false,
    "intent": "pretty_mode.on"
  }
}
```

## delay

Добавляет задержку между командами

Пример (использование с pretty_mode):
```json
{
  "qid": "2fe48f7b5dac450e949b39ddc7e176da",
  "result": {
    "commands": [
      {
        "turn_on": true,
        "type": "pretty_mode"
      },
      {
        "length": 300,
        "type": "delay"
      },
      {
        "text": "^Посмотрим^ — вы на меня, а я на вас",
        "blocking": true,
        "normalize": true,
        "force_say": false,
        "kws_skip": null,
        "encoder": "opus",
        "encoder_bitrate": null,
        "encoder_frame_size": null,
        "model_name": null,
        "long_reader_request": false,
        "speed": 1.0,
        "type": "tts",
        "stream_id": "b9fec072-e9d2-44a3-8ce0-c0509c9c1cc2"
      },
      {
        "min_waiting_time": 4.0,
        "mute_activation_sound": false,
        "callback_data": "{\"forced_listen\": true, \"listen_previous_intent\": \"pretty_mode.on\"}",
        "blocking": true,
        "type": "listen"
      }
    ],
    "controls": [],
    "skill": "pretty_mode",
    "asr_text": "сделай ми ми ми",
    "secure": false,
    "intent": "pretty_mode.on"
  }
}
```

## listen

Продолжить запись речи

Пример (использование с pretty_mode):
```json
{
  "qid": "2fe48f7b5dac450e949b39ddc7e176da",
  "result": {
    "commands": [
      {
        "turn_on": true,
        "type": "pretty_mode"
      },
      {
        "length": 300,
        "type": "delay"
      },
      {
        "text": "^Посмотрим^ — вы на меня, а я на вас",
        "blocking": true,
        "normalize": true,
        "force_say": false,
        "kws_skip": null,
        "encoder": "opus",
        "encoder_bitrate": null,
        "encoder_frame_size": null,
        "model_name": null,
        "long_reader_request": false,
        "speed": 1.0,
        "type": "tts",
        "stream_id": "b9fec072-e9d2-44a3-8ce0-c0509c9c1cc2"
      },
      {
        "min_waiting_time": 4.0,
        "mute_activation_sound": false,
        "callback_data": "{\"forced_listen\": true, \"listen_previous_intent\": \"pretty_mode.on\"}",
        "blocking": true,
        "type": "listen"
      }
    ],
    "controls": [],
    "skill": "pretty_mode",
    "asr_text": "сделай ми ми ми",
    "secure": false,
    "intent": "pretty_mode.on"
  }
}
```

## general_settings_v1

Установка параметров

Пример:
```json
{
  "qid": "2a37ab3af25642d6917ce40a2211cecf",
  "result": {
    "commands": [
      {
        "settings": {
          "home_id": "mock",
          "room_id": "",
          "groups": [],
          "id": "mock",
          "revision": 602,
          "name": "mock",
          "coordinates": [
            0.0,
            0.0
          ],
          "timezone": "Europe/Moscow",
          "keyword_sound": true,
          "children_mode": false,
          "alarm_volume": 40,
          "master_volume": 20,
          "skillserver_type": "",
          "reminder_sync": true,
          "allow_music_from_app": true,
          "upnp_discovery": false,
          "bt_handsfree": false,
          "blackbox_depth": 30,
          "clock_brightness": -1,
          "clock_night_brightness": 20,
          "clock_enabled": true,
          "demomode_enabled_at": null,
          "is_blocked": false,
          "speaker_calls_available": false,
          "baby_monitor_calls_available": false
        },
        "action_text": "Увеличиваю яркость часов, новое значение - 20 из 100 (максимум)",
        "type": "general_settings_v1"
      }
    ],
    "controls": [],
    "skill": "controls",
    "asr_text": "поставь яркость на сорок",
    "secure": false,
    "intent": "controls.led_digits_brightness_equal"
  }
}
```

Выставляются сразу все параметры, использование с одним параметром не тестировалось

## hint

Подсказка, найдена в связке с попыткой включить музыку без подписки

Пример:
```json
{
  "qid": "a5e4cac8585041c3a072e6b84131c1b4",
  "result": {
    "commands": [
      {
        "subscription_required_hint": true,
        "type": "hint"
      }
    ],
    "controls": [],
    "skill": "music",
    "asr_text": "включи популярную музыку",
    "secure": false,
    "intent": "music.play_any_playlist"
  }
}
```

## text

Отвечает за показ сообщения в виде текста, для колонки бесполезен

## text_suggest

Отвечает за текстовые подсказки, для колонки бесполезен

## night_mode_settings_v1

Управление ночным режимом

Пример:
```json
{
  "qid": "1068863ae0d84c6aa6c6322ec7c67bff",
  "result": {
    "commands": [
      {
        "settings": {
          "id": "mock",
          "revision": 231,
          "enabled": true,
          "scheduled": true,
          "start_at": 0,
          "stop_at": 36000
        },
        "type": "night_mode_settings_v1"
      },
    ],
    "controls": [],
    "skill": "night_mode",
    "asr_text": "включи ночной режим",
    "secure": false,
    "intent": "night_mode.enable"
  }
}
```

## tts

Отвечает за озвучку текста

Пример (использование с pretty_mode):
```json
{
  "qid": "2fe48f7b5dac450e949b39ddc7e176da",
  "result": {
    "commands": [
      {
        "text": "^Посмотрим^ — вы на меня, а я на вас",
        "blocking": true,
        "normalize": true,
        "force_say": false,
        "kws_skip": null,
        "encoder": "opus",
        "encoder_bitrate": null,
        "encoder_frame_size": null,
        "model_name": null,
        "long_reader_request": false,
        "speed": 1.0,
        "type": "tts",
        "stream_id": "b9fec072-e9d2-44a3-8ce0-c0509c9c1cc2"
      },
    ],
    "controls": [],
    "skill": "pretty_mode",
    "asr_text": "сделай ми ми ми",
    "secure": false,
    "intent": "pretty_mode.on"
  }
}
```

## update_dashboard

Не до конца ясен принцип работы, в запросах идет просто как:

```json
{
  "type": "update_dashboard"
},
```

## timer

Управление таймерами

Пример:
```json
{
  "qid": "c81a498473a9425689945ab0cf858bb3",
  "result": {
    "commands": [
      {
        "timestamp": 1793679895,
        "cancel": false,
        "timestamp_delta": 3600,
        "type": "timer"
      },
    ],
    "controls": [],
    "skill": "timer_ds",
    "asr_text": "поставь таймер на час",
    "secure": false,
    "intent": "timer_ds.start"
  }
}
```

При отмене таймера возвращается не пустой список, а:
```json
{
  "timestamp": 0,
  "cancel": true,
  "timestamp_delta": 0,
  "type": "timer"
},
```

## media

Отвечает за произведение медиа

Пример (радио):
```json
{
  "qid": "e99c4a7a33864542a10b55586f05627b",
  "result": {
    "commands": [
      {
        "url": "https://vc.go.mail.ru/radio.mp3?radiostatistica=VKMarusya",
        "meta": {
          "artist": "Русское радио",
          "source": {
            "artist": "Русское радио",
            "media_type": "radio",
            "type": "radio",
            "uid": "https://vc.go.mail.ru/radio.mp3?radiostatistica=VKMarusya",
            "phrase_id": "20261103-0612-4481-b39d-1969bcac5896",
            "skill_name": "radio",
            "stat_flags": "{\"audio_id_source\": \"radio\", \"cpp_hash\": \"de2bf9087708b754\", \"performer\": \"\\u0420\\u0443\\u0441\\u0441\\u043a\\u043e\\u0435 \\u0440\\u0430\\u0434\\u0438\\u043e\", \"title\": \"105,7\", \"is_child_voice\": \"0\", \"child_recognition\": \"0\", \"mode\": \"default\", \"child_content_type\": \"0\", \"skill\": \"radio\", \"audio_url\": \"https://vc.go.mail.ru/radio.mp3?radiostatistica=VKMarusya\"}"
          },
          "title": "105,7",
          "url": "https://vc.go.mail.ru/radio.mp3?radiostatistica=VKMarusya",
          "coverUrl": "https://resources-vc.go.mail.ru/voice/skillserver_resources/prod/radio_logo/RusRadio_Logo.jpg",
          "stat_flags": "{\"audio_id_source\": \"radio\", \"cpp_hash\": \"de2bf9087708b754\", \"performer\": \"\\u0420\\u0443\\u0441\\u0441\\u043a\\u043e\\u0435 \\u0440\\u0430\\u0434\\u0438\\u043e\", \"title\": \"105,7\", \"is_child_voice\": \"0\", \"child_recognition\": \"0\", \"mode\": \"default\", \"child_content_type\": \"0\", \"skill\": \"radio\", \"audio_url\": \"https://vc.go.mail.ru/radio.mp3?radiostatistica=VKMarusya\"}"
        },
        "media_type": 2,
        "kws_skip": null,
        "autoplay": true,
        "append": false,
        "event_media_end": null,
        "action_text": "",
        "content_value": {},
        "need_vk_session": null,
        "page_token": null,
        "type": "media"
      }
    ],
    "controls": [],
    "skill": "radio",
    "asr_text": "включи радио",
    "secure": false,
    "intent": "radio.play"
  }
}
```

Пример (крайне корявая попытка использовать просто mp3 файлы):
```json
{
  "qid": "e99c4a7a33864542a10b55586f05627b",
  "result": {
    "commands": [
    {
        "url": "url.mp3",
        "meta": {
          "artist": "Русское радио",
          "source": {
            "artist": "Русское радио",
            "media_type": "music",
            "type": "url",
            "uid": "url.mp3",
            "phrase_id": "20261103-0612-4481-b39d-1969bcac5896",
            "skill_name": "music",
            "stat_flags": "{\"audio_id_source\": \"url\", \"cpp_hash\": \"de2bf9087708b754\", \"performer\": \"\\u0420\\u0443\\u0441\\u0441\\u043a\\u043e\\u0435 \\u0440\\u0430\\u0434\\u0438\\u043e\", \"title\": \"105,7\", \"is_child_voice\": \"0\", \"child_recognition\": \"0\", \"mode\": \"default\", \"child_content_type\": \"0\", \"skill\": \"radio\", \"audio_url\": \"url.mp3\"}"
          },
          "title": "105,7",
          "url": "url.mp3",
          "coverUrl": "https://resources-vc.go.mail.ru/voice/skillserver_resources/prod/radio_logo/RusRadio_Logo.jpg",
          "stat_flags": "{\"audio_id_source\": \"url\", \"cpp_hash\": \"de2bf9087708b754\", \"performer\": \"\\u0420\\u0443\\u0441\\u0441\\u043a\\u043e\\u0435 \\u0440\\u0430\\u0434\\u0438\\u043e\", \"title\": \"105,7\", \"is_child_voice\": \"0\", \"child_recognition\": \"0\", \"mode\": \"default\", \"child_content_type\": \"0\", \"skill\": \"radio\", \"audio_url\": \"url.mp3\"}"
        },
        "media_type": 1,
        "kws_skip": null,
        "autoplay": true,
        "append": false,
        "event_media_end": null,
        "action_text": "",
        "content_value": {},
        "need_vk_session": null,
        "page_token": null,
        "type": "media"
      }
    ],
    "controls": [],
    "skill": "music",
    "asr_text": "включи песню",
    "secure": false,
    "intent": "music.play_track"
  }
}
```

Колонка съест такую команду, но начнет произведение только после полного скачивания файла, без stat_flags играет сразу

## bg_music и play_url

Аналог media

## light_demo

Демонстрация работы светодиода - при включении переливается между цветами с плавными затуханиями

Пример (включение)
```json
{
  "qid": "c81a498473a9425689945ab0cf858bb3",
  "result": {
    "commands": [
      {
        "type": "enter_light_demo"
      },
    ],
    "controls": [],
    "skill": "unkown",
    "asr_text": "запрос",
    "secure": false,
    "intent": "unkown"
  }
}
```
Пример (выключение)
```json
{
  "qid": "c81a498473a9425689945ab0cf858bb3",
  "result": {
    "commands": [
      {
        "type": "exit_light_demo"
      },
    ],
    "controls": [],
    "skill": "unkown",
    "asr_text": "запрос",
    "secure": false,
    "intent": "unkown"
  }
}
```

## Controls

Отвечают за управление музыкой и громкостью

Добавляется в поле "controls": [] из запросов выше

Найденные контроллы:
Следующий трек
```json
{
    "type": "next_control"
}
```
Предыдущий трек
```json
{
    "type": "previous_control"
}
```
Установка трека на репит (за что отвечает count - пока неизвестно)
```json
{
    "count": 0,
    "type": "repeat_control"
}
```
Установка плейлиса на репит (за что отвечает count - пока неизвестно)
```json
{
    "count": 0,
    "type": "repeat_playlist_control"
}
```
Перемотка трека (по всей видимости работает только вперед)
```json
{
    "elapsed": 0,
    "position": 0,
    "type": "rewind_control"
}
```
Перемешать плейлист
```json
{
    "type": "shuffle_control"
}
```
Пауза
```json
{
    "type": "pause_control"
}
```
Продолжить воспроизведение
```json
{
    "type": "resume_control"
}
```
Установить громкость (от 0 до 100)
```json
{
    "level": 20,
    "type": "volume_control"
}
```
