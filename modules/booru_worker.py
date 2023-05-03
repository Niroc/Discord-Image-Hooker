import asyncio
import random
import traceback
import json

import aiohttp
from aiohttp_requests import requests
from modules import webhook_handler
# custom tweaks for each booru
from modules import conf_danbooru
from modules import conf_konachan
from modules import conf_rule34
from modules import conf_safebooru

def add_booru_to_check(config):
    # we can use this to dynamically add booru's enabled by the user
    booru_dict = {
        "Danbooru": conf_danbooru.DanbooruSettings(),
        "Konachan": conf_konachan.KonachanSettings(),
        "Safebooru": conf_safebooru.SafebooruSettings(),
        "Rule34": conf_rule34.Rule34Settings()
    }
    enabled_boards = []
    for key, board_object in booru_dict.items():
        try:
            if config[key]:  # flag must be set to true
                if key == 'Safebooru' and config['Danbooru'] is True:
                    # safebooru is a safe backup of danbooru
                    print('> Safebooru search not started as Danbooru is enabled')
                elif config['NSFW'] is True and board_object.content_type == 'safe':
                    # search is NSFW but, board only supports safe content so skip
                    print("> %s only supports safe content, NSFW search for %s canceled." % (board_object.board_name, config['criteria']))
                elif config['NSFW'] is False and board_object.content_type == 'nsfw':
                    # search is safe only but board only has nsfw content so skip
                    print("> %s only supports NSFW content, safe search for %s canceled." % (board_object.board_name, config['criteria']))
                else:
                    enabled_boards.append(board_object)
        except:
            pass  # nothing was configured
    if len(enabled_boards) == 0:
        print('\033[31mError: No boards have been activated in config.json file to search for %r\033[39m' %
              config['criteria'])
    return enabled_boards


