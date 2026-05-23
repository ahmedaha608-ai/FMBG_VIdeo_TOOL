import os
from pyrogram import Client, filters
from pyrogram.types import Message
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env (للتشغيل المحلي)
load_dotenv()

# جلب بيانات الاعتماد من البيئة
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# التأكد من إدخال البيانات الحساسة لتجنب توقف البوت
if not all([API_ID, API_HASH, BOT_TOKEN]):
    print("❌ خطأ: يرجى إعداد متغيرات البيئة API_ID و API_HASH و BOT_TOKEN أولاً!")
    exit(1)

# إعداد وتشغيل عميل Pyrogram
app = Client(
    "ffmpeg_video_bot",
    api_id=int(API_ID),
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# الاستجابة لأمر /start وإظهار القائمة المطلوبة
@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    menu_text = (
        "👋 أهلاً بك في بوت معالجة الفيديو بجودة عالية!\n\n"
        "إليك قائمة الأوامر المتاحة حالياً:\n"
        "🔹 /LeechKMD\n"
        "🔹 /Compressor_video\n"
        "🔹 /Change_thumbs\n"
        "🔹 /Ussting\n\n"
        "اضغط على أي أمر لتفعيله."
    )
    await message.reply_text(menu_text)

if __name__ == "__main__":
    print("🚀 البوت بدأ العمل بنجاح وهو جاهز لاستقبال الأوامر الفعالة...")
    app.run()
