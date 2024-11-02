# bot.py
from PIL import Image
import datetime
import discord
from discord.ext import commands
from discord import ButtonStyle
from discord.ui import Button, View
from dotenv import load_dotenv
from DebtManager import DebtManager
from Dice import Dice
from DiceImage import DiceImage
from PokerNightManager import PokerNightManager
from PokerNightManager import PokerNightOCR
from PIL import Image
from PIL import ImageDraw
import requests
from io import BytesIO
import os
import json
import sys
import random
import pandas as pd
import numpy as np
from tabulate import tabulate


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
EMBED_GENERATING_CHANNEL_ID=1239570801750048870
# Create a bot instance
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True    # Necessary for operating within guilds
intents.message_content = True  # Necessary to access the content of messages

bot = commands.Bot(command_prefix='!', intents=intents, description="This is a Dice Roll bot", help_command=None)
dm=DebtManager("./ledger.json")
di=DiceImage()
PNM=PokerNightManager()
PNOCR=PokerNightOCR()

#games[game_channel_id]={"active_game": Dice, "call_data": (False, 0)}
games={}
# Event listener for when the bot has switched from offline to online.
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

@bot.event
async def on_message(message):
    global games
    # Check if the message is from the bot itself or another bot
    if message.author.bot:
        return

    # Check if the message is a command
    if message.content.startswith(bot.command_prefix):
        # Process the command
        await bot.process_commands(message)
        return
    
    if str(message.channel.id) in games.keys():
        await message.delete()
    
    return;

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.message.delete();
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f'This command is on a cooldown, please wait.')
    else:
        raise error

#Diceroll game commands:
class DiceRollView(View):
    def __init__(self):
        super().__init__()
        
    @discord.ui.button(label="Roll", style=discord.ButtonStyle.blurple)
    async def roll(self, interaction: discord.Interaction, button: Button):
        global dm
        global games 
        
        call_data=games[str(interaction.channel_id)]["call_data"]
        active_game=games[str(interaction.channel_id)]["active_game"]
        
        if call_data[0]:
            await interaction.response.edit_message(content=f"PENDING RAISE REQUEST\n")
        elif active_game.round_started and active_game.p.index(interaction.user.name)==active_game.turn:
            roll_outcome=active_game.roll()
            message=""
            if roll_outcome==1:
                loser_p=active_game.round_loser()
                loser=active_game.p[loser_p]
                winner=active_game.p[(loser_p+1)%2]
                dm.update_data(loser, winner, active_game.current_bet)
                message="Press Go Agane to start another round"
            di.dice_game_image(roll_outcome, len(active_game.history), active_game.current_bet, active_game.p, active_game.scores, active_game.turn)
            embed=await generate_embed(di.dice_game_image_path, active_game.p)
            await interaction.response.edit_message(content=message, embed=embed)
            os.remove(di.dice_game_image_path)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="call raise", style=discord.ButtonStyle.green)
    async def callraise(self, interaction: discord.Interaction, button: Button):
        global games
        
        call_data=games[str(interaction.channel_id)]["call_data"]
        active_game=games[str(interaction.channel_id)]["active_game"]
        
        if call_data[0]:
            if interaction.user.id!=call_data[2].author.id and interaction.user.name in active_game.p:
                active_game.raise_the_stake(call_data[1])
                await call_data[2].delete()
                games[str(interaction.channel_id)]["call_data"]=(False, 0)
            di.dice_game_image(active_game.most_recent_roll(), len(active_game.history), active_game.current_bet, active_game.p, active_game.scores, active_game.turn)
            embed=await generate_embed(di.dice_game_image_path, active_game.p)
            await interaction.response.edit_message(content="", embed=embed)
            os.remove(di.dice_game_image_path)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="decline raise", style=discord.ButtonStyle.green)
    async def declineraise(self, interaction: discord.Interaction, button: Button):
        global games
        
        call_data=games[str(interaction.channel_id)]["call_data"]
        active_game=games[str(interaction.channel_id)]["active_game"]
        
        if call_data[0]:
            if interaction.user.id!=call_data[2].author.id and interaction.user.name in active_game.p:
                await call_data[2].delete()
                games[str(interaction.channel_id)]["call_data"]=(False, 0)
        await interaction.response.defer()
    
    @discord.ui.button(label="Go Agane", style=discord.ButtonStyle.blurple)
    async def goagane(self, interaction: discord.Interaction, button: Button):
        global di
        global games
        
        active_game=games[str(interaction.channel_id)]["active_game"]
        
        if interaction.user.name in active_game.p and not active_game.round_started:
            active_game.start_round(active_game.p.index(interaction.user.name))
            
            di.dice_game_image(0, len(active_game.history), active_game.current_bet, active_game.p, active_game.scores, active_game.turn)
            embed=await generate_embed(di.dice_game_image_path, active_game.p[0]+" VS "+active_game.p[1])
            await interaction.response.edit_message(content="", embed=embed)
            os.remove(di.dice_game_image_path)
        else:
            await interaction.response.defer()
        
    @discord.ui.button(label="Quitter", style=discord.ButtonStyle.red)
    async def quitter(self, interaction: discord.Interaction, button: Button):
        global games
        
        active_game=games[str(interaction.channel_id)]["active_game"]
        
        if interaction.user.name in active_game.p and not active_game.round_started:
            thread = bot.get_channel(interaction.channel_id)
            await thread.parent.send(content="FINAL SCORE\n"+active_game.score_toString())
            await thread.delete()
            del games[str(interaction.channel_id)]
            self.stop()
        else:
            pass;
   
    
