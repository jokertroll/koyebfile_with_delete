import requests
import shlex
import asyncio
import httpx
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS

# ================= CONFIG =================
API_BASE = "https://christian-erminia-abhisworkspace-82b29324.koyeb.app/api/hdtv"
ADMIN_SECRET = "admin"

PAGE_SIZE = 10

# user_id -> { page, query, pending_delete_id }
USER_STATE = {}

# ================= HELPERS =================
# Adding insert at first or last logic
def parse_flags(text):
    tokens = shlex.split(text)
    data = {
        "tmdbID": None,
        "fileLink": None,
        "title": None,
        "overview": None,
        "poster": None,
        "pinned": None,
        "position": None   # 👈 ADD THIS
    }

    i = 0
    while i < len(tokens):
        t = tokens[i]

        if t == "-tmdb" and i + 1 < len(tokens):
            data["tmdbID"] = int(tokens[i + 1]); i += 2; continue

        if t == "-f" and i + 1 < len(tokens):
            data["fileLink"] = tokens[i + 1]; i += 2; continue

        if t == "-title" and i + 1 < len(tokens):
            data["title"] = tokens[i + 1]; i += 2; continue

        if t == "-overview" and i + 1 < len(tokens):
            data["overview"] = tokens[i + 1]; i += 2; continue

        if t == "-poster" and i + 1 < len(tokens):
            data["poster"] = tokens[i + 1]; i += 2; continue

        if t == "-p":
            data["pinned"] = True; i += 1; continue

        if t == "-u":
            data["pinned"] = False; i += 1; continue

        # 🔥 NEW: position flag
        if t == "-o" and i + 1 < len(tokens):
            if tokens[i + 1] in ("f", "l"):
                data["position"] = tokens[i + 1]
            i += 2; continue

        i += 1

    return data


# def parse_flags(text):
#     tokens = shlex.split(text)
#     data = {
#         "tmdbID": None,
#         "fileLink": None,
#         "title": None,
#         "overview": None,
#         "poster": None,
#         "pinned": None
#     }

#     i = 0
#     while i < len(tokens):
#         t = tokens[i]
#         if t == "-tmdb" and i + 1 < len(tokens):
#             data["tmdbID"] = int(tokens[i + 1]); i += 2; continue
#         if t == "-f" and i + 1 < len(tokens):
#             data["fileLink"] = tokens[i + 1]; i += 2; continue
#         if t == "-title" and i + 1 < len(tokens):
#             data["title"] = tokens[i + 1]; i += 2; continue
#         if t == "-overview" and i + 1 < len(tokens):
#             data["overview"] = tokens[i + 1]; i += 2; continue
#         if t == "-poster" and i + 1 < len(tokens):
#             data["poster"] = tokens[i + 1]; i += 2; continue
#         if t == "-p":
#             data["pinned"] = True; i += 1; continue
#         if t == "-u":
#             data["pinned"] = False; i += 1; continue
#         i += 1

#     return data

# async def send_movie_preview(client, chat_id, show, action_text):
#     title = show.get("title", "Unknown")
#     overview = show.get("overview", "No overview available.")
#     poster = show.get("poster_path")

#     caption = (
#         f"🎬 <b>{title}</b>\n\n"
#         f"{overview}\n\n"
#         f"{action_text}"
#     )
    
#     if poster:
#         await client.send_photo(
#             chat_id,
#             poster,
#             caption=caption,
#             parse_mode=ParseMode.HTML
#         )
#     else:
#         await client.send_message(
#             chat_id,
#             caption,
#             parse_mode=ParseMode.HTML
#         )

