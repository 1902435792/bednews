import urllib.request
import re
import random
import sys
import gzip
import io

sys.stdout.reconfigure(encoding='utf-8')

PC_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
]

def get_headers(referer=""):
    return {
        'User-Agent': random.choice(PC_AGENTS),
        'Referer': referer,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Cookie': 'SUB=_2AkMVWnfrf8NxqwJRmP4SzWvhaY12zAHEieKkgmpwJRMxHRl-yT9kqnErtRB6PToS8q_1d4gX-X7-c1d9f8s_;'
    }

def fetch_content(url, referer=""):
    req = urllib.request.Request(url, headers=get_headers(referer))
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            if response.info().get('Content-Encoding') == 'gzip':
                f = io.BytesIO(data)
                data = gzip.GzipFile(fileobj=f).read()
            return data.decode('utf-8')
    except Exception as e:
        return None

def fetch_baidu_hot():
    print(f"\n=== 百度热搜 (全网聚合) ===")
    url = "https://top.baidu.com/board?tab=realtime"
    html = fetch_content(url)
    if html:
        matches = re.findall(r'<div class="c-single-text-ellipsis">(.*?)</div>', html)
        seen = set()
        count = 0
        for title in matches:
            title = title.strip()
            if title and title not in seen and len(title) > 2:
                count += 1
                print(f"{count}. {title}")
                seen.add(title)
                if count >= 15: break

def fetch_social_news():
    print(f"\n=== 民生新闻 (非热搜底池) ===")
    # 尝试抓取百度新闻-社会频道的RSS/HTML
    # url = "http://news.baidu.com/n?cmd=4&class=civilnews&tn=rss" (RSS often blocked or encoding issues)
    # Using mobile optimized page for stability:
    url = "https://news.baidu.com/widget?id=CivilNews" 
    html = fetch_content(url)
    
    if html:
        # Match news titles in the widget
        # Pattern usually: <a href="..." ...>Title</a>
        matches = re.findall(r'<a href="[^"]+"[^>]*>([^<]+)</a>', html)
        count = 0
        seen = set()
        for title in matches:
            title = title.strip()
            # Filter out generic nav links
            if len(title) > 6 and "百度" not in title and title not in seen:
                count += 1
                print(f"{count}. [社会] {title}")
                seen.add(title)
                if count >= 10: break

def fetch_weibo():
    print(f"\n=== 微博热搜 (争议/话题) ===")
    # Scrape s.weibo.com HTML directly
    url = "https://s.weibo.com/top/summary"
    html = fetch_content(url, "https://weibo.com/")
    if html:
        # Match <a href="/weibo?q=..." target="_blank">Title</a> inside td-02
        matches = re.findall(r'<a href="/weibo\?q=[^"]+" target="_blank">([^<]+)</a>', html)
        count = 0
        for title in matches:
            if "剧" not in title and count < 15: 
                count += 1
                print(f"{count}. {title}")

if __name__ == "__main__":
    print("全网舆情扫描中 (Baidu Hot, Social News, Weibo)...")
    fetch_baidu_hot()
    fetch_social_news()
    fetch_weibo()
    print("\n扫描完成。")
