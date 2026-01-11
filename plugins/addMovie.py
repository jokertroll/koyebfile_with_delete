import requests
from pyrogram import Client, filters
from config import ADMINS

API_BASE = "https://christian-erminia-abhisworkspace-82b29324.koyeb.app/api"
ADMIN_SECRET = "admin"  # must match backend .env


# --------------------------------------------------
# Command Parser
# --------------------------------------------------
def parse_command_flags(text: str):
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

        # -tmdb 12345
        if token == "-tmdb" and i + 1 < len(tokens):
            data["tmdbID"] = int(tokens[i + 1].lstrip("-"))
            i += 2
            continue

        # -f https://...
        if token == "-f" and i + 1 < len(tokens):
            link = tokens[i + 1]

            # ✅ FIX: handle "-https://..."
            if link.startswith("-http"):
                link = link[1:]

            data["fileLink"] = link
            i += 2
            continue

        # -o f | l
        if token == "-o" and i + 1 < len(tokens):
            pos = tokens[i + 1].lower()
            if pos in ("f", "l"):
                data["position"] = pos
            i += 2
            continue

        # -p (pin)
        if token == "-p":
            data["pinned"] = True
            i += 1
            continue

        # -u (unpin)
        if token == "-u":
            data["pinned"] = False
            i += 1
            continue

        i += 1

    return data


# --------------------------------------------------
# PUT / ADD MOVIE
# --------------------------------------------------
@Client.on_message(filters.command("put") & filters.user(ADMINS))
async def handle_put(client, message):
    try:
        cmd = parse_command_flags(message.text)

        if not cmd["tmdbID"] or not cmd["fileLink"]:
            await message.reply(
                "❌ <b>Invalid command</b>\n\n"
                "<code>/put -tmdb 550 -f https://file.mp4 [-o f|l] [-p|-u]</code>"
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

        res = requests.post(f"{API_BASE}/addMovie", json=payload, timeout=20)

        if res.status_code != 200:
            await message.reply(f"❌ Failed:\n<code>{res.text}</code>")
            return

        movie = res.json().get("movie", {})

        title = movie.get("title", "Unknown")
        overview = movie.get("overview", "No overview available.")
        poster = movie.get("poster_path")

        flags = []
        if cmd["position"] == "f":
            flags.append("📌 First")
        elif cmd["position"] == "l":
            flags.append("⬇️ Last")

        if cmd["pinned"]:
            flags.append("⭐ Pinned")
        elif cmd["pinned"] is False:
            flags.append("❌ Unpinned")

        flag_text = " | ".join(flags)

        caption = (
            f"✅ <b>{title}</b>\n\n"
            f"<code>{overview[:300]}</code>\n\n"
            f"🎬 Movie added successfully\n"
            f"{flag_text}"
        )

        if poster:
            await client.send_photo(
                chat_id=message.chat.id,
                photo=f"https://image.tmdb.org/t/p/w500{poster}",
                caption=caption
            )
        else:
            await message.reply(caption)

    except Exception as e:
        await message.reply(f"❌ Exception:\n<code>{str(e)}</code>")

@Client.on_message(filters.command("update") & filters.user(ADMINS))
async def handle_update(client, message):
    try:
        cmd = parse_command_flags(message.text)

        if not cmd["tmdbID"]:
            await message.reply(
                "❌ <b>Usage</b>\n"
                "<code>/update -tmdb 550 [-f link] [-o f|l] [-p|-u]</code>"
            )
            return

        payload = {
            "tmdbID": cmd["tmdbID"],
            "secret": ADMIN_SECRET
        }

        if cmd["fileLink"]:
            payload["fileLink"] = cmd["fileLink"]

        if cmd["position"]:
            payload["position"] = cmd["position"]

        if cmd["pinned"] is not None:
            payload["pinned"] = cmd["pinned"]

        res = requests.put(f"{API_BASE}/updateMovie", json=payload, timeout=20)

        if res.status_code != 200:
            await message.reply(f"❌ Update failed:\n<code>{res.text}</code>")
            return

        movie = res.json().get("movie", {})

        title = movie.get("title", "Unknown")
        poster = movie.get("poster_path")

        flags = []
        if cmd["position"] == "f":
            flags.append("📌 Moved to First")
        elif cmd["position"] == "l":
            flags.append("⬇️ Moved to Last")

        if cmd["pinned"] is True:
            flags.append("⭐ Pinned")
        elif cmd["pinned"] is False:
            flags.append("❌ Unpinned")

        caption = (
            f"✏️ <b>{title}</b>\n\n"
            f"🎬 Movie updated successfully\n"
            f"{' | '.join(flags)}"
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
        await message.reply(f"❌ Exception:\n<code>{str(e)}</code>")

@Client.on_message(filters.command("delete") & filters.user(ADMINS))
async def handle_delete(client, message):
    try:
        cmd = parse_command_flags(message.text)
        tmdb_id = cmd["tmdbID"]

        if not tmdb_id:
            await message.reply(
                "❌ <b>Usage</b>\n"
                "<code>/delete -tmdb 550</code>"
            )
            return

        payload = {
            "tmdbID": tmdb_id,
            "secret": ADMIN_SECRET
        }

        res = requests.delete(f"{API_BASE}/deleteMovie", json=payload, timeout=20)

        if res.status_code != 200:
            await message.reply(f"❌ Delete failed:\n<code>{res.text}</code>")
            return

        movie = res.json().get("movie", {})
        title = movie.get("title", "Unknown")
        poster = movie.get("poster_path")

        caption = f"🗑️ <b>{title}</b>\n\nMovie deleted successfully"

        if poster:
            await client.send_photo(
                message.chat.id,
                f"https://image.tmdb.org/t/p/w500{poster}",
                caption=caption
            )
        else:
            await message.reply(caption)

    except Exception as e:
        await message.reply(f"❌ Exception:\n<code>{str(e)}</code>")

