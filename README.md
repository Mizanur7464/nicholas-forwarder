# Telegram Channel Forwarder Bot

A bot that automatically forwards/copies all messages from a main channel to another channel.

## Requirements

- Python 3.10 or higher
- Telegram bot token (from @BotFather)
- Two channels (main + destination)

## Setup

### 1. Create a bot

1. Open [@BotFather](https://t.me/BotFather) on Telegram.
2. Send `/newbot` and set a name and username.
3. Copy the token you get (e.g. `7123456789:AAH...`).

### 2. Get channel IDs

- **Option A:** Forward any post from the channel to [@userinfobot](https://t.me/userinfobot) or [@getidsbot](https://t.me/getidsbot). The bot will show you the channel ID (e.g. `-1001234567890`).
- **Option B:** For public channels you can also use the username (e.g. `@your_channel`).

### 3. Add bot as admin

1. **Main channel** (source): Add the bot as **Administrator** with at least "Post messages" or equivalent permission.
2. **Destination channel:** Add the bot as **Administrator** with "Post messages" permission so it can forward there.

### 4. Configure the project

```bash
# Optional: virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac

# Install packages
pip install -r requirements.txt

# Create config file
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/Mac
```

Edit `.env` and set:

```env
BOT_TOKEN=your_bot_token
SOURCE_CHANNEL_ID=-100xxxxxxxxxx
DESTINATION_CHANNEL_ID=-100xxxxxxxxxx
COPY_WITHOUT_FORWARD_LABEL=true
```

- `COPY_WITHOUT_FORWARD_LABEL=true` → Copy without "forwarded" label (cleaner look)
- `COPY_WITHOUT_FORWARD_LABEL=false` → Normal forward (shows source)

### 5. Run the bot

```bash
python bot.py
```

If there are no errors, the log will show: `Bot running... Source channel: ... -> Destination: ...`  
Any post in the main channel will then be automatically forwarded to the destination channel.

## Files

| File | Description |
|------|-------------|
| `bot.py` | Bot logic – listens for channel posts and copies/forwards them |
| `config.py` | Loads token and channel IDs from `.env` |
| `.env` | Your token and IDs (do not share) |
| `.env.example` | Example config – do not put real values here |

## Troubleshooting

- **Messages not forwarding:** Make sure the bot is admin in both channels and has permission to post in the destination.
- **Wrong channel ID:** Get the ID again via @userinfobot; use numeric ID for private channels (e.g. `-100...`).
- **Bot not starting:** Check that `BOT_TOKEN` and both channel IDs in `.env` are correct.
