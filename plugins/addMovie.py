# AddMovieBot.py
import requests
from pyrogram import Client, filters
from config import ADMINS

API_BASE = "https://christian-erminia-abhisworkspace-82b29324.koyeb.app/api"
ADMIN_SECRET = "admin"  # must match backend .env


# ---------------- UTILITY ----------------
def parse_put_flags(text):
    """
    Parse /put command flags
    Example: /put -tmdb 550 -f https://file.mp4 -o f
    """
    tokens = text.split()
    data = {"tmdbID": None, "fileLink": None, "position": None}

    i = 0
    while i < len(tokens):
        token = tokens[i].lower()
        if token == "-tmdb" and i + 1 < len(tokens):
            try:
                data["tmdbID"] = int(tokens[i + 1])
            except:
                data["tmdbID"] = None
            i += 2
            continue
        if token == "-f" and i + 1 < len(tokens):
            data["fileLink"] = tokens[i + 1]
            i += 2
            continue
        if token == "-o" and i + 1 < len(tokens):
            pos = tokens[i + 1].lower()
            if pos in ("f", "l"):
                data["position"] = pos
            i += 2
            continue
        i += 1

    return data


# ---------------- /put ADD OR UPDATE ----------------
@Client.on_message(filters.command("put") & filters.user(ADMINS))
async def handle_put(client, message):
    try:
        cmd = parse_put_flags(message.text)

        if not cmd["tmdbID"] or not cmd["fileLink"]:
            await message.reply(
                "❌ Usage:\n"
                "/put -tmdb 550 -f https://file.mp4 [-o f|l]"
            )
            return

        payload = {
            "tmdbID": cmd["tmdbID"],
            "fileLink": cmd["fileLink"],
            "secret": ADMIN_SECRET
        }

        if cmd["position"]:
            payload["position"] = cmd["position"]
        else:
            payload["position"] = "l"  # default last

        # 1️⃣ Try ADD
        res = requests.post(f"{API_BASE}/addMovie", json=payload)
        action = "Added"

        # 2️⃣ If exists → UPDATE
        if res.status_code != 200 and "already exists" in res.text.lower():
            res = requests.put(f"{API_BASE}/updateMovie", json=payload)
            action = "Updated"

        if res.status_code == 200:
            movie = res.json().get("movie", {})
            title = movie.get("title", "Unknown")
            overview = movie.get("overview", "No overview available.")
            poster = movie.get("poster_path")

            pos_flag = "⬆ First" if payload["position"] == "f" else "⬇ Last"

            caption = (
                f"✅ <b>{title}</b>\n\n"
                f"<code>{overview}</code>\n\n"
                f"🎬 {action} successfully\n"
                f"{pos_flag}"
            )

            if poster:
                await client.send_photo(
                    message.chat.id,
                    f"https://image.tmdb.org/t/p/w500{poster}",
                    caption=caption
                )
            else:
                await message.reply(caption)
        else:
            await message.reply(f"❌ Failed:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception:\n<code>{str(e)}</code>")


# ---------------- /update (just change file link) ----------------
@Client.on_message(filters.command("update") & filters.user(ADMINS))
async def handle_update(client, message):
    try:
        # /update -tmdb 550 -f https://newfile.mp4
        parts = message.text.split()
        if "-tmdb" not in parts or "-f" not in parts:
            await message.reply("❌ Usage: /update -tmdb 550 -f https://file.mp4")
            return

        tmdb_id = int(parts[parts.index("-tmdb") + 1])
        file_link = parts[parts.index("-f") + 1]

        payload = {"tmdbID": tmdb_id, "fileLink": file_link, "secret": ADMIN_SECRET}

        res = requests.put(f"{API_BASE}/updateMovie", json=payload)

        if res.status_code == 200:
            movie = res.json().get("movie", {})
            title = movie.get("title", "Unknown")
            overview = movie.get("overview", "No overview available.")
            poster_path = movie.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

            caption = f"✏️ <b>{title}</b>\n\n<code>{overview}</code>\n\n🎬 Updated successfully!"
            if poster_url:
                await client.send_photo(message.chat.id, poster_url, caption=caption)
            else:
                await message.reply(caption)
        else:
            await message.reply(f"❌ Failed to update:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred: <code>{str(e)}</code>")


# ---------------- /delete ----------------
@Client.on_message(filters.command("delete") & filters.user(ADMINS))
async def handle_delete(client, message):
    try:
        # /delete -tmdb 550
        parts = message.text.split()
        if "-tmdb" not in parts:
            await message.reply("❌ Usage: /delete -tmdb 550")
            return

        tmdb_id = int(parts[parts.index("-tmdb") + 1])

        payload = {"tmdbID": tmdb_id, "secret": ADMIN_SECRET}
        res = requests.delete(f"{API_BASE}/deleteMovie", json=payload)

        if res.status_code == 200:
            await message.reply("🗑️ Movie deleted successfully!")
        else:
            await message.reply(f"❌ Failed to delete:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred: <code>{str(e)}</code>")


# ---------------- /pin ----------------
@Client.on_message(filters.command("pin") & filters.user(ADMINS))
async def handle_pin(client, message):
    try:
        # /pin -tmdb 550
        parts = message.text.split()
        if "-tmdb" not in parts:
            await message.reply("❌ Usage: /pin -tmdb 550")
            return

        tmdb_id = int(parts[parts.index("-tmdb") + 1])
        payload = {"tmdbID": tmdb_id, "pinned": True, "secret": ADMIN_SECRET}

        res = requests.put(f"{API_BASE}/updateMovie", json=payload)

        if res.status_code == 200:
            await message.reply("⭐ Movie pinned successfully!")
        else:
            await message.reply(f"❌ Failed to pin:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred: <code>{str(e)}</code>")


# ---------------- /unpin ----------------
@Client.on_message(filters.command("unpin") & filters.user(ADMINS))
async def handle_unpin(client, message):
    try:
        # /unpin -tmdb 550
        parts = message.text.split()
        if "-tmdb" not in parts:
            await message.reply("❌ Usage: /unpin -tmdb 550")
            return

        tmdb_id = int(parts[parts.index("-tmdb") + 1])
        payload = {"tmdbID": tmdb_id, "pinned": False, "secret": ADMIN_SECRET}

        res = requests.put(f"{API_BASE}/updateMovie", json=payload)

        if res.status_code == 200:
            await message.reply("📌 Movie unpinned successfully!")
        else:
            await message.reply(f"❌ Failed to unpin:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred: <code>{str(e)}</code>")
