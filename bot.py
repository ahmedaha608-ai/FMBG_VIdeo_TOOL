import os
import time
import asyncio
import subprocess
import re
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

async def split_and_upload_video(client, message, status, file_path, caption_text):
    file_size = os.path.getsize(file_path)
    if file_size <= MAX_TG_SIZE:
        start_time = time.time()
        await message.reply_video(video=file_path, caption=caption_text, progress=progress_callback, progress_args=(client, status, "Uploading video to Telegram", start_time))
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

@app.on_message(filters.command("start"))
async def start_silent(client, message: Message):
    pass

# --- دالة التحميل الذكية والمطورة للروابط المعقدة ---
async def process_single_link(client, message, status, target_link, chat_id, user_id):
    # تنظيف الرابط تلقائياً لو بيبدأ بـ حروف أو أرقام غلط مثل (2/https)
    target_link = re.sub(r'^.*?https?://', 'https://', target_link)
    
    user_download_dir = f"dl_{chat_id}_{user_id}_{int(time.time())}"
    os.makedirs(user_download_dir, exist_ok=True)

    if any(x in target_link for x in ["youtube.com", "youtu.be", "facebook.com", "instagram.com", "tiktok.com", "twitter.com"]):
        await status.edit_text(f"⚡ Social Media link detected! Extracting via YT-DLP...\n🔗 `{target_link[:50]}...`")
        output_template = os.path.join(user_download_dir, "%(title)s.%(ext)s")
        cmd = ["yt-dlp", "-f", "b[ext=mp4]/b", "-o", output_template, target_link]
    else:
        await status.edit_text(f"⏳ Downloading direct link via Aria2 (Anti-Protection Mode)...\n🔗 `{target_link[:50]}...`")
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        cmd = [
            "aria2c", 
            f"--dir={user_download_dir}", 
            f"--user-agent={user_agent}", 
            "--max-connection-per-server=16", 
            "--split=16",
            "--check-certificate=false",
            "--retry-wait=5",
            "--max-tries=5",
            target_link  # تمرير الرابط كمتغير نقي داخل مصفوفة الحماية لمنع كسر علامة &
        ]

    process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = await process.communicate()

    if not os.path.exists(user_download_dir) or not os.listdir(user_download_dir):
        error_msg = stderr.decode().strip() if stderr else "Network Block or Link Expired"
        await status.edit_text(f"❌ **Download Failed!**\n🔗 `{target_link[:60]}...`\n\nℹ️ **Reason:** {error_msg[:100]}")
        try: os.rmdir(user_download_dir)
        except: pass
        return False

    await status.edit_text("📤 Download finished successfully! Preparing to upload...")
    for root, dirs, files in os.walk(user_download_dir):
        for file in files:
            file_path = os.path.join(root, file)
            caption = f"🎬 **File Loaded:** `{file}`\n👤 **By:** {message.from_user.mention}"
            try:
                await split_and_upload_video(client, message, status, file_path, caption)
            except Exception as e:
                await message.reply_text(f"❌ Upload Error: `{str(e)}`")
            if os.path.exists(file_path): os.remove(file_path)

    try:
        import shutil
        shutil.rmtree(user_download_dir)
    except: pass
    return True

