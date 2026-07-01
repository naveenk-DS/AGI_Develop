# app/services/playwright_automation.py
"""
Isolated Playwright automation — runs in its own thread with its own event loop.
This avoids the "Event loop is closed" conflict with FastAPI's main event loop.
"""
import asyncio
import threading
from concurrent.futures import Future
from loguru import logger
from playwright.async_api import async_playwright

_loop = None
_thread = None
_browser = None
_playwright = None


def _start_background_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def get_loop():
    """Get or create the dedicated background event loop for Playwright."""
    global _loop, _thread
    if _loop is None:
        _loop = asyncio.new_event_loop()
        _thread = threading.Thread(target=_start_background_loop, args=(_loop,), daemon=True)
        _thread.start()
        logger.info("Playwright background event loop started")
    return _loop


async def _ensure_browser():
    global _browser, _playwright
    if _browser is None:
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(headless=False)
        logger.info("Playwright browser launched")
    return _browser


async def _click_element(url: str, selector: str = None, text: str = None):
    """Open a page and click an element by selector or visible text."""
    browser = await _ensure_browser()
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        if selector:
            await page.click(selector, timeout=8000)
        elif text:
            await page.get_by_text(text, exact=False).first.click(timeout=8000)
        return f"Clicked on {selector or text} at {url}"
    except Exception as e:
        return f"Could not click: {e}"
    finally:
        await page.close()


async def _fill_form(url: str, fields: dict, submit_selector: str = None):
    """Open a page, fill form fields, optionally submit."""
    browser = await _ensure_browser()
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        for selector, value in fields.items():
            await page.fill(selector, value, timeout=8000)
        if submit_selector:
            await page.click(submit_selector, timeout=8000)
        return f"Form filled at {url}"
    except Exception as e:
        return f"Could not fill form: {e}"
    finally:
        await page.close()


async def _scrape_text(url: str, selector: str = None) -> str:
    """Get visible text content from a page or specific element."""
    browser = await _ensure_browser()
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        if selector:
            content = await page.inner_text(selector)
        else:
            content = await page.inner_text("body")
        return content[:2000]  # cap length
    except Exception as e:
        return f"Could not scrape: {e}"
    finally:
        await page.close()


def _run_coroutine_threadsafe(coro):
    """Submit a coroutine to the dedicated Playwright loop and wait for result."""
    loop = get_loop()
    future: Future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=30)


# ── Public sync-callable functions (safe to call from FastAPI/LangGraph) ──────
def click_on_page(url: str, selector: str = None, text: str = None) -> str:
    return _run_coroutine_threadsafe(_click_element(url, selector, text))


def fill_form_on_page(url: str, fields: dict, submit_selector: str = None) -> str:
    return _run_coroutine_threadsafe(_fill_form(url, fields, submit_selector))


def scrape_page_text(url: str, selector: str = None) -> str:
    return _run_coroutine_threadsafe(_scrape_text(url, selector))


async def _get_clickable_elements(page) -> list:
    """Extract all clickable elements with their visible text/labels from the DOM."""
    elements = await page.evaluate("""
        () => {
            const selectors = 'button, a, input[type="submit"], input[type="button"], [role="button"], [onclick]';
            const els = document.querySelectorAll(selectors);
            const results = [];
            els.forEach((el, i) => {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    const text = (el.innerText || el.value || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').trim();
                    if (text) {
                        results.push({
                            index: i,
                            text: text.substring(0, 60),
                            tag: el.tagName.toLowerCase(),
                            type: el.type || ''
                        });
                    }
                }
            });
            return results;
        }
    """)
    return elements


async def _get_input_fields(page) -> list:
    """Extract all fillable input fields with their labels/placeholders."""
    fields = await page.evaluate("""
        () => {
            const inputs = document.querySelectorAll('input, textarea, select');
            const results = [];
            inputs.forEach((el, i) => {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0 && el.type !== 'hidden' && el.type !== 'submit' && el.type !== 'button') {
                    const label = el.getAttribute('aria-label') || el.placeholder || el.name || el.id || '';
                    results.push({
                        index: i,
                        label: label,
                        type: el.type || el.tagName.toLowerCase(),
                        name: el.name || ''
                    });
                }
            });
            return results;
        }
    """)
    return fields

