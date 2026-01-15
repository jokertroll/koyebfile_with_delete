import os
import subprocess
import uuid
import shutil
from pyrogram import Client, filters
from pyrogram.types import Message
from plugins.premium import is_premium  # Your existing premium logic

@Client.on_message(filters.command("insta") & filters.private)
async def insta_download(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply("❗ Send a valid Instagram post URL.\nUsage: `/insta <URL>`", quote=True)

    user_id = message.from_user.id
    if not is_premium(user_id):
        return await message.reply("🚫 This feature is only for premium users.", quote=True)

    url = message.command[1]
    temp_dir = f"temp_insta_{uuid.uuid4()}"
    os.makedirs(temp_dir, exist_ok=True)

    msg = await message.reply("📥 Downloading Instagram post...", quote=True)

    try:
        # Download all media
        cmd = [
            "yt-dlp",
            "--cookies", "plugins/cookies.txt",  # 👈 Required for Instagram now!
            "--no-playlist",
            "-o", os.path.join(temp_dir, "%(title)s.%(ext)s"),
            url
        ]
        subprocess.run(cmd, check=True)

        media_files = sorted(os.listdir(temp_dir))
        if not media_files:
            return await msg.edit("❌ Nothing was downloaded.")

        await msg.edit(f"📤 Uploading {len(media_files)} file(s)...")

        for media in media_files:
            full_path = os.path.join(temp_dir, media)
            if media.endswith((".mp4", ".webm")):
                await client.send_video(message.chat.id, video=full_path)
            elif media.endswith((".jpg", ".jpeg", ".png", ".webp")):
                await client.send_photo(message.chat.id, photo=full_path)

        await msg.edit("✅ All files sent!")

    except subprocess.CalledProcessError:
        await msg.edit("❌ Failed to download. The post may be private or invalid.")
    except Exception as e:
        await msg.edit(f"⚠️ Error: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
