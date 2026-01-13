#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
search_archive.py - 《睡前消息》文稿全文搜索

直接搜索 GitHub 克隆的完整文稿库，支持全文检索和上下文提取。

用法:
    python search_archive.py "死亡 焦虑"
    python search_archive.py "数字遗产" --type main --limit 10
    python search_archive.py "房地产" --context 3
"""

import argparse
import os
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import json

# 设置编码
sys.stdout.reconfigure(encoding='utf-8')

# 默认存档路径
ARCHIVE_ROOT = Path(__file__).parent.parent / "archive"
INDEX_CACHE = Path(__file__).parent.parent / "data" / "index" / "archive_index.json"

# 同义词扩展
SYNONYMS = {
    '死亡': ['死', '殡葬', '墓地', '遗体', '火化', '丧葬'],
    '焦虑': ['恐惧', '不安', '紧张', '恐慌'],
    '独居': ['单身', '独住', '空巢', '一人户'],
    '数字': ['网络', '互联网', '虚拟', '线上', 'APP'],
    '遗产': ['继承', '遗嘱', '财产'],
    '法律': ['法规', '法条', '法院', '立法', '司法'],
    '房地产': ['烂尾', '恒大', '碧桂园', '万科', '预售', '业主', '楼市'],
    '债务': ['城投', '破产', '违约', '融资', '信贷'],
    '教育': ['大学', '高考', '教培', '双减', '考研', '内卷'],
    '医疗': ['医保', '医院', '药品', '看病', '疫情'],
    '就业': ['失业', '裁员', '考公', '灵活就业', '工资'],
    '消费': ['购买', '花钱', '支出', '消费主义'],
    '资本': ['投资', '融资', '利润', '市场', '金融'],
}


def expand_keywords(keywords: List[str]) -> List[str]:
    """扩展关键词，加入同义词"""
    expanded = set(keywords)
    for word in keywords:
        for key, synonyms in SYNONYMS.items():
            if word in key or key in word:
                expanded.add(key)
                expanded.update(synonyms)
            if word in synonyms:
                expanded.add(key)
                expanded.update(synonyms)
    return list(expanded)


def parse_episode_info(filepath: Path) -> Dict:
    """从文件路径和内容中提取期数信息"""
    filename = filepath.stem
    
    # 尝试从文件名提取期数
    ep_match = re.search(r'(\d+)', filename)
    episode = int(ep_match.group(1)) if ep_match else 0
    
    # 确定节目类型
    parent = filepath.parent.name
    if parent == 'main':
        show_type = '主节目'
    elif parent == 'business':
        show_type = '商业'
    elif parent == 'daily':
        show_type = '日更'
    elif parent == 'opinion':
        show_type = '观点'
    elif parent == 'reference':
        show_type = '参考'
    else:
        show_type = parent
    
    return {
        'episode': episode,
        'type': show_type,
        'filename': filename,
        'path': str(filepath)
    }


def extract_title(content: str) -> str:
    """从内容中提取标题"""
    # 尝试匹配第一个 # 标题
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if title_match:
        return title_match.group(1).strip()
    
    # 尝试匹配第一个有意义的行
    for line in content.split('\n')[:10]:
        line = line.strip()
        if line and not line.startswith('---') and len(line) > 5:
            return line[:80]
    
    return '无标题'


def search_file(filepath: Path, keywords: List[str], context_lines: int = 2) -> Optional[Dict]:
    """搜索单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return None
    
    content_lower = content.lower()
    
    # 计算匹配分数
    score = 0
    matches = []
    
    for kw in keywords:
        kw_lower = kw.lower()
        # 计算出现次数
        count = content_lower.count(kw_lower)
        if count > 0:
            score += count * len(kw)  # 长关键词权重更高
            
            # 提取上下文
            for match in re.finditer(re.escape(kw_lower), content_lower):
                start = match.start()
                # 找到这个位置对应的行
                line_start = content.rfind('\n', 0, start) + 1
                line_end = content.find('\n', start)
                if line_end == -1:
                    line_end = len(content)
                
                context = content[line_start:line_end].strip()
                if context and len(context) > 10:
                    matches.append({
                        'keyword': kw,
                        'context': context[:200]
                    })
    
    if score == 0:
        return None
    
    # 提取元信息
    info = parse_episode_info(filepath)
    title = extract_title(content)
    
    return {
        'score': score,
        'title': title,
        'episode': info['episode'],
        'type': info['type'],
        'path': info['path'],
        'matches': matches[:5],  # 最多5个匹配上下文
        'word_count': len(content)
    }


