import json
import logging
import os
import requests
import telegram
import time as time_


from dotenv import load_dotenv
from http import HTTPStatus
from sys import stdout


from exception import (
    VariableNotValidException, GetEndpointException,
    HTTPStatusCodeIncorrectException, HWisNotListException,
    KeyDictResponseException
)

load_dotenv()
PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s, %(levelname)s, %(message)s",
    stream=stdout
)
logger = logging.getLogger(__name__)


def send_message(bot: telegram.Bot, message: str) -> None:
    """Функиция отправки сообщения о статусе работу в телеграм."""
    try:
        logger.info("Начата отправка сообщения в Telegram")
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        message = f"Ошибка отправки сообщения: {error}"
        logger.error(message)
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
            message_error = (
                f"API эндпоинта недоступна. Ошибка: "
                f"{response.status_code}"
            )
            logger.error(message_error)
            raise HTTPStatusCodeIncorrectException(message_error)
        return response.json()
    except requests.exceptions.RequestException as error:
        message_error = f"Ошибка получения эндпоинта: {error}"
        logger.error(message_error)
        raise GetEndpointException(message_error)
    except json.decoder.JSONDecodeError as error:
        raise Exception((f"Ответ {response.text} получен не в виде JSON: "
                         f"{error}"))


def check_response(response: dict) -> list:
    """Функция проверяет ответ API на корректность."""
    if response is None:
        message_error = "Отсутствует ответ от API"
        logger.error(message_error)
        raise KeyDictResponseException(message_error)
    if not isinstance(response, dict):
        response_type = type(response)
        message_error = f'Ответ пришел в неккоректном формате: {response_type}'
        logger.error(message_error)
        raise TypeError(message_error)
    if "homeworks" not in response:
        message_error = "Отсутствует ключ homeworks"
        logger.error(message_error)
        raise KeyError(message_error)
    if not isinstance(response["homeworks"], list):
        message_error = 'Ответ должен приходить в виде списка'
        logger.error(message_error)
        raise HWisNotListException(message_error)
    return response["homeworks"]


def parse_status(homework: dict) -> str:
    """Извлекает статус домашней работы."""
    if "homework_name" not in homework or "status" not in homework:
        message_error = "Отсутствует ожидаемые ключи в homework"
        logger.error(message_error)
        raise KeyError(message_error)
    homework_name = homework["homework_name"]
    homework_status = homework["status"]
    if homework_status not in HOMEWORK_STATUSES:
        message_error = f"Недокмуентированный статус в API: {homework_status}"
        logger.error(message_error)
        raise KeyError(message_error)
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Функция проверяет доступность параметров."""
    bool_tokens = True
    env_var = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]

    for env in env_var:
        if env is None:
            logger.critical(
                f"Отсутствует обязательная переменная {env}"
            )
            bool_tokens = False
    return bool_tokens


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        message = 'Отсутствуют переменные среды'
        logger.critical(message)
        raise VariableNotValidException(message)

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
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.critical(message)
            time_.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
