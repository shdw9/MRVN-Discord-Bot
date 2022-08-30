from discord.ext import commands
from discord.ext.commands import CommandNotFound
import discord, asyncio, datetime, random, asyncio, json, requests

APIKEY = "" #TRN API KEY

rankedStats = {}

players = ["player1","player2","player3"]

notificationChannelId = ""

bot = commands.Bot(command_prefix='!')

def getApexProfile(username):
    r = requests.get(f"https://public-api.tracker.gg/apex/v1/standard/profile/5/{username}",headers={"TRN-Api-Key":APIKEY})
    return json.loads(r.text)

def getRankedStats(profile):
    rankInfo = []
    for x in profile["stats"]:
        if x["metadata"]["key"] == "RankScore" or x["metadata"]["key"] == "ArenaRankScore":
            rankInfo.append(x)
    return rankInfo

def getRankInformation(username):
    profile = getApexProfile(username)["data"]
    
    rankedInfo = getRankedStats(profile)
    rankNameBR = rankedInfo[0]["metadata"]["description"]
    rankPointsBR = rankedInfo[0]["value"]
    rankNameArena = rankedInfo[1]["metadata"]["description"]
    rankPointsArena = rankedInfo[1]["value"]
    avatarUrl = profile["metadata"]["avatarUrl"]
    level = profile["metadata"]["level"]

    # save to hashmap
    rankedStats[username]=[{"rank":rankNameBR,"rp":rankPointsBR},{"rank":rankNameArena,"rp":rankPointsArena}]

    return [username,level,avatarUrl,rankNameBR,rankPointsBR,rankNameArena,rankPointsArena,profile["metadata"]["rankImage"]]

async def checkRank(player):
    profile = getApexProfile(player)["data"]
    rankedInfo = getRankedStats(profile)
    rankNameBR = rankedInfo[0]["metadata"]["description"]
    rankPointsBR = rankedInfo[0]["value"]
    rankNameArena = rankedInfo[1]["metadata"]["description"]
    rankPointsArena = rankedInfo[1]["value"]
    rankImage = profile["metadata"]["rankImage"]
    avatarUrl = profile["metadata"]["avatarUrl"]

    async def rankUpdate(queue,old,new,rankImage,avatarUrl):
        embed=discord.Embed(timestamp=datetime.datetime.utcnow(), color=0xff00ff)
        embed.set_author(name="🚨 " + player.upper() + " RANK UPDATE 🚨",icon_url=avatarUrl)
        embed.add_field(name=queue.upper(),value=old + " **>>>** " + new)
        embed.set_footer(text="powered by shdw 👻",icon_url="https://i.imgur.com/ri6NrsN.png")
        embed.set_image(url=rankImage)
        await bot.get_channel(int(notificationChannelId)).send(embed=embed)

    async def lossRP(queue,old,new,avatarUrl,rank):
        embed=discord.Embed(description="*-" + str(int(old) - int(new)) + "* RP in " + queue,timestamp=datetime.datetime.utcnow(), color=0xE7548C)
        embed.set_author(name="🚨 " + player.upper() + " RP UPDATE 🚨",icon_url=avatarUrl)
        embed.add_field(name=queue.upper(),value=rank + " - " + str(new) + " RP")
        embed.set_footer(text="powered by shdw 👻",icon_url="https://i.imgur.com/ri6NrsN.png")
        embed.set_thumbnail(url="https://i.imgur.com/bTORHF3.png")
        await bot.get_channel(int(notificationChannelId)).send(embed=embed)
    
    async def gainRP(queue,old,new,avatarUrl,rank):
        embed=discord.Embed(description="**+" + str(int(new)-int(old)) + "** RP in " + queue,timestamp=datetime.datetime.utcnow(), color=0x62C979)
        embed.set_author(name="🚨 " + player.upper() + " RP UPDATE 🚨",icon_url=avatarUrl)
        embed.add_field(name=queue.upper(),value=rank + " - " + str(new) + " RP")
        embed.set_footer(text="powered by shdw 👻",icon_url="https://i.imgur.com/ri6NrsN.png")
        embed.set_thumbnail(url="https://i.imgur.com/0m1B3Et.png")
        await bot.get_channel(int(notificationChannelId)).send(embed=embed)

    # br
    if not rankNameBR == rankedStats[player][0]["rank"]:
        await rankUpdate("Battle Royale",rankedStats[player][0]["rank"],rankNameBR,rankImage,avatarUrl)
    elif int(rankPointsBR) < int(rankedStats[player][0]["rp"]):
        await lossRP("Battle Royale",rankedStats[player][0]["rp"],rankPointsBR,avatarUrl,rankNameBR)
    elif int(rankPointsBR) > int(rankedStats[player][0]["rp"]):
        await gainRP("Battle Royale",rankedStats[player][0]["rp"],rankPointsBR,avatarUrl,rankNameBR)

    # arenas
    if not rankNameArena == rankedStats[player][1]["rank"]:
        await rankUpdate("Arenas",rankedStats[player][1]["rank"],rankNameArena,rankImage,avatarUrl)
    elif int(rankPointsArena) < int(rankedStats[player][1]["rp"]):
        await lossRP("Arenas",rankedStats[player][1]["rp"],rankPointsArena,avatarUrl,rankNameArena)
    elif int(rankPointsArena) > int(rankedStats[player][1]["rp"]):
        await gainRP("Arenas",rankedStats[player][1]["rp"],rankPointsArena,avatarUrl,rankNameArena)

    rankedStats[player]=[{"rank":rankNameBR,"rp":rankPointsBR},{"rank":rankNameArena,"rp":rankPointsArena}]
        
async def background_task():
    await bot.wait_until_ready()
    print("Updating " + str(len(players)) + " profiles ...")
    for x in players:
        getRankInformation(x)
    print("Finished updating " + str(len(players)) + " profiles.")
    print("Beginning rank monitoring for " + str(len(players)) + " players ...")
    while(True):
        for x in players:
            await checkRank(x)
            await asyncio.sleep(20)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=5, name="Apex Legends"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return
    raise error

@bot.command()
async def apex(ctx, username):
    try:
        profile = getRankInformation(username)
        print(f"Pulled {username}'s APEX data .")
    except:
        await ctx.reply("That player does not exist!")
        return
    embed=discord.Embed(description="Level " + str(profile[1]),timestamp=datetime.datetime.utcnow())
    embed.set_author(name=username + "'s stats",icon_url=profile[2])
    embed.set_thumbnail(url=profile[7])
    embed.set_footer(text="from apex.tracker.gg")
    embed.add_field(name="Battle Royale",value=profile[3] + " - " + str(profile[4]))
    embed.add_field(name="Arenas",value=profile[5] + " - " + str(profile[6]))
    await ctx.reply(embed=embed)

bot.loop.create_task(background_task())

bot.run("")
