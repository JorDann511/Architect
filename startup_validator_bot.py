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

Я **Architect - Startup Idea Validator** - AI-ассистент для анализа стартап-идей.

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

Powered by yolam_ 🤖"""

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
        # Промпт для генерации курса в JSON формате
        prompt = f"""Создай полноценный онлайн-курс по теме: "{topic}"

Верни ответ СТРОГО в JSON формате:

{{
  "title": "Название курса",
  "description": "Описание курса (2-3 предложения)",
  "duration": "Примерная длительность (например: 4 недели, 20 часов)",
  "level": "Уровень сложности (Начальный/Средний/Продвинутый)",
  "skills": ["навык 1", "навык 2", "навык 3", "навык 4", "навык 5"],
  "modules": [
    {{
      "id": 1,
      "title": "Название модуля",
      "description": "Краткое описание модуля",
      "duration": "2 часа",
      "lessons": [
        {{
          "title": "Урок 1",
          "description": "Подробное описание урока (3-4 предложения о том, что изучается)",
          "duration": "20 мин",
          "topics": ["Тема 1", "Тема 2", "Тема 3"],
          "materials": [
            {{"type": "video", "title": "Название видео", "url": "https://youtube.com/..."}},
            {{"type": "article", "title": "Название статьи", "url": "https://..."}},
            {{"type": "docs", "title": "Документация", "url": "https://..."}}
          ],
          "practice": "Конкретное практическое задание для этого урока"
        }}
      ],
      "practice": "Практическое задание для всего модуля",
      "quiz": [
        {{
          "question": "Вопрос теста?",
          "options": ["Вариант 1", "Вариант 2", "Вариант 3"],
          "correct": 0
        }}
      ]
    }}
  ],
  "resources": {{
    "videos": ["Ссылка или название видео 1", "Ссылка или название видео 2"],
    "articles": ["Ссылка или название статьи 1", "Ссылка или название статьи 2"],
    "books": ["Название книги 1", "Название книги 2"]
  }},
  "finalProject": "Описание итогового проекта"
}}

