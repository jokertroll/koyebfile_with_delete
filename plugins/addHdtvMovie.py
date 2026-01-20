# plugins\addHdtvMovie.py
import requests
import shlex
from pyrogram.enums import ParseMode
from pyrogram import Client, filters
from config import ADMINS

API_BASE = "https://christian-erminia-abhisworkspace-82b29324.koyeb.app/api"
ADMIN_SECRET = "admin"  # must match backend .env

# commands
# /puthdtv -tmdb 1399 -f https://file.mp4 -o f -p
# /putcustomhdtv -title "My Show" -overview "Amazing story" -poster https://img.jpg -f https://file.mp4 -o l
# /updatehdtv -tmdb 1399 -f https://newfile.mp4 -o l -u
# /updatehdtv -title "My Show" -overview "New text" -poster https://new.jpg -f https://file.mp4
# /deletehdtv -tmdb 1399


# ---------------- Helper ----------------
def parse_hdtv_flags(text):
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

# ---------------- /help ----------------
@Client.on_message(filters.command("help") & filters.user(ADMINS))
async def handle_help(client, message):
    try:
        # Split message text to see if a specific command is requested
        tokens = message.text.split()
        command_requested = tokens[1].lower() if len(tokens) > 1 else None

        # Define commands and descriptions
        commands_info = {
            "put": "Add/update a movie by TMDB ID. Usage: /put -tmdb 550 -f <file> [-o f|l] [-p|-u]",
            "update":"update movie by TMDB ID.Usage: /update -tmdb 550 -f https://newfile.mp4 [-o f|l] [-p|-u]",
            "delete":"Delete a movie by TMDB ID. Usage /delete -tmdb 550",
            "puts": "Add/update a show/movie. Usage: /puts -tmdb <id> -f <file> [-o f|l] [-p|-u]",
            "deleteseries": "Delete a series by TMDB ID. Usage: /deleteseries -tmdb 1399",
            "updateseries": "Update series info. Usage: /updateseries -tmdb 1399 -f <file> [-o f|l] [-p|-u]",
            "pin": "Pin a movie/show. Usage: /pin -tmdb <id>",
            "unpin": "Unpin a movie/show. Usage: /unpin -tmdb <id>",
            "addc": "Add carosuel. Usage: /addc -tmdb 550 -i https://image.com/img.jpg",
            "delc": "Delete carosuel. Usage:/delc -tmdb 550",
            "trend": "Add trending movie with is position. Usage:/trend -tmdb 550 -p 1",
            "deltrend": "Delete trending movie. Usage: /deltrend -tmdb <id>",
            "upcome": "Add upcoming movie. Usage: /upcome -tmdb 550 -p 1 -ott 2026-02-10",
            "delupcome": "Delete upcoming movie. Usage: /delupcome -tmdb <id>",
            "puthdtv": "Add/update a TMDB HDTV show. Usage: /puthdtv -tmdb 1399 -f <file> [-o f|l] [-p|-u]",
            "putcustomhdtv": "Add custom HDTV show. Usage: /putcustomhdtv -title <title> -overview <text> -poster <url> -f <file> [-o f|l] [-p|-u]",
            "updatehdtv": "Update HDTV show info. Usage: /updatehdtv -tmdb 1399 -f <file> [-o f|l] [-p|-u] OR /updatehdtv -title <title> -overview <text> -poster <url> -f <file>",
            "deletehdtv": "Delete HDTV show. Usage: /deletehdtv -tmdb 1399",
        }

        if command_requested:
            # Show detailed info for requested command
            info = commands_info.get(command_requested)
            if info:
                await message.reply(f"ℹ️ <b>/{command_requested}</b>\n\n{info}")
            else:
                await message.reply(f"❌ Unknown command: {command_requested}")
        else:
            # Show all commands
            command_list = "\n".join([f"/{cmd}" for cmd in commands_info.keys()])
            await message.reply(
                f"📚 <b>Available Commands:</b>\n{command_list}\n\n"
                "Type /help <command> to see usage details for a specific command."
            )

    except Exception as e:
        await message.reply(f"❌ Exception:\n<code>{str(e)}</code>")

