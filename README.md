# Discord-Image-Hooker
Auto image poster for Discord using Webhooks that's able to search for specific tags and filter out sub tags to fine tune your results and also able to send the result to multiple Discord Webhooks if required. <br/>
* This has MD5 checking per search reference to help stop duplicate images being posted.<br/>
* This will filter out NSFW images that break Discords T&C's.<br/><br/>
## Currently supports scraping from...
(You can enable or disable these per search reference if you do not like a particular imageboard)
* Danbooru
* Konachan
* Rule34 (Disabled by default... furry warning)

### Requirements
You need to install these...
* [Python >= 3.6](https://www.python.org/downloads/)
* [aiohttp-requests](https://pypi.org/project/aiohttp-requests/)
* [discord-webhook](https://pypi.org/project/discord-webhook/)
* [beautifulsoup4](https://pypi.org/project/beautifulsoup4/)
* [aiosqlite](https://pypi.org/project/aiosqlite/)

## How to Configure
Here's a link to Discords tutorial on how to setup webhooks in your Discord server, the only section you need to follow is "Making a Webhook".<br/>
https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks
<br /><br />
After you've made your webhook(s) open up the "config.json" file and fill in the respective fields. (Also, delete any unneeded example config)
![config example](https://cdn.discordapp.com/attachments/591684716760006692/713002817262059560/Screenshot_2020-05-21_13-18-26.png)
<br /><br />
Finally to start the script, run "python3 main.py" from the command line.

