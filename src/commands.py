from ai_handler import ai_process
from enum import Enum

class Commands(str, Enum):
    META   = "meta"
    NEWS   = "news"
    HELP   = "help"
    GITHUB = "github"

COMMAND_RESPONSE_MAP = {
    Commands.HELP   : """Available commands:
    !help   - Show all available commands.
    !meta   - Display the current top 3 meta champions for each role.
    !news   - Get the latest League of Legends patch notes and updates.
    !github - View the bot's GitHub repository.
    """,
    Commands.META   : "What are the top 3 highest win rate champions for each roles (Top, mid, jg, support, adc) in the game now?",
    Commands.NEWS   : "Get the latest League of Legends patch notes and summarize it.",
    Commands.GITHUB : "GitHub Repository: https://github.com/JunRong19",
}

async def execute_command(command:Commands) -> str:
    """Execute user's command."""
    command = command.lower()

    try:
        command_key = Commands(command[1:]) # Ignore the !
    except ValueError:
        return "Invalid command. Type !help to see all available commands."
    
    match command_key:
        case Commands.META:
            return await ai_process(COMMAND_RESPONSE_MAP[command_key])
        case Commands.NEWS:
            return await ai_process(COMMAND_RESPONSE_MAP[command_key])
        case Commands.HELP:
            return COMMAND_RESPONSE_MAP[command_key]
        case Commands.GITHUB:
            return COMMAND_RESPONSE_MAP[command_key]