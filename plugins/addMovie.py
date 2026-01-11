import requests
from pyrogram import Client, filters
from config import ADMINS

API_BASE = "https://christian-erminia-abhisworkspace-82b29324.koyeb.app/api"
ADMIN_SECRET = "admin"  # must match backend .env


# ---------------- Helper ----------------
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
            data["tmdbID"] = int(tokens[i + 1])
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


# ---------------- PUT (Add or Update) ----------------
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

        if cmd["position"]:
            payload["position"] = cmd["position"]

        if cmd["pinned"] is not None:
            payload["pinned"] = cmd["pinned"]

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

            flags = []
            if payload.get("position") == "f":
                flags.append("⬆ First")
            elif payload.get("position") == "l":
                flags.append("⬇ Last")

            if payload.get("pinned") is True:
                flags.append("⭐ Pinned")
            elif payload.get("pinned") is False:
                flags.append("📌 Unpinned")

            flag_text = " | ".join(flags)

            caption = (
                f"🎬 <b>{title}</b>\n\n"
                f"<code>{overview}</code>\n\n"
                f"{action} successfully\n"
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


# ---------------- UPDATE (file link or position) ----------------
@Client.on_message(filters.command("update") & filters.user(ADMINS))
async def handle_update(client, message):
    try:
        cmd = parse_command_flags(message.text)

        if not cmd["tmdbID"] or not cmd["fileLink"]:
            await message.reply(
                "❌ Usage:\n"
                "/update -tmdb 550 -f https://newfile.mp4 [-o f|l] [-p|-u]"
            )
            return

        payload = {
            "tmdbID": cmd["tmdbID"],
            "fileLink": cmd["fileLink"],
            "secret": ADMIN_SECRET
        }

        if cmd["position"]:
            payload["position"] = cmd["position"]

        if cmd["pinned"] is not None:
            payload["pinned"] = cmd["pinned"]

        res = requests.put(f"{API_BASE}/updateMovie", json=payload)

        if res.status_code == 200:
            movie = res.json().get("movie", {})
            title = movie.get("title", "Unknown")
            overview = movie.get("overview", "No overview available.")
            poster = movie.get("poster_path")

            flags = []
            if payload.get("position") == "f":
                flags.append("⬆ First")
            elif payload.get("position") == "l":
                flags.append("⬇ Last")

            if payload.get("pinned") is True:
                flags.append("⭐ Pinned")
            elif payload.get("pinned") is False:
                flags.append("📌 Unpinned")

            flag_text = " | ".join(flags)

            caption = (
                f"✏️ <b>{title}</b>\n\n"
                f"<code>{overview}</code>\n\n"
                f"Updated successfully\n"
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
            await message.reply(f"❌ Failed to update:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred: <code>{str(e)}</code>")


# ---------------- DELETE ----------------
@Client.on_message(filters.command("delete") & filters.user(ADMINS))
async def handle_delete(client, message):
    try:
        parts = message.text.split("-")
        tmdb_id = int(parts[1].replace("tmdb", "").strip())

        payload = {"tmdbID": tmdb_id, "secret": ADMIN_SECRET}
        res = requests.delete(f"{API_BASE}/deleteMovie", json=payload)

        if res.status_code == 200:
            movie = res.json().get("movie", {})
            title = movie.get("title", "Unknown")
            overview = movie.get("overview", "No overview available.")
            poster = movie.get("poster_path")

            caption = f"🗑️ <b>{title}</b>\n\n<code>{overview}</code>\n\nDeleted successfully!"
            if poster:
                await client.send_photo(
                    message.chat.id,
                    f"https://image.tmdb.org/t/p/w500{poster}",
                    caption=caption
                )
            else:
                await message.reply(caption)
        else:
            await message.reply(f"❌ Failed to delete:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred: <code>{str(e)}</code>")


# ---------------- PIN ----------------
@Client.on_message(filters.command("pin") & filters.user(ADMINS))
async def handle_pin(client, message):
    try:
        parts = message.text.split("-")
        tmdb_id = int(parts[1].replace("tmdb", "").strip())

        payload = {"tmdbID": tmdb_id, "pinned": True, "secret": ADMIN_SECRET}
        res = requests.put(f"{API_BASE}/updateMovie", json=payload)

        if res.status_code == 200:
            movie = res.json().get("movie", {})
            title = movie.get("title", "Unknown")
            overview = movie.get("overview", "No overview available.")
            poster = movie.get("poster_path")

            caption = f"⭐ <b>{title}</b>\n\n<code>{overview}</code>\n\nPinned successfully!"
            if poster:
                await client.send_photo(
                    message.chat.id,
                    f"https://image.tmdb.org/t/p/w500{poster}",
                    caption=caption
                )
            else:
                await message.reply(caption)
        else:
            await message.reply(f"❌ Failed to pin:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred: <code>{str(e)}</code>")


# ---------------- UNPIN ----------------
@Client.on_message(filters.command("unpin") & filters.user(ADMINS))
async def handle_unpin(client, message):
    try:
        parts = message.text.split("-")
        tmdb_id = int(parts[1].replace("tmdb", "").strip())

        payload = {"tmdbID": tmdb_id, "pinned": False, "secret": ADMIN_SECRET}
        res = requests.put(f"{API_BASE}/updateMovie", json=payload)

        if res.status_code == 200:
            movie = res.json().get("movie", {})
            title = movie.get("title", "Unknown")
            overview = movie.get("overview", "No overview available.")
            poster = movie.get("poster_path")

            caption = f"📌 <b>{title}</b>\n\n<code>{overview}</code>\n\nUnpinned successfully!"
            if poster:
                await client.send_photo(
                    message.chat.id,
                    f"https://image.tmdb.org/t/p/w500{poster}",
                    caption=caption
                )
            else:
                await message.reply(caption)
        else:
            await message.reply(f"❌ Failed to unpin:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred: <code>{str(e)}</code>")
