
A simple, straightforward Telegram bot that allows approved users to download music tracks and full albums using `somedl`.In a nutshell i meant for this code to be run locally for a specific user in my case myself.

## Features
- Search and download single tracks
- Download full albums with the `/album` command
- Supports YouTube Music links
- Only approved users can use the bot
- Prevents concurrent downloads to manage server resources
- Cleans up temporary files automatically after each request

## Prerequisites
- Python 3.8 or higher
- A Telegram Bot Token from BotFather

## Setup

1. **Install System Dependencies (FFmpeg)**
   The bot requires FFmpeg to process and convert audio files. You must install it on your system:
   - **Windows**: Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) or use Winget: `winget install ffmpeg`
   - **Mac**: Use Homebrew: `brew install ffmpeg`
   - **Linux**: Use APT: `sudo apt install ffmpeg`

2. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/music-downloader-bot.git
   cd music-downloader-bot
   ```

3. **Install Python dependencies**:
   This will install `python-telegram-bot`, `python-dotenv`, and the `somedl` downloader.



   note:the tool somedl is a great tool please check out the og repo https://github.com/ChemistryGull/SomeDL
   ```bash
   pip install -r requirements.txt
   
   ```

3. **Configure the environment variables**:
   Rename `.env.example` to `.env` and fill in your details:
   ```bash
   cp .env.example .env
   ```
   Open the `.env` file and set the required variables:
   - `TELEGRAM_BOT_TOKEN`: The token you received from BotFather.
   - `SOMEDL_PATH`: The path to the `somedl` executable on your system.
   - `DOWNLOAD_DIR`: A temporary directory where music will be saved before being sent.
   - `ALLOWED_USERS`: A comma-separated list of Telegram User IDs that are allowed to use this bot.

## Usage

Start the bot:
```bash
python bot.py
```

Send a message to your bot on Telegram:
- Type a song name: `Nirvana - Smells Like Teen Spirit`
- Type an album command: `/album Dark Side of the Moon Pink Floyd`
- Send a YouTube Music URL

## Disclaimer
This project is for educational purposes only. Please respect the copyright of the music and only download content you are legally permitted to.
