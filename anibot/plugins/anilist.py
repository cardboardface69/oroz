# base code was taken from @DeletedUser420's Userge-Plugins repo
# I've just tweaked his file a bit (maybe a lot)
# But i sticked to the result format he used which looked cool

""" Search for Anime related Info using Anilist API """

import asyncio
import random
import base64
import requests
from natsort import natsorted
import time
import random
import re
import os
from pyrogram import filters, Client
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Message
import urllib.request
from pyrogram.errors import UserNotParticipant
from .. import ANILIST_CLIENT, ANILIST_REDIRECT_URL,HELP_DICT, ANILIST_SECRET, OWNER, TRIGGERS as trg, BOT_NAME, anibot
from ..utils.data_parser import (
    get_all_genres, search_filler, parse_filler, get_all_tags, get_scheduled, get_top_animes, get_user_activity, get_user_favourites, toggle_favourites,
    get_anime, get_airing, get_anilist, get_character, get_wo, get_wols, get_additional_info, get_manga, browse_,
    get_featured_in_lists, update_anilist, get_user, ANIME_DB, MANGA_DB, CHAR_DB, AIRING_DB, GUI
)
from ..utils.helper import ANON_JSON, check_user, get_btns, AUTH_USERS, rand_key, clog, control_user, PIC_LS
from ..utils.db import get_collection

GROUPS = get_collection("GROUPS")
SFW_GRPS = get_collection("SFW_GROUPS")
DC = get_collection('DISABLED_CMDS')
AG = get_collection('AIRING_GROUPS')
CG = get_collection('CRUNCHY_GROUPS')
SG = get_collection('SUBSPLEASE_GROUPS')
HD = get_collection('HEADLINES_GROUPS')

no_pic = [
    'https://telegra.ph/file/0d2097f442e816ba3f946.jpg',
    'https://telegra.ph/file/5a152016056308ef63226.jpg',
    'https://telegra.ph/file/d2bf913b18688c59828e9.jpg',
    'https://telegra.ph/file/d53083ea69e84e3b54735.jpg',
    'https://telegra.ph/file/b5eb1e3606b7d2f1b491f.jpg'
]

DC = get_collection('DISABLED_CMDS')


@anibot.on_message(filters.command(["watch", f"watch{BOT_NAME}"], prefixes=trg))
@control_user
async def get_watch_order(client: anibot, message: Message, mdata: dict):
    """Get List of Scheduled Anime"""
    gid = mdata['chat']['id']
    find_gc = await DC.find_one({'_id': gid})
    if find_gc is not None and 'watch' in find_gc['cmd_list'].split():
        return
    x = message.text.split(" ", 1)
    if len(x)==1:
        await message.reply_text("Nothing given to search for!!!")
        return
    user = mdata['from_user']['id']
    data = get_wols(x[1])
    msg = f"Found related animes for the query {x[1]}"
    buttons = []
    if data == []:
        await client.send_message(gid, 'No results found!!!')
        return
    for i in data:
        buttons.append([InlineKeyboardButton(str(i[1]), callback_data=f"watch_{i[0]}_{x[1]}_0_{user}")])
    await message.reply_text(msg, reply_markup=InlineKeyboardMarkup(buttons))


@anibot.on_callback_query(filters.regex(pattern=r"watch_(.*)"))
@check_user
async def watch_(client: anibot, cq: CallbackQuery, cdata: dict):
    kek, id_, qry, req, user = cdata['data'].split("_")
    msg, total = get_wo(int(id_), int(req))
    totalpg, lol = divmod(total, 50)
    button = []
    if lol!=0:
        totalpg + 1
    if total>50:
        if int(req)==0:
            button.append([InlineKeyboardButton(text="Next", callback_data=f"{kek}_{id_}_{qry}_{int(req)+1}_{user}")])
        elif int(req)==totalpg:
            button.append([InlineKeyboardButton(text="Prev", callback_data=f"{kek}_{id_}_{qry}_{int(req)-1}_{user}")])
        else:
            button.append(
                [
                    InlineKeyboardButton(text="Prev", callback_data=f"{kek}_{id_}_{qry}_{int(req)-1}_{user}"),
                    InlineKeyboardButton(text="Next", callback_data=f"{kek}_{id_}_{qry}_{int(req)+1}_{user}")
                ]
            )
    button.append([InlineKeyboardButton("Back", callback_data=f"wol_{qry}_{user}")])
    await cq.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(button))


@anibot.on_callback_query(filters.regex(pattern=r"wol_(.*)"))
@check_user
async def wls(client: anibot, cq: CallbackQuery, cdata: dict):
    kek, qry, user = cdata['data'].split("_")
    data = get_wols(qry)
    msg = f"Found related animes for the query {qry}"
    buttons = []
    for i in data:
        buttons.append([InlineKeyboardButton(str(i[1]), callback_data=f"watch_{i[0]}_{qry}_0_{user}")])
    await cq.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(buttons))
FILLERS = {}
DC = get_collection('DISABLED_CMDS')

@anibot.on_message(filters.command(['random', f"random{BOT_NAME}"], prefixes=trg))
async def handle_message(client: Client, message: Message): 
    rnx = random.randrange(0,10000)
    sax = f"https://pic.re/image/{rnx}"
    sugi = await message.reply_photo(sax)
    await asyncio.sleep(120)
    return await sugi.delete()

@anibot.on_message(filters.command(['fillers', f"fillers{BOT_NAME}"], prefixes=trg))
@control_user
async def fillers_cmd(client: anibot, message: Message, mdata: dict):
    find_gc = await DC.find_one({'_id': mdata['chat']['id']})
    if find_gc is not None and 'watch' in find_gc['cmd_list'].split():
        return
    qry = mdata['text'].split(" ", 1)
    if len(qry)==1:
        return await message.reply_text("Give some anime name to search fillers for\nexample: /fillers Detective Conan")
    k = search_filler(qry[1])
    if k == {}:
        await message.reply_text("No fillers found for the given anime...")
        return
    button = []
    list_ = list(k.keys())
    if len(list_)==1:
        result = parse_filler(k.get(list_[0]))
        msg = ""
        msg += f"Fillers for anime `{list_[0]}`\n\nManga Canon episodes:\n"
        msg += str(result.get("total_ep"))
        msg += "\n\nMixed/Canon fillers:\n"
        msg += str(result.get("mixed_ep"))
        msg += "\n\nFillers:\n"
        msg += str(result.get("filler_ep"))
        if result.get("ac_ep") is not None:
            msg += "\n\nAnime Canon episodes:\n"
            msg += str(result.get("ac_ep"))
        await message.reply_text(msg)
        return
    for i in list_:
        fl_js = rand_key()
        FILLERS[fl_js] = [k.get(i), i]
        button.append([InlineKeyboardButton(i, callback_data=f"fill_{fl_js}_{mdata['from_user']['id']}")])
    await message.reply_text("Pick anime you want to see fillers list for:", reply_markup=InlineKeyboardMarkup(button))


@anibot.on_callback_query(filters.regex(pattern=r"fill_(.*)"))
@check_user
async def filler_btn(client: anibot, cq: CallbackQuery, cdata: dict):
    kek, req, user = cdata['data'].split("_")
    result = parse_filler((FILLERS.get(req))[0])
    msg = ""
    msg += f"**Fillers for anime** `{(FILLERS.get(req))[1]}`\n\n**Manga Canon episodes:**\n"
    msg += str(result.get("total_ep"))
    msg += "\n\n**Mixed/Canon fillers:**\n"
    msg += str(result.get("mixed_ep"))
    msg += "\n\n**Fillers:**\n"
    msg += str(result.get("filler_ep"))
    if result.get("ac_ep") is not None:
        msg += "\n\n**Anime Canon episodes:**\n"
        msg += str(result.get("ac_ep"))
    fillerx = await cq.edit_message_text(msg)
    await asyncio.sleep(180)          
ADMIN = [1535813080, 149334579, 1874293288, 1468855699, 2109830713, 59714451044, 5258228429, 1443454117]  
@anibot.on_message(filters.chat(-1001944303479) & ~filters.user(ADMIN) & filters.regex(pattern=r"\baniwatch\.to\b"))
async def mana_cmd(client: Client, message: Message):

         ser = message.from_user.username
         await message.reply_text(f"**@{ser}**, Unfortunately forwarding any links of our website will be deleted as to not violate any **Telegram Terms of Service**.")
         await message.delete()
   
@anibot.on_message(filters.chat(-1001944303479) & ~filters.user(ADMIN) & filters.regex("aniwatch.nz"))
async def malna_cmd(client: Client, message: Message):      
         ser = message.from_user.username
         await message.reply_text(f"**@{ser}**, Unfortunately forwarding any links of our website will be deleted as to not violate any **Telegram Terms of Service**.")
         await message.delete()
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("hindu"))

async def malna_cmd(client: Client, message: Message):            
         await message.delete()
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("muslim"))

async def malna_cmd(client: Client, message: Message):
            
         await message.delete()
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("muslims"))

async def malna_cmd(client: Client, message: Message):
         await message.delete() 
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("hindus"))

async def malna_cmd(client: Client, message: Message):
            
         await message.delete()  
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("christian"))

async def malna_cmd(client: Client, message: Message):
            
         await message.delete()         
@anibot.on_message(filters.chat(-1001944303479) & ~filters.user(ADMIN) & filters.regex("aniwatch.se"))
async def mana_cmd(client: Client, message: Message):
      
         ser = message.from_user.username
         await message.reply_text(f"**@{ser}**, Unfortunately forwarding any links of our website will be deleted as to not violate any **Telegram Terms of Service**.")
         await message.delete()

