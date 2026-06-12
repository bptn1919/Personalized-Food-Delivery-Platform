import re


def remove_accents(text: str) -> str:
    """
    Convert string to lowercase and remove Vietnamese accents.
    """
    text = text.lower()
    text = re.sub(r"[àáạảãâầấậẩẫăằắặẳẵ]", "a", text)
    text = re.sub(r"[èéẹẻẽêềếệểễ]", "e", text)
    text = re.sub(r"[ìíịỉĩ]", "i", text)
    text = re.sub(r"[òóọỏõôồốộổỗơờớợởỡ]", "o", text)
    text = re.sub(r"[ùúụủũưừứựửữ]", "u", text)
    text = re.sub(r"[ỳýỵỷỹ]", "y", text)
    text = re.sub(r"[đ]", "d", text)

    text = re.sub(r"[\u0300\u0301\u0303\u0309\u0323]", "", text)
    text = re.sub(r"[\u02C6\u0306\u031B]", "", text)
    return text
