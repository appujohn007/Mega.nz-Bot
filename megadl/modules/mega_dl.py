# Copyright (c) 2023 Itz-fork
# Author: https://github.com/Itz-fork
# Project: https://github.com/Itz-fork/Mega.nz-Bot
# Description: Handle mega.nz download function


import re
from os import path, makedirs

from pyrogram import filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from megadl import CypherClient
from megadl.lib.megatools import MegaTools


@CypherClient.on_message(
    filters.regex(r"(https?:\/\/mega\.nz\/(file|folder|#)?.+)|(\/Root\/?.+)")
)
@CypherClient.run_checks
async def dl_from(client: CypherClient, msg: Message):
    # Push info to temp db
    _mid = msg.id
    _usr = msg.from_user.id
    client.glob_tmp[_usr] = [msg.text, f"{client.dl_loc}/{_usr}"]
    await msg.reply(
        "**Select what you want to do 🤗**",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Download 💾", callback_data=f"dwn_mg-{_mid}")],
                [InlineKeyboardButton("Info ℹ️", callback_data=f"info_mg-{_mid}")],
                [InlineKeyboardButton("Cancel ❌", callback_data=f"cancelqcb-{_usr}")],
            ]
        ),
    )


prv_rgx = r"(\/Root\/?.+)"


@CypherClient.on_callback_query(filters.regex(r"dwn_mg?.+"))
@CypherClient.run_checks
async def dl_from_cb(client: CypherClient, query: CallbackQuery):
    # Access saved info
    _mid = int(query.data.split("-")[1])
    qcid = query.message.chat.id
    qusr = query.from_user.id
    dtmp = client.glob_tmp.get(qusr)
    url = dtmp[0]
    dlid = dtmp[1]

    # weird workaround to add support for private mode
    conf = None
    if client.is_public:
        udoc = await client.database.is_there(qusr, True)
        if not udoc and re.match(prv_rgx, url):
            return await query.edit_message_text(
                "`You must be logged in first to download this file 😑`"
            )
        if udoc:
            email = client.cipher.decrypt(udoc["email"]).decode()
            password = client.cipher.decrypt(udoc["password"]).decode()
            proxy = f"--proxy {udoc['proxy']}" if udoc["proxy"] else ""
            conf = f"--username {email} --password {password} {proxy}"

    # Create unique download folder
    if not path.isdir(dlid):
        makedirs(dlid)

    # Edit message to indicate download is starting
    await query.edit_message_text("`Your download is starting 📥...`", reply_markup=None)

    # Download the file/folder
    cli = MegaTools(client, conf)
    f_list = await cli.download(
        url,
        qusr,
        qcid,
        query.message.message_id,
        path=dlid,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Cancel ❌", callback_data=f"cancelqcb-{qusr}")],
            ]
        ),
    )

    # Handle if download fails
    if not f_list:
        return

    # Update message to indicate successful download
    await query.edit_message_text("`Successfully downloaded the content 🥳`")

    # Send each file with its file name as caption
    for file_path in f_list:
        file_name = file_path.split('/')[-1]  # Extract file name from file path
        await client.send_document(
            qcid,
            file_path,
            caption=file_name,  # Use file name as caption
            reply_to_message_id=_mid,
        )

    # Update download count
    if client.database:
        await client.database.plus_fl_count(qusr, downloads=len(f_list))

    # Clean up
    await client.full_cleanup(dlid, qusr)
    await query.message.delete()
