import os
import glob
import asyncio
import subprocess
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables from .env file
load_dotenv()

# Configuration
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SOMEDL_PATH = os.getenv("SOMEDL_PATH", "somedl")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./music_temp")
ALLOWED_USERS_STR = os.getenv("ALLOWED_USERS", "")
ALLOWED_USERS = [int(user_id.strip()) for user_id in ALLOWED_USERS_STR.split(",") if user_id.strip().isdigit()]

# Global lock - only one download at a time
download_lock = asyncio.Lock()


def clean_download_dir():
    """Delete all mp3 files in the download folder."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    for f in glob.glob(os.path.join(DOWNLOAD_DIR, "*.mp3")):
        try:
            os.remove(f)
        except Exception as e:
            print(f"[WARN] Could not delete leftover file {f}: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "*Music Downloader Bot*\n\n"
        "Just send me a song or album name!\n\n"
        "*Examples:*\n"
        "- `Nirvana - Smells Like Teen Spirit`\n"
        "- `Thriller Michael Jackson`\n"
        "- `https://music.youtube.com/watch?v=...`\n\n"
        "*Commands:*\n"
        "/start - Show this message\n"
        "/help - Search tips\n"
        "/album <name> - Download a full album\n"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "*Search Tips*\n\n"
        "- Use `Artist - Song` for best results\n"
        "- Add `original` to avoid radio edits\n"
        "- Paste a YouTube Music URL for exact match\n"
        "- Use /album for full album downloads\n"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def album_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /album <name>\nExample: /album Dark Side of the Moon Pink Floyd"
        )
        return
    query = " ".join(context.args)
    await update.message.reply_text("Album downloads take a few minutes. Tracks will arrive one by one!")
    await run_download(update, context, query, extra_flags=["--fetch-album"])


async def handle_music_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    if not query:
        return
    await run_download(update, context, query)


async def run_download(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    query: str,
    extra_flags: list = None
):
    if extra_flags is None:
        extra_flags = []
        
    chat_id = update.message.chat_id
    
    if update.message.from_user.id not in ALLOWED_USERS:
        await update.message.reply_text("Unauthorized.")
        return

    # If another download is in progress, tell the user to wait
    if download_lock.locked():
        await update.message.reply_text("Another download is in progress. Please wait a moment and try again.")
        return

    async with download_lock:
        # Always wipe the folder before starting
        clean_download_dir()

        status_msg = await update.message.reply_text(
            f"Searching for: *{query}*...", parse_mode="Markdown"
        )

        try:
            command = [
                SOMEDL_PATH,
                query,
                "--format", "mp3",
                "--output", DOWNLOAD_DIR,
                *extra_flags
            ]

            loop = asyncio.get_event_loop()
            process = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    cwd=DOWNLOAD_DIR,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
            )

            if process.stdout:
                print(f"[stdout]\n{process.stdout}")
            if process.stderr:
                print(f"[stderr]\n{process.stderr}")

            if process.returncode != 0:
                await status_msg.edit_text(
                    f"Could not download *{query}*.\n\n"
                    "Try:\n- `Artist - Song` format\n"
                    "- A YouTube Music URL\n"
                    "- /help for tips",
                    parse_mode="Markdown"
                )
                return

            mp3_files = sorted(
                glob.glob(os.path.join(DOWNLOAD_DIR, "*.mp3")),
                key=os.path.getctime
            )

            if not mp3_files:
                await status_msg.edit_text(
                    "Download finished but no files found.\n"
                    "Make sure FFmpeg is installed."
                )
                return

            total = len(mp3_files)
            await status_msg.edit_text(
                f"Uploading {total} track{'s' if total > 1 else ''}..."
            )

            for i, filepath in enumerate(mp3_files, 1):
                try:
                    if total > 1:
                        await context.bot.send_message(
                            chat_id=chat_id, text=f"Track {i}/{total}"
                        )
                    with open(filepath, "rb") as audio:
                        await context.bot.send_audio(chat_id=chat_id, audio=audio)
                except Exception as e:
                    print(f"[ERROR] Failed to send {filepath}: {e}")
                    await context.bot.send_message(
                        chat_id=chat_id, text=f"Could not send track {i}."
                    )
                finally:
                    # Always delete the file whether sending succeeded or not
                    if os.path.exists(filepath):
                        os.remove(filepath)

            await status_msg.delete()

        except FileNotFoundError:
            await status_msg.edit_text(
                "SomeDL not found. Check the SOMEDL_PATH in your configuration."
            )
            print(f"[ERROR] somedl not found at: {SOMEDL_PATH}")

        except Exception as e:
            await status_msg.edit_text("Something went wrong. Check the console.")
            print(f"[ERROR] {e}")

        finally:
            # Always clean up after every request no matter what happened
            clean_download_dir()


def main():
    if not TOKEN:
        print("[ERROR] No TELEGRAM_BOT_TOKEN provided. Please set it in your .env file.")
        return

    # Wipe any leftover files from previous session on startup
    clean_download_dir()
    print("Download folder cleaned on startup.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("album", album_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_music_request))

    print("Bot is running! Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()