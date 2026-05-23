import os
import asyncio
import mimetypes
from pyrogram import Client, filters
from pyrogram.types import Message
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not all([API_ID, API_HASH, BOT_TOKEN]):
    print("❌ خطأ: يرجى إعداد متغيرات البيئة (API_ID, API_HASH, BOT_TOKEN) أولاً!")
    exit(1)

app = Client("torrent_leech_bot", api_id=int(API_ID), api_hash=API_HASH, bot_token=BOT_TOKEN)

# مخزن مؤقت لتتبع حالة التورنت لكل مستخدم داخل كل جروب بشكل منفرد
torrent_states = {}

# 1. أمر البداية
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        "👋 أهلاً بك في بوت تحميل التورنت الفوري داخل المجموعات!\n\n"
        "اضغط على الأمر /torrentleechkmd من القائمة لبدء التحميل الفعلي."
    )

# 2. الاستماع لأمر التورنت (تأكد من تفعيله في BotFather بنفس الحروف الصغيرة)
@app.on_message(filters.command("torrentleechkmd"))
async def set_torrent_leech(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # حجز الحالة للمستخدم الحالي في هذا الجروب
    torrent_states[(chat_id, user_id)] = 'waiting_torrent'
    
    await message.reply_text(
        f"📥 {message.from_user.mention} تم تفعيل ميزة التورنت لك بنجاح!\n"
        "من فضلك أرسل الآن في الشات:\n"
        "• رابط مغناطيسي (Magnet Link)\n"
        "• أو قم برفع ملف تورنت ينتهي بـ `.torrent`"
    )

# 3. استقبال ومعالجة التورنت والروابط الفعلية عبر Aria2
@app.on_message(filters.text | filters.document)
async def handle_torrent_input(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # التحقق من أن المرسل هو صاحب الطلب المفعل
    if torrent_states.get((chat_id, user_id)) != 'waiting_torrent':
        return # تجاهل الرسالة إذا لم يضغط المستخدم على الأمر أولاً لعدم إزعاج الجروب

    download_target = None

    # التحقق من نوع المدخلات
    if message.document and message.document.file_name.endswith(".torrent"):
        status = await message.reply_text("⏳ جاري حفظ ملف التورنت على السيرفر لتشغيله...")
        download_target = await message.download()
        
    elif message.text:
        download_target = message.text.strip()
        if not (download_target.startswith("magnet:") or download_target.startswith("http")):
            return await message.reply_text("❌ عذراً، هذا ليس رابط مغناطيسي (Magnet) أو ملف تورنت صحيح.")
        status = await message.reply_text("⏳ جاري الاتصال بالـ Seeders وبدء التحميل الفعلي عبر Aria2...")
    else:
        return

    # إلغاء الحالة فوراً لمنع التكرار أثناء المعالجة
    torrent_states[(chat_id, user_id)] = None

    # إنشاء مجلد تحميل معزول تماماً لهذا المستخدم في هذا الجروب
    user_download_dir = f"torrent_{chat_id}_{user_id}"
    os.makedirs(user_download_dir, exist_ok=True)

    # أمر التحميل الفعلي
    cmd = [
        "aria2c", 
        f"--dir={user_download_dir}", 
        "--seed-time=0", 
        "--max-connection-per-server=16",
        download_target
    ]
    
    process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await process.wait()

    # التحقق من اكتمال التحميل
    if not os.path.exists(user_download_dir) or not os.listdir(user_download_dir):
        await status.edit_text("❌ فشل تحميل التورنت. تأكد أن التورنت نشط ويحتوي على متصلين (Seeds).")
        if message.document and os.path.exists(download_target):
            os.remove(download_target)
        return

    await status.edit_text("📤 اكتمل تحميل الملف على السيرفر! جاري الرفع إلى تليجرام الآن...")

    # رفع الملفات الناتجة وتحديد نوعها تلقائياً
    for root, dirs, files in os.walk(user_download_dir):
        for file in files:
            file_path = os.path.join(root, file)
            mime_type, _ = mimetypes.guess_type(file_path)
            caption_text = f"🎬 تم تحميل وتوصيل الملف بنجاح!\n👤 بطلب من: {message.from_user.mention}"

            try:
                if mime_type and mime_type.startswith("video"):
                    await message.reply_video(video=file_path, caption=caption_text)
                else:
                    await message.reply_document(document=file_path, caption=caption_text)
            except Exception as e:
                await message.reply_text(f"❌ حدث خطأ أثناء رفع الملف `{file}`:\n`{str(e)}`")
            
            if os.path.exists(file_path):
                os.remove(file_path)

    # تنظيف السيرفر بالكامل بعد انتهاء المهمة لضمان عدم امتلاء المساحة
    try:
        import shutil
        shutil.rmtree(user_download_dir)
        if message.document and os.path.exists(download_target):
            os.remove(download_target)
    except:
        pass

    await status.delete()

if __name__ == "__main__":
    print("🚀 البوت بدأ العمل ومستعد لاستقبال الأوامر المفعّلة من BotFather بدون كراش...")
    app.run()
