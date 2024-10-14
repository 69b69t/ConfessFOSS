import nextcord
from nextcord.ext import commands

description = "ConfessFOSS"

intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="$", description=description, intents=intents)
bot.remove_command('help')

#startup
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

#logging. spammy
"""
@bot.event
async def on_message(message):
    print(f'Message from {message.author}: {message.content}')
    await bot.process_commands(message)
"""

#help command
@bot.command()
async def help(ctx):
    help_text = (
        "Here are the available commands:\n"
        "$help\n"
    )
    await ctx.send(help_text)


#confess slash command(waiting on registration)
@bot.slash_command(description="spoy: Add a description to the command")
async def confess(interaction: nextcord.Interaction, arg: str):
    embed = nextcord.Embed(
        title="confession"
    )
    embed.add_field(
        name="",
        value=arg,
        inline=False
    )

    print(f"user {interaction.user.name} (ID: {interaction.user.id}) sent confession {arg}")
    await interaction.response.send_message("confession sent", ephemeral=True)
    await interaction.channel.send(embed=embed)

#Simple command that responds with Pong!
@bot.slash_command()
async def ping(interaction: nextcord.Interaction):
    await interaction.response.send_message("Pong!")

bot.run('TOKEN')
