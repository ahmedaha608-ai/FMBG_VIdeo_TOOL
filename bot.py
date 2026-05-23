from pyrogram import Client, filters
from pyrogram.types import Message
import subprocess
import os

print("FFmpeg Video Bot Started Successfully")

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client(
    "ffmpeg_video_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


@app.on_message(filters.command("start"))
async def start(_, message: Message):
    await message.reply_text(
        "✅ بوت ضغط الفيديو يعمل بنجاح\n\nأرسل فيديو للضغط."
    )


@app.on_message(filters.video)
async def compress_video(client, message: Message):
    try:
        status = await message.reply_text("📥 جاري تحميل الفيديو...")

        input_path = await message.download()
        output_path = f"compressed_{message.video.file_name or 'video.mp4'}"

        await status.edit("⚙️ جاري ضغط الفيديو...")

        command = [
            "ffmpeg",
            "-i", input_path,
            "-vcodec", "libx264",
            "-crf", "32",
            output_path
        ]

        subprocess.run(command, check=True)

        await status.edit("📤 جاري رفع الفيديو المضغوط...")

        await message.reply_video(output_path)

        os.remove(input_path)
        os.remove(output_path)

        await status.delete()

    except Exception as e:
        await message.reply_text(f"❌ Error:\n{str(e)}")


print("BOT IS RUNNING NOW")

app.run()
