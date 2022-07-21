import abc
import json
from typing import Any, Optional


class BaseStorage:
    @abc.abstractmethod
    def save_state(self, state: dict) -> None:
        """Сохранить состояние в постоянное хранилище"""
        pass

    @abc.abstractmethod
    def retrieve_state(self) -> dict:
        """Загрузить состояние локально из постоянного хранилища"""
        pass


class JsonFileStorage(BaseStorage):
    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path

    def save_state(self, state: dict) -> None:
        storage_data = self.retrieve_state()
        try:
            with open(self.file_path, "w") as f:
                if storage_data:
                    storage_data.update(state)
                    f.write(json.dumps(storage_data))
                else:
                    f.write(json.dumps(state))
        except FileNotFoundError:
            return None

    def retrieve_state(self) -> dict:
        try:
            with open(self.file_path, "r") as f:
                data = f.read()
                if data:
                    return json.loads(data)
                return {}
        except FileNotFoundError:
            return {}


class State:
    """
    Класс для хранения состояния при работе с данными,
    чтобы постоянно не перечитывать данные с начала.
    """

    def __init__(self, storage: BaseStorage):
        self.storage = storage

    def set_state(self, key: str, value: Any) -> None:
        """Установить состояние для определённого ключа"""
        self.storage.save_state({key: value})

    def get_state(self, key: str) -> Any:
        """Получить состояние по определённому ключу"""
        return self.storage.retrieve_state().get(key)
