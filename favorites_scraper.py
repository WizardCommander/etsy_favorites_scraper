import pandas as pd
import time
import random
import os
import subprocess
import tempfile
import socket
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

# === CONFIG ===
CSV_PATH = "etsy_buyer_profile_urls.csv"
OUTPUT_CSV = "favorites_master.csv"
CLOTHING_KEYWORDS = ["shirt", "tee", "hat", "cap", "hoodie", "sweater", "beanie"]
MAX_PROFILES_PER_RUN = 10  # Adjust as needed

LOCATIONS = [
    ("us", "atl"), ("us", "bos"), ("us", "chi"), ("us", "dal"), ("us", "den"),
    ("us", "hou"), ("us", "mkc"), ("us", "lax")
]

def rotate_mullvad():
    country, city = random.choice(LOCATIONS)
    print(f"Rotating Mullvad IP to: {city.upper()}, {country.upper()}")
    subprocess.run(["mullvad", "relay", "set", "location", country, city])
    subprocess.run(["mullvad", "connect"])
    time.sleep(6)

    for _ in range(5):
        try:
            socket.gethostbyname("www.google.com")
            print("Internet OK")
            return True
        except socket.gaierror:
            print("DNS failed, retrying...")
            time.sleep(3)
    print("Internet not working after Mullvad switch. Exiting.")
    return False

def scrape_user(row):
    user_id = row["Profile URL"].split("/people/")[1].split("/")[0]
    profile_url = f"https://www.etsy.com/people/{user_id}"
    print(f"👤 Scraping: {user_id}")
    print(f"🔗 URL: {profile_url}")

    temp_profile = tempfile.mkdtemp()
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={temp_profile}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--no-first-run")
    options.add_argument("--start-maximized")

    print("Launching UC Chrome...")
    driver = uc.Chrome(options=options, headless=False)

    try:
        print("Visiting:", profile_url)
        driver.get(profile_url)
        time.sleep(random.uniform(4.0, 6.0))

        if "Nothing to see here yet" in driver.page_source:
            print("No favorites found. Skipping.")
            return []

        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script(f"window.scrollBy(0, {random.randint(300, 800)});")
            time.sleep(random.uniform(1.5, 3.0))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2.0, 4.0))
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        soup = BeautifulSoup(driver.page_source, "html.parser")
        cards = soup.find_all("div", class_="favorite-listing-card--desktop")
        extracted = []

        for card in cards:
            try:
                a_tag = card.find("a", class_="listing-link")
                if not a_tag:
                    continue
                listing_url = a_tag["href"].split("?")[0]
                title = a_tag.get("title", "").strip().lower()
                img_tag = card.find("img", class_="width-full height-full display-block position-absolute")
                image_url = img_tag["src"] if img_tag else None
                is_clothing = any(kw in title for kw in CLOTHING_KEYWORDS)

                extracted.append({
                    "user_id": user_id,
                    "listing_url": listing_url,
                    "title": title,
                    "image_url": image_url,
                    "is_clothing": is_clothing
                })
            except Exception as e:
                print(f"[WARN] Skipped listing: {e}")

        return extracted

    finally:
        driver.quit()

# === MAIN LOOP ===
df = pd.read_csv(CSV_PATH)
if "scraped" not in df.columns:
    df["scraped"] = False

unscraped_df = df[df["scraped"] == False]
if unscraped_df.empty:
    print("All profiles have been scraped.")
    exit()

for i, (_, row) in enumerate(unscraped_df.iterrows()):
    if i >= MAX_PROFILES_PER_RUN:
        print("Max profiles hit for this run.")
        break

    rotate_success = rotate_mullvad()
    if not rotate_success:
        break

    listings = scrape_user(row)

    if listings:
        df_out = pd.DataFrame(listings)
        if os.path.exists(OUTPUT_CSV):
            df_out.to_csv(OUTPUT_CSV, mode='a', header=False, index=False)
        else:
            df_out.to_csv(OUTPUT_CSV, index=False)
        print(f"Saved {len(df_out)} listings.")
    else:
        print("No listings scraped.")

    df.loc[df["Profile URL"] == row["Profile URL"], "scraped"] = True
    df.to_csv(CSV_PATH, index=False)

    print("Finished profile\n")
    time.sleep(random.uniform(5, 10))  # delay between runs