@anibot.on_message(filters.chat(-1001944303479) & ~filters.user(ADMIN) & filters.regex("aniwatchtv.to"))
async def mana_cmd(client: Client, message: Message):

         ser = message.from_user.username
         await message.reply_text(f"**@{ser}**, Unfortunately forwarding any links of our website will be deleted as to not violate any **Telegram Terms of Service**.")
         kaze = await message.delete()
      
@anibot.on_message(filters.chat(-1001944303479) & ~filters.user(ADMIN) & filters.regex("aniwatch.me"))
async def mana_cmd(client: Client, message: Message):
      
         ser = message.from_user.username
         await message.reply_text(f"**@{ser}**, Unfortunately forwarding any links of our website will be deleted as to not violate any **Telegram Terms of Service**.")
         await message.delete()
      
@anibot.on_message(filters.chat(-1001944303479) &  ~filters.user(ADMIN) & filters.regex("mangareader.to"))
async def mana_cmd(client: Client, message: Message):
      
         ser = message.from_user.username
         await message.reply_text(f"**@{ser}**, Unfortunately forwarding any links of our website will be deleted as to not violate any **Telegram Terms of Service**.")
         await message.delete()
      
# Define the blacklist of words and website domains
blacklist = [
    "4ani",
    "6ani.me",
    "9anime",
    "999hentai",
    "9ani",
    "anicrush.to",
    "animekisa",
    "animebee",
    "animeflix",
    "animepahe",
    "animesuge",
    "aniwave",
    "AsuraScans",
    "Bato",
    "Comick",
    "gogo",
    "zorox.to",
    "goku.com",
    "h4anime",
    "hanime",
    "Jnovels",
    "kaido.to",
    "kissanime",
    "Manga4Life",
    "MangaBuddy",
    "MangaDex",
    "MangaFire",
    "MangaKakalot",
    "MangaLife",
    "mangareader.to",
    "Mangasee",
    "manhwa18",
    "marin.moe",
    "nhentai",
    "piracy.moe",
    "shiro",
    "TCBScans",
    "anix.to",
    "anix",
]

# Implement the message filter to detect and handle prohibited content
@anibot.on_message(filters.chat(-1001944303479) & ~filters.user(ADMIN) & filters.regex("(" + "|".join(blacklist) + ")"))
async def handle_blacklisted_content(client: Client, message: Message):
    user_username = message.from_user.username
    await message.reply_text(f"@{user_username}, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service**.")
    await message.delete()
@anibot.on_message(filters.chat(-1001944303479) &  ~filters.user(ADMIN) & filters.regex("999hentai"))
async def mana_cmd(client: Client, message: Message):
      
         ser = message.from_user.username
         await message.reply_text(f"**@{ser}**, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")
         await message.delete()

@anibot.on_message(filters.chat(-1001944303479) & ~filters.user(ADMIN) & filters.regex("zoro.moe"))
async def mana_cmd(client: Client, message: Message):
      
         ser = message.from_user.username
         await message.reply_text(f"**@{ser}**, Unfortunately forwarding any links of our website will be deleted as to not violate any **Telegram Terms of Service**.")
         await message.delete()
      
@anibot.on_message(filters.chat(-1001944303479) &  ~filters.user(ADMIN) & filters.regex(pattern=r"\bZoro\.to\b"))
async def mana_cmd(client: Client, message: Message):
      
         ser = message.from_user.username
         await message.reply_text(f"**@{ser}**, Unfortunately forwarding any links of our website will be deleted as to not violate any **Telegram Terms of Service**.")
         await message.delete()
      

@anibot.on_message(filters.chat(-1001944303479) &  ~filters.user(ADMIN) & filters.regex("Zoro.vc"))

async def mana_cmd(client: Client, message: Message):

      

         ser = message.from_user.username

         await message.reply_text(f"**@{ser}**, Unfortunately forwarding any links of our website will be deleted as to not violate any **Telegram Terms of Service**.")

         await message.delete()

      
@anibot.on_message(filters.chat(-1001944303479) &  ~filters.user(ADMIN) & filters.regex("goku.to"))
async def mana_cmd(client: Client, message: Message):
      
         ser = message.from_user.username
         await message.reply_text(f"**@{ser}**, Unfortunately forwarding any links of our website will be deleted as to not violate any **Telegram Terms of Service**.")
         await message.delete()
      
        
@anibot.on_message(filters.chat(-1001944303479) &  ~filters.user(ADMIN) & filters.regex("Goku.to"))

async def mana_cmd(client: Client, message: Message):
         ser = message.from_user.username

         await message.reply_text(f"**@{ser}**, Unfortunately forwarding any links of our website will be deleted as to not violate any **Telegram Terms of Service**.")

         await message.delete()

    

 
@anibot.on_message(filters.chat(-1001944303479) & ~filters.user(ADMIN) & filters.regex(pattern=r"\bMangareader\.to\b"))
async def mana_cmd(client: Client, message: Message):
    
         ser = message.from_user.username
         await message.reply_text(f"**@{ser}**, Unfortunately forwarding any links of our website will be deleted as to not violate any **Telegram Terms of Service**.")
         await message.delete()

@anibot.on_message(filters.chat(-1001944303479) & ~filters.user(ADMIN) & filters.regex(pattern=r"\bmangareader\.to\b"))
async def mana_cmd(client: Client, message: Message):
      
         ser = message.from_user.username
         await message.reply_text(f"**@{ser}**, Unfortunately forwarding any links of our website will be deleted as to not violate any **Telegram Terms of Service**.")
         await message.delete()
      
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("gogo"))

async def mana_cmd(client: Client, message: Message):


         ser = message.from_user.username

         await message.reply_text(f"**@{ser}**, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")

         await message.delete()


@anibot.on_message(filters.chat(-1001944303479) & filters.regex("gogoanime"))

async def mana_cmd(client: Client, message: Message):



         ser = message.from_user.username

         await message.reply_text(f"**@{ser}**, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")

         await message.delete()
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("Gogoanime"))


async def mana_cmd(client: Client, message: Message):

         ser = message.from_user.username

         await message.reply_text(f"**@{ser}**, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")

         await message.delete()
          


@anibot.on_message(filters.chat(-1001944303479) & filters.regex("animepahe"))
async def mana_cmd(client: Client, message: Message):
      
         ser = message.from_user.username
         await message.reply_text(f"@{ser}, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")
         await message.delete()
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("Anikatsu"))
async def mana_cmd(client: Client, message: Message):
      
         ser = message.from_user.username
         await message.reply_text(f"@{ser}, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")
         await message.delete()
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("Saikou"))
async def mana_cmd(client: Client, message: Message):
      
         ser = message.from_user.username
         await message.reply_text(f"@{ser}, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")
         await message.delete()
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("9anime"))
async def mana_cmd(client: Client, message: Message):
      
         ser = message.from_user.username
         await message.reply_text(f"@{ser}, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")
         await message.delete()
      
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("Animepahe"))
async def mana_cmd(client: Client, message: Message):
      
         ser = message.from_user.username
         await message.reply_text(f"@{ser}, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")
         await message.delete()
      
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("animesuge"))
async def mana_cmd(client: Client, message: Message):
      
         ser = message.from_user.username
         await message.reply_text(f"@{ser}, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")
         await message.delete()

@anibot.on_message(filters.chat(-1001944303479) & filters.regex("Animesuge"))
async def mana_cmd(client: Client, message: Message):

         ser = message.from_user.username
         await message.reply_text(f"@{ser}, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")
         await message.delete()
    
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("kissanime"))
async def mana_cmd(client: Client, message: Message):
      
         ser = message.from_user.username
         await message.reply_text(f"@{ser}, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")
         await message.delete()

@anibot.on_message(filters.chat(-1001944303479) & filters.regex("Kissanime"))
async def mana_cmd(client: Client, message: Message):
      
         ser = message.from_user.username
         await message.reply_text(f"@{ser}, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")
         await message.delete()
      
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("zoro.vc"))
async def mana_cmd(client: Client, message: Message):

         ser = message.from_user.username
         await message.reply_text(f"@{ser}, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")
         await message.delete()

   
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("Animebee"))
async def mana_cmd(client: Client, message: Message):
      
         ser = message.from_user.username
         await message.reply_text(f"@{ser}, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")
         await message.delete()
     
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("animixplay"))
async def mana_cmd(client: Client, message: Message):
      
         ser = message.from_user.username
         await message.reply_text(f"@{ser}, Refrain from sending any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")
         await message.delete()
      
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("Animixplay"))
async def mana_cmd(client: Client, message: Message):

         ser = message.from_user.username
         await message.reply_text(f"@{ser}, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")
                      
         await message.delete()
      
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("animekaizoku"))
async def mana_cmd(client: Client, message: Message):
      
         ser = message.from_user.username
         await message.reply_text(f"@{ser}, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")
         await message.delete()

