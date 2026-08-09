import asyncio
import os
import cv2
import numpy as np
from playwright.async_api import async_playwright

async def record_demo_video():
    output_video_path = "docs/assets/schemap_demo_showcase.mp4"
    os.makedirs("docs/assets", exist_ok=True)
    
    html_file_path = "file:///" + os.path.abspath("demo_presentation.html").replace("\\", "/")
    
    fps = 30
    duration_seconds = 16  # 4 steps x 4 seconds each
    total_frames = fps * duration_seconds
    width, height = 1920, 1080
    
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    print(f"Recording Schemap demo video to {output_video_path}...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": width, "height": height})
        await page.goto(html_file_path)
        await page.wait_for_timeout(1000)

        for frame_idx in range(total_frames):
            screenshot_bytes = await page.screenshot(type="png")
            # Convert bytes to numpy array
            nparr = np.frombuffer(screenshot_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR) # BGR
            out.write(img)
            
            if (frame_idx + 1) % 30 == 0:
                print(f"Captured {(frame_idx + 1) // 30} / {duration_seconds} seconds...")
            
            await asyncio.sleep(1 / fps)

        await browser.close()
        out.release()

    print(f"[SUCCESS] Video recorded and saved to {output_video_path}")

if __name__ == "__main__":
    asyncio.run(record_demo_video())
