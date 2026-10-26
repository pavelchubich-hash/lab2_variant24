# Практическая работа №2 (Вариант 24)

## 1. Общее описание
Веб-приложение с HTTP API для асинхронной минификации JavaScript-кода согласно теме курсовой работы («Веб-приложение с HTTP API для асинхронной минификации JavaScript-кода»).

Приложение разработано на языке Python и включает:
* **Этап 1 (Преобразование данных)**: CLI-утилита минификации JavaScript-кода, принимающая исходный код через стандартный ввод (stdin) и сохраняющая результат на диск.
* **Этап 2 (HTTP API)**: Веб-приложение на базе микрофреймворка **Bottle** с ответами в формате **XML** (`application/xml`). Реализована валидация обязательных заголовков `Content-Type` (415) и `Accept` (406), запуск вычислительной задачи через `subprocess` и Model-Based Testing (MBT) на базе `hypothesis.stateful.RuleBasedStateMachine`.
* **Этап 3 (Реляционная СУБД SQLite)**: Подключение ORM **PonyORM** и СУБД SQLite для хранения сущностей Person, Command и Result. Обеспечено полное покрытие методов HTTP API со слоем доступа к данным на базе PonyORM/SQLite с помощью MBT-тестов Hypothesis.

---

## 2. Описание всех функций и настроек

### Утилита минификации (`src/minifier.py`):
* `remove_comments(source_code)`: Удаление однострочных (`//`) и многострочных (`/* */`) комментариев с сохранением строк и спецсимволов.
* `collapse_whitespace(code)`: Сжатие избыточных пробелов, табуляций и переносов строк вокруг операторов.
* `minify_javascript(source_code)`: Полный конвейер минификации JS-кода.
* `parse_output_argument(args)`: Разбор аргументов командной строки для пути сохранения.
* `run_minifier_cli(args)`: Чтение кода из `stdin`, минификация и запись на диск.

### Вспомогательные функции XML (`src/xml_utils.py`):
* `serialize_id_response(identifier)`: Сериализация ответа с ID сущности.
* `serialize_status_response(success)`: Сериализация статуса операции (`true`/`false`).
* `serialize_error(code, message)`: Сериализация ошибки с HTTP-кодом и сообщением.
* `serialize_persons(persons)`: Формирование XML со списком сущностей Person.
* `serialize_commands(commands)`: Формирование XML со списком сущностей Command.
* `serialize_results(results)`: Формирование XML со списком сущностей Result.
* `serialize_report(items)`: Формирование отчёта по формуле (24) в формате XML.
* `parse_xml_to_dict(xml_text)`: Разбор корневого словаря из XML.
* `parse_xml_items(xml_text, item_tag)`: Извлечение списка записей из XML.

### Веб-сервер Bottle (`src/http_server.py`):
* `check_request_headers(method, headers)`: Проверка обязательных заголовков (`Content-Type` и `Accept`).
* `enforce_headers(handler_func)`: Декоратор маршрутов для проверки заголовков и возврата кодов 415 / 406.
* `execute_computation(data, test_mode)`: Запуск CLI-утилиты через модуль `subprocess` либо возврат эмулированного результата в тестовом режиме.
* `create_app(storage, test_mode)`: Фабрика создания и настройки приложения Bottle с маршрутами по табл. 24.

#### Маршруты HTTP API (Таблица 24):
* `PUT /public/api/person-make/:identifier` (1.1): Создание/обновление записи Person.
* `GET /public/api/person-remove` (1.2): Удаление Person по идентификатору.
* `POST /public/api/person-scan` (1.3): Поиск и просмотр записей Person.
* `PUT /public/api/command-make/:identifier` (2.1): Создание Command, запуск минификации через subprocess и формирование Result.
* `GET /public/api/command-remove` (2.2): Удаление Command по идентификатору.
* `POST /public/api/command-scan/:person` (2.3): Выборка команд конкретного пользователя.
* `POST /public/api/result-scan/:command` (3.1): Выборка результатов для указанной команды.
* `POST /public/api/report-scan` (4.1): Построение отчёта по формуле (24):
  $$\pi_{C.tags, R.result} ( C \rtimes_{C.identifier = R.command} ( \sigma_{R.created > now - 5\text{ min}} R ) )$$

### Клиент HTTP API (`src/http_client.py`):
* `HTTPClient`: Клиент, методы которого соответствуют маршрутам таблицы 24 с заменой символов `/` и `-` на `_`:
  * `public_api_person_make(identifier, ip, platform, user_agent)`
  * `public_api_person_remove(identifier)`
  * `public_api_person_scan(filters)`
  * `public_api_command_make(identifier, data, person, tags, status, triggered)`
  * `public_api_command_remove(identifier)`
  * `public_api_command_scan(person, filters)`
  * `public_api_result_scan(command, filters)`
  * `public_api_report_scan()`

### Слой PonyORM SQLite (`src/pony_storage.py`):
* `Person`, `Command`, `Result`: Сущности БД PonyORM, отражающие ER-диаграмму.
* `init_database(filename)`: Инициализация подключения к SQLite и генерация схемы таблиц.
* `create_person`, `delete_person`, `get_persons`: CRUD для Person.
* `create_command`, `delete_command`, `get_commands_by_person`, `get_all_commands`: CRUD для Command.
* `create_result`, `get_results_by_command`, `get_all_results`: CRUD для Result.
* `select_report_data()`: Реляционное соединение и проекция отчёта по формуле (24).

---

## 3. Описание команд для сборки проекта и запуска тестов

### Запуск тестов и формирование отчёта о покрытии ветвей:
В ОС Linux/macOS:
```bash
bash run.sh
```

В ОС Windows:
```cmd
run.bat
```

### Ручной запуск тестов через Python:
```bash
python -m coverage run --source=src --branch -m pytest
python -m coverage report -m
```

### Запуск статического анализатора (PEP8):
```bash
python -m flake8 src tests
```

---

## 4. Примеры использования

### 1. Запуск CLI-утилиты минификации JavaScript (Этап 1):
```bash
python src/minifier.py -o output.js < examples/input1.js
```

### 2. Запуск сервера HTTP API:
```bash
python src/http_server.py
```

### 3. Использование API-клиента в Python коде:
```python
from http_client import HTTPClient
from http_server import create_app
import pony_storage

# Инициализация БД PonyORM и сервера
pony_storage.init_database("app.db")
app = create_app(storage=pony_storage, test_mode=False)
client = HTTPClient(app=app)

# 1. Создание пользователя
client.public_api_person_make(
    identifier=1,
    ip="192.168.1.10",
    platform="Linux",
    user_agent="Firefox/120.0"
)

# 2. Создание команды и запуск минификации JS через subprocess
js_source = "/* Test */ function add(a, b) { return a + b; }"
client.public_api_command_make(
    identifier=1,
    data=js_source,
    person=1,
    tags="math,core",
    status="done",
    triggered=1
)

# 3. Получение результата минификации
results = client.public_api_result_scan(command=1)
print("Результат минификации:", results[0]["result"])

# 4. Построение отчёта по формуле (24)
report = client.public_api_report_scan()
print("Отчёт:", report)
```
