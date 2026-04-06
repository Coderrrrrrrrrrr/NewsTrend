import os
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth

class BrowserHelper:
    def __init__(self, profile_dir="./data/browser_profile", headless=True):
        self.profile_dir = profile_dir
        self.headless = headless
        if not os.path.exists(self.profile_dir):
            os.makedirs(self.profile_dir)

    async def get_browser_context(self, playwright):
        """
        Launch a persistent browser context with stealth plugin.
        """
        # Specify executable path if needed, but playwright usually handles it.
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=self.profile_dir,
            headless=self.headless,
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        return context

    async def fetch_page_with_stealth(self, url, wait_until="networkidle"):
        """
        Fetch a page and return its content using stealth mode.
        """
        async with async_playwright() as p:
            context = await self.get_browser_context(p)
            page = await context.new_page()
            await stealth(page)
            
            try:
                await page.goto(url, wait_until=wait_until, timeout=30000)
                content = await page.content()
                # Extract cookies for possible injection
                cookies = await context.cookies()
                return content, cookies
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                return None, None
            finally:
                await context.close()

    def launch_interactive_browser(self):
        """
        Launch a non-headless browser for manual verification.
        This blocks until the browser is closed.
        """
        import subprocess
        # Use a simpler approach: launch chrome with the same user data dir via CLI
        # Or use playwright if it's easier to manage
        async def _launch():
            async with async_playwright() as p:
                context = await self.get_browser_context(p)
                # Ensure headless is false for this call
                # Actually launch_persistent_context doesn't allow changing headless easily if pre-set
                # Let's create a new one for interactive
                pass
        
        # Refactor: just run a script that launches playwright non-headless
        script_path = os.path.join(os.getcwd(), "scripts/launch_browser.py")
        if not os.path.exists("scripts"):
            os.makedirs("scripts")
            
        with open(script_path, "w", encoding="utf-8") as f:
            abs_profile = os.path.abspath(self.profile_dir)
            f.write(f"""
import asyncio
import sys
import os
from playwright.async_api import async_playwright

async def main():
    print(f"[*] Starting Shadow Browser with profile: {repr(abs_profile)}")
    try:
        async with async_playwright() as p:
            try:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir={repr(abs_profile)},
                    headless=False,
                    viewport={{'width': 1280, 'height': 800}},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
            except Exception as e:
                if "user_data_dir is already in use" in str(e).lower() or "is already open" in str(e).lower():
                    print("\\n[!] Error: The browser profile is already in use by another process.")
                    print("[!] Please ensure no other crawl tasks are running and try again.")
                else:
                    print(f"\\n[!] Failed to launch browser: {{e}}")
                return

            page = await context.new_page()
            await page.goto("https://weixin.sogou.com/")
            print("\\n[SUCCESS] Browser launched.")
            print("[ACTION] Please complete the CAPTCHA/Verification in the browser window.")
            print("[ACTION] Close the browser window when you are finished.")
            
            # Block until context is closed or pages are empty
            while len(context.pages) > 0:
                await asyncio.sleep(1)
            
            await context.close()
            print("[*] Browser closed. Verification data saved to profile.")
    except Exception as e:
        print(f"\\n[CRITICAL ERROR] {{e}}")
    finally:
        print("\\n[DONE] Press Enter to exit...")
        input()

if __name__ == "__main__":
    asyncio.run(main())
""")
        return script_path

if __name__ == "__main__":
    # Test
    bh = BrowserHelper()
    # asyncio.run(bh.fetch_page_with_stealth("https://httpbin.org/headers"))