#start game with dice roll
@bot.command()
async def dr(ctx, user: commands.MemberConverter()=None, starting_dice: int =200, starting_bet: int =1):
    # Send initial message
    global di
    global games
    
    if str(ctx.channel.id) in games.keys():
        await ctx.send("An active game already exists in this channel")
        return;
    
    if user==None:
        await ctx.send("Mention another user to challenge to dice")
        return;
    
    if not str(ctx.channel.id) in games.keys():
        active_game=Dice(ctx.author.name, user.name, starting_dice, starting_bet)
        active_game.start_game()
        
        thread_name = "Dice Roll: "+active_game.p[0]+" vs "+active_game.p[1]
        thread = await ctx.message.create_thread(name=thread_name)
        games[str(thread.id)]={}
        games[str(thread.id)]["active_game"]=active_game
        games[str(thread.id)]["call_data"]=(False, 0)
        
        di.dice_game_image(0, len(active_game.history), active_game.current_bet, active_game.p, active_game.scores, active_game.turn)
        embed=await generate_embed(di.dice_game_image_path, active_game.p[0]+" VS "+active_game.p[1])
        message = await thread.send(content="", embed=embed, view=DiceRollView())
        os.remove(di.dice_game_image_path)

#raise bet
@bot.command()
async def rb(ctx, value: int):
    global games
    
    if str(ctx.channel.id) in games.keys() and value > 0:
        active_game=games[str(ctx.channel.id)]["active_game"]
        if ctx.author.name in active_game.p and active_game.round_started:
            await ctx.message.delete()
            msg=await ctx.channel.send(content="**RAISE REQUEST OF "+str(value)+" BY "+ctx.author.name+"**")
            games[str(ctx.channel.id)]["call_data"]=(True, value, msg)
            
#get balance of this user
@bot.command()
async def ledger(ctx, user: commands.MemberConverter()=None):
    global dm
    global di
    global games
    
    name=ctx.author.name
    avatar_url = ctx.author.avatar.url
    
    #games[game_channel_id]={"active_game": Dice, "call_data": (False, 0)}
    if str(ctx.channel.id) in games.keys():
        await ctx.message.delete()
    
    if user!=None:
        name=user.name
        avatar_url=user.avatar.url
        
    response = requests.get(avatar_url)
    avatar_bytes = BytesIO(response.content)
    avatar_image = Image.open(avatar_bytes)
    
    di.ledger_image(name, dm.get_ledger(name), avatar_image)
    await ctx.send(file=discord.File(di.ledger_image_path))
    os.remove(di.ledger_image_path)
    
#help
@bot.command()
async def help(ctx):
    await ctx.send("Welcome to Dice Roll bot\n\n!dr @player starting_dice[optional] starting bet[optional] - use this command to start the game. Only 1 game active at a time for now. By default the person to start first round is the one that starts the game. Keep rolling until the round is over aka rolled a 1. Can choose to go agane once round over. Whoever clicks that button must roll first for the next round. Can only quit game at the end of a round, gotta follow through.\n\n!rb value - request a raise bet by the value, which will force all rolls to halt until the other player responds by calling or declining\n\n!ledger @player[optional] - will pull up the debts/winnings")  

@bot.command()
async def flex(ctx):
    global PNM
    await ctx.send(f"But what if we played flex instead though.. monkas - {ctx.author.name}")

@bot.command()
async def poker(ctx):
    global PNM
    await ctx.send(f"Fine, I'll poker - {ctx.author.name}")
    
#Poker Night commands:
class PlayerButton(Button):
    def __init__(self, label, player_name):
        super().__init__(style=ButtonStyle.primary, label=label)
        self.player_name = player_name

    async def callback(self, interaction):
        global PNM
        # Increment the counter for the player
        PNM.active_night_add_buyin(self.player_name)
        self.label = f"{self.player_name}: {PNM.active_night_player_data[self.player_name][0]}"
        await interaction.response.edit_message(view=self.view)


