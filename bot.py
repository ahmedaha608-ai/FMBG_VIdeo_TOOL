import os
import sys
import time
import asyncio
import logging
import requests
import yt_dlp
import speedtest

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client(
    "KMD_PRO",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

user_tasks = {}
send_modes = {}
last_edit_time = {}  # المتغير الجديد لتفادي Flood Wait

# =========================
# ULTRA PROGRESS
# =========================

async def ultra_progress(
    current,
    total,
    msg,
    start,
    uid,
    filename="video.mp4"
):

    if uid in user_tasks:
        if user_tasks[uid].get("cancel"):
            raise Exception("❌ تم إلغاء العملية")

    now = time.time()
    
    # التأكد من وجود المفتاح في القاموس
    if uid not in last_edit_time:
        last_edit_time[uid] = 0
    
    # شرط التحديث كل 5 ثوانٍ فقط لتجنب Flood Wait
    if now - last_edit_time[uid] > 5:
        diff = now - start
        if diff == 0: return
        
        percentage = current * 100 / total
        speed = current / diff
        
        # ... (باقي كود الحساب) ...
        # ملاحظة: تم ترك مساحة للكود الخاص بك، تأكد من إكمال بناء 'text' هنا
        
        try:
            # هنا يتم تحديث الرسالة
            # await msg.edit_text(text) 
            last_edit_time[uid] = now
        except Exception:
            pass
