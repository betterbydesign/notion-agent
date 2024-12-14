import os
from dotenv import load_dotenv
from config import Config
from notion_client import NotionClient
from ai_client import AIClient

import asyncio
import os
from dotenv import load_dotenv
from config import Config
from notion_client import NotionClient
from ai_client import AIClient

async def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Initialize configuration
    config = Config("config.yaml")
    
    # Initialize Notion client with workspace A token
    notion = NotionClient(
        token=os.getenv("NOTION_WORKSPACE_A_TOKEN"),
        config=config.config
    )
    
    # Initialize AI client
    ai = AIClient(config.config)
    
    # Example: Get a block from Notion
    block_id = "your-block-id-here"  # Replace with actual block ID
    try:
        block = notion.get_block(block_id)
        print(f"Retrieved block: {block}")
        
        # Generate AI response based on block content
        if "content" in block:
            response = await ai.generate_text(f"Analyze this text: {block['content']}")
            print(f"AI Analysis: {response}")
            
            # Update the block with AI response
            notion.update_block(
                block_id,
                content=response
            )
            print("Block updated with AI response")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
