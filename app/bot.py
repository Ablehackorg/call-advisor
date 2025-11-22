# app/bot.py
import asyncio
from typing import Dict

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from .config import settings
from .gigachat_client import generate_recommendation, GigaChatError
from .logging_conf import logger
from .mailer import send_recommendation_email


dp = Dispatcher()

# Храним последнюю рекомендацию для каждого пользователя Telegram
LAST_RECOMMENDATIONS: Dict[int, str] = {}


@dp.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        "Привет! Я бот-прототип для теста интеграции с GigaChat.\n\n"
        "1️⃣ Пришли мне *текст транскрипта звонка*.\n"
        "2️⃣ Я отправлю его в GigaChat и верну рекомендации по работе менеджера.\n"
        "3️⃣ После этого ты сможешь *одной кнопкой* отправить рекомендацию "
        f"на email: {settings.RESULT_EMAIL}."
    )
    await message.answer(text, parse_mode="Markdown")


@dp.message(F.text)
async def handle_transcript(message: Message):
    transcript = (message.text or "").strip()

    if not transcript:
        await message.answer("Текст пустой, пришли, пожалуйста, транскрипт звонка.")
        return

    MAX_CHARS = 8000
    if len(transcript) > MAX_CHARS:
        transcript = transcript[:MAX_CHARS]
        await message.answer(
            "Транскрипт очень длинный, обработаю только первые 8000 символов."
        )

    await message.answer("Обрабатываю транскрипт, запрашиваю рекомендации в GigaChat...")

    loop = asyncio.get_running_loop()
    try:
        recommendation = await loop.run_in_executor(
            None, generate_recommendation, transcript
        )
    except GigaChatError as e:
        logger.error("GigaChat error in bot: %s", e)
        await message.answer(
            "Не удалось получить рекомендацию от GigaChat. "
            "Попробуй ещё раз позже или проверь настройки бэка."
        )
        return
    except Exception as e:
        logger.exception("Unexpected error in bot: %s", e)
        await message.answer("Произошла непредвиденная ошибка. Попробуй ещё раз.")
        return

    user_id = message.from_user.id
    LAST_RECOMMENDATIONS[user_id] = recommendation

    await message.answer("Готово! Вот рекомендации по звонку:")

    chunk_size = 4000
    for i in range(0, len(recommendation), chunk_size):
        await message.answer(recommendation[i : i + chunk_size])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да, отправить на email",
                    callback_data="send_email_yes",
                ),
                InlineKeyboardButton(
                    text="Нет, не отправлять",
                    callback_data="send_email_no",
                ),
            ]
        ]
    )

    await message.answer(
        f"Отправить эту рекомендацию на email: {settings.RESULT_EMAIL} ?",
        reply_markup=keyboard,
    )


@dp.callback_query(F.data == "send_email_yes")
async def on_send_email_yes(callback: CallbackQuery):
    user_id = callback.from_user.id
    recommendation = LAST_RECOMMENDATIONS.get(user_id)

    if not recommendation:
        await callback.answer(
            "Не нашёл сохранённую рекомендацию для этого пользователя. "
            "Попробуй отправить транскрипт ещё раз.",
            show_alert=True,
        )
        return

    try:
        send_recommendation_email(recommendation)
    except Exception:
        await callback.message.answer(
            "Не удалось отправить письмо. Проверь настройки SMTP на бэке."
        )
        await callback.answer()
        return

    await callback.message.answer("Рекомендация отправлена на email клиента ✅")
    await callback.answer()


@dp.callback_query(F.data == "send_email_no")
async def on_send_email_no(callback: CallbackQuery):
    await callback.message.answer("Ок, не отправляю рекомендации на email.")
    await callback.answer()


async def main():
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    logger.info("Starting Telegram bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
