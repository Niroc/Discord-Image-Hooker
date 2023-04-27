import aiosqlite


class DB_object():
    def __init__(self):
        self.db_name = "Discord_Image_Hooker_SQLite.db"


    async def make_table(self, table_name):
        create_table_query = "CREATE TABLE IF NOT EXISTS %s (md5 CHARACTER(32) PRIMARY KEY);" % await self.fix_start_with_numbers(table_name)
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(create_table_query)
            await db.commit()

    async def check_for_value(self, table_name, md5):
        # use TOP to terminate loop after finding first record
        check_table_query = "SELECT EXISTS (SELECT md5 FROM %r WHERE md5 = %r) LIMIT 1" % (await self.fix_start_with_numbers(table_name), md5)
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute(check_table_query)
            total_number_of_rows = await cursor.fetchone()
            await cursor.close()
        # if no results are returned in total_rows then, the key doesn't exist
        return total_number_of_rows

    async def add_md5_checksum(self, table_name, md5):
        md5_insert_query = "INSERT INTO %r (md5) VALUES (%r)" % (await self.fix_start_with_numbers(table_name), md5)
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(md5_insert_query)
            await db.commit()

    async def fix_table_names(self, name):
        # fix any illegal table names
        offenders = " `~!@#$%^&*()-_=+[{]};:',<.>/?"
        for o in offenders:
            name = str(name).replace(o, '')
        return name

    async def fix_start_with_numbers(self, item):
        # table names can't start with a number
        if item[0].isdigit():
            return "a" + item
        else:
            return item
