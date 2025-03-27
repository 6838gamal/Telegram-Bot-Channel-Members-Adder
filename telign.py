from telethon.sync import TelegramClient, events
from telethon.errors.rpcerrorlist import PhoneNumberBannedError, PeerFloodError, UserPrivacyRestrictedError, ChatAdminRequiredError, ChatWriteForbiddenError, UserBannedInChannelError, UserAlreadyParticipantError, FloodWaitError
from telethon.tl.functions.channels import InviteToChannelRequest, JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest, AddChatUserRequest
from telethon.tl.types import InputPeerChannel, InputPeerUser
import pickle, os, sys, time, random
from colorama import init, Fore
from time import sleep
import requests
import asyncio

init()

# Color definitions
n = Fore.RESET
lg = Fore.LIGHTGREEN_EX
r = Fore.RED
w = Fore.WHITE
cy = Fore.CYAN
ye = Fore.YELLOW
colors = [lg, r, w, cy, ye]
info = f'{lg}[{w}i{lg}]{n}'
error = f'{lg}[{r}!{lg}]{n}'
success = f'{w}[{lg}*{w}]{n}'
INPUT = f'{lg}[{cy}~{lg}]{n}'
plus = f'{w}[{lg}+{w}]{n}'
minus = f'{w}[{lg}-{w}]{n}'

# Telegram App ID and Hash
APP_ID = 20200731
APP_HASH = 'debec87745352ef7c5fdcae9622930a1'

# Bot Token
BOT_TOKEN = '7619415487:AAGm0unxV44fKLEmyTK2O7ZirgVMeLCBZGE'

# Initialize the Telegram client
client = TelegramClient('bot_session', APP_ID, APP_HASH)

# Global variables to store source and target group links
scraped_grp = None
target_link = None
process_started = False

# Start Method
def start_method():
    """Start Method: Initialize the process."""
    print(f'{info}{lg} Start Method: Initializing the process{n}')
    return "👋 Welcome! Please provide the source group link."

# Source Method
def source_method(group_link):
    """Source Method: Scrape members from a group."""
    global scraped_grp
    print(f'{info}{lg} Source Method: Scrape members from a group{n}')
    scraped_grp = group_link
    return f"✅ Source group set to: {scraped_grp}\n\n" \
           "Now, please provide the target group link."

# Target Method
def target_method(target):
    """Target Method: Select target group."""
    global target_link
    print(f'{info}{lg} Target Method: Select target group{n}')
    target_link = target
    return f"✅ Target group set to: {target_link}\n\n" \
           "Now, use /process to start adding members."

# Process Method
async def process_method(event):
    """Process Method: Add members from source to target group."""
    global scraped_grp, target_link, process_started
    print(f'{info}{lg} Process Method: Adding members from source to target group{n}')
    if not scraped_grp or not target_link:
        return "❌ Please set both source and target groups first."

    process_started = True
    await event.reply("🚀 Starting the process...\n\n" \
                     f"Source Group: {scraped_grp}\n" \
                     f"Target Group: {target_link}\n\n" \
                     "Please wait while the bot processes your request.")

    try:
        # Connect to the source group
        source_entity = await client.get_entity(scraped_grp)
        target_entity = await client.get_entity(target_link)

        # Scrape members from the source group
        members = await client.get_participants(source_entity, aggressive=True)
        total_members = len(members)
        await event.reply(f"🔍 Found {total_members} members in the source group.")

        # Add members to the target group
        added_count = 0
        skipped_count = 0
        for i, user in enumerate(members):
            if not process_started:  # Allow stopping the process
                break

            try:
                # Skip invalid or deleted accounts
                if not user or not hasattr(user, 'id') or not user.id:
                    skipped_count += 1
                    continue

                # Add user to the target group
                await client(InviteToChannelRequest(target_entity, [user]))
                added_count += 1
                await event.reply(f"✅ Added {user.first_name or 'Unknown'} ({user.id}) to the target group.")
                
                # Add delay to avoid flooding
                await asyncio.sleep(random.uniform(5, 10))
                
            except UserPrivacyRestrictedError:
                await event.reply(f"❌ User {user.first_name or 'Unknown'} has privacy restrictions and cannot be added.")
                skipped_count += 1
            except UserAlreadyParticipantError:
                await event.reply(f"❌ User {user.first_name or 'Unknown'} is already in the target group.")
                skipped_count += 1
            except PeerFloodError:
                await event.reply("❌ Too many requests. Please wait before trying again.")
                break
            except FloodWaitError as e:
                wait_time = e.seconds
                await event.reply(f"⏳ Flood control: Waiting {wait_time} seconds before continuing...")
                await asyncio.sleep(wait_time)
                continue
            except Exception as e:
                await event.reply(f"❌ Error adding {user.first_name or 'Unknown'}: {str(e)}")
                skipped_count += 1
                continue

            # Progress update every 10 users or when complete
            if (i + 1) % 10 == 0 or (i + 1) == total_members:
                progress = int((i + 1) / total_members * 100)
                await event.reply(f"⏳ Progress: {progress}% ({i+1}/{total_members})\n"
                                 f"✅ Added: {added_count} | ❌ Skipped: {skipped_count}")

        process_started = False
        return f"🎉 Process completed!\n" \
               f"✅ Successfully added: {added_count} members\n" \
               f"❌ Skipped: {skipped_count} members\n" \
               f"📊 Total processed: {total_members} members"
    except Exception as e:
        process_started = False
        return f"❌ An error occurred: {e}"

# Event handler for new messages
@client.on(events.NewMessage)
async def handle_message(event):
    """Handle incoming messages from the bot."""
    sender = await event.get_sender()
    message = event.message.message

    print(f"{lg}[+] Received message from {sender.username}: {message}{n}")

    if message.startswith('/start'):
        response = start_method()
    elif message.startswith('/process'):
        if process_started:
            response = "🔄 The process is already running. Please wait."
        else:
            response = await process_method(event)
    elif message.startswith('https://t.me/'):
        if scraped_grp is None:
            response = source_method(message)
        elif target_link is None:
            response = target_method(message)
        else:
            response = "✅ Both source and target groups are already set. Use /process to start."
    else:
        response = "❌ Unknown command or invalid input. Please provide a valid group link or use /start, /process."

    # Reply to the bot
    if not process_started or message.startswith('/process'):
        await event.reply(response)
    print(f"{lg}[+] Replied to the bot: {response}{n}")

# Main function to run the bot
async def main():
    print(f"{lg}[+] Connecting to Telegram...{n}")
    await client.connect()
    if not await client.is_user_authorized():
        print(f"{r}[!] Failed to connect. Please check your bot token.{n}")
        return

    print(f"{lg}[+] Bot is running...{n}")
    await client.run_until_disconnected()

if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())