import asyncio
import aiohttp
import json
from telethon import TelegramClient, events
import logging

logging.basicConfig(filename='bot_log.log', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Telegram API настройки
api_id = 1028279
api_hash = 'd202f2bedb4087154fcb94b85f95cb0c'
bot_token = '6716101251:AAEPXVSIAo_rH18fTvIlgRK9mhcMX55p0xQ'

# Функция для загрузки данных о сессиях
def load_sessions():
    try:
        with open('sessions.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Функция для сохранения данных о сессиях
def save_session(phone_number, username, webhook_url):
    sessions = load_sessions()
    sessions[phone_number] = {'username': username, 'webhook_url': webhook_url}
    with open('sessions.json', 'w') as file:
        json.dump(sessions, file)

async def send_to_webhook(webhook_url, data):
    logging.info(f"Отправка данных на {webhook_url}: {data}")  # Замена print на logging.info
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, json=data) as response:
            response_text = await response.text()
            if response.status == 200:
                logging.info(f"Данные успешно отправлены на {webhook_url}")  # Замена print на logging.info
            else:
                logging.error(f"Ошибка при отправке данных: {response.status}, Ответ: {response_text}")  # Замена print на logging.error
async def monitor_account(client, expected_username, webhook_url):
    @client.on(events.NewMessage)
    async def handler(event):
        # Получаем информацию о пользователе, который отправил сообщение
        sender = await event.get_sender()
        sender_username = sender.username if sender else None  # Получаем имя пользователя отправителя

        # Сравниваем имя пользователя отправителя с ожидаемым именем
        if event.is_private and sender_username == expected_username:
            data = {"from": sender_username, "text": event.message.text,"token": 'asfjadkhfakdfuwi34u194u210edsahd', "number": client.session.filename.split('_')[1]}
            await send_to_webhook(webhook_url, data)
    await client.start()
    print(f"Мониторинг аккаунта {client.session.filename}...")
    await client.run_until_disconnected()

async def start_bot():
    bot = TelegramClient('bot', api_id, api_hash)
    await bot.start(bot_token=bot_token)

    active_auth_requests = set()

    # Загрузка и возобновление мониторинга для сохраненных сессий
    saved_sessions = load_sessions()
    for phone_number, session_info in saved_sessions.items():
        session_name = f'session_{phone_number}_{session_info["username"]}'
        client = TelegramClient(session_name, api_id, api_hash)
        asyncio.create_task(monitor_account(client, session_info["username"], session_info["webhook_url"]))

    @bot.on(events.NewMessage(pattern='/add'))
    async def add_account_handler(event):
        try:
            split_text = event.message.text.split(maxsplit=3)
            if len(split_text) == 4:
                _, phone_number, username, webhook_url = split_text

                # Уникальное имя сессии для каждой пары номера телефона и имени бота
                session_name = f'session_{phone_number}_{username}'
                client = TelegramClient(session_name, api_id, api_hash)
                await client.connect()

                if not await client.is_user_authorized():
                    if phone_number not in active_auth_requests:
                        active_auth_requests.add(phone_number)
                        await client.send_code_request(phone_number)
                        await event.respond('Введите код аутентификации от Telegram:')

                        # Ожидание ввода кода аутентификации
                        @bot.on(events.NewMessage(incoming=True, from_users=event.sender_id))
                        async def wait_for_code(code_event):
                            if code_event.message.text.isdigit():
                                code = code_event.message.text.strip()
                                try:
                                    await client.sign_in(phone_number, code)
                                    active_auth_requests.remove(phone_number)
                                    asyncio.create_task(monitor_account(client, username, webhook_url))
                                    save_session(phone_number, username, webhook_url)
                                    await event.respond(f'Аккаунт {phone_number} добавлен и начал мониторинг.')
                                except Exception as e:
                                    await event.respond(f'Ошибка входа: {e}')
                                finally:
                                    bot.remove_event_handler(wait_for_code)

                    else:
                        await event.respond(f'Процесс аутентификации для {phone_number} уже идет.')
                else:
                    save_session(phone_number, username, webhook_url)
                    asyncio.create_task(monitor_account(client, username, webhook_url))
                    await event.respond(f'Бот {username} добавлен к аккаунту {phone_number}.')
            else:
                await event.respond('Используйте /add <номер телефона> <username> <webhook_url>')
        except Exception as e:
            await event.respond(f'Произошла ошибка: {e}')

    print("Бот запущен...")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(start_bot())