@anibot.on_message(filters.chat(-1001944303479) & filters.regex("nyaa.si"))
async def mana_cmd(client: Client, message: Message):
      
         ser = message.from_user.username
         await message.reply_text(f"@{ser}, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")
         await message.delete()
      
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("animix"))
async def mana_cmd(client: Client, message: Message):
         ser = message.from_user.username
         await message.reply_text(f"@{ser}, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")
         await message.delete()
      
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("gogoanime"))
async def mana_cmd(client: Client, message: Message):
      
         sr = message.from_user.username
         await message.reply_text(f"@{sr}, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")
         await message.delete()
      
          
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("4anime"))
async def mana_cmd(client: Client, message: Message):
      
         sk = message.from_user.username
         await message.reply_text(f"@{sk}, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")
         await message.delete()
      
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("nhentai"))
async def mana_cmd(client: Client, message: Message):
      
         sur = message.from_user.username
         await message.reply_text(f"@{sur}, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")

         await message.delete()
      
@anibot.on_message(filters.chat(-1001944303479) & filters.regex("twist.moe"))
async def mana_cmd(client: Client, message: Message):
      
         sor = message.from_user.username
         zex = await message.reply_text(f"@{sor}, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")
         await message.delete()

@anibot.on_message(filters.chat(-1001944303479) & filters.regex("an!m!x"))
async def mana_cmd(client: Client, message: Message):
      
         syer = message.from_user.username
         zex = await message.reply_text(f"@{syer}, Refrain from forwarding any links of 3rd party websites, they will be deleted as to not violate any **Telegram Terms of Service.**")
         await message.delete()
      


@anibot.on_message(filters.chat(-1001944303479) & filters.command(["help", f"manga{BOT_NAME}"], prefixes=trg))
async def mana_cmd(client: Client, message: Message):
         repl_markup=InlineKeyboardMarkup([[InlineKeyboardButton(

                                                       "HELP", url="https://t.me/zorolostbot?start=help")]])
         await message.reply_text(f"Click below button for bot help.", reply_markup=repl_markup)     
@anibot.on_message(filters.command(["manga", f"manga{BOT_NAME}"], prefixes=trg))
@control_user
async def manga_cmd(client: Client, message: Message, mdata: dict):
    """Search Manga Info"""
    text = mdata['text'].split(" ", 1)
    gid = mdata['chat']['id']
    gidtype = mdata['chat']['type']
    user = mdata['from_user']['id']
    if gidtype in ["supergroup", "group"] and not await (GROUPS.find_one({"id": gid})):
        try:
            gidtitle = mdata['chat']['username']
        except KeyError:
            gidtitle = mdata['chat']['title']
        await GROUPS.insert_one({"id": gid, "grp": gidtitle})
        await clog("ANIBOT", f"Bot added to a new group\n\n{gidtitle}\nID: `{gid}`", "NEW_GROUP")
    find_gc = await DC.find_one({'_id': gid})
    if find_gc is not None and 'manga' in find_gc['cmd_list'].split():
        return
    if len(text)==1:
        k = await message.reply_text("Please give a query to search about\nexample: /manga One Piece")
        await asyncio.sleep(5)
        return await k.delete()
    query = text[1]
    qdb = rand_key()
    MANGA_DB[qdb] = query
    auth = False
    if (await AUTH_USERS.find_one({"id": user})):
        auth = True
    result = await get_manga(qdb, 1, auth=auth, user=user, cid=gid if gid!=user else None)
    if len(result) == 1:
        k = await message.reply_text(result[0])
        await asyncio.sleep(5)
        return await k.delete()
    pic, finals_ = result[0], result[1][0]
    buttons = get_btns("MANGA", lsqry=qdb, lspage=1, user=user, result=result, auth=auth)
    if await (SFW_GRPS.find_one({"id": gid})) and result[2].pop()=="True":
        buttons = get_btns("MANGA", lsqry=qdb, lspage=1, user=user, result=result, auth=auth, sfw="True")
        await message.reply_photo(no_pic[random.randint(0, 4)], caption="This manga is marked 18+ and not allowed in this group", reply_markup=buttons)
        return
    mangax = await message.reply_photo(pic, caption=finals_, reply_markup=buttons)
    if pic not in PIC_LS:
        PIC_LS.append(pic)
@anibot.on_message(filters.command(["zoro", f"anime{BOT_NAME}"], prefixes=trg))
@control_user
async def zoro_cmd(client: Client, message: Message, mdata: dict):
    """Search Anime Info"""
    text = mdata['text'].split(" ", 1)
    args = message.text.split(" ", 1)
    gid = mdata['chat']['id']
    gidtype = mdata['chat']['type']
    user = mdata['from_user']['id']
    if gidtype in ["supergroup", "group"] and not await (GROUPS.find_one({"id": gid})):
        try:
            gidtitle = mdata['chat']['username']
        except KeyError:
            gidtitle = mdata['chat']['title']
        await GROUPS.insert_one({"id": gid, "grp": gidtitle})
        await clog("ANIBOT", f"Bot added to a new group\n\n{gidtitle}\nID: {gid}", "NEW_GROUP")
    find_gc = await DC.find_one({'_id': gid})
    if find_gc is not None and 'zoro' in find_gc['cmd_list'].split():
        return
    if len(text)==1:
        k = await message.reply_text("Please give a query to search about\nexample: /zoro One Piece")
        await asyncio.sleep(5)
        return await k.delete()
    query = text[1]
    zoro_query = args[1]
    zoro_query = zoro_query.replace(" ","%20")
    zoro_url = f"https://zoro.to/search?keyword={zoro_query}"
    qdb = rand_key()
    ANIME_DB[qdb] = query
    auth = False
    if (await AUTH_USERS.find_one({"id": user})):
        auth = True
    result = await get_anilist(qdb, 1, auth=auth, user=user, cid=gid if gid!=user else None)
    if len(result) == 1:
        k = await message.reply_text(result[0])
        await asyncio.sleep(5)
        return await k.delete()
    pic, msg = result[0], result[1][0]
    buttons = get_btns("ANIME", result=result, user=user, auth=auth)
    if await (SFW_GRPS.find_one({"id": gid})) and result[2].pop()=="True":
        await message.reply_photo(no_pic[random.randint(0, 4)], caption="This anime is marked 18+ and not allowed in this group")
        return
    animexx = await message.reply_photo(pic, caption=msg, 
                   reply_markup=InlineKeyboardMarkup(         
                    [
                        [
                            InlineKeyboardButton(
                                text="📺 Watch Online",
                                url=zoro_url,
                            ),
                        ],
                      ],
                    ),
                )
    if pic not in PIC_LS:
        PIC_LS.append(pic)
@anibot.on_message(filters.command(["mangareader", f"mangareader{BOT_NAME}"], prefixes=trg))
@control_user
async def mangareader_cmd(client: Client, message: Message, mdata: dict):
    """Search Manga Info"""
    text = mdata['text'].split(" ", 1)
    args = message.text.split(" ", 1)
    gid = mdata['chat']['id']
    gidtype = mdata['chat']['type']
    user = mdata['from_user']['id']
    if gidtype in ["supergroup", "group"] and not await (GROUPS.find_one({"id": gid})):
        try:
            gidtitle = mdata['chat']['username']
        except KeyError:
            gidtitle = mdata['chat']['title']
        await GROUPS.insert_one({"id": gid, "grp": gidtitle})
        await clog("ANIBOT", f"Bot added to a new group\n\n{gidtitle}\nID: `{gid}`", "NEW_GROUP")
    find_gc = await DC.find_one({'_id': gid})
    if find_gc is not None and 'mangareader' in find_gc['cmd_list'].split():
        return
    if len(text)==1:
        k = await message.reply_text("Please give a query to search about\nexample: /mangareader One Piece")
        await asyncio.sleep(5)
        return await k.delete()
    query = text[1]
    mangareader_query = args[1]
    mangareader_query = mangareader_query.replace(" ","%20") 
    mangareader_url = f"https://mangareader.to/search?keyword={mangareader_query}"
    qdb = rand_key()
    MANGA_DB[qdb] = query
    auth = False
    if (await AUTH_USERS.find_one({"id": user})):
        auth = True
    result = await get_manga(qdb, 1, auth=auth, user=user, cid=gid if gid!=user else None)
    if len(result) == 1:
        k = await message.reply_text(result[0])
        await asyncio.sleep(5)
        return await k.delete()
    pic, finals_ = result[0], result[1][0]
    buttons = get_btns("MANGA", lsqry=qdb, lspage=1, user=user, result=result, auth=auth)
    if await (SFW_GRPS.find_one({"id": gid})) and result[2].pop()=="True":
        buttons = get_btns("MANGA", lsqry=qdb, lspage=1, user=user, result=result, auth=auth, sfw="True")
        await message.reply_photo(no_pic[random.randint(0, 4)], caption="This manga is marked 18+ and not allowed in this group", reply_markup=buttons)
        return
    mangar = await message.reply_photo(pic, caption=finals_,
                   reply_markup=InlineKeyboardMarkup(         
                    [
                        [
                            InlineKeyboardButton(
                                text="📖Read Online",
                                url=mangareader_url,
                            ),
                        ],
                      ],
                    ),
                )                                    
    if pic not in PIC_LS:
       PIC_LS.append(pic)



