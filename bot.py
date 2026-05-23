from pyrogram import Client, filters
import os

print("BOT STARTING...")

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client(
    "video_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start"))
def start(client, message):
    message.reply_text("البوت شغال بنجاح ✅")

@app.on_message(filters.video)
def video_handler(client, message):
    message.reply_text("تم استلام الفيديو ✅")

print("BOT IS RUNNING NOW")

app.run()
