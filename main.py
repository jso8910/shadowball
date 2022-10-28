from discord.ext import commands
from table2ascii import table2ascii
from sheets import ShadowballSheet
from discord.ui import Select, View
import discord
from dotenv import dotenv_values
config = dotenv_values(".env")
# from discord import app_commands

# class aclient(discord.Client):
#     def __init__(self):
#         super().__init__(intents=discord.Intents.default())
#         self.synced = False

#     async def on_ready(self):
#         await self.wait_until_ready()
#         if not self.synced:
#             await tree.sync(guild = discord.Object(id = config['GUILD_ID'])) # Testing server id
#             self.synced = True
#         print(f"We have logged in as {self.user}")

# client = aclient()
sheet = ShadowballSheet()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!',
                   description="Ranger Shadowball bot", intents=intents)
# tree = app_commands.CommandTree(client)

# @tree.command(name = "add_game", description = "Add a new game", guild = discord.Object(id = config['GUILD_ID']))
# @app_commands.checks.has_role("Scouter")


@bot.command()
@commands.has_role('Scouter')
async def add_game(ctx: commands.context.Context, home_team: str, away_team: str, date: str):
    sheet.new_game(away_team, home_team, date)
    await ctx.send(f"Created a new game! {away_team} v {home_team} {date}")

# @tree.command(name = "set_game", description = "Set the current game", guild = discord.Object(id = config['GUILD_ID']))
# @app_commands.checks.has_role("Scouter")


@bot.command()
@commands.has_role('Scouter')
async def set_game(ctx: commands.context.Context):
    games = sheet.get_games()
    sel = Select(options=[
        discord.SelectOption(label=title) for title in games
    ])

    async def callback(interaction):
        if "Scouter" in [y.name for y in interaction.user.roles]:
            await interaction.response.send_message(sheet.set_game(sel.values[0]) or f"Set game to: {sel.values[0]}")
        else:
            await interaction.response.send_message("You aren't a scouter, stop trying to do this.")
    sel.callback = callback
    view = View()
    view.add_item(sel)
    await ctx.send(f"Set the game that's going on now", view=view)

# @tree.command(name = "input_pitch", description = "Enter the pitch that was entered as well as the maximum difference that is a home run", guild = discord.Object(id = config['GUILD_ID']))
# @app_commands.checks.has_role("Scouter")


@bot.command()
@commands.has_role('Scouter')
async def input_pitch(ctx: commands.context.Context, pitch: int, homer_diff: int):
    sheet.finish_pitch(pitch, homer_diff)
    await ctx.send(f"Updated the leaderboard with the most recent pitch and got things ready for the next pitch!")

# @tree.command(name = "guess", description = "Make your shadowball guess", guild = discord.Object(id = config['GUILD_ID']))


@bot.command()
async def guess(ctx: commands.context.Context, number: int):
    updated_guess = sheet.make_guess(ctx.author.nick, number)
    await ctx.send(f"{'Updated' if updated_guess else 'Set'} your guess for this pitch as {number}.")

# @tree.command(name = "leaderboard", description = "Get shadowball leaderboard. Remember to input the minimum number of guesses!", guild = discord.Object(id = config['GUILD_ID']))


@bot.command()
async def leaderboard(ctx: commands.context.Context, min_guesses: int):
    leaderboard = sheet.get_leaderboard(min_guesses)
    output = table2ascii(
        header=["Name", "# of Guesses", "Points", "PPG"],
        body=[row + [round(int(row[2]) / int(row[1]), 3)]
              for row in leaderboard],
    )
    await ctx.send(f"Leaderboard of all qualifying players (more than {min_guesses} guesses) sorted by points per guess (PPG)```\n{output}\n```")

# @tree.command(name = "homerball_lb", description = "Get homerball leaderboard. Remember to input the minimum number of guesses!", guild = discord.Object(id = config['GUILD_ID']))


@bot.command()
async def homerball_leaderboard(ctx: commands.context.Context, min_guesses: int):
    leaderboard = sheet.get_homerball_lb(min_guesses)
    output = table2ascii(
        header=["Name", "# of Homers", "# of Guesses"],
        body=[[row[1]] + [row[2]] + [row[3]] for row in leaderboard],
    )
    await ctx.send(f"Leaderboard of all qualifying players (more than {min_guesses} guesses) sorted by points per guess (PPG)```\n{output}\n```")


@bot.event
async def on_command_error(ctx: commands.context.Context, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("Hey, you're not a scouter! You can't do this!")
    elif isinstance(error, commands.MissingRequiredArgument):
        match ctx.invoked_with:
            case 'add_game':
                await ctx.send(f"Missing argument {str(error.param).replace(': int', ' which is a number')}. Correct form is `!add_game <home_team> <away_team> <date>`")
            case 'input_pitch':
                await ctx.send(f"Missing argument {str(error.param).replace(': int', ' which is a number')}. Correct form is `!input_pitch <pitch> <homer_diff>`")
            case 'guess':
                await ctx.send(f"Missing argument {str(error.param).replace(': int', ' which is a number')}. Correct form is `!guess <number>`")
            case 'leaderboard':
                await ctx.send(f"Missing argument {str(error.param).replace(': int', ' which is a number')}. Correct form is `!leaderboard <min_guesses>`")
            case 'homerball_leaderboard':
                await ctx.send(f"Missing argument {str(error.param).replace(': int', ' which is a number')}. Correct form is `!homerball_leaderboard <min_guesses>`")
    else:
        await ctx.send(error)

# @tree.error
# async def error_handler(interaction, error):
#     if isinstance(error, app_commands.MissingRole):
#         print("We're here")
#         await interaction.response.send_message("Hey, you're not a scouter! You can't do this!")
#     else:
#         await interaction.response.send_message(error)


bot.run(config["DISCORD_KEY"])
