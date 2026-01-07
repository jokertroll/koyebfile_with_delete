# addMovie.py
import requests
from pyrogram import Client, filters
from config import ADMINS

API_BASE = "https://christian-erminia-abhisworkspace-82b29324.koyeb.app/api"
ADMIN_SECRET = "admin"  # must match backend .env

# ---------------- Add / Put ----------------
@Client.on_message(filters.command("put") & filters.user(ADMINS))
async def handle_put(client, message):
    try:
        # /put -tmdb 550 -f -https://filelink.mp4
        parts = message.text.split("-")
        tmdb_id = int(parts[1].replace("tmdb", "").strip())
        file_link = parts[3].strip()

        payload = {
            "tmdbID": tmdb_id,
            "fileLink": file_link,
            "secret": ADMIN_SECRET
        }

        res = requests.post(f"{API_BASE}/addMovie", json=payload)

        if res.status_code == 200:
            data = res.json()
            movie = data.get("movie", {})
            title = movie.get("title", "Unknown")
            overview = movie.get("overview", "No overview available.")
            poster_path = movie.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

            caption = f"✅ <b>{title}</b>\n\n<code>{overview}</code>\n\n🎬 Posted successfully!"
            if poster_url:
                await client.send_photo(chat_id=message.chat.id, photo=poster_url, caption=caption)
            else:
                await message.reply(caption)
        else:
            await message.reply(f"❌ Failed to post:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred: <code>{str(e)}</code>")

# ---------------- Update ----------------
@Client.on_message(filters.command("update") & filters.user(ADMINS))
async def handle_update(client, message):
    try:
        # /update -tmdb 550 -f -https://newfilelink.mp4
        parts = message.text.split("-")
        tmdb_id = int(parts[1].replace("tmdb", "").strip())
        file_link = parts[3].strip()

        payload = {
            "tmdbID": tmdb_id,
            "fileLink": file_link,
            "secret": ADMIN_SECRET
        }

        res = requests.put(f"{API_BASE}/updateMovie", json=payload)

        if res.status_code == 200:
            data = res.json()
            movie = data.get("movie", {})
            title = movie.get("title", "Unknown")
            overview = movie.get("overview", "No overview available.")
            poster_path = movie.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

            caption = f"✏️ <b>{title}</b>\n\n<code>{overview}</code>\n\n🎬 Updated successfully!"
            if poster_url:
                await client.send_photo(chat_id=message.chat.id, photo=poster_url, caption=caption)
            else:
                await message.reply(caption)
        else:
            await message.reply(f"❌ Failed to update:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred: <code>{str(e)}</code>")

# ---------------- Delete ----------------
@Client.on_message(filters.command("delete") & filters.user(ADMINS))
async def handle_delete(client, message):
    try:
        # /delete -tmdb 550
        parts = message.text.split("-")
        tmdb_id = int(parts[1].replace("tmdb", "").strip())

        payload = {"tmdbID": tmdb_id, "secret": ADMIN_SECRET}
        res = requests.delete(f"{API_BASE}/deleteMovie", json=payload)

        if res.status_code == 200:
            await message.reply("🗑️ Movie deleted successfully!")
        else:
            await message.reply(f"❌ Failed to delete:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred: <code>{str(e)}</code>")