async def send_movie_preview(client, chat_id, show, action_text):
    title = show.get("title", "Unknown")
    overview = show.get("overview", "No overview available.")
    poster = show.get("poster_path")
    is_custom = show.get("isCustom", False)
    tmdb_id = show.get("tmdbID")

    caption = (
        f"🎬 <b>{title}</b>\n\n"
        f"{overview}\n\n"
        f"{action_text}"
    )

    # Check if the movie is custom or not
    if not is_custom and tmdb_id:
        # For non-custom movies, fetch the TMDB poster
        tmdb_poster_url = f"https://image.tmdb.org/t/p/w500{poster}"  # Append the image size (w500) for standard resolution
        try:
            # Check if the image exists by sending a HEAD request to TMDB image URL
            response = requests.head(tmdb_poster_url)
            if response.status_code == 200:
                poster = tmdb_poster_url  # Update poster with the valid TMDB image URL
            else:
                poster = None  # If the poster does not exist, handle it gracefully
        except requests.RequestException as e:
            print(f"Error fetching TMDB poster: {e}")
            poster = None

    # Send the movie preview with or without the poster
    if poster:
        # Send photo with caption
        await client.send_photo(
            chat_id,
            poster,
            caption=caption,
            parse_mode=ParseMode.HTML
        )
    else:
        # Send message without photo
        await client.send_message(
            chat_id,
            caption,
            parse_mode=ParseMode.HTML
        )


async def send_hdtv_page(client, chat_id, user_id, page=1, query=None):
    params = {"page": page, "limit": PAGE_SIZE}
    if query:
        params["q"] = query

    res = requests.get(API_BASE, params=params)
    if res.status_code != 200:
        await client.send_message(chat_id, "❌ Failed to fetch HDTV list")
        return

    data = res.json()
    shows = data["results"]
    total_pages = data["totalPages"]

    if not shows:
        await client.send_message(chat_id, "📭 No HDTV found")
        return

    USER_STATE[user_id] = {
        "page": page,
        "query": query,
        "items": shows
    }

    text = f"📺 <b>HDTV LIST</b> (Page {page}/{total_pages})\n\n"
    buttons = []

    for i, s in enumerate(shows, start=1):
        tag = "TMDB" if s.get("tmdbID") else "CUSTOM"
        text += f"{i}. <b>{s['title']}</b> ({tag})\n"
        buttons.append([
            InlineKeyboardButton(
                f"❌ Delete {i}",
                callback_data=f"hdtv_del:{s['_id']}"
            )
        ])

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅ Prev", callback_data=f"hdtv_page:{page-1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton("Next ➡", callback_data=f"hdtv_page:{page+1}"))

    if nav:
        buttons.append(nav)

    # Send message with buttons
    message = await client.send_message(
        chat_id,
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )

    # Wait for 30 seconds before removing the buttons
    await asyncio.sleep(30)

    # Edit the message to remove the buttons
    await client.edit_message_reply_markup(
        chat_id,
        message.id,  # Use the message id of the original message
        reply_markup=None  # Remove the inline buttons
    )


# async def send_hdtv_page(client, chat_id, user_id, page=1, query=None):
#     params = {"page": page, "limit": PAGE_SIZE}
#     if query:
#         params["q"] = query

#     res = requests.get(API_BASE, params=params)
#     if res.status_code != 200:
#         await client.send_message(chat_id, "❌ Failed to fetch HDTV list")
#         return

#     data = res.json()
#     shows = data["results"]
#     total_pages = data["totalPages"]

#     if not shows:
#         await client.send_message(chat_id, "📭 No HDTV found")
#         return

#     USER_STATE[user_id] = {
#         "page": page,
#         "query": query,
#         "items": shows
#     }

#     text = f"📺 <b>HDTV LIST</b> (Page {page}/{total_pages})\n\n"
#     buttons = []

#     for i, s in enumerate(shows, start=1):
#         tag = "TMDB" if s.get("tmdbID") else "CUSTOM"
#         text += f"{i}. <b>{s['title']}</b> ({tag})\n"
#         buttons.append([
#             InlineKeyboardButton(
#                 f"❌ Delete {i}",
#                 callback_data=f"hdtv_del:{s['_id']}"
#             )
#         ])

#     nav = []
#     if page > 1:
#         nav.append(InlineKeyboardButton("⬅ Prev", callback_data=f"hdtv_page:{page-1}"))
#     if page < total_pages:
#         nav.append(InlineKeyboardButton("Next ➡", callback_data=f"hdtv_page:{page+1}"))

