import json
import asyncio
from modules import danbooru


def load_config():
    with open('config.json', 'r') as f:
        config = json.load(f)
    f.close()
    return config


async def main():
    # load our config file
    config = load_config()

    task_list = []

    # load danbooru workers
    for custom_searches in config['Danbuuro']:
        task_list.append(loop.create_task(danbooru.DanbooruWorker(custom_searches['criteria'],
                                                                  custom_searches['Discord uri'],
                                                                  custom_searches['NSFW'],
                                                                  custom_searches['Ignore']).main()))
    # let our asynchronous task run...
    await asyncio.wait(task_list)


if __name__ == '__main__':
    # Declare event loop
    loop = asyncio.get_event_loop()
    # Run the code until completing all task
    loop.run_until_complete(main())
    # Close the loop
    loop.close()