def search_archive(query: str, archive_path: Path = None, 
                   show_type: str = 'all', limit: int = 10,
                   expand: bool = True) -> List[Dict]:
    """
    全文搜索存档
    
    Args:
        query: 搜索词（空格分隔）
        archive_path: 存档根目录
        show_type: 节目类型 (all/main/business/daily/opinion)
        limit: 返回数量上限
        expand: 是否扩展关键词
    
    Returns:
        匹配结果列表
    """
    if archive_path is None:
        archive_path = ARCHIVE_ROOT
    
    keywords = query.split()
    if expand:
        keywords = expand_keywords(keywords)
    
    print(f"🔍 搜索关键词: {', '.join(keywords[:10])}{'...' if len(keywords) > 10 else ''}")
    
    results = []
    
    # 确定搜索目录
    if show_type == 'all':
        search_dirs = ['main', 'business', 'daily', 'opinion', 'reference']
    else:
        search_dirs = [show_type]
    
    # 遍历搜索（递归搜索所有子目录）
    file_count = 0
    for dirname in search_dirs:
        dir_path = archive_path / dirname
        if not dir_path.exists():
            continue
        
        # 使用递归glob搜索所有层级的md文件
        for filepath in dir_path.rglob('*.md'):
            # 跳过目录索引文件（如 1-100.md, 501-600.md）
            if re.match(r'^\d+-\d+\.md$', filepath.name):
                continue
            file_count += 1
            result = search_file(filepath, keywords)
            if result:
                results.append(result)
    
    print(f"📁 扫描了 {file_count} 个文件，找到 {len(results)} 个匹配")
    
    # 按分数排序
    results.sort(key=lambda x: (-x['score'], -x['episode']))
    
    return results[:limit]


def print_results(results: List[Dict], query: str):
    """格式化输出搜索结果"""
    print(f"\n{'='*60}")
    print(f"📺 《睡前消息》历史节目搜索")
    print(f"🔍 查询: {query}")
    print(f"{'='*60}")
    
    if not results:
        print("\n❌ 未找到相关节目")
        print("\n💡 建议：")
        print("   - 尝试更宽泛的关键词")
        print("   - 使用同义词（如'独居'→'空巢'）")
        print("   - 搜索相关产业/领域")
        return
    
    for i, r in enumerate(results, 1):
        print(f"\n[{i}] 第{r['episode']}期 ({r['type']}) | 相关度: {r['score']}")
        print(f"    📌 {r['title'][:60]}{'...' if len(r['title']) > 60 else ''}")
        
        # 显示匹配上下文
        if r['matches']:
            print(f"    📝 匹配片段:")
            for m in r['matches'][:2]:
                context = m['context'][:80]
                # 高亮关键词
                print(f"       「{context}...」")
        
        print(f"    📂 {r['path']}")
    
    print(f"\n{'='*60}")
    print("💡 使用建议:")
    print("   1. 使用 view_file 查看完整内容")
    print("   2. 在蓝图中引用历史案例作为对比")
    print("   3. 提取历史节目中的论证结构复用")
    print("   4. 创建 [[wikilink]] 双链引用")


