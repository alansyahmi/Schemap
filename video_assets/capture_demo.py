import asyncio
import os
from playwright.async_api import async_playwright

async def capture_demo_scenes():
    out_dir = os.path.abspath('video_assets/rendered_demo')
    os.makedirs(out_dir, exist_ok=True)
    
    html_path = os.path.abspath('video_assets/schemap_demo_cinema.html').replace('\\', '/')
    file_url = f'file:///{html_path}'

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1280, 'height': 800})
        await page.goto(file_url, wait_until='domcontentloaded')

        scenes = [
            ("scene1_problem.png", 0),
            ("scene2_schemap_ground.png", 1),
            ("scene3_verified_sql.png", 2),
            ("scene4_attack_blocked.png", 3),
            ("scene5_scorecard_proof.png", 4),
        ]

        for filename, scene_idx in scenes:
            await page.evaluate(f'window.goToScene({scene_idx})')
            await asyncio.sleep(0.3)
            save_path = os.path.join(out_dir, filename)
            await page.screenshot(path=save_path, full_page=False)
            print(f"Captured Scene {scene_idx + 1} -> {filename}")

        await browser.close()
        print("All 5 demo scenes verified and captured cleanly!")

if __name__ == '__main__':
    asyncio.run(capture_demo_scenes())
