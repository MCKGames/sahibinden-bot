import requests
from bs4 import BeautifulSoup
import json
import os
import time

# AYARLAR (GitHub Secrets'tan çekilecek)
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# Motor kategorisi - Yeni ilanlar en üstte
SAHIBINDEN_URL = "https://www.sahibinden.com/hobi-oyuncak-ticari-oyun-urunleri?sorting=date_desc"

# İstersen daha özel filtre ekle, örnek:
# SAHIBINDEN_URL = "https://www.sahibinden.com/motosiklet/istanbul?price_max=150000&a28=12345&sorting=date_desc"

SEEN_IDS_FILE = "seen_ads.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": False}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Telegram hatası: {e}")

def load_seen_ids():
    if os.path.exists(SEEN_IDS_FILE):
        with open(SEEN_IDS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen_ids(seen_ids):
    with open(SEEN_IDS_FILE, "w") as f:
        json.dump(list(seen_ids), f)

def scrape_new_ads():
    seen_ids = load_seen_ids()
    new_ads = []

    try:
        response = requests.get(SAHIBINDEN_URL, headers=HEADERS, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        rows = soup.find_all("tr", {"class": "searchResultsItem"})

        for row in rows:
            ad_id = row.get("data-id")
            if not ad_id or ad_id in seen_ids:
                continue

            link_tag = row.find("a", class_="classifiedTitle")
            if not link_tag:
                continue
            link = "https://www.sahibinden.com" + link_tag["href"]
            title = link_tag.get_text(strip=True)

            price_tag = row.find("td", {"class": "searchResultsPriceValue"})
            price = price_tag.get_text(strip=True) if price_tag else "Fiyat belirtilmemiş"

            location_tag = row.find("td", {"class": "searchResultsLocationValue"})
            location_date = location_tag.get_text(strip=True) if location_tag else ""

            message = f"🏍️ Yeni Motor İlanı!\n\n{title}\n💰 {price}\n📍 {location_date}\n🔗 {link}"

            new_ads.append((ad_id, message))

        for ad_id, _ in new_ads:
            seen_ids.add(ad_id)
        save_seen_ids(seen_ids)

        return new_ads

    except Exception as e:
        print(f"Hata: {e}")
        send_telegram_message(f"🚨 Motor botu hatası: {e}")
        return []

new_ads = scrape_new_ads()
for _, message in reversed(new_ads):
    send_telegram_message(message)
    time.sleep(2)

if new_ads:
    print(f"{len(new_ads)} yeni motor ilanı bildirildi.")
else:
    print("Yeni ilan yok.")
