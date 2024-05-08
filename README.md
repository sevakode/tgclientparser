**Telegram Monitoring Bot**
==========================

This project represents a Telegram bot that allows adding and monitoring Telegram accounts, sending messages to a specified webhook URL.

**Dependencies**
---------------

* Python 3.7 or higher
* aiohttp==3.9.5
* python-dotenv==1.0.1
* Telethon==1.35.0

**Setup**
--------

1. Clone the repository:
```
git clone https://github.com/sevakode/tgclientparser.git
```
2. Navigate to the project directory:
```
cd tgclientparser
```
3. Install dependencies:
```
pip install -r requirements.txt
```
4. Create a `.env` file in the project root and add the following environment variables:
```
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
```
Replace `your_api_id`, `your_api_hash`, and `your_bot_token` with the corresponding values obtained from Telegram.

**Running**
---------

To start the bot, run the following command:
```
python app.py
```
**Usage**
---------

### Adding an account for monitoring

To add an account for monitoring, use the following command:
```
/add <phone_number> <username> <webhook_url>
```
Replace `<phone_number>`, `<username>`, and `<webhook_url>` with the corresponding values. The bot will request an authentication code, which you will need to enter.

After successful authentication, the bot will start monitoring the specified account and send messages to the specified webhook URL.

**Logging**
---------

The bot saves logs to the `bot_log.log` file in the project root. The logs contain information about sent messages and possible errors.
