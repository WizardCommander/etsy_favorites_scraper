import undetected_chromedriver as uc
import time

options = uc.ChromeOptions()
options.add_argument("--no-first-run")
options.add_argument("--no-default-browser-check")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--user-data-dir=C:/Users/Gamer/AppData/Local/Google/Chrome/User Data")
options.add_argument("--profile-directory=ScraperProfile")  # clean one

print("📦 Launching UC Chrome...")
driver = uc.Chrome(options=options, headless=False)
print("🚀 UC Chrome launched")

try:
    print("🌍 Navigating to example.com...")
    driver.get("https://example.com")
    print("✅ Navigation success")
except Exception as e:
    print(f"❌ Navigation failed: {e}")

time.sleep(10)
driver.quit()