@anibot.on_message(filters.command(["character", f"character{BOT_NAME}"], prefixes=trg))
@control_user
async def character_cmd(client: Client, message: Message, mdata: dict):
    """Get Info about a Character"""
    text = mdata['text'].split(" ", 1)
    gid = mdata['chat']['id']
    gidtype = mdata['chat']['type']
    user = mdata['from_user']['id']
    if gidtype in ["supergroup", "group"] and not await (GROUPS.find_one({"id": gid})):
        try:
            gidtitle = mdata['chat']['username']
        except KeyError:
            gidtitle = mdata['chat']['title']
        await GROUPS.insert_one({"id": gid, "grp": gidtitle})
        await clog("ANIBOT", f"Bot added to a new group\n\n{gidtitle}\nID: `{gid}`", "NEW_GROUP")
    find_gc = await DC.find_one({'_id': gid})
    if find_gc is not None and 'character' in find_gc['cmd_list'].split():
        return
    if len(text)==1:
        k = await message.reply_text("Please give a query to search about\nExample: `/character Nami`")
        await asyncio.sleep(5)
        return await k.delete()
    query = text[1]
    qdb = rand_key()
    CHAR_DB[qdb]=query
    auth = False
    if (await AUTH_USERS.find_one({"id": user})):
        auth = True
    result = await get_character(qdb, 1, auth=auth, user=user)
    if len(result) == 1:
        k = await message.reply_text(result[0])
        await asyncio.sleep(5)
        return await k.delete()
    img = result[0]
    cap_text = result[1][0]
    buttons = get_btns("CHARACTER", user=user, lsqry=qdb, lspage=1, result=result, auth=auth)
    characterx = await message.reply_photo(img, caption=cap_text, reply_markup=buttons)

@anibot.on_message(filters.command(["anime", f"anilist{BOT_NAME}"], prefixes=trg))
@control_user
async def anime_cmd(client: Client, message: Message, mdata: dict):
    text = mdata['text'].split(" ", 1)
    gid = mdata['chat']['id']
    user = mdata['from_user']['id']
    find_gc = await DC.find_one({'_id': gid})
    if find_gc is not None and 'anime' in find_gc['cmd_list'].split():
        return
    if len(text)==1:
        k = await message.reply_text("Please give a query to search about\nexample: /anime Boku no Pico")
        await asyncio.sleep(5)
        return await k.delete()
    query = text[1]
    qdb = rand_key()
    ANIME_DB[qdb] = query
    auth = False
    if (await AUTH_USERS.find_one({"id": user})):
        auth = True
    result = await get_anilist(qdb, 1, auth=auth, user=user, cid=gid if gid!=user else None)
    if len(result) == 1:
        k = await message.reply_text(result[0])
        await asyncio.sleep(5)
        return await k.delete()
    pic, msg = result[0], result[1][0]
    
    buttons = get_btns("ANIME", lsqry=qdb, lspage=1, result=result, user=user, auth=auth)
    if await (SFW_GRPS.find_one({"id": gid})) and result[2].pop()=="True":
        buttons = get_btns("ANIME", lsqry=qdb, lspage=1, result=result, user=user, auth=auth, sfw="True")
        await client.send_photo(gid, no_pic[random.randint(0, 4)], caption="This anime is marked 18+ and not allowed in this group", reply_markup=buttons)
        return
    anilistx = await message.reply_photo(pic, caption=msg, reply_markup=buttons)
    if pic not in PIC_LS:
        PIC_LS.append(pic)
 
    
@anibot.on_message(filters.command(["flex", f"flex{BOT_NAME}", "user", f"user{BOT_NAME}"], prefixes=trg))
@control_user
async def flex_cmd(client: Client, message: Message, mdata: dict):
    query = mdata['text'].split(" ", 1)
    gid = mdata['chat']['id']
    qry = None
    find_gc = await DC.find_one({'_id': gid})
    if "user" in query[0]:
        if find_gc is not None and 'user' in find_gc['cmd_list'].split():
            return
        if not len(query)==2:
            k = await message.reply_text("Please give an anilist username to search about\nexample: /user herkz")
            await asyncio.sleep(5)
            return await k.delete()
        else:
            qry = {"search": query[1]}
    if find_gc is not None and 'flex' in find_gc['cmd_list'].split():
        return
    user = mdata['from_user']['id']
    if not "user" in query[0] and not (await AUTH_USERS.find_one({"id": user})):
        return await message.reply_text(
            "Please connect your account first to use this cmd",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Auth", url=f"https://t.me/{BOT_NAME.replace('@', '')}/?start=auth")]])
        )
    result = await get_user(qry, query[0], user)
    if len(result) == 1:
        k = await message.reply_text(result[0])
        await asyncio.sleep(5)
        return await k.delete()
    pic, msg, buttons = result
    await message.reply_photo(pic, caption=msg, reply_markup=buttons)


@anibot.on_message(filters.command(["top", f"top{BOT_NAME}"], prefixes=trg))
@control_user
async def top_tags_cmd(client: Client, message: Message, mdata: dict):
    query = mdata['text'].split(" ", 1)
    gid = mdata['chat']['id']
    find_gc = await DC.find_one({'_id': gid})
    if find_gc is not None and 'top' in find_gc['cmd_list'].split():
        return
    get_tag = "None"
    if len(query)==2:
        get_tag = query[1]
    user = mdata['from_user']['id']
    result = await get_top_animes(get_tag, 1, user)
    if len(result) == 1:
        k = await message.reply_text(result[0])
        await asyncio.sleep(5)
        return await k.delete()
    if await (SFW_GRPS.find_one({"id": gid})) and str(result[0][1])=="True":
        return await message.reply_text('No nsfw stuff allowed in this group!!!')
    msg, buttons = result
    topx = await message.reply_text(msg[0], reply_markup=buttons if buttons!='' else None)

@anibot.on_message(filters.command(["airing", f"airing{BOT_NAME}"], prefixes=trg))
@control_user
async def airing_cmd(client: Client, message: Message, mdata: dict):
    """Get Airing Detail of Anime"""
    text = mdata['text'].split(" ", 1)
    gid = mdata['chat']['id']
    find_gc = await DC.find_one({'_id': gid})
    if find_gc is not None and 'airing' in find_gc['cmd_list'].split():
        return
    if len(text)==1:
        k = await message.reply_text("Please give a query to search about\nexample: `/airing One Piece`")
        await asyncio.sleep(5)
        return await k.delete()
    query = text[1]
    qdb = rand_key()
    AIRING_DB[qdb] = query
    auth = False
    user = mdata['from_user']['id']
    if (await AUTH_USERS.find_one({"id": user})):
        auth = True
    result = await get_airing(qdb, 1, auth=auth, user=user)
    if len(result) == 1:
        k = await message.reply_text(result[0])
        await asyncio.sleep(5)
        return await k.delete()
    coverImg, out = result[0]
    btn = get_btns("AIRING", user=user, result=result, lsqry=qdb, lspage=1)
    if await (SFW_GRPS.find_one({"id": gid})) and result[2].pop()=="True":
        btn = get_btns("AIRING", user=user, result=result, auth=auth, lsqry=qdb, lspage=1, sfw="True")
        await client.send_photo(gid, no_pic[random.randint(0, 4)], caption="This anime is marked 18+ and not allowed in this group", reply_markup=btn)
        return
    airingx = await message.reply_text(text=out, reply_markup=btn)
    update = True
    for i in PIC_LS:
        if coverImg in i:
            update = False
            break
    if update:
        PIC_LS.append(coverImg)

@anibot.on_message(filters.command(["schedule", f"schedule{BOT_NAME}"], prefixes=trg))
@control_user
async def get_schuled(client: anibot, message: Message, mdata: dict):
    """Get List of Scheduled Anime"""
    gid = mdata['chat']['id']
    find_gc = await DC.find_one({'_id': gid})
    if find_gc is not None and 'schedule' in find_gc['cmd_list'].split():
        return
    x = await message.reply_text( "<code>Fetching Scheduled Anime</code>")
    user = mdata['from_user']['id']
    msg = await get_scheduled()
    buttons = get_btns("SCHEDULED", result=[0], user=user)
    await x.edit_text(msg, reply_markup=buttons)

@anibot.on_callback_query(filters.regex(pattern=r"sched_(.*)"))
@check_user
async def ns_(client: anibot, cq: CallbackQuery, cdata: dict):
    kek, day, user = cdata['data'].split("_")
    msg = await get_scheduled(int(day))
    buttons = get_btns("SCHEDULED", result=[int(day)], user=user)
    schedulex = await cq.edit_message_text(msg, reply_markup=buttons)

@anibot.on_message(filters.command(["auth", f"auth{BOT_NAME}"], prefixes=trg))
@control_user
async def auth_link_cmd(client, message: Message, mdata: dict):
    try:
        user = mdata['from_user']['id']
    except KeyError:
        user = 00000000
    if mdata['chat']['id']==user:
        text = "Click the below button to authorize yourself"
        if not os.environ.get('ANILIST_REDIRECT_URL'):
            text = """Follow the steps to complete Authorization:
1. Click the below button
2. Authorize the app and copy the authorization code
3. Send the code along with cmd /code like '/code <u>auth code from website</u>'"""
        await message.reply_text(
            text = text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                text="Authorize",
                url=f"https://anilist.co/api/v2/oauth/authorize?client_id={ANILIST_CLIENT}&redirect_uri={ANILIST_REDIRECT_URL}&response_type=code"
            )]])
        )
    else:
        await message.reply_text(
            "Go to bot pm to authorize yourself!!!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Auth", url=f"https://t.me/{BOT_NAME.replace('@', '')}/?start=auth")]])
        )

