import asyncio
import logging
from navix.services.whatsapp import WhatsAppClient, Message

# Enable logging so we can see what the package is doing in the background
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# This is the callback function that will run every time a new message is received
async def handle_new_message(msg: Message):
    # To find your exact WhatsApp ID/Name, just look at what prints out here!
    print("\n" + "="*50)
    print(f"👀 DISCOVERED A MESSAGE!")
    print(f"👉 YOUR EXACT CHAT ID IS: '{msg.chat_id}'")
    print(f"👉 EXACT SENDER NAME IS: '{msg.sender_name}'")
    print(f"Type: {msg.type.name if hasattr(msg.type, 'name') else msg.type}")
    print(f"Content: {msg.content}")
    print("="*50 + "\n")
    
    # Once you see the exact ID printed above, you can re-enable the filter below:
    # TARGET_CHAT_NAME = "Exact Name Printed Above" 
    # if msg.chat_id != TARGET_CHAT_NAME:
    #     return

async def main():
    print("Starting WhatsApp client...")
    # headless=False so you can see the browser and scan the QR code on your first run
    client = WhatsAppClient(session_dir="./whatsapp_session", headless=False)
    
    # Register the callback function
    client.on_message(handle_new_message)
    
    # Start the client (this opens the browser)
    await client.start()
    print("WhatsApp client is running and listening for new messages. Press Ctrl+C to stop.")
    
    # Keep the script running forever
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping WhatsApp client...")
        await client.stop()

if __name__ == "__main__":
    asyncio.run(main())
