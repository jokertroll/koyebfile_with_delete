import requests
import html
from pyrogram import Client, filters
from config import ADMINS

API_BASE = "https://christian-erminia-abhisworkspace-82b29324.koyeb.app/api"
ADMIN_SECRET = "admin"

# ---------------- Add / Put ----------------
@Client.on_message(filters.command("put") & filters.user(ADMINS))
async def handle_put(client, message):
    try:
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
            title = html.escape(movie.get("title", "Unknown"))
            overview = html.escape(movie.get("overview", "No overview available."))
            overview = overview[:1000]  # truncate to avoid Telegram limits
            poster_path = movie.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

            caption = f"✅ <b>{title}</b>\n\n<code>{overview}</code>\n\n🎬 Posted successfully!"
            if poster_url:
                await client.send_photo(chat_id=message.chat.id, photo=poster_url, caption=caption)
            else:
                await message.reply(caption)
        else:
            await message.reply(f"❌ Failed to post:\n<code>{html.escape(res.text)}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred: <code>{html.escape(str(e))}</code>")

# ---------------- Update ----------------
@Client.on_message(filters.command("update") & filters.user(ADMINS))
async def handle_update(client, message):
    try:
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
            title = html.escape(movie.get("title", "Unknown"))
            overview = html.escape(movie.get("overview", "No overview available."))
            overview = overview[:1000]
            poster_path = movie.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

            caption = f"✏️ <b>{title}</b>\n\n<code>{overview}</code>\n\n🎬 Updated successfully!"
            if poster_url:
                await client.send_photo(chat_id=message.chat.id, photo=poster_url, caption=caption)
            else:
                await message.reply(caption)
        else:
            await message.reply(f"❌ Failed to update:\n<code>{html.escape(res.text)}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred: <code>{html.escape(str(e))}</code>")

# ---------------- Delete ----------------
@Client.on_message(filters.command("delete") & filters.user(ADMINS))
async def handle_delete(client, message):
    try:
        parts = message.text.split("-")
        tmdb_id = int(parts[1].replace("tmdb", "").strip())

        payload = {"tmdbID": tmdb_id, "secret": ADMIN_SECRET}
        res = requests.delete(f"{API_BASE}/deleteMovie", json=payload)

        if res.status_code == 200:
            await message.reply("🗑️ Movie deleted successfully!")
        else:
            await message.reply(f"❌ Failed to delete:\n{html.escape(res.text)}")

    except Exception as e:
        await message.reply(f"❌ Exception occurred: <code>{html.escape(str(e))}</code>")