def deep_analyze(results: List[Dict], top_n: int = 3) -> List[Dict]:
    """
    对高分结果进行深度分析
    
    提取:
    - 核心论点（"所以"、"本质上"、"关键在于"等句式）
    - 论证结构（层层剥皮 / 对比分析 / 数据堆叠）
    - 可引用金句
    
    Args:
        results: 搜索结果列表
        top_n: 分析前N个高分结果
    
    Returns:
        带深度分析的结果列表
    """
    # 核心论点提取模式
    ARGUMENT_PATTERNS = [
        r'所以[，,]?([^。！？]{10,80})[。！？]',
        r'本质上[，,]?([^。！？]{10,80})[。！？]',
        r'关键在于[，,]?([^。！？]{10,80})[。！？]',
        r'真正的问题是[，,]?([^。！？]{10,80})[。！？]',
        r'换句话说[，,]?([^。！？]{10,80})[。！？]',
        r'这说明[，,]?([^。！？]{10,80})[。！？]',
        r'这意味着[，,]?([^。！？]{10,80})[。！？]',
        r'核心矛盾是[，,]?([^。！？]{10,80})[。！？]',
        r'根本原因是[，,]?([^。！？]{10,80})[。！？]',
        r'问题的本质是[，,]?([^。！？]{10,80})[。！？]',
    ]
    
    # 金句提取模式（反问/强调/总结）
    QUOTE_PATTERNS = [
        r'[^。！？]*[难道|为什么|怎么可能|凭什么][^。！？]*[？?]',  # 反问句
        r'这不是[^，,。！？]+[，,][^。！？]+[。！？]',  # 这不是...而是...
        r'不是[^，,。！？]+的问题[，,][^。！？]+[。！？]',  # 不是...的问题
        r'[^。！？]{5,}，而不是[^。！？]+[。！？]',  # ...而不是...
    ]
    
    # 论证结构标记
    STRUCTURE_MARKERS = {
        '层层剥皮': ['表面上', '深层', '本质上', '进一步', '更深层'],
        '对比分析': ['相比之下', '然而', '但是', '不同的是', 'A和B'],
        '数据堆叠': [r'\d+%', r'\d+亿', r'\d+万', '数据显示', '统计'],
        '历史类比': ['历史上', '当年', '曾经', '重演', '如出一辙'],
        '制度批判': ['制度', '法律', '规定', '政策', '体制'],
    }
    
    analyzed_results = []
    
    for result in results[:top_n]:
        filepath = Path(result['path'])
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            continue
        
        analysis = {
            **result,
            'core_arguments': [],
            'quotes': [],
            'structure': [],
            'summary': ''
        }
        
        # 提取核心论点
        for pattern in ARGUMENT_PATTERNS:
            matches = re.findall(pattern, content)
            for match in matches[:2]:  # 每个模式最多2个
                clean = match.strip()
                if len(clean) > 15 and clean not in analysis['core_arguments']:
                    analysis['core_arguments'].append(clean)
        
        # 限制核心论点数量
        analysis['core_arguments'] = analysis['core_arguments'][:5]
        
        # 提取金句
        for pattern in QUOTE_PATTERNS:
            matches = re.findall(pattern, content)
            for match in matches[:2]:
                clean = match.strip()
                if 15 < len(clean) < 100 and clean not in analysis['quotes']:
                    analysis['quotes'].append(clean)
        
        analysis['quotes'] = analysis['quotes'][:3]
        
        # 识别论证结构
        for structure_name, markers in STRUCTURE_MARKERS.items():
            count = 0
            for marker in markers:
                if re.search(marker, content):
                    count += 1
            if count >= 2:  # 至少出现2个标记词才认定
                analysis['structure'].append(structure_name)
        
        # 生成简要总结
        if analysis['core_arguments']:
            analysis['summary'] = f"核心论点: {analysis['core_arguments'][0][:50]}..."
        
        analyzed_results.append(analysis)
    
    return analyzed_results


