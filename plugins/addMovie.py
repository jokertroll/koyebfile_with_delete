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
        # Example command: /pu -tmdb 550 -f -https://filelink.mp4 -o f
        text = message.text

        # Split flags by " -" (space + dash) for easier parsing
        parts = text.split(" -")[1:]  # skip the command itself

        cmd_data = {
            "tmdbID": None,
            "fileLink": None,
            "position": "l",  # default last
        }

        for part in parts:
            part = part.strip()
            if part.startswith("tmdb"):
                cmd_data["tmdbID"] = int(part.replace("tmdb", "").strip())
            elif part.startswith("f") and part[1:].startswith("http"):
                # In case someone types "-f -https://..." without spaces
                cmd_data["fileLink"] = part[1:].strip()
            elif part.startswith("http"):
                cmd_data["fileLink"] = part.strip()
            elif part.startswith("o"):
                pos = part.replace("o", "").strip().lower()
                if pos in ["f", "l"]:
                    cmd_data["position"] = pos

        # Validate required fields
        if not cmd_data["tmdbID"] or not cmd_data["fileLink"]:
            await message.reply("❌ Invalid command! Make sure to include -tmdb and -fileLink.")
            return

        payload = {
            "tmdbID": cmd_data["tmdbID"],
            "fileLink": cmd_data["fileLink"],
            "position": cmd_data["position"],
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

            caption = f"✅ <b>{title}</b>\n\n<code>{overview}</code>\n\n🎬 Posted successfully!\nPosition: {cmd_data['position'].upper()}"
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

