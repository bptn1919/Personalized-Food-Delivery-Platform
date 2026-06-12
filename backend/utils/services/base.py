import logging
from abc import ABC


class BaseService(ABC):
    logger = logging.getLogger("django")

    # Singleton pattern
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
