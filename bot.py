import os
import sys
import time
import asyncio
import logging
import subprocess
import yt_dlp
import speedtest

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
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

async def run_cmd(cmd):
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return process.returncode, stdout.decode(), stderr.decode()

@app.on_message(filters.command("start"))
async def start_cmd(client, m: Message):
    await m.reply_text("🔥 KMD Professional Suite جاهز")

@app.on_message(filters.command("YtLeechkmd"))
async def yt_leech(client, m: Message):
    if len(m.command) < 2:
        return await m.reply_text("⚠️ أرسل الرابط")

    url = m.command[1]
    msg = await m.reply_text("🔍 جاري الفحص...")

    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)

            formats = [
                f for f in info.get('formats', [])
                if f.get('ext') == 'mp4'
            ][:8]

            buttons = []

            for f in formats:
                buttons.append([
                    InlineKeyboardButton(
                        f"{f.get('format_note', 'MP4')}",
                        callback_data=f"dl|{f['format_id']}|{url}"
                    )
                ])

            await msg.edit_text(
                "🎬 اختر الجودة",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

    except Exception as e:
        await msg.edit_text(f"❌ {e}")

@app.on_callback_query(filters.regex("^dl"))
async def download_callback(client, cq: CallbackQuery):
    _, fid, url = cq.data.split("|", 2)

    filename = f"{DOWNLOAD_DIR}/{time.time()}.mp4"

    await cq.message.edit_text("📥 جاري التحميل...")

    try:
        ydl_opts = {
            'format': fid,
            'outtmpl': filename,
            'quiet': True,
            'merge_output_format': 'mp4'
        }

        loop = asyncio.get_event_loop()

        await loop.run_in_executor(
            None,
            lambda: yt_dlp.YoutubeDL(ydl_opts).download([url])
        )

        await cq.message.edit_text("📤 جاري الرفع...")

        await cq.message.reply_video(
            filename,
            caption="✅ تم التحميل بواسطة KMD PRO"
        )

    except Exception as e:
        await cq.message.edit_text(f"❌ {e}")

    finally:
        if os.path.exists(filename):
            os.remove(filename)

@app.on_message(filters.command("x265"))
async def x265_encode(client, m: Message):

    if not m.reply_to_message:
        return await m.reply_text("⚠️ رد على فيديو")

    media = m.reply_to_message.video or m.reply_to_message.document

    if not media:
        return await m.reply_text("⚠️ الملف غير مدعوم")

    msg = await m.reply_text("📥 جاري التحميل...")

    input_file = await m.reply_to_message.download(
        file_name=f"{DOWNLOAD_DIR}/input.mp4"
    )

    output_file = f"{DOWNLOAD_DIR}/x265_output.mp4"

    await msg.edit_text("🔄 ضغط HEVC x265...")

    cmd = [
        "ffmpeg",
        "-i", input_file,
        "-c:v", "libx265",
        "-preset", "medium",
        "-crf", "28",
        "-c:a", "aac",
        "-b:a", "128k",
        output_file,
        "-y"
    ]

    code, out, err = await run_cmd(cmd)

    if code != 0:
        return await msg.edit_text(f"❌ فشل التحويل")

    await msg.edit_text("📤 جاري الرفع...")

    await m.reply_video(
        output_file,
        caption="✅ تم الضغط بصيغة HEVC x265"
    )

    for f in [input_file, output_file]:
        if os.path.exists(f):
            os.remove(f)

@app.on_message(filters.command("Speedtestkmd"))
async def speedtest_cmd(client, m: Message):
    msg = await m.reply_text("🚀 اختبار السرعة...")

    try:
        s = speedtest.Speedtest()
        s.get_best_server()

        d = s.download() / 1024 / 1024
        u = s.upload() / 1024 / 1024
        p = s.results.ping

        text = (
            f"📊 Download: {d:.2f} Mbps\n"
            f"📤 Upload: {u:.2f} Mbps\n"
            f"📡 Ping: {p:.0f} ms"
        )

        await msg.edit_text(text)

    except Exception as e:
        await msg.edit_text(f"❌ {e}")

@app.on_message(filters.command("kmdrestart"))
async def restart_bot(client, m: Message):
    await m.reply_text("♻️ جاري إعادة التشغيل...")
    os.execv(sys.executable, ['python'] + sys.argv)

if __name__ == "__main__":
    print("KMD PRO Started")
    app.run()
