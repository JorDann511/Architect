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

# Groq API client - функция для избежания проблем с кешированием
def get_groq_client():
    return Groq(api_key=os.environ.get("GROQ_API_KEY"))

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
• Создание онлайн-курсов по любой теме

📝 **Как использовать:**
Просто опишите свою идею стартапа, и я проведу детальный анализ!

Или используйте /analyze для пошагового ввода данных.
Используйте /course для создания онлайн-курса.

Powered by Groq AI 🤖"""

    keyboard = [
        [InlineKeyboardButton("🚀 Начать анализ", callback_data='start_analysis')],
        [InlineKeyboardButton("🎓 Создать курс", callback_data='create_course')],
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
    elif query.data == 'create_course':
        user_id = query.from_user.id
        user_states[user_id] = {'step': 'waiting_course_topic'}
        await query.edit_message_text(
            "🎓 **Создание курса**\n\nНапишите тему курса, который хотите создать.\n\nНапример:\n• Python для начинающих\n• Основы маркетинга\n• Дизайн в Figma",
            parse_mode='Markdown'
        )


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

    # Проверяем состояние пользователя
    if user_id in user_states and user_states[user_id].get('step') == 'waiting_course_topic':
        # Пользователь ввел тему курса
        await generate_course(update, context, text)
        # Очищаем состояние
        del user_states[user_id]
    elif user_id not in user_states:
        # Если пользователь просто описывает идею без команды
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
        groq_client = get_groq_client()
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
/course - Создать онлайн-курс по теме
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

Powered by Groq AI 🚀"""

    await update.message.reply_text(help_text, parse_mode='Markdown')


async def course_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /course"""
    text = """🎓 **AI Course Generator**

Я создам для вас полноценный онлайн-курс по любой теме!

**Что будет в курсе:**
• Структурированная программа обучения
• Теоретические материалы
• Практические задания
• Ссылки на видео и статьи
• Тесты для проверки знаний
• Красивый лендинг для прохождения

**Как использовать:**
Просто напишите тему курса после команды:

Например:
`/course Python для начинающих`
`/course Основы маркетинга`
`/course Дизайн в Figma`

Или просто напишите тему в следующем сообщении! 📚"""

    await update.message.reply_text(text, parse_mode='Markdown')

    # Сохраняем состояние
    user_id = update.effective_user.id
    user_states[user_id] = {'step': 'waiting_course_topic'}


async def generate_course(update: Update, context: ContextTypes.DEFAULT_TYPE, topic: str):
    """Генерация курса по теме"""

    processing_msg = await update.message.reply_text(
        f"🎓 Создаю курс по теме: **{topic}**\n\nЭто займет 20-30 секунд...\n\n⏳ Генерирую структуру курса...",
        parse_mode='Markdown'
    )

    try:
        # Промпт для генерации курса
        prompt = f"""Создай полноценный онлайн-курс по теме: "{topic}"

Структура курса должна включать:

1. **Название курса** - привлекательное и понятное
2. **Описание** - кратко о чем курс и для кого (2-3 предложения)
3. **Что вы изучите** - 5-7 ключевых навыков
4. **Программа курса** - 5-7 модулей, каждый модуль содержит:
   - Название модуля
   - 3-5 уроков с описанием
   - Практическое задание
   - Тест (3-5 вопросов с вариантами ответов)

5. **Рекомендуемые ресурсы:**
   - 3-5 видео на YouTube (реальные ссылки если знаешь, или примеры)
   - 3-5 статей/блогов
   - 2-3 книги

6. **Итоговый проект** - практическое задание для закрепления