# ---------------- /put ADD OR UPDATE HDTV ----------------
@Client.on_message(filters.command("puthdtv") & filters.user(ADMINS))
async def handle_put_hdtv(client, message):
    try:
        cmd = parse_hdtv_flags(message.text)

        if not cmd["tmdbID"] or not cmd["fileLink"]:
            await message.reply(
                "❌ Usage:\n"
                "/puthdtv -tmdb 1399 -f https://file.mp4 [-o f|l] [-p|-u]"
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
        res = requests.post(f"{API_BASE}/addHdtv", json=payload)
        action = "Added"

        # 2️⃣ If exists → UPDATE
        if res.status_code != 200 and "already exists" in res.text.lower():
            res = requests.put(f"{API_BASE}/updateHdtv", json=payload)
            action = "Updated"

        if res.status_code == 200:
            show = res.json().get("show", {})
            title = show.get("title") or show.get("name", "Unknown")
            overview = show.get("overview", "No overview available.")
            poster = show.get("poster_path")

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
                f"📺 <b>{title}</b>\n\n"
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


# ---------------- /putcustomhdtv ----------------

@Client.on_message(filters.command("putcustomhdtv") & filters.user(ADMINS))
async def handle_put_custom_hdtv(client, message):
    try:
        tokens = shlex.split(message.text)
        payload = {"secret": ADMIN_SECRET, "customData": {}}

        if "-title" not in tokens:
            await message.reply("❌ Must provide -title")
            return
        payload["customData"]["title"] = tokens[tokens.index("-title") + 1]

        if "-overview" in tokens:
            payload["customData"]["overview"] = tokens[tokens.index("-overview") + 1]

        if "-poster" in tokens:
            payload["customData"]["poster_path"] = tokens[tokens.index("-poster") + 1]

        if "-f" not in tokens:
            await message.reply("❌ Must provide -f file link")
            return
        payload["fileLink"] = tokens[tokens.index("-f") + 1]

        if "-o" in tokens:
            pos = tokens[tokens.index("-o") + 1].lower()
            if pos in ("f", "l"):
                payload["position"] = pos

        if "-p" in tokens:
            payload["pinned"] = True
        if "-u" in tokens:
            payload["pinned"] = False

        res = requests.post(f"{API_BASE}/addHdtv", json=payload)

        if res.status_code == 200:
            show = res.json()["show"]

            caption = (
                f"📺 <b>{show['title']}</b>\n\n"
                f"{show.get('overview','No overview')}\n\n"
                f"Added successfully"
            )

            if show.get("poster_path"):
                await client.send_photo(
                    message.chat.id,
                    show["poster_path"],
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
            else:
                await message.reply(caption, parse_mode=ParseMode.HTML)

        else:
            await message.reply(f"❌ Failed:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception:\n<code>{str(e)}</code>")

# ---------------- /updatehdtv ----------------
@Client.on_message(filters.command("updatehdtv") & filters.user(ADMINS))
async def handle_update_hdtv(client, message):
    try:
        cmd = parse_hdtv_flags(message.text)

        if not cmd["tmdbID"] and "-title" not in message.text:
            await message.reply("❌ Usage:\n/updatehdtv -tmdb 1399 -f https://file.mp4 [-o f|l] [-p|-u]")
            return

        payload = {"secret": ADMIN_SECRET}
        if cmd["tmdbID"]:
            payload["tmdbID"] = cmd["tmdbID"]
        if cmd["fileLink"]:
            payload["fileLink"] = cmd["fileLink"]
        if cmd["position"]:
            payload["position"] = cmd["position"]
        if cmd["pinned"] is not None:
            payload["pinned"] = cmd["pinned"]

        # Custom fields
        if "-title" in message.text:
            tokens = message.text.split()
            payload["customData"] = {}
            idx = tokens.index("-title")
            payload["customData"]["title"] = tokens[idx + 1]
            if "-overview" in tokens:
                idx2 = tokens.index("-overview")
                payload["customData"]["overview"] = tokens[idx2 + 1]
            if "-poster" in tokens:
                idx3 = tokens.index("-poster")
                payload["customData"]["poster_path"] = tokens[idx3 + 1]

        res = requests.put(f"{API_BASE}/updateHdtv", json=payload)

        if res.status_code == 200:
            show = res.json().get("show", {})
            title = show.get("title") or show.get("name", "Unknown")
            overview = show.get("overview", "No overview available.")
            poster = show.get("poster_path")

            caption = f"✏️ <b>{title}</b>\n\n<code>{overview}</code>\n\nUpdated successfully"
            if poster:
                await client.send_photo(message.chat.id, poster, caption=caption)
            else:
                await message.reply(caption)
        else:
            await message.reply(f"❌ Failed:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception:\n<code>{str(e)}</code>")

# ---------------- /deletehdtv ----------------
@Client.on_message(filters.command("deletehdtv") & filters.user(ADMINS))
async def handle_delete_hdtv(client, message):
    try:
        tokens = message.text.split()
        if "-tmdb" not in tokens:
            await message.reply("❌ Usage:\n/deletehdtv -tmdb 1399")
            return
        tmdb_id = int(tokens[tokens.index("-tmdb") + 1])

        payload = {"tmdbID": tmdb_id, "secret": ADMIN_SECRET}
        res = requests.delete(f"{API_BASE}/deleteHdtv", json=payload)

        if res.status_code == 200:
            show = res.json().get("show", {})
            title = show.get("title") or show.get("name", "Unknown")
            overview = show.get("overview", "No overview available.")
            poster = show.get("poster_path")

            caption = f"🗑️ <b>{title}</b>\n\n<code>{overview}</code>\n\nDeleted successfully!"
            if poster:
                await client.send_photo(message.chat.id, poster, caption=caption)
            else:
                await message.reply(caption)
        else:
            await message.reply(f"❌ Failed:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception:\n<code>{str(e)}</code>")
