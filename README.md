# Roblox Moderation Bot

A Discord moderation bot built with Python (discord.py). It integrates with the Roblox and Bloxlink APIs to verify user identities, check linked accounts, and log moderation actions via slash commands.

## Prerequisites
- Python 3.8 or higher.
- Discord Developer Bot Token.
- Bloxlink Server API Key.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Environment setup:
Copy the `.env.example` file to a new file named `.env` and insert credentials.
```bash
cp .env.example .env
```

## Configuration

Edit `config.py` to match your server environment:
- `GUILD_ID`: Your Discord server ID.
- `LOG_CHANNEL_ID`: The channel or forum ID where logs will be posted use a thread type.
- `ALLOWED_ROLE_IDS`: A list of role IDs authorized to use the bot commands.

## Usage

Start the bot by running the main script:
```bash
python main.py
```

Once online, authorized users can utilize the following command in your Discord server:
`/log username:<roblox_username> reason:<reason> punishment:<punishment> proof:<link>`