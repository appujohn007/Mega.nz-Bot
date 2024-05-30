


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
        "**Gᴏᴛᴄʜᴀ Yᴏᴜʀ Lɪɴᴋ🤓  Bᴏss Wʜᴀᴛ's ɴᴇxᴛ🫡? **",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Dᴏᴡɴʟᴏᴀᴅ Nᴏᴡ 📥", callback_data=f"dwn_mg-{_mid}")],
                [InlineKeyboardButton("Gᴇᴛ Iɴғᴏ 📄", callback_data=f"info_mg-{_mid}")],
                [InlineKeyboardButton("ᑕᗩᑎᑕᗴᒪ ❌", callback_data=f"cancelqcb-{_usr}")],
            ]
        ),
    )


prv_rgx = r"(\/Root\/?.+)"

import os
import re
from os import makedirs, path
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

@CypherClient.on_callback_query(filters.regex(r"dwn_mg?.+"))
@CypherClient.run_checks
async def dl_from_cb(client: CypherClient, query: CallbackQuery):
    try:
        # Access saved info
        _mid = int(query.data.split("-")[1])
        qcid = query.message.chat.id
        qusr = query.from_user.id
        dtmp = client.glob_tmp.get(qusr)
        url = dtmp[0]
        dlid = dtmp[1]

        # Print debug information
        print(f"_mid: {_mid}, qcid: {qcid}, qusr: {qusr}, url: {url}, dlid: {dlid}")

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

        # Download the file/folder
        resp = await query.edit_message_text(
            "`𝙲𝚘𝚖𝚖𝚎𝚗𝚌𝚒𝚗𝚐 𝚈𝚘𝚞𝚛 𝙳𝚘𝚠𝚗𝚕𝚘𝚊𝚍 👾`", reply_markup=None
        )

        cli = MegaTools(client, conf)

        f_list = await cli.download(
            url,
            qusr,
            qcid,
            resp.id,
            path=dlid,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("cancel ❌", callback_data=f"cancelqcb-{qusr}")],
                ]
            ),
        )
        
        if not f_list:
            return

        await query.edit_message_text("`Successfully downloaded the content 🥳`")
        
        # update download count
        if client.database:
            await client.database.plus_fl_count(qusr, downloads=len(f_list))
        
        # Send file(s) to the user
        await resp.edit("`𝚃𝚛𝚢𝚒𝚗𝚐 𝚝𝚘 𝚞𝚙𝚕𝚘𝚊𝚍 𝚗𝚘𝚠 📤...`")
        await client.send_files(
            f_list,
            qcid,
            resp.id,
            reply_to_message_id=_mid,
            caption=f"**[𝙅𝙤𝙞𝙣 𝙊𝙪𝙧 𝘾𝙤𝙢𝙢𝙪𝙣𝙞𝙩𝙮](https://t.me/botio_devs)🥰**",
        )
        await client.full_cleanup(dlid, qusr)
        await resp.delete()
    
    except Exception as e:
        print(f"An error occurred: {e}")
        await query.edit_message_text(f"An error occurred: {e}")
    await client.full_cleanup(dlid, qusr)
    await resp.delete()
