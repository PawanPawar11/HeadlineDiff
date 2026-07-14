import sys
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import datetime
import time

def get_wayback_captures(url, from_date=None, to_date=None, limit=100):
    """
    Fetch historical snapshots of a URL from the Wayback Machine CDX API.
    Retries on timeout or temporary failure.
    """
    cdx_url = "https://web.archive.org/cdx/search/cdx"
    params = {
        "url": url,
        "output": "json",
        "fl": "timestamp,original,statuscode,mimetype",
        "filter": "statuscode:200",
        "collapse": "digest",  # collapse identical captures
        "limit": limit
    }
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date

    max_retries = 3
    timeout = 30
    
    for attempt in range(max_retries):
        try:
            print(f"Querying Wayback CDX API (Attempt {attempt+1}/{max_retries})...")
            response = requests.get(cdx_url, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            if not data or len(data) <= 1:
                return []
            
            # The first row is the header list
            headers = data[0]
            rows = data[1:]
            
            captures = []
            for row in rows:
                capture = dict(zip(headers, row))
                ts_str = capture["timestamp"]
                capture["datetime"] = datetime.datetime.strptime(ts_str, "%Y%m%d%H%M%S")
                captures.append(capture)
                
            return captures
        except requests.exceptions.Timeout as te:
            print(f"Timeout querying CDX API on attempt {attempt+1}: {te}")
            if attempt < max_retries - 1:
                time.sleep(3)
                timeout += 15  # increase timeout on retry
        except Exception as e:
            print(f"Error querying CDX API on attempt {attempt+1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(3)
            else:
                break
    return []

def fetch_snapshot_html(timestamp, url):
    """
    Fetch the raw HTML of a URL at a specific timestamp.
    Uses the 'id_' suffix to get raw content without the Wayback toolbar.
    """
    raw_url = f"https://web.archive.org/web/{timestamp}id_/{url}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(raw_url, headers=headers, timeout=20)
        # Handle transient HTTP issues (like 503, 429) gracefully with a retry
        if response.status_code in [429, 503]:
            time.sleep(2)
            response = requests.get(raw_url, headers=headers, timeout=20)
            
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching snapshot {timestamp}: {e}")
        return None

def extract_headline(html, url):
    """
    Extract the headline from the HTML using site-specific rules or generic selectors.
    """
    if not html:
        return None
        
    soup = BeautifulSoup(html, "lxml")
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    
    headline = None
    
    # 1. Try meta tags first (often contains the clean editorial headline)
    meta_tags = [
        ("property", "og:title"),
        ("name", "twitter:title"),
        ("property", "twitter:title"),
        ("name", "title")
    ]
    for attr, val in meta_tags:
        tag = soup.find("meta", attrs={attr: val})
        if tag and tag.get("content"):
            headline = tag["content"].strip()
            break
            
    # 2. Site-specific rules for fallback/h1 parsing if needed
    if not headline:
        if "nytimes.com" in domain:
            h1 = soup.find("h1", {"itemprop": "headline"}) or soup.find("h1")
            if h1:
                headline = h1.get_text().strip()
        elif "cnn.com" in domain:
            h1 = soup.find("h1", {"class": "pg-headline"}) or soup.find("h1", {"class": "headline"}) or soup.find("h1")
            if h1:
                headline = h1.get_text().strip()
        elif "bbc" in domain:
            h1 = soup.find("h1", {"id": "main-heading"}) or soup.find("h1")
            if h1:
                headline = h1.get_text().strip()
        else:
            h1 = soup.find("h1")
            if h1:
                headline = h1.get_text().strip()
                
    # 3. Last fallback: <title> tag
    if not headline:
        title_tag = soup.find("title")
        if title_tag:
            headline = title_tag.get_text().strip()
            
    # Clean up common suffixes
    if headline:
        suffixes = [" - The New York Times", " - CNN", " - BBC News", " - BBC", " | Fox News"]
        for suffix in suffixes:
            if headline.endswith(suffix):
                headline = headline[:-len(suffix)].strip()
                
    return headline

def track_headline_changes(url, sample_limit=15):
    """
    Main function to track headline changes for a single URL over time.
    """
    print(f"Tracking headline changes for: {url}")
    captures = get_wayback_captures(url)
    if not captures:
        print("No successful captures found in Wayback Machine.")
        return []
        
    print(f"Found {len(captures)} historical snapshots.")
    
    # Sample captures to avoid fetching hundreds of pages
    # We want to keep:
    # 1. The first capture (original published headline)
    # 2. The last capture (current headline)
    # 3. Spaced out captures in between
    if len(captures) > sample_limit:
        sampled_indices = sorted(list(set(
            [0] + 
            [int(i * (len(captures) - 1) / (sample_limit - 1)) for i in range(1, sample_limit - 1)] + 
            [len(captures) - 1]
        )))
        sampled_captures = [captures[i] for i in sampled_indices]
    else:
        sampled_captures = captures
        
    print(f"Sampled {len(sampled_captures)} snapshots for analysis...")
    
    history = []
    last_headline = None
    
    for i, cap in enumerate(sampled_captures):
        ts = cap["timestamp"]
        dt = cap["datetime"]
        print(f"[{i+1}/{len(sampled_captures)}] Fetching snapshot from {dt.strftime('%Y-%m-%d %H:%M:%S')}...", end="", flush=True)
        
        html = fetch_snapshot_html(ts, url)
        if not html:
            print(" Failed.")
            continue
            
        headline = extract_headline(html, url)
        if not headline:
            print(" No headline found.")
            continue
            
        print(" Success.")
        
        # Only record if headline changed
        if headline != last_headline:
            history.append({
                "timestamp": ts,
                "datetime": dt.isoformat(),
                "headline": headline,
                "changed": last_headline is not None
            })
            last_headline = headline
            
        # Rate limit friendly sleep
        time.sleep(1.5)
        
    return history

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python wayback_scraper.py <url>")
        sys.exit(1)
        
    target_url = sys.argv[1]
    history = track_headline_changes(target_url)
    
    print("\n--- Headline History ---")
    if not history:
        print("No headline changes detected (or unable to fetch snapshots).")
    else:
        for idx, entry in enumerate(history):
            prefix = "[NEW]" if entry["changed"] else "[ORIGINAL]"
            print(f"{entry['datetime']} - {prefix}: {entry['headline']}")
