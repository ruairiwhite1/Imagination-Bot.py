from asyncio import sleep
from datetime import datetime
from glob import glob

from discord import Intents
from discord import Embed, File
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from discord.ext.commands import (CommandNotFound, BadArgument, MissingRequiredArgument)
from discord.errors import HTTPException
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import Context

from ..db import db

PREFIX = "+"
OWNER_IDS = [616926646657744898]
COGS = [path.split("/")[-1][:-3] for path in glob("./lib/cogs/*.py")]
IGNORE_EXCEPTIONS = (CommandNotFound, BadArgument)


class Ready(object):
    def __init__(self):
        for cog in COGS:
            setattr(self, cog, False)

    def ready_up(self, cog):
        setattr(self, cog, True)
        print(f" {cog} cog ready")

    def all_ready(self):
        return all([getattr(self, cog) for cog in COGS])


class Bot(BotBase):
    def __init__(self):
        self.PREFIX = PREFIX
        self.ready = False
        self.cogs_ready = Ready()

        self.guild = None
        self.scheduler = AsyncIOScheduler()

        db.autosave(self.scheduler)
        super().__init__(
            command_prefix=PREFIX, owner_ids=OWNER_IDS, intents=Intents.all()
        )

    def setup(self):
        for cog in COGS:
            self.load_extension(f"lib.cogs.{cog}")
            print(f" {cog} cog loaded")

        print("setup complete")

    def run(self, version):
        self.VERSION = version

        print("running setup...")
        self.setup()

        with open("./lib/bot/token.0", "r", encoding="utf-8") as tf:
            self.TOKEN = tf.read()

        print("running bot...")
        super().run(self.TOKEN, reconnect=True)

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=Context)

        if ctx.command is not None and ctx.guild is not None:
            if self.ready:
                await self.invoke(ctx)

            else:
                await ctx.send("I am not ready to recieve commands. Please wait a few seconds.")

        print("running bot...")
        super().run(self.TOKEN, reconnect=True)

    async def rules_reminder(self):
        channel = self.stdout.send(647403000205410305)
        await self.stdout.send("Remember to adhere to the rules!")

    async def on_connect(self):
        print("Bot connected")

    async def on_disconnect(self):
        print("Bot disconnected")

    async def on_error(self, err, *args, **kwargs):
        if SystemError == "on_command_error":
            await args[0].send("Uh oh, that wasn't supposed to happen.")

        await self.stdout.send("An error occured.")
        raise

    async def on_command_error(self, context, exception):
        if any([isinstance(exc, error) for error in IGNORE_EXCEPTIONS]):
            pass

        elif isinstance(exc, MissingRequiredArgument):
            await ctx.send("One or more required arguments are missing.")

        elif isinstance(exc.original, HTTPException):
            await ctx.send("Unable to send message.")

        elif isinstance(exc.original, Forbidden):
            await ctx.send("I do not have permission to do that.")

        else:
            raise exc.original

    async def on_ready(self):
        if not self.ready:
            self.ready = True
            self.guild = self.get_guild(655105137244766259)
            self.stdout = self.get_channel(647403000205410305)
            self.scheduler.add_job(
                self.rules_reminder,
                CronTrigger(day_of_week=0, hour=12, minute=0, second=0),
            )
            self.scheduler.start()

            await self.stdout.send("Have no fear, the Imagination Bot is here!")

            while not self.cogs_ready.all_ready():
                await sleep(0.5)

            await self.stdout.send("Now online")
            self.ready = True
            print("Bot ready")

        else:
            print("Bot reconnected")

    async def on_message(self, message):
        if not message.author.bot:
            await self.process_commands(message)


bot = Bot()

