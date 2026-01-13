#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
data_cache.py - 数据缓存模块

提供搜索结果缓存、数据验证和来源评分功能。

用法:
    from data_cache import DataCache
    
    cache = DataCache()
    cache.set("query", data, source="国家统计局", ttl_days=7)
    result = cache.get("query")
"""

import json
import os
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List


# 数据目录
DATA_DIR = Path(__file__).parent.parent / "data"
CACHE_DIR = DATA_DIR / "cache"
VERIFIED_DIR = DATA_DIR / "verified"
REUSED_DIR = DATA_DIR / "reused"
INDEX_DIR = DATA_DIR / "index"


# 来源权威度评分
SOURCE_AUTHORITY = {
    # 政府官方来源 (9-10)
    "国家统计局": 10,
    "中国人民银行": 10,
    "最高人民法院": 10,
    "国家法律法规数据库": 10,
    "海关总署": 10,
    "财政部": 10,
    "新华社": 9,
    "人民日报": 9,
    "中央电视台": 9,
    
    # 学术/研究来源 (7-8)
    "学术论文": 8,
    "知网": 8,
    "万方": 8,
    "Semantic Scholar": 8,
    "行业白皮书": 7,
    "研究报告": 7,
    
    # 专业媒体 (5-6)
    "财经媒体": 6,
    "经济观察报": 6,
    "第一财经": 6,
    "界面新闻": 5,
    "澎湃新闻": 5,
    
    # 其他来源 (1-4)
    "自媒体": 3,
    "论坛/社区": 2,
    "未知来源": 1,
}


class DataCache:
    """数据缓存管理器"""
    
    def __init__(self):
        self._ensure_dirs()
        self._load_index()
    
    def _ensure_dirs(self):
        """确保目录存在"""
        for d in [CACHE_DIR, VERIFIED_DIR, REUSED_DIR, INDEX_DIR]:
            d.mkdir(parents=True, exist_ok=True)
    
    def _load_index(self):
        """加载数据索引"""
        index_file = INDEX_DIR / "data_index.json"
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                self._index = json.load(f)
        else:
            self._index = {"entries": [], "last_updated": None}
    
    def _save_index(self):
        """保存数据索引"""
        self._index["last_updated"] = datetime.now().isoformat()
        index_file = INDEX_DIR / "data_index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(self._index, f, ensure_ascii=False, indent=2)
    
    def _hash_key(self, key: str) -> str:
        """生成缓存键的哈希值"""
        return hashlib.md5(key.encode('utf-8')).hexdigest()[:12]
    
    def _get_cache_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        month = datetime.now().strftime("%Y-%m")
        cache_month_dir = CACHE_DIR / month
        cache_month_dir.mkdir(parents=True, exist_ok=True)
        return cache_month_dir / f"{self._hash_key(key)}.json"
    
    def set(self, key: str, data: Any, source: str = "未知来源", 
            ttl_days: int = 7, category: str = "general") -> None:
        """
        缓存数据
        
        Args:
            key: 缓存键（通常是查询字符串）
            data: 要缓存的数据
            source: 数据来源
            ttl_days: 缓存有效期（天）
            category: 数据类别 (economic/legal/social/academic/general)
        """
        cache_entry = {
            "key": key,
            "data": data,
            "source": source,
            "authority": self.get_authority_score(source),
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=ttl_days)).isoformat(),
            "category": category,
            "access_count": 0
        }
        
        cache_path = self._get_cache_path(key)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_entry, f, ensure_ascii=False, indent=2)
        
        # 更新索引
        self._index["entries"].append({
            "key": key,
            "hash": self._hash_key(key),
            "source": source,
            "category": category,
            "created_at": cache_entry["created_at"]
        })
        self._save_index()
    
    def get(self, key: str) -> Optional[Dict]:
        """
        获取缓存数据
        
        Returns:
            缓存条目（包含data, source, authority等字段），如不存在或已过期返回None
        """
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        with open(cache_path, 'r', encoding='utf-8') as f:
            entry = json.load(f)
        
        # 检查是否过期
        expires_at = datetime.fromisoformat(entry["expires_at"])
        if datetime.now() > expires_at:
            cache_path.unlink()  # 删除过期缓存
            return None
        
        # 更新访问计数
        entry["access_count"] += 1
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(entry, f, ensure_ascii=False, indent=2)
        
        return entry
    
    def get_authority_score(self, source: str) -> int:
        """获取来源权威度评分"""
        # 精确匹配
        if source in SOURCE_AUTHORITY:
            return SOURCE_AUTHORITY[source]
        
        # 模糊匹配
        source_lower = source.lower()
        for known_source, score in SOURCE_AUTHORITY.items():
            if known_source.lower() in source_lower:
                return score
        
        return SOURCE_AUTHORITY["未知来源"]
    
    def validate_data(self, data: Dict) -> Dict[str, Any]:
        """
        验证数据质量
        
        Returns:
            {
                "is_valid": bool,
                "timeliness": "有效|过期|未知",
                "authority": int,
                "issues": [问题列表]
            }
        """
        issues = []
        
        # 检查来源
        source = data.get("source", "未知来源")
        authority = self.get_authority_score(source)
        if authority < 5:
            issues.append(f"来源权威度较低 ({source}: {authority}/10)")
        
        # 检查时效性
        timeliness = "未知"
        if "year" in data or "date" in data:
            data_year = data.get("year") or int(data.get("date", "2020")[:4])
            current_year = datetime.now().year
            age = current_year - data_year
            if age <= 2:
                timeliness = "有效"
            elif age <= 5:
                timeliness = "较旧"
                issues.append(f"数据为{data_year}年，可能已过时")
            else:
                timeliness = "过期"
                issues.append(f"数据为{data_year}年，严重过期")
        
        # 检查完整性
        if "value" in data and data["value"] is None:
            issues.append("数据值缺失")
        if "unit" not in data:
            issues.append("缺少单位")
        
        return {
            "is_valid": len(issues) == 0,
            "timeliness": timeliness,
            "authority": authority,
            "authority_label": self._get_authority_label(authority),
            "issues": issues
        }
    
    def _get_authority_label(self, score: int) -> str:
        """获取权威度标签"""
        if score >= 9:
            return "官方权威"
        elif score >= 7:
            return "学术可信"
        elif score >= 5:
            return "专业媒体"
        elif score >= 3:
            return "待验证"
        else:
            return "低可信度"
    
    def format_citation(self, data: Dict, style: str = "inline") -> str:
        """
        格式化数据引用
        
        Args:
            data: 数据条目
            style: "inline"（行内）或 "footnote"（脚注）
        
        Returns:
            格式化后的引用文本
        """
        source = data.get("source", "未知来源")
        year = data.get("year", datetime.now().year)
        title = data.get("title", "")
        url = data.get("url", "")
        
        validation = self.validate_data(data)
        authority = validation["authority"]
        
        if style == "inline":
            return f"[来源: {source}{year}年，权威度: {authority}/10]"
        else:
            citation = f"{source}"
            if title:
                citation += f"《{title}》"
            if year:
                citation += f"，{year}年"
            if url:
                citation += f"，{url}"
            return citation
    
    def search_local(self, query: str, category: str = None) -> List[Dict]:
        """
        搜索本地数据仓库
        
        Args:
            query: 搜索词
            category: 限定类别
        
        Returns:
            匹配的数据条目列表
        """
        results = []
        
        for entry in self._index.get("entries", []):
            if category and entry.get("category") != category:
                continue
            
            if query.lower() in entry.get("key", "").lower():
                cache_data = self.get(entry["key"])
                if cache_data:
                    results.append(cache_data)
        
        # 按权威度排序
        results.sort(key=lambda x: x.get("authority", 0), reverse=True)
        
        return results


# 便捷函数
_cache_instance = None

def get_cache() -> DataCache:
    """获取全局缓存实例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = DataCache()
    return _cache_instance


def cache_data(key: str, data: Any, source: str = "未知来源", **kwargs):
    """缓存数据的便捷函数"""
    get_cache().set(key, data, source, **kwargs)


def get_cached(key: str) -> Optional[Dict]:
    """获取缓存的便捷函数"""
    return get_cache().get(key)


def validate_data(data: Dict) -> Dict:
    """验证数据的便捷函数"""
    return get_cache().validate_data(data)


def format_citation(data: Dict, style: str = "inline") -> str:
    """格式化引用的便捷函数"""
    return get_cache().format_citation(data, style)


if __name__ == "__main__":
    # 测试
    cache = DataCache()
    
    # 测试缓存
    test_data = {
        "value": 1.4,
        "unit": "亿",
        "year": 2025,
        "title": "中国独居人口统计"
    }
    cache.set("中国独居人口", test_data, source="国家统计局", category="social")
    
    # 测试获取
    result = cache.get("中国独居人口")
    if result:
        print(f"✅ 缓存成功: {result['data']}")
        print(f"📊 权威度: {result['authority']}/10")
        print(f"📎 引用: {cache.format_citation(result['data'])}")
    
    # 测试验证
    validation = cache.validate_data(test_data)
    print(f"✅ 验证结果: {validation}")
