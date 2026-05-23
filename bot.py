# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os
import re
import sys
import json
import time
import asyncio
import requests
import subprocess
import shutil
from urllib.parse import urlparse, unquote

import core as helper
from utils import progress_bar
from vars import API_ID, API_HASH, BOT_TOKEN
from aiohttp import ClientSession
from pyromod import listen
from subprocess import getstatusoutput

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid

bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN)

# مخازن البيانات المؤقتة للأوامر
user_thumbs = {}
poster_pending_data = {}
MAX_TG_SIZE = 2000 * 1024 * 1024  # 2 جيجابايت

QUALITY_SETTINGS = {
    "240p": {"scale": "426:240", "crf": "30", "bitrate": "64k"},
    "360p": {"scale": "640:360", "crf": "28", "bitrate": "96k"},
    "480p": {"scale": "854:480", "crf": "26", "bitrate": "128k"},
    "720p": {"scale": "1280:720", "crf": "24", "bitrate": "192k"}
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# 📊 [العداد المتقدم الخارق]
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

# ✂️ [دالة التقسيم والرفع التلقائي]
async def split_and_upload_video(client, message, status, file_path, caption_text, thumb_path="no"):
    file_size = os.path.getsize(file_path)
    current_thumb = None if thumb_path == "no" else thumb_path
    
    if file_size <= MAX_TG_SIZE:
        start_time = time.time()
        await message.reply_video(video=file_path, thumb=current_thumb, caption=caption_text, progress=progress_callback, progress_args=(client, status, "Uploading video to Telegram", start_time))
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
            await message.reply_video(video=part_output, thumb=current_thumb, caption=f"{caption_text}\n🧩 **Part:** {i+1}/{num_parts}", progress=progress_callback, progress_args=(client, status, f"Uploading part {i+1}", start_time))
            os.remove(part_output)


@bot.on_message(filters.command(["start"]))
async def start(bot: Client, m: Message):
    if len(m.command) > 1 and m.chat.type == m.chat.type.PRIVATE:
        payload = m.command[1]
        if payload.startswith("getposter_"):
            poster_id = payload.replace("getposter_", "")
            data = poster_pending_data.get(poster_id)
            if data:
                poster_text = (
                    f"🎬 **فيلم:** {data['title']}\n\n"
                    f"📝 **قصة الفيلم:**\n{data['story']}\n\n"
                    f"📌 **تفاصيل الفيلم:**\n\n"
                    f"📁 **قسم الفيلم:** {data['section']}\n\n"
                    f"🎭 **نوع الفيلم:** {data['genre']}\n\n"
                    f"🎬 **المخرجين:** {data['director']}\n\n"
                    f"🌟 **بطولة:** {data['cast']}\n\n"
                    f"📅 **موعد الصدور:** {data['year']}\n\n"
                    f"🌍 **دولة الفيلم:** {data['country']}\n\n"
                    f"🎯 **التصنيف العمري:** {data['age_rating']}\n\n"
                    f"💿 **جودة الفيلم:** {data['quality']}\n\n"
                    f"🍿 **الإعلان الرسمي (البرومو):**\n🔗 {data['trailer']}\n\n"
                    f"🖥️ **مشاهدة الفيلم:**\n[الذهاب لصفحة المشاهدة]({data['watch_url']})"
                )
                try: await m.reply_photo(photo=data['image'], caption=poster_text)
                except Exception: await m.reply_text(poster_text, disable_web_page_preview=False)
                return
            else:
                return await m.reply_text("⚠️ عذراً، انتهت صلاحية بيانات هذا البوستر.")

    await m.reply_text(f"<b>Hello {m.from_user.mention} 👋\n\n I Am A Bot For Download Links From Your **.TXT** File And Then Upload That File On Telegram So Basically If You Want To Use Me First Send Me /upload Command And Then Follow Few Steps..\n\nUse /stop to stop any ongoing task.</b>")


@bot.on_message(filters.command("stop"))
async def restart_handler(_, m):
    await m.reply_text("**Stopped**🚦", True)
    os.execl(sys.executable, sys.executable, *sys.argv)


# 🎬 [أمر البوستر الداخلي الفوري والنظيف] 🎬
@bot.on_message(filters.command("poster"))
async def generate_poster_cmd(client, message: Message):
    user_id = message.from_user.id
    search_query = ""
    if len(message.command) > 1: search_query = message.text.split(None, 1)[1].strip()
    elif message.reply_to_message and message.reply_to_message.text: search_query = message.reply_to_message.text.strip()

    if not search_query: 
        return await message.reply_text("⚠️ اكتب اسم العمل بعد الأمر، مثال:\n`/poster حظ سعيد`")
    
    poster_id = f"{user_id}_{int(time.time())}"
    
    # القالب الداخلي الذكي الافتراضي
    poster_pending_data[poster_id] = {
        "title": search_query,
        "story": "يدور العمل في إطار مشوق ومثير حول تفاصيل غير متوقعة تغير مسار الأبطال تماماً.",
        "section": "أفلام عربية / أجنبية", "genre": "دراما • كوميدي • تشويق", "director": "مخرج العمل المعتمد",
        "cast": "نخبة من ألمع النجوم", "year": "2026", "country": "مصر / عالمي", "age_rating": "+12", "quality": "Full HD",
        "trailer": "http://www.youtube.com/watch?v=chiAM271c4M", "watch_url": "https://t.me/Series_World", "image": "https://elcinema.com/shared/images/placeholder_work.png"
    }

    # تخصيص خاص لفيلم حظ سعيد كمثال داخلي
    if "حظ سعيد" in search_query:
        poster_pending_data[poster_id].update({
            "title": "حظ سعيد",
            "story": "يدور الفيلم في إطار كوميدي سياسي حول شخصية الشاب (سعيد) الذي يكافح بكل الطرق من أجل إتمام زواجه من خطيبته (سماح)، ويقدم طلباً للحصول على شقة ضمن المشروع القومي للشباب. يذهب سعيد للحصول على الأوراق الرسمية المطلوبة من مبنى مجمع التحرير، ولكن تنفجر أحداث ثورة 25 يناير في نفس اليوم، ليتورط وسط الاحتجاجات والمظاهرات في مواقف كوميدية وسياسية تغير مسار حياته.",
            "section": "أفلام عربية", "genre": "كوميدي • دراما • سياسي", "director": "طارق عبدالمعطي", "cast": "أحمد عيد • مي كساب • أحمد صفوت • ضياء الميرغني • سامي مغاوري", "year": "2012"
        })

    bot_username = (await client.get_me()).username
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🎬 عرض بوستر وتفاصيل الفيلم (tDm)", url=f"https://t.me/{bot_username}?start=getposter_{poster_id}")]])
    await message.reply_text(f"🔍 تم العثور على معلومات: **{search_query}**\nاضغط أسفله للعرض في الخاص.", reply_markup=keyboard)


# ⚙️ [أوامر كومبريسور وضغط وتقليل حجم الفيديو]
@bot.on_message(filters.command(["compresskmd", "composer"]))
async def ask_for_quality(client, message: Message):
    if not message.reply_to_message or not (message.reply_to_message.video or message.reply_to_message.document):
        return await message.reply_text("⚠️ Error: Please reply to a video message to compress it!")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 240p", callback_data=f"q_240p_{message.reply_to_message.id}"), InlineKeyboardButton("🎬 360p", callback_data=f"q_360p_{message.reply_to_message.id}")],
        [InlineKeyboardButton("🎬 480p", callback_data=f"q_480p_{message.reply_to_message.id}"), InlineKeyboardButton("🎬 720p", callback_data=f"q_720p_{message.reply_to_message.id}")]
    ])
    await message.reply_text("⚙️ Choose compression quality:", reply_markup=keyboard)