class FinishButton(Button):
    def __init__(self):
        super().__init__(style=ButtonStyle.success, label="FINISH")

    async def callback(self, interaction):
        global PNM
        await interaction.response.defer()
        
        s_name, s_link=PNM.create_new_sheet()
        
        #await interaction.response.send_message(f"{s_name} sheet created: {s_link}")
        await interaction.followup.send(f"{s_name} sheet created: {s_link}", ephemeral=False)
        
        # Disable all buttons after FINISH
        for item in self.view.children:
            item.disabled = True
            
        await interaction.message.edit(view=self.view)
        self.view.stop()
        
class AbortButton(Button):
    def __init__(self):
        super().__init__(style=ButtonStyle.danger, label="ABORT")

    async def callback(self, interaction):
        
        await interaction.followup.send("Track Aborted", ephemeral=False)
        
        # Disable all buttons after FINISH
        for item in self.view.children:
            item.disabled = True
            
        await interaction.message.edit(view=self.view)
        self.view.stop()
        
@bot.command()
async def track(ctx, *, names: str):
    global PNM
    normalized_input = names.replace(",", "\n")
    player_names = [name.strip().capitalize() for name in normalized_input.splitlines() if name.strip()]
    
    PNM.init_active_night_players(player_names)
    view = View(timeout=None)
    for name in player_names:
        button = PlayerButton(label=f"{name}: 1", player_name=name)
        view.add_item(button)

    finish_button = FinishButton()
    abort_button = AbortButton()
    view.add_item(finish_button)
    view.add_item(abort_button)
    await ctx.send("Track Buyins. Click button to add 1", view=view)

@bot.command()
async def scoreocr(ctx, night: int, image_url: str = None):
    global PNOCR
    global PNM
    
    if len(ctx.message.attachments) > 0:
        attachment = ctx.message.attachments[0]
        if attachment.content_type.startswith("image/"):
            image_url=attachment.url
    
    if image_url:
        try:
            name_score=PNOCR.process_image_from_url(image_url)
            await ctx.send("OCR result:\n```"+tabulate(name_score)+"```")
            
            try:
                norm_name_score=PNM.normalize_name_score(name_score)
            except:
                await ctx.send("Error matching names/alias from OCR result to player data (1st worksheet of google spreadsheet)")
                return;
            await ctx.send("OCR result:\n```"+tabulate(norm_name_score)+"```")    
            msg=PNM.add_scores_to_night(norm_name_score, night)
            await ctx.send(msg)
        except requests.exceptions.RequestException:
            await ctx.send("Invalid URL or failed to fetch the image. Please check the URL.")
    else:
        await ctx.send("No image uploaded or URL provided. Please attach an image or provide an image URL.")

@bot.command()
async def checkdata(ctx):
    global PNM
    await ctx.send(PNM.checkdata())

@bot.command()
async def leaderboard(ctx):
    global PNM
    await ctx.send(PNM.leaderboard())

@bot.command()
async def pokersheet(ctx):
    global PNM
    await ctx.send(PNM.gs_url)
    
@bot.command()
async def reconnect(ctx):
    global PNM
    await ctx.send(PNM.reconnect())

@bot.command()
async def stats(ctx, user: commands.MemberConverter()=None):
    global PNM
    
    name=ctx.author.name
    if user!=None:
        name=user.name
    
    output_path=PNM.personal_stats(name)
    await ctx.send(file=discord.File(output_path))
    os.remove(output_path)
    
@bot.command()
async def invite(ctx, channel_id: int=845885699080454167):
    """Create an invite link for a given channel ID."""
    # Fetch the channel by its ID
    channel = bot.get_channel(channel_id)
    
    # Check if the bot has permission to create an invite
    if channel and channel.permissions_for(ctx.guild.me).create_instant_invite:
        # Create the invite link
        invite = await channel.create_invite(max_uses=1, unique=True)  # Can customize max_uses, etc.
        await ctx.send(f"Here's your invite link: {invite}")
    else:
        await ctx.send("I don't have permission to create invites in that channel.")

@bot.command()
async def list_channels(ctx):
    """List all channel names and their IDs in the server."""
    channels = ctx.guild.channels
    response = ""
    for channel in channels:
        response += f"{channel.name} (ID: {channel.id})\n"
    
    await ctx.send(f"Channels in {ctx.guild.name}:\n{response}")
    
async def generate_embed(file_path, title, embed_channel_id=EMBED_GENERATING_CHANNEL_ID):
    embed_channel=bot.get_channel(embed_channel_id)
    file=discord.File(file_path)
    temp_message = await embed_channel.send(file = file)
    attachment = temp_message.attachments[0]
    embed = discord.Embed(title = title, description = "", color = 0x26ad00)
    embed.set_image(url = attachment.url)
    return embed

bot.run(TOKEN)