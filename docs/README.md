# PESU Bot

<p align="center">
    <a href="https://github.com/sach-12/pesu-bot/issues">
        <img alt="Issues" src="https://img.shields.io/github/issues/sach-12/pesu-bot">
    </a>
    <a href="https://github.com/sach-12/pesu-bot/stargazers" alt="Stars">
        <img alt="Stars" src="https://img.shields.io/github/stars/sach-12/pesu-bot">
    </a>
    <a href="https://github.com/sach-12/pesu-bot/blob/main/LICENSE" alt="License">
        <img alt="License" src="https://img.shields.io/github/license/sach-12/pesu-bot">
    </a>
    <a href="https://github.com/sach-12/pesu-bot/contributors" alt="Contributors">
        <img alt="Contributors" src="https://img.shields.io/github/contributors/sach-12/pesu-bot"/>
    </a>
</p>

The source code for community management bot used in PESU Discord Server

Download the required modules by using the following command:

```sh
pip3 install -r requirements.txt
```

You will need a `.env` file with the following variables:

```sh
BOT_PREFIX= "YOUR_BOT_PREFIX"
BOT_TOKEN="YOUR_BOT_TOKEN"
GUILD_ID="YOUR_GUILD_ID" (742797665301168220 for PESU Discord Server)
MONGO_URI="YOUR_MONGO_URI"
DB_NAME="YOUR_DATABASE_NAME"
```

If you wish to contribute to the bot, run these steps:

1. Create a new branch called `beta-(discord-username)`
2. Do whatever changes you wish to do and create a pull request with the following information furnished in the request message: `The cog you wish to change | What did you change`
3. Create a pull request to the **dev** branch.
4. Wait for approval for reviewers. Your PR may be directly accepted or requested for further changes.

**Under no circumstances is anyone allowed to merge to the main branch.**
