import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Button, View, Select, Modal, TextInput
import json
import os
import random
import time
import asyncio
from datetime import datetime
from typing import Optional

# ═════════════════════════════════════════════
#  إعدادات البوت
# ═════════════════════════════════════════════
PREFIX = "!"
TOKEN = os.environ.get("TOKEN", "MTQ3MzQ4NjE0OTA5MDgwODEyMg.G9Ud9L.DXqJwAhP0KKJBYkDdpamuuBfKyythGBHupmOd4")
LIME_COLOR = 0x00FF00  # 🟢 لون Lime

WELCOME_CHANNEL_ID = 1470539807074549850
GOODBYE_CHANNEL_ID = 1470539840314671134
TICKET_CATEGORY_ID = 1470541327383920736  # غيّر هذا لـ ID الفئة الصحيحة

TICKET_TYPES = {
    "support": {"name": "🛠️ دعم فني | Technical Support", "emoji": "🛠️"},
    "application": {"name": "📝 تقديم طلب | Application", "emoji": "📝"},
    "report": {"name": "⚠️ بلاغات | Reports", "emoji": "⚠️"},
    "complaint": {"name": "📢 شكوى عن إدارة | Staff Complaint", "emoji": "📢"}
}

# أذكار إسلامية
AZKAR = [
    "سبحان الله وبحمده سبحان الله العظيم",
    "لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير",
    "اللهم صل وسلم على نبينا محمد",
    "أستغفر الله وأتوب إليه",
    "الحمد لله رب العالمين",
    "لا حول ولا قوة إلا بالله",
    "سبحان الله والحمد لله ولا إله إلا الله والله أكبر",
    "اللهم إني أسألك العافية في الدنيا والآخرة",
    "ربنا آتنا في الدنيا حسنة وفي الآخرة حسنة وقنا عذاب النار",
    "اللهم إنك عفو كريم تحب العفو فاعف عني"
]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ═════════════════════════════════════════════
#  حفظ البيانات
# ═════════════════════════════════════════════
DATA_FILE = "data.json"
TICKETS_FILE = "tickets.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_tickets():
    if not os.path.exists(TICKETS_FILE):
        return {}
    with open(TICKETS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_tickets(data):
    with open(TICKETS_FILE, "w", encoding="utf-8") as f:
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

# ═════════════════════════════════════════════
#  XP System
# ═════════════════════════════════════════════
def xp_needed(level):
    return level * 100

def add_xp(user_data, amount):
    user_data["xp"] += amount
    while user_data["xp"] >= xp_needed(user_data["level"]):
        user_data["xp"] -= xp_needed(user_data["level"])
        user_data["level"] += 1
        return True
    return False

# ═════════════════════════════════════════════
#  الشوب الجزائري
# ═════════════════════════════════════════════
SHOP_ITEMS = [
    {"id": "couscous", "name": "🍲 كسكسي", "price": 500, "category": "أكل"},
    {"id": "chorba", "name": "🥣 شوربة فريك", "price": 300, "category": "أكل"},
    {"id": "brik", "name": "🥟 بريك بالبيض", "price": 200, "category": "أكل"},
    {"id": "qahwa", "name": "☕ قهوة", "price": 50, "category": "مشروب"},
    {"id": "mint_tea", "name": "🍵 شاي بالنعناع", "price": 80, "category": "مشروب"},
    {"id": "phone", "name": "📱 هاتف", "price": 15000, "category": "يومي"},
    {"id": "laptop", "name": "💻 لابتوب", "price": 50000, "category": "يومي"},
    {"id": "peugeot", "name": "🚗 بيجو 206", "price": 300000, "category": "سيارة"},
    {"id": "villa", "name": "🏰 فيلا", "price": 9000000, "category": "عقار"},
]

# ═════════════════════════════════════════════
#  نظام التيكتات
# ═════════════════════════════════════════════
class TicketTypeSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="دعم فني | Technical Support",
                description="للمساعدة التقنية | For technical help",
                emoji="🛠️",
                value="support"
            ),
            discord.SelectOption(
                label="تقديم طلب | Application",
                description="تقديم طلب انضمام | Submit application",
                emoji="📝",
                value="application"
            ),
            discord.SelectOption(
                label="بلاغات | Reports",
                description="الإبلاغ عن مشكلة | Report an issue",
                emoji="⚠️",
                value="report"
            ),
            discord.SelectOption(
                label="شكوى عن إدارة | Staff Complaint",
                description="شكوى ضد أحد الإدارة | Complain about staff",
                emoji="📢",
                value="complaint"
            )
        ]
        super().__init__(
            placeholder="اختر نوع التيكت | Select ticket type",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_type_select"
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        ticket_type = self.values[0]
        guild = interaction.guild
        
        # Get or create category
        category = discord.utils.get(guild.categories, name="📩 Tickets")
        if not category:
            category = await guild.create_category("📩 Tickets")
        
        # Check if user already has a ticket
        for channel in category.text_channels:
            if channel.topic and str(interaction.user.id) in channel.topic:
                await interaction.followup.send(
                    f"❌ عندك تيكت مفتوح! | You already have an open ticket!\n{channel.mention}",
                    ephemeral=True
                )
                return
        
        # Get ticket number
        ticket_num = len(category.text_channels) + 1
        
        # Create ticket channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        ticket_info = TICKET_TYPES[ticket_type]
        ticket_channel = await category.create_text_channel(
            name=f"ticket-{ticket_num}",
            overwrites=overwrites,
            topic=f"Ticket by {interaction.user.id} | Type: {ticket_type}"
        )
        
        embed = discord.Embed(
            title=f"🎫 {ticket_info['name']}",
            description=f"مرحباً {interaction.user.mention}!\nHello {interaction.user.mention}!\n\nاشرح مشكلتك وسنساعدك قريباً ✨\nExplain your issue and we'll help you soon!",
            color=LIME_COLOR
        )
        embed.add_field(
            name="📌 نوع التيكت | Ticket Type",
            value=ticket_info['name'],
            inline=False
        )
        embed.set_footer(text="m00d Bot • Ticket System")
        
        close_button = Button(
            label="🔒 إغلاق التيكت | Close Ticket",
            style=discord.ButtonStyle.danger,
            custom_id="close_ticket"
        )
        
        async def close_callback(inter: discord.Interaction):
            if not inter.user.guild_permissions.manage_channels and inter.user.id != interaction.user.id:
                await inter.response.send_message(
                    "❌ ما عندك صلاحية! | No permission!",
                    ephemeral=True
                )
                return
            
            delete_button = Button(label="🗑️ حذف | Delete", style=discord.ButtonStyle.danger)
            cancel_button = Button(label="❌ إلغاء | Cancel", style=discord.ButtonStyle.secondary)
            
            async def delete_callback(i: discord.Interaction):
                await i.response.send_message("🗑️ جاري حذف التيكت... | Deleting ticket...", ephemeral=True)
                await asyncio.sleep(2)
                await ticket_channel.delete()
            
            async def cancel_callback(i: discord.Interaction):
                await i.response.send_message("❌ تم الإلغاء | Cancelled", ephemeral=True)
            
            delete_button.callback = delete_callback
            cancel_button.callback = cancel_callback
            
            confirm_view = View(timeout=60)
            confirm_view.add_item(delete_button)
            confirm_view.add_item(cancel_button)
            
            await inter.response.send_message(
                "⚠️ هل أنت متأكد؟ | Are you sure?",
                view=confirm_view,
                ephemeral=True
            )
        
        close_button.callback = close_callback
        view = View(timeout=None)
        view.add_item(close_button)
        
        await ticket_channel.send(embed=embed, view=view)
        await interaction.followup.send(
            f"✅ تم إنشاء تيكتك! | Ticket created!\n{ticket_channel.mention}",
            ephemeral=True
        )

class TicketSetupView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketTypeSelect())

