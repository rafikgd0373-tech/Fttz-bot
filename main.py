import discord
import json
import os
import random
import time
import aiohttp
import asyncio
from datetime import datetime
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageOps
from io import BytesIO

# ─────────────────────────────────────────────
#  إعدادات البوت
# ─────────────────────────────────────────────
PREFIX = "!"
TOKEN = os.environ.get("TOKEN", "YOUR_TOKEN_HERE")

WELCOME_CHANNEL_ID = 1470539807074549850
GOODBYE_CHANNEL_ID = 1470539840314671134

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ─────────────────────────────────────────────
#  حفظ البيانات JSON
# ─────────────────────────────────────────────
DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(data, user_id):
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "mood": 0,
            "xp": 0,
            "level": 1,
            "last_collect": 0,
            "last_work": 0,
            "chat_messages": 0,
            "voice_minutes": 0,
            "inventory": []
        }
    return data[uid]

# ─────────────────────────────────────────────
#  نظام اللفل والـ XP
# ─────────────────────────────────────────────
def xp_needed(level):
    return level * 100

def add_xp(user_data, amount):
    user_data["xp"] += amount
    while user_data["xp"] >= xp_needed(user_data["level"]):
        user_data["xp"] -= xp_needed(user_data["level"])
        user_data["level"] += 1
        return True  # leveled up
    return False

# ─────────────────────────────────────────────
#  الشوب الجزائري
# ─────────────────────────────────────────────
SHOP_ITEMS = [
    # 🍽️ أكلات
    {"id": "couscous",    "name": "🍲 كسكسي",             "price": 500,    "category": "أكل"},
    {"id": "chorba",      "name": "🥣 شوربة فريك",         "price": 300,    "category": "أكل"},
    {"id": "brik",        "name": "🥟 بريك بالبيض",        "price": 200,    "category": "أكل"},
    {"id": "rechta",      "name": "🍜 رشتة",               "price": 400,    "category": "أكل"},
    {"id": "mhajeb",      "name": "🫓 مهاجب",              "price": 150,    "category": "أكل"},
    {"id": "dolma",       "name": "🫑 دولمة",              "price": 350,    "category": "أكل"},
    {"id": "makroud",     "name": "🍮 مقروض",              "price": 100,    "category": "أكل"},
    {"id": "baklawa",     "name": "🍯 بقلاوة",             "price": 250,    "category": "أكل"},
    # ☕ مشروبات
    {"id": "qahwa",       "name": "☕ قهوة",               "price": 50,     "category": "مشروب"},
    {"id": "mint_tea",    "name": "🍵 شاي بالنعناع",       "price": 80,     "category": "مشروب"},
    {"id": "leben",       "name": "🥛 لبن",                "price": 60,     "category": "مشروب"},
    {"id": "limonade",    "name": "🍋 ليمونادة",           "price": 70,     "category": "مشروب"},
    # 🏠 أشياء يومية
    {"id": "phone",       "name": "📱 هاتف",               "price": 15000,  "category": "يومي"},
    {"id": "laptop",      "name": "💻 لابتوب",             "price": 50000,  "category": "يومي"},
    {"id": "tv",          "name": "📺 تلفزيون",            "price": 20000,  "category": "يومي"},
    {"id": "fridge",      "name": "🧊 ثلاجة",              "price": 18000,  "category": "يومي"},
    {"id": "washing_m",   "name": "🫧 غسالة",              "price": 22000,  "category": "يومي"},
    # 🚗 سيارات
    {"id": "peugeot",     "name": "🚗 بيجو 206",           "price": 300000, "category": "سيارة"},
    {"id": "renault",     "name": "🚙 رونو كليو",          "price": 350000, "category": "سيارة"},
    {"id": "mercedes",    "name": "🏎️ مرسيدس",            "price": 900000, "category": "سيارة"},
    {"id": "bus",         "name": "🚌 حافلة",              "price": 500000, "category": "سيارة"},
    # 🏠 عقارات
    {"id": "studio",      "name": "🏠 ستوديو",             "price": 1000000, "category": "عقار"},
    {"id": "f3",          "name": "🏡 شقة F3",             "price": 3000000, "category": "عقار"},
    {"id": "villa",       "name": "🏰 فيلا",               "price": 9000000, "category": "عقار"},
    # 🏪 محلات
    {"id": "cafe",        "name": "☕ مقهى",               "price": 500000,  "category": "محل"},
    {"id": "restaurant",  "name": "🍽️ مطعم",              "price": 800000,  "category": "محل"},
    {"id": "shop",        "name": "🏪 دكان",               "price": 200000,  "category": "محل"},
    {"id": "pharmacy",    "name": "💊 صيدلية",             "price": 600000,  "category": "محل"},
]

