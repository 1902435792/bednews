#!/usr/bin/env python3
"""
智能热点分析系统 v3.0

整合 40+ 平台热点抓取 + 智能分析：
1. 语义分类 - 识别议题类型（政策/民生/经济/争议）
2. 热度合并 - 相似话题聚合
3. 来源权重 - 深度报道优先
4. 历史对比 - 标记已分析过的议题

使用方法:
    python multi_platform_hot.py --depth       # 深度报道（推荐）
    python multi_platform_hot.py --all         # 全量抓取
    python multi_platform_hot.py --json        # JSON 输出
    python multi_platform_hot.py --list-sources # 列出平台
"""

import urllib.request
import re
import random
import sys
import gzip
import io
import json
import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

# ==================== 路径配置 ====================
SCRIPT_DIR = Path(__file__).parent
# 归档目录（用于历史对比）
ARCHIVE_DIR = Path("d:/a1114/aaa111/bedtime_news_archive")

# ==================== 通用配置 ====================

PC_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
]

# ==================== 来源权重配置 ====================

# T1: 深度报道（最高权重）
# T2: 专业财经/科技媒体
# T3: 综合热搜
# T4: 娱乐/短视频

SOURCE_TIERS = {
    # T1 深度报道
    "caixin": 1, "caixin_weekly": 1, "thepaper": 1,
    # T2 专业媒体
    "wallstreetcn-hot": 2, "cls-telegraph": 2, "36kr-quick": 2, "36kr-hot": 2,
    "huxiu": 2, "ithome": 2, "gelonghui": 2, "jin10": 2,
    "ifeng": 2, "cankaoxiaoxi": 2, "zaobao": 2,
    "hackernews": 2, "github-trending": 2,
    # T3 综合热搜
    "baidu": 3, "weibo": 3, "zhihu-hot": 3, "toutiao": 3,
    "bilibili-hot": 3, "douban": 3, "v2ex": 3, "hupu": 3,
    "xueqiu": 3, "juejin": 3, "sspai": 3, "producthunt": 3,
    # T4 短视频/社区
    "douyin": 4, "kuaishou": 4, "tieba": 4, "iqiyi": 4, "qqvideo": 4,
    "coolapk": 4, "smzdm": 4, "steam": 4, "chongbuluo": 4, "nowcoder": 4,
}

# ==================== 语义分类配置 ====================

TOPIC_TYPES = {
    "政策制度": {
        "核心词": ["政策", "改革", "制度", "法规", "条例", "规定", "新规", "通知", "意见"],
        "强化词": ["发布", "实施", "修订", "出台", "印发", "公布", "落地"],
    },
    "民生痛点": {
        "核心词": ["烂尾", "欠薪", "维权", "投诉", "拖欠", "讨薪", "上访", "信访"],
        "场景词": ["业主", "农民工", "患者", "学生", "教师", "退休", "养老", "医保"],
    },
    "经济金融": {
        "核心词": ["股市", "房价", "利率", "GDP", "通胀", "降息", "加息", "货币"],
        "数据词": ["增长", "下跌", "上涨", "%", "亿", "万亿", "同比", "环比"],
    },
    "社会争议": {
        "核心词": ["争议", "质疑", "回应", "曝光", "调查", "通报", "处罚", "约谈"],
        "情绪词": ["愤怒", "不满", "抗议", "热议", "刷屏", "炸锅"],
    },
    "科技产业": {
        "核心词": ["AI", "人工智能", "芯片", "半导体", "新能源", "电动车", "5G", "算力"],
        "公司词": ["华为", "腾讯", "阿里", "字节", "苹果", "特斯拉", "英伟达", "OpenAI"],
    },
}

# ==================== NewsNow 平台配置 ====================

