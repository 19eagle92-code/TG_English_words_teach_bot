print("Hello! I am an English words teach bot!")

from dotenv import load_dotenv
import os

load_dotenv()
secret = os.getenv("TG_BOT_TOKEN")
