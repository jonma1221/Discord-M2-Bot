import os

from google import genai
import asyncio

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY")).aio

def get_youtube_guides(prompt) -> str:
    response = client.models.generate_content(
        model="gemini-3-flash-preview", contents=f"Make sure to limit the character count to 2000 characters so the message can be sent to discord. Include youtube links if possible. Here is the prompt: {prompt}"
    )
    return response.text

async def execute_prompt(prompt):
    def blocking_call():
        return client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=f"Make sure to limit the character count to 2000 characters so the message can be sent to discord. Include youtube links if possible. Here is the prompt: {prompt}"
        )

    response = await asyncio.to_thread(blocking_call)
    return response.text

async def execute_prompt_async(prompt):
    response = await client.models.generate_content(
        model="gemini-3-flash-preview", contents=f"Format the responses using Discord Markdown. Make sure to limit the character count to 2000 characters so the message can be sent to discord. Include youtube links if possible. Here is the prompt: {prompt}"
    )
    return response.text