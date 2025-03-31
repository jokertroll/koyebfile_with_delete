import os
import asyncio
import humanize
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

from bot import Bot
from config import *
from helper_func import subscribed, encode, decode, get_messages
from database.database import add_user, del_user, full_userbase, present_user

file_delete_duration = FILE_AUTO_DELETE  # Time in seconds for auto-delete
formatted_delete_time = humanize.naturaldelta(file_delete_duration)

@Bot.on_message(filters.command('start') & filters.private & subscribed)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    if not await present_user(user_id):
        try:
            await add_user(user_id)
        except:
            pass
    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
        except:
            return
        decoded_string = await decode(base64_string)
        arguments = decoded_string.split("-")
        if len(arguments) == 3:
            try:
                start_id = int(int(arguments[1]) / abs(client.db_channel.id))
                end_id = int(int(arguments[2]) / abs(client.db_channel.id))
            except:
                return
            ids = range(start_id, end_id + 1) if start_id <= end_id else list(reversed(range(end_id, start_id + 1)))
        elif len(arguments) == 2:
            try:
                ids = [int(int(arguments[1]) / abs(client.db_channel.id))]
            except:
                return
        temp_msg = await message.reply("Fetching files, please wait...")
        try:
            messages = await get_messages(client, ids)
        except:
            await message.reply_text("Something went wrong!")
            return
        await temp_msg.delete()

        sent_messages = []  # List to keep track of sent messages

        for msg in messages:
            caption = CUSTOM_CAPTION.format(previouscaption=msg.caption.html if msg.caption else "", filename=msg.document.file_name) if CUSTOM_CAPTION and msg.document else (msg.caption.html if msg.caption else "")
            reply_markup = None
            try:
                sent_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                sent_messages.append(sent_msg)
            except FloodWait as e:
                await asyncio.sleep(e.value)
                sent_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                sent_messages.append(sent_msg)
            except Exception as e:
                print(f"Error copying message: {e}")
                pass

        # warning_msg = await client.send_message(
        #     chat_id=message.from_user.id,
        #     text=f"<b>❗ IMPORTANT ❗</b>\n\nThis file will be deleted in {formatted_delete_time}.\n\n📌 Please save or forward it elsewhere.",
        # )
        warning_msg = await client.send_message(
            chat_id=message.from_user.id,
            text=(
                "⚠️ <b>Attention!</b> ⚠️\n\n"
                "⏳ <b>Above files will be automatically deleted in</b> {formatted_delete_time}.\n\n"
                "💾 <b>Make sure to save or forward it before it's gone!</b> 🚀\n\n"
                "📌 <i>Tip: Download now to avoid losing access.</i>"
                ),
            parse_mode=ParseMode.HTML
        )


        asyncio.create_task(delete_files(sent_messages, client, warning_msg))
        return
    else:
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("😊 About Me", callback_data = "about"),
                    InlineKeyboardButton("🔒 Close", callback_data = "close")
                ]
            ]
        )
        await message.reply_text(
            text = START_MSG.format(
                first = message.from_user.first_name,
                last = message.from_user.last_name,
                username = None if not message.from_user.username else '@' + message.from_user.username,
                mention = message.from_user.mention,
                id = message.from_user.id
            ),
            reply_markup = reply_markup,
            disable_web_page_preview = True,
            quote = True
        )
        return

async def delete_files(messages, client, warning_message):
    await asyncio.sleep(FILE_AUTO_DELETE)
    for msg in messages:
        try:
            await client.delete_messages(chat_id=msg.chat.id, message_ids=[msg.id])
        except Exception as e:
            print(f"Error deleting message {msg.id}: {e}")

    try:
        # await warning_message.edit_text("<b><i>Your files has been successfully deleted ✅<i></b>")
        await warning_message.edit_text("<b><i>Your files have been successfully deleted ✅</i></b>")
    except Exception as e:
        print(f"Error editing warning message: {e}")