setting_text = """
This allows you to change group settings
        
• NSFW toggle switches on filtering of 18+ marked content
• Airing notifications notifies about airing of anime in recent
• Crunchyroll updates will toggle notifications about release of animes on crunchyroll site
• Headlines will toggle notifications for anime news powered by livechart.me
• Change UI can be used to change bullet style.
"""
@anibot.on_message(~filters.private & filters.command(["settings", f"settings{BOT_NAME}"], prefixes=trg))
@control_user
async def sfw_cmd(client: Client, message: Message, mdata: dict):
    user = mdata['from_user']['id']
    cid = mdata['chat']['id']
    if user in OWNER or (await client.get_chat_member(cid, user)).status!='member':
        
        sfw = "NSFW: Allowed"
        if await (SFW_GRPS.find_one({"id": cid})):
            sfw = "NSFW: Not Allowed"
        notif = "Airing notifications: OFF"
        if await (AG.find_one({"_id": cid})):
            notif = "Airing notifications: ON"
        cr = "Crunchyroll Updates: OFF"
        if await (CG.find_one({"_id": cid})):
            cr = "Crunchyroll Updates: ON"
        hd = "Headlines: OFF"
        if await (HD.find_one({"_id": cid})):
            hd = "Headlines: ON"
        await message.reply_text(
            text = setting_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text=sfw, callback_data=f"settogl_sfw_{cid}")],
                [InlineKeyboardButton(text=notif, callback_data=f"settogl_notif_{cid}")],
                [InlineKeyboardButton(text=cr, callback_data=f"settogl_cr_{cid}")],
                [InlineKeyboardButton(text=hd, callback_data=f"settogl_hd_{cid}")],
                [InlineKeyboardButton(text="Change UI", callback_data=f"cui_call_{cid}")]
            ])
        )

@anibot.on_message(filters.private & filters.command("code", prefixes=trg))
@control_user
async def man_code_cmd(client: Client, message: Message, _):
    text = message.text.split(" ", 1)
    if len(text)==1:
        return await message.reply_text('Send the code you obtained from website along with the cmd')
    await code_cmd(text[1], message)


async def code_cmd(code: str, message: Message):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    json = {
        'grant_type': 'authorization_code',
        'client_id': ANILIST_CLIENT,
        'client_secret': ANILIST_SECRET,
        'redirect_uri': ANILIST_REDIRECT_URL,
        'code': code
    }
    us_ = message.from_user.id
    if (await AUTH_USERS.find_one({"id": us_})):
        return await message.reply_text("You have already authorized yourself\nIf you wish to logout send /logout")
    response: dict = requests.post("https://anilist.co/api/v2/oauth/token", headers=headers, json=json).json()
    if response.get("access_token"):
        await AUTH_USERS.insert_one({"id": us_, "token": response.get("access_token")})
        await message.reply_text("Authorization Successfull!!!" )
    else:
        await message.reply_text("Please retry authorization process!!!\nSomething unexpected happened")
    if os.environ.get('ANILIST_REDIRECT_URL'):
        await AUTH_USERS.find_one_and_delete({'code': code})


@anibot.on_message(filters.command(["me", f"me{BOT_NAME}", "activity", f"activity{BOT_NAME}"], prefixes=trg))
@control_user
async def activity_cmd(client: Client, message: Message, mdata: dict):
    user = mdata['from_user']['id']
    gid = mdata['chat']['id']
    find_gc = await DC.find_one({'_id': gid})
    if find_gc is not None and ('me' or 'activity') in find_gc['cmd_list'].split():
        return
    if not (await AUTH_USERS.find_one({"id": user})):
        return await message.reply_text(
            "Please connect your account first to use this cmd",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Auth", url=f"https://t.me/{BOT_NAME.replace('@', '')}/?start=auth")]])
        )
    result = await get_user(None, "flex", user)
    query = result[0].split("/").pop().split("?")[0]
    result = await get_user_activity(int(query), user=int(user))
    pic, msg, kek = result
    btns = InlineKeyboardMarkup([[InlineKeyboardButton("Profile", url=f"https://anilist.co/user/{query}")]])
    await message.reply_photo(pic, caption=msg, reply_markup=btns)


@anibot.on_message(filters.command(["favourites", f"favourites{BOT_NAME}"], prefixes=trg))
@control_user
async def favourites_cmd(client: Client, message: Message, mdata: dict):
    user = mdata['from_user']['id']
    gid = mdata['chat']['id']
    find_gc = await DC.find_one({'_id': gid})
    if find_gc is not None and 'favourites' in find_gc['cmd_list'].split():
        return
    if not (await AUTH_USERS.find_one({"id": user})):
        return await message.reply_text(
            "Please connect your account first to use this cmd",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Auth", url=f"https://t.me/{BOT_NAME.replace('@', '')}/?start=auth")]])
        )
    result = await get_user(None, "flex", user)
    query = result[0].split("/").pop().split("?")[0]
    btn = InlineKeyboardMarkup(
        [   
            [
                InlineKeyboardButton("ANIME", callback_data=f"myfavqry_ANIME_{query}_1_no_{user}"),
                InlineKeyboardButton("CHARACTER", callback_data=f"myfavqry_CHAR_{query}_1_no_{user}"),
                InlineKeyboardButton("MANGA", callback_data=f"myfavqry_MANGA_{query}_1_no_{user}")
            ],
            [
                InlineKeyboardButton("Profile", url=f"https://anilist.co/user/{query}")
            ]
        ]
    )
    await client.send_photo(gid, result[0], caption="Choose one of the below options", reply_markup=btn)


@anibot.on_message(filters.command(["logout", f"logout{BOT_NAME}"], prefixes=trg))
@control_user
async def logout_cmd(client: Client, message: Message, mdata: dict):
    try:
        user = mdata['from_user']['id']
    except KeyError:
        user = 00000000
    gid = mdata['chat']['id']
    if gid == user:
        if (await AUTH_USERS.find_one({"id": user})):
            AUTH_USERS.find_one_and_delete({"id": user})
            await message.reply_text("Logged out!!!")
        else:
            await message.reply_text("You are not authorized to begin with!!!")
    else:
        await message.reply_text("Send this cmd in pm!!!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Logout", url=f"https://t.me/{BOT_NAME.replace('@', '')}/?start=logout")]]))


@anibot.on_message(filters.command(["browse", f"browse{BOT_NAME}"], prefixes=trg))
@control_user
async def browse_cmd(client: Client, message: Message, mdata: dict):
    user = mdata['from_user']['id']
    gid = mdata['chat']['id']
    up = 'Upcoming'
    tr = '• Trending •'
    pp = 'Popular'
    btns = [[
        InlineKeyboardButton(tr, callback_data=f'browse_{tr.lower()}_{user}'),
        InlineKeyboardButton(pp, callback_data=f'browse_{pp.lower()}_{user}'),
        InlineKeyboardButton(up, callback_data=f'browse_{up.lower()}_{user}'),
    ]]
    msg = await browse_('trending')
    browsex = await message.reply_text(msg, reply_markup=InlineKeyboardMarkup(btns))
    await asyncio.sleep(180)
    return await browsex.delete()

@anibot.on_message(filters.command(["gettags", f"gettags{BOT_NAME}", "getgenres", f"getgenres{BOT_NAME}"], prefixes=trg))
@control_user
async def list_tags_genres_cmd(client, message: Message, mdata: dict):
    gid = mdata['chat']['id']
    text = mdata['text']
    find_gc = await DC.find_one({'_id': gid})
    if find_gc is not None and "gettags" in text.split()[0] and 'gettags' in find_gc['cmd_list'].split():
        return
    if find_gc is not None and "getgenres" in text.split()[0] and 'getgenres' in find_gc['cmd_list'].split():
        return
    if await (SFW_GRPS.find_one({"id": gid})) and 'nsfw' in text:
        return await message.reply_text('No nsfw allowed here!!!')
    msg = (await get_all_tags(text)) if "gettags" in text.split()[0] else (await get_all_genres())
    genrex = await message.reply_text(msg)
    await asyncio.sleep(180)
    return await genrex.delete()

@anibot.on_callback_query(filters.regex(pattern=r"page_(.*)"))
@check_user
async def page_btn(client: Client, cq: CallbackQuery, cdata: dict):
    kek, media, query, page, auth, user = cq.data.split("_")
    gid = cdata["message"]["chat"]["id"]
    if media=="ANIME":
        try:
            ANIME_DB[query]
        except KeyError:
            return await cq.answer("Query Expired!!!\nCreate new one", show_alert=True)
    if media=="MANGA":
        try:
            MANGA_DB[query]
        except KeyError:
            return await cq.answer("Query Expired!!!\nCreate new one", show_alert=True)
    if media=="CHARACTER":
        try:
            CHAR_DB[query]
        except KeyError:
            return await cq.answer("Query Expired!!!\nCreate new one", show_alert=True)
    if media=="AIRING":
        try:
            AIRING_DB[query]
        except KeyError:
            return await cq.answer("Query Expired!!!\nCreate new one", show_alert=True)
    await cq.answer()
    authbool = bool(1) if auth=="True" else bool(0)
    if media in ["ANIME", "MANGA"]:
        result = await (get_anilist if media == "ANIME" else get_manga)(query, int(page), auth=authbool, user=int(user), cid=gid if gid!=user else None)
    else:
        result = await (get_character if media == "CHARACTER" else get_airing)(query, int(page), auth=authbool, user=int(user))
    pic, msg = result[0], result[1][0]
    if media == "AIRING":
        pic, msg = result[0][0], result[0][1]
    button = get_btns(media, lsqry=query, lspage=int(page), result=result, user=user, auth=authbool)
    if await (SFW_GRPS.find_one({"id": gid})) and media!="CHARACTER" and result[2].pop()=="True":
        button = get_btns(media, lsqry=query, lspage=int(page), result=result, user=user, auth=authbool, sfw="True")
        await cq.edit_message_media(InputMediaPhoto(no_pic[random.randint(0, 4)], caption="This material is marked 18+ and not allowed in this group"), reply_markup=button)
        return
    await cq.edit_message_media(InputMediaPhoto(pic, caption=msg), reply_markup=button)
    if media!="CHARACTER":
        if pic not in PIC_LS:
            PIC_LS.append(pic)


