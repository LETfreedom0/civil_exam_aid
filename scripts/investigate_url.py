import requests
from bs4 import BeautifulSoup
import os

URL = "http://www.impta.com.cn/dangzhengqungwy/%E5%86%85%E8%92%99%E5%8F%A4%E8%87%AA%E6%B2%BB%E5%8C%BA%E5%85%9A%E6%94%BF%E7%BE%A4%E6%9C%BA%E5%85%B3%EF%BC%88%E5%8F%82%E5%85%AC%E5%8D%95%E4%BD%8D%EF%BC%892025%E5%B9%B4%E5%BA%A6%E8%80%83%E8%AF%95%E5%BD%95%E7%94%A8%E5%85%AC%E5%8A%A1%E5%91%98%E8%81%8C%E4%BD%8D%E8%A1%A8(%E6%99%AE%E9%80%9A%E5%B2%97%E4%BD%8D).htm"

def fetch_content(url):
    print(f"Fetching {url}...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        # response.encoding = 'utf-8' # Assume UTF-8, might need adjustment
        response.encoding = response.apparent_encoding # Automatically detect encoding (fixes mojibake)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching: {e}")
        return None

def analyze_html(html):
    if not html:
        return
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # 1. Check for tables
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables.")
    
    if tables:
        table = tables[0]
        rows = table.find_all('tr')
        print(f"Table has {len(rows)} rows.")
        
        # Print rows 5-15 to identify headers
        print("\n--- Table Preview (Rows 5-15) ---")
        for i, row in enumerate(rows[5:15]):
            cols = row.find_all(['th', 'td'])
            col_texts = [ele.get_text(strip=True) for ele in cols]
            print(f"Row {i+5}: {col_texts}")
        print("------------------------------------\n")
    
    # 2. Check for attachments (links ending with xls, xlsx, doc, docx, pdf)
    links = soup.find_all('a')
    attachments = []
    for link in links:
        href = link.get('href')
        if href and (href.endswith('.xls') or href.endswith('.xlsx') or href.endswith('.pdf')):
            attachments.append(href)
            
    print(f"Found {len(attachments)} potential attachments:")
    for att in attachments:
        print(f" - {att}")

    # 3. Print first few lines of text to see structure
    print("\nPage Text Preview:")
    print(soup.get_text()[:500].strip())

if __name__ == "__main__":
    html = fetch_content(URL)
    analyze_html(html)
