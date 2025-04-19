from discord import app_commands

NETWORK_CHOICES = [
    app_commands.Choice(name="all", value="all"),
    app_commands.Choice(name="arbitrum", value="arbitrum"),
    app_commands.Choice(name="avax", value="avax"),
    app_commands.Choice(name="base", value="base"),
    app_commands.Choice(name="berachain", value="berachain"),
    app_commands.Choice(name="bsc", value="bsc"),
    app_commands.Choice(name="ethereum", value="eth"),
    app_commands.Choice(name="fantom", value="fantom"),
    app_commands.Choice(name="monad", value="monad"),
    app_commands.Choice(name="optimism", value="optimism"),
    app_commands.Choice(name="polygon", value="polygon"),
    app_commands.Choice(name="solana", value="solana"),
    app_commands.Choice(name="sonic", value="sonic"),
    app_commands.Choice(name="sui", value="sui"),
]
