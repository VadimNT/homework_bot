class UnionClassByTelegramBotException(Exception):
    """Базовый класс исключений для телеграмм-бота"""
    pass


class HTTPStatusCodeIncorrectException(UnionClassByTelegramBotException):
    """
    Исключение возникает, если страница возвращает статус отличный от 200.
    """
    pass


class GetEndpointException(UnionClassByTelegramBotException):
    """Невозможно получить эндпоинт API."""
    pass


class ResponseNotListException(UnionClassByTelegramBotException):
    """
    Исключение, вознкиающие при получении ответа от API
     не в нужном формате List.
     """
    pass


class KeyDictResponseException(UnionClassByTelegramBotException):
    """Исключение, возникающие при отсутствуии нужного ключа в ответе API."""
    pass