#     if nav:
#         buttons.append(nav)

#     await client.send_message(
#         chat_id,
#         text,
#         reply_markup=InlineKeyboardMarkup(buttons),
#         parse_mode=ParseMode.HTML
#     )

async def hdtv_exists(title=None, tmdb_id=None):
    if not title and not tmdb_id:
        return False

    params = {}
    if title:
        params["q"] = title

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(API_BASE, params=params)
            res.raise_for_status()
            results = res.json().get("results", [])
    except httpx.RequestError as e:
        print(f"Network error checking HDTV existence: {e}")
        return False
    except Exception as e:
        print(f"Error checking HDTV existence: {e}")
        return False

    for show in results:
        if tmdb_id and show.get("tmdbID") == tmdb_id:
            return True
        # if title and show.get("title", "").lower() == title.lower():
        #     return True
        if title and show.get("title", "").strip().lower() == title.strip().lower():
            return True


    return False

# def hdtv_exists(title=None, tmdb_id=None):
#     params = {}
#     if title:
#         params["q"] = title

#     res = requests.get(API_BASE, params=params)
#     if res.status_code != 200:
#         return False

#     for s in res.json().get("results", []):
#         if tmdb_id and s.get("tmdbID") == tmdb_id:
#             return True
#         if title and s.get("title", "").lower() == title.lower():
#             return True

#     return False

# ================= COMMANDS =================

# ---------------- /help ----------------
@Client.on_message(filters.command("help") & filters.user(ADMINS))
async def handle_help(client, message):
    try:
        # Split message text to see if a specific command is requested
        tokens = message.text.split()
        command_requested = tokens[1].lower() if len(tokens) > 1 else None

        # Define commands and descriptions
        commands_info = {
            "put": "Add/update a movie by TMDB ID.\n Usage:\n\n /put -tmdb 550 -f <file> [-o f|l] [-p|-u]",
            "update":"update movie by TMDB ID.\n Usage:\n\n /update -tmdb 550 -f https://newfile.mp4 [-o f|l] [-p|-u]",
            "delete":"Delete a movie by TMDB ID.\n Usage:\n\n /delete -tmdb 550",
            "puts": "Add/update a show/movie.\n Usage:\n\n /puts -tmdb <id> -f <file> [-o f|l] [-p|-u]",
            "deleteseries": "Delete a series by TMDB ID.\n Usage:\n\n /deleteseries -tmdb 1399",
            "updateseries": "Update series info.\n Usage:\n\n /updateseries -tmdb 1399 -f <file> [-o f|l] [-p|-u]",
            "pin": "Pin a movie/show.\n Usage:\n\n /pin -tmdb <id>",
            "unpin": "Unpin a movie/show.\n Usage:\n\n /unpin -tmdb <id>",
            "addc": "Add carosuel.\n Usage:\n\n /addc -tmdb 550 -i https://image.com/img.jpg",
            "delc": "Delete carosuel.\n Usage:\n\n /delc -tmdb 550",
            "trend": "Add trending movie with is position.\n Usage:\n\n /trend -tmdb 550 -p 1",
            "deltrend": "Delete trending movie.\n Usage:\n\n /deltrend -tmdb <id>",
            "upcome": "Add upcoming movie.\n Usage:\n\n /upcome -tmdb 550 -p 1 -ott 2026-02-10",
            "delupcome": "Delete upcoming movie.\n Usage:\n\n /delupcome -tmdb <id>",
            "puthdtv": "Add/update a TMDB HDTV show.\n Usage:\n\n /puthdtv -tmdb 1399 -f <file> [-o f|l] [-p|-u]",
            "putcustomhdtv": "Add custom HDTV show.\n Usage:\n\n /putcustomhdtv -title <title> -overview <text> -poster <url> -f <file> [-o f|l] [-p|-u]",
            "updatehdtv": "Update HDTV show info.\n Usage:\n\n /updatehdtv -tmdb 1399 -f <file> [-o f|l] [-p|-u] OR /updatehdtv -title <title> -overview <text> -poster <url> -f <file>",
            "listhdtv": "Delete HDTV show.\n Usage:\n\n /listhdtv [search]\n\n",
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


@Client.on_message(filters.command("listhdtv") & filters.user(ADMINS))
async def listhdtv(client, message):
    query = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    await send_hdtv_page(
        client,
        message.chat.id,
        message.from_user.id,
        page=1,
        query=query
    )

# ================= CALLBACKS =================

@Client.on_callback_query(filters.regex("^hdtv_page:"))
async def paginate_hdtv(client, callback):
    page = int(callback.data.split(":")[1])
    state = USER_STATE.get(callback.from_user.id, {})
    await callback.message.delete()
    await send_hdtv_page(
        client,
        callback.message.chat.id,
        callback.from_user.id,
        page=page,
        query=state.get("query")
    )


@Client.on_callback_query(filters.regex("^hdtv_del:"))
async def ask_delete_confirm(client, callback):
    hdtv_id = callback.data.split(":")[1]
    USER_STATE.setdefault(callback.from_user.id, {})["pending_delete"] = hdtv_id

    await callback.message.reply(
        "⚠️ <b>Confirm Delete</b>\n\nType <code>YES</code> to confirm",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❎ Cancel", callback_data="hdtv_cancel")]
        ]),
        parse_mode=ParseMode.HTML
    )


