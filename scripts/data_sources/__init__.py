"""
data_sources - 《睡前消息》数据增强层

提供权威数据源接入、本地缓存和数据验证功能。

模块:
    - data_cache: 数据缓存和来源评分
    - law_search: 法律法规数据源
    - academic_search: 学术论文数据源
    - data_router: 统一调度器

快速使用:
    from data_sources.data_router import route_query
    
    # 自动路由查询
    result = route_query("中国独居人口", query_type="auto")
    
    # 指定类型查询
    result = route_query("民法典 继承", query_type="legal")
    result = route_query("death anxiety", query_type="academic")
"""

from .data_cache import (
    DataCache,
    get_cache,
    cache_data,
    get_cached,
    validate_data,
    format_citation,
    SOURCE_AUTHORITY
)

from .law_search import (
    search_laws,
    get_law_article,
    format_law_citation
)

from .academic_search import (
    search_papers,
    get_paper_by_id,
    format_academic_citation
)

from .data_router import (
    route_query,
    detect_query_type,
    format_results
)

__all__ = [
    # Cache
    "DataCache",
    "get_cache",
    "cache_data",
    "get_cached",
    "validate_data",
    "format_citation",
    "SOURCE_AUTHORITY",
    # Law
    "search_laws",
    "get_law_article",
    "format_law_citation",
    # Academic
    "search_papers",
    "get_paper_by_id",
    "format_academic_citation",
    # Router
    "route_query",
    "detect_query_type",
    "format_results"
]
