from navix.automation.tools import tool
from navix.services.browser.browser import (
    open_url, search_google, search_wikipedia, open_youtube, get_news
)
from navix.services.ai.command_parser import execute_browser_command

@tool(
    name="browser_open_url", 
    description="Opens a specific URL in a new browser tab."
)
async def browser_open_url(url: str):
    return await open_url(url)

@tool(
    name="browser_search", 
    description="Performs a Google search and reads the results."
)
async def browser_search(query: str):
    return await search_google(query)

@tool(
    name="browser_complex_command", 
    description="Executes a complex browser automation task (e.g. 'find the cheapest flight to Tokyo')."
)
async def browser_complex_command(command: str):
    return await execute_browser_command(command)
