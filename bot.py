import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, timedelta
import asyncpg
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Список хэштегов, которые мы отслеживаем
ALLOWED_HASHTAGS = ['#охужэтоимя', '#тт', '#dance_me', '#my_life', '#music', '#the_test_of_life', '#work', '#sports', '#hair', '#concert', '#mymem', '#элайнеры', '#auto', '#drugs', '#Израиль']

# Функция для извлечения хэштегов из текста
def extract_hashtags(text):
    return [word for word in text.split() if word.startswith('#')]

# Подключение к базе данных Supabase
async def connect_db():
    conn = await asyncpg.connect('postgresql://postgres.qsdzkiwrxetumusvqqnd:cOrHC4sLlyVhttJy@aws-0-us-west-1.pooler.supabase.com:6543/postgres')
    return conn

# Сохранение постов в базе данных
async def save_post_to_db(message, media_info, hashtags):
    conn = await connect_db()
    try:
        await conn.execute('''
            INSERT INTO posts (message, hashtags, media_type, media_file_path, created_at) 
            VALUES ($1, $2, $3, $4, $5)
        ''', message, hashtags, media_info.get('type'), media_info.get('file_path'), datetime.now())
    finally:
        await conn.close()

# Функция для получения всех сообщений из канала
async def fetch_channel_posts(context, last_sync_time):
    channel_id = "@TimeHope_bot"  # Ваш ID канала
    current_time = datetime.now()
    
    async for message in context.bot.get_chat_history(channel_id):
        message_time = message.date.replace(tzinfo=None)
        if last_sync_time <= message_time <= current_time:
            hashtags = extract_hashtags(message.text or message.caption)
            matched_hashtags = [hashtag for hashtag in hashtags if hashtag in ALLOWED_HASHTAGS]
            
            if matched_hashtags:
                media_info = await save_media(message, context)
                await save_post_to_db(message.text or message.caption, media_info, matched_hashtags)

# Функция для сохранения медиа
async def save_media(message, context):
    media_info = {}

    if message.photo:
        file_id = message.photo[-1].file_id
        media_info['type'] = 'photo'
        media_info['file_id'] = file_id
        file_path = await download_file(file_id, "photos", context)
        media_info['file_path'] = file_path
        
    elif message.video:
        file_id = message.video.file_id
        media_info['type'] = 'video'
        media_info['file_id'] = file_id
        file_path = await download_file(file_id, "videos", context)
        media_info['file_path'] = file_path
    
    elif message.animation:
        file_id = message.animation.file_id
        media_info['type'] = 'gif'
        media_info['file_id'] = file_id
        file_path = await download_file(file_id, "gifs", context)
        media_info['file_path'] = file_path
    
    return media_info

# Функция для загрузки файлов
async def download_file(file_id, folder, context):
    file = await context.bot.get_file(file_id)
    file_path = os.path.join(folder, file.file_id)
    
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    await file.download_to_drive(file_path)
    return file_path

# Планировщик синхронизации в 00:00
def start_scheduler(application):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(sync_with_channel, 'cron', hour=0, minute=0, timezone='Europe/Moscow', args=[application])
    scheduler.start()

# Функция для синхронизации с каналом
async def sync_with_channel(application):
    logger.info("Синхронизация с каналом началась...")
    last_sync_time = datetime.now() - timedelta(days=1)
    async with application.bot:
        await fetch_channel_posts(application, last_sync_time)
    logger.info("Синхронизация завершена.")

if __name__ == "__main__":
    application = ApplicationBuilder().token("7956547094:AAGaa0bxNyavehJw6HmMLatxJRGLbgIVNrs").build()

    # Запуск планировщика и бота
    start_scheduler(application)
    application.run_polling()
