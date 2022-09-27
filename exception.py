class HTTPStatusCodeIncorrectException(Exception):
    """
    Исключение возникает, если страница возвращает статус отличный от 200.
    """


class GetEndpointException(Exception):
    """Невозможно получить эндпоинт API."""


class HWisNotListException(Exception):
    """Тип получаемого домашнего задания List."""


class KeyDictResponseException(Exception):
    """Исключение, возникающие при отсутствуии нужного ключа в ответе API."""


class VariableNotValidException(Exception):
    """Переменные среды не корректны."""
