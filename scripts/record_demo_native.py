import asyncio
import os
import shutil
from playwright.async_api import async_playwright

async def record_playwright_video():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_video_path = os.path.join(repo_root, "docs", "assets", "schemap_demo_showcase.webm")
    os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
    
    html_abs = os.path.join(repo_root, "examples", "demo_presentation.html")
    html_file_path = "file:///" + html_abs.replace("\\", "/")
    
    width, height = 1920, 1080
    temp_dir = os.path.abspath("temp_video_dir")
    os.makedirs(temp_dir, exist_ok=True)

    print(f"Recording native Playwright WebM video to {output_video_path}...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": width, "height": height},
            record_video_dir=temp_dir,
            record_video_size={"width": width, "height": height}
        )
        page = await context.new_page()
        await page.goto(html_file_path)
        
        # Record 4 full animation cycles (16 seconds total)
        await page.wait_for_timeout(17000)

        video_path = await page.video.path()
        await context.close()
        await browser.close()

        # Copy recorded video to output path
        shutil.copy(video_path, output_video_path)
        shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"[SUCCESS] High quality WebM video recorded and saved to {output_video_path}")

if __name__ == "__main__":
    asyncio.run(record_playwright_video())
