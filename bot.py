import os
import asyncio
import mimetypes
from pyrogram import Client, filters
from pyrogram.types import Message, BotCommand
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not all([API_ID, API_HASH, BOT_TOKEN]):
    print("❌ خطأ: يرجى إعداد متغيرات البيئة أولاً!")
    exit(1)

app = Client("torrent_leech_bot", api_id=int(API_ID), api_hash=API_HASH, bot_token=BOT_TOKEN)

# مخزن مؤقت لتتبع حالة التورنت لكل مستخدم داخل كل جروب بشكل منفرد
# الصيغة: {(chat_id, user_id): 'waiting_torrent'}
torrent_states = {}

# أمر البداية
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        "👋 أهلاً بك في بوت تحميل التورنت الفوري!\n"
        "استخدم الأمر /torrentleechKMD لبدء تحميل أي ملف تورنت أو رابط مغناطيسي."
    )

# تفعيل أمر التورنت المنفصل
@app.on_message(filters.command("torrentleechKMD"))
async def set_torrent_leech(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # ربط الحالة بالجروب والمستخدم معاً لمنع التداخل
    torrent_states[(chat_id, user_id)] = 'waiting_torrent'
    
    await message.reply_text(
        f"📥 {message.from_user.mention} تم تفعيل ميزة التورنت الحقيقية لك!\n"
        "من فضلك أرسل الآن:\n"
        "• رابط مغناطيسي (Magnet Link)\n"
        "• أو اسحب وأفلت ملف تورنت بصيغة `.torrent`"
    )

# استقبال ملفات التورنت والروابط المغناطيسية ومعالجتها بشكل منفصل
@app.on_message(filters.text | filters.document)
async def handle_torrent_input(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # التحقق هل هذا المستخدم أرسل الملف بعد الضغط على الأمر الخاص به؟
    if torrent_states.get((chat_id, user_id)) != 'waiting_torrent':
        return # يتجاهل الرسالة تماماً إذا لم يطلب المستخدم الأمر أولاً لعدم إزعاج الجروب

    download_target = None

    # 1. إذا أرسل المستخدم ملف .torrent
    if message.document and message.document.file_name.endswith(".torrent"):
        status = await message.reply_text("⏳ جاري حفظ ملف التورنت على السيرفر لتشغيله...")
        download_target = await message.download()
        
    # 2. إذا أرسل المستخدم رابط نصي (Magnet)
    elif message.text:
        download_target = message.text.strip()
        if not (download_target.startswith("magnet:") or download_target.startswith("http")):
            return await message.reply_text("❌ عذراً، هذا ليس رابط مغناطيسي (Magnet) أو ملف تورنت صحيح.")
        status = await message.reply_text("⏳ جاري الاتصال بالـ Seeders وبدء التحميل عبر Aria2...")
    else:
        return

    # إلغاء الحالة فوراً لمنع التكرار أثناء المعالجة
    torrent_states[(chat_id, user_id)] = None

    # إنشاء مجلد تحميل فرعي خاص ومستقل بهذا المستخدم داخل هذا الجروب
    user_download_dir = f"torrent_{chat_id}_{user_id}"
    os.makedirs(user_download_dir, exist_ok=True)

    # تشغيل أداة aria2c الفعالة لتحميل التورنت بالخلفية بشكل غير متزامن (Async)
    cmd = [
        "aria2c", 
        f"--dir={user_download_dir}", 
        "--seed-time=0", 
        "--max-connection-per-server=16",
        download_target
    ]
    
    process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await process.wait()

    # فحص المجلد المخصص للمستخدم وجلب الملفات الناتجة
    if not os.path.exists(user_download_dir) or not os.listdir(user_download_dir):
        await status.edit_text("❌ فشل تحميل التورنت. تأكد أن الرابط يحتوي على متصلين (Seeds) نشطين.")
        # تنظيف ملف التورنت المرفوع لو كان موجوداً
        if message.document and os.path.exists(download_target):
            os.remove(download_target)
        return

    await status.edit_text("📤 اكتمل تحميل الفيلم بنجاح على السيرفر! جاري الرفع إلى تليجرام الآن...")

    # رفع كافة الملفات التي تم تحميلها داخل المجلد الخاص بالمستخدم
    for root, dirs, files in os.walk(user_download_dir):
        for file in files:
            file_path = os.path.join(root, file)
            
            # معرفة نوع الملف تلقائياً لرفعه بشكل صحيح
            mime_type, _ = mimetypes.guess_type(file_path)
            caption_text = f"🎬 تم تحميل وتوصيل الملف بنجاح!\n👤 بطلب من: {message.from_user.mention}"

            try:
                if mime_type and mime_type.startswith("video"):
                    await message.reply_video(video=file_path, caption=caption_text)
                else:
                    await message.reply_document(document=file_path, caption=caption_text)
            except Exception as e:
                await message.reply_text(f"❌ حدث خطأ أثناء رفع الملف `{file}`:\n`{str(e)}`")
            
            # حذف الملف فوراً بعد الرفع لتوفير مساحة السيرفر
            if os.path.exists(file_path):
                os.remove(file_path)

    # تنظيف المجلد المؤقت والملفات الأساسية بالكامل بعد انتهاء المهمة
    try:
        import shutil
        shutil.rmtree(user_download_dir)
        if message.document and os.path.exists(download_target):
            os.remove(download_target)
    except:
        pass

    await status.delete()

if __name__ == "__main__":
    app.start()
    # تعيين القائمة الرسمية الشفافة بالأمر الجديد المنفصل
    app.set_bot_commands([
        BotCommand("torrentleechKMD", "📥 تحميل ملفات وروابط التورنت الفورية"),
        BotCommand("start", "👋 تشغيل البوت")
    ])
    print("🚀 بوت التورنت المنفصل والآمن للمجموعات يعمل الآن بنجاح...")
    asyncio.get_event_loop().run_forever()
