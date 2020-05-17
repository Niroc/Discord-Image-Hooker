import asyncio
import random
import datetime
import time
from aiohttp_requests import requests
import traceback
from modules import webhook_handler


class DanbooruWorker:
    def __init__(self, ToSearch, Webhooks, IsNSFW, IgnoreTags):
        # List of Strings - the Discord Webhook/s we will post the images to
        self.Discord_Webhook_URL_List = Webhooks

        # String - our search reference
        self.Search_Criteria = ToSearch

        # Boolean - are we posting safe or none-safe content?
        self.Post_NSFW = IsNSFW

        # List of String - tags we ignore
        self.Ignore_Criteria = []

        # ensure tags have preceding and trailing spaces so we don't encounter partial matches
        for tag in IgnoreTags:
            if not tag.startswith(' '):
                tag = ' ' + tag
            if not tag.endswith(' '):
                tag = tag + ' '
            self.Ignore_Criteria.append(tag)

        # String - URLs we'll use to get the goods
        self.Danbooru_Initialize_URL = "https://danbooru.donmai.us/posts.json?tags=%s&limit=1"
        self.Danbooru_Scrape_URL = "https://danbooru.donmai.us/posts.json?tags=%s+id:>=%i"
        self.Danbooru_Main_URL = "https://danbooru.donmai.us/posts/"
        self.Danbooru_Home_URL = "https://danbooru.donmai.us/"

        # List of Strings - We need to filter out these on NSFW images so we don't break Discords T+C's
        # I'm pretty sure you need a gold account with danbooru to get loli and shota images anyway
        self.Forbidden_Tags = [' guro ', ' loli ', ' shota ']

        # We will need to keep track of the last image ID we posted
        self.Previous_Image_ID = None

    async def get_latest_image_id(self):
        # used to get the latest image id on startup
        response = await requests.get(self.Danbooru_Initialize_URL % self.Search_Criteria)
        json = await response.json()
        # if the json length is zero, the search reference is not valid
        if len(json) == 0:
            pass
        else:
            self.Previous_Image_ID = json[0]['id']

    async def check_for_new_images(self):
        # get the latest image list uploaded after self.Previous_Image_ID
        response = await requests.get(self.Danbooru_Scrape_URL % (self.Search_Criteria, self.Previous_Image_ID))
        try:
            image_list_json = await response.json()
        except:
            if "502 bad gateway" in response:
                print('\033[31m' +
                      "Error: 502 bad gateway - Danbooru Service Temporarily Overloaded." +
                      '\033[39m')
            else:
                print('\033[31m' + "Error: Failed to encode json")
                print(response)
                print('\033[39m')  # reset to default color
            return

        Images_to_send = []
        for Image_metadata in image_list_json:
            # Discord Webhooks can send multiple embeds in a single message
            # so lets build a list of items to send...

            # check if the image ID matches our previous image idea on record
            if Image_metadata['id'] == self.Previous_Image_ID:
                continue

            # use this so we don't have to return out of function to skip
            # ignored content potentially making us miss an image.
            should_continue = False

            # check if images breaks Discord T+C's
            for illegal_tag in self.Forbidden_Tags:
                if illegal_tag in Image_metadata['tag_string'] and Image_metadata['rating'] != 's':
                    print('\033[31m' + "Error: skipping NSFW image %r matching '%s' because it contains Discord illegal tag: %s" % (
                        Image_metadata['id'], self.Search_Criteria, illegal_tag) + '\033[39m')

                    should_continue = True

            # check if images contain tags user wants to ignore
            for ignored_tag in self.Ignore_Criteria:
                if ignored_tag in Image_metadata['tag_string']:
                    #print("skipping image %r matching '%s' because it matches ignore tag: %s" % (
                    #    Image_metadata['id'], self.Search_Criteria, ignored_tag))
                    should_continue = True

            if should_continue:
                # skip to next image in list
                continue

            elif self.Post_NSFW is False and Image_metadata['rating'] == 's':
                print("Adding SFW image matching '%s', ID: %r" % (self.Search_Criteria, Image_metadata['id']))
                Images_to_send.append(Image_metadata)
            elif self.Post_NSFW and Image_metadata['rating'] != 's':
                print("Adding NSFW image matching '%s', ID: %r" % (self.Search_Criteria, Image_metadata['id']))
                Images_to_send.append(Image_metadata)
            else:
                # new entry must not match the desired safety rating
                continue

        # send our list we've built
        await self.make_discord_content(Images_to_send)

        # update last posted image ID with most recent
        self.Previous_Image_ID = image_list_json[0]['id']

    async def make_discord_content(self, list_of_images):
        # turn our metadata into Discord Embeds
        embed_list = []
        for image_metadata in list_of_images:

            img_id = str(image_metadata['id'])
            timestamp = await make_utc_epoch_string(image_metadata['created_at'])
            source = await return_valid_source_url(image_metadata['source'], image_metadata['pixiv_id'])

            # cater for artist that are banned from Danbooru...
            if image_metadata['is_banned']:
                # this wont be shown anyway but, the field needs a valid url
                img_file_url = source

            # Display sample image to avoid posting file too large
            else:
                img_file_url = image_metadata['large_file_url']

            # danbooru posts url
            post_url = self.Danbooru_Main_URL + img_id

            # generate Discord embed object
            discord_embed = await webhook_handler.make_embed(character=image_metadata['tag_string_character'],
                                                             artist=image_metadata['tag_string_artist'],
                                                             post_url=post_url,
                                                             file_url=img_file_url,
                                                             colour=img_id,
                                                             timestamp=timestamp,
                                                             origin_site="Danbooru",
                                                             origin_site_url=self.Danbooru_Home_URL,
                                                             source=source,
                                                             is_banned=image_metadata['is_banned'])
            if discord_embed is not None:
                # add valid embed to the list
                embed_list.append(discord_embed)

        # check if the original embed list hasn't got anything to send
        if len(embed_list) == 0:
            return  # there's nothing to send...
        else:
            await webhook_handler.send_to_discord(self.Discord_Webhook_URL_List, embed_list)

    async def main(self):
        print("Task created searching Danbooru for %r, NSFW: %r" % (self.Search_Criteria, self.Post_NSFW))
        # acquire most recent Danbooru post ID match our search criteria
        await self.get_latest_image_id()

        if self.Previous_Image_ID is None:
            print('\033[31m'  # set terminal text to red
                  + 'Error: There are no tags matching %r on Danbooru' % self.Search_Criteria
                  + '\033[39m')  # reset to default color
            return  # return before we start the while loop

        # main loop
        while True:
            # make random sleep delay between 5 ~ 20 minutes
            await asyncio.sleep(random.randint(300, 1200))

            # use traceback lib so we actually get a stacktrace as we're use asyncio...
            try:
                await self.check_for_new_images()
            except:
                print('\033[31mError: ')  # make terminal text red
                traceback.print_exc()
                print('\033[39m')  # reset to default color

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
