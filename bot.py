import logging
from disnake.ext import commands
import dotenv
import os
import asyncio
from server import run_server
from util.database import Database
import json
import threading
from tendo import singleton

try:
    instance = singleton.SingleInstance() 
except singleton.SingleInstanceException:
    exit()

class CaddieBot(commands.InteractionBot):
    def __init__(self, config: dict, **options):
        super().__init__(**options)
        self.database = Database(config['db_connection'])
        self.debug: bool = config['debug']
        self.logger = logging.getLogger('disnake')

    async def on_ready(self):
        self.logger.info(f'PID: {os.getpid()}')
        self.logger.info(f'Logged in as {self.user}')

async def main():
    bot_token = os.getenv("BOT_TOKEN")
    with open('bot_config.json') as config_file:
        config: dict = json.load(config_file)

    log_path = config['log_file']
    log_dir = os.path.dirname(log_path)
    log_file = os.path.basename(log_path)
    home_dir = os.path.expanduser("~")
    log_dir = os.path.join(home_dir, log_dir)
    log_path = os.path.join(log_dir, log_file)
    os.makedirs(log_dir, exist_ok=True)

    bot_logger = logging.getLogger('disnake')
    bot_logger.setLevel(logging.INFO)
    log_file_handler = logging.FileHandler(log_path, mode='a')
    log_file_handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
    bot_logger.addHandler(log_file_handler)
    
    bot = CaddieBot(config) 
    bot.load_extensions("exts")

    try:
        await bot.start(bot_token)
    except InterruptedError:
        pass
    except BaseException:
        pass
    finally:
        bot.logger.info('Logging out of session...')
        await bot.close()

if __name__ == "__main__":
    dotenv.load_dotenv()
    threading.Thread(target=run_server).start()
    asyncio.run(main())
