# bot.py

import discord

from discord.ext import commands

from discord import app_commands

from pymongo import MongoClient

import requests

import re

from datetime import datetime, timezone

# ======================

# CONFIGURATION

# ======================

MONGO_URI = "PLACE MONGODB URI HERE"

DISCORD_TOKEN = "DISCORD BOT TOKEN"

# MongoDB

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

db = client["mcscanner"]

servers_collection = db["servers"]

# Bot

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=intents)

# ======================

# UTILITIES

# ======================

def get_skin_url(username: str):

    """Get Minecraft player skin URL"""

    try:

        res = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{username}", timeout=5)

        if res.status_code == 200:

            uuid = res.json().get("id")

            return f"https://crafatar.com/avatars/{uuid}?size=160&overlay"

    except Exception:

        pass

    return None

def extract_online_players(players_str: str) -> int:

    """Extract current player count from 'X/Y' format"""

    if not players_str or not isinstance(players_str, str):

        return 0

    match = re.match(r"(\d+)/\d+", players_str)

    return int(match.group(1)) if match else 0

def create_server_embed(title: str, servers: list, color: discord.Color) -> discord.Embed:

    """Create formatted embed for server list"""

    embed = discord.Embed(title=title, color=color, timestamp=datetime.now(timezone.utc))

    if not servers:

        embed.description = "🔭 No servers found."

        embed.set_footer(text="Live server data • Updated in real-time")

        return embed

    for s in servers[:10]:

        ip = s.get("ip", "Unknown")

        port = s.get("port", 25565)

        version = s.get("version", "Unknown")

        players = s.get("players", "0/0")

        desc = (s.get("description") or s.get("motd") or "No description").strip()

        if len(desc) > 100:

            desc = desc[:97] + "..."

        embed.add_field(

            name=f"🌐 `{ip}:{port}`",

            value=f"🧩 **Version:** `{version}`\n"

                  f"👥 **Players:** `{players}`\n"

                  f"📜 **MOTD:** `{desc}`",

            inline=False

        )

    embed.set_footer(text="Live server data • Updated in real-time")

    return embed

# ======================

# EVENTS

# ======================

@bot.event

async def on_ready():

    """Bot startup event"""

    await bot.tree.sync()

    print(f"✅ {bot.user} is online and ready!")

    print(f"📊 Connected to {len(bot.guilds)} guilds")

    print(f"🗄️ Database has {servers_collection.estimated_document_count():,} servers")

# ======================

# SLASH COMMANDS

# ======================

@bot.tree.command(name="help", description="📘 View all available commands")

async def help_command(interaction: discord.Interaction):

    """Display help menu with all commands"""

    await interaction.response.defer(thinking=True)

    embed = discord.Embed(

        title="✨ Minecraft Server Explorer",

        description="Discover thousands of live Minecraft servers!",

        color=discord.Color.teal()

    )

    embed.add_field(name="🎲 `/random`", value="Get 10 random servers", inline=False)

    embed.add_field(name="🔍 `/find`", value="Search by version or MOTD keyword", inline=False)

    embed.add_field(name="🏆 `/top`", value="Top 10 servers by player count", inline=False)

    embed.add_field(name="📊 `/count`", value="Total number of servers", inline=False)

    embed.add_field(name="🧑 `/user`", value="Get player skin & info", inline=False)

    embed.add_field(name="🏓 `/ping`", value="Check bot latency", inline=False)

    embed.add_field(name="🤖 `/botinfo`", value="Bot statistics", inline=False)

    embed.set_thumbnail(url=bot.user.display_avatar.url)

    embed.set_footer(text="Made with ❤️ for Minecraft enthusiasts")

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="random", description="🎲 Show 10 random Minecraft servers")

async def random_servers(interaction: discord.Interaction):

    """Get random servers from database"""

    await interaction.response.defer(thinking=True)

    try:

        servers = list(servers_collection.aggregate([{"$sample": {"size": 10}}]))

    except Exception:

        servers = list(servers_collection.find().limit(10))

    embed = create_server_embed("🎲 Random Minecraft Servers", servers, discord.Color.green())

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="find", description="🔍 Find servers by version or MOTD")

@app_commands.describe(

    version="Minecraft version (e.g., '1.20.1') — use '*' for any",

    motd_keyword="Keyword in server description (case-insensitive)"

)