@anibot.on_callback_query(filters.regex(pattern=r"btn_(.*)"))
@check_user
async def anime_btn(client: Client, cq: CallbackQuery, cdata: dict):
    await cq.answer()
    query = cdata['data'].split("_")
    idm = query[1]
    user = int(query.pop())
    authbool = bool(1) if query[2]=="True" else bool(0)
    vars_ = {"id": int(idm)}
    cid = cdata["message"]["chat"]["id"]
    result = await get_anime(vars_, auth=authbool, user=user, cid=cid if cid!=user else None)
    pic, msg = result[0], result[1]
    btns = get_btns("ANIME", result=result, user=user, auth=authbool)
    await cq.edit_message_media(InputMediaPhoto(pic, caption=msg), reply_markup=btns)
    if pic not in PIC_LS:
        PIC_LS.append(pic)


@anibot.on_callback_query(filters.regex(pattern=r"topanimu_(.*)"))
@check_user
async def top_tags_btn(client: Client, cq: CallbackQuery, cdata: dict):
    await cq.answer()
    kek, gnr, page, user = cdata['data'].split("_")
    result = await get_top_animes(gnr, page=page, user=user)
    msg, buttons = result[0][0], result[1]
    await cq.edit_message_text(msg, reply_markup=buttons)


@anibot.on_callback_query(filters.regex(pattern=r"settogl_(.*)"))
async def nsfw_toggle_btn(client: Client, cq: CallbackQuery):
    cus = cq.from_user.id
    gid = cq.data.split('_').pop()
    try:
        k = (await client.get_chat_member(gid, cus)).status
    except UserNotParticipant:
        await cq.answer()
        return
    if cus not in OWNER and str(k)=="member":
        await cq.answer("You don't have enough permissions to change this!!!", show_alert=True)
        return
    await cq.answer()
    query = cq.data.split("_")
    if await (SFW_GRPS.find_one({"id": int(query[2])})):
        sfw = "NSFW: Not Allowed"
    else:
        sfw = "NSFW: Allowed"
    if await (AG.find_one({"_id": int(query[2])})):
        notif = "Airing notifications: ON"
    else:
        notif = "Airing notifications: OFF"
    if await (CG.find_one({"_id": int(query[2])})):
        cr = "Crunchyroll Updates: ON"
    else:
        cr = "Crunchyroll Updates: OFF"
    if await (HD.find_one({"_id": int(query[2])})):
        hd = "Headlines: ON"
    else:
        hd = "Headlines: OFF"
    if query[1]=="sfw":
        if await (SFW_GRPS.find_one({"id": int(query[2])})):
            await SFW_GRPS.find_one_and_delete({"id": int(query[2])})
            sfw = "NSFW: Allowed"
        else:
            await SFW_GRPS.insert_one({"id": int(query[2])})
            sfw = "NSFW: Not Allowed"
    if query[1]=="notif":
        if await (AG.find_one({"_id": int(query[2])})):
            await AG.find_one_and_delete({"_id": int(query[2])})
            notif = "Airing notifications: OFF"
        else:
            await AG.insert_one({"_id": int(query[2])})
            notif = "Airing notifications: ON"
    if query[1]=="cr":
        if await (CG.find_one({"_id": int(query[2])})):
            await CG.find_one_and_delete({"_id": int(query[2])})
            cr = "Crunchyroll Updates: OFF"
        else:
            await CG.insert_one({"_id": int(query[2])})
            cr = "Crunchyroll Updates: ON"
    if query[1]=="hd":
        if await (HD.find_one({"_id": int(query[2])})):
            await HD.find_one_and_delete({"_id": int(query[2])})
            hd = "Headlines: OFF"
        else:
            await HD.insert_one({"_id": int(query[2])})
            hd = "Headlines: ON"
    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton(text=sfw, callback_data=f"settogl_sfw_{query[2]}")],
        [InlineKeyboardButton(text=notif, callback_data=f"settogl_notif_{query[2]}")],
        [InlineKeyboardButton(text=cr, callback_data=f"settogl_cr_{query[2]}")],
        [InlineKeyboardButton(text=sp, callback_data=f"settogl_sp_{query[2]}")],
        [InlineKeyboardButton(text=hd, callback_data=f"settogl_hd_{query[2]}")],
        [InlineKeyboardButton(text="Change UI", callback_data=f"cui_call_{query[2]}")]
    ])
    if query[1]=="call":
        await cq.edit_message_text(text = setting_text, reply_markup=btns)
    await cq.edit_message_reply_markup(reply_markup=btns)


@anibot.on_callback_query(filters.regex(pattern=r"myacc_(.*)"))
@check_user
async def flex_btn(client: Client, cq: CallbackQuery, cdata: dict):
    await cq.answer()
    query = cdata['data'].split("_")[1]
    user = cdata['data'].split("_").pop()
    result = await get_user_activity(int(query), user=int(user))
    pic, msg, btns = result
    await cq.edit_message_media(InputMediaPhoto(pic, caption=msg), reply_markup=btns)


@anibot.on_callback_query(filters.regex(pattern=r"myfavs_(.*)"))
@check_user
async def list_favourites_btn(client: Client, cq: CallbackQuery, cdata: dict):
    await cq.answer()
    q = cdata['data'].split("_")
    btn = [[
        InlineKeyboardButton("ANIME", callback_data=f"myfavqry_ANIME_{q[1]}_1_{q[2]}_{q[3]}"),
        InlineKeyboardButton("CHARACTER", callback_data=f"myfavqry_CHAR_{q[1]}_1_{q[2]}_{q[3]}"),
        InlineKeyboardButton("MANGA", callback_data=f"myfavqry_MANGA_{q[1]}_1_{q[2]}_{q[3]}")
    ]]
    if q[2] == "yes":
        btn.append([InlineKeyboardButton("Back", callback_data=f"getusrbc_{q[3]}")])
    else:
        btn.append([InlineKeyboardButton("Profile", url=f"https://anilist.co/user/{q[1]}")])
    await cq.edit_message_media(
        InputMediaPhoto(f"https://img.anili.st/user/{q[1]}?a={time.time()}", caption="Choose one of the below options"),
        reply_markup=InlineKeyboardMarkup(btn)
    )


@anibot.on_callback_query(filters.regex(pattern=r"myfavqry_(.*)"))
@check_user
async def favourites_btn(client: Client, cq: CallbackQuery, cdata: dict):
    await cq.answer()
    q = cdata['data'].split("_")
    pic, msg, btns = await get_user_favourites(q[2], int(q[5]), q[1], q[3], q[4])
    await cq.edit_message_media(InputMediaPhoto(pic, caption=msg), reply_markup=btns)


@anibot.on_callback_query(filters.regex(pattern=r"getusrbc_(.*)"))
@check_user
async def get_user_back_btn(client: Client, cq: CallbackQuery, cdata: dict):
    await cq.answer()
    query = cdata['data'].split("_")[1]
    result = await get_user(None, "flex", user=int(query))
    pic, msg, btns = result
    await cq.edit_message_media(InputMediaPhoto(pic, caption=msg), reply_markup=btns)


@anibot.on_callback_query(filters.regex(pattern=r"fav_(.*)"))
@check_user
async def toggle_favourites_btn(client: Client, cq: CallbackQuery, cdata: dict):
    query = cdata['data'].split("_")
    if query[1]=="ANIME" and len(query)>4:
        try:
            ANIME_DB[query[3]]
        except KeyError:
            return await cq.answer("Query Expired!!!\nCreate new one", show_alert=True)
    if query[1]=="MANGA":
        try:
            MANGA_DB[query[3]]
        except KeyError:
            return await cq.answer("Query Expired!!!\nCreate new one", show_alert=True)
    idm = int(query[2])
    user = int(query.pop())
    gid = cdata["message"]["chat"]["id"]
    rslt = await toggle_favourites(id_=idm, media=query[1], user=user)
    if rslt=="ok":
        await cq.answer("Updated")
    else:
        return
    result = (
        (await get_anime({"id": idm}, auth=True, user=user, cid=gid if gid!=user else None)) if query[1]=="ANIME" and len(query)==3
        else (await get_anilist(query[3], page = int(query[4]), auth=True, user=user, cid=gid if gid!=user else None)) if query[1]=="ANIME" and len(query)!=3
        else (await get_manga(query[3], page = int(query[4]), auth=True, user=user, cid=gid if gid!=user else None)) if query[1]=="MANGA"
        else (await get_airing({"id": idm}, auth=True, user=user)) if query[1]=="AIRING"
        else (await get_character(query[3], int(query[4]), auth=True, user=user))
    )
    pic, msg = (
        (result[0], result[1]) if query[1]=="ANIME" and len(query)==3
        else (result[0]) if query[1]=="AIRING"
        else (result[0], result[1][0])
    )
    btns = get_btns(
        query[1],
        result=result,
        user=user,
        auth=True,
        lsqry=query[3] if len(query)!=3 else None,
        lspage=int(query[4]) if len(query)!=3 else None
    )
    await cq.edit_message_media(InputMediaPhoto(pic, caption=msg), reply_markup=btns)


