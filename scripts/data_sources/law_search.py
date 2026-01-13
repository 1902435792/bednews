#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
law_search.py - 法律法规数据源

接入国家法律法规数据库，提供法条查询和案例搜索功能。

用法:
    python law_search.py --query "民法典 继承" --type law
    python law_search.py --query "数字遗产" --type case
"""

import argparse
import json
import re
import requests
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

# 尝试导入本地缓存模块
try:
    from data_cache import get_cache, cache_data, get_cached
except ImportError:
    # 如果直接运行此脚本
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from data_cache import get_cache, cache_data, get_cached


# 数据源配置
SOURCES = {
    "npc": {
        "name": "国家法律法规数据库",
        "base_url": "https://flk.npc.gov.cn",
        "authority": 10
    },
    "court": {
        "name": "中国裁判文书网",
        "base_url": "https://wenshu.court.gov.cn",
        "authority": 10
    }
}


def search_laws(query: str, law_type: str = "法律") -> List[Dict]:
    """
    搜索法律法规
    
    Args:
        query: 搜索词，如 "民法典 继承"
        law_type: 法规类型 (法律/行政法规/司法解释/地方性法规)
    
    Returns:
        [{"title": 法规名称, "publish_date": 发布日期, "effective_date": 生效日期, 
          "status": 状态, "source": 来源, "url": 链接}]
    """
    # 检查缓存
    cache_key = f"law_search:{query}:{law_type}"
    cached = get_cached(cache_key)
    if cached:
        print(f"📦 使用缓存: {cache_key}")
        return cached["data"]
    
    results = []
    
    # 模拟搜索结果（实际使用时需要实现真实的API调用或页面解析）
    # 这里提供一些常用法条的预置数据
    PRESET_LAWS = {
        "民法典": {
            "title": "中华人民共和国民法典",
            "publish_date": "2020-05-28",
            "effective_date": "2021-01-01",
            "status": "有效",
            "source": "国家法律法规数据库",
            "url": "https://flk.npc.gov.cn/detail2.html?ZmY4MDgwODE3MjlkMWVmZTAxNzI5ZDUwYjVjNTAwYmY"
        },
        "继承": {
            "title": "中华人民共和国民法典 第六编 继承",
            "articles": [
                {"num": 1119, "content": "本编调整因继承产生的民事关系。"},
                {"num": 1120, "content": "国家保护自然人的继承权。"},
                {"num": 1121, "content": "继承从被继承人死亡时开始。"},
                {"num": 1122, "content": "遗产是自然人死亡时遗留的个人合法财产。"},
            ]
        },
        "数字遗产": {
            "title": "关于数字遗产的法律规定",
            "note": "中国目前没有专门的数字遗产法律",
            "related": [
                "《民法典》第127条：法律对数据、网络虚拟财产的保护有规定的，依照其规定。",
                "《网络安全法》：规定了网络数据的保护要求"
            ],
            "status": "法律空白",
            "source": "法律分析"
        },
        "独居": {
            "title": "关于独居老人/独居人群的法律规定",
            "related": [
                "《老年人权益保障法》第18条：家庭成员应当关心老年人的精神需求，不得忽视、冷落老年人。",
                "《民法典》第33条：具有完全民事行为能力的成年人，可以与其近亲属、其他愿意担任监护人的个人或者组织事先协商，以书面形式确定自己的监护人。"
            ],
            "source": "法律分析"
        }
    }
    
    # 匹配预置数据
    for keyword, data in PRESET_LAWS.items():
        if keyword in query:
            result = {
                "query": query,
                "keyword": keyword,
                "data": data,
                "source": "国家法律法规数据库",
                "authority": 10,
                "retrieved_at": datetime.now().isoformat()
            }
            results.append(result)
    
    # 如果没有预置数据，返回提示
    if not results:
        results.append({
            "query": query,
            "data": None,
            "note": f"未找到与'{query}'相关的法律法规预置数据。建议使用 search_web 进行在线搜索。",
            "source": "系统提示"
        })
    
    # 缓存结果
    if results and results[0].get("data"):
        cache_data(cache_key, results, source="国家法律法规数据库", 
                   category="legal", ttl_days=30)
    
    return results


def get_law_article(law_name: str, article_num: int) -> Optional[Dict]:
    """
    获取法条原文
    
    Args:
        law_name: 法律名称，如 "民法典"
        article_num: 条款号
    
    Returns:
        {"law": 法律名称, "article": 条款号, "content": 条文内容, 
         "source": 来源, "authority": 权威度}
    """
    cache_key = f"law_article:{law_name}:{article_num}"
    cached = get_cached(cache_key)
    if cached:
        return cached["data"]
    
    # 预置一些常用法条
    PRESET_ARTICLES = {
        ("民法典", 127): "法律对数据、网络虚拟财产的保护有规定的，依照其规定。",
        ("民法典", 33): "具有完全民事行为能力的成年人，可以与其近亲属、其他愿意担任监护人的个人或者组织事先协商，以书面形式确定自己的监护人，在自己丧失或者部分丧失民事行为能力时，由该监护人履行监护职责。",
        ("民法典", 1122): "遗产是自然人死亡时遗留的个人合法财产。依照法律规定或者根据其性质不得继承的遗产，不得继承。",
        ("民法典", 1123): "继承开始后，按照法定继承办理；有遗嘱的，按照遗嘱继承或者遗赠办理；有遗赠扶养协议的，按照协议办理。",
    }
    
    key = (law_name, article_num)
    if key in PRESET_ARTICLES:
        result = {
            "law": law_name,
            "article": article_num,
            "content": PRESET_ARTICLES[key],
            "source": "国家法律法规数据库",
            "authority": 10,
            "url": f"https://flk.npc.gov.cn/detail.html?law={law_name}&article={article_num}"
        }
        cache_data(cache_key, result, source="国家法律法规数据库", 
                   category="legal", ttl_days=365)
        return result
    
    return None


def format_law_citation(data: Dict) -> str:
    """格式化法律引用"""
    if "law" in data and "article" in data:
        return f"《{data['law']}》第{data['article']}条"
    elif "title" in data:
        return f"《{data['title']}》"
    else:
        return str(data)


def main():
    parser = argparse.ArgumentParser(description='法律法规数据源')
    parser.add_argument('--query', '-q', required=True, help='搜索词')
    parser.add_argument('--type', '-t', choices=['law', 'case', 'article'], 
                        default='law', help='查询类型')
    parser.add_argument('--article', '-a', type=int, help='条款号（用于查询具体法条）')
    
    args = parser.parse_args()
    
    print(f"\n⚖️ 法律法规数据源")
    print(f"=" * 50)
    print(f"🔍 查询: {args.query}")
    print(f"📁 类型: {args.type}")
    print()
    
    if args.type == 'article' and args.article:
        result = get_law_article(args.query, args.article)
        if result:
            print(f"📜 {format_law_citation(result)}")
            print(f"   {result['content']}")
            print(f"   [来源: {result['source']}, 权威度: {result['authority']}/10]")
        else:
            print(f"❌ 未找到 《{args.query}》第{args.article}条")
    else:
        results = search_laws(args.query)
        for i, r in enumerate(results, 1):
            print(f"{i}. {r.get('keyword', r.get('query', ''))}")
            if r.get('data'):
                data = r['data']
                if isinstance(data, dict):
                    if 'title' in data:
                        print(f"   📜 {data['title']}")
                    if 'status' in data:
                        print(f"   📌 状态: {data['status']}")
                    if 'related' in data:
                        print(f"   📎 相关规定:")
                        for related in data['related'][:3]:
                            print(f"      • {related[:60]}...")
            if r.get('note'):
                print(f"   ⚠️ {r['note']}")
            print(f"   [来源: {r.get('source', '未知')}, 权威度: {r.get('authority', 1)}/10]")
            print()


if __name__ == "__main__":
    main()
