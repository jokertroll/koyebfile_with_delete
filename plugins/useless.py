from bot import Bot
from pyrogram.types import Message
from pyrogram import filters
from config import ADMINS, BOT_STATS_TEXT, USER_REPLY_TEXT
from datetime import datetime
from helper_func import get_readable_time

from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

@Bot.on_message(filters.command('join') & filters.private)
async def followus(bot: Bot, message: Message):
    reply_markup=InlineKeyboardMarkup(
                        [
                         [
                          InlineKeyboardButton('🎬 𝑴𝒐𝒗𝒊𝒆𝒔 𝒈𝒓𝒐𝒖𝒑', url="t.me/+BtIY_7IaFKgxYzQ1"),
                          InlineKeyboardButton('🥹 𝑼𝒑𝒅𝒂𝒕𝒆𝒔 𝑪𝒉𝒂𝒏𝒏𝒆𝒍', url="t.me/MoviezAddaKA")
                       ],[
                          InlineKeyboardButton("🧑‍💻 𝑩𝒐𝒕 𝑪𝒓𝒆𝒂𝒕𝒆𝒓", url="t.me/kmadminsbot")
                         ]
                        ]
                    )
    await message.reply(f"<b> ⭐ ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴs ᴛᴏ ᴊᴏɪɴ ᴜꜱ ⭐</b>\n\n", reply_markup=reply_markup, disable_web_page_preview = True)



@Bot.on_message(filters.command('stats') & filters.user(ADMINS))
async def stats(bot: Bot, message: Message):
    now = datetime.now()
    delta = now - bot.uptime
    time = get_readable_time(delta.seconds)
    await message.reply(BOT_STATS_TEXT.format(uptime=time))


@Bot.on_message(filters.private)
async def useless(_,message: Message):
    if USER_REPLY_TEXT:
        await message.reply(USER_REPLY_TEXT)

# ---------------- /help ----------------
@Bot.on_message(filters.command("help") & filters.user(ADMINS))
async def handle_help(client, message):
    try:
        # Split message text to see if a specific command is requested
        tokens = message.text.split()
        command_requested = tokens[1].lower() if len(tokens) > 1 else None

        # Define commands and descriptions
        commands_info = {
            "put": "Add/update a movie by TMDB ID. Usage:\n /put -tmdb 550 -f <file> [-o f|l] [-p|-u]",
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