@app.on_message(filters.command("leechkmd"))
async def handle_leech_cmd(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    raw_text = ""

    if len(message.command) > 1:
        raw_text = message.text.split(None, 1)[1].strip()
    elif message.reply_to_message and message.reply_to_message.text:
        raw_text = message.reply_to_message.text.strip()

    if not raw_text:
        return await message.reply_text("⚠️ Error: Provide a link after command or reply to a text message containing links!")

    # تحسين استخراج الروابط لتشمل أي سطر يحتوي على بروتوكول الرابط حتى لو بدأ برموز خاطئة
    links = [line.strip() for line in raw_text.splitlines() if "http" in line]

    if not links:
        return await message.reply_text("❌ Error: No valid links found!")

    status = await message.reply_text("🔎 Analyzing and preparing progress bar...")
    total_links = len(links)

    if total_links == 1:
        await process_single_link(client, message, status, links[0], chat_id, user_id)
        await status.delete()
    else:
        await status.edit_text(f"📋 Found {total_links} links. Starting batch processing...")
        await asyncio.sleep(2)
        for index, link in enumerate(links, start=1):
            await status.edit_text(f"🔄 Processing link [{index}/{total_links}]...")
            try:
                await process_single_link(client, message, status, link, chat_id, user_id)
            except Exception as e:
                await message.reply_text(f"⚠️ Error on link {index}: `{str(e)}`")
        await status.edit_text(f"✅ All {total_links} links have been processed successfully!")

@app.on_message(filters.command("torrentkmd"))
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
            status = await message.reply_text("⏳ Downloading .torrent file...")
            target_input = await reply_msg.download()
            is_file = True
        elif reply_msg.text:
            target_input = reply_msg.text.strip()

    if not target_input:
        return await message.reply_text("⚠️ Error: Provide magnet link or reply to a `.torrent` file!")

    status = await message.reply_text("⏳ Connecting to torrent network...")
    user_download_dir = f"dl_{chat_id}_{user_id}_torrent"
    os.makedirs(user_download_dir, exist_ok=True)

    cmd = ["aria2c", f"--dir={user_download_dir}", "--seed-time=0", target_input]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await process.wait()

    if not os.path.exists(user_download_dir) or not os.listdir(user_download_dir):
        await status.edit_text("❌ Torrent download failed.")
        if is_file and os.path.exists(target_input): os.remove(target_input)
        return

    await status.edit_text("📤 Torrent downloaded! Uploading with progress bar...")
    for root, dirs, files in os.walk(user_download_dir):
        for file in files:
            file_path = os.path.join(root, file)
            caption = f"🎬 **Torrent File:** `{file}`"
            await split_and_upload_video(client, message, status, file_path, caption)
            if os.path.exists(file_path): os.remove(file_path)

    try:
        import shutil
        shutil.rmtree(user_download_dir)
        if is_file and os.path.exists(target_input): os.remove(target_input)
    except: pass
    await status.delete()

@app.on_message(filters.command("compresskmd"))
async def ask_for_quality(client, message: Message):
    if not message.reply_to_message or not (message.reply_to_message.video or message.reply_to_message.document):
        return await message.reply_text("⚠️ Error: Reply to a video!")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 240p", callback_data=f"q_240p_{message.reply_to_message.id}"), InlineKeyboardButton("🎬 360p", callback_data=f"q_360p_{message.reply_to_message.id}")],
        [InlineKeyboardButton("🎬 480p", callback_data=f"q_480p_{message.reply_to_message.id}"), InlineKeyboardButton("🎬 720p", callback_data=f"q_720p_{message.reply_to_message.id}")]
    ])
    await message.reply_text("⚙️ Choose compression quality:", reply_markup=keyboard)

@app.on_callback_query(filters.regex(r"^q_"))
async def start_compression_callback(client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split("_")
    quality, target_msg_id = data_parts[1], int(data_parts[2])
    chat_id, user_id = callback_query.message.chat.id, callback_query.from_user.id
    try: target_msg = await client.get_messages(chat_id, target_msg_id)
    except: return await callback_query.answer("❌ Video not found.")

    status = callback_query.message
    await status.edit_text("📥 Fetching original video...")
    start_time = time.time()
    input_file = await target_msg.download(progress=progress_callback, progress_args=(client, status, "Downloading original", start_time))
    
    output_file = f"compressed_{quality}_{chat_id}_{user_id}.mp4"
    await status.edit_text(f"⚡ Encoding to x265 ({quality})...")
    settings = QUALITY_SETTINGS[quality]
    cmd = ["ffmpeg", "-i", input_file, "-vf", f"scale={settings['scale']}", "-vcodec", "libx265", "-crf", settings['crf'], "-preset", "faster", "-acodec", "aac", "-b:a", settings['bitrate'], output_file, "-y"]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await process.wait()

    if os.path.exists(output_file):
        await split_and_upload_video(client, target_msg, status, output_file, f"🎬 Compressed to {quality}!")
        os.remove(output_file)
    else:
        await status.edit_text("❌ Compression failed.")
    if os.path.exists(input_file): os.remove(input_file)
    await status.delete()

@app.on_message(filters.photo)
async def save_photo_thumb(client, message: Message):
    thumb_path = f"thumb_{message.chat.id}_{message.from_user.id}.jpg"
    await message.download(file_name=thumb_path)
    user_thumbs[(message.chat.id, message.from_user.id)] = thumb_path
    await message.reply_text("🖼️ Thumbnail saved! Reply to a video with `/thumbkmd`.")

@app.on_message(filters.command("thumbkmd"))
async def apply_thumb_via_reply(client, message: Message):
    chat_id, user_id = message.chat.id, message.from_user.id
    thumb_path = user_thumbs.get((chat_id, user_id))
    if not thumb_path: return await message.reply_text("⚠️ Send a photo first!")
    if not message.reply_to_message: return await message.reply_text("⚠️ Reply to a video!")

    status = await message.reply_text("⏳ Applying thumbnail...")
    start_time = time.time()
    input_file = await message.reply_to_message.download(progress=progress_callback, progress_args=(client, status, "Downloading video", start_time))
    
    start_time = time.time()
    await message.reply_to_message.reply_video(video=input_file, thumb=thumb_path, caption="🖼️ Thumbnail Updated!", progress=progress_callback, progress_args=(client, status, "Uploading", start_time))
    if os.path.exists(thumb_path): os.remove(thumb_path)
    if os.path.exists(input_file): os.remove(input_file)
    user_thumbs[(chat_id, user_id)] = None
    await status.delete()

if __name__ == "__main__":
    print("🚀 Bot is running with Advanced Anti-Protection Link Downloader!")
    app.run()