@anibot.on_callback_query(filters.regex(pattern=r"(lsadd|lsupdt)_(.*)"))
@check_user
async def list_update_anilist_btn(client: Client, cq: CallbackQuery, cdata: dict):
    stts_ls = ["COMPLETED", "CURRENT", "PLANNING", "DROPPED", "PAUSED", "REPEATING"]
    query = cdata['data'].split("_")
    btns = []
    row = []
    for i in stts_ls:
        row.append(
            InlineKeyboardButton(
                text=i,
                callback_data=cq.data.replace("lsadd", f"lsas_{i}") if query[0]=="lsadd" else cq.data.replace("lsupdt", f"lsus_{i}")
            )
        )
        if len(row)==3:
            btns.append(row)
            row = []
    if query[0]=="lsupdt":
        btns.append([InlineKeyboardButton("Delete", callback_data=cq.data.replace("lsupdt", f"dlt_{i}"))])
    await cq.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btns))


@anibot.on_callback_query(filters.regex(pattern=r"browse_(upcoming|trending|popular)_(.*)"))
@check_user
async def browse_btn(client: Client, cq: CallbackQuery, cdata: dict):
    query = cdata['data'].split("_")
    if '•' in query[1]:
        return
    msg = await browse_(query[1])
    up = 'Upcoming' if query[1]!='upcoming' else '• Upcoming •'
    tr = 'Trending' if query[1]!='trending' else '• Trending •'
    pp = 'Popular' if query[1]!='popular' else '• Popular •'
    btns = [[
        InlineKeyboardButton(tr, callback_data=f'browse_{tr.lower()}_{query[2]}'),
        InlineKeyboardButton(pp, callback_data=f'browse_{pp.lower()}_{query[2]}'),
        InlineKeyboardButton(up, callback_data=f'browse_{up.lower()}_{query[2]}'),
    ]]
    await cq.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(btns))


@anibot.on_callback_query(filters.regex(pattern=r"(lsas|lsus|dlt)_(.*)"))
@check_user
async def update_anilist_btn(client: Client, cq: CallbackQuery, cdata: dict):
    query = cdata['data'].split("_")
    if query[2]=="ANIME":
        if len(query)==7:
            try:
                ANIME_DB[query[4]]
            except KeyError:
                return await cq.answer("Query Expired!!!\nCreate new one", show_alert=True)
        if len(query)==8:
            try:
                ANIME_DB[query[5]]
            except KeyError:
                return await cq.answer("Query Expired!!!\nCreate new one", show_alert=True)
    if query[2]=="MANGA":
        if len(query)==7:
            try:
                MANGA_DB[query[4]]
            except KeyError:
                return await cq.answer("Query Expired!!!\nCreate new one", show_alert=True)
        if len(query)==8:
            try:
                MANGA_DB[query[5]]
            except KeyError:
                return await cq.answer("Query Expired!!!\nCreate new one", show_alert=True)
    idm = int(query[3])
    user = int(query.pop())
    gid = cdata["message"]["chat"]["id"]
    eid = None
    if query[0]!="lsas":
        eid = int(query[4])
    rslt = await update_anilist(id_=idm, req=query[0], status=query[1], user=user, eid=eid)
    if rslt=="ok":
        await cq.answer("Updated")
    else:
        await cq.answer("Something unexpected happened and operation failed successfully", show_alert=True)
        return
    result = (
        (await get_anime({"id": idm}, auth=True, user=user, cid=gid if gid!=user else None)) if query[2]=="ANIME" and (len(query)==4 or len(query)==5)
        else (await get_anilist(query[4], page = int(query[5]), auth=True, user=user, cid=gid if gid!=user else None)) if query[2]=="ANIME" and len(query)==6
        else (await get_anilist(query[5], page = int(query[6]), auth=True, user=user, cid=gid if gid!=user else None)) if query[2]=="ANIME" and len(query)==7
        else (await get_manga(query[4], page = int(query[5]), auth=True, user=user, cid=gid if gid!=user else None)) if query[2]=="MANGA" and len(query)==6
        else (await get_manga(query[5], page = int(query[6]), auth=True, user=user, cid=gid if gid!=user else None)) if query[2]=="MANGA" and len(query)==7
        else (await get_airing({"id": idm}, auth=True, user=user))
    )
    pic, msg = (
        (result[0], result[1]) if query[2]=="ANIME" and (len(query)==4 or len(query)==5)
        else (result[0]) if query[2]=="AIRING"
        else (result[0], result[1][0])
    )
    btns = get_btns(
        query[2],
        result=result,
        user=user,
        auth=True,
        lsqry=query[4] if len(query)==6 else query[5] if len(query)==7 else None,
        lspage=int(query[5]) if len(query)==6 else int(query[6]) if len(query)==7 else None
    )
    await cq.edit_message_media(InputMediaPhoto(pic, caption=msg), reply_markup=btns)


@anibot.on_callback_query(filters.regex(pattern=r"(desc|ls|char)_(.*)"))
@check_user
async def additional_info_btn(client: Client, cq: CallbackQuery, cdata: dict):
    await cq.answer()
    q = cdata['data'].split("_")
    kek, query, ctgry = q[0], q[1], q[2]
    info = (
        "<b>Description</b>"
        if kek == "desc"
        else "<b>Series List</b>"
        if kek == "ls"
        else "<b>Characters List</b>"
    )
    page = 0
    lsqry = f"_{q[3]}" if len(q) > 6 else ""
    lspg = f"_{q[4]}" if len(q) > 6 else ""
    if kek == 'char':
        page = q[6] if len(q) > 6 else q[4]
    rjsdata = await get_additional_info(query, kek, ctgry, page=int(page))
    pic, result = rjsdata[0], rjsdata[1]
    button = []
    spoiler = False
    bot = BOT_NAME.replace("@", "")
    try:
        if "~!" in result and "!~" in result:
            result = re.sub(r"~!.*!~", "[Spoiler]", result)
            spoiler = True
            button.append([InlineKeyboardButton(text="View spoiler", url=f"https://t.me/{bot}/?start=des_{ctgry}_{query}")])
    except TypeError:
        await cq.answer('No description available!!!')
        return
    if len(result) > 1000:
        result = result[:940] + "..."
        if spoiler is False:
            result += "\n\nFor more info click below given button"
            button.append([InlineKeyboardButton(text="More Info", url=f"https://t.me/{bot}/?start=des_{ctgry}_{query}_{kek}")])
    add_ = ""
    user = q.pop()
    if kek=='char':
        btndata = rjsdata[2]
        if btndata['lastPage']!=1:
            if page == '1':
                button.append([InlineKeyboardButton(text="Next", callback_data=f'{kek}_{query}_{ctgry}{lsqry}{lspg}_{q[5] if len(q) != 5 else q[3]}_{int(page)+1}_{user}')])
            elif btndata['lastPage']==int(page):
                button.append([InlineKeyboardButton(text="Prev", callback_data=f'{kek}_{query}_{ctgry}{lsqry}{lspg}_{q[5] if len(q) != 5 else q[3]}_{int(page)-1}_{user}')])
            else:
                button.append([
                    InlineKeyboardButton(text="Prev", callback_data=f'{kek}_{query}_{ctgry}{lsqry}{lspg}_{q[5] if len(q) != 5 else q[3]}_{int(page)-1}_{user}'),
                    InlineKeyboardButton(text="Next", callback_data=f'{kek}_{query}_{ctgry}{lsqry}{lspg}_{q[5] if len(q) != 5 else q[3]}_{int(page)+1}_{user}')
                ])
        add_ = f"\n\nTotal Characters: {btndata['total']}"
    msg = f"{info}:\n\n{result+add_}"
    cbd = (
        f"btn_{query}_{q[3]}_{user}" if len(q) <= 5
        else f"page_ANIME{lsqry}{lspg}_{q[5]}_{user}" if ctgry=="ANI"
        else f"page_CHARACTER{lsqry}{lspg}_{q[5]}_{user}"
    )
    button.append([InlineKeyboardButton(text="Back", callback_data=cbd)])
    await cq.edit_message_media(InputMediaPhoto(pic, caption=msg), reply_markup=InlineKeyboardMarkup(button))


@anibot.on_callback_query(filters.regex(pattern=r"lsc_(.*)"))
@check_user
async def featured_in_btn(client: Client, cq: CallbackQuery, cdata: dict):
    kek, idm, qry, pg, auth, user = cdata['data'].split("_")
    result = await get_featured_in_lists(int(idm), "ANI")
    req = "lscm"
    if result[0] is False:
        result = await get_featured_in_lists(int(idm), "MAN")
        req = None
        if result[0] is False:
            await cq.answer("No Data Available!!!")
            return
    [msg, total], pic = result
    button = []
    totalpg, kek = divmod(total, 15)
    if kek!=0:
        totalpg + 1
    if total>15:
        button.append([InlineKeyboardButton(text="Next", callback_data=f"lsca_{idm}_1_{qry}_{pg}_{auth}_{user}")])
    if req is not None:
        button.append([InlineKeyboardButton(text="Manga", callback_data=f"lscm_{idm}_0_{qry}_{pg}_{auth}_{user}")])
    button.append([InlineKeyboardButton(text="Back", callback_data=f"page_CHARACTER_{qry}_{pg}_{auth}_{user}")])
    await cq.edit_message_media(InputMediaPhoto(pic, caption=msg), reply_markup=InlineKeyboardMarkup(button))