async def find_servers(interaction: discord.Interaction, version: str = "*", motd_keyword: str = ""):

    """Search for servers matching criteria"""

    await interaction.response.defer(thinking=True)

    query = {}

    if version != "*":

        query["version"] = {"$regex": f"^{re.escape(version)}", "$options": "i"}

    if motd_keyword.strip():

        query["$or"] = [

            {"description": {"$regex": re.escape(motd_keyword), "$options": "i"}},

            {"motd": {"$regex": re.escape(motd_keyword), "$options": "i"}}

        ]

    try:

        servers = list(servers_collection.aggregate([

            {"$match": query},

            {"$sample": {"size": 10}}

        ]))

    except Exception:

        servers = list(servers_collection.find(query).limit(10))

    title = f"🔍 Results — Version: `{version}`, MOTD: `{motd_keyword or 'Any'}`"

    embed = create_server_embed(title, servers, discord.Color.blue())

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="count", description="📊 Show total number of servers")

async def count_servers(interaction: discord.Interaction):

    """Display total server count"""

    await interaction.response.defer(thinking=True)

    count = servers_collection.estimated_document_count()

    embed = discord.Embed(

        title="📊 Server Database Stats",

        description=f"**Total Servers:** `{count:,}`",

        color=discord.Color.purple(),

        timestamp=datetime.now(timezone.utc)

    )

    embed.set_footer(text="Updated in real-time")

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="top", description="🏆 Top 10 servers by player count")

async def top_servers(interaction: discord.Interaction):

    """Get most populated servers"""

    await interaction.response.defer(thinking=True)

    servers = list(servers_collection.find({"players": {"$exists": True}}).limit(200))

    servers.sort(key=lambda s: extract_online_players(s.get("players", "0/0")), reverse=True)

    top_10 = servers[:10]

    embed = create_server_embed("🏆 Top Servers by Player Count", top_10, discord.Color.gold())

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="ping", description="🏓 Check bot latency")

async def ping_command(interaction: discord.Interaction):

    """Display bot response time"""

    await interaction.response.defer(thinking=True)

    latency = round(bot.latency * 1000)

    status = "🟢 Excellent" if latency < 100 else "🟡 Good" if latency < 200 else "🔴 High"

    await interaction.followup.send(f"🏓 **Latency:** `{latency}ms` — {status}")

@bot.tree.command(name="botinfo", description="🤖 Get bot information")

async def botinfo_command(interaction: discord.Interaction):

    """Display bot statistics"""

    await interaction.response.defer(thinking=True)

    embed = discord.Embed(

        title="🤖 Bot Information",

        color=discord.Color.blurple(),

        timestamp=datetime.now(timezone.utc)

    )

    embed.set_thumbnail(url=bot.user.display_avatar.url)

    embed.add_field(name="Name", value=bot.user.name, inline=True)

    embed.add_field(name="ID", value=f"`{bot.user.id}`", inline=True)

    embed.add_field(name="Servers", value=f"`{len(bot.guilds)}`", inline=True)

    total_members = sum(g.member_count for g in bot.guilds)

    embed.add_field(name="Users", value=f"`{total_members:,}`", inline=True)

    embed.add_field(name="Database", value=f"`{servers_collection.estimated_document_count():,}` servers", inline=False)

    embed.set_footer(text="Powered by MongoDB • Python + Discord.py")

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="user", description="🧑 Get Minecraft player skin & info")

@app_commands.describe(username="Minecraft username")

async def user_command(interaction: discord.Interaction, username: str):

    """Fetch player profile and skin"""

    await interaction.response.defer(thinking=True)

    skin_url = get_skin_url(username)

    if not skin_url:

        await interaction.followup.send("❌ Player not found on Mojang servers.", ephemeral=True)

        return

    embed = discord.Embed(

        title=f"🧑 Minecraft Profile: `{username}`",

        color=discord.Color.orange(),

        timestamp=datetime.now(timezone.utc)

    )

    embed.set_thumbnail(url=skin_url)

    embed.add_field(name="Skin", value=f"[View Full Skin](https://crafatar.com/skins/{username})", inline=True)

    embed.add_field(name="Head", value=f"[Download Head](https://crafatar.com/renders/head/{username})", inline=True)

    embed.add_field(name="Recent Servers", value="🔭 Not tracked (requires player list storage)", inline=False)

    embed.set_footer(text="Data from Mojang API • Skin by Crafatar")

    await interaction.followup.send(embed=embed)

# ======================

# RUN BOT

# ======================

if __name__ == "__main__":

    if DISCORD_TOKEN == "YOUR_DISCORD_BOT_TOKEN_HERE":

        print("❌ ERROR: Please replace 'YOUR_DISCORD_BOT_TOKEN_HERE' with your actual Discord bot token!")

        exit(1)

    

    try:

        bot.run(DISCORD_TOKEN)

    except discord.LoginFailure:

        print("❌ ERROR: Invalid Discord token. Please check your token and try again.")

    except Exception as e:

        print(f"❌ ERROR: An unexpected error occurred: {e}")
