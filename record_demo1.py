import asyncio
import os
import shutil
from playwright.async_api import async_playwright

async def record_demo1_video():
    output_video_path = "docs/assets/schemap_demo1_hallucinated_sql.webm"
    os.makedirs("docs/assets", exist_ok=True)
    
    html_file_path = "file:///" + os.path.abspath("demo1_presentation.html").replace("\\", "/")
    
    width, height = 1920, 1080
    temp_dir = os.path.abspath("temp_video_dir_demo1")
    os.makedirs(temp_dir, exist_ok=True)

    print(f"Recording Demo 1 video to {output_video_path}...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": width, "height": height},
            record_video_dir=temp_dir,
            record_video_size={"width": width, "height": height}
        )
        page = await context.new_page()
        await page.goto(html_file_path)
        
        # Wait for full 4 steps + final screen callout (~18.5 seconds)
        await page.wait_for_timeout(19000)

        video_path = await page.video.path()
        await context.close()
        await browser.close()

        # Copy recorded video to output path
        shutil.copy(video_path, output_video_path)
        shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"[SUCCESS] Demo 1 WebM video recorded successfully: {output_video_path}")

if __name__ == "__main__":
    asyncio.run(record_demo1_video())
