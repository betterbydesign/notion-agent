import asyncio
from dotenv import load_dotenv
import os
from notion_wrapper import NotionClient
from config import Config

async def main():
    load_dotenv()
    config = Config("config.yaml")
    notion = NotionClient(
        token=os.getenv("NOTION_WORKSPACE_A_TOKEN"),
        config=config.config
    )
    
    page_id = "15b54dbce6ab809299cff2ba8ea24753"
    
    # Get page content
    blocks = notion.client.blocks.children.list(page_id).get('results', [])
    
    # Print all text content
    for block in blocks:
        if block['type'] == 'paragraph':
            rich_text = block.get('paragraph', {}).get('rich_text', [])
            if rich_text and len(rich_text) > 0:
                text = rich_text[0].get('plain_text', '')
                if text:
                    print(text)
        elif block['type'] == 'numbered_list_item':
            rich_text = block.get('numbered_list_item', {}).get('rich_text', [])
            if rich_text and len(rich_text) > 0:
                text = rich_text[0].get('plain_text', '')
                if text:
                    print(text)

if __name__ == "__main__":
    asyncio.run(main())
