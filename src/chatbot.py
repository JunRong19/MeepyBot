from dotenv import load_dotenv
load_dotenv()

import os

from lcu_driver import Connector
connector = Connector()

from lcu_api import LCUAPI
lcu = LCUAPI()

from ai_handler import ai_process
from guardrails import Guardrails, IS_VALID
guardrails = Guardrails()

from commands import execute_command

# Set your API key here.
if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = ""

blacklist = []

async def send_message(connection, puuid, message):
    """Send a message to a player using LCU."""
    res = await lcu.send_message_by_puuid(connection, puuid, message)

    if res:
        print("Message sent successfully!")

@connector.ready
async def connect(connection):
    """Fired when LCU API establish connection with league client."""
    print('LCU API is ready to be used.')

    # Check if the bot is already logged into its account
    bot = await lcu.get_bot_summoner(connection)
    if bot:
        os.environ["BOT_PUUID"] = bot['puuid']   # Cache the bot's UID.
        print(f"Bot is logged in as: {bot['gameName']}#{bot['tagLine']} (PUUID: {bot['puuid']})")
    else:
        print('Unable to get bot summoner data.')
        connector.stop()

@connector.close
async def disconnect(_):
    """Fired when League Client is closed (or disconnected from websocket)"""
    print('The client have been closed!')

@connector.ws.register('/lol-chat/v1/conversations/', event_types=('CREATE',))
async def on_new_message(connection, event):
    """Fired when a new message is received by the bot."""

    data = event.data
    if not data:
        return
    
    # print(event.data)

    player_puuid = data.get('fromPuuid')

    # Ignore no puuid, when friend get re-added with existing messages.
    if player_puuid is None:
        return
    
    # Ignore bot reply.
    if player_puuid == os.getenv("BOT_PUUID"):
        return
    
    # Ignore hidden messages.
    if data.get('body', '') == "joined_room" or data.get('body', '') == "left_room":
        return
    
    # Get player info using puuid.
    player = await lcu.get_player_by_puuid(connection, player_puuid)
    if not player:
        return

    # Extract player's query.
    message  = data.get('body', '')

    name     = player.get('gameName')
    tag      = player.get('tagLine')
    fullName = f"{name}#{tag}"
    print(f"New message from {fullName}: {message}")

    await send_message(connection, player_puuid, "Processing message, please wait...")

    # Handle commands.
    if message.startswith("!"):
        command_res = await execute_command(message)
        cleaned_command_response = await guardrails.validate_response(command_res)
        return await send_message(connection, player_puuid, cleaned_command_response)
    
    # Validate query.
    query_validate = await guardrails.validate_query(message)
    if (query_validate == IS_VALID.INVALID):
        return await send_message(connection, player_puuid, "Invalid message. It has to be related to League of Legends.")
        
    # Send message to AI to process message.
    response = await ai_process(message)    

    # Clean output.
    cleaned_response = await guardrails.validate_response(response)
    await send_message(connection, player_puuid, cleaned_response)

@connector.ws.register('/lol-chat/v2/friend-requests/', event_types=('CREATE','UPDATE'))
async def on_new_friend_request(connection, event):
    """Fired when a new friend request is received by the bot."""
    print("New friend request!")

    data = event.data
    if not data:
        return
    
    player_puuid = data.get('puuid')

    name     = data.get('gameName')
    tag      = data.get('tagLine')
    fullName = f"{name}#{tag}"

    if fullName in blacklist:
        print(f"Denied adding of blacklisted user: {fullName}")
        return 

    try:
        # Auto accept friend requests.
        await lcu.accept_friend_request(connection, player_puuid)
    except Exception as e:
        print(f"Unable to accept friend request: {e}")

    # Send welcome message.
    print(f"Added friend: {fullName}")
    await send_message(connection, player_puuid, "Thanks for trying Meepy Bot! Send a query or type !help to see available commands.")

connector.start()
