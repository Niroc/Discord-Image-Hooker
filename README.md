# Discord-Image-Hooker
Auto image poster for Discord using Webhooks that's able to search for specific tags and filter out sub tags to fine tune your results and also able to send the result to multiple Discord Webhooks if required. Also, this has MD5 checking per search reference to help mitigate duplicate images being posted
![DisHooker Example](https://cdn.discordapp.com/attachments/591684716760006692/711903037374857306/Screenshot_2020-05-18_12-27-21.png)
## Currently supports scraping from...
* Danbooru

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
![config example](https://cdn.discordapp.com/attachments/601389892299128834/710105817889636402/Screenshot_2020-05-13_13-26-45.png)
<br /><br />
Finally to start the script, run "python3 main.py" from the command line.
<br /><br />

Here's a YouTube video demonstrating it being setup and sending an image to Discord within 2 minutes.<br />
[![https://cdn.discordapp.com/attachments/601389892299128834/710102466884009984/Screenshot_2020-05-13_13-13-15.png](http://img.youtube.com/vi/qhZzlEGbJOQ/0.jpg)](https://youtu.be/qhZzlEGbJOQ)
