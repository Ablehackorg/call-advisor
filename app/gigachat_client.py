# app/gigachat_client.py
import uuid
from typing import Optional

import requests

from .config import settings
from .prompt_templates import BASE_SALES_PROMPT


class GigaChatError(Exception):
    """Базовое исключение для ошибок работы с GigaChat."""


def get_access_token() -> str:
    """
    Получение OAuth-токена для GigaChat.
    """
    rq_uid = str(uuid.uuid4())

    resp = requests.post(
        settings.GIGACHAT_OAUTH_URL,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": rq_uid,
            "Authorization": f"Basic {settings.GIGACHAT_AUTH_KEY}",
        },
        data={"scope": settings.GIGACHAT_SCOPE},
        timeout=10,
        verify=False,  # для Сбера: self-signed серт, отключаем проверку в прототипе
    )

    if not resp.ok:
        raise GigaChatError(
            f"Failed to obtain access token: {resp.status_code} {resp.text}"
        )

    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise GigaChatError(f"No access_token in response: {data}")

    return token


def generate_recommendation(
    transcript: str,
    custom_prompt: Optional[str] = None,
) -> str:
    """
    Отправляет транскрипт звонка в GigaChat и возвращает текст рекомендации.
    """
    transcript = (transcript or "").strip()
    if not transcript:
        raise GigaChatError("Пустой транскрипт звонка")

    token = get_access_token()
    system_prompt = custom_prompt or BASE_SALES_PROMPT

    payload = {
        "model": settings.GIGACHAT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript},
        ],
        "max_tokens": 512,
        "temperature": 0.2,
    }

    resp = requests.post(
        settings.GIGACHAT_API_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json=payload,
        timeout=60,
        verify=False,  # аналогично, отключаем проверку SSL для прототипа
    )

    if not resp.ok:
        raise GigaChatError(
            f"GigaChat generation failed: {resp.status_code} {resp.text}"
        )

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        raise GigaChatError(f"Unexpected GigaChat response format: {e} | {data}")
