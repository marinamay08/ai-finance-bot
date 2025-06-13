from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContexTypes,
    filteres
)
from handlers import parse_expense

async def start(
        update: Update, 
        context: ContexTypes.DEFAULT_TYPE
):
    await update.message.reply_text("Hi! I'm your personal fin planner")

async def handle_message(
        update: Update,
        context: ContexTypes.DEFAULT_TYPE
):
    user_input = update.message.text
    parsed = parse_expense(user_input)
    if parsed:
        amount, category = parsed
        await update.message.reply_text(f'Записано {amount} в категорию {category}')
    else:
        await update.message.reply_text('Не удалось распарсить категорию (мы обязательно потом сделаем умный парсер)')

def main():
    app = ApplicationBuilder().token("TOKEN").build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()