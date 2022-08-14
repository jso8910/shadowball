from dotenv import dotenv_values
config = dotenv_values(".env")
import discord
from discord import app_commands
from discord.ui import Select, View
from sheets import ShadowballSheet
from table2ascii import table2ascii

class aclient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.synced = False
    
    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync(guild = discord.Object(id = config['GUILD_ID'])) # Testing server id
            self.synced = True
        print(f"We have logged in as {self.user}")

client = aclient()
sheet = ShadowballSheet()
tree = app_commands.CommandTree(client)

@tree.command(name = "add_game", description = "Add a new game", guild = discord.Object(id = config['GUILD_ID']))
@app_commands.checks.has_role("S8 General Manager")
async def add_game(interaction: discord.Interaction, home_team: str, away_team: str, date: str):
    await interaction.response.defer()
    sheet.new_game(away_team, home_team, date)
    await interaction.followup.send(f"Created a new game! {away_team} v {home_team} {date}", ephemeral=True)

@tree.command(name = "set_game", description = "Set the current game", guild = discord.Object(id = config['GUILD_ID']))
@app_commands.checks.has_role("S8 General Manager")
async def set_game(interaction: discord.Interaction):
    await interaction.response.defer()
    games = sheet.get_games()
    sel = Select(options=[
        discord.SelectOption(label=title) for title in games
        ])
    async def callback(interaction):
        if "S8 General Manager" in [y.name for y in interaction.user.roles]:
            await interaction.response.send_message(sheet.set_game(sel.values[0]) or f"Set game to: {sel.values[0]}")
        else:
            await interaction.response.send_message("You aren't a general manager, stop trying to do this." + str(interaction.user.roles), ephemeral=True)
    sel.callback = callback
    view = View()
    view.add_item(sel)
    await interaction.followup.send(f"Set the game that's going on now", view=view, ephemeral=True)

@tree.command(name = "input_pitch", description = "Enter the pitch that was entered as well as the maximum difference that is a home run", guild = discord.Object(id = config['GUILD_ID']))
@app_commands.checks.has_role("S8 General Manager")
async def input_pitch(interaction: discord.Interaction, pitch: int, homer_diff: int):
    await interaction.response.defer()
    sheet.finish_pitch(pitch, homer_diff)
    await interaction.followup.send(f"Updated the leaderboard with the most recent pitch and got things ready for the next pitch!")

@tree.command(name = "guess", description = "Make your shadowball guess", guild = discord.Object(id = config['GUILD_ID']))
async def guess(interaction: discord.Interaction, number: int):
    await interaction.response.defer()
    updated_guess = sheet.make_guess(interaction.user, number)
    await interaction.followup.send(f"{'Updated' if updated_guess else 'Set'} your guess for this pitch as {number}.")

@tree.command(name = "leaderboard", description = "Get shadowball leaderboard. Remember to input the minimum number of guesses!", guild = discord.Object(id = config['GUILD_ID']))
async def leaderboard(interaction: discord.Interaction, min_guesses: int):
    await interaction.response.defer()
    leaderboard = sheet.get_leaderboard(min_guesses)
    output = table2ascii(
        header=["Name", "# of Guesses", "Points", "PPG"],
        body=[row + [round(int(row[2]) / int(row[1]), 3)] for row in leaderboard],
    )
    await interaction.followup.send(f"Leaderboard of all qualifying players (more than {min_guesses} guesses) sorted by points per guess (PPG)```\n{output}\n```")

@tree.command(name = "homerball_lb", description = "Get homerball leaderboard. Remember to input the minimum number of guesses!", guild = discord.Object(id = config['GUILD_ID']))
async def homerball_leaderboard(interaction: discord.Interaction, min_guesses: int):
    await interaction.response.defer()
    leaderboard = sheet.get_homerball_lb(min_guesses)
    output = table2ascii(
        header=["Name", "# of Homers", "# of Guesses"],
        body=[[row[1]] + [row[2]] + [row[3]] for row in leaderboard],
    )
    await interaction.followup.send(f"Leaderboard of all qualifying players (more than {min_guesses} guesses) sorted by points per guess (PPG)```\n{output}\n```")


@tree.error
async def error_handler(interaction, error):
    if isinstance(error, app_commands.MissingRole):
        print("We're here")
        await interaction.response.send_message("Hey, you're not a GM! You can't do this!", ephemeral = True)
    else:
        await interaction.followup.send(error, ephemeral = True)

client.run(config["DISCORD_KEY"])