async def _voice_click(url: str, spoken_instruction: str, existing_page=None) -> str:
    """Click an element based on natural voice description, matched via DOM + LLM."""
    browser = await _ensure_browser()
    page = existing_page or await browser.new_page()
    opened_new_page = existing_page is None

    try:
        if opened_new_page:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)

        elements = await _get_clickable_elements(page)
        if not elements:
            return "No clickable elements found on this page."

        # Ask LLM to match spoken instruction to the right element
        from core.llm import get_llm
        llm = get_llm()
        elements_list = "\n".join([f"{i}: {e['text']} ({e['tag']})" for i, e in enumerate(elements)])

        prompt = (
            f"Naveen said: 'click {spoken_instruction}'\n\n"
            f"Available clickable elements on the page:\n{elements_list}\n\n"
            "Which index number best matches what Naveen wants to click? "
            "Reply with ONLY the number. If nothing matches well, reply -1."
        )
        result = await llm.ainvoke(prompt)
        try:
            chosen_index = int(result.content.strip())
        except:
            chosen_index = -1

        if chosen_index == -1 or chosen_index >= len(elements):
            return f"Could not find anything matching '{spoken_instruction}' on this page."

        matched_text = elements[chosen_index]["text"]

        # Click using Playwright's text-based locator for reliability
        await page.get_by_text(matched_text, exact=False).first.click(timeout=8000)

        return f"Clicked '{matched_text}'"

    except Exception as e:
        return f"Could not click: {e}"
    finally:
        if opened_new_page:
            await page.close()


async def _voice_fill(url: str, spoken_field: str, value: str, existing_page=None) -> str:
    """Fill a form field based on natural voice description."""
    browser = await _ensure_browser()
    page = existing_page or await browser.new_page()
    opened_new_page = existing_page is None

    try:
        if opened_new_page:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)

        fields = await _get_input_fields(page)
        if not fields:
            return "No fillable fields found on this page."

        from core.llm import get_llm
        llm = get_llm()
        fields_list = "\n".join([f"{i}: {f['label']} ({f['type']})" for i, f in enumerate(fields)])

        prompt = (
            f"Naveen said: 'fill {spoken_field} with {value}'\n\n"
            f"Available input fields on the page:\n{fields_list}\n\n"
            "Which index number best matches the field Naveen wants to fill? "
            "Reply with ONLY the number. If nothing matches, reply -1."
        )
        result = await llm.ainvoke(prompt)
        try:
            chosen_index = int(result.content.strip())
        except:
            chosen_index = -1

        if chosen_index == -1 or chosen_index >= len(fields):
            return f"Could not find a field matching '{spoken_field}'."

        field_label = fields[chosen_index]["label"]
        field_name = fields[chosen_index]["name"]

        # Fill using name attribute selector
        if field_name:
            await page.fill(f'[name="{field_name}"]', value, timeout=8000)
        else:
            return f"Found field '{field_label}' but could not target it reliably."

        return f"Filled '{field_label}' with '{value}'"

    except Exception as e:
        return f"Could not fill field: {e}"
    finally:
        if opened_new_page:
            await page.close()


# ── Public sync-callable wrappers ──────────────────────────────────────────────
def voice_click(url: str, spoken_instruction: str) -> str:
    return _run_coroutine_threadsafe(_voice_click(url, spoken_instruction))


def voice_fill(url: str, spoken_field: str, value: str) -> str:
    return _run_coroutine_threadsafe(_voice_fill(url, spoken_field, value))

def shutdown_browser():
    async def _close():
        global _browser, _playwright
        if _browser:
            await _browser.close()
        if _playwright:
            await _playwright.stop()
    _run_coroutine_threadsafe(_close())