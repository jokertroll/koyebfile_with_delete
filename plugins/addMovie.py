# botMovies.py
import requests
from pyrogram import Client, filters
from config import ADMINS

API_BASE = "https://christian-erminia-abhisworkspace-82b29324.koyeb.app/api"
ADMIN_SECRET = "admin"  # must match backend .env

# ---------------- Helper: Parse command flags ----------------
def parse_command_flags(text):
    """
    Parses commands like:
    /pu -tmdb 550 -f https://file.mp4 -o f -p
    Returns a dict with tmdbID, fileLink, position, pinned
    """
    parts = text.split(" -")[1:]  # skip command itself
    data = {"tmdbID": None, "fileLink": None, "position": None, "pinned": None}

    for part in parts:
        part = part.strip()
        if part.startswith("tmdb"):
            data["tmdbID"] = int(part.replace("tmdb", "").strip())
        elif part.startswith("f") or part.startswith("http"):
            # Accept both -f https:// or just -https://
            data["fileLink"] = part.replace("f", "").strip()
        elif part.startswith("o"):
            pos = part.replace("o", "").strip().lower()
            if pos in ["f", "l"]:
                data["position"] = pos
        elif part == "p":  # pin
            data["pinned"] = True
        elif part == "u":  # unpin
            data["pinned"] = False
    return data

# ---------------- Add / Put Command ----------------
@Client.on_message(filters.command(["pu", "put"]) & filters.user(ADMINS))
async def handle_put(client, message):
    try:
        cmd_data = parse_command_flags(message.text)
        tmdb_id = cmd_data["tmdbID"]
        file_link = cmd_data["fileLink"]
        position = cmd_data["position"]
        pinned = cmd_data["pinned"]

        if not tmdb_id:
            await message.reply("❌ Invalid command! Include -tmdb {tmdbID}.")
            return

        payload = {
            "tmdbID": tmdb_id,
            "secret": ADMIN_SECRET
        }
        if file_link:
            payload["fileLink"] = file_link
        if position:
            payload["position"] = position
        if pinned is not None:
            payload["pinned"] = pinned

        res = requests.post(f"{API_BASE}/addMovie", json=payload)

        if res.status_code == 200:
            data = res.json()
            movie = data.get("movie", {})
            title = movie.get("title", "Unknown")
            overview = movie.get("overview", "No overview available.")
            poster_path = movie.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

            pin_status = "📌 Pinned" if pinned else "❌ Unpinned" if pinned == False else ""
            caption = f"✅ <b>{title}</b> {pin_status}\n\n<code>{overview}</code>\n\n🎬 Posted successfully!"
            if poster_url:
                await client.send_photo(chat_id=message.chat.id, photo=poster_url, caption=caption)
            else:
                await message.reply(caption)
        else:
            await message.reply(f"❌ Failed to post:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred: <code>{str(e)}</code>")

# ---------------- Update Command ----------------
@Client.on_message(filters.command("update") & filters.user(ADMINS))
async def handle_update(client, message):
    try:
        cmd_data = parse_command_flags(message.text)
        tmdb_id = cmd_data["tmdbID"]
        file_link = cmd_data["fileLink"]
        position = cmd_data["position"]
        pinned = cmd_data["pinned"]

        if not tmdb_id:
            await message.reply("❌ Invalid command! Include -tmdb {tmdbID}.")
            return

        payload = {"tmdbID": tmdb_id, "secret": ADMIN_SECRET}
        if file_link:
            payload["fileLink"] = file_link
        if position:
            payload["position"] = position
        if pinned is not None:
            payload["pinned"] = pinned

        res = requests.put(f"{API_BASE}/updateMovie", json=payload)

        if res.status_code == 200:
            data = res.json()
            movie = data.get("movie", {})
            title = movie.get("title", "Unknown")
            poster_path = movie.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

            pin_status = "📌 Pinned" if pinned else "❌ Unpinned" if pinned == False else ""
            caption = f"✏️ <b>{title}</b> {pin_status}\n\n🎬 Updated successfully!"
            if poster_url:
                await client.send_photo(chat_id=message.chat.id, photo=poster_url, caption=caption)
            else:
                await message.reply(caption)
        else:
            await message.reply(f"❌ Failed to update:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred: <code>{str(e)}</code>")

# ---------------- Delete Command ----------------
@Client.on_message(filters.command("delete") & filters.user(ADMINS))
async def handle_delete(client, message):
    try:
        cmd_data = parse_command_flags(message.text)
        tmdb_id = cmd_data["tmdbID"]

        if not tmdb_id:
            await message.reply("❌ Invalid command! Include -tmdb {tmdbID}.")
            return

        payload = {"tmdbID": tmdb_id, "secret": ADMIN_SECRET}
        res = requests.delete(f"{API_BASE}/deleteMovie", json=payload)

        if res.status_code == 200:
            data = res.json()
            deleted_movie = data.get("movie") or data.get("series")  # depending on backend
            if deleted_movie:
                title = deleted_movie.get("title", "Unknown")
                await message.reply(f"🗑️ Movie <b>{title}</b> deleted successfully!")
            else:
                await message.reply("🗑️ Movie deleted successfully!")
        else:
            await message.reply(f"❌ Failed to delete:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred: <code>{str(e)}</code>")