Формат ответа - структурированный Markdown с эмодзи для красоты.
Будь конкретным и практичным. Курс должен быть реально полезным!"""

        # Вызов Groq API
        groq_client = get_groq_client()
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

        course_content = chat_completion.choices[0].message.content

        # Обновляем сообщение
        await processing_msg.edit_text(
            "✅ Курс создан!\n\n🎨 Генерирую красивый лендинг...",
            parse_mode='Markdown'
        )

        # Генерируем HTML лендинг
        html_content = generate_course_html(topic, course_content)

        # Сохраняем в файл
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            html_file_path = f.name

        # Удаляем сообщение о процессе
        await processing_msg.delete()

        # Отправляем курс текстом
        if len(course_content) > 4000:
            parts = [course_content[i:i+4000] for i in range(0, len(course_content), 4000)]
            for i, part in enumerate(parts):
                if i == 0:
                    await update.message.reply_text(
                        f"🎓 **Курс: {topic}**\n\n{part}",
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(part, parse_mode='Markdown')
        else:
            await update.message.reply_text(
                f"🎓 **Курс: {topic}**\n\n{course_content}",
                parse_mode='Markdown'
            )

        # Отправляем HTML файл
        with open(html_file_path, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=f"course_{topic.replace(' ', '_')}.html",
                caption="📱 Откройте этот файл в браузере для интерактивного прохождения курса!\n\n✨ Современный дизайн, прогресс-бар, чекбоксы для отметки пройденного."
            )

        # Удаляем временный файл
        import os as os_module
        os_module.unlink(html_file_path)

        # Кнопки для дальнейших действий
        keyboard = [
            [InlineKeyboardButton("🎓 Создать еще курс", callback_data='create_course')],
            [InlineKeyboardButton("🚀 Анализ стартапа", callback_data='start_analysis')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Хотите создать еще один курс? 👇",
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"Error generating course: {e}")
        await processing_msg.edit_text(
            f"❌ Произошла ошибка при создании курса:\n`{str(e)}`\n\nПопробуйте еще раз!",
            parse_mode='Markdown'
        )


def generate_course_html(topic: str, course_content: str):
    """Генерирует HTML лендинг для курса"""

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic} - Онлайн Курс</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .progress-container {{
            background: #f5f5f5;
            padding: 20px;
            border-bottom: 1px solid #e0e0e0;
        }}

        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            position: relative;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}

        .content {{
            padding: 40px;
        }}

        .module {{
            margin-bottom: 30px;
            border: 2px solid #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            transition: all 0.3s;
        }}

        .module:hover {{
            border-color: #667eea;
            box-shadow: 0 5px 15px rgba(102,126,234,0.2);
        }}

        .module-header {{
            background: #f8f9fa;
            padding: 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 15px;
        }}

        .module-header:hover {{
            background: #e9ecef;
        }}

        .module-checkbox {{
            width: 24px;
            height: 24px;
            cursor: pointer;
        }}

        .module-title {{
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
            flex: 1;
        }}

        .module-content {{
            padding: 20px;
            display: none;
            background: white;
        }}

        .module-content.active {{
            display: block;
        }}

        .lesson {{
            padding: 15px;
            margin: 10px 0;
            background: #f8f9fa;
            border-radius: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .lesson-checkbox {{
            width: 20px;
            height: 20px;
            cursor: pointer;
        }}

        .completed {{
            opacity: 0.6;
            text-decoration: line-through;
        }}

        .footer {{
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            border-top: 1px solid #e0e0e0;
        }}

        .footer p {{
            color: #666;
            margin-bottom: 10px;
        }}

        .badge {{
            display: inline-block;
            padding: 5px 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 20px;
            font-size: 0.9em;
            margin: 5px;
        }}

        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8em;
            }}

            .content {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 {topic}</h1>
            <p>Интерактивный онлайн-курс</p>
        </div>

        <div class="progress-container">
            <div class="progress-bar">
                <div class="progress-fill" id="progressBar">0%</div>
            </div>
            <p style="text-align: center; margin-top: 10px; color: #666;">
                <span id="completedCount">0</span> из <span id="totalCount">0</span> уроков пройдено
            </p>
        </div>

        <div class="content">
            <div style="white-space: pre-wrap; line-height: 1.8;">
{course_content}
            </div>

            <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 15px;">
                <h3 style="margin-bottom: 15px;">✅ Отметьте пройденные разделы:</h3>
                <div id="checklistContainer"></div>
            </div>
        </div>

        <div class="footer">
            <p>Создано с помощью AI Course Generator 🤖</p>
            <div>
                <span class="badge">Powered by Groq AI</span>
                <span class="badge">Telegram Bot</span>
            </div>
        </div>
    </div>

    <script>
        // Создаем чеклист из контента
        const content = document.querySelector('.content > div').textContent;
        const lines = content.split('\\n').filter(line => line.trim());
        const checklistContainer = document.getElementById('checklistContainer');

        let checkboxCount = 0;
        lines.forEach((line, index) => {{
            if (line.match(/^(#{1,3}|\\d+\\.|•|-)/)) {{
                const div = document.createElement('div');
                div.className = 'lesson';
                div.innerHTML = `
                    <input type="checkbox" class="lesson-checkbox" id="check_${{index}}" onchange="updateProgress()">
                    <label for="check_${{index}}" style="cursor: pointer; flex: 1;">${{line}}</label>
                `;
                checklistContainer.appendChild(div);
                checkboxCount++;
            }}
        }});

        document.getElementById('totalCount').textContent = checkboxCount;

        function updateProgress() {{
            const checkboxes = document.querySelectorAll('.lesson-checkbox');
            const checked = document.querySelectorAll('.lesson-checkbox:checked').length;
            const total = checkboxes.length;
            const percentage = total > 0 ? Math.round((checked / total) * 100) : 0;

            document.getElementById('progressBar').style.width = percentage + '%';
            document.getElementById('progressBar').textContent = percentage + '%';
            document.getElementById('completedCount').textContent = checked;

            // Сохраняем прогресс в localStorage
            const progress = Array.from(checkboxes).map(cb => cb.checked);
            localStorage.setItem('courseProgress', JSON.stringify(progress));
        }}

        // Восстанавливаем прогресс
        window.addEventListener('load', () => {{
            const saved = localStorage.getItem('courseProgress');
            if (saved) {{
                const progress = JSON.parse(saved);
                const checkboxes = document.querySelectorAll('.lesson-checkbox');
                progress.forEach((checked, index) => {{
                    if (checkboxes[index]) {{
                        checkboxes[index].checked = checked;
                    }}
                }});
                updateProgress();
            }}
        }});
    </script>
</body>
</html>"""

    return html


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
    application.add_handler(CommandHandler("course", course_command))
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
