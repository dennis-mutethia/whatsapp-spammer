import asyncio
import csv
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import PageLoadState   # <-- Add this import

from utils.db import Db

BASE_URL = "https://www.truepeoplesearch.com"
CAPTCHA_PATH = "/InternalCaptcha"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# High timeout in seconds (effectively "no timeout" for practical purposes)
NAV_TIMEOUT = 180   # 3 minutes — increase if your connection is slow

results = []  # Global list to store results across pages

async def get_current_url(tab) -> str:
    """Get current URL via JavaScript."""
    try:
        return await tab.execute_script("return window.location.href")
    except Exception:
        return ""


async def wait_for_captcha_if_needed(tab):
    current_url = await get_current_url(tab)
    if CAPTCHA_PATH in current_url:
        print("\n🔒 CAPTCHA detected!")
        print("👉 Solve it manually in the visible Chrome window.")
        print("⏳ Waiting for you to solve it...\n")
        
        while CAPTCHA_PATH in (await get_current_url(tab)):
            await asyncio.sleep(15)   # Check every 2s instead of 1s (less CPU)
        
        print("✅ CAPTCHA solved! Resuming...\n")
        await asyncio.sleep(10)  # Give the page a moment to settle


async def scrape_people(name: str, age_range: str = "57-80"):
    options = ChromiumOptions()
    options.binary_location = CHROME_PATH
    
    # Important: Tell go_to() to consider the page "loaded" earlier
    options.page_load_state = PageLoadState.INTERACTIVE

    async with Chrome(options=options) as browser:
        tab = await browser.start()

        # Hide automation fingerprint
        await tab.execute_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            delete window.chrome;
            window.chrome = { runtime: {} };
        """)

        page = 1

        while True:            
            search_url = f"{BASE_URL}/results?name={name.replace(' ', '%20')}&agerange={age_range}&page={page}"
            print(f"🌐 Opening: {search_url}")

            await tab.go_to(search_url, timeout=NAV_TIMEOUT)
                        
            print(f"📄 Scraping page {page}...")
            await wait_for_captcha_if_needed(tab)

            if not await scrape_current_page(tab):
                print(f"⚠️  Failed to scrape page {page}, stopping.")
                break

            page += 1
            await asyncio.sleep(10)  # Gentle delay between pages


async def scrape_current_page(tab) -> list[dict]:
    try:
        print("   ⏳ Waiting for search results to load...")

        # Try multiple possible selectors (more robust)
        cards = []
        
        # check for people results container - this is the most common one
        try:
            cards = await tab.find(class_name='card-summary', find_all=True, timeout=30)
        except Exception:
            pass

        # case of captcha page - look for generic card class
        if not cards:
            try:
                cards = await tab.find(class_name='card', find_all=True, timeout=15)
                await scrape_current_page(tab)
            except Exception:
                pass

        print(f"   ✅ Found {len(cards)} result card(s)")
        
        # if len(cards) == 1 and "captcha" in (await get_current_url(tab)).lower():
        #     await scrape_current_page(tab)
            
        links = []
        
        for card in cards:
            try:
                detail_link = card.get_attribute("data-detail-link")
                if detail_link:
                    detail_link = detail_link.strip()                
                    full_link = f"{BASE_URL}{detail_link}"
                    links.append(full_link)        
                
            except Exception as card_err:
                print(f"⚠️  Error parsing one card: {card_err}")
                continue

        for link in links:
            print(f"   🔗 Processing detail page: {link}")
            await tab.go_to(link, timeout=NAV_TIMEOUT)

            await asyncio.sleep(3)  # Wait for detail page to load

            title = await tab.find(tag_name="title", timeout=10)
            title_text = await title.text
            
            title_text_array = title_text.split(",")
            
            if len(title_text_array) < 4:
                print(f"⚠️  Unexpected title format: {title_text}")
                continue
            
            name = title_text_array[0].strip()
            age = int(title_text_array[1].strip().split(" in ")[0].strip().replace("Age ", ""))
            city = title_text_array[1].strip().split(" in ")[1].strip()
            state = title_text_array[2].strip()
            phone = title_text_array[3].strip().replace("(", "").replace(") ", "").replace("-", "")
            
            row = {
                "name": name,
                "age": age,
                "city": city,
                "state": state,
                "phone": f'1{phone}'
            }
            
            results.append(row)
                    
        return True 
                                            
    except Exception as e:
        print(f"⚠️  Scrape error on current page: {e}")
        return False
    

async def go_to_next_page(tab) -> bool:
    try:
        # Look for "Next" link with reasonable timeout
        next_btn = await tab.find(tag_name='a', text='Next', timeout=10)
        await next_btn.click()
        await asyncio.sleep(10)          # Wait for navigation to start
        await tab.wait_for_navigation(timeout=NAV_TIMEOUT)  # Optional but helpful if available
        return True
    except Exception:
        return False


async def scrape():        
    await scrape_people("John", age_range="57-80")
    
    if results:
        db = Db()        
        query = text("""            
            INSERT IGNORE INTO contacts (name, age, city, state, phone)
            VALUES (:name, :age, :city, :state, :phone)
        """)
        
        try:
            with self.db.engine.begin() as conn:  
                conn.execute(query, results)
                logger.info("Inserted %d contacts into database", len(results))
        except SQLAlchemyError as e:
            logger.error("Error inserting contacts: %s", e)

