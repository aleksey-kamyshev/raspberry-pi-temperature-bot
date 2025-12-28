# RPi Telegram Monitor

Simple Telegram bot for monitoring Raspberry Pi system status.

## Features
- CPU temperature monitoring
- CPU load monitoring
- RAM usage monitoring
- Automatic status updates every 10 minutes
- Manual status request via command

## Commands
- `/start` — subscribe to automatic updates
- `/stop` — stop automatic updates
- `/temp` — get current system status

## Tech stack
- Python 3
- requests
- psutil

## Use case
Useful for monitoring headless Raspberry Pi devices without SSH access.

## Setup
1. Clone repository
2. Create `.env` file with `TG_BOT_TOKEN`
3. Install dependencies  
   `pip install -r requirements.txt`
4. Run bot  
   `python bot.py`
