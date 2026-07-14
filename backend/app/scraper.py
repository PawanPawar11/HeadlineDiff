import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import datetime
import time
import re

def get_wayback_captures(url, from_date=None, to_date=None, limit=100):
    """
    Fetch historical snapshots of a URL from the Wayback Machine CDX API.
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
            response = requests.get(cdx_url, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            if not data or len(data) <= 1:
                return []
            
            headers = data[0]
            rows = data[1:]
            
            captures = []
            for row in rows:
                capture = dict(zip(headers, row))
                ts_str = capture["timestamp"]
                capture["datetime"] = datetime.datetime.strptime(ts_str, "%Y%m%d%H%M%S")
                captures.append(capture)
                
            return captures
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(3)
                timeout += 15
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(3)
            else:
                break
    return []

def fetch_snapshot_html(timestamp, url):
    """
    Fetch raw HTML of a URL at a specific timestamp from the Wayback Machine.
    """
    raw_url = f"https://web.archive.org/web/{timestamp}id_/{url}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(raw_url, headers=headers, timeout=20)
        if response.status_code in [429, 503]:
            time.sleep(2)
            response = requests.get(raw_url, headers=headers, timeout=20)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching snapshot {timestamp} for {url}: {e}")
        return None

def extract_headline(html, url):
    """
    Extract article headline from HTML using site-specific or generic selectors.
    """
    if not html:
        return None
        
    soup = BeautifulSoup(html, "lxml")
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    
    headline = None
    
    # 1. Try meta tags first
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
            
    # 2. Site-specific fallbacks
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
                
    if not headline:
        title_tag = soup.find("title")
        if title_tag:
            headline = title_tag.get_text().strip()
            
    # Clean up standard suffixes
    if headline:
        suffixes = [" - The New York Times", " - CNN", " - BBC News", " - BBC", " | Fox News"]
        for suffix in suffixes:
            if headline.endswith(suffix):
                headline = headline[:-len(suffix)].strip()
                
    return headline

def track_url_history(url, sample_limit=15):
    """
    Track headline history of a single URL.
    """
    captures = get_wayback_captures(url)
    if not captures:
        return []
        
    if len(captures) > sample_limit:
        sampled_indices = sorted(list(set(
            [0] + 
            [int(i * (len(captures) - 1) / (sample_limit - 1)) for i in range(1, sample_limit - 1)] + 
            [len(captures) - 1]
        )))
        sampled_captures = [captures[i] for i in sampled_indices]
    else:
        sampled_captures = captures
        
    history = []
    last_headline = None
    
    for cap in sampled_captures:
        ts = cap["timestamp"]
        dt = cap["datetime"]
        
        html = fetch_snapshot_html(ts, url)
        if not html:
            continue
            
        headline = extract_headline(html, url)
        if not headline:
            continue
            
        if headline != last_headline:
            history.append({
                "timestamp": ts,
                "datetime": dt.isoformat(),
                "headline": headline,
                "changed": last_headline is not None
            })
            last_headline = headline
            
        time.sleep(1.0)
        
    return history

def get_section_urls(domain):
    """
    Return standard section URLs for major domains.
    """
    sections = {
        "cnn.com": [
            "https://www.cnn.com/politics",
            "https://www.cnn.com/world",
            "https://www.cnn.com/us"
        ],
        "foxnews.com": [
            "https://www.foxnews.com/politics",
            "https://www.foxnews.com/world",
            "https://www.foxnews.com/us"
        ],
        "nytimes.com": [
            "https://www.nytimes.com/section/politics",
            "https://www.nytimes.com/section/world",
            "https://www.nytimes.com/section/us"
        ],
        "bbc.com": [
            "https://www.bbc.com/news/world",
            "https://www.bbc.com/news/politics"
        ]
    }
    
    # Normalize domain to match keys
    for key in sections:
        if key in domain:
            return sections[key]
            
    # Default fallback
    return [f"https://{domain}"]

def scrape_topic_headlines_from_sections(domain, date_str, query):
    """
    Search historical section captures of a domain near a date for a specific topic query.
    date_str format: YYYYMMDD
    """
    section_urls = get_section_urls(domain)
    found_headlines = []
    seen_urls = set()
    
    # We will search matching section pages captured near the target date
    # CDX params to find closest capture
    cdx_url = "https://web.archive.org/cdx/search/cdx"
    
    for section_url in section_urls:
        params = {
            "url": section_url,
            "output": "json",
            "fl": "timestamp,original",
            "limit": 1,
            # query captures around the target date
            "from": date_str,
            "to": date_str
        }
        
        # If no captures directly on that date, widen the search range to +/- 2 days
        dt = datetime.datetime.strptime(date_str, "%Y%m%d")
        from_dt = (dt - datetime.timedelta(days=2)).strftime("%Y%m%d")
        to_dt = (dt + datetime.timedelta(days=2)).strftime("%Y%m%d")
        params["from"] = from_dt
        params["to"] = to_dt
        
        try:
            response = requests.get(cdx_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            if not data or len(data) <= 1:
                continue
            
            # Use the closest snapshot
            ts, orig_url = data[1][0], data[1][1]
            print(f"Fetching section snapshot for {section_url} at {ts}...")
            
            html = fetch_snapshot_html(ts, orig_url)
            if not html:
                continue
                
            soup = BeautifulSoup(html, "lxml")
            links = soup.find_all("a", href=True)
            
            query_terms = [t.lower() for t in query.split()]
            
            for link in links:
                href = link["href"]
                text = link.get_text().strip()
                
                # Filter out short labels like "Read More", "Politics", etc.
                if len(text) < 15:
                    continue
                    
                # Clean up text whitespace
                text = re.sub(r'\s+', ' ', text)
                
                # Check if it matches query terms (fuzzy containment)
                matches_query = all(term in text.lower() or term in href.lower() for term in query_terms)
                
                if matches_query:
                    # Clean up URL (sometimes has wayback prefix, so strip it)
                    clean_href = href
                    if "/web/" in href:
                        # e.g., /web/20220908173259/http://cnn.com/... -> http://cnn.com/...
                        match = re.search(r'/web/\d+/(https?://.*)$', href)
                        if match:
                            clean_href = match.group(1)
                        else:
                            # Relative path after wayback prefix
                            match_rel = re.search(r'/web/\d+/(.*)$', href)
                            if match_rel:
                                clean_href = urljoin(f"https://{domain}", match_rel.group(1))
                    else:
                        clean_href = urljoin(f"https://{domain}", href)
                        
                    # Normalize URL to avoid duplicates
                    normalized_url = clean_href.split("?")[0].rstrip("/")
                    
                    if normalized_url not in seen_urls:
                        seen_urls.add(normalized_url)
                        found_headlines.append({
                            "headline": text,
                            "url": clean_href,
                            "section": section_url.split("/")[-1]
                        })
                        
            time.sleep(1.0) # rate-limiting friendly
        except Exception as e:
            print(f"Error scraping section {section_url} for date {date_str}: {e}")
            
    return found_headlines
