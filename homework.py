import json
import logging
import os
import sys
import requests
import telegram
import time as time_


from dotenv import load_dotenv
from http import HTTPStatus


from exception import (
    GetEndpointException, HTTPStatusCodeIncorrectException,
    KeyDictResponseException, ResponseNotListException,
    UnionClassByTelegramBotException,
)

load_dotenv()
PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)


def send_message(bot: telegram.Bot, message: str) -> None:
    """Функиция отправки сообщения о статусе работу в телеграм."""
    try:
        logger.info("Начата отправка сообщения в Telegram")
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger.error(f"Ошибка отправки сообщения: {error}")
    else:
        logger.info(f"Сообщение отправлено: {message}")


def get_api_answer(current_timestamp: int) -> dict:
    """Функция получения ответа API в JSON-формате."""
    timestamp = current_timestamp or int(time_.time())
    params = {"from_date": timestamp}
    try:
        response = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params=params
        )
        if response.status_code != HTTPStatus.OK:
            raise HTTPStatusCodeIncorrectException(
                f"API эндпоинта недоступна. Ошибка: "
                f"{response.status_code}"
            )
        return response.json()
    except requests.exceptions.RequestException as error:
        raise GetEndpointException(f"Ошибка получения эндпоинта") from error
    except json.decoder.JSONDecodeError as error:
        raise Exception(f"Ответ {response.text} получен не в виде JSON: "
                        f"{error}")


def check_response(response: dict) -> list:
    """Функция проверяет ответ API на корректность."""
    if response is None:
        raise KeyDictResponseException("Отсутствует ответ от API")
    if not isinstance(response, dict):
        raise TypeError(
            f"Ответ пришел в неккоректном формате: {type(response)}"
        )
    if "homeworks" not in response:
        raise KeyError("Отсутствует ключ homeworks")
    if not isinstance(response["homeworks"], list):
        raise ResponseNotListException("Ответ должен приходить в виде списка")
    return response["homeworks"]


def parse_status(homework: dict) -> str:
    """Извлекает статус домашней работы."""
    if "homework_name" not in homework or "status" not in homework:
        raise KeyError("Отсутствует ожидаемые ключи в homework")
    homework_name = homework["homework_name"]
    homework_status = homework["status"]
    if homework_status not in HOMEWORK_VERDICTS:
        raise KeyError(f"Недокмуентированный статус в API: {homework_status}")
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Функция проверяет доступность параметров."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical("Отсутствуют переменные среды")
        sys.exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time_.time())
    status_old = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                status = parse_status(homeworks[0])
                if status_old != status:
                    send_message(bot, status)
                status_old = status
            else:
                logger.debug('Отсутствие в ответе API новых статусов')
            current_timestamp = int(time_.time())
            time_.sleep(RETRY_TIME)
        except UnionClassByTelegramBotException as error:
            send_message(bot, str(error))
            logger.error(str(error))
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.critical(message)
            time_.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