NEWSNOW_SOURCES = {
    # 热搜
    "baidu": {"name": "百度热搜", "category": "热搜", "priority": 1},
    "weibo": {"name": "微博热搜", "category": "热搜", "priority": 1},
    "zhihu-hot": {"name": "知乎热榜", "category": "热搜", "priority": 1},
    "douyin": {"name": "抖音热榜", "category": "热搜", "priority": 1},
    "toutiao": {"name": "今日头条", "category": "热搜", "priority": 1},
    "tieba": {"name": "百度贴吧", "category": "热搜", "priority": 2},
    "kuaishou": {"name": "快手热榜", "category": "热搜", "priority": 2},
    # 财经
    "wallstreetcn-hot": {"name": "华尔街见闻", "category": "财经", "priority": 1},
    "cls-telegraph": {"name": "财联社电报", "category": "财经", "priority": 1},
    "xueqiu": {"name": "雪球热帖", "category": "财经", "priority": 2},
    "gelonghui": {"name": "格隆汇", "category": "财经", "priority": 2},
    "jin10": {"name": "金十数据", "category": "财经", "priority": 2},
    # 科技
    "36kr-quick": {"name": "36氪快讯", "category": "科技", "priority": 1},
    "36kr-hot": {"name": "36氪热榜", "category": "科技", "priority": 1},
    "ithome": {"name": "IT之家", "category": "科技", "priority": 1},
    "huxiu": {"name": "虎嗅", "category": "科技", "priority": 1},
    "sspai": {"name": "少数派", "category": "科技", "priority": 2},
    "juejin": {"name": "掘金热榜", "category": "科技", "priority": 2},
    "v2ex": {"name": "V2EX", "category": "科技", "priority": 2},
    # 视频
    "bilibili-hot": {"name": "B站热门", "category": "视频", "priority": 1},
    "iqiyi": {"name": "爱奇艺热播", "category": "视频", "priority": 2},
    "qqvideo": {"name": "腾讯视频", "category": "视频", "priority": 2},
    # 新闻
    "thepaper": {"name": "澎湃新闻", "category": "新闻", "priority": 1},
    "ifeng": {"name": "凤凰新闻", "category": "新闻", "priority": 2},
    "cankaoxiaoxi": {"name": "参考消息", "category": "新闻", "priority": 2},
    "zaobao": {"name": "联合早报", "category": "新闻", "priority": 2},
    # 国际
    "github-trending": {"name": "GitHub趋势", "category": "国际", "priority": 1},
    "hackernews": {"name": "Hacker News", "category": "国际", "priority": 1},
    "producthunt": {"name": "Product Hunt", "category": "国际", "priority": 2},
    # 社区
    "douban": {"name": "豆瓣热门", "category": "社区", "priority": 2},
    "hupu": {"name": "虎扑热帖", "category": "社区", "priority": 2},
    "coolapk": {"name": "酷安热榜", "category": "社区", "priority": 3},
    "smzdm": {"name": "什么值得买", "category": "社区", "priority": 3},
    # 游戏
    "steam": {"name": "Steam热销", "category": "游戏", "priority": 2},
}

# ==================== 通用工具函数 ====================

def get_headers(referer: str = "") -> Dict[str, str]:
    return {
        'User-Agent': random.choice(PC_AGENTS),
        'Referer': referer,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }


def fetch_content(url: str, referer: str = "") -> Optional[str]:
    """获取网页内容（绕过代理直接连接）"""
    # 创建无代理的 opener
    proxy_handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy_handler)
    
    req = urllib.request.Request(url, headers=get_headers(referer))
    try:
        with opener.open(req, timeout=15) as response:
            data = response.read()
            if response.info().get('Content-Encoding') == 'gzip':
                data = gzip.GzipFile(fileobj=io.BytesIO(data)).read()
            return data.decode('utf-8')
    except Exception as e:
        print(f"[警告] 抓取失败 {url[:30]}...: {e}", file=sys.stderr)
        return None


# ==================== 语义分类 ====================

def classify_topic(title: str) -> Optional[str]:
    """
    智能语义分类：根据关键词组合识别议题类型
    返回匹配度最高的类型，或 None
    """
    best_match = None
    best_score = 0
    
    for topic_type, keywords in TOPIC_TYPES.items():
        score = 0
        core_matched = False
        
        # 核心词匹配（必须有）
        for word in keywords.get("核心词", []):
            if word in title:
                core_matched = True
                score += 2
        
        if not core_matched:
            continue
        
        # 强化词/场景词匹配（加分）
        for key in ["强化词", "场景词", "数据词", "情绪词", "公司词"]:
            for word in keywords.get(key, []):
                if word in title:
                    score += 1
        
        if score > best_score:
            best_score = score
            best_match = topic_type
    
    return best_match if best_score >= 2 else None


# ==================== 热度合并 ====================

def tokenize(text: str) -> Set[str]:
    """简单分词：提取中文词（2-4字）和英文单词"""
    # 中文词
    chinese = set(re.findall(r'[\u4e00-\u9fff]{2,4}', text))
    # 英文词
    english = set(re.findall(r'[a-zA-Z]{3,}', text.lower()))
    return chinese | english


