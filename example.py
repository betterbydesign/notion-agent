import asyncio
import os
from dotenv import load_dotenv
from config import Config
from notion_wrapper import NotionClient
from ai_client import AIClient

async def search_pages(notion):
    search_query = input("Enter search term to find pages: ").strip()
    print(f"\nSearching for pages containing '{search_query}'...")
    results = notion.client.search(
        query=search_query,
        filter={"property": "object", "value": "page"}
    ).get('results', [])
    
    if not results:
        print("No pages found matching your search.")
        return None, None
    
    print("\nFound pages:")
    for i, page in enumerate(results, 1):
        title_array = page.get('properties', {}).get('title', {}).get('title', [])
        title = title_array[0].get('plain_text', 'Untitled') if title_array else 'Untitled'
        print(f"{i}. {title} (ID: {page['id']})")
    
    selection = input("\nEnter the number of the page to select (or press Enter to cancel): ").strip()
    if selection.isdigit() and 1 <= int(selection) <= len(results):
        page = results[int(selection)-1]
        title_array = page.get('properties', {}).get('title', {}).get('title', [])
        title = title_array[0].get('plain_text', 'Untitled') if title_array else 'Untitled'
        return page['id'], title
    return None, None

async def get_page_content(notion, page_id):
    blocks = notion.client.blocks.children.list(page_id).get('results', [])
    content = []
    for block in blocks:
        if block['type'] == 'paragraph':
            rich_text = block.get('paragraph', {}).get('rich_text', [])
            if rich_text and len(rich_text) > 0:
                text = rich_text[0].get('plain_text', '')
                if text:
                    content.append(text)
        elif block['type'] == 'numbered_list_item':
            rich_text = block.get('numbered_list_item', {}).get('rich_text', [])
            if rich_text and len(rich_text) > 0:
                text = rich_text[0].get('plain_text', '')
                if text:
                    content.append(text)
    return '\n'.join(content)  # Changed from ' '.join to '\n'.join for better readability

async def chat_mode(ai, notion=None, context=None):
    print("\nEntering chat mode. Type 'exit' to return to main menu.")
    if context:
        print("Current context: Using content from your selected Notion page.")
        # Don't set initial context, just use it for each question
    
    while True:
        question = input("\nYou: ").strip()
        if question.lower() == 'exit':
            break
        
        if context:
            # Include the context in each question
            full_prompt = f"""Here is the content of a Notion page:

{context}

Based on this content, please answer the following question:
{question}"""
            response = await ai.generate_text(full_prompt)
        else:
            response = await ai.generate_text(question)
        
        print("\nAI:", response)

async def write_to_page(notion, page_id):
    print("\nEnter your content (press Enter twice to finish):")
    lines = []
    while True:
        line = input()
        if not line and lines and not lines[-1]:
            break
        lines.append(line)
    
    content = '\n'.join(lines[:-1])  # Remove the last empty line
    
    if content:
        notion.client.blocks.children.append(
            page_id,
            children=[{
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {
                            "content": content
                        }
                    }]
                }
            }]
        )
        print("Content added to the page successfully!")

async def main():
    load_dotenv()
    config = Config("config.yaml")
    notion = NotionClient(
        token=os.getenv("NOTION_WORKSPACE_A_TOKEN"),
        config=config.config
    )
    ai = AIClient(config.config)
    
    current_page_id = None
    current_page_title = None
    current_page_content = None
    
    while True:
        print("\n=== Notion AI Agent ===")
        if current_page_id:
            print(f"Current page: {current_page_title}")
        print("\n1. Search and select a page")
        print("2. Chat with AI" + (" about current page" if current_page_id else ""))
        print("3. Write to current page" if current_page_id else "3. [Select a page first]")
        print("4. Analyze current page" if current_page_id else "4. [Select a page first]")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        try:
            if choice == '1':
                current_page_id, current_page_title = await search_pages(notion)
                if current_page_id:
                    current_page_content = await get_page_content(notion, current_page_id)
                    print(f"\nSelected page: {current_page_title}")
            
            elif choice == '2':
                await chat_mode(ai, notion, current_page_content if current_page_id else None)
            
            elif choice == '3':
                if current_page_id:
                    await write_to_page(notion, current_page_id)
                else:
                    print("\nPlease select a page first (option 1)")
            
            elif choice == '4':
                if current_page_id and current_page_content:
                    print("\nAnalyzing page content...")
                    analysis = await ai.generate_text(
                        f"Please analyze this content and provide a summary and key insights:\n\n{current_page_content}"
                    )
                    print("\nAI Analysis:")
                    print(analysis)
                    
                    if input("\nWould you like to append this analysis to the page? (y/n): ").lower() == 'y':
                        notion.client.blocks.children.append(
                            current_page_id,
                            children=[{
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{
                                        "type": "text",
                                        "text": {
                                            "content": f"\nAI Analysis:\n{analysis}"
                                        }
                                    }]
                                }
                            }]
                        )
                        print("Analysis appended to the page!")
                else:
                    print("\nPlease select a page first (option 1)")
            
            elif choice == '5':
                print("\nGoodbye!")
                break
            
            else:
                print("\nInvalid choice. Please enter a number between 1 and 5.")
                
        except Exception as e:
            print(f"\nError: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