# ─────────────────────────────────────────────
#  مولد الكارد (profile card)
# ─────────────────────────────────────────────
async def fetch_avatar(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status == 200:
                return await r.read()
    return None

def make_profile_card(username, avatar_bytes, level, xp, xp_needed_val, mood, rank, mode="chat"):
    W, H = 700, 220
    bg_color = (18, 18, 30)
    accent = (130, 90, 255)
    text_color = (255, 255, 255)
    sub_color = (180, 180, 200)
    bar_bg = (50, 50, 70)

    img = Image.new("RGBA", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    # gradient side bar
    for i in range(H):
        r = int(accent[0] * (1 - i/H))
        g = int(accent[1] * (1 - i/H))
        b = int(accent[2])
        draw.rectangle([(0, i), (6, i)], fill=(r, g, b))

    # avatar
    if avatar_bytes:
        av = Image.open(BytesIO(avatar_bytes)).convert("RGBA").resize((90, 90))
        mask = Image.new("L", (90, 90), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 89, 89), fill=255)
        av.putalpha(mask)
        img.paste(av, (20, 65), av)

        # avatar border
        border_mask = Image.new("L", (94, 94), 0)
        ImageDraw.Draw(border_mask).ellipse((0, 0, 93, 93), fill=255)
        border_img = Image.new("RGBA", (94, 94), accent + (255,))
        img.paste(border_img, (18, 63), border_mask)
        img.paste(av, (20, 65), av)

    # username
    try:
        font_big  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        font_med  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        font_sm   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font_big = font_med = font_sm = ImageFont.load_default()

    draw.text((125, 30), username, font=font_big, fill=text_color)

    # rank badge
    rank_txt = f"#{rank}"
    draw.rounded_rectangle([(125, 65), (165, 88)], radius=8, fill=accent)
    draw.text((130, 68), rank_txt, font=font_sm, fill=(255,255,255))

    # level
    lv_txt = f"Level {level}"
    draw.text((180, 65), lv_txt, font=font_med, fill=accent)

    # XP bar
    bar_x, bar_y = 125, 100
    bar_w, bar_h = 540, 16
    draw.rounded_rectangle([(bar_x, bar_y), (bar_x+bar_w, bar_y+bar_h)], radius=8, fill=bar_bg)
    xp_ratio = min(xp / xp_needed_val, 1.0)
    if xp_ratio > 0:
        draw.rounded_rectangle([(bar_x, bar_y), (bar_x+int(bar_w*xp_ratio), bar_y+bar_h)], radius=8, fill=accent)
    xp_txt = f"XP: {xp:,} / {xp_needed_val:,}"
    draw.text((bar_x, bar_y + 22), xp_txt, font=font_sm, fill=sub_color)

    # mood
    mood_txt = f"💰 m00d: {mood:,}"
    draw.text((125, 155), mood_txt, font=font_med, fill=(255, 215, 0))

    # mode label
    mode_label = "🗨️ Top Chat" if mode == "chat" else "🔊 Top Voice"
    draw.text((500, 155), mode_label, font=font_sm, fill=sub_color)

    # footer line
    draw.line([(20, 200), (680, 200)], fill=(50,50,70), width=1)
    draw.text((20, 205), "m00d Bot • Server Economy", font=font_sm, fill=(80,80,100))

    buf = BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf

# ─────────────────────────────────────────────
#  أحداث البوت
# ─────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"✅ البوت شغال: {bot.user}")

@bot.event
async def on_member_join(member):
    ch = bot.get_channel(WELCOME_CHANNEL_ID)
    if ch:
        embed = discord.Embed(
            title="🎉 أهلاً وسهلاً!",
            description=f"مرحباً بك {member.mention} في السيرفر! 🌟\nWelcome to the server!",
            color=0x8A5CFF
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="👤 العضو", value=member.name, inline=True)
        embed.add_field(name="🔢 رقم العضو", value=f"#{member.guild.member_count}", inline=True)
        embed.set_footer(text=f"انضم في {datetime.now().strftime('%Y-%m-%d')}")
        await ch.send(embed=embed)

@bot.event
async def on_member_remove(member):
    ch = bot.get_channel(GOODBYE_CHANNEL_ID)
    if ch:
        embed = discord.Embed(
            title="👋 وداعاً!",
            description=f"غادر {member.name} السيرفر.\nGoodbye {member.name}, we'll miss you!",
            color=0xFF5555
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await ch.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.strip().lower()

    # ─── تحيات عربية وإنجليزية ───
    arabic_greets = ["هلا", "اهلا", "أهلا", "سلام عليكم", "السلام عليكم",
                     "السلام عليكم ورحمة الله وبركاته",
                     "سلام عليكم ورحمة الله وبركاته"]
    english_greets = ["hi", "hello", "hi guys", "hey", "hey guys"]

    for g in arabic_greets:
        if content == g:
            await message.channel.send(f"وعليكم السلام ورحمة الله وبركاته {message.author.mention}! 👋🌸")
            break
    else:
        for g in english_greets:
            if content == g:
                await message.channel.send(f"Hello {message.author.mention}! Welcome 👋😊")
                break

    # ─── XP من الرسائل ───
    data = load_data()
    user = get_user(data, message.author.id)
    user["chat_messages"] = user.get("chat_messages", 0) + 1
    leveled = add_xp(user, random.randint(5, 15))
    save_data(data)
    if leveled:
        await message.channel.send(
            f"🎉 مبروك {message.author.mention}! وصلت للفل **{user['level']}**! 🚀"
        )

    await bot.process_commands(message)

# ─────────────────────────────────────────────
#  أوامر الـ m00d
# ─────────────────────────────────────────────
@bot.command(name="collect")
async def collect(ctx):
    data = load_data()
    user = get_user(data, ctx.author.id)
    now = time.time()
    cooldown = 30 * 60  # 30 دقيقة

    remaining = cooldown - (now - user["last_collect"])
    if remaining > 0:
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        embed = discord.Embed(
            title="⏳ انتظر شوية!",
            description=f"تقدر تجمع مرة ثانية بعد **{mins}** دقيقة و **{secs}** ثانية.",
            color=0xFF9900
        )
        await ctx.send(embed=embed)
        return

    earned = random.randint(100, 1000)
    user["mood"] += earned
    user["last_collect"] = now
    save_data(data)

    embed = discord.Embed(
        title="💰 تم الجمع!",
        description=f"جمعت **{earned:,} m00d** 🎉\nرصيدك الحالي: **{user['mood']:,} m00d**",
        color=0x00FF88
    )
    await ctx.send(embed=embed)

@bot.command(name="balance", aliases=["bal"])
async def balance(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = load_data()
    user = get_user(data, member.id)
    embed = discord.Embed(
        title=f"💳 رصيد {member.display_name}",
        description=f"**{user['mood']:,} m00d** 💰",
        color=0x8A5CFF
    )
    await ctx.send(embed=embed)

@bot.command(name="work")
async def work(ctx):
    data = load_data()
    user = get_user(data, ctx.author.id)
    now = time.time()
    cooldown = 60 * 60  # ساعة

    remaining = cooldown - (now - user.get("last_work", 0))
    if remaining > 0:
        mins = int(remaining // 60)
        embed = discord.Embed(
            title="⏳ تعبت من الشغل!",
            description=f"ارتح **{mins}** دقيقة ثم اشتغل مرة ثانية.",
            color=0xFF9900
        )
        await ctx.send(embed=embed)
        return

    jobs = [
        ("👨‍🍳 طباخ", "طبخت كسكسي للسيرفر"),
        ("🚗 سائق تاكسي", "وصلت زبائن كثار"),
        ("💻 مبرمج", "كتبت كود للباس"),
        ("🏗️ بناء", "بنيت جدار كامل"),
        ("🛒 بياع", "بعت بضاعة في السوق"),
        ("📦 ساعي", "وزعت الطرود"),
    ]
    job_name, desc = random.choice(jobs)
    earned = random.randint(10000, 100000)
    user["mood"] += earned
    user["last_work"] = now
    save_data(data)

    embed = discord.Embed(
        title=f"💼 {job_name}",
        description=f"{desc}\nكسبت **{earned:,} m00d** 💰\nرصيدك: **{user['mood']:,} m00d**",
        color=0x00CCFF
    )
    await ctx.send(embed=embed)

@bot.command(name="leaderboard", aliases=["lb"])
async def leaderboard(ctx):
    data = load_data()
    guild_members = {str(m.id): m for m in ctx.guild.members}
    sorted_users = sorted(
        [(uid, d) for uid, d in data.items() if uid in guild_members],
        key=lambda x: x[1].get("mood", 0),
        reverse=True
    )[:10]

    embed = discord.Embed(title="🏆 أغنى أعضاء السيرفر - m00d", color=0xFFD700)
    medals = ["🥇", "🥈", "🥉"] + ["4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    desc = ""
    for i, (uid, d) in enumerate(sorted_users):
        member = guild_members.get(uid)
        name = member.display_name if member else f"User#{uid}"
        desc += f"{medals[i]} **{name}** — {d.get('mood',0):,} m00d\n"
    embed.description = desc or "ما في بيانات بعد!"
    await ctx.send(embed=embed)

# ─── أوامر الأدمن ───
@bot.command(name="add")
@commands.has_permissions(administrator=True)
async def add_mood(ctx, member: discord.Member, amount: int):
    data = load_data()
    user = get_user(data, member.id)
    user["mood"] += amount
    save_data(data)
    embed = discord.Embed(
        description=f"✅ تمت إضافة **{amount:,} m00d** لـ {member.mention}\nرصيده: **{user['mood']:,} m00d**",
        color=0x00FF88
    )
    await ctx.send(embed=embed)

@bot.command(name="remove")
@commands.has_permissions(administrator=True)
async def remove_mood(ctx, member: discord.Member, amount: int):
    data = load_data()
    user = get_user(data, member.id)
    user["mood"] = max(0, user["mood"] - amount)
    save_data(data)
    embed = discord.Embed(
        description=f"✅ تم سحب **{amount:,} m00d** من {member.mention}\nرصيده: **{user['mood']:,} m00d**",
        color=0xFF5555
    )
    await ctx.send(embed=embed)

@bot.command(name="set")
@commands.has_permissions(administrator=True)
async def set_mood(ctx, member: discord.Member, amount: int):
    data = load_data()
    user = get_user(data, member.id)
    user["mood"] = amount
    save_data(data)
    embed = discord.Embed(
        description=f"✅ تم تعيين رصيد {member.mention} على **{amount:,} m00d**",
        color=0x8A5CFF
    )
    await ctx.send(embed=embed)

# ─────────────────────────────────────────────
#  الشوب
# ─────────────────────────────────────────────
@bot.command(name="shop")
async def shop(ctx, category: str = None):
    categories = {}
    for item in SHOP_ITEMS:
        cat = item["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)

    if category is None:
        embed = discord.Embed(title="🏪 شوب السيرفر", color=0x8A5CFF)
        embed.description = "اكتب `!shop <فئة>` لتشوف الأشياء\n\n"
        for cat in categories:
            embed.add_field(name=f"📂 {cat}", value=f"`!shop {cat}`", inline=True)
        embed.set_footer(text="للشراء: !buy <id>")
        await ctx.send(embed=embed)
        return

    items = None
    for cat, itms in categories.items():
        if cat == category or category in cat:
            items = itms
            break

    if not items:
        await ctx.send("❌ الفئة غير موجودة! اكتب `!shop` لتشوف الفئات.")
        return

    embed = discord.Embed(title=f"🏪 {category}", color=0x8A5CFF)
    for item in items:
        embed.add_field(
            name=item["name"],
            value=f"💰 **{item['price']:,} m00d**\n`!buy {item['id']}`",
            inline=True
        )
    await ctx.send(embed=embed)

@bot.command(name="buy")
async def buy(ctx, item_id: str):
    item = next((i for i in SHOP_ITEMS if i["id"] == item_id), None)
    if not item:
        await ctx.send("❌ العنصر غير موجود! اكتب `!shop` لتشوف الأشياء.")
        return

    data = load_data()
    user = get_user(data, ctx.author.id)

    if user["mood"] < item["price"]:
        needed = item["price"] - user["mood"]
        await ctx.send(f"❌ ما عندكش فلوس كافية! تحتاج **{needed:,} m00d** أكثر.")
        return

    user["mood"] -= item["price"]
    if "inventory" not in user:
        user["inventory"] = []
    user["inventory"].append(item_id)
    save_data(data)

    embed = discord.Embed(
        title="✅ تم الشراء!",
        description=f"اشتريت **{item['name']}** بـ **{item['price']:,} m00d**\nرصيدك: **{user['mood']:,} m00d**",
        color=0x00FF88
    )
    await ctx.send(embed=embed)

@bot.command(name="inventory", aliases=["inv"])
async def inventory(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = load_data()
    user = get_user(data, member.id)
    inv = user.get("inventory", [])

    if not inv:
        await ctx.send(f"🎒 مخزن {member.display_name} فاضي!")
        return

    embed = discord.Embed(title=f"🎒 مخزن {member.display_name}", color=0x8A5CFF)
    item_counts = {}
    for iid in inv:
        item_counts[iid] = item_counts.get(iid, 0) + 1
    desc = ""
    for iid, count in item_counts.items():
        item = next((i for i in SHOP_ITEMS if i["id"] == iid), None)
        if item:
            desc += f"{item['name']} x{count}\n"
    embed.description = desc
    await ctx.send(embed=embed)

# ─────────────────────────────────────────────
#  أوامر الـ XP واللفل (مثل ProBot)
# ─────────────────────────────────────────────
@bot.command(name="p")
async def profile_chat(ctx, member: discord.Member = None):
    """Top Chat Profile Card"""
    member = member or ctx.author
    data = load_data()
    user = get_user(data, member.id)

    # ترتيب الـ chat
    guild_members_ids = {str(m.id) for m in ctx.guild.members}
    sorted_chat = sorted(
        [(uid, d) for uid, d in data.items() if uid in guild_members_ids],
        key=lambda x: x[1].get("chat_messages", 0),
        reverse=True
    )
    rank = next((i+1 for i, (uid, _) in enumerate(sorted_chat) if uid == str(member.id)), 999)

    avatar_bytes = await fetch_avatar(str(member.display_avatar.url))
    buf = make_profile_card(
        member.display_name, avatar_bytes,
        user["level"], user["xp"], xp_needed(user["level"]),
        user["mood"], rank, mode="chat"
    )
    await ctx.send(file=discord.File(buf, "profile.png"))

@bot.command(name="T")
async def profile_voice(ctx, member: discord.Member = None):
    """Top Voice Profile Card"""
    member = member or ctx.author
    data = load_data()
    user = get_user(data, member.id)

    guild_members_ids = {str(m.id) for m in ctx.guild.members}
    sorted_voice = sorted(
        [(uid, d) for uid, d in data.items() if uid in guild_members_ids],
        key=lambda x: x[1].get("voice_minutes", 0),
        reverse=True
    )
    rank = next((i+1 for i, (uid, _) in enumerate(sorted_voice) if uid == str(member.id)), 999)

    avatar_bytes = await fetch_avatar(str(member.display_avatar.url))
    buf = make_profile_card(
        member.display_name, avatar_bytes,
        user["level"], user["xp"], xp_needed(user["level"]),
        user["mood"], rank, mode="voice"
    )
    await ctx.send(file=discord.File(buf, "profile_voice.png"))

@bot.command(name="c")
async def top_voice(ctx):
    """Top Voice Leaderboard"""
    data = load_data()
    guild_members = {str(m.id): m for m in ctx.guild.members}
    sorted_voice = sorted(
        [(uid, d) for uid, d in data.items() if uid in guild_members],
        key=lambda x: x[1].get("voice_minutes", 0),
        reverse=True
    )[:10]

    embed = discord.Embed(title="🔊 Top Voice - أكثر الناس في الفويس", color=0x00CCFF)
    medals = ["🥇","🥈","🥉"] + ["4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    desc = ""
    for i, (uid, d) in enumerate(sorted_voice):
        m = guild_members.get(uid)
        name = m.display_name if m else f"User#{uid}"
        mins = d.get("voice_minutes", 0)
        hours = mins // 60
        desc += f"{medals[i]} **{name}** — {hours}h {mins%60}m\n"
    embed.description = desc or "ما في بيانات بعد!"
    await ctx.send(embed=embed)

@bot.command(name="top")
async def top_chat(ctx):
    """Top Chat Leaderboard"""
    data = load_data()
    guild_members = {str(m.id): m for m in ctx.guild.members}
    sorted_chat = sorted(
        [(uid, d) for uid, d in data.items() if uid in guild_members],
        key=lambda x: x[1].get("chat_messages", 0),
        reverse=True
    )[:10]

    embed = discord.Embed(title="🗨️ Top Chat - أكثر الناس رسائل", color=0x8A5CFF)
    medals = ["🥇","🥈","🥉"] + ["4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    desc = ""
    for i, (uid, d) in enumerate(sorted_chat):
        member = guild_members.get(uid)
        name = member.display_name if member else f"User#{uid}"
        msgs = d.get("chat_messages", 0)
        desc += f"{medals[i]} **{name}** — {msgs:,} رسالة\n"
    embed.description = desc or "ما في بيانات بعد!"
    await ctx.send(embed=embed)

@bot.command(name="level", aliases=["lvl", "rank"])
async def show_level(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = load_data()
    user = get_user(data, member.id)
    embed = discord.Embed(
        title=f"⭐ لفل {member.display_name}",
        color=0x8A5CFF
    )
    embed.add_field(name="🎯 اللفل", value=f"**{user['level']}**", inline=True)
    embed.add_field(name="✨ XP", value=f"**{user['xp']:,} / {xp_needed(user['level']):,}**", inline=True)
    embed.add_field(name="💰 m00d", value=f"**{user['mood']:,}**", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)

# ─────────────────────────────────────────────
#  تتبع الفويس
# ─────────────────────────────────────────────
voice_join_times = {}

@bot.event
async def on_voice_state_update(member, before, after):
    uid = str(member.id)
    if before.channel is None and after.channel is not None:
        voice_join_times[uid] = time.time()
    elif before.channel is not None and after.channel is None:
        if uid in voice_join_times:
            joined = voice_join_times.pop(uid)
            mins = int((time.time() - joined) / 60)
            if mins > 0:
                data = load_data()
                user = get_user(data, member.id)
                user["voice_minutes"] = user.get("voice_minutes", 0) + mins
                user["mood"] += mins * 10  # 10 m00d كل دقيقة فويس
                save_data(data)

# ─────────────────────────────────────────────
#  أمر المساعدة
# ─────────────────────────────────────────────
@bot.command(name="help", aliases=["مساعدة"])
async def help_cmd(ctx):
    embed = discord.Embed(title="📖 أوامر البوت", color=0x8A5CFF)
    embed.add_field(name="💰 المال (m00d)", value="""
`!collect` — اجمع m00d كل 30 دقيقة
`!work` — اشتغل واكسب 10K-100K m00d
`!balance` — شوف رصيدك
`!leaderboard` — أغنى الأعضاء
""", inline=False)
    embed.add_field(name="🏪 الشوب", value="""
`!shop` — شوف الفئات
`!shop أكل` — شوف الأكلات
`!buy <id>` — اشتري شيء
`!inventory` — مخزنك
""", inline=False)
    embed.add_field(name="⭐ اللفل والـ XP", value="""
`p` — بروفايل كارد (Chat)
`T` — بروفايل كارد (Voice)
`!level` — شوف لفلك
`!top` — Top Chat
`!c` — Top Voice
""", inline=False)
    embed.add_field(name="👑 أدمن فقط", value="""
`!add @يوزر <مبلغ>` — أعطي m00d
`!remove @يوزر <مبلغ>` — اسحب m00d
`!set @يوزر <مبلغ>` — حدد الرصيد
""", inline=False)
    embed.set_footer(text="الترحيب والتوديع تلقائي 🎉")
    await ctx.send(embed=embed)

# ─────────────────────────────────────────────
#  تشغيل البوت
# ─────────────────────────────────────────────
bot.run(TOKEN)