def print_deep_results(results: List[Dict], query: str):
    """输出深度分析结果"""
    print(f"\n{'='*70}")
    print(f"🔬 《睡前消息》深度分析")
    print(f"🔍 查询: {query}")
    print(f"📊 分析了 {len(results)} 个高分结果")
    print(f"{'='*70}")
    
    for i, r in enumerate(results, 1):
        print(f"\n{'─'*70}")
        print(f"📺 [{i}] 第{r['episode']}期 | 相关度: {r['score']}")
        print(f"📌 {r['title'][:60]}")
        print(f"📂 {r['path']}")
        
        # 论证结构
        if r['structure']:
            print(f"\n🏗️  论证结构: {' + '.join(r['structure'])}")
        
        # 核心论点
        if r['core_arguments']:
            print(f"\n💡 核心论点:")
            for j, arg in enumerate(r['core_arguments'][:3], 1):
                print(f"   {j}. {arg[:70]}{'...' if len(arg) > 70 else ''}")
        
        # 金句
        if r['quotes']:
            print(f"\n✨ 可引用金句:")
            for quote in r['quotes'][:2]:
                print(f"   「{quote[:80]}{'...' if len(quote) > 80 else ''}」")
    
    print(f"\n{'='*70}")
    print("📋 深度分析完成")
    print("💡 建议:")
    print("   1. 复用论证结构到当前议题")
    print("   2. 引用金句增强说服力")
    print("   3. 核心论点可作为类比参考")
    print(f"{'='*70}")


def build_index(archive_path: Path = None) -> Dict:
    """构建搜索索引（用于加速后续搜索）"""
    if archive_path is None:
        archive_path = ARCHIVE_ROOT
    
    print("🔧 构建搜索索引...")
    
    index = {
        'version': '1.0',
        'built_at': datetime.now().isoformat(),
        'entries': []
    }
    
    for dirname in ['main', 'business', 'daily', 'opinion']:
        dir_path = archive_path / dirname
        if not dir_path.exists():
            continue
        
        for filepath in dir_path.glob('*.md'):
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                info = parse_episode_info(filepath)
                title = extract_title(content)
                
                # 提取关键词（简单分词）
                words = set(re.findall(r'[\u4e00-\u9fa5]{2,}', content))
                
                index['entries'].append({
                    'episode': info['episode'],
                    'type': info['type'],
                    'title': title,
                    'path': str(filepath),
                    'keywords': list(words)[:100]  # 最多100个关键词
                })
            except Exception as e:
                print(f"⚠️ 处理 {filepath} 失败: {e}")
    
    # 保存索引
    INDEX_CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_CACHE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 索引构建完成: {len(index['entries'])} 条目")
    print(f"📁 索引文件: {INDEX_CACHE}")
    
    return index


def main():
    parser = argparse.ArgumentParser(
        description='《睡前消息》文稿全文搜索',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python search_archive.py "死亡 焦虑"
  python search_archive.py "房地产 烂尾" --type main --limit 10
  python search_archive.py "数字遗产" --deep              # 深度分析Top 3
  python search_archive.py "教育" --deep --deep-n 5       # 深度分析Top 5
  python search_archive.py --build-index
        '''
    )
    parser.add_argument('query', nargs='?', help='搜索关键词（空格分隔）')
    parser.add_argument('--type', '-t', default='all',
                        choices=['all', 'main', 'business', 'daily', 'opinion'],
                        help='节目类型')
    parser.add_argument('--limit', '-l', type=int, default=10, help='返回数量上限')
    parser.add_argument('--no-expand', action='store_true', help='禁用关键词扩展')
    parser.add_argument('--archive', help='存档根目录')
    parser.add_argument('--build-index', action='store_true', help='构建搜索索引')
    parser.add_argument('--deep', '-d', action='store_true', 
                        help='深度分析模式：提取核心论点、论证结构、金句')
    parser.add_argument('--deep-n', type=int, default=3, 
                        help='深度分析的结果数量（默认3）')
    
    args = parser.parse_args()
    
    archive_path = Path(args.archive) if args.archive else ARCHIVE_ROOT
    
    if args.build_index:
        build_index(archive_path)
        return
    
    if not args.query:
        parser.print_help()
        return
    
    results = search_archive(
        args.query,
        archive_path=archive_path,
        show_type=args.type,
        limit=args.limit,
        expand=not args.no_expand
    )
    
    if args.deep and results:
        # 深度分析模式
        analyzed = deep_analyze(results, top_n=args.deep_n)
        print_deep_results(analyzed, args.query)
    else:
        # 普通搜索模式
        print_results(results, args.query)


if __name__ == "__main__":
    main()
