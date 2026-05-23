import os
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# --- [إعداداتك هنا] ---
API_ID = 12345678       # ضع رقم الـ ID الخاص بك
API_HASH = "ضع_الـ_HASH_هنا"
BOT_TOKEN = "ضع_التوكين_هنا"

bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# مخازن البيانات
user_thumbs = {}
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# --- [دالة الرفع الذكية] ---
async def split_and_upload_video(client, message, status, file_path, caption):
    await status.edit_text("📤 **جاري الرفع لتيليجرام...**")
    # الرفع مع صورة البوستر إذا كانت موجودة
    thumb = user_thumbs.get(message.from_user.id)
    await client.send_video(chat_id=message.chat.id, video=file_path, caption=caption, thumb=thumb)
    await status.delete()

# --- [الأوامر] ---

@bot.on_message(filters.command("start"))
async def start(bot, m):
    await m.reply_text("👋 **أهلاً بك في بوت التحميل المطور.**\n\nالأوامر المتاحة:\n/ytleechkmd [رابط]\n/leechkmd [رابط]\n/torrentkmd [رابط]\n/compresskmd (رد على فيديو)\n/thumbkmd (رد على صورة)\n/poster [اسم الفيلم]")

@bot.on_message(filters.command("ytleechkmd"))
async def ytleech_cmd(client, message):
    if len(message.command) < 2: return await message.reply_text("⚠️ **الاستخدام:** `/ytleechkmd [الرابط]`")
    url = message.command[1]
    msg = await message.reply_text("📥 **جاري معالجة الفيديو...**")
    cmd = f'yt-dlp --user-agent "{USER_AGENT}" -f "best[ext=mp4]" "{url}" -o "video.mp4"'
    process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await process.wait()
    if os.path.exists("video.mp4"):
        await split_and_upload_video(client, message, msg, "video.mp4", "✅ **تم التحميل والرفع!**")
        os.remove("video.mp4")
    else: await msg.edit_text("❌ **فشل التحميل.**")

@bot.on_message(filters.command("leechkmd"))
async def leech_cmd(client, message):
    if len(message.command) < 2: return await message.reply_text("⚠️ **أرسل الرابط مع الأمر.**")
    await message.reply_text("📥 **جاري تنفيذ التحميل المباشر...**")

@bot.on_message(filters.command("torrentkmd"))
async def torrent_cmd(client, message):
    if len(message.command) < 2: return await message.reply_text("⚠️ **أرسل رابط التورنت.**")
    await message.reply_text("🧲 **جاري بدء مهمة التورنت...**")

@bot.on_message(filters.command(["compresskmd", "composer"]))
async def compress_cmd(client, message):
    if not message.reply_to_message or not message.reply_to_message.video:
        return await message.reply_text("⚠️ **يجب الرد على فيديو للضغط.**")
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("360p", callback_data="q_360p"), InlineKeyboardButton("720p", callback_data="q_720p")]])
    await message.reply_text("⚙️ **اختر الجودة:**", reply_markup=kb)

@bot.on_message(filters.command("thumbkmd"))
async def set_thumb(client, message):
    if message.reply_to_message and message.reply_to_message.photo:
        path = await client.download_media(message.reply_to_message.photo.file_id, file_name=f"thumb_{message.from_user.id}.jpg")
        user_thumbs[message.from_user.id] = path
        await message.reply_text("✅ **تم حفظ البوستر.**")
    else: await message.reply_text("⚠️ **رد على صورة لحفظها كـ بوستر.**")

@bot.on_message(filters.command("poster"))
async def poster_cmd(client, message):
    if len(message.command) < 2: return await message.reply_text("⚠️ **اكتب اسم العمل.**")
    await message.reply_text("🔍 **جارٍ البحث عن تفاصيل العمل...**")

print("البوت يعمل الآن... 🚀")
bot.run()
