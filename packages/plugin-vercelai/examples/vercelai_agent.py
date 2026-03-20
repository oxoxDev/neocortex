"""Example demonstrating Neocortex memory tools with Vercel AI SDK Python."""

import asyncio
import os
from dotenv import load_dotenv

from ai_sdk import generate_text
from ai_sdk.providers.openai import openai
from ai_sdk.messages import UserMessage

from tinyhumansai import TinyHumanMemoryClient
from neocortex_vercelai import NeocortexMemoryTools

async def main():
    load_dotenv()
    token = os.getenv("ALPHAHUMAN_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not token or not openai_key:
        print("Please set ALPHAHUMAN_API_KEY and OPENAI_API_KEY")
        return

    # Initialize Memory Client
    memory_client = TinyHumanMemoryClient(token=token)

    # Initialize Tools Wrapper
    memory_tools_wrapper = NeocortexMemoryTools(client=memory_client, default_namespace="vercelai_session")
    
    # Get tools dictionary for Vercel AI SDK
    tools = memory_tools_wrapper.get_tools()

    print("--- Saving memory ---")
    result1 = await generate_text(
        model=openai("gpt-4o-mini"),
        messages=[
            UserMessage(content="Please remember that my favorite hobby is painting minatures. Save it in your memory."),
        ],
        tools=tools,
        max_steps=5, # Allow the SDK to automatically execute the tool and feed the result back
    )
    print("Agent Response:", result1.text)

    print("\n\n--- Recalling memory ---")
    result2 = await generate_text(
        model=openai("gpt-4o-mini"),
        messages=[
            UserMessage(content="What is my favorite hobby? Check your memory."),
        ],
        tools=tools,
        max_steps=5,
    )
    print("Agent Response:", result2.text)

if __name__ == "__main__":
    asyncio.run(main())
