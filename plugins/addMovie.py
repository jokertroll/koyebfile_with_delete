import requests
import html
from pyrogram import Client, filters
from config import ADMINS

API_BASE = "https://christian-erminia-abhisworkspace-82b29324.koyeb.app/api"
ADMIN_SECRET = "admin"

MAX_OVERVIEW = 900


def safe(text):
    return html.escape(text or "")


# ---------------- ADD / PUT ----------------
@Client.on_message(filters.command("put") & filters.user(ADMINS))
async def handle_put(client, message):
    try:
        parts = message.text.split("-")
        tmdb_id = int(parts[1].replace("tmdb", "").strip())
        file_link = parts[3].strip()

        res = requests.post(
            f"{API_BASE}/addMovie",
            json={"tmdbID": tmdb_id, "fileLink": file_link, "secret": ADMIN_SECRET}
        )

        if res.status_code != 200:
            return await message.reply(
                f"❌ Failed to post:\n<code>{safe(res.text)}</code>"
            )

        movie = res.json().get("movie", {})
        title = safe(movie.get("title", "Unknown"))
        overview = safe(movie.get("overview", ""))[:MAX_OVERVIEW]
        poster = movie.get("poster_path")

        caption = (
            f"✅ <b>{title}</b>\n\n"
            f"<code>{overview}</code>\n\n"
            f"🎬 Posted successfully!"
        )

        if poster:
            await client.send_photo(
                message.chat.id,
                f"https://image.tmdb.org/t/p/w500{poster}",
                caption=caption
            )
        else:
            await message.reply(caption)

    except Exception as e:
        await message.reply(f"❌ Exception occurred:\n<code>{safe(str(e))}</code>")


# ---------------- UPDATE ----------------
@Client.on_message(filters.command("update") & filters.user(ADMINS))
async def handle_update(client, message):
    try:
        parts = message.text.split("-")
        tmdb_id = int(parts[1].replace("tmdb", "").strip())
        file_link = parts[3].strip()

        res = requests.put(
            f"{API_BASE}/updateMovie",
            json={"tmdbID": tmdb_id, "fileLink": file_link, "secret": ADMIN_SECRET}
        )

        if res.status_code != 200:
            return await message.reply(
                f"❌ Failed to update:\n<code>{safe(res.text)}</code>"
            )

        movie = res.json().get("movie", {})
        title = safe(movie.get("title", "Unknown"))
        overview = safe(movie.get("overview", ""))[:MAX_OVERVIEW]
        poster = movie.get("poster_path")

        caption = (
            f"✏️ <b>{title}</b>\n\n"
            f"<code>{overview}</code>\n\n"
            f"🎬 Updated successfully!"
        )

        if poster:
            await client.send_photo(
                message.chat.id,
                f"https://image.tmdb.org/t/p/w500{poster}",
                caption=caption
            )
        else:
            await message.reply(caption)

    except Exception as e:
        await message.reply(f"❌ Exception occurred:\n<code>{safe(str(e))}</code>")


# ---------------- DELETE ----------------
@Client.on_message(filters.command("delete") & filters.user(ADMINS))
async def handle_delete(client, message):
    try:
        parts = message.text.split("-")
        tmdb_id = int(parts[1].replace("tmdb", "").strip())

        res = requests.delete(
            f"{API_BASE}/deleteMovie",
            json={"tmdbID": tmdb_id, "secret": ADMIN_SECRET}
        )

        if res.status_code != 200:
            return await message.reply(
                f"❌ Failed to delete:\n<code>{safe(res.text)}</code>"
            )

        movie = res.json().get("movie", {})
        title = safe(movie.get("title", "Unknown"))
        poster = movie.get("poster_path")

        caption = f"🗑️ <b>{title}</b>\n\nDeleted successfully."

        if poster:
            await client.send_photo(
                message.chat.id,
                f"https://image.tmdb.org/t/p/w500{poster}",
                caption=caption
            )
        else:
            await message.reply(caption)

    except Exception as e:
        await message.reply(f"❌ Exception occurred:\n<code>{safe(str(e))}</code>")