ВАЖНО:
- Создай 5-7 модулей, каждый с 3-5 уроками
- Для каждого урока укажи конкретные темы (topics)
- Добавь реальные ссылки на материалы (YouTube, статьи, документацию)
- Практические задания должны быть конкретными и выполнимыми
- Будь конкретным и практичным!"""

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

        course_json = chat_completion.choices[0].message.content

        # Парсим JSON (убираем markdown если есть)
        import json
        import re
        json_match = re.search(r'\{.*\}', course_json, re.DOTALL)
        if json_match:
            course_data = json.loads(json_match.group())
        else:
            course_data = json.loads(course_json)

        # Обновляем сообщение
        await processing_msg.edit_text(
            "✅ Курс создан!\n\n🎨 Генерирую интерактивный лендинг...",
            parse_mode='Markdown'
        )

        # Генерируем HTML лендинг
        html_content = generate_course_html(topic, course_data)

        # Сохраняем в файл
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            html_file_path = f.name

        # Удаляем сообщение о процессе
        await processing_msg.delete()

        # Отправляем только HTML файл
        with open(html_file_path, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=f"course_{topic.replace(' ', '_')}.html",
                caption=f"🎓 **Курс готов: {course_data['title']}**\n\n📱 Откройте файл в браузере для интерактивного обучения!\n\n✨ Роадмап с прогрессом\n✨ Интерактивные уроки\n✨ Тесты и задания\n✨ Современный дизайн"
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


def generate_course_html(topic: str, course_data: dict):
    """Генерирует современный HTML лендинг для курса с роадмапом"""

    # Генерируем HTML для модулей
    modules_html = ""
    lesson_id = 0
    for idx, module in enumerate(course_data['modules'], 1):
        lessons_html = ""
        for lesson_idx, lesson in enumerate(module['lessons']):
            lesson_id += 1
            # Экранируем данные для JSON
            import json

            # Подготавливаем данные урока
            lesson_topics = lesson.get('topics', ['Основные концепции', 'Практические примеры', 'Лучшие практики'])
            lesson_materials = lesson.get('materials', [
                {'type': 'video', 'title': 'Видео-лекция по теме', 'url': '#'},
                {'type': 'article', 'title': 'Статья с примерами', 'url': '#'},
                {'type': 'docs', 'title': 'Документация', 'url': '#'}
            ])
            lesson_practice = lesson.get('practice', 'Примените полученные знания на практике.')

            lesson_data_json = json.dumps({
                'title': lesson['title'],
                'description': lesson['description'],
                'duration': lesson['duration'],
                'module': module['title'],
                'topics': lesson_topics,
                'materials': lesson_materials,
                'practice': lesson_practice
            }).replace("'", "\\'")

            lessons_html += f"""
                <div class="lesson" data-lesson-id="{lesson_id}" data-lesson='{lesson_data_json}'>
                    <div class="lesson-icon">📖</div>
                    <div class="lesson-content">
                        <h4>{lesson['title']}</h4>
                        <p>{lesson['description']}</p>
                        <span class="duration">⏱ {lesson['duration']}</span>
                    </div>
                    <input type="checkbox" class="lesson-check" data-module="{idx}" onclick="event.stopPropagation()">
                </div>
            """

        modules_html += f"""
        <div class="module" data-module="{idx}">
            <div class="module-header">
                <div class="module-number">{idx}</div>
                <div class="module-info">
                    <h3>{module['title']}</h3>
                    <p>{module['description']}</p>
                    <span class="module-duration">⏱ {module['duration']}</span>
                </div>
                <div class="module-status">
                    <span class="status-badge">0/{len(module['lessons'])}</span>
                </div>
            </div>
            <div class="module-content">
                <div class="lessons">
                    {lessons_html}
                </div>
                <div class="practice">
                    <h4>💪 Практическое задание</h4>
                    <p>{module['practice']}</p>
                </div>
            </div>
        </div>
        """

    # Генерируем HTML для ресурсов
    resources_html = ""
    if course_data.get('resources'):
        resources = course_data['resources']

        videos_html = "".join([f'<li>🎥 {v}</li>' for v in resources.get('videos', [])])
        articles_html = "".join([f'<li>📄 {a}</li>' for a in resources.get('articles', [])])
        books_html = "".join([f'<li>📚 {b}</li>' for b in resources.get('books', [])])

        resources_html = f"""
        <div class="resources">
            <h3>📚 Рекомендуемые ресурсы</h3>
            <div class="resources-grid">
                <div class="resource-category">
                    <h4>Видео</h4>
                    <ul>{videos_html}</ul>
                </div>
                <div class="resource-category">
                    <h4>Статьи</h4>
                    <ul>{articles_html}</ul>
                </div>
                <div class="resource-category">
                    <h4>Книги</h4>
                    <ul>{books_html}</ul>
                </div>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{course_data['title']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .hero {{
            background: white;
            border-radius: 24px;
            padding: 60px 40px;
            margin-bottom: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
        }}

        .hero h1 {{
            font-size: 3em;
            margin-bottom: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .hero-meta {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 30px;
            flex-wrap: wrap;
        }}

        .meta-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 24px;
            background: #f8f9fa;
            border-radius: 12px;
            font-weight: 500;
        }}

        .skills {{
            background: white;
            border-radius: 24px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .skills h2 {{
            margin-bottom: 20px;
            font-size: 2em;
        }}

        .skills-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }}

        .skill-item {{
            padding: 15px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .progress-section {{
            background: white;
            border-radius: 24px;
            padding: 30px 40px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .progress-bar {{
            width: 100%;
            height: 40px;
            background: #e0e0e0;
            border-radius: 20px;
            overflow: hidden;
            position: relative;
            margin-bottom: 15px;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 1.1em;
        }}

        .progress-text {{
            text-align: center;
            color: #666;
            font-size: 1.1em;
        }}

        .roadmap {{
            background: white;
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }}

        .roadmap h2 {{
            margin-bottom: 30px;
            font-size: 2em;
        }}

        .module {{
            margin-bottom: 20px;
            border: 2px solid #e0e0e0;
            border-radius: 16px;
            overflow: hidden;
            transition: all 0.3s;
        }}

        .module.completed {{
            border-color: #4caf50;
            background: #f1f8f4;
        }}

        .module-header {{
            padding: 25px;
            background: #f8f9fa;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 20px;
            transition: background 0.3s;
        }}

        .module-header:hover {{
            background: #e9ecef;
        }}

        .module-number {{
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5em;
            font-weight: bold;
            flex-shrink: 0;
        }}

        .module.completed .module-number {{
            background: #4caf50;
        }}

        .module-info {{
            flex: 1;
        }}

        .module-info h3 {{
            font-size: 1.4em;
            margin-bottom: 8px;
        }}

        .module-info p {{
            color: #666;
            margin-bottom: 8px;
        }}

        .module-duration {{
            color: #999;
            font-size: 0.9em;
        }}

        .module-status {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .status-badge {{
            padding: 8px 16px;
            background: #667eea;
            color: white;
            border-radius: 20px;
            font-weight: 500;
        }}

        .module.completed .status-badge {{
            background: #4caf50;
        }}

        .module-content {{
            display: none;
            padding: 25px;
            background: white;
        }}

        .module-content.active {{
            display: block;
        }}

        .lessons {{
            margin-bottom: 25px;
        }}

        .lesson {{
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 20px;
            margin-bottom: 15px;
            background: #f8f9fa;
            border-radius: 12px;
            transition: all 0.3s;
            cursor: pointer;
        }}

        .lesson:hover {{
            background: #e9ecef;
            transform: translateX(5px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}

        .lesson.completed {{
            background: #e8f5e9;
        }}

        .lesson-icon {{
            font-size: 1.5em;
        }}

        .lesson-content {{
            flex: 1;
        }}

        .lesson-content h4 {{
            margin-bottom: 5px;
            font-size: 1.1em;
        }}

        .lesson-content p {{
            color: #666;
            font-size: 0.95em;
            margin-bottom: 5px;
        }}

        .duration {{
            color: #999;
            font-size: 0.85em;
        }}

        .lesson-check {{
            width: 24px;
            height: 24px;
            cursor: pointer;
        }}

        /* Модальное окно для урока */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            animation: fadeIn 0.3s ease;
            align-items: center;
            justify-content: center;
        }}

        .modal.active {{
            display: flex;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        .modal-content {{
            background: white;
            border-radius: 24px;
            max-width: 700px;
            width: 90%;
            max-height: 85vh;
            overflow-y: auto;
            position: relative;
            animation: slideUp 0.3s ease;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        }}

        @keyframes slideUp {{
            from {{ transform: translateY(50px); opacity: 0; }}
            to {{ transform: translateY(0); opacity: 1; }}
        }}

        .modal-header {{
            padding: 30px 30px 20px 30px;
            border-bottom: 2px solid #f0f0f0;
            position: sticky;
            top: 0;
            background: white;
            z-index: 10;
            border-radius: 24px 24px 0 0;
        }}

        .modal-close {{
            position: absolute;
            right: 20px;
            top: 20px;
            font-size: 32px;
            font-weight: 300;
            color: #999;
            cursor: pointer;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: all 0.2s ease;
            background: transparent;
            border: none;
        }}

        .modal-close:hover {{
            background: #f0f0f0;
            color: #000;
        }}

        .modal-module-badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        .modal-title {{
            font-size: 28px;
            font-weight: 700;
            color: #000;
            line-height: 1.3;
            margin-bottom: 8px;
        }}

        .modal-meta {{
            font-size: 14px;
            color: #666;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .modal-body {{
            padding: 30px;
        }}

        .modal-section {{
            margin-bottom: 30px;
        }}

        .modal-section-title {{
            font-size: 18px;
            font-weight: 700;
            color: #000;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .modal-section-title::before {{
            content: '';
            width: 4px;
            height: 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 2px;
        }}

        .modal-description {{
            font-size: 16px;
            line-height: 1.8;
            color: #333;
            margin-bottom: 20px;
        }}

        .modal-list {{
            list-style: none;
            padding: 0;
        }}

        .modal-list li {{
            padding: 12px 0;
            border-bottom: 1px solid #f0f0f0;
            font-size: 15px;
            line-height: 1.6;
            color: #333;
            display: flex;
            align-items: flex-start;
            gap: 10px;
        }}

        .modal-list li:last-child {{
            border-bottom: none;
        }}

        .modal-list li::before {{
            content: '✓';
            color: #667eea;
            font-weight: 700;
            font-size: 18px;
            flex-shrink: 0;
        }}

        .modal-links {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        .modal-link {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 15px 20px;
            background: #f8f9fa;
            border-radius: 12px;
            text-decoration: none;
            color: #000;
            font-size: 15px;
            font-weight: 500;
            transition: all 0.2s ease;
            border: 2px solid transparent;
        }}

        .modal-link:hover {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            transform: translateX(5px);
        }}

        .modal-link::before {{
            content: '🔗';
            font-size: 20px;
        }}

        .modal-practice {{
            background: #fff3e0;
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #ff9800;
        }}

        .modal-practice h4 {{
            margin-bottom: 10px;
            color: #f57c00;
            font-size: 16px;
        }}

        .modal-practice p {{
            color: #333;
            line-height: 1.6;
        }}

        .practice {{
            padding: 20px;
            background: #fff3e0;
            border-radius: 12px;
            border-left: 4px solid #ff9800;
            margin-bottom: 20px;
        }}

        .practice h4 {{
            margin-bottom: 10px;
            color: #f57c00;
        }}

        .resources {{
            background: white;
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }}

        .resources h3 {{
            margin-bottom: 25px;
            font-size: 2em;
        }}

        .resources-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
        }}

        .resource-category {{
            padding: 20px;
            background: #f8f9fa;
            border-radius: 12px;
        }}

        .resource-category h4 {{
            margin-bottom: 15px;
            font-size: 1.2em;
        }}

        .resource-category ul {{
            list-style: none;
        }}

        .resource-category li {{
            padding: 10px 0;
            border-bottom: 1px solid #e0e0e0;
        }}

        .resource-category li:last-child {{
            border-bottom: none;
        }}

        .final-project {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }}

        .final-project h3 {{
            margin-bottom: 20px;
            font-size: 2em;
        }}

        .footer {{
            text-align: center;
            padding: 30px;
            color: white;
        }}

        .footer p {{
            margin-bottom: 10px;
            opacity: 0.9;
        }}

        @media (max-width: 768px) {{
            .hero {{
                padding: 40px 20px;
            }}

            .hero h1 {{
                font-size: 2em;
            }}

            .hero-meta {{
                flex-direction: column;
                gap: 15px;
            }}

            .module-header {{
                flex-direction: column;
                align-items: flex-start;
            }}

            .resources-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>🎓 {course_data['title']}</h1>
            <p style="font-size: 1.2em; color: #666; margin-bottom: 20px;">{course_data['description']}</p>
            <div class="hero-meta">
                <div class="meta-item">
                    <span>⏱</span>
                    <span>{course_data['duration']}</span>
                </div>
                <div class="meta-item">
                    <span>📊</span>
                    <span>{course_data['level']}</span>
                </div>
                <div class="meta-item">
                    <span>📚</span>
                    <span>{len(course_data['modules'])} модулей</span>
                </div>
            </div>
        </div>

        <div class="skills">
            <h2>✨ Что вы изучите</h2>
            <div class="skills-grid">
                {"".join([f'<div class="skill-item"><span>✓</span><span>{skill}</span></div>' for skill in course_data['skills']])}
            </div>
        </div>

        <div class="progress-section">
            <h3 style="margin-bottom: 20px;">📈 Ваш прогресс</h3>
            <div class="progress-bar">
                <div class="progress-fill" id="progressBar">0%</div>
            </div>
            <p class="progress-text">
                <span id="completedCount">0</span> из <span id="totalCount">0</span> уроков завершено
            </p>
        </div>

        <div class="roadmap">
            <h2>🗺 Роадмап курса</h2>
            {modules_html}
        </div>

        {resources_html}

        <div class="final-project">
            <h3>🎯 Итоговый проект</h3>
            <p style="font-size: 1.1em; line-height: 1.6;">{course_data['finalProject']}</p>
        </div>

        <div class="footer">
            <p>Создано с помощью AI Course Generator 🤖</p>
            <p style="opacity: 0.7;">Powered by Groq AI · Telegram Bot</p>
        </div>
    </div>

    <!-- Модальное окно для урока -->
    <div class="modal" id="lessonModal">
        <div class="modal-content">
            <div class="modal-header">
                <button class="modal-close" onclick="closeModal()">&times;</button>
                <div class="modal-module-badge" id="modalModuleName"></div>
                <h2 class="modal-title" id="modalLessonTitle"></h2>
                <div class="modal-meta">
                    <span>⏱</span>
                    <span id="modalLessonDuration"></span>
                </div>
            </div>
            <div class="modal-body">
                <div class="modal-section">
                    <h3 class="modal-section-title">📖 Описание урока</h3>
                    <p class="modal-description" id="modalLessonDescription"></p>
                </div>

                <div class="modal-section">
                    <h3 class="modal-section-title">🎯 Что вы изучите</h3>
                    <ul class="modal-list" id="modalLessonTopics">
                        <!-- Темы будут добавлены динамически -->
                    </ul>
                </div>

                <div class="modal-section">
                    <h3 class="modal-section-title">📚 Материалы для изучения</h3>
                    <div class="modal-links" id="modalLessonLinks">
                        <!-- Ссылки будут добавлены динамически -->
                    </div>
                </div>

                <div class="modal-section">
                    <div class="modal-practice">
                        <h4>💪 Практическое задание</h4>
                        <p id="modalLessonPractice">Примените полученные знания на практике, выполнив задание из этого урока.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Подсчет общего количества уроков
        const totalLessons = document.querySelectorAll('.lesson-check').length;
        document.getElementById('totalCount').textContent = totalLessons;

        // Загрузка сохраненного прогресса
        function loadProgress() {{
            const saved = localStorage.getItem('courseProgress_{topic.replace(" ", "_")}');
            if (saved) {{
                const progress = JSON.parse(saved);
                document.querySelectorAll('.lesson-check').forEach((checkbox, index) => {{
                    if (progress[index]) {{
                        checkbox.checked = true;
                        checkbox.closest('.lesson').classList.add('completed');
                    }}
                }});
                updateProgress();
            }}
        }}

        // Сохранение прогресса
        function saveProgress() {{
            const progress = Array.from(document.querySelectorAll('.lesson-check')).map(cb => cb.checked);
            localStorage.setItem('courseProgress_{topic.replace(" ", "_")}', JSON.stringify(progress));
        }}

        // Обновление прогресса
        function updateProgress() {{
            const checkboxes = document.querySelectorAll('.lesson-check');
            const checked = document.querySelectorAll('.lesson-check:checked').length;
            const percentage = totalLessons > 0 ? Math.round((checked / totalLessons) * 100) : 0;

            document.getElementById('progressBar').style.width = percentage + '%';
            document.getElementById('progressBar').textContent = percentage + '%';
            document.getElementById('completedCount').textContent = checked;

            // Обновляем статус модулей
            document.querySelectorAll('.module').forEach(module => {{
                const moduleNum = module.dataset.module;
                const moduleCheckboxes = module.querySelectorAll('.lesson-check');
                const moduleChecked = module.querySelectorAll('.lesson-check:checked').length;
                const statusBadge = module.querySelector('.status-badge');

                statusBadge.textContent = `${{moduleChecked}}/${{moduleCheckboxes.length}}`;

                if (moduleChecked === moduleCheckboxes.length && moduleCheckboxes.length > 0) {{
                    module.classList.add('completed');
                }} else {{
                    module.classList.remove('completed');
                }}
            }});

            saveProgress();
        }}

        // Обработчики событий
        document.querySelectorAll('.lesson-check').forEach(checkbox => {{
            checkbox.addEventListener('change', function() {{
                if (this.checked) {{
                    this.closest('.lesson').classList.add('completed');
                }} else {{
                    this.closest('.lesson').classList.remove('completed');
                }}
                updateProgress();
            }});
        }});

        // Раскрытие/скрытие модулей
        document.querySelectorAll('.module-header').forEach(header => {{
            header.addEventListener('click', function() {{
                const content = this.nextElementSibling;
                content.classList.toggle('active');
            }});
        }});

        // Открытие модального окна при клике на урок
        document.querySelectorAll('.lesson').forEach(lesson => {{
            lesson.addEventListener('click', function(e) {{
                // Не открываем модалку если кликнули на чекбокс
                if (e.target.classList.contains('lesson-check')) {{
                    return;
                }}

                const lessonData = JSON.parse(this.dataset.lesson);
                openLessonModal(lessonData);
            }});
        }});

        // Функция открытия модального окна
        function openLessonModal(lessonData) {{
            const modal = document.getElementById('lessonModal');

            // Заполняем основные данные
            document.getElementById('modalModuleName').textContent = lessonData.module;
            document.getElementById('modalLessonTitle').textContent = lessonData.title;
            document.getElementById('modalLessonDuration').textContent = lessonData.duration;
            document.getElementById('modalLessonDescription').textContent = lessonData.description;

            // Заполняем темы урока
            const topicsList = document.getElementById('modalLessonTopics');
            topicsList.innerHTML = '';
            lessonData.topics.forEach(topic => {{
                const li = document.createElement('li');
                li.textContent = topic;
                topicsList.appendChild(li);
            }});

            // Заполняем материалы
            const linksContainer = document.getElementById('modalLessonLinks');
            linksContainer.innerHTML = '';
            lessonData.materials.forEach(material => {{
                const link = document.createElement('a');
                link.href = material.url;
                link.className = 'modal-link';
                link.target = '_blank';
                link.rel = 'noopener noreferrer';

                // Иконка в зависимости от типа
                const icon = material.type === 'video' ? '🎥' :
                            material.type === 'article' ? '📄' : '📚';

                link.innerHTML = `${{icon}} ${{material.title}}`;

                // Если ссылка заглушка, отключаем переход
                if (material.url === '#') {{
                    link.onclick = (e) => {{ e.preventDefault(); }};
                    link.style.opacity = '0.6';
                }}

                linksContainer.appendChild(link);
            }});

            // Заполняем практическое задание
            document.getElementById('modalLessonPractice').textContent = lessonData.practice;

            // Показываем модалку
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }}

        // Функция закрытия модального окна
        function closeModal() {{
            const modal = document.getElementById('lessonModal');
            modal.classList.remove('active');
            document.body.style.overflow = 'auto';
        }}

        // Закрытие по клику вне модалки
        document.getElementById('lessonModal').addEventListener('click', function(e) {{
            if (e.target === this) {{
                closeModal();
            }}
        }});

        // Закрытие по ESC
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape') {{
                closeModal();
            }}
        }});

        // Инициализация
        loadProgress();
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
