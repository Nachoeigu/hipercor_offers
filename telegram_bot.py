import os
import requests
from dotenv import load_dotenv
class TelegramBot:

    def __init__(self, user):
        load_dotenv()
        print("Setting the Telegram Bot")
        self.token = os.getenv('TELEGRAM_TOKEN')
        if user == 'jose':
            self.chat_id = os.getenv('TELEGRAM_CHATID_JOSE')
        elif user == 'nacho':
            self.chat_id = os.getenv('TELEGRAM_CHATID_NACHO')
        self.url = "https://api.telegram.org/bot"+ self.token + "/sendMessage" + "?chat_id=" + self.chat_id + "&text="

    def send_message(self, text):
        requests.get(self.url + text)     
