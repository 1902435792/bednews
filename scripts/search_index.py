import json
import argparse
import os
import sys

# 设置默认编码
sys.stdout.reconfigure(encoding='utf-8')

# 同义词/关键词扩展映射
SYNONYMS = {
    '文物': ['博物馆', '藏品', '古董', '文化遗产', '国宝'],
    '捐赠': ['捐献', '赠送', '无偿', '转让'],
    '腐败': ['贪腐', '贪污', '受贿', '行贿', '内部人'],
    '房地产': ['烂尾', '恒大', '碧桂园', '万科', '预售', '业主'],
    '债务': ['城投', '利息', '破产', '违约', '融资'],
    '教育': ['大学', '高考', '教培', '双减', '考研', '内卷'],
    '医疗': ['医保', '医院', '药品', '看病'],
    '就业': ['失业', '裁员', '考公', '灵活就业'],
}

def expand_keywords(keywords):
    """扩展关键词，加入同义词"""
    expanded = set(keywords)
    for word in keywords:
        for key, synonyms in SYNONYMS.items():
            if word in key or word in synonyms:
                expanded.add(key)
                expanded.update(synonyms)
    return list(expanded)

def load_index(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 索引加载失败: {e}")
        return []

def score_item(item, keywords):
    score = 0
    title = item.get('title', '').lower()
    desc = item.get('description', '').lower()
    tags = [t.lower() for t in item.get('tags', [])]
    
    for word in keywords:
        word = word.lower()
        # 标题匹配权重最高
        if word in title:
            score += 15
        # 描述匹配
        if word in desc:
            score += 8
        # 标签匹配
        if any(word in tag for tag in tags):
            score += 5
            
    return score

def search(query, index_path, top_n=5, expand=True):
    index = load_index(index_path)
    if not index:
        return []

    keywords = query.lower().split()
    
    # 关键词扩展
    if expand:
        keywords = expand_keywords(keywords)
    
    results = []
    for item in index:
        s = score_item(item, keywords)
        if s > 0:
            results.append((s, item))

    # 按分数排序
    results.sort(key=lambda x: (x[0], x[1].get('id', '0')), reverse=True)

    return results[:top_n]

def print_results(results, query):
    """格式化输出搜索结果"""
    print(f"\n🔍 历史镜像搜索结果 (Query: {query})")
    print("=" * 50)
    
    if not results:
        print("❌ 未找到相关历史节目。")
        print("\n💡 建议：尝试使用不同的关键词，如：")
        print("   - 更宽泛的概念（如'管理制度'代替具体事件）")
        print("   - 相关产业/领域（如'文化遗产'代替'博物馆'）")
        return

    for i, (score, item) in enumerate(results, 1):
        ep_id = item.get('id', '?')
        title = item.get('title', '无标题')
        desc = item.get('description', '暂无摘要')[:80]
        tags = ', '.join(item.get('tags', []))
        path = item.get('path', '')
        
        print(f"\n[{i}] 第{ep_id}期 | 相关度: {score}")
        print(f"    📌 {title}")
        print(f"    📝 {desc}...")
        print(f"    🏷️  Tags: {tags}")
        print(f"    📂 Path: {path}")
    
    print("\n" + "=" * 50)
    print("💡 使用建议：")
    print("   1. 在蓝图中【必须】引用至少1个历史案例作为对比")
    print("   2. 可使用 view_file 查看完整节目内容")
    print("   3. 寻找'历史押韵'：相似逻辑、相似结构的案例")

def main():
    parser = argparse.ArgumentParser(
        description='睡前消息历史索引搜索工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python search_index.py "博物馆 文物"
  python search_index.py "房地产 烂尾" --top 10
  python search_index.py "教育内卷" --no-expand
        '''
    )
    parser.add_argument('query', help='搜索关键词（空格分隔）')
    parser.add_argument('--index', 
                        default='.agent/resources/bedtime-news/references/bedtime_news_index.json',
                        help='索引文件路径')
    parser.add_argument('--top', type=int, default=5, help='返回结果数量')
    parser.add_argument('--no-expand', action='store_true', help='禁用关键词扩展')
    
    args = parser.parse_args()
    
    results = search(args.query, args.index, args.top, not args.no_expand)
    print_results(results, args.query)

if __name__ == "__main__":
    main()
