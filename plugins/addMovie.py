# addMovie.py
import requests
from pyrogram import Client, filters
from config import ADMINS

API_BASE = "https://christian-erminia-abhisworkspace-82b29324.koyeb.app/api"
ADMIN_SECRET = "admin"  # must match backend .env

def parse_command_flags(text):
    """
    Parse flags like -tmdb, -o, -https
    Returns: dict {tmdbID, fileLink, position}
    """
    parts = [p.strip() for p in text.split("-") if p.strip()]
    data = {"tmdbID": None, "fileLink": None, "position": None}

    for i, part in enumerate(parts):
        if part.startswith("tmdb"):
            data["tmdbID"] = int(part.replace("tmdb", ""))
        elif part == "o" and i + 1 < len(parts):
            # position flag
            pos = parts[i + 1].lower()
            if pos in ["f", "l"]:
                data["position"] = pos
        elif part.startswith("http"):
            data["fileLink"] = part

    return data

# ---------------- Add / Put ----------------
@Client.on_message(filters.command("put") & filters.user(ADMINS))
async def handle_put(client, message):
    try:
        cmd_data = parse_command_flags(message.text)
        tmdb_id = cmd_data["tmdbID"]
        file_link = cmd_data["fileLink"]
        position = cmd_data["position"]

        payload = {
            "tmdbID": tmdb_id,
            "fileLink": file_link,
            "position": position,  # include pinned/position
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
        cmd_data = parse_command_flags(message.text)
        tmdb_id = cmd_data["tmdbID"]
        file_link = cmd_data["fileLink"]
        position = cmd_data["position"]

        payload = {
            "tmdbID": tmdb_id,
            "fileLink": file_link,
            "position": position,
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

