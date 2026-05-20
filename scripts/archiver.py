#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《睡前消息》归档与可视化触发脚本 (Python 替代版，解决 PowerShell 编码问题)
用法: python archiver.py --topic "议题" --category "社会" [--date "20260519"] [--no-visual]
"""

import os
import sys
import shutil
import re
import argparse
from datetime import datetime

def sanitize_filename(name: str) -> str:
    # 移除 Windows 文件名非法字符
    sanitized = re.sub(r'[\\/:*?"<>|]', '', name)
    # 将空格替换为下划线
    sanitized = re.sub(r'\s+', '_', sanitized)
    return sanitized

def main():
    parser = argparse.ArgumentParser(description="睡前消息归档工具")
    parser.add_argument("--topic", required=True, help="议题名称")
    parser.add_argument("--category", default="Uncategorized", help="归档分类")
    parser.add_argument("--date", default=datetime.now().strftime("%Y%m%d"), help="归档日期")
    parser.add_argument("--no-visual", action="store_true", help="跳过可视化生成")
    
    args = parser.parse_args()
    
    # 1. 定义路径
    workspace_root = os.getcwd()
    output_dir = os.path.join(workspace_root, ".agent", "skills", "bedtime-news", "output")
    source_script = os.path.join(output_dir, "broadcast_script.md")
    source_blueprint = os.path.join(output_dir, "analysis_blueprint.md")
    
    archive_root = r"D:\a1114\aaa111\bedtime_news_archive"
    visual_script = os.path.join(workspace_root, ".agent", "skills", "bedtime-news", "scripts", "generate_visual.py")
    
    # 2. 净化文件名与目标目录
    safe_topic = sanitize_filename(args.topic)
    target_folder = os.path.join(archive_root, args.category)
    target_subfolder = os.path.join(target_folder, f"{args.date}_{safe_topic}")
    
    # 3. 创建目录
    if not os.path.exists(target_folder):
        os.makedirs(target_folder, exist_ok=True)
        print(f"Created Category Folder: {args.category}")
        
    if not os.path.exists(target_subfolder):
        os.makedirs(target_subfolder, exist_ok=True)
        print(f"Created Topic Folder: {safe_topic}")
        
    # 4. 拷贝核心文件（如果 output 下存在，拷贝；如果不存在，假定已直接在目标目录创建）
    if os.path.exists(source_script):
        shutil.copy2(source_script, os.path.join(target_subfolder, "Script.md"))
        print("Archived Script from Output")
        
    if os.path.exists(source_blueprint):
        shutil.copy2(source_blueprint, os.path.join(target_subfolder, "Blueprint.md"))
        print("Archived Blueprint from Output")
        
    target_blueprint = os.path.join(target_subfolder, "Blueprint.md")
    
    # 5. 生成可视化
    if not args.no_visual:
        if os.path.exists(target_blueprint) and os.path.exists(visual_script):
            print("\nGenerating Visualizations...")
            try:
                # 调用已有的 generate_visual.py
                import subprocess
                cmd = [
                    sys.executable,
                    visual_script,
                    "--blueprint", target_blueprint,
                    "--output", target_subfolder,
                    "--topic", args.topic,
                    "--format", "both"
                ]
                subprocess.run(cmd, check=True)
                print("Visualization files generated")
            except Exception as e:
                print(f"Warning: Could not generate visualizations - {e}", file=sys.stderr)
        else:
            print(f"Skipping visualization: Blueprint not found at {target_blueprint}")
            
    # 6. 生成索引文件 README.md (以完美 UTF-8 无 BOM 写入，解决乱码)
    original_archive = r"D:\a1114\aaa111\睡前消息归档"
    created_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    index_content = f"""---
topic: {args.topic}
category: {args.category}
date: {args.date}
created: {created_time}
original_archive: {original_archive}
---

# {args.topic}

[[Script|口播文稿]] | [[Blueprint|分析蓝图]] | [[{safe_topic}_论证链条|论证可视化]]

## 核心结论
<!-- 请手动填写或由AI补充 -->

## 历史双链
<!-- 引用原节目时使用以下格式 -->
<!-- [[睡前消息归档/第XXX期|第XXX期：标题]] -->

**原节目库路径**: `{original_archive}`

> 💡 在Obsidian中，使用 `[[睡前消息归档/第XXX期]]` 链接到原节目
"""
    
    index_path = os.path.join(target_subfolder, "README.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)
    print("Created Index: README.md")
    
    print(f"\nArchiving Complete: {target_subfolder}")
    print(f"Original Archive: {original_archive}")
    print("Files:")
    for item in os.listdir(target_subfolder):
        print(f"  - {item}")

if __name__ == "__main__":
    main()
