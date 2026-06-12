import hashlib
import mimetypes
import os
from datetime import datetime
from typing import Optional


class Utils:
    @staticmethod
    def generate_hashed_name(file_name: str) -> str:
        name, extension = os.path.splitext(file_name)
        timestamp = datetime.now().timestamp()
        hashed_name = hashlib.sha256(f"{name}{timestamp}".encode()).hexdigest()
        return f"{hashed_name}{extension}"

    @staticmethod
    def get_content_type(file_name: str) -> Optional[str]:
        mime, _ = mimetypes.guess_type(file_name)
        return mime
