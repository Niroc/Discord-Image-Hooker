import datetime
import time


class DanbooruSettings:
    def __init__(self):
        self.board_name = "Danbooru"

        self.Initialize_URL = "https://danbooru.donmai.us/posts.json?tags=%s&limit=1"
        self.Scrape_URL = "https://danbooru.donmai.us/posts.json?tags=%s+id:>=%i"
        self.Main_URL = "https://danbooru.donmai.us/posts/"
        self.Home_URL = "https://danbooru.donmai.us/"

        # We will need to keep track of the last image ID we posted
        self.Previous_Image_ID = None

        self.tag_json_title = 'tag_string'

    async def get_json_data(self, image_metadata):
        characters = image_metadata['tag_string_character']

        artist = image_metadata['tag_string_artist']

        img_id = str(image_metadata['id'])

        timestamp = await make_utc_epoch_string(image_metadata['created_at'])

        source = await return_valid_source_url(image_metadata['source'], image_metadata['pixiv_id'])

        post_url = self.Main_URL + img_id

        # cater for artist that are banned from Danbooru...
        if image_metadata['is_banned']:
            # this wont be shown anyway but, the field needs a valid url
            img_file_url = source

        # Display sample image to avoid posting file too large
        else:
            img_file_url = image_metadata['large_file_url']

        booru_name = self.board_name

        home_URL = self.Home_URL

        is_banned = image_metadata['is_banned']

        return characters, artist, post_url, img_file_url, timestamp, booru_name, home_URL, source, is_banned


async def return_valid_source_url(url, pixiv_ID):
    # Danbooru doesn't supply the valid pixiv source url in the json metadata so, we need to fix it for them...
    if pixiv_ID is None:
        return url
    else:
        return "https://www.pixiv.net/artworks/" + str(pixiv_ID)


async def make_utc_epoch_string(date_time_str):
    # use witchcraft to get an UTC epoch string that's accepted by 'discord_webhook.py' and actually accurate...
    date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M:%S.%f%z')
    utc_time_struct = date_time_obj.utctimetuple()
    utc_epoch_string = datetime.datetime.fromtimestamp(time.mktime(utc_time_struct)).strftime('%s')
    return utc_epoch_string