# ═════════════════════════════════════════════
#  Keep Alive System
# ═════════════════════════════════════════════
@tasks.loop(minutes=5)
async def keep_alive():
    """Keep bot alive by printing status every 5 minutes"""
    print(f"🟢 Bot is alive | {datetime.now().strftime('%H:%M:%S')}")

# ═════════════════════════════════════════════
#  Azkar Task - إرسال أذكار للأعضاء
# ═════════════════════════════════════════════
@tasks.loop(hours=2)
async def send_azkar():
    """Send Islamic azkar to random members every 2 hours"""
    for guild in bot.guilds:
        # Get random online members
        online_members = [m for m in guild.members if not m.bot and m.status != discord.Status.offline]
        if not online_members:
            continue
        
        # Pick 1-3 random members
        selected = random.sample(online_members, min(3, len(online_members)))
        
        for member in selected:
            try:
                zikr = random.choice(AZKAR)
                embed = discord.Embed(
                    title="📿 ذكر من بوت m00d",
                    description=f"**{zikr}**",
                    color=LIME_COLOR
                )
                embed.set_footer(text="جعله الله في ميزان حسناتك ✨")
                await member.send(embed=embed)
            except:
                pass  # Member has DMs closed
    
    print(f"📿 Azkar sent | {datetime.now().strftime('%H:%M:%S')}")

