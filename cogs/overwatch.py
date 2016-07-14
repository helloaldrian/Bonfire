from .utils import config
from discord.ext import commands
import discord

import urllib.parse
import urllib.request
import urllib.error
import json

base_url = "https://owapi.net/api/v2/u/"
check_g_stats = ["eliminations","deaths",'kpd','wins','losses','time_played',
                'cards','damage_done','healing_done','multikills']
check_o_stats = ['wins','losses']

class Overwatch:
    """Class for viewing Overwatch stats"""
    def __init__(self, bot):
        self.bot = bot

    @commands.group(no_pm=True)
    async def ow(self):
        pass

    @ow.command(name="stats", pass_context=True, no_pm=True)
    async def ow_stats(self, ctx, user: discord.Member=None, hero: str=""):
        """Command used to lookup information on your own user, or on another's
        When adding your battletag, it is quite picky, use the exact format user#xxxx
        Multiple names with the same username can be used, this is why the numbers are needed
        Capitalization also matters"""
        if user is None:
            user = ctx.message.author
        cursor = config.getCursor()
        cursor.execute('use {}'.format(config.db_default))
        cursor.execute('select battletag from overwatch where id=%s', (user.id,))
        result = cursor.fetchone()
        config.closeConnection()
        if result is None:
            await self.bot.say("I do not have this user's battletag saved!")
            return
        bt = result['battletag']
        await self.bot.say("Searching profile information....")
        
        try:
            if hero == "":
                result = urllib.request.urlopen(base_url + "{}/stats/general".format(bt))
                data = json.loads(result.read().decode('utf-8'))
                fmt = "\n".join("{}: {}".format(i, r) for i, r in data['game_stats'].items() if i in check_g_stats)
                fmt += "\n"
                fmt += "\n".join("{}: {}".format(i, r) for i, r in data['overall_stats'].items() if i in check_o_stats)
                await self.bot.say("Overwatch stats for {}: ```py\n{}```".format(user.name, fmt.title().replace("_", " ")))
            else:
                result = urllib.request.urlopen(base_url + "{}/heroes/{}".format(bt, hero.lower().replace('-', '')))
                data = json.loads(result.read().decode('utf-8'))
                fmt = "\n".join("{}: {}".format(i, r) for i, r in data['general_stats'].items() if i in check_g_stats)
                fmt += "\n"
                fmt += "\n".join("{}: {}".format(i, r) for i, r in data['hero_stats'].items())
                await self.bot.say("Overwatch stats for {} using the hero {}: ```py\n{}``` "
                                   .format(user.name, hero.title(), fmt.title().replace("_", " ")))
        except urllib.error.HTTPError as error:
            error_no = int(re.search("\d+",str(error)).group(0))
            if error_no == 500:
                await self.bot.say("{} has not used the hero {} before!".format(user.name, hero.title()))
            elif error_no == 400:
                await self.bot.say("{} is not an actual hero!".format(hero.title())

    @ow.command(pass_context=True, name="add")
    async def add(self, ctx, bt: str):
        """Saves your battletag for looking up information"""
        bt = bt.replace("#", "-")
        await self.bot.say("Looking up your profile information....")
        url = base_url + "{}/stats/general".format(bt)
        try:
            urllib.request.urlopen(url)
        except urllib.error.HTTPError:
            await self.bot.say("Profile does not exist! Battletags are picky, "
                               "format needs to be `user#xxxx`. Capitalization matters")
            return
        cursor = config.getCursor()
        cursor.execute('use {}'.format(config.db_default))
        cursor.execute('select * from overwatch where id=%s', (ctx.message.author.id,))
        result = cursor.fetchone()
        if result:
            cursor.execute('update overwatch set battletag=%s where id=%s', (bt, ctx.message.author.id))
            await self.bot.say("I have updated your saved battletag {}".format(ctx.message.author.mention))
        else:
            cursor.execute('insert into overwatch (id, battletag) values (%s, %s)', (ctx.message.author.id, bt))
            await self.bot.say("I have just saved your battletag {}".format(ctx.message.author.mention))
        config.closeConnection()

    @ow.command(pass_context=True, name="delete", aliases=['remove'])
    async def delete(self, ctx):
        """Removes your battletag from the records"""
        cursor = config.getCursor()
        cursor.execute('use {}'.format(config.db_default))
        cursor.execute('select * from overwatch where id=%s', (ctx.message.author.id,))
        result = cursor.fetchone()
        if result:
            cursor.execute('delete from overwatch where id=%s', (ctx.message.author.id,))
            await self.bot.say("I no longer have your battletag saved {}".format(ctx.message.author.mention))
        else:
            await self.bot.say("I don't even have your battletag saved {}".format(ctx.message.author.mention))
        config.closeConnection()


def setup(bot):
    bot.add_cog(Overwatch(bot))