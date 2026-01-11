import requests
from pyrogram import Client, filters
from config import ADMINS

API_BASE = "https://christian-erminia-abhisworkspace-82b29324.koyeb.app/api"
ADMIN_SECRET = "admin"  # must match backend .env


def parse_command_flags(text):
    tokens = text.split()

    data = {
        "tmdbID": None,
        "fileLink": None,
        "position": None,   # f | l
        "pinned": None      # True | False
    }

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token == "-tmdb" and i + 1 < len(tokens):
            data["tmdbID"] = int(tokens[i + 1].replace("-", ""))
            i += 2
            continue

        if token == "-f" and i + 1 < len(tokens):
            data["fileLink"] = tokens[i + 1].replace("-", "", 1)
            i += 2
            continue

        if token == "-o" and i + 1 < len(tokens):
            pos = tokens[i + 1].lower()
            if pos in ["f", "l"]:
                data["position"] = pos
            i += 2
            continue

        if token == "-p":
            data["pinned"] = True
            i += 1
            continue

        if token == "-u":
            data["pinned"] = False
            i += 1
            continue

        i += 1

    return data



# ---------------- Add / Put ----------------
@Client.on_message(filters.command("put") & filters.user(ADMINS))
async def handle_put(client, message):
    try:
        cmd = parse_command_flags(message.text)

        if not cmd["tmdbID"] or not cmd["fileLink"]:
            await message.reply(
                "❌ Usage:\n"
                "/put -tmdb 550 -f https://file.mp4 [-o f|l] [-p|-u]"
            )
            return

        payload = {
            "tmdbID": cmd["tmdbID"],
            "fileLink": cmd["fileLink"],
            "secret": ADMIN_SECRET
        }

        # optional flags
        if cmd["position"]:
            payload["position"] = cmd["position"]

        if cmd["pinned"] is not None:
            payload["pinned"] = cmd["pinned"]

        res = requests.post(f"{API_BASE}/addMovie", json=payload)

        if res.status_code == 200:
            movie = res.json().get("movie", {})
            title = movie.get("title", "Unknown")
            overview = movie.get("overview", "No overview available.")
            poster = movie.get("poster_path")

            flags = []
            if payload.get("position") == "f":
                flags.append("📌 First")
            if payload.get("pinned"):
                flags.append("⭐ Pinned")

            flag_text = " | ".join(flags)

            caption = (
                f"✅ <b>{title}</b>\n\n"
                f"<code>{overview}</code>\n\n"
                f"🎬 Added successfully\n"
                f"{flag_text}"
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

