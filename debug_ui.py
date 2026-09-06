import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navigating to Streamlit app...")
        await page.goto("http://localhost:8501", timeout=60000)
        
        # Wait for the app to finish running (usually a span with data-testid="stStatusWidget" appears and disappears)
        print("Waiting for app to load...")
        await page.wait_for_selector('section[data-testid="stSidebar"]', timeout=30000)
        await page.wait_for_timeout(3000) # Give it 3 extra seconds to fully settle
        
        print("Closing the sidebar...")
        close_btn = await page.query_selector('[data-testid="stSidebarCollapseButton"]')
        if close_btn:
            await close_btn.click()
        else:
            print("Could not find close button.")
            
        print("Waiting 10 seconds (as user described)...")
        await page.wait_for_timeout(10000)
        
        print("Extracting DOM info for sidebar controls and header...")
        info = await page.evaluate('''() => {
            function getInfo(selector) {
                const el = document.querySelector(selector);
                if (!el) return null;
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                return {
                    tagName: el.tagName,
                    classes: el.className,
                    rect: {x: rect.x, y: rect.y, width: rect.width, height: rect.height},
                    display: style.display,
                    visibility: style.visibility,
                    opacity: style.opacity,
                    transform: style.transform,
                    position: style.position,
                    zIndex: style.zIndex,
                    pointerEvents: style.pointerEvents,
                    parent: el.parentElement ? el.parentElement.tagName + " " + el.parentElement.className : null
                };
            }
            
            return {
                header: getInfo('header[data-testid="stHeader"]'),
                collapsedControl: getInfo('[data-testid="collapsedControl"]'),
                expandBtn: getInfo('[data-testid="stSidebarExpandButton"]'),
                toolbar: getInfo('[data-testid="stToolbar"]'),
                mainMenu: getInfo('#MainMenu'),
                body: {width: document.body.clientWidth, height: document.body.clientHeight}
            };
        }''')
        
        import json
        print(json.dumps(info, indent=2))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
