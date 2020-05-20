import json
import asyncio
from modules import hooker_db
from modules import booru_worker


def load_config():
    with open('config.json', 'r') as f:
        config = json.load(f)
    f.close()
    return config


async def main():
    # load our config file
    config = load_config()

    # load database object
    database = hooker_db.DB_object()

    task_list = []

    # ensure there's a table for our search references
    for search_ref in config:

        table_name = await database.fix_table_names(search_ref['criteria'] + str(search_ref['NSFW']))
        try:
            await database.make_table(table_name)
        except:
            pass

    for conf in config:
        task_list.append(loop.create_task(booru_worker.SearchTask(database, conf).main()))

    # let our asynchronous task run...
    await asyncio.wait(task_list)


if __name__ == '__main__':
    # Declare event loop
    loop = asyncio.get_event_loop()
    # Run the code until completing all task
    loop.run_until_complete(main())
    # Close the loop
    loop.close()