class SearchTask:
    def __init__(self, database, self_config):
        self.table_name = ''
        self.database = database

        # booru modules will be loaded into here if configured
        self.booru_objects = add_booru_to_check(self_config)

        # List of Strings - the Discord Webhook/s we will post the images to
        self.Discord_Webhook_URL_List = self_config['Discord uri']

        # String - our search reference
        self.Search_Criteria = self_config['criteria']

        # Boolean - are we posting safe or none-safe content?
        self.Post_NSFW = self_config['NSFW']

        # List of String - tags we ignore
        self.Ignore_Criteria = []

        # ensure tags have preceding and trailing spaces so we don't encounter partial matches
        for tag in self_config['Ignore']:
            if not tag.startswith(' '):
                tag = ' ' + tag
            if not tag.endswith(' '):
                tag = tag + ' '
            self.Ignore_Criteria.append(tag)

        # List of Strings - We need to filter out these on NSFW images so we don't break Discords T+C's
        self.Forbidden_Tags = [' guro ', ' loli ', ' shota ']

        # On some sites, just trying get the json response leaves us with permission errors
        # ...probably to stop people using scripts...
        # So, lets spoof being a web browser to avoid the 403 errors
        self.token_headers = {
            "Referer": "http://behoimi.org/post/show/",
            "User-Agent": "Mozilla/5.0"}

    async def gelbooru_get_method(self, url):
        try:
            # get content
            response = await requests.get(url, headers=self.token_headers)

            # we have to read it into byte array for gelbooru based boards
            message_content_string = await response.read()
        except aiohttp.ClientConnectionError as C:
            print('\033[31m' + str(C) + '\033[39m')
            return []
        # convert bytes to JSON
        #message_json = json.loads(message_content_string)
        try:
            message_json = json.loads(message_content_string)
        except:
            print('\033[31m' + "Error: Failed to encode json for gelbooru method")
            print(message_content_string)
            print('\033[39m')  # reset to default color
            return []

        return message_json

    async def danbooru_get_method(self, url):
        # get content
        try:
            response = await requests.get(url, headers=self.token_headers, timeout=120)
        except aiohttp.ClientConnectionError as C:
            print('\033[31m' + str(C) + '\033[39m')
            return []
        # encode json
        try:
            json = await response.json()
        except:
            print('\033[31m' + "Error: Failed to encode json for danbooru method")
            print(message_content_string)
            print('\033[39m')  # reset to default color
            return []

        return json

    async def get_latest_image_id(self, current_booru_obj):
        # check if booru requires bespoke get function
        if current_booru_obj.booru_type == "gelbooru":
            # so far only safebooru requires this
            json = await self.gelbooru_get_method(current_booru_obj.Initialize_URL % self.Search_Criteria)
        elif current_booru_obj.booru_type == "danbooru":
            json = await self.danbooru_get_method(current_booru_obj.Initialize_URL % self.Search_Criteria)

        # if the json length is zero, the search reference is not valid
        if len(json) == 0:
            print("There are no matches for %r on board %r" % (self.Search_Criteria, current_booru_obj.board_name))
            current_booru_obj.Previous_Image_ID = None
        elif json[0]['id'] == "N/A":
            # we don't need to spit out error
            print("Skipped NSFW search %r for safebooru" % self.Search_Criteria)
            current_booru_obj.Previous_Image_ID = None
        else:
            # return new previous ID
            current_booru_obj.Previous_Image_ID = json[0]['id']

    async def check_for_new_images(self, current_booru_obj):
        # get the latest image list uploaded after self.Previous_Image_ID

        # check if booru requires bespoke get function
        if current_booru_obj.booru_type == "gelbooru":
            image_list_json = await self.gelbooru_get_method(current_booru_obj.Scrape_URL % (self.Search_Criteria, current_booru_obj.Previous_Image_ID))
        elif current_booru_obj.booru_type == "danbooru":
            image_list_json = await self.danbooru_get_method(current_booru_obj.Scrape_URL % (self.Search_Criteria, current_booru_obj.Previous_Image_ID))

        Images_to_send = []
        for Image_metadata in image_list_json:
            # Discord Webhooks can send multiple embeds in a single message
            # so lets build a list of items to send...
            #print("checking: %r" % Image_metadata['id'])

            # pass on bad deeter iata
            if 'id' not in Image_metadata:
                continue

            # check if the image ID matches our previous image idea on record
            if Image_metadata['id'] == current_booru_obj.Previous_Image_ID:
                continue

            # use this so we don't have to return out of function to skip
            # ignored content potentially making us miss an image.
            should_continue = False

            # check if images breaks Discord T+C's
            for illegal_tag in self.Forbidden_Tags:
                if illegal_tag in Image_metadata[current_booru_obj.tag_json_title] and not str(Image_metadata['rating']).startswith('s'):
                    print('\033[31m'
                          + "Error: skipping NSFW image %r matching '%s' because it contains Discord illegal tag: %s" %
                          (Image_metadata['id'], self.Search_Criteria, illegal_tag)
                          + '\033[39m')
                    should_continue = True

            # check if images contain tags user wants to ignore
            for ignored_tag in self.Ignore_Criteria:
                if ignored_tag in Image_metadata[current_booru_obj.tag_json_title]:
                    #print("skipping image %r matching '%s' because it matches ignore tag: %s" % (
                    #    Image_metadata['id'], self.Search_Criteria, ignored_tag))
                    should_continue = True

            # need this due to the use of nested for loops
            if should_continue:
                # skip to next image in list
                continue

            # check matches one of the desired safety ratings else continue to next loop if it doesn't
            if str(self.Post_NSFW).lower() == "any":
                pass  # we don't care about safety rating
            elif self.Post_NSFW is False and (Image_metadata['rating'].startswith('s') or Image_metadata['rating'].startswith('g')):
                pass
            elif self.Post_NSFW and not Image_metadata['rating'].startswith('g'):
                pass
            else:  # new entry must not match the desired safety rating
                continue

            if current_booru_obj.md5_tag not in Image_metadata:
                continue

            # finally check if image already exists in database
            db_response = await self.database.check_for_value(self.table_name,
                                                              Image_metadata[current_booru_obj.md5_tag])
            if db_response[0] == 0:
                # add to db
                await self.database.add_md5_checksum(self.table_name, Image_metadata[current_booru_obj.md5_tag])
            else:
                # already exists in db
                #print("%r already exists in table: %r, will skip" % (Image_metadata['id'], self.table_name))
                continue

            # we must have met all of the criteria outlined above so add the image...
            Images_to_send.append(Image_metadata)

            index_number = await self.get_latest_valid_id_index(0, image_list_json)

            # be sure to update this even if there's nothing valid to post to reduce traffic
            if current_booru_obj.Previous_Image_ID != image_list_json[index_number]['id']:
                current_booru_obj.Previous_Image_ID = image_list_json[index_number]['id']

        if len(Images_to_send) > 0:
            # send our list we've built
            embeds = await self.make_discord_content(Images_to_send, current_booru_obj)
            return embeds
        else:
            return []

    async def get_latest_valid_id_index(self, index, image_list_json):
        # if duff data then skip current index and check again... eventually we will hit the previous working record
        # pass on bad data
        if 'id' not in image_list_json[index]:
            index += 1
            # check again incase there 2 or more duff records
            await self.get_latest_valid_id_index(index, image_list_json)

        # return number of a valid index
        return index

    async def fix_html_characters(self, text):
        text_fix = text.replace('%29', ')').replace('%28', '(').replace('%27', '\'').replace('%3A', ':').replace(' ', ', ').replace('_', ' ')
        if text_fix.endswith(', '):
            return text_fix[:-2]
        else:
            return text_fix

    async def make_discord_content(self, list_of_images, current_booru_obj):
        # turn our metadata into Discord Embeds
        embed_list = []
        count = 0
        current_url = ''
        list_of_chars_and_artist = []
        IDs = []
        for img in list_of_images:
            characters, artist, post_url, img_file_url2, timestamp, booru_name, home_url, source, is_banned = \
                await current_booru_obj.get_json_data(img)

            # default to unknown when no artist is supplied
            if len(artist) == 0:
                artist = 'Unknown'

            # see if source url is populated with a link
            if source == '' or source is None or not source.startswith('http'):
                # if source url is duff check if post url is ok
                if post_url == '' or post_url is None or not post_url.startswith('http'):
                    # both source and post url are bad, don't add link
                    list_of_chars_and_artist.append("\\> %s by %s\n" % (
                            await self.fix_html_characters(characters), await self.fix_html_characters(artist)))
                else:
                    # source is bad, failover to post url
                    list_of_chars_and_artist.append("\\> [%s by %s](%s)\n" % (
                        await self.fix_html_characters(characters), await self.fix_html_characters(artist), post_url))
            else:
                # use source link provided
                list_of_chars_and_artist.append("\\> [%s by %s](%s)\n" % (
                    await self.fix_html_characters(characters), await self.fix_html_characters(artist), source))
            IDs.append([booru_name, str(img['id'])])

        for image_metadata in list_of_images:
            # use our custom conf python files to get this data
            characters, artist, post_url, img_file_url, timestamp, booru_name, home_url, source, is_banned = \
                await current_booru_obj.get_json_data(image_metadata)

            # discord won't display .gifv images at all but changing the extension to .gif will at least display the first frame
            if img_file_url.lower().endswith('.gifv'):
                img_file_url = img_file_url[:-1]

            # if true, then 'count' is a multiple of 4
            if ((count & 3) == 0):

                img_id = image_metadata['id']
                
                current_url = post_url

                # generate Discord embed object
                discord_embed = await webhook_handler.make_embed(character=characters,
                                                             artist=artist,
                                                             post_url=post_url,
                                                             file_url=img_file_url,
                                                             colour=img_id,
                                                             timestamp=timestamp,
                                                             origin_site=booru_name,
                                                             origin_site_url=home_url,
                                                             source=source,
                                                             is_banned=is_banned,
                                                             finished_description="".join(list_of_chars_and_artist[0:4]),
                                                             ID_list=IDs[0:4])
                                                            
                # delete what we've already posted
                del list_of_chars_and_artist[0:4]
                del IDs[0:4]
            else:
                discord_embed = await webhook_handler.make_embed_small(img_file_url, current_url)
                
            count += 1

            if discord_embed is not None:
                # add valid embed to the list
                embed_list.append(discord_embed)

        return embed_list

    async def main(self):
        print("Task created searching for %r, NSFW: %r" % (self.Search_Criteria, self.Post_NSFW))
        self.table_name = await self.database.fix_table_names(self.Search_Criteria + str(self.Post_NSFW))

        # acquire most recent post ID that match our search criteria for each of our configured boards
        for booru in self.booru_objects:
            await self.get_latest_image_id(booru)

        # main loop
        while True:
            # make random sleep delay between 20 ~ 30 minutes
            await asyncio.sleep(random.randint(1200, 1800))
            #print("trying %r" % self.Search_Criteria)

            # use traceback lib so we actually get a stacktrace as we're use asyncio...
            try:
                embeds = []
                for board in self.booru_objects:
                    if board.Previous_Image_ID is None:
                        continue  # search reference must not have been valid
                    embeds += await self.check_for_new_images(board)
                if len(embeds) == 0:
                    pass  # there's nothing to send...
                else:
                    await webhook_handler.send_to_discord(self.Discord_Webhook_URL_List,
                                                          embeds,
                                                          self.Search_Criteria,
                                                          self.Post_NSFW)
            except:
                print('\033[31mError: ')  # make terminal text red
                traceback.print_exc()
                print('\033[39m')  # reset to default color