# ═════════════════════════════════════════════
#  Bot Events
# ═════════════════════════════════════════════
@bot.event
async def on_ready():
    print(f"✅ البوت شغال: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ تم مزامنة {len(synced)} أمر slash")
    except Exception as e:
        print(f"❌ خطأ في المزامنة: {e}")
    
    bot.add_view(TicketSetupView())
    
    # Start tasks
    if not keep_alive.is_running():
        keep_alive.start()
    if not send_azkar.is_running():
        send_azkar.start()
    
    print("🟢 All systems online!")

@bot.event
async def on_member_join(member):
    ch = bot.get_channel(WELCOME_CHANNEL_ID)
    if ch:
        embed = discord.Embed(
            title="🎉 أهلاً وسهلاً | Welcome!",
            description=f"مرحباً بك {member.mention} في السيرفر! 🌟\nWelcome to the server!",
            color=LIME_COLOR
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await ch.send(embed=embed)

@bot.event
async def on_member_remove(member):
    ch = bot.get_channel(GOODBYE_CHANNEL_ID)
    if ch:
        embed = discord.Embed(
            title="👋 وداعاً | Goodbye!",
            description=f"غادر {member.name} السيرفر\n{member.name} left the server",
            color=0xFF5555
        )
        await ch.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    content = message.content.strip().lower()
    
    # Greetings - respond in same language only
    arabic_greets = ["هلا", "اهلا", "أهلا", "سلام عليكم", "السلام عليكم", 
                     "السلام عليكم ورحمة الله وبركاته", "سلام عليكم ورحمة الله وبركاته"]
    english_greets = ["hi", "hello", "hi guys", "hey", "hey guys"]
    
    for g in arabic_greets:
        if content == g:
            await message.channel.send(f"وعليكم السلام ورحمة الله وبركاته {message.author.mention}! 👋")
            break
    else:
        for g in english_greets:
            if content == g:
                await message.channel.send(f"Hello {message.author.mention}! Welcome 👋😊")
                break
    
    # XP from messages
    data = load_data()
    user = get_user(data, message.author.id)
    user["chat_messages"] = user.get("chat_messages", 0) + 1
    leveled = add_xp(user, random.randint(5, 15))
    save_data(data)
    if leveled:
        await message.channel.send(
            f"🎉 مبروك {message.author.mention}! وصلت للفل **{user['level']}**! 🚀\n🎉 Congrats! You reached level **{user['level']}**! 🚀"
        )
    
    await bot.process_commands(message)

# ═════════════════════════════════════════════
#  SLASH COMMANDS - Announcements
# ═════════════════════════════════════════════
@bot.tree.command(name="announce", description="📢 إرسال إعلان للأعضاء | Send announcement to members")
@app_commands.checks.has_permissions(administrator=True)
async def announce_members(interaction: discord.Interaction, message: str, member_count: int = 10):
    """
    Send announcement to random members
    
    Parameters:
    message: الرسالة اللي تبي ترسلها | Message to send
    member_count: عدد الأعضاء (1-50) | Number of members (1-50)
    """
    await interaction.response.defer(ephemeral=True)
    
    if member_count < 1 or member_count > 50:
        await interaction.followup.send("❌ العدد لازم يكون بين 1-50 | Count must be 1-50", ephemeral=True)
        return
    
    # Get online members
    online_members = [m for m in interaction.guild.members if not m.bot and m.status != discord.Status.offline]
    
    if not online_members:
        await interaction.followup.send("❌ ما في أعضاء أونلاين! | No online members!", ephemeral=True)
        return
    
    selected = random.sample(online_members, min(member_count, len(online_members)))
    
    success = 0
    failed = 0
    
    for member in selected:
        try:
            await member.send(message)
            success += 1
            await asyncio.sleep(1)  # Rate limit protection
        except:
            failed += 1
    
    await interaction.followup.send(
        f"✅ تم الإرسال!\nSuccessful: **{success}**\nFailed: **{failed}**",
        ephemeral=True
    )

@bot.tree.command(name="setup", description="⚙️ إعداد نظام التيكتات | Setup ticket system")
@app_commands.checks.has_permissions(administrator=True)
async def setup_tickets(interaction: discord.Interaction, channel: discord.TextChannel):
    """Setup ticket system in specified channel"""
    
    embed = discord.Embed(
        title="🎫 نظام التيكتات | Ticket System",
        description="اختر نوع التيكت من القائمة لإنشاء تيكت جديد!\nSelect ticket type from the menu to create a new ticket!",
        color=LIME_COLOR
    )
    embed.add_field(
        name="📋 أنواع التيكتات | Ticket Types",
        value="🛠️ **دعم فني** | Technical Support\n📝 **تقديم طلب** | Application\n⚠️ **بلاغات** | Reports\n📢 **شكوى عن إدارة** | Staff Complaint",
        inline=False
    )
    embed.set_footer(text="m00d Bot • اختر من القائمة تحت | Select from menu below")
    
    view = TicketSetupView()
    await channel.send(embed=embed, view=view)
    
    await interaction.response.send_message(
        f"✅ تم إعداد نظام التيكتات بنجاح! | Ticket system setup complete!\n📍 {channel.mention}",
        ephemeral=True
    )

# ═════════════════════════════════════════════
#  SLASH COMMANDS - Economy
# ═════════════════════════════════════════════
@bot.tree.command(name="collect", description="💰 اجمع m00d كل 30 دقيقة | Collect m00d every 30 minutes")
async def slash_collect(interaction: discord.Interaction):
    data = load_data()
    user = get_user(data, interaction.user.id)
    now = time.time()
    cooldown = 30 * 60
    
    remaining = cooldown - (now - user["last_collect"])
    if remaining > 0:
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        embed = discord.Embed(
            title="⏳ انتظر شوية! | Wait a bit!",
            description=f"تقدر تجمع مرة ثانية بعد **{mins}** دقيقة و **{secs}** ثانية\nYou can collect again after **{mins}** minutes and **{secs}** seconds",
            color=0xFF9900
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    earned = random.randint(100, 1000)
    user["mood"] += earned
    user["last_collect"] = now
    save_data(data)
    
    embed = discord.Embed(
        title="💰 تم الجمع! | Collected!",
        description=f"جمعت **{earned:,} m00d** 🎉\nYou collected **{earned:,} m00d**!\n\n💵 رصيدك | Balance: **{user['mood']:,} m00d**",
        color=LIME_COLOR
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="work", description="💼 اشتغل واكسب 10K-100K m00d | Work and earn 10K-100K m00d")
async def slash_work(interaction: discord.Interaction):
    data = load_data()
    user = get_user(data, interaction.user.id)
    now = time.time()
    cooldown = 60 * 60
    
    remaining = cooldown - (now - user.get("last_work", 0))
    if remaining > 0:
        mins = int(remaining // 60)
        embed = discord.Embed(
            title="⏳ تعبت من الشغل! | Tired from work!",
            description=f"ارتح **{mins}** دقيقة ثم اشتغل مرة ثانية\nRest for **{mins}** minutes then work again",
            color=0xFF9900
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    jobs = [
        ("👨‍🍳 طباخ | Chef", "طبخت كسكسي | Cooked couscous"),
        ("🚗 سائق | Driver", "وصلت زبائن | Drove customers"),
        ("💻 مبرمج | Programmer", "كتبت كود | Wrote code"),
    ]
    job_name, desc = random.choice(jobs)
    earned = random.randint(10000, 100000)
    user["mood"] += earned
    user["last_work"] = now
    save_data(data)
    
    embed = discord.Embed(
        title=f"💼 {job_name}",
        description=f"{desc}\nكسبت **{earned:,} m00d** 💰\nYou earned **{earned:,} m00d**!\n\n💵 رصيدك | Balance: **{user['mood']:,} m00d**",
        color=LIME_COLOR
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="balance", description="💳 شوف رصيدك | Check your balance")
async def slash_balance(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    member = member or interaction.user
    data = load_data()
    user = get_user(data, member.id)
    embed = discord.Embed(
        title=f"💳 رصيد | Balance: {member.display_name}",
        description=f"**{user['mood']:,} m00d** 💰",
        color=LIME_COLOR
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="level", description="⭐ شوف لفلك | Check your level")
async def slash_level(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    member = member or interaction.user
    data = load_data()
    user = get_user(data, member.id)
    embed = discord.Embed(
        title=f"⭐ لفل | Level: {member.display_name}",
        color=LIME_COLOR
    )
    embed.add_field(name="🎯 اللفل | Level", value=f"**{user['level']}**", inline=True)
    embed.add_field(name="✨ XP", value=f"**{user['xp']:,} / {xp_needed(user['level']):,}**", inline=True)
    embed.add_field(name="💰 m00d", value=f"**{user['mood']:,}**", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="📖 أوامر البوت | Bot commands")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(title="📖 أوامر البوت | Bot Commands", color=LIME_COLOR)
    embed.add_field(name="💰 المال | Money", value="`/collect` `/work` `/balance` `/leaderboard`", inline=False)
    embed.add_field(name="⭐ اللفل | Level", value="`/level` `/top` `/topvoice`", inline=False)
    embed.add_field(name="🏪 الشوب | Shop", value="`!shop` `!buy <id>` `!inventory`", inline=False)
    embed.add_field(name="🎫 التيكتات | Tickets", value="`/setup` — إعداد (أدمن) | Setup (Admin)", inline=False)
    embed.add_field(name="👑 أدمن | Admin", value="`/add` `/remove` `/announce`", inline=False)
    embed.set_footer(text="m00d Bot • Use / or ! for commands")
    await interaction.response.send_message(embed=embed)

# ═════════════════════════════════════════════
#  PREFIX COMMANDS - Economy
# ═════════════════════════════════════════════
@bot.command(name="collect")
async def collect(ctx):
    data = load_data()
    user = get_user(data, ctx.author.id)
    now = time.time()
    cooldown = 30 * 60
    
    remaining = cooldown - (now - user["last_collect"])
    if remaining > 0:
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        embed = discord.Embed(
            title="⏳ انتظر شوية! | Wait a bit!",
            description=f"تقدر تجمع مرة ثانية بعد **{mins}** دقيقة و **{secs}** ثانية\nYou can collect again after **{mins}** minutes and **{secs}** seconds",
            color=0xFF9900
        )
        await ctx.send(embed=embed)
        return
    
    earned = random.randint(100, 1000)
    user["mood"] += earned
    user["last_collect"] = now
    save_data(data)
    
    embed = discord.Embed(
        title="💰 تم الجمع! | Collected!",
        description=f"جمعت **{earned:,} m00d** 🎉\nYou collected **{earned:,} m00d**!\n\n💵 رصيدك | Balance: **{user['mood']:,} m00d**",
        color=LIME_COLOR
    )
    await ctx.send(embed=embed)

@bot.command(name="work")
async def work(ctx):
    data = load_data()
    user = get_user(data, ctx.author.id)
    now = time.time()
    cooldown = 60 * 60
    
    remaining = cooldown - (now - user.get("last_work", 0))
    if remaining > 0:
        mins = int(remaining // 60)
        embed = discord.Embed(
            title="⏳ تعبت من الشغل! | Tired from work!",
            description=f"ارتح **{mins}** دقيقة ثم اشتغل مرة ثانية\nRest for **{mins}** minutes then work again",
            color=0xFF9900
        )
        await ctx.send(embed=embed)
        return
    
    jobs = [
        ("👨‍🍳 طباخ | Chef", "طبخت كسكسي | Cooked couscous"),
        ("🚗 سائق | Driver", "وصلت زبائن | Drove customers"),
        ("💻 مبرمج | Programmer", "كتبت كود | Wrote code"),
    ]
    job_name, desc = random.choice(jobs)
    earned = random.randint(10000, 100000)
    user["mood"] += earned
    user["last_work"] = now
    save_data(data)
    
    embed = discord.Embed(
        title=f"💼 {job_name}",
        description=f"{desc}\nكسبت **{earned:,} m00d** 💰\nYou earned **{earned:,} m00d**!\n\n💵 رصيدك | Balance: **{user['mood']:,} m00d**",
        color=LIME_COLOR
    )
    await ctx.send(embed=embed)

@bot.command(name="balance", aliases=["bal"])
async def balance(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = load_data()
    user = get_user(data, member.id)
    embed = discord.Embed(
        title=f"💳 رصيد | Balance: {member.display_name}",
        description=f"**{user['mood']:,} m00d** 💰",
        color=LIME_COLOR
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
    
    embed = discord.Embed(title="🏆 أغنى الأعضاء | Richest Members - m00d", color=LIME_COLOR)
    medals = ["🥇", "🥈", "🥉"] + ["4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    desc = ""
    for i, (uid, d) in enumerate(sorted_users):
        member = guild_members.get(uid)
        name = member.display_name if member else f"User#{uid}"
        desc += f"{medals[i]} **{name}** — {d.get('mood',0):,} m00d\n"
    embed.description = desc or "ما في بيانات بعد! | No data yet!"
    await ctx.send(embed=embed)

@bot.command(name="level", aliases=["lvl", "rank"])
async def show_level(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = load_data()
    user = get_user(data, member.id)
    embed = discord.Embed(
        title=f"⭐ لفل | Level: {member.display_name}",
        color=LIME_COLOR
    )
    embed.add_field(name="🎯 اللفل | Level", value=f"**{user['level']}**", inline=True)
    embed.add_field(name="✨ XP", value=f"**{user['xp']:,} / {xp_needed(user['level']):,}**", inline=True)
    embed.add_field(name="💰 m00d", value=f"**{user['mood']:,}**", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
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
    
    embed = discord.Embed(title="🗨️ Top Chat - أكثر الناس رسائل", color=LIME_COLOR)
    medals = ["🥇","🥈","🥉"] + ["4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    desc = ""
    for i, (uid, d) in enumerate(sorted_chat):
        member = guild_members.get(uid)
        name = member.display_name if member else f"User#{uid}"
        msgs = d.get("chat_messages", 0)
        desc += f"{medals[i]} **{name}** — {msgs:,} رسالة | messages\n"
    embed.description = desc or "ما في بيانات بعد! | No data yet!"
    await ctx.send(embed=embed)

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
    
    embed = discord.Embed(title="🔊 Top Voice - أكثر الناس في الفويس", color=LIME_COLOR)
    medals = ["🥇","🥈","🥉"] + ["4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    desc = ""
    for i, (uid, d) in enumerate(sorted_voice):
        m = guild_members.get(uid)
        name = m.display_name if m else f"User#{uid}"
        mins = d.get("voice_minutes", 0)
        hours = mins // 60
        desc += f"{medals[i]} **{name}** — {hours}h {mins%60}m\n"
    embed.description = desc or "ما في بيانات بعد! | No data yet!"
    await ctx.send(embed=embed)

@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="📖 أوامر البوت | Bot Commands", color=LIME_COLOR)
    embed.add_field(name="💰 المال | Money", value="`!collect` `!work` `!balance` `!leaderboard`", inline=False)
    embed.add_field(name="⭐ اللفل | Level", value="`!level` `!top` `!c`", inline=False)
    embed.add_field(name="🏪 الشوب | Shop", value="`!shop` `!buy <id>` `!inventory`", inline=False)
    embed.add_field(name="👑 أدمن | Admin", value="`!add @user <amount>` `!remove @user <amount>`", inline=False)
    embed.add_field(name="✨ استخدم / أيضاً!", value="جرّب `/help` للأوامر الجديدة!\nTry `/help` for new commands!", inline=False)
    await ctx.send(embed=embed)

# ═════════════════════════════════════════════
#  ADMIN COMMANDS
# ═════════════════════════════════════════════
@bot.command(name="add")
@commands.has_permissions(administrator=True)
async def add_mood(ctx, member: discord.Member, amount: int):
    data = load_data()
    user = get_user(data, member.id)
    user["mood"] += amount
    save_data(data)
    embed = discord.Embed(
        description=f"✅ تمت إضافة **{amount:,} m00d** لـ {member.mention}\n✅ Added **{amount:,} m00d** to {member.mention}\n\n💵 رصيده | Balance: **{user['mood']:,} m00d**",
        color=LIME_COLOR
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
        description=f"✅ تم سحب **{amount:,} m00d** من {member.mention}\n✅ Removed **{amount:,} m00d** from {member.mention}\n\n💵 رصيده | Balance: **{user['mood']:,} m00d**",
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
        description=f"✅ تم تعيين رصيد {member.mention} على **{amount:,} m00d**\n✅ Set {member.mention}'s balance to **{amount:,} m00d**",
        color=LIME_COLOR
    )
    await ctx.send(embed=embed)

# Voice tracking
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
                user["mood"] += mins * 10
                save_data(data)

# ═════════════════════════════════════════════
#  RUN BOT
# ═════════════════════════════════════════════
bot.run(TOKEN)
