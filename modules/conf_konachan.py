from aiohttp_requests import requests
from bs4 import BeautifulSoup
import asyncio


class KonachanSettings:
    def __init__(self):
        self.board_name = "Konachan"

        self.Initialize_URL = "http://konachan.com/post/index.json?tags=%s&limit=1"
        self.Scrape_URL = "http://konachan.com/post/index.json?tags=%s+id:>=%i"
        self.Main_URL = "http://konachan.com/post/show/"
        self.Home_URL = "http://konachan.com/"

        # We will need to keep track of the last image ID we posted
        self.Previous_Image_ID = None

        # some boards require obscure aways to get the json metadata (like safebooru)
        self.custom_get_function = False

        # sites like to have custom field names
        self.tag_json_title = 'tags'
        self.md5_tag = 'md5'

        # On some sites, just trying get the json response leaves us with permission errors
        # ...probably to stop people using scripts...
        # So, lets spoof being a web browser to avoid the 403 errors
        self.token_headers = {
            "Referer": "http://behoimi.org/post/show/",
            "User-Agent": "Mozilla/5.0"}

    async def get_json_data(self, image_metadata):
        img_id = str(image_metadata['id'])

        timestamp = image_metadata[
            'created_at']  # we actually get a correct epoch unlike Danbooru none utc datetime string

        source = image_metadata['source']

        post_url = self.Main_URL + img_id

        img_file_url = image_metadata['sample_url']  # they use the correct field unlike Danbooru

        booru_name = self.board_name

        home_URL = self.Home_URL

        is_banned = False  # this doesn't exist on Konachans version so, it can only be false

        # needed to make a special function to get these
        characters, artist = await self.get_character_and_artists(post_url)

        return characters, artist, post_url, img_file_url, timestamp, booru_name, home_URL, source, is_banned

    async def get_character_and_artists(self, post_url):
        # lets scrape the whole webpage so we can get names of characters and artists from Konachan
        characters = ''
        artist = ''
        response = await requests.get(post_url, headers=self.token_headers)
        webpage = await response.text()
        soup = BeautifulSoup(webpage, features="html.parser")
        for each in soup.find_all("li", class_="tag-link tag-type-artist"):
            artist += str(each).split('data-name="')[1].split('" data-type=')[0] + ' '

        for each in soup.find_all("li", class_="tag-link tag-type-character"):
            characters += str(each).split('data-name="')[1].split('" data-type=')[0] + ' '

        # sleep for one second to avoid hitting the rate limit
        await asyncio.sleep(1)

        return characters, artist