@Client.on_callback_query(filters.regex("^hdtv_cancel$"))
async def cancel_delete(client, callback):
    USER_STATE.get(callback.from_user.id, {}).pop("pending_delete", None)
    await callback.message.edit("❎ Delete cancelled")


@Client.on_message(filters.regex("^YES$") & filters.user(ADMINS))
async def confirm_delete(client, message):
    state = USER_STATE.get(message.from_user.id)
    if not state or "pending_delete" not in state:
        await message.reply("❌ No delete action pending")
        return

    hdtv_id = state["pending_delete"]
    res = requests.delete(f"{API_BASE}/{hdtv_id}",json={"secret": ADMIN_SECRET})
    if res.status_code == 201:
        show = res.json()["show"]
        await send_movie_preview(
            client,
            message.chat.id,
            show,
            "✅ <b>🗑️ Deleted successfully</b>"
        )
    if res.status_code == 200:
        await message.reply("🗑️ Deleted successfully")
    else:
        await message.reply("❌ Delete failed")

    state.pop("pending_delete", None)

# ================= ADD / UPDATE =================

@Client.on_message(filters.command("puthdtv") & filters.user(ADMINS))
async def add_hdtv(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: `/addhdtv -tmdb 123 -f link` OR `-title 'Name' -f link`")

    flags = parse_flags(message.text)
    
    # 1. Base Payload
    payload = {
        "file_link": flags["fileLink"], # Matches your backend var
        "pinned": flags["pinned"] if flags["pinned"] is not None else False,
        "position": flags["position"] or "l"  # 'f' or 'l'
    }

    # 2. Logic to structure TMDB vs CUSTOM (Crucial for your backend)
    if flags["tmdbID"]:
        payload["tmdbID"] = flags["tmdbID"]
    elif flags["title"]:
        # Nesting data inside customData as required by your new backend service
        payload["customData"] = {
            "title": flags["title"],
            "overview": flags["overview"] or "No overview provided.",
            "poster_path": flags["poster"]
        }
    else:
        return await message.reply("❌ Error: Provide either `-tmdb` or `-title`.")

    headers = {"admin-secret": ADMIN_SECRET}

    try:
        # Using httpx for modern async request handling
        async with httpx.AsyncClient() as ac:
            response = await ac.post(API_BASE, json=payload, headers=headers)
        
        if response.status_code in (200, 201):
            new_show = response.json()
            await send_movie_preview(client, message.chat.id, new_show, "✅ Added Successfully!")
        else:
            # Captures the "already exists" error from your new backend logic
            error_data = response.json()
            error_msg = error_data.get('message', 'Unknown API Error')
            await message.reply(f"❌ Failed: {error_msg}")

    except Exception as e:
        await message.reply(f"❌ Connection Error: {str(e)}")

