# Lapis Lazuli - A simple Discord music bot written in Python

Support is offered on my [Discord server](https://discord.gg/wF26b6taYz)!

---

Setup:
* Clone this repository - `git clone https://github.com/MrZomka/LapisLazuli.git`
* Create a virtual environment - `python -m venv ./.venv`
* Use the virtual environment - `source ./.venv/bin/activate`
* Install all dependencies - `pip install -r requirements.txt`
* Copy `config.example.json` to `config.json` and put your bot's token in the `token` field.
* Run the `main.py` file - `python main.py`

---

# If you are getting "Sign in to confirm you're not a bot...", read the following guide to fix the issue!
How to enable OAuth2:
* Install [yt-dlp-youtube-oauth2](https://github.com/coletdjnz/yt-dlp-youtube-oauth2)
* Try downloading anything from YouTube with `--username oauth2 --password ''` added to your command.
* If OAuth2 wasn't setup before, you will get the following message: ```[youtube+oauth2] To give yt-dlp access to your account, go to https://www.google.com/device and enter code XXX-YYY-ZZZ```
* Open `https://www.google.com/device` and enter the code that was given to you by the app and sign in. (It will display as YouTube on TV, that's normal! That's just how this plugin works.)
* Go to `config.json` and set `use-oauth-plugin` to `true`.
### It is highly recommended that you use a sockpuppet account for this since Google *could* ban you. Use this with caution and only when necessary.