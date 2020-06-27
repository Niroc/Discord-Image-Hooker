import asyncio
from aiohttp_requests import requests
from bs4 import BeautifulSoup
from datetime import datetime


class Rule34Settings:
    def __init__(self):
        self.board_name = "Rule34"

        self.Initialize_URL = "https://rule34.xxx/index.php?page=dapi&s=post&q=index&tags=%s&limit=1&json=1"
        self.Scrape_URL = "https://rule34.xxx/index.php?page=dapi&s=post&q=index&tags=%s+id:%%3E=%i&json=1"
        self.Main_URL = "https://rule34.xxx/index.php?page=post&s=view&id="
        self.Home_URL = "https://rule34.xxx/"
        self.image_URL = "https://rule34.xxx/images"

        # We will need to keep track of the last image ID we posted
        self.Previous_Image_ID = None

        # either danbooru or gelbooru
        self.booru_type = "gelbooru"

        # either 'safe', 'nsfw' or 'any'
        self.content_type = 'nsfw'

        # sites like to have custom field names
        self.tag_json_title = 'tags'
        self.md5_tag = 'hash'

        # On some sites, just trying get the json response leaves us with permission errors
        # ...probably to stop people using scripts...
        # So, lets spoof being a web browser to avoid the 403 errors
        self.token_headers = {
            "Referer": "http://behoimi.org/post/show/",
            "User-Agent": "Mozilla/5.0"}

    async def get_json_data(self, image_metadata):
        img_id = str(image_metadata['id'])

        post_url = self.Main_URL + img_id

        # this doesn't always work
        # img_file_url = "https://rule34.xxx/images/" + image_metadata['directory'] + "/" + image_metadata['image']

        # sometimes the directory prefix on rule34 has a forward slash... sometimes it doesn't
        picture_dir = image_metadata['directory'] + "/" + image_metadata['image']
        if str(picture_dir).startswith('/'):
            img_file_url = self.image_URL + picture_dir
        else:
            img_file_url = self.image_URL + "/" + picture_dir


        booru_name = self.board_name

        home_url = self.Home_URL

        is_banned = False  # it can only be false

        # needed to make a special function to get these
        characters, artist, time_string, source = await self.get_info_from_webpage(post_url)

        # convert to epoch
        try:
            timestamp = datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S").strftime('%s')
        except:
            print("can't format time string...")
            print(time_string)
            timestamp = None

        return characters, artist, post_url, img_file_url, timestamp, booru_name, home_url, source, is_banned

    async def get_info_from_webpage(self, post_url):
        # lets scrape the whole webpage so we can get names of characters and artists from the gelbooru based boards
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
            #print(each)
            timestamp = str(each).split('Posted: ')[1].split('<br')[0]
            try:
                # this isn't always included on rule 34
                source = str(each).split('Source: <a href="')[1].split('"')[0]
            except:
                source = None

        # sleep for one second to avoid hitting the rate limit
        await asyncio.sleep(1)

        return characters, artist, timestamp, source


