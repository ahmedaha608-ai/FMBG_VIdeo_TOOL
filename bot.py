import os
import time
import asyncio
import subprocess
import mimetypes
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv

load_dotenv()
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("video_ultimate_bot", api_id=int(API_ID), api_hash=API_HASH, bot_token=BOT_TOKEN)

user_thumbs = {}
MAX_TG_SIZE = 2000 * 1024 * 1024  # 2 جيجابايت

QUALITY_SETTINGS = {
    "240p": {"scale": "426:240", "crf": "30", "bitrate": "64k"},
    "360p": {"scale": "640:360", "crf": "28", "bitrate": "96k"},
    "480p": {"scale": "854:480", "crf": "26", "bitrate": "128k"},
    "720p": {"scale": "1280:720", "crf": "24", "bitrate": "192k"}
}

# --- دالة شريط التقدم الفعلي ---
def create_progress_bar(current, total, status_text, start_time):
    now = time.time()
    diff = now - start_time
    if diff == 0: return ""
    percentage = current * 100 / total
    speed = current / diff
    speed_mb = speed / (1024 * 1024)
    current_mb = current / (1024 * 1024)
    total_mb = total / (1024 * 1024)
    progress_str = "█" * int(percentage // 10) + "░" * (10 - int(percentage // 10))
    return f"📊 **{status_text}**\n\n🎬 [{progress_str}] {percentage:.1f}%\n📦 **Processed:** {current_mb:.2f} MB / {total_mb:.2f} MB\n⚡ **Speed:** {speed_mb:.2f} MB/s\n⏱️ **Time:** {round(diff)}s"

async def progress_callback(current, total, client, message, status_text, start_time):
    if not hasattr(progress_callback, "last_update"): progress_callback.last_update = 0
    if time.time() - progress_callback.last_update > 4 or current == total:
        progress_callback.last_update = time.time()
        bar = create_progress_bar(current, total, status_text, start_time)
        try: await message.edit_text(bar)
        except: pass

# --- دالة التقطيع والرفع التلقائي للأحجام الضخمة ---
async def split_and_upload_video(client, message, status, file_path, caption_text):
    file_size = os.path.getsize(file_path)
    if file_size <= MAX_TG_SIZE:
        start_time = time.time()
        await message.reply_video(video=file_path, caption=caption_text, progress=progress_callback, progress_args=(client, status, "Uploading video", start_time))
        return

    await status.edit_text("✂️ File is larger than 2GB! Splitting video automatically...")
    duration_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    proc = await asyncio.create_subprocess_exec(*duration_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, _ = await proc.communicate()
    total_duration = float(stdout.decode().strip())

    num_parts = (file_size // MAX_TG_SIZE) + 1
    part_duration = total_duration / num_parts

    for i in range(num_parts):
        start_seek = i * part_duration
        part_output = f"{file_path}.part{i+1}.mp4"
        await status.edit_text(f"⚡ Processing part [{i+1}/{num_parts}]...")
        
        split_cmd = ["ffmpeg", "-ss", str(start_seek), "-i", file_path, "-t", str(part_duration), "-c", "copy", part_output, "-y"]
        process = await asyncio.create_subprocess_exec(*split_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        await process.wait()

        if os.path.exists(part_output):
            await status.edit_text(f"📤 Uploading part [{i+1}/{num_parts}]...")
            start_time = time.time()
            await message.reply_video(video=part_output, caption=f"{caption_text}\n🧩 **Part:** {i+1}/{num_parts}", progress=progress_callback, progress_args=(client, status, f"Uploading part {i+1}", start_time))
            os.remove(part_output)

# --- 1. أمر البداية ---
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        "👋 Welcome to the Ultimate Media Leech & Compressor Bot!\n\n"
        "💡 **How to use:**\n"
        "• `/leech [link]` - Download direct link\n"
        "• `/torrent [magnet/file]` - Download torrent\n"
        "• Reply with `/compress` on any video to change resolution\n"
        "• Reply with `/thumb` on any video after sending a photo to change thumbnail."
    )

# --- 2. معالجة أمر الـ Leech (الروابط المباشرة) ---
@app.on_message(filters.command("leech"))
async def handle_leech_cmd(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    target_link = None

    if len(message.command) > 1:
        target_link = message.text.split(None, 1)[1].strip()
    elif message.reply_to_message and message.reply_to_message.text:
        target_link = message.reply_to_message.text.strip()

    if not target_link or not target_link.startswith("http"):
        return await message.reply_text("⚠️ Error: Provide a link after the command or reply to a link message!")

    status = await message.reply_text("⏳ Initializing download from direct link...")
    await download_and_process_aria(client, message, status, target_link, chat_id, user_id)

# --- 3. معالجة أمر التورنت (ملفات وماجنت) ---
@app.on_message(filters.command("torrent"))
async def handle_torrent_cmd(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    target_input = None
    is_file = False

    if len(message.command) > 1:
        target_input = message.text.split(None, 1)[1].strip()
    elif message.reply_to_message:
        reply_msg = message.reply_to_message
        if reply_msg.document and reply_msg.document.file_name.endswith(".torrent"):
            status = await message.reply_text("⏳ Downloading .torrent file from Telegram...")
            target_input = await reply_msg.download()
            is_file = True
        elif reply_msg.text:
            target_input = reply_msg.text.strip()

    if not target_input:
        return await message.reply_text("⚠️ Error: Provide a magnet link after the command or reply to a `.torrent` file!")

    if not is_file and not (target_input.startswith("magnet:") or target_input.startswith("http")):
        return await message.reply_text("❌ Error: Invalid magnet link format.")

    status = await message.reply_text("⏳ Connecting to seeders via Aria2...")
    await download_and_process_aria(client, message, status, target_input, chat_id, user_id, is_file)

# --- دالة معالجة وتحميل Aria2 المشتركة ---
async def download_and_process_aria(client, message, status, target, chat_id, user_id, is_file=False):
    user_download_dir = f"dl_{chat_id}_{user_id}"
    os.makedirs(user_download_dir, exist_ok=True)

    cmd = ["aria2c", f"--dir={user_download_dir}", "--seed-time=0", "--max-connection-per-server=16", target]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await process.wait()

    if not os.path.exists(user_download_dir) or not os.listdir(user_download_dir):
        await status.edit_text("❌ Download failed. Check link or seeders status.")
        if is_file and os.path.exists(target): os.remove(target)
        return

    await status.edit_text("📤 Download finished! Preparing smart upload progress bar...")

    for root, dirs, files in os.walk(user_download_dir):
        for file in files:
            file_path = os.path.join(root, file)
            mime_type, _ = mimetypes.guess_type(file_path)
            caption = f"🎬 File uploaded successfully!\n📄 Name: `{file}`\n👤 Requested by: {message.from_user.mention}"

            try:
                await split_and_upload_video(client, message, status, file_path, caption)
            except Exception as e:
                await message.reply_text(f"❌ Upload Error: `{str(e)}`")
            
            if os.path.exists(file_path): os.remove(file_path)

    try:
        import shutil
        shutil.rmtree(user_download_dir)
        if is_file and os.path.exists(target): os.remove(target)
    except: pass
    await status.delete()

# --- 4. أمر ضغط الفيديو بالرد لتوليد أزرار الجودات ---
@app.on_message(filters.command("compress"))
async def ask_for_quality(client, message: Message):
    if not message.reply_to_message or not (message.reply_to_message.video or message.reply_to_message.document):
        return await message.reply_text("⚠️ Error: You must reply with this command to the video you want to compress!")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 240p", callback_data=f"q_240p_{message.reply_to_message.id}"), InlineKeyboardButton("🎬 360p", callback_data=f"q_360p_{message.reply_to_message.id}")],
        [InlineKeyboardButton("🎬 480p", callback_data=f"q_480p_{message.reply_to_message.id}"), InlineKeyboardButton("🎬 720p", callback_data=f"q_720p_{message.reply_to_message.id}")]
    ])
    await message.reply_text(f"⚙️ **Hello {message.from_user.first_name}, choose your preferred compression resolution:**", reply_markup=keyboard)

@app.on_callback_query(filters.regex(r"^q_"))
async def start_compression_callback(client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split("_")
    quality, target_msg_id = data_parts[1], int(data_parts[2])
    chat_id, user_id = callback_query.message.chat.id, callback_query.from_user.id
    
    try: target_msg = await client.get_messages(chat_id, target_msg_id)
    except: return await callback_query.answer("❌ Original video message not found.", show_alert=True)

    status = callback_query.message
    await status.edit_text(f"📥 Downloading source video file for {quality} conversion...")

    start_time = time.time()
    input_file = await target_msg.download(progress=progress_callback, progress_args=(client, status, "Downloading original video", start_time))
    
    output_file = f"compressed_{quality}_{chat_id}_{user_id}.mp4"
    await status.edit_text(f"⚡ Encoding to x265 ({quality})... please hold on.")
    
    settings = QUALITY_SETTINGS[quality]
    cmd = ["ffmpeg", "-i", input_file, "-vf", f"scale={settings['scale']}", "-vcodec", "libx265", "-crf", settings['crf'], "-preset", "faster", "-acodec", "aac", "-b:a", settings['bitrate'], output_file, "-y"]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await process.wait()

    if os.path.exists(output_file):
        caption = f"🎬 Compressed Successfully!\n⚙️ **Quality:** {quality} (HEVC x265)\n👤 Requested by: {callback_query.from_user.mention}"
        await split_and_upload_video(client, target_msg, status, output_file, caption)
        os.remove(output_file)
    else:
        await status.edit_text("❌ Compression processing failed.")

    if os.path.exists(input_file): os.remove(input_file)
    await status.delete()

# --- 5. تغيير الـ Thumbnail بالرد ---
@app.on_message(filters.photo)
async def save_photo_thumb(client, message: Message):
    thumb_path = f"thumb_{message.chat.id}_{message.from_user.id}.jpg"
    await message.download(file_name=thumb_path)
    user_thumbs[(message.chat.id, message.from_user.id)] = thumb_path
    await message.reply_text("🖼️ Thumbnail saved! Now reply to your video with `/thumb` to apply it.")

@app.on_message(filters.command("thumb"))
async def apply_thumb_via_reply(client, message: Message):
    chat_id, user_id = message.chat.id, message.from_user.id
    thumb_path = user_thumbs.get((chat_id, user_id))

    if not thumb_path: return await message.reply_text("⚠️ Send a photo first to use it as thumbnail.")
    if not message.reply_to_message: return await message.reply_text("⚠️ Reply with this command to the video target.")

    status = await message.reply_text("⏳ Processing video metadata with new thumbnail...")
    start_time = time.time()
    input_file = await message.reply_to_message.download(progress=progress_callback, progress_args=(client, status, "Downloading video file", start_time))
    
    start_time = time.time()
    await message.reply_to_message.reply_video(video=input_file, thumb=thumb_path, caption=f"🖼️ Thumbnail updated successfully!\n👤 Requested by: {message.from_user.mention}", progress=progress_callback, progress_args=(client, status, "Uploading custom thumbnail video", start_time))
    
    if os.path.exists(thumb_path): os.remove(thumb_path)
    if os.path.exists(input_file): os.remove(input_file)
    user_thumbs[(chat_id, user_id)] = None
    await status.delete()

if __name__ == "__main__":
    print("🚀 Bot deployed successfully with simplified clean commands!")
    app.run()
