"""
Startup Idea Validator - Telegram Bot
AI-powered startup idea analysis bot
"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from groq import Groq

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Groq API client
groq_client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

# Хранилище состояний пользователей
user_states = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user

    welcome_text = f"""👋 Привет, {user.first_name}!

Я **Startup Idea Validator** - AI-ассистент для анализа стартап-идей.

🚀 **Что я умею:**
• Анализ рынка и конкурентов
• Оценка рисков
• Рекомендации по MVP
• Roadmap разработки
• Оценка жизнеспособности идеи

📝 **Как использовать:**
Просто опишите свою идею стартапа, и я проведу детальный анализ!

Или используйте /analyze для пошагового ввода данных.

Powered by Claude AI 🤖"""

    keyboard = [
        [InlineKeyboardButton("🚀 Начать анализ", callback_data='start_analysis')],
        [InlineKeyboardButton("ℹ️ Примеры идей", callback_data='examples')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()

    if query.data == 'start_analysis':
        await start_analysis(query, context)
    elif query.data == 'examples':
        await show_examples(query, context)


async def start_analysis(query, context):
    """Начало пошагового анализа"""
    user_id = query.from_user.id
    user_states[user_id] = {'step': 'idea'}

    text = """📝 **Шаг 1/3: Описание идеи**

Опишите вашу идею стартапа:
• Что это за продукт/сервис?
• Какую проблему решает?
• Кто целевая аудитория?

Напишите подробное описание (2-5 предложений)."""

    await query.edit_message_text(text, parse_mode='Markdown')


async def show_examples(query, context):
    """Показать примеры идей"""
    examples = """💡 **Примеры стартап-идей:**

**1. EdTech платформа**
"Платформа для онлайн-обучения программированию с AI-ментором. Персонализированные треки обучения, code review от AI, практические проекты. Целевая аудитория: начинающие разработчики 18-35 лет."

**2. HealthTech приложение**
"Мобильное приложение для отслеживания здоровья с AI-рекомендациями. Анализ симптомов, напоминания о приеме лекарств, интеграция с носимыми устройствами. Для людей с хроническими заболеваниями."

**3. B2B SaaS**
"Платформа для автоматизации HR-процессов с AI. Подбор кандидатов, анализ резюме, автоматические интервью. Для компаний 50-500 сотрудников."

Готовы описать свою идею? Просто напишите её в чат! 👇"""

    keyboard = [[InlineKeyboardButton("🚀 Начать анализ", callback_data='start_analysis')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(examples, reply_markup=reply_markup, parse_mode='Markdown')


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /analyze"""
    user_id = update.effective_user.id
    user_states[user_id] = {'step': 'idea'}

    text = """📝 **Анализ стартап-идеи**

Опишите вашу идею подробно:
• Что это за продукт/сервис?
• Какую проблему решает?
• Кто целевая аудитория?
• Почему это актуально сейчас?

Чем подробнее опишете, тем точнее будет анализ! 🎯"""

    await update.message.reply_text(text, parse_mode='Markdown')


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text

    # Если пользователь просто описывает идею без команды
    if user_id not in user_states:
        await analyze_idea_simple(update, context, text)
    else:
        # Пошаговый ввод (можно расширить позже)
        await analyze_idea_simple(update, context, text)


async def analyze_idea_simple(update: Update, context: ContextTypes.DEFAULT_TYPE, idea_text: str):
    """Простой анализ идеи"""

    # Отправляем сообщение о начале анализа
    processing_msg = await update.message.reply_text(
        "🔍 Анализирую вашу идею...\n\nЭто может занять 10-20 секунд ⏳",
        parse_mode='Markdown'
    )

    try:
        # Промпт для Claude
        prompt = f"""Ты эксперт по анализу стартапов и продуктовой разработке. Проанализируй следующую идею стартапа:

**Описание идеи:** {idea_text}

Проведи детальный анализ и предоставь структурированный ответ:

## 📊 Анализ рынка
- Размер рынка и потенциал
- Основные тренды
- Барьеры входа

## 🎯 Конкуренты
- 3-5 прямых конкурентов
- Ваше преимущество

## ⚠️ Риски
- Топ-3 риска
- Как их минимизировать

## 🚀 MVP Рекомендации
- 5 ключевых фичей для MVP
- Что НЕ делать в MVP
- Метрики успеха

## 💻 Технический стек
- Рекомендуемые технологии
- Оценка сложности (1-10)

## 📅 Roadmap
- MVP: сроки и задачи
- Growth: следующие шаги
- Scale: долгосрочная перспектива

## ⭐ Итоговая оценка
- Оценка идеи (1-10)
- Главные факторы успеха
- Рекомендация: стоит ли запускать?

Будь конкретным и практичным. Используй эмодзи для структурирования."""

        # Вызов Groq API
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=4000,
        )

        analysis = chat_completion.choices[0].message.content

        # Удаляем сообщение о процессе
        await processing_msg.delete()

        # Отправляем результат (разбиваем если слишком длинный)
        if len(analysis) > 4000:
            # Разбиваем на части
            parts = [analysis[i:i+4000] for i in range(0, len(analysis), 4000)]
            for i, part in enumerate(parts):
                if i == 0:
                    await update.message.reply_text(
                        f"✅ **Анализ завершен!**\n\n{part}",
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(part, parse_mode='Markdown')
        else:
            await update.message.reply_text(
                f"✅ **Анализ завершен!**\n\n{analysis}",
                parse_mode='Markdown'
            )

        # Кнопки для дальнейших действий
        keyboard = [
            [InlineKeyboardButton("🔄 Анализировать другую идею", callback_data='start_analysis')],
            [InlineKeyboardButton("💡 Примеры идей", callback_data='examples')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Хотите проанализировать еще одну идею? 👇",
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"Error analyzing idea: {e}")
        await processing_msg.edit_text(
            f"❌ Произошла ошибка при анализе:\n`{str(e)}`\n\nПопробуйте еще раз или обратитесь к @your_username",
            parse_mode='Markdown'
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """🤖 **Startup Idea Validator - Помощь**

**Команды:**
/start - Начать работу с ботом
/analyze - Начать анализ идеи
/help - Показать эту справку

**Как использовать:**
1. Опишите свою идею стартапа
2. Получите детальный AI-анализ
3. Используйте рекомендации для запуска

**Что анализируется:**
• Рынок и конкуренты
• Риски и возможности
• MVP рекомендации
• Технический стек
• Roadmap разработки
• Оценка жизнеспособности

**Поддержка:** @your_username

Powered by Claude AI 🚀"""

    await update.message.reply_text(help_text, parse_mode='Markdown')


def main():
    """Запуск бота"""

    # Проверяем наличие токенов
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    groq_key = os.environ.get("GROQ_API_KEY")

    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return

    if not groq_key:
        logger.error("GROQ_API_KEY not set!")
        return

    # Создаем приложение
    application = Application.builder().token(bot_token).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    logger.info("Starting Startup Idea Validator Bot...")
    print("""
    ╔═══════════════════════════════════════════╗
    ║   Startup Idea Validator Bot             ║
    ║   AI-powered startup analysis            ║
    ╚═══════════════════════════════════════════╝

    Bot is running... Press Ctrl+C to stop.
    """)

    # Фикс для Python 3.14
    import asyncio
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
