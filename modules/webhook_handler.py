import asyncio
from discord_webhook import DiscordWebhook, DiscordEmbed


def fix_html_characters(text):
    return text.replace('_', '\\_').replace('%29', ')').replace('%28', '(')


async def make_embed(character=None, artist=None, post_url=None, file_url=None, colour=None, timestamp=None,
                     origin_site=None, origin_site_url=None, source=None, is_banned=False):
    # print("character=%r\nartist=%r\npost_url=%r\nfile_url=%r\ncolour=%r\ntimestamp=%r\norigin_site=%r\norigin_site_url=%r\nsource=%r\nis_banned=%r\n" % (
    #    character, artist, post_url, file_url, colour, timestamp, origin_site, origin_site_url, source, is_banned))

    if colour is None:
        colour = 0xd7d7d7  # white, mostly

    # workout source link if available to put in embed description
    if is_banned and source is not None:
        description_text = "[Artist %r is banned from %r but, click here for the source anyway...](%s)" % (
        artist, origin_site, source)
    elif is_banned and source is None:
        # we can't provide any useful information, there is no point making an embed...
        return None
    elif source == '' or source is None or not source.startswith('http'):
        description_text = 'Source Unavailable'
    elif source is not None:
        description_text = '[Source Link](%s)' % source
    else:
        # this should never get called
        description_text = ''

    title_string = fix_html_characters("%s by %s" % (character, artist))

    # very log titles will cause the embed to fail
    if len(title_string) < 256:
        title = title_string
    else:
        title = title_string[0:253] + "..."
        title_leftovers = "..." + title_string[253:]
        # concat leftovers with source link
        description_text = title_leftovers + "\n" + description_text

    # shameless self-promotion with url
    description_text = description_text + " | Powered by [Image Hooker](https://github.com/Niroc/Discord-Image-Hooker)"

    # make an embed object
    embed = DiscordEmbed(title=title, description=description_text, color=colour)

    # URL to post (not the source)
    embed.set_url(url=post_url)

    if timestamp is not None:
        embed.set_timestamp(timestamp=int(timestamp))

    if origin_site is not None:
        embed.set_author(name=origin_site, url=origin_site_url)

    # check if video
    if file_url.lower().endswith('mp4') or file_url.lower().endswith("webm"):
        embed.add_embed_field(inline=False, name="Video URL (I can't embed these like with images)",
                              value=file_url)
    elif not is_banned:
        embed.set_image(url=file_url)
    else:
        pass

    return embed


async def send_to_discord(webhook_list, embed_list, criteria, nsfw):
    # Webhooks can send a maximum of 10 embeds per transaction so, lets make unique
    # dictionary entries each with a list that's limited to a max of 10 embeds.
    # This should help us avoid Discord's rate limit
    unique_key = "a"
    embeds_to_send = {unique_key: []}

    print("Sending %r embed/s matching %r NSFW = %r" % (len(embed_list), criteria, nsfw))

    for embed in embed_list:
        # check if we've hit the 10 embed limit
        if len(embeds_to_send[unique_key]) == 10:
            # if true, it's time to make another unique key for a new hash table entry
            unique_key += "a"
            # also make another emtpy list to append to
            embeds_to_send[unique_key] = []

        embeds_to_send[unique_key].append(embed)

    # loop around each possible set of 10 embeds
    for key, sorted_list_of_embeds in embeds_to_send.items():
        # send to each possible webhook uri
        for webhook_uri in webhook_list:
            await post_embeds(webhook_uri, sorted_list_of_embeds)
            await asyncio.sleep(2)  # short delay to help prevent rate limiting
        await asyncio.sleep(10)  # short delay to help prevent rate limiting


async def post_embeds(webhook_url, embed_list):
    # ensure user provided discord url is accurate
    if not webhook_url.lower().startswith("https://discord"):
        webhook_url = "https://discordapp.com/api/webhooks/" + webhook_url

    webhook = DiscordWebhook(url=webhook_url)

    # add embeds, the max limit that can bee added to a post is 10
    for embed in embed_list:
        webhook.add_embed(embed)

    response = webhook.execute()
    if response.status_code == 404 or response.status_code == 401:
        print('\033[31m'  # set terminal text to red
              + 'Error: The following Webhook URL in your config.json file is invalid...\n'
              + '%r' % webhook_url
              + '\033[39m')  # reset to default color
