import os
import re
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


URL = "https://coinmarketcap.com/"
FILE_NAME = r"C:/crypto mini/crypto_selenium_log.csv" 
TOP_N = 20 



def clean_numeric_text(text):
    
    if not isinstance(text, str):
        return None
    
    text = text.replace('$', '').replace(',', '').replace('%', '')
    
    
    multiplier = 1
    if 'T' in text:
        multiplier = 1_000_000_000_000
        text = text.replace('T', '')
    elif 'B' in text:
        multiplier = 1_000_000_000
        text = text.replace('B', '')
    elif 'M' in text:
        multiplier = 1_000_000
        text = text.replace('M', '')
        
    try:
        return float(text) * multiplier
    except (ValueError, TypeError):
        return None

def get_top_cryptos(headless=True):
    
    print("🚀 Initializing browser...")
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("window-size=1920,1080") # Helps in headless mode

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        driver.get(URL)
        print("⏳ Waiting for page data to load...")
        wait = WebDriverWait(driver, 20)
        
        
        table_selector = "div.sc-14cb0828-0.dGSaKH.cmc-table-responsive > div > table.cmc-table"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, table_selector)))
        
        
        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, f"{table_selector} tbody tr")) >= TOP_N)
        print("✅ Page loaded successfully.")

        rows = driver.find_elements(By.CSS_SELECTOR, f"{table_selector} tbody tr")[:TOP_N]
        crypto_data = []
        print(f"Parsing data for top {TOP_N} coins...")

        for row in rows:
            cols = row.find_elements(By.TAG_NAME, 'td')
            if len(cols) < 8: 
                continue

            try:
                
                name = cols[2].find_element(By.CSS_SELECTOR, 'p.coin-item-symbol').text
                price = clean_numeric_text(cols[3].text)
                change_1h = clean_numeric_text(cols[4].text)
                change_24h = clean_numeric_text(cols[5].text)
                change_7d = clean_numeric_text(cols[6].text)
                market_cap = clean_numeric_text(cols[7].text)

                crypto_data.append({
                    "Name": name,
                    "PriceUSD": price,
                    "Change1h": change_1h,
                    "Change24h": change_24h,
                    "Change7d": change_7d,
                    "MarketCapUSD": market_cap,
                })
            except Exception:
                
                continue
        
        return pd.DataFrame(crypto_data)

    except Exception as e:
        print(f"❌ An error occurred during scraping: {e}")
        driver.save_screenshot("error_screenshot.png") 
        print("📸 Screenshot saved as error_screenshot.png")
        return pd.DataFrame()
    finally:
        print("Browser closing.")
        driver.quit()

def save_to_csv(df, filename):
    """REVISED: Efficiently appends data to a CSV file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    df["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
   
    cols = df.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    df = df[cols]
    
   
    write_header = not os.path.exists(filename)
    df.to_csv(filename, mode='a', header=write_header, index=False)
    print(f"✅ Data for {len(df)} coins appended successfully to {filename}")

def analyze_and_print_summary(df):
    """Prints a simple analysis of the scraped data."""
    if "Change24h" not in df.columns:
        return
        
    
    top_gainer = df.loc[df["Change24h"].idxmax()]
    top_loser = df.loc[df["Change24h"].idxmin()]
    
    print("\n--- Quick Summary ---")
    print(f"📈 Top Gainer (24h): {top_gainer['Name']} ({top_gainer['Change24h']:.2f}%)")
    print(f"📉 Top Loser (24h):   {top_loser['Name']} ({top_loser['Change24h']:.2f}%)")
    print("---------------------\n")

def main():
    """Main function to run the crypto scraper."""
    data = get_top_cryptos(headless=True) 

    if data.empty:
        print("⚠ Scraping finished with no data. Exiting.")
    else:
        print("\n--- Scraped Data ---")
        print(data.head()) 
        print("--------------------\n")
        
        save_to_csv(data, FILE_NAME)
        analyze_and_print_summary(data)

if __name__ == "_main_":
    main()