def jaccard_similarity(a: str, b: str) -> float:
    """Jaccard 相似度"""
    tokens_a = tokenize(a)
    tokens_b = tokenize(b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return intersection / union if union > 0 else 0.0


def merge_similar_topics(items: List[Dict], threshold: float = 0.5) -> List[Dict]:
    """
    合并相似话题
    返回合并后的列表，每项包含 merged_items（合并的原始项）和 heat（热度=平台数）
    """
    if not items:
        return []
    
    merged = []
    used = set()
    
    for i, item in enumerate(items):
        if i in used:
            continue
        
        group = [item]
        used.add(i)
        
        for j, other in enumerate(items):
            if j in used or j == i:
                continue
            
            if jaccard_similarity(item['title'], other['title']) >= threshold:
                group.append(other)
                used.add(j)
        
        # 选择最佳代表（来源权重最高的）
        group.sort(key=lambda x: SOURCE_TIERS.get(x.get('source', ''), 4))
        representative = group[0].copy()
        representative['heat'] = len(group)
        representative['merged_sources'] = [g.get('source_name', g.get('source', '')) for g in group]
        merged.append(representative)
    
    return merged


# ==================== 历史对比 ====================

def load_analyzed_topics() -> List[str]:
    """加载已分析过的议题列表"""
    topics = []
    
    if not ARCHIVE_DIR.exists():
        return topics
    
    # 遍历归档目录
    for category_dir in ARCHIVE_DIR.iterdir():
        if not category_dir.is_dir():
            continue
        for topic_dir in category_dir.iterdir():
            if topic_dir.is_dir():
                # 提取议题名（格式：YYYYMMDD_议题名）
                name = topic_dir.name
                if '_' in name:
                    topic_name = name.split('_', 1)[1]
                    topics.append(topic_name)
    
    return topics


def check_if_analyzed(title: str, analyzed_topics: List[str]) -> Optional[str]:
    """检查标题是否与已分析议题相似"""
    for topic in analyzed_topics:
        if jaccard_similarity(title, topic) >= 0.4:
            return topic
    return None


# ==================== 数据抓取 ====================

def fetch_baidu_hot() -> List[Dict]:
    """直接抓取百度热搜（备用方案，不依赖第三方API）"""
    results = []
    url = "https://top.baidu.com/board?tab=realtime"
    html = fetch_content(url, "https://www.baidu.com/")
    
    if not html:
        return results
    
    # 匹配热搜标题
    pattern = r'<div class="c-single-text-ellipsis"[^>]*>([^<]{4,50})</div>'
    matches = re.findall(pattern, html)
    
    seen = set()
    for title in matches:
        title = title.strip()
        if title and title not in seen and len(title) > 3:
            results.append({
                "title": title,
                "url": f"https://www.baidu.com/s?wd={urllib.parse.quote(title)}",
                "source": "baidu",
                "source_name": "百度热搜",
                "category": "热搜",
                "tier": 3,
            })
            seen.add(title)
            if len(results) >= 20:
                break
    
    return results


def fetch_weibo_hot() -> List[Dict]:
    """直接抓取微博热搜（备用方案）"""
    results = []
    url = "https://weibo.com/ajax/side/hotSearch"
    
    # 创建无代理的 opener
    proxy_handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy_handler)
    
    try:
        req = urllib.request.Request(url, headers=get_headers("https://weibo.com/"))
        with opener.open(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            realtime = data.get('data', {}).get('realtime', [])
            for item in realtime[:20]:
                word = item.get('word', '')
                if word:
                    results.append({
                        "title": word,
                        "url": f"https://s.weibo.com/weibo?q={urllib.parse.quote(word)}",
                        "source": "weibo",
                        "source_name": "微博热搜",
                        "category": "热搜",
                        "tier": 3,
                    })
    except:
        pass
    
    return results


def fetch_newsnow_source(source_id: str, limit: int = 10) -> List[Dict]:
    """从 NewsNow 抓取热点（绕过代理直连）"""
    results = []
    source_info = NEWSNOW_SOURCES.get(source_id, {"name": source_id, "category": "其他", "priority": 3})
    
    api_url = f"https://newsnow.busiyi.world/api/{source_id}"
    
    # 创建无代理的 opener
    proxy_handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy_handler)
    
    try:
        req = urllib.request.Request(api_url, headers={
            'User-Agent': random.choice(PC_AGENTS),
            'Accept': 'application/json',
        })
        with opener.open(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if isinstance(data, list):
                for i, item in enumerate(data[:limit], 1):
                    title = item.get('title', item.get('name', ''))
                    url = item.get('url', item.get('link', ''))
                    if title:
                        results.append({
                            "title": title,
                            "url": url,
                            "source": source_id,
                            "source_name": source_info["name"],
                            "category": source_info["category"],
                            "tier": SOURCE_TIERS.get(source_id, 4),
                        })
    except:
        pass  # 静默失败
    
    return results


def fetch_caixin_depth() -> List[Dict]:
    results = []
    html = fetch_content("https://www.caixin.com/", "https://www.caixin.com/")
    
    if not html:
        return results
    
    matches = re.findall(r'<a[^>]*href="(https://[^"]*caixin\.com/[^"]+)"[^>]*>([^<]{10,80})</a>', html)
    
    seen = set()
    for url, title in matches:
        title = title.strip()
        if title and title not in seen and len(title) > 8 and "更多" not in title and "登录" not in title:
            results.append({
                "title": title,
                "url": url,
                "source": "caixin",
                "source_name": "财新网",
                "category": "深度报道",
                "tier": 1,
            })
            seen.add(title)
            if len(results) >= 15:
                break
    
    return results


def fetch_caixin_weekly() -> List[Dict]:
    results = []
    html = fetch_content("https://weekly.caixin.com/", "https://www.caixin.com/")
    
    if not html:
        return results
    
    matches = re.findall(r'<a[^>]*href="(https://weekly\.caixin\.com/[^"]+)"[^>]*>([^<]{8,60})</a>', html)
    
    seen = set()
    for url, title in matches:
        title = title.strip()
        if title and title not in seen and len(title) > 6:
            results.append({
                "title": f"[封面] {title}",
                "url": url,
                "source": "caixin_weekly",
                "source_name": "财新周刊",
                "category": "封面报道",
                "tier": 1,
            })
            seen.add(title)
            if len(results) >= 5:
                break
    
    return results


def fetch_thepaper_depth() -> List[Dict]:
    results = []
    html = fetch_content("https://www.thepaper.cn/", "https://www.thepaper.cn/")
    
    if not html:
        return results
    
    matches = re.findall(r'<a[^>]*href="([^"]*newsDetail_forward_\d+[^"]*)"[^>]*>([^<]{8,80})</a>', html)
    
    seen = set()
    for url_path, title in matches:
        title = title.strip()
        if not url_path.startswith('http'):
            url_path = f"https://www.thepaper.cn{url_path}"
        
        if title and title not in seen and len(title) > 8 and "广告" not in title:
            results.append({
                "title": title,
                "url": url_path,
                "source": "thepaper",
                "source_name": "澎湃新闻",
                "category": "深度报道",
                "tier": 1,
            })
            seen.add(title)
            if len(results) >= 15:
                break
    
    return results


# ==================== 聚合与分析 ====================

def aggregate_and_analyze(
    include_newsnow: bool = True,
    include_caixin: bool = True,
    include_thepaper: bool = True,
    depth_only: bool = False,
    priority: int = 2,
) -> Tuple[List[Dict], List[Dict]]:
    """
    抓取、合并、分类、对比
    
    返回: (深度报道列表, 新议题列表)
    新议题 = 热搜有但深度报道没覆盖的话题
    """
    depth_items = []  # 深度报道
    hot_items = []    # 热搜/热榜
    
    # 1. 抓取数据（分开收集）
    if include_caixin:
        print("[信息] 抓取财新网...", file=sys.stderr)
        depth_items.extend(fetch_caixin_depth())
        depth_items.extend(fetch_caixin_weekly())
    
    if include_thepaper:
        print("[信息] 抓取澎湃新闻...", file=sys.stderr)
        depth_items.extend(fetch_thepaper_depth())
    
    if include_newsnow and not depth_only:
        print("[信息] 抓取热搜平台...", file=sys.stderr)
        
        # 先尝试 NewsNow
        for source_id, info in NEWSNOW_SOURCES.items():
            if info["priority"] <= priority:
                hot_items.extend(fetch_newsnow_source(source_id, limit=5))
        
        # 如果 NewsNow 失败（0条），使用备用方案
        if len(hot_items) == 0:
            print("[信息] NewsNow 不可用，使用备用热搜源...", file=sys.stderr)
            hot_items.extend(fetch_baidu_hot())
            hot_items.extend(fetch_weibo_hot())
    
    # 2. 深度报道合并
    print(f"[信息] 处理深度报道 ({len(depth_items)} 条)...", file=sys.stderr)
    depth_merged = merge_similar_topics(depth_items, threshold=0.5)
    
    # 3. 热搜合并
    print(f"[信息] 处理热搜 ({len(hot_items)} 条)...", file=sys.stderr)
    hot_merged = merge_similar_topics(hot_items, threshold=0.5)
    
    # 4. 构建深度报道标题集（用于检测新议题）
    depth_titles = [item['title'] for item in depth_merged]
    
    # 5. 找出"新议题"：热搜有但深度报道没覆盖的话题
    new_topics = []
    covered_topics = []
    
    for hot_item in hot_merged:
        # 检查是否被深度报道覆盖
        is_covered = False
        for depth_title in depth_titles:
            if jaccard_similarity(hot_item['title'], depth_title) >= 0.3:
                is_covered = True
                break
        
        if is_covered:
            hot_item['is_new'] = False
            covered_topics.append(hot_item)
        else:
            hot_item['is_new'] = True
            new_topics.append(hot_item)
    
    # 6. 语义分类
    for item in depth_merged + new_topics:
        item['topic_type'] = classify_topic(item['title'])
    
    # 7. 历史对比
    analyzed_topics = load_analyzed_topics()
    for item in depth_merged + new_topics:
        match = check_if_analyzed(item['title'], analyzed_topics)
        if match:
            item['analyzed_as'] = match
    
    # 8. 新议题按热度排序（热度高的优先）
    new_topics.sort(key=lambda x: (-x.get('heat', 1), x.get('tier', 4)))
    
    print(f"[信息] 发现 {len(new_topics)} 个待挖掘新议题", file=sys.stderr)
    
    return depth_merged, new_topics


# ==================== 输出格式化 ====================

def print_item(item: Dict, show_sources: bool = True):
    """打印单个条目"""
    tags = []
    
    # 热度
    heat = item.get('heat', 1)
    if heat > 1:
        tags.append(f"🔥×{heat}")
    
    # 语义分类
    topic_type = item.get('topic_type')
    if topic_type:
        tags.append(f"[{topic_type}]")
    
    # 已分析
    if 'analyzed_as' in item:
        tags.append(f"[已分析:{item['analyzed_as'][:8]}]")
    
    prefix = " ".join(tags) + " " if tags else ""
    print(f"  {prefix}{item['title'][:55]}")
    
    # 如果有合并来源，显示
    if show_sources and heat > 1:
        sources = item.get('merged_sources', [])[:3]
        print(f"    └─ 来源: {', '.join(sources)}")


def print_results(depth_items: List[Dict], new_topics: List[Dict], json_mode: bool = False):
    """分区输出：深度报道 + 新议题"""
    if json_mode:
        output = {
            "depth_reports": depth_items,
            "new_topics": new_topics,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return
    
    print(f"\n{'='*70}")
    print(f"📰 智能热点分析 v3.1 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*70}")
    
    # ===== 新议题区（最重要！）=====
    if new_topics:
        print(f"\n### 🆕 待挖掘新议题 ({len(new_topics)}条) ###")
        print(">>> 这些话题热搜有热度，但财新/澎湃尚未报道 <<<")
        print("-" * 50)
        
        for item in new_topics[:15]:
            print_item(item, show_sources=True)
    else:
        print("\n### 🆕 待挖掘新议题 ###")
        print("  （暂无，深度报道已覆盖大部分热点）")
    
    # ===== 深度报道区 =====
    if depth_items:
        print(f"\n### 📖 深度报道参考 ({len(depth_items)}条) ###")
        print("-" * 50)
        
        for item in depth_items[:10]:
            print_item(item, show_sources=False)
    
    print(f"\n{'='*70}")
    print(f"💡 新议题 {len(new_topics)} 条 | 深度报道 {len(depth_items)} 条")


# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(description="智能热点分析系统 v3.1")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--depth", action="store_true", help="仅抓取深度报道")
    parser.add_argument("--all", action="store_true", help="全量抓取")
    parser.add_argument("--priority", type=int, default=2, help="NewsNow 优先级 (1-3)")
    parser.add_argument("--list-sources", action="store_true", help="列出所有平台")
    
    args = parser.parse_args()
    
    if args.list_sources:
        print("可用平台 (按权重分层):\n")
        for tier in [1, 2, 3, 4]:
            tier_name = {1: "T1 深度报道", 2: "T2 专业媒体", 3: "T3 综合热搜", 4: "T4 社区"}[tier]
            print(f"[{tier_name}]")
            for source_id, t in SOURCE_TIERS.items():
                if t == tier:
                    name = NEWSNOW_SOURCES.get(source_id, {}).get('name', source_id)
                    print(f"  - {name}")
            print()
        return
    
    priority = 3 if args.all else args.priority
    
    depth_items, new_topics = aggregate_and_analyze(
        include_newsnow=not args.depth,
        include_caixin=True,
        include_thepaper=True,
        depth_only=args.depth,
        priority=priority,
    )
    
    print_results(depth_items, new_topics, json_mode=args.json)


if __name__ == "__main__":
    main()

