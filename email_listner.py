import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="agent/.env")

os.environ["GOOGLE_CLOUD_PROJECT"] = os.getenv("GOOGLE_CLOUD_PROJECT")

import json
import asyncio
import threading
import time
from google.cloud import pubsub_v1
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Import the agent
from agent.gmailassistant import main as agent_main

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
SUBSCRIPTION_ID = os.getenv("SUBSCRIPTION_ID")
TOKEN_PATH = os.getenv("TOKEN_PATH")

# Deduplication: Track processed message IDs (not history IDs!)
processed_messages = set()
message_lock = threading.Lock()
MAX_CACHE_SIZE = 100

# Gmail service
def get_gmail_service():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    return build("gmail", "v1", credentials=creds)

def get_latest_message_id():
    """Get the ID of the most recent email"""
    try:
        service = get_gmail_service()
        results = service.users().messages().list(
            userId='me',
            maxResults=1,
            labelIds=['INBOX']
        ).execute()
        
        messages = results.get('messages', [])
        if messages:
            return messages[0]['id']
        return None
    except Exception as e:
        print(f"Error getting message ID: {e}")
        return None

def run_agent_in_background(message_id):
    """Run the agent in a new event loop in a background thread"""
    try:
        print(f"🤖 Starting agent for message ID: {message_id}...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(agent_main())
        loop.close()
        print("✅ Agent completed\n")
    except Exception as e:
        print(f"❌ Agent error: {e}\n")

# Process incoming email notification
def process_notification(message):
    try:
        # Decode Pub/Sub message
        data = json.loads(message.data.decode('utf-8'))
        email_address = data.get('emailAddress')
        history_id = data.get('historyId')
        
        # Get the actual message ID of the latest email
        latest_message_id = get_latest_message_id()
        
        if not latest_message_id:
            print("⚠️ No message found in inbox")
            message.ack()
            return
        
        # Check if we've already processed this message
        with message_lock:
            if latest_message_id in processed_messages:
                print(f"⏭️  Skipping - already processed message ID: {latest_message_id}")
                message.ack()
                return
            
            # Add to processed set
            processed_messages.add(latest_message_id)
            
            # Keep cache size limited
            if len(processed_messages) > MAX_CACHE_SIZE:
                processed_messages.pop()
        
        # Print notification
        print("\n" + "="*60)
        print("📧 NEW EMAIL RECEIVED!")
        print("="*60)
        print(f"Account: {email_address}")
        print(f"History ID: {history_id}")
        print(f"Message ID: {latest_message_id}")
        print("="*60 + "\n")
        
        # Start agent in a background thread
        agent_thread = threading.Thread(
            target=run_agent_in_background, 
            args=(latest_message_id,),
            daemon=True
        )
        agent_thread.start()
        
        # Acknowledge immediately
        message.ack()
        
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        message.nack()

# Main listener
def main():
    print("="*60)
    print("🚀 Gmail Event Listener Started")
    print("="*60)
    print(f"Project: {PROJECT_ID}")
    print(f"Subscription: {SUBSCRIPTION_ID}")
    print("\n📬 Waiting for incoming emails...")
    print("Press Ctrl+C to stop\n")
    
    # Create subscriber
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)
    
    # Start listening
    streaming_pull_future = subscriber.subscribe(
        subscription_path,
        callback=process_notification
    )
    
    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        streaming_pull_future.cancel()
        streaming_pull_future.result()
        print("\n\n⏹️ Listener stopped")

if __name__ == "__main__":
    main()