import os
import asyncio
import aiohttp
import json
import logging
from dotenv import load_dotenv
from telethon import TelegramClient, events, sync
load_dotenv()

logging.basicConfig(filename='bot_log.log', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')

def load_sessions():
    try:
        with open('sessions.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_session(phone_number, username, webhook_url):
    sessions = load_sessions()
    sessions[phone_number] = {'username': username, 'webhook_url': webhook_url}
    with open('sessions.json', 'w') as file:
        json.dump(sessions, file)

async def send_to_webhook(webhook_url, data):
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, json=data) as response:
            response_text = await response.text()
            if response.status == 200:
                logging.info(f"Data sent successfully to {webhook_url}")
            else:
                logging.error(f"Failed to send data: {response.status}, Response: {response_text}")

async def monitor_account(client, username, webhook_url):
    @client.on(events.NewMessage)
    async def handler(event):
        sender = await event.get_sender()
        sender_username = sender.username if sender else None
        if event.is_private and sender_username == username:
            data = {"from": sender_username, "text": event.message.text, "number": client.session.filename.split('_')[1]}
            await send_to_webhook(webhook_url, data)
    await client.start()
    logging.info(f"Monitoring account {client.session.filename}...")
    await client.run_until_disconnected()


async def list_sessions(bot):
    sessions = load_sessions()
    active_sessions = []
    inactive_sessions = []
    for phone_number, info in sessions.items():
        session_name = f'session_{phone_number}_{info["username"]}'
        client = TelegramClient(session_name, api_id, api_hash)
        if await client.is_connected():
            active_sessions.append((phone_number, info["username"]))
        else:
            inactive_sessions.append((phone_number, info["username"]))
    await bot.send_message('me', f"Active Sessions: {active_sessions}\nInactive Sessions: {inactive_sessions}")

async def get_recent_messages(client, number_of_messages=10):
    messages = await client.get_messages('me', limit=number_of_messages)
    return messages

@bot.on(events.NewMessage(pattern='/list'))
async def handle_list_sessions(event):
    await list_sessions(bot)

@bot.on(events.NewMessage(pattern='/get_recent_messages'))
async def handle_get_recent_messages(event):
    split_text = event.message.text.split()
    if len(split_text) == 2:
        _, number_of_messages = split_text
        number_of_messages = int(number_of_messages)
        messages = await get_recent_messages(bot, number_of_messages)
        formatted_messages = "\n".join([f"{msg.sender_id}: {msg.text}" for msg in messages])
        await event.respond(f"Recent Messages:\n{formatted_messages}")
    else:
        await event.respond("Usage: /get_recent_messages <number_of_messages>")

async def start_bot():
    bot = TelegramClient('bot', api_id, api_hash)
    await bot.start(bot_token=bot_token)
    active_auth_requests = set()
    saved_sessions = load_sessions()

    for phone_number, session_info in saved_sessions.items():
        session_name = f'session_{phone_number}_{session_info["username"]}'
        client = TelegramClient(session_name, api_id, api_hash)
        asyncio.create_task(monitor_account(client, session_info["username"], session_info["webhook_url"]))

    @bot.on(events.NewMessage(pattern='/add'))
    async def add_account_handler(event):
        split_text = event.message.text.split(maxsplit=3)
        if len(split_text) == 4:
            _, phone_number, username, webhook_url = split_text
            session_name = f'session_{phone_number}_{username}'
            client = TelegramClient(session_name, api_id, api_hash)
            await client.connect()
            if not await client.is_user_authorized():
                if phone_number not in active_auth_requests:
                    active_auth_requests.add(phone_number)
                    await client.send_code_request(phone_number)
                    await event.respond('Enter the Telegram authentication code:')
                    @bot.on(events.NewMessage(incoming=True, from_users=event.sender_id))
                    async def wait_for_code(code_event):
                        if code_event.message.text.isdigit():
                            code = code_event.message.text.strip()
                            try:
                                await client.sign_in(phone_number, code)
                                active_auth_requests.remove(phone_number)
                                asyncio.create_task(monitor_account(client, username, webhook_url))
                                save_session(phone_number, username, webhook_url)
                                await event.respond(f'Account {phone_number} added and monitoring started.')
                            except Exception as e:
                                await event.respond(f'Login error: {e}')
                            finally:
                                bot.remove_event_handler(wait_for_code)
                else:
                    await event.respond(f'Authentication process for {phone_number} is already in progress.')
            else:
                save_session(phone_number, username, webhook_url)
                asyncio.create_task(monitor_account(client, username, webhook_url))
                await event.respond(f'Bot {username} added to account {phone_number}.')
        else:
            await event.respond('Use /add <phone_number> <username> <webhook_url>')

    logging.info("Bot started...") 
    await bot.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(start_bot())
