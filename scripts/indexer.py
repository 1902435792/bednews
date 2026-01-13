import os
import re
import json
import argparse
from datetime import datetime

# Expanded Keyword Dictionary
KEYWORDS = {
    '地产': ['房', '烂尾', '恒大', '融创', '碧桂园', '土地', '房价', '物业', '业主', '拆迁'],
    '教育': ['大学', '高考', '衡水', '教材', '小学', '教师', '教培', '双减', '考研'],
    '债务': ['债', '城投', '独山', '利息', '破产', '违约', '融资', '专项债'],
    '国际': ['美国', '日本', '俄罗斯', '普京', '拜登', '特朗普', '乌克兰', '以色列', '欧洲', '印度'],
    '科技': ['芯片', 'AI', '华为', '新能源', '电动车', '比亚迪', '半导体', '甚至', '太空'],
    '社会': ['生育', '养老', '医保', '就业', '考公', '治安', '刑讯', '延迟退休', '人口'],
    '法律': ['法', '判决', '律师', '公安', '宪法', '修正案', '刑法'],
    '历史': ['明朝', '清朝', '民国', '抗战', '苏联', '文革', '改革开放', '建国'],
    '工业': ['工厂', '制造', '产能', '供应链', '出口', '外贸', '基建']
}

def parse_frontmatter(content):
    """
    Extracts YAML-like frontmatter including description.
    """
    meta = {}
    frontmatter_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if frontmatter_match:
        frontmatter = frontmatter_match.group(1)
        
        # Title
        title_match = re.search(r'title:\s*(.*)', frontmatter)
        if title_match:
            meta['title'] = title_match.group(1).strip()
        
        # Date
        date_match = re.search(r'date:\s*(.*)', frontmatter)
        if date_match:
            meta['date'] = date_match.group(1).strip()
            
        # Description (Critical for optimization)
        desc_match = re.search(r'description:\s*(.*)', frontmatter)
        if desc_match:
            desc = desc_match.group(1).strip()
            if desc and desc.lower() != 'null':
                meta['description'] = desc
    return meta

def extract_body_abstract(content):
    """
    Extracts the first 200 characters of the body text (skipping frontmatter and headers).
    """
    # Remove frontmatter
    body = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
    # Remove Headers
    body = re.sub(r'#+\s.*', '', body)
    # Remove Links/Images
    body = re.sub(r'!\[.*?\]\(.*?\)', '', body)
    body = re.sub(r'\[.*?\]\(.*?\)', '', body)
    # Trim whitespace
    body = body.strip()
    return body[:200] + '...' if len(body) > 200 else body

def extract_episode_id(filename, title):
    base = os.path.basename(filename)
    name_part = os.path.splitext(base)[0]
    if name_part.isdigit():
        return name_part
    if title:
        ep_match = re.search(r'【睡前消息(\d+)】', title)
        if ep_match:
            return ep_match.group(1)
        ep_match = re.search(r'^(\d+)', title)
        if ep_match:
            return ep_match.group(1)
    return name_part

def generate_tags(text):
    """
    Scans the provided text (Title + Description + Body) for keywords.
    """
    tags = set()
    for tag_category, keys in KEYWORDS.items():
        if any(k in text for k in keys):
            tags.add(tag_category)
    return list(tags)

def index_archive(archive_root, output_file):
    index = []
    main_dir = os.path.join(archive_root, 'main')
    
    if not os.path.exists(main_dir):
        print(f"Error: {main_dir} not found.")
        return

    print(f"Scanning {main_dir} with advanced options...")
    
    for root, dirs, files in os.walk(main_dir):
        for file in files:
            if file.endswith('.md'):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    meta = parse_frontmatter(content)
                    title = meta.get('title', '')
                    date_str = meta.get('date', '')
                    description = meta.get('description', '')
                    
                    if not title:
                        continue 
                        
                    if re.match(r'^\d+-\d+\.md$', file):
                        continue

                    ep_id = extract_episode_id(file, title)
                    
                    # Optimization: Fallback to abstract if no description
                    if not description:
                        description = extract_body_abstract(content)
                    
                    # Optimization: Scan full content for better tags
                    full_text = f"{title} {description} {content}"
                    tags = generate_tags(full_text)
                    
                    rel_path = os.path.relpath(full_path, archive_root).replace('\\', '/')
                    
                    entry = {
                        'id': ep_id,
                        'title': title,
                        'date': date_str,
                        'description': description, # Added field
                        'tags': tags,
                        'path': rel_path
                    }
                    index.append(entry)
                    
                except Exception as e:
                    print(f"Skipping {file}: {e}")

    # Sort
    try:
        index.sort(key=lambda x: int(x['id']) if x['id'].isdigit() else 0, reverse=True)
    except:
        pass

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
        
    print(f"Optimized Index created {len(index)} episodes to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, help='Archive root directory')
    parser.add_argument('--out', required=True, help='Output JSON file')
    args = parser.parse_args()
    
    index_archive(args.root, args.out)