@bot.on_callback_query(filters.regex(r"^q_"))
async def start_compression_callback(client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split("_")
    quality, target_msg_id = data_parts[1], int(data_parts[2])
    chat_id, user_id = callback_query.message.chat.id, callback_query.from_user.id
    try: target_msg = await client.get_messages(chat_id, target_msg_id)
    except: return

    status = callback_query.message
    await status.edit_text("📥 Fetching original video...")
    start_time = time.time()
    input_file = await target_msg.download(progress=progress_callback, progress_args=(client, status, "Downloading original", start_time))
    
    output_file = f"compressed_{quality}_{chat_id}_{user_id}.mp4"
    await status.edit_text(f"⚡ Encoding to x265 ({quality})...")
    settings = QUALITY_SETTINGS[quality]
    
    try:
        cmd = ["ffmpeg", "-i", input_file, "-vf", f"scale={settings['scale']}", "-vcodec", "libx265", "-crf", settings['crf'], "-preset", "faster", "-acodec", "aac", "-b:a", settings['bitrate'], output_file, "-y"]
        process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        await process.wait()
    except Exception: pass

    if os.path.exists(output_file):
        await split_and_upload_video(client, target_msg, status, output_file, f"🎬 Compressed to {quality}!")
        os.remove(output_file)
    else:
        await status.edit_text("❌ Compression failed.")
    if os.path.exists(input_file): os.remove(input_file)
    try: await status.delete()
    except: pass


# 🛠️ [تحميل الـ TXT الأساسي والمدرع بكسر الحظر وخطة الطوارئ]
@bot.on_message(filters.command(["upload"]))
async def upload(bot: Client, m: Message):
    editable = await m.reply_text('𝕤ᴇɴᴅ ᴛxᴛ ғɪλᴇ ⚡️')
    input: Message = await bot.listen(editable.chat.id)
    x = await input.download()
    await input.delete(True)

    try:
       with open(x, "r") as f:
           content = f.read()
       content = content.split("\n")
       links = []
       for i in content:
           i = i.strip()
           if "://" in i:
               links.append(i.split("://", 1))
       os.remove(x)
    except Exception as e:
           await m.reply_text(f"**Invalid file input.**\nError: `{str(e)}`")
           try: os.remove(x)
           except: pass
           return
    
    if not links:
        return await m.reply_text("❌ **الملف فارغ ولا يحتوي على روابط صحيحة!**")
   
    await editable.edit(f"**𝕋ᴏᴛᴀλ ʟɪɴᴋ𝕤 ғᴏᴜɴᴅ ᴀʀᴇ🔗🔗** **{len(links)}**\n\n**𝕊ᴇɴᴅ 𝔽ʀᴏᴍ ᴡʜᴇʀे ʏᴏُ ᴡᴀɴᴛ ᴛᴏ ᴅᴏᴡɴλᴏαᴅ ɪɴɪᴛɪαλ ɪ𝕤** **1**")
    input0: Message = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)

    await editable.edit("**Now Please Send Me Your Batch Name**")
    input1: Message = await bot.listen(editable.chat.id)
    raw_text0 = input1.text
    await input1.delete(True)
    
    await editable.edit("**𝔼ɴᴛᴇʀ ʀᴇ𝕤ᴏλᴜᴛɪᴏɴ📸**\n144,240,360,480,720,1080 please choose quality")
    input2: Message = await bot.listen(editable.chat.id)
    raw_text2 = input2.text
    await input2.delete(True)
    
    try:
        if raw_text2 == "144": res = "256x144"
        elif raw_text2 == "240": res = "426x240"
        elif raw_text2 == "360": res = "640x360"
        elif raw_text2 == "480": res = "854x480"
        elif raw_text2 == "720": res = "1280x720"
        elif raw_text2 == "1080": res = "1920x1080" 
        else: res = "UN"
    except Exception:
        res = "UN"

    await editable.edit("Now Enter A Caption to add caption on your uploaded file")
    input3: Message = await bot.listen(editable.chat.id)
    raw_text3 = input3.text
    await input3.delete(True)
    highlighter = f"️ ⁪⁬⁮⁮⁮"
    if raw_text3 == 'Robin':
        MR = highlighter 
    else:
        MR = raw_text3
   
    await editable.edit("Now send the Thumb url\nEg » `https://graph.org/file/ce1723991756e48c35aa1.jpg` \n Or if don't want thumbnail send = no")
    input6 = await bot.listen(editable.chat.id)
    raw_text6 = input6.text
    await input6.delete(True)
    await editable.delete()

    thumb = raw_text6.strip()
    if thumb.startswith("http://") or thumb.startswith("https://"):
        getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb = "no"

    try: count = 1 if len(links) == 1 else int(raw_text)
    except: count = 1

    try:
        for i in range(count - 1, len(links)):
            V = links[i][1].replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","")
            url = "https://" + V

            if "visionias" in url:
                async with ClientSession() as session:
                    async with session.get(url, headers={'User-Agent': USER_AGENT, 'Referer': 'http://www.visionias.in/'}) as resp:
                        text = await resp.text()
                        url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)

            elif 'videos.classplusapp' in url:
                try:
                    url = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers={'x-access-token': 'eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MzgzNjkyMTIsIm9yZ0lkIjoyNjA1LCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTcwODI3NzQyODkiLCJuYW1lIjoiQWNlIiwiZW1haWwiOm51bGwsImlzRmlyc3RMb2dpbiI6dHJ1ZSwiZGVmYXVsdExhbmd1YWdlIjpudWxsLCJjb3VudHJ5Q29kZSI6IklOIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJpYXQiOjE2NDMyODE4NzcsImV4cCI6MTY0Mzg4NjY3N30.hM33P2ai6ivdzxPPfm01LAd4JWv-vnrSxGXqvCirCSpUfhhofpeqyeHPxtstXwe0'}).json()['url']
                except: pass

            elif '/master.mpd' in url:
                id = url.split("/")[-2]
                url = "https://d26g5bnklkwsh4.cloudfront.net/" + id + "/master.m3u8"

            name1 = links[i][0].replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
            name = f'{str(count).zfill(3)}) {name1[:60]}'

            if "youtu" in url:
                ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
            else:
                ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"

            if "jw-prod" in url:
                cmd = f'yt-dlp --user-agent "{USER_AGENT}" --no-check-certificate -o "{name}.mp4" "{url}"'
            else:
                cmd = f'yt-dlp --user-agent "{USER_AGENT}" --no-check-certificate -f "{ytf}" "{url}" -o "{name}.mp4"'

            try:  
                cc = f'**[📽️] Vid_ID:** {str(count).zfill(3)}.** {name1}{MR}.mkv\n**Batch** » **{raw_text0}**'
                cc1 = f'**[📁] Pdf_ID:** {str(count).zfill(3)}. {name1}{MR}.pdf \n**Batch** » **{raw_text0}**'
                
                if "drive" in url:
                    try:
                        ka = await helper.download(url, name)
                        await bot.send_document(chat_id=m.chat.id, document=ka, caption=cc1)
                        count += 1
                        os.remove(ka)
                        time.sleep(1)
                    except FloodWait as e:
                        await asyncio.sleep(e.value)
                        continue
                
                elif ".pdf" in url:
                    try:
                        cmd_pdf = f'yt-dlp --user-agent "{USER_AGENT}" -o "{name}.pdf" "{url}" -R 25 --fragment-retries 25'
                        os.system(cmd_pdf)
                        await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                        count += 1
                        os.remove(f'{name}.pdf')
                    except FloodWait as e:
                        await asyncio.sleep(e.value)
                        continue
                else:
                    Show = f"**⥥ 🄳🄾🅆🄽🄻🄾🄰🄳🄸🄽🄶⬇️⬇️... »**\n\n**📝Name »** `{name}`\n❄`Quality » {raw_text2}`\n\n**🔗URL »** `{url}`"
                    prog = await m.reply_text(Show)
                    
                    res_file = await helper.download_video(url, cmd, name)
                    filename = res_file
                    
                    output_mp4 = f"{name}.mp4"
                    if not res_file or not os.path.exists(output_mp4) or os.path.getsize(output_mp4) < 1000:
                        await prog.edit(f"⚠️ خط الدفاع الأول فشل.. جاري سحب البث عبر محرك [FFmpeg Engine] لكسر الجدار الناري...")
                        cmd_ffmpeg = [
                            "ffmpeg", "-headers", f"User-Agent: {USER_AGENT}\r\n",
                            "-i", url, "-c", "copy", "-bsf:a", "aac_adtstoasc", output_mp4, "-y"
                        ]
                        process_ff = await asyncio.create_subprocess_exec(*cmd_ffmpeg, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        await process_ff.wait()
                        filename = output_mp4

                    if os.path.exists(filename) and os.path.getsize(filename) > 1000:
                        await prog.delete(True)
                        await split_and_upload_video(bot, m, prog, filename, cc, thumb)
                        count += 1
                        time.sleep(1)
                    else:
                        await prog.edit(f"❌ فشل تحميل هذا الرابط بجميع الطرق المتوفرة بسبب حظر جدار الحماية للموقع المستضيف.\n\n🔗 الرابط: `{url}`")
                        time.sleep(2)

            except Exception as e:
                await m.reply_text(f"**downloading Interupted **\n{str(e)}\n**Name** » {name}\n**Link** » `{url}`")
                continue

    except Exception as e:
        await m.reply_text(str(e))
    await m.reply_text("**Done Boss😎**")

bot.run()