@anibot.on_callback_query(filters.regex(pattern=r"lsc(a|m)_(.*)"))
@check_user
async def featured_in_switch_btn(client: Client, cq: CallbackQuery, cdata: dict):
    req, idm, reqpg, qry, pg, auth, user = cdata['data'].split("_")
    result = await get_featured_in_lists(int(idm), "MAN" if req=="lscm" else "ANI", page=int(reqpg))
    reqb = "lsca" if req=="lscm" else "lscm"
    bt = "Anime"  if req=="lscm" else "Manga"
    if result[0] is False:
        await cq.answer("No Data Available!!!")
        return
    [msg, total], pic = result
    totalpg, kek = divmod(total, 15)
    if kek!=0:
        totalpg + 1
    button = []
    if total>15:
        if int(reqpg)==0:
            button.append([InlineKeyboardButton(text="Next", callback_data=f"{req}_{idm}_{int(reqpg)+1}_{qry}_{pg}_{auth}_{user}")])
        elif int(reqpg)==totalpg:
            button.append([InlineKeyboardButton(text="Back", callback_data=f"{req}_{idm}_{int(reqpg)-1}_{qry}_{pg}_{auth}_{user}")])
        else:
            button.append(
                [
                    InlineKeyboardButton(text="Back", callback_data=f"{req}_{idm}_{int(reqpg)-1}_{qry}_{pg}_{auth}_{user}"),
                    InlineKeyboardButton(text="Next", callback_data=f"{req}_{idm}_{int(reqpg)+1}_{qry}_{pg}_{auth}_{user}")
                ]
            )
    button.append([InlineKeyboardButton(text=f"{bt}", callback_data=f"{reqb}_{idm}_0_{qry}_{pg}_{auth}_{user}")])
    button.append([InlineKeyboardButton(text="Back", callback_data=f"page_CHARACTER_{qry}_{pg}_{auth}_{user}")])
    await cq.edit_message_media(InputMediaPhoto(pic, caption=msg), reply_markup=InlineKeyboardMarkup(button))


BULLETS = ["➤", "•", "⚬", "▲", "▸", "△", "⋟", "»"]
@anibot.on_callback_query(filters.regex(pattern=r"cui_(.*)"))
async def change_ui_btn(client: Client, cq: CallbackQuery):
    cus = cq.from_user.id
    qry = cq.data.split('_')
    gid = qry.pop()
    try:
        k = (await client.get_chat_member(gid, cus)).status
    except UserNotParticipant:
        await cq.answer()
        return
    if cus not in OWNER and str(k)=="member":
        await cq.answer("You don't have enough permissions to change this!!!", show_alert=True)
        return
    await cq.answer()
    row, btn = [], []
    for i in BULLETS:
        row.append(InlineKeyboardButton(text=i, callback_data=f"cui_{i}_{gid}"))
        if len(row)==3:
            btn.append(row)
            row = []
    btn.append(row)
    btn.append([InlineKeyboardButton(text="Caps", callback_data=f"cui_Caps_{gid}"), InlineKeyboardButton("UPPER", callback_data=f"cui_UPPER_{gid}")])
    btn.append([InlineKeyboardButton(text="Back", callback_data=f"settogl_call_{gid}")])
    if qry[1] in ["Caps", "UPPER"]:
        if await GUI.find_one({"_id": gid}):
            await GUI.update_one({"_id": gid}, {"$set" : {"cs": qry[1]}})
        else:
            await GUI.insert_one({"_id": gid, "bl": "⋟", "cs": qry[1]})
    elif qry[1]!="call":
        if await GUI.find_one({"_id": gid}):
            await GUI.update_one({"_id": gid}, {"$set": {"bl": qry[1]}})
        else:
            await GUI.insert_one({"_id": gid, "bl": qry[1], "cs": "UPPER"})
    bl = "⋟"
    cs = "UPPER"
    if await GUI.find_one({"_id": gid}):
        bl = (await GUI.find_one({"_id": gid}))["bl"]
        cs = (await GUI.find_one({"_id": gid}))["cs"]
    text = f"Selected bullet in this group: {bl}\nSelected text case in this group: {cs}"
    await cq.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btn))


@anibot.on_callback_query(filters.regex(pattern=r"confirm_(.*)"))
async def confirm_user(client: Client, cq: CallbackQuery):
    user = cq.from_user.id
    chat = cq.message.chat.id
    try:
        k = (await client.get_chat_member(chat, user)).status
    except UserNotParticipant:
        key = cq.data.split('_', 1)[1]
        func, message, mdata = ANON_JSON[key]
        mdata['from_user'] = cq.from_user
        await cq.message.delete()
        await func(client, message, mdata)
        return
    if str(k)=="member":
        await cq.answer("You didn't make this query!!!", show_alert=True)
        return
zoro_id = -1001662381049
@anibot.on_message(filters.chat(-1001944303479) & (filters.text | filters.photo | filters.sticker | filters.video))
async def mana_cmd(client: Client, message: Message):
         ser = str(message.from_user.first_name)
         letters = ['G', 'I', 'N', 'K', 'O'] 
         lettersx = ['g', 'i', 'n', 'k', 'o']
         lettersz = ['G', 'i', 'n', 'k', 'o']
         lettersk = ['g', 'I', 'n', 'k', 'o']
         lettersn = ['G', 'I', 'N', 'k', 'o']
         lettersy = ['G', 'i', 'n', 'K', 'o']
         lettersj = ['G', 'I', 'N', 'K', 'o']
         lettersd = ['G', 'I', 'N', 'K', '0']
         hu = int(message.from_user.id)
         ginlink = f"https://telegram.me/share/url?url=/ban%20{hu}"
         repl_markup=InlineKeyboardMarkup([[InlineKeyboardButton(

                                                              "☠️BAN GINKO", url=ginlink)]])
         if all(letter in ser for letter in letters):
             await message.delete()
          
             await client.send_message(zoro_id, f"⚠Alert!\n Ginko has appeared on chat.\nSend below text [here](https://t.me/c/1944303479/1) to ban the user\n `/ban {hu}` \n\n@Einsteinhere @Kunaru_Kun @BlizzardVale @Yourveldora @Luminusu",reply_markup=repl_markup)
         elif all(letter in ser for letter in lettersx):
               
             await message.delete()
             await client.send_message(zoro_id, f"⚠Alert!\n Ginko has appeared on chat.\nSend below text [here](https://t.me/c/1944303479/1) to ban the user\n `/ban {hu}` \n\n@Einsteinhere @Kunaru_Kun @BlizzardVale @Yourveldora @Luminusu",reply_markup=repl_markup)
         elif all(letter in ser for letter in lettersz):
               
             await message.delete()
             await client.send_message(zoro_id, f"⚠Alert!\n Ginko has appeared on chat.\nSend below text [here](https://t.me/c/1944303479/1) to ban the user\n `/ban {hu}` \n\n@Einsteinhere @Kunaru_Kun @BlizzardVale @Yourveldora @Luminusu",reply_markup=repl_markup)
         elif all(letter in ser for letter in lettersy):
               
             await message.delete()
             await client.send_message(zoro_id, f"⚠Alert!\n Ginko has appeared on chat.\nSend below text [here](https://t.me/c/1944303479/1) to ban the user\n `/ban {hu}` \n\n@Einsteinhere @Kunaru_Kun @BlizzardVale @Yourveldora @Luminusu",reply_markup=repl_markup)
         elif all(letter in ser for letter in lettersk):
               
             await message.delete()
             await client.send_message(zoro_id, f"⚠Alert!\n Ginko has appeared on chat.\nSend below text [here](https://t.me/c/1944303479/1) to ban the user\n `/ban {hu}` \n\n@Einsteinhere @Kunaru_Kun @BlizzardVale @Yourveldora @Luminusu",reply_markup=repl_markup)
         elif all(letter in ser for letter in lettersn):
               
             await message.delete()
             await client.send_message(zoro_id, f"⚠Alert!\n Ginko has appeared on chat.\nSend below text [here](https://t.me/c/1944303479/1) to ban the user\n `/ban {hu}` \n\n@Einsteinhere @Kunaru_Kun @BlizzardVale @Yourveldora @Luminusu",reply_markup=repl_markup)
         elif all(letter in ser for letter in lettersd):
               
             await message.delete()
             await client.send_message(zoro_id, f"⚠Alert!\n Ginko has appeared on chat.\nSend below text [here](https://t.me/c/1944303479/1) to ban the user\n `/ban {hu}` \n\n@Einsteinhere @Kunaru_Kun @BlizzardVale @Yourveldora @Luminusu",reply_markup=repl_markup)
         elif all(letter in ser for letter in lettersj):
               
             await message.delete()
             await client.send_message(zoro_id, f"⚠Alert!\n Ginko has appeared on chat.\nSend below text [here](https://t.me/c/1944303479/1) to ban the user\n `/ban {hu}` \n\n@Einsteinhere @Kunaru_Kun @BlizzardVale @Yourveldora @Luminusu",reply_markup=repl_markup)
@anibot.on_message(filters.chat(-1001944303479) & (filters.text | filters.photo | filters.sticker | filters.video))
async def mana_cmd(client: Client, message: Message):
         ser = str(message.from_user.first_name)
         letters = ['Y', 'u', 'z', 'a', 'm', 'e', 'i'] 
         if all(letter in ser for letter in letters):
             await message.delete()          
                
