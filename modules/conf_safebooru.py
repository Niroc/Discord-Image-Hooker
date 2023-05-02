import asyncio
from aiohttp_requests import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json


class SafebooruSettings:
    def __init__(self):
        self.board_name = "Safebooru"

        #    safebooru's indexes
        self.Initialize_URL = "https://safebooru.org/index.php?page=dapi&s=post&q=index&tags=%s&limit=1&json=1"
        self.Scrape_URL = "https://safebooru.org/index.php?page=dapi&s=post&q=index&tags=%s+id:%%3E=%i&json=1"

        # these urls will still work
        self.Main_URL = "https://safebooru.org/index.php?page=post&s=view&id="
        self.Home_URL = "https://safebooru.org/"

        self.post_url = "https://safebooru.org/index.php?page=dapi&s=post&q=index&json=1"

        # We will need to keep track of the last image ID we posted
        self.Previous_Image_ID = None

        # either danbooru or gelbooru
        self.booru_type = "gelbooru"

        # either 'safe', 'nsfw' or 'any'
        self.content_type = 'safe'

        # sites like to have custom field names
        self.tag_json_title = 'tags'
        self.md5_tag = 'hash'

        self.token_headers = {
            "Referer": "http://behoimi.org/post/show/",
            "User-Agent": "Mozilla/5.0"}

    async def get_json_data(self, image_metadata):
        img_id = str(image_metadata['id'])

        post_url = self.Main_URL + img_id

        img_file_url = "https://safebooru.org//images/" + image_metadata['directory'] + "/" + image_metadata['image']

        booru_name = self.board_name

        home_url = self.Home_URL

        is_banned = False  # it can only be false

        # needed to make a special function to get these
        characters, artist, time_string, source = await self.get_info_from_webpage(post_url)

        # convert to epoch
        try:
            timestamp = datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S").strftime('%s')
        except:
            timestamp = None

        return unescape_brackets(characters), unescape_brackets(artist), post_url, img_file_url, timestamp, booru_name, home_url, source, is_banned

    async def get_info_from_webpage(self, post_url):
        # let's scrape the whole webpage so we can get names of characters and artists from safebooru

        # set blanks to default to... just incase
        characters = ''
        artist = ''
        timestamp = ''
        source = ''
        response = await requests.get(post_url, headers=self.token_headers)
        webpage = await response.text()
        soup = BeautifulSoup(webpage, features="html.parser")
        # get artist names
        for each in soup.find_all("li", class_="tag-type-artist"):
            artist += str(each).split(';tags=')[1].split('">')[0] + ' '
        # get character names
        for each in soup.find_all("li", class_="tag-type-character"):
            characters += str(each).split(';tags=')[1].split('">')[0] + ' '

        # get timestamp and source from html
        for each in soup.find_all("div", id="stats"):
            timestamp = str(each).split('Posted: ')[1].split('<br')[0]
            source = str(each).split('Source: ')[1].split('href="')[1].split('"')[0]

            # the pixiv links it provides are duff
            if "i.pximg.net" in source:
                source = "https://www.pixiv.net/en/artworks/" + source.split('/')[-1].split('_')[0]

        # sleep for one second to avoid hitting the rate limit
        await asyncio.sleep(1)

        return characters, artist, timestamp, source


def unescape_brackets(text):
    return text.replace('%%29', ')').replace('%%28', '(')
