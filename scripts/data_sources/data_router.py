#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
data_router.py - 数据源统一调度器

根据查询类型自动选择最合适的数据源。

用法:
    python data_router.py --query "中国独居人口" --type auto
    python data_router.py --query "民法典 继承" --type legal
    python data_router.py --query "death anxiety" --type academic
"""

import argparse
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# 导入数据源模块
try:
    from data_cache import get_cache, cache_data, get_cached, validate_data, format_citation
    from law_search import search_laws, get_law_article
    from academic_search import search_papers
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from data_cache import get_cache, cache_data, get_cached, validate_data, format_citation
    from law_search import search_laws, get_law_article
    from academic_search import search_papers


# 查询类型关键词
TYPE_KEYWORDS = {
    "legal": ["法", "律", "条", "规", "诉", "判", "案", "罪", "民法典", "刑法", "宪法", "合同"],
    "academic": ["研究", "论文", "学术", "调查", "实验", "数据", "分析", "theory", "study"],
    "economic": ["GDP", "经济", "增长", "人口", "统计", "收入", "消费", "就业", "通胀"],
    "social": ["社会", "文化", "教育", "医疗", "养老", "独居", "家庭", "心理"]
}


def detect_query_type(query: str) -> str:
    """
    自动检测查询类型
    
    Returns:
        legal / academic / economic / social / general
    """
    query_lower = query.lower()
    
    scores = {t: 0 for t in TYPE_KEYWORDS}
    
    for query_type, keywords in TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in query_lower:
                scores[query_type] += 1
    
    max_type = max(scores, key=scores.get)
    if scores[max_type] > 0:
        return max_type
    
    return "general"


def route_query(query: str, query_type: str = "auto", limit: int = 5) -> Dict:
    """
    路由查询到合适的数据源
    
    Args:
        query: 查询字符串
        query_type: 查询类型 (auto/legal/academic/economic/social/general)
        limit: 返回数量上限
    
    Returns:
        {
            "query": 原始查询,
            "type": 查询类型,
            "sources_used": [使用的数据源],
            "results": [结果列表],
            "cached": 是否使用缓存,
            "timestamp": 时间戳
        }
    """
    # 自动检测类型
    if query_type == "auto":
        query_type = detect_query_type(query)
    
    results = []
    sources_used = []
    cached = False
    
    print(f"\n🔀 数据路由器")
    print(f"=" * 50)
    print(f"📝 查询: {query}")
    print(f"📁 类型: {query_type}")
    print()
    
    # 1. 先检查本地缓存
    cache = get_cache()
    local_results = cache.search_local(query, category=query_type)
    if local_results:
        print(f"📦 本地缓存命中: {len(local_results)} 条")
        results.extend([r["data"] for r in local_results])
        sources_used.append("本地缓存")
        cached = True
    
    # 2. 根据类型调用对应数据源
    if query_type == "legal":
        print(f"⚖️ 调用法律数据源...")
        law_results = search_laws(query)
        for r in law_results:
            if r.get("data"):
                results.append({
                    "type": "legal",
                    "data": r["data"],
                    "source": r.get("source", "法律数据库"),
                    "authority": r.get("authority", 10)
                })
        sources_used.append("法律法规数据库")
    
    elif query_type == "academic":
        print(f"📚 调用学术数据源...")
        papers = search_papers(query, limit=limit)
        for paper in papers:
            results.append({
                "type": "academic",
                "data": paper,
                "source": paper.get("source", "Semantic Scholar"),
                "authority": paper.get("authority", 8)
            })
        sources_used.append("Semantic Scholar")
    
    elif query_type == "economic":
        print(f"📊 调用经济数据源...")
        # TODO: 接入国家统计局 API
        print(f"⚠️ 经济数据源暂未实现，请使用 search_web 在线搜索")
        results.append({
            "type": "economic",
            "data": None,
            "note": "建议搜索: https://data.stats.gov.cn/",
            "source": "系统提示"
        })
        sources_used.append("系统提示")
    
    elif query_type == "social":
        print(f"🏠 调用社会数据源...")
        # 社会类问题同时调用学术和法律数据源
        papers = search_papers(query, limit=3)
        for paper in papers:
            results.append({
                "type": "academic",
                "data": paper,
                "source": paper.get("source", "Semantic Scholar"),
                "authority": paper.get("authority", 8)
            })
        sources_used.append("Semantic Scholar")
        
        law_results = search_laws(query)
        for r in law_results:
            if r.get("data"):
                results.append({
                    "type": "legal",
                    "data": r["data"],
                    "source": r.get("source", "法律数据库"),
                    "authority": r.get("authority", 10)
                })
        sources_used.append("法律法规数据库")
    
    else:  # general
        print(f"🔍 通用类型，尝试多数据源...")
        # 尝试所有数据源
        papers = search_papers(query, limit=2)
        for paper in papers:
            results.append({
                "type": "academic",
                "data": paper,
                "source": paper.get("source", "Semantic Scholar"),
                "authority": paper.get("authority", 8)
            })
        sources_used.append("Semantic Scholar")
    
    # 3. 按权威度排序
    results.sort(key=lambda x: x.get("authority", 0), reverse=True)
    
    # 4. 验证结果
    for r in results:
        if r.get("data") and isinstance(r["data"], dict):
            validation = validate_data(r["data"])
            r["validation"] = validation
    
    return {
        "query": query,
        "type": query_type,
        "sources_used": list(set(sources_used)),
        "results": results[:limit],
        "total_found": len(results),
        "cached": cached,
        "timestamp": datetime.now().isoformat()
    }


def format_results(response: Dict) -> str:
    """格式化查询结果为 Markdown"""
    lines = []
    lines.append(f"## 数据查询结果")
    lines.append(f"")
    lines.append(f"**查询**: {response['query']}")
    lines.append(f"**类型**: {response['type']}")
    lines.append(f"**数据源**: {', '.join(response['sources_used'])}")
    lines.append(f"**结果数**: {response['total_found']}")
    lines.append(f"")
    
    for i, r in enumerate(response["results"], 1):
        lines.append(f"### {i}. {r['type'].upper()}")
        
        data = r.get("data")
        if data is None:
            lines.append(f"⚠️ {r.get('note', '无数据')}")
            continue
        
        if isinstance(data, dict):
            if "title" in data:
                lines.append(f"**{data['title']}**")
            
            if "content" in data:
                lines.append(f"> {data['content']}")
            
            if "abstract" in data:
                lines.append(f"> {data['abstract'][:150]}...")
            
            if "authors" in data:
                lines.append(f"作者: {', '.join(data['authors'][:3])}")
            
            if "year" in data:
                lines.append(f"年份: {data['year']}")
            
            if "citations" in data:
                lines.append(f"引用: {data['citations']}")
        
        lines.append(f"")
        lines.append(f"[来源: {r['source']}, 权威度: {r['authority']}/10]")
        
        if r.get("validation"):
            v = r["validation"]
            lines.append(f"[验证: {v['authority_label']}, 时效: {v['timeliness']}]")
            if v["issues"]:
                lines.append(f"⚠️ 问题: {'; '.join(v['issues'])}")
        
        lines.append(f"")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='数据源统一调度器')
    parser.add_argument('--query', '-q', required=True, help='查询字符串')
    parser.add_argument('--type', '-t', 
                        choices=['auto', 'legal', 'academic', 'economic', 'social', 'general'],
                        default='auto', help='查询类型')
    parser.add_argument('--limit', '-l', type=int, default=5, help='返回数量上限')
    parser.add_argument('--format', '-f', choices=['json', 'markdown'], 
                        default='markdown', help='输出格式')
    
    args = parser.parse_args()
    
    response = route_query(args.query, args.type, args.limit)
    
    if args.format == 'json':
        print(json.dumps(response, ensure_ascii=False, indent=2))
    else:
        print(format_results(response))


if __name__ == "__main__":
    main()
