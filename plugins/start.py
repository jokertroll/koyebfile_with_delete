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
            reply_markup = None if DISABLE_CHANNEL_BUTTON else msg.reply_markup
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

        warning_msg = await client.send_message(
            chat_id=message.from_user.id,
            text=f"<b>❗ IMPORTANT ❗</b>\n\nThis file will be deleted in {formatted_delete_time}.\n\n📌 Please save or forward it elsewhere.",
        )

        asyncio.create_task(delete_files(sent_messages, client, warning_msg))
        return
    else:
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🧠 Help", callback_data="help"), InlineKeyboardButton("🔰 About", callback_data="about")]
        ])
        await message.reply_photo(
            caption=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=f'@{message.from_user.username}' if message.from_user.username else None,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup,
        )

async def delete_files(messages, client, warning_message):
    await asyncio.sleep(FILE_AUTO_DELETE)
    for msg in messages:
        try:
            await client.delete_messages(chat_id=msg.chat.id, message_ids=[msg.id])
        except Exception as e:
            print(f"Error deleting message {msg.id}: {e}")

    try:
        await warning_message.edit_text("Your file has been successfully deleted ✅")
    except Exception as e:
        print(f"Error editing warning message: {e}")
