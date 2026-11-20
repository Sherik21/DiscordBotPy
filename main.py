import asyncio
from bot.bot import Bot

def main():
    bot = Bot()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
   main()