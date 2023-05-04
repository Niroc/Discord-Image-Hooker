import asyncio
from aiohttp_requests import requests
from bs4 import BeautifulSoup
from datetime import datetime


class REALBOORUSettings:
    def __init__(self):
        self.board_name = "REALBOORU"

        self.Initialize_URL = "https://realbooru.com/index.php?page=dapi&s=post&q=index&tags=%s&limit=10&json=1"
        self.Scrape_URL = "https://realbooru.com/index.php?page=dapi&s=post&q=index&tags=%s+id:%%3E=%i&json=1"
        self.Main_URL = "https://realbooru.com/index.php?page=post&s=view&id="
        self.Home_URL = "https://realbooru.com/"

        # We will need to keep track of the last image ID we posted
        self.Previous_Image_ID = None

        # either danbooru or gelbooru
        self.booru_type = "gelbooru"

        # either 'safe', 'nsfw' or 'any'
        # everything is marked as explicit on REALBOORU
        self.content_type = 'nsfw'

        # sites like to have custom field names
        self.tag_json_title = 'tags'
        self.md5_tag = 'hash'

        self.token_headers = {
            "Referer": "http://behoimi.org/post/show/",
            "User-Agent": "Mozilla/5.0"}

    async def get_json_data(self, image_metadata):
        img_id = str(image_metadata['id'])

        post_url = self.Main_URL + img_id

        img_file_url = "https://realbooru.com/images/" + str(image_metadata['directory']) + "/" + str(image_metadata['image'])

        booru_name = self.board_name

        home_url = self.Home_URL

        is_banned = False  # it can only be false

        # custom scraping for info
        characters, artist, source = await self.get_info_from_webpage(post_url)

        # not enough information for full epoch given as of 10 june 2020
        timestamp = image_metadata['change']

        return characters, artist, post_url, img_file_url, timestamp, booru_name, home_url, source, is_banned

    async def get_info_from_webpage(self, post_url):
        # let's scrape the whole webpage so we can get names of characters and artists from the gelbooru based boards
        characters = ''
        artist = ''
        source = ''
        response = await requests.get(post_url, headers=self.token_headers)
        webpage = await response.text()
        soup = BeautifulSoup(webpage, features="html.parser")

        # set models names as the artists if provided
        for each in soup.find_all("a", class_="model"):
            artist += str(each).split(';tags=')[1].split('">')[0] + ' '
        # get character for any potential cosplayers
        for each in soup.find_all("a", class_="character"):
            characters += str(each).split(';tags=')[1].split('">')[0] + ' '
        # try to find source
        for each in soup.find_all("input", id="source"):
            source = str(each).split('value="')[1].split('"')[0]

        # sleep for one second to avoid hitting the rate limit
        await asyncio.sleep(1)

        return characters, artist, source
