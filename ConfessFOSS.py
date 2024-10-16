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
cur.execute("CREATE TABLE IF NOT EXISTS channels(channel_id INTEGER)")
cur.execute("CREATE TABLE IF NOT EXISTS guilds(guild_id INTEGER, confession_count INTEGER)")
cur.execute("CREATE TABLE IF NOT EXISTS confessions(guild_id INTEGER, channel_id INTEGER, user_id INTEGER, confession_id INTEGER)")
cur.execute("CREATE TABLE IF NOT EXISTS confession_bans(guild_id INTEGER, user_id INTEGER, ban_state INTEGER)")
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

#get this out of my face
async def add_confession_to_database(interaction: nextcord.Interaction):
    #if user has never used this bot, add them to user list
    user_id = interaction.user.id
    res = cur.execute(f"SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if(res.fetchone() is None):
        #add to user list
        res = cur.execute(f"INSERT INTO users VALUES(?)", (user_id,))
        print(f"user {user_id} never confessed before")

    #if channel has never been confessed in before, add to channel list
    channel_id = interaction.channel_id
    res = cur.execute(f"SELECT channel_id FROM channels WHERE channel_id=?", (channel_id,))
    if(res.fetchone() is None):
        #add to channel list
        res = cur.execute(f"INSERT INTO channels VALUES(?)", (channel_id,))
        print(f"channel {channel_id} never confessed in before")

    #if guild has never been confessed in, prompt an admin to add a confession channel
    guild_id = interaction.guild_id
    res = cur.execute(f"SELECT guild_id FROM guilds WHERE guild_id=?", (guild_id,))
    if(res.fetchone() is None):
        #add to guild list
        #and add confession counter
        res = cur.execute(f"INSERT INTO guilds VALUES(?, 0)", (guild_id,))
        print(f"guild {guild_id} never confessed in before")


    #increment confession count
    res = cur.execute(f"UPDATE guilds SET confession_count = confession_count + 1 WHERE guild_id=?", (guild_id,))
    res = cur.execute(f"SELECT confession_count FROM guilds WHERE guild_id=?", (guild_id,))

    #get the current confession_count in this guild_id
    confession_count = res.fetchone()[0]

    #add confession to confession table
    res = cur.execute(f"INSERT INTO confessions VALUES(?, ?, ?, ?)", (guild_id, channel_id, user_id, confession_count,))

    con.commit()

    return confession_count

#confess slash command
@bot.slash_command(description="Confess something anonymously.")
async def confess(interaction: nextcord.Interaction, arg: str):

    #lookup their confession_ban state
    res = cur.execute(f"SELECT ban_state FROM confession_bans WHERE guild_id=? AND user_id=?", (interaction.guild_id, interaction.user.id,))

    ban_state = res.fetchone()
    if(ban_state is not None and ban_state[0] == 1):
        #user banned, return
        await interaction.response.send_message(f"you are banned from using the bot in this server", ephemeral=True)
        return


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

"""
@bot.slash_command(description="Modify bot settings in this server.")
async def setting(interaction: nextcord.Interaction, setting_name: str, setting_value: str):
    #when you modify a setting, check for that setting in the guild. if not exists, add it and set.
    #all settings should be automatically put in the database on server join though

    #SETTINGS
    #deanonymize between single poster(all confessions from the same poster have the same id)
    #channel blacklist(default blacklist, could be whitelist)
"""

@bot.slash_command(description="Ban a confession ID from confessing in this guild again.")
async def confessban(interaction: nextcord.Interaction, confession_id: int):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(f"you are not an an admin in this server", ephemeral=True)
        return


    guild_id = interaction.guild_id

    #find the user who wrote that confession...

    res = cur.execute(f"SELECT user_id FROM confessions WHERE confession_id=?", (confession_id,))
    
    user_id = res.fetchone()
    if(user_id is None):
        await interaction.response.send_message(f"invalid confession id", ephemeral=True)
        return
    user_id = user_id[0]
    
    #confession_id is valid...
    #check if the user is already banned

    res = cur.execute(f"SELECT ban_state FROM confession_bans WHERE guild_id=? AND user_id=?", (guild_id, user_id,))

    ban_state = res.fetchone()

    #ban_state 0 is unbanned
    #ban_state 1 is banned

    if(ban_state is None):
        #treat like someone who is unbanned
        #create user ban record
        res = cur.execute(f"INSERT INTO confession_bans VALUES(?, ?, 1)", (guild_id, user_id,))
        await interaction.response.send_message(f"user banned", ephemeral=True)
    elif(ban_state[0] == 1):
        #user is already banned. toggle ban
        res = cur.execute(f"UPDATE confession_bans SET ban_state = 0 WHERE guild_id=? AND user_id=?", (guild_id, user_id,))
        await interaction.response.send_message(f"user is now unbanned(they have a history of being banned)", ephemeral=True)
    elif(ban_state[0] == 0):
        #user is not banned, but already has a record
        #this is for the case where a user gets banned and then unbanned, then banned again
        res = cur.execute(f"UPDATE confession_bans SET ban_state = 1 WHERE guild_id=? AND user_id=?", (guild_id, user_id,))
        await interaction.response.send_message(f"user banned(again)", ephemeral=True)

    con.commit()
    #get the current confession_count in this guild_id
    


#MAKE EVERYTHING SQL SAFE

with open('token.txt', 'r') as file:
    # Read a single line (or string)
    bot.run(file.readline().strip())
