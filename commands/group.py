import discord
from discord import app_commands

from commands.matrix import MatrixCommand
from commands.find import FindCommand
from commands.react import ReactCommand
from commands.help import HelpCommand

class GemHunterGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="gemhunter", description="The ultimate gem analyzer")
        self.add_command(MatrixCommand())
        self.add_command(FindCommand())
        self.add_command(ReactCommand())
        self.add_command(HelpCommand())
