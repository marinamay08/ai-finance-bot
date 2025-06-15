import csv
import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from .handlers import process_message, save_expense
from .categories import add_category_mapping, get_combined_category_map
from config.settings import BOT_TOKEN

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

user_inputs = {}  # временное хранилище для выбора категории

HELP_MESSAGE = """🤖 Я помогу тебе вести учет расходов!

📝 Как использовать:
1. Отправь сообщение в формате:
   сумма комментарий
   Например:
   200 кофе
   1500 продукты
   3000 подписка

2. Я автоматически определю категорию расхода.
   Если не смогу - предложу выбрать из списка.

3. Все расходы сохраняются в файл.

💰 Особенности:
• Сумма может быть целым числом или десятичной дробью
• Разделитель - точка или запятая (200.50 или 200,50)
• Комментарий используется для определения категории
• Можно добавлять свои соответствия комментариев и категорий

❓ Если формат не распознан, я подскажу правильный формат."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/start от пользователя: {update.effective_user.username if update.effective_user else 'unknown'}")
    await update.message.reply_text("Привет! Я — твой персональный финпомощник 💸\n\nИспользуй /help чтобы узнать, как я работаю!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/help от пользователя: {update.effective_user.username if update.effective_user else 'unknown'}")
    await update.message.reply_text(HELP_MESSAGE)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username if update.effective_user else 'unknown'
    if update.message and update.message.text:
        logger.info(f"Новое сообщение от @{username}: {update.message.text}")
    else:
        logger.info(f"Новое сообщение от @{username}, но текст отсутствует (update.message is None)")
        return
    if not update.effective_user or not update.effective_user.username:
        logger.warning("Пользователь без username попытался отправить сообщение")
        await update.message.reply_text("Для работы с ботом необходимо указать username в настройках Telegram.")
        return

    user_input = update.message.text

    try:
        result = process_message(user_input, username)
        logger.info(f"Результат парсинга: amount={result.amount}, category={result.category}, error_message={result.error_message}")

        # Если парсер вернул ошибку (нет суммы или нет комментария) — сообщаем об ошибке
        if result.amount is None or (result.error_message and result.category is None and result.amount is None):
            logger.warning(f"Ошибка парсинга: {result.error_message}")
            await update.message.reply_text(result.error_message)
            return

        # Если категория определена — сохраняем расход
        if result.category:
            logger.info(f"Категория определена автоматически: {result.category}")
            await update.message.reply_text(f"Записано: {result.amount} ₽ на категорию «{result.category}»")
        # Если сумма и комментарий есть, но категория не определена — предлагаем выбрать категорию
        elif result.amount is not None and result.error_message:
            user_inputs[username] = (result.amount, result.error_message)  # error_message содержит comment
            categories = sorted(set(get_combined_category_map().values()))
            logger.info(f"Категория не определена. Доступные категории: {categories}")
            if not categories:
                logger.error("Список категорий пуст! Клавиатура не будет отправлена.")
                await update.message.reply_text("Не удалось определить категорию и список категорий пуст. Обратитесь к администратору.")
                return
            keyboard = [[InlineKeyboardButton(cat, callback_data=cat)] for cat in categories]
            await update.message.reply_text("Не удалось определить категорию. Пожалуйста, выбери:",
                                          reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            logger.warning("Не удалось распознать сообщение. Неизвестная ошибка парсинга.")
            await update.message.reply_text("Формат не распознан. Введи как: 200 кофе")
    except Exception as e:
        logger.exception(f"Ошибка при обработке сообщения: {str(e)}")
        await update.message.reply_text(f"Произошла ошибка при обработке сообщения: {str(e)}")

async def handle_category_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    username = query.from_user.username if query.from_user else 'unknown'
    logger.info(f"Выбор категории пользователем @{username}: {query.data}")

    if not query.from_user or not query.from_user.username:
        logger.warning("Пользователь без username попытался выбрать категорию")
        await query.edit_message_text("Для работы с ботом необходимо указать username в настройках Telegram.")
        return

    if username not in user_inputs:
        logger.warning(f"Пользователь @{username} попытался выбрать категорию, но данных нет в user_inputs")
        await query.edit_message_text("Время выбора категории истекло. Пожалуйста, отправьте сообщение заново.")
        return

    try:
        amount, comment = user_inputs.pop(username)
        add_category_mapping(comment, query.data)
        save_expense(amount, query.data, comment, username)
        logger.info(f"Сохранён расход: {amount} {query.data} {comment} @{username}")
        await query.edit_message_text(f"Записано: {amount} ₽ на категорию «{query.data}»")
    except Exception as e:
        logger.exception(f"Ошибка при сохранении расхода: {str(e)}")
        await query.edit_message_text(f"Произошла ошибка при сохранении: {str(e)}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_category_choice))
    logger.info("Бот запущен и ожидает сообщения...")
    app.run_polling()

if __name__ == "__main__":
    main()