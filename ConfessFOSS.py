import nextcord
from nextcord.ext import commands

import sqlite3

#intent stuff
intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="$", description="ConfessFOSS", intents=intents)
bot.remove_command('help')

#create database if it dosent exist yet
print("connecting to the database...")
con = sqlite3.connect("ConfessFOSS.db")
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER)")
cur.execute("CREATE TABLE IF NOT EXISTS channels(channel_id INTEGER, confession_count INTEGER)")
cur.execute("CREATE TABLE IF NOT EXISTS guilds(guild_id INTEGER, confession_channel INTEGER)")
cur.execute("CREATE TABLE IF NOT EXISTS confessions(guild_id INTEGER, channel_id INTEGER, user_id INTEGER, confession_id INTEGER)")
cur.execute("CREATE TABLE IF NOT EXISTS settings(guild_id INTEGER, setting TEXT, value TEXT)")

#startup
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

#help command
@bot.command(description="the help command")
async def help(ctx):
    help_text = (
        "Here are the available commands:\n"
        "$help\n"
    )
    await ctx.send(help_text)

#confess slash command
@bot.slash_command(description="confess something anonymously")
async def confess(interaction: nextcord.Interaction, arg: str):

    #add the confession to database
    #we do stuff with the database first, then do stuff with discord
    confession_count = await add_confession_to_database(interaction)

    embed = nextcord.Embed(
        title=f"Confession #{confession_count}"
    )
    embed.add_field(
        name="",
        value=arg,
        inline=False
    )
    
    print(f"user {interaction.user.name} (ID: {interaction.user.id}) sent confession {arg}")
    await interaction.response.send_message(f"Confession #{confession_count} sent", ephemeral=True)
    await interaction.channel.send(embed=embed)

@bot.slash_command()
async def ping(interaction: nextcord.Interaction):
    await interaction.response.send_message("Pong!")

async def add_confession_to_database(interaction: nextcord.Interaction):
    #if user has never used this bot, add them to user list
    user_id = interaction.user.id
    res = cur.execute(f"SELECT user_id FROM users WHERE user_id={user_id}")
    if(res.fetchone() is None):
        #add to user list
        res = cur.execute(f"INSERT INTO users VALUES({user_id})")
        print(f"user {user_id} never confessed before")

    #if channel has never been confessed in before, add to channel list
    channel_id = interaction.channel_id
    res = cur.execute(f"SELECT channel_id FROM channels WHERE channel_id={channel_id}")
    if(res.fetchone() is None):
        #add to channel list
        res = cur.execute(f"INSERT INTO channels VALUES({channel_id}, 0)")
        print(f"channel {channel_id} never confessed in before")

    #if guild has never been confessed in, prompt an admin to add a confession channel
    guild_id = interaction.guild_id
    res = cur.execute(f"SELECT guild_id FROM guilds WHERE guild_id={guild_id}")
    if(res.fetchone() is None):
        #add to channel list
        res = cur.execute(f"INSERT INTO guilds VALUES({guild_id}, 0)")
        print(f"guild {guild_id} never confessed in before")


    #increment confession count
    res = cur.execute(f"UPDATE CHANNELS SET confession_count = confession_count + 1 WHERE channel_id={interaction.channel_id}")
    res = cur.execute(f"SELECT confession_count FROM channels WHERE channel_id={channel_id}")

    #get the current confession_count in this channel_id
    confession_count = res.fetchone()[0]

    #add confession to confession table
    res = cur.execute(f"INSERT INTO confessions VALUES({guild_id}, {channel_id}, {user_id}, {confession_count})")

    con.commit()

    return confession_count




with open('token.txt', 'r') as file:
    # Read a single line (or string)
    bot.run(file.readline().strip())
