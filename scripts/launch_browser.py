
import asyncio
import sys
import os
from playwright.async_api import async_playwright

async def main():
    print(f"[*] Starting Shadow Browser with profile: 'E:\\PycharmProject\\AccioWork\\NewsTrend\\data\\browser_profile'")
    try:
        async with async_playwright() as p:
            try:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir='E:\\PycharmProject\\AccioWork\\NewsTrend\\data\\browser_profile',
                    headless=False,
                    viewport={'width': 1280, 'height': 800},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
            except Exception as e:
                if "user_data_dir is already in use" in str(e).lower() or "is already open" in str(e).lower():
                    print("\n[!] Error: The browser profile is already in use by another process.")
                    print("[!] Please ensure no other crawl tasks are running and try again.")
                else:
                    print(f"\n[!] Failed to launch browser: {e}")
                return

            page = await context.new_page()
            await page.goto("https://weixin.sogou.com/")
            print("\n[SUCCESS] Browser launched.")
            print("[ACTION] Please complete the CAPTCHA/Verification in the browser window.")
            print("[ACTION] Close the browser window when you are finished.")
            
            # Block until context is closed or pages are empty
            while len(context.pages) > 0:
                await asyncio.sleep(1)
            
            await context.close()
            print("[*] Browser closed. Verification data saved to profile.")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")
    finally:
        print("\n[DONE] Press Enter to exit...")
        input()

if __name__ == "__main__":
    asyncio.run(main())
