#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generate_visual.py - 《睡前消息》归档可视化生成脚本

从分析蓝图中提取论证链条，生成 Mermaid 图表和 Obsidian Canvas。
整合自 axton-obsidian-visual-skills。

用法:
    python generate_visual.py --blueprint <path> --output <dir> [--format mermaid|canvas|both]
"""

import argparse
import json
import re
import os
from datetime import datetime
from pathlib import Path


def extract_argument_chain(blueprint_path: str) -> dict:
    """从分析蓝图中提取论证链条"""
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取核心定义
    core_def_match = re.search(r'\*\*不是[^，]+，而是[^。\*]+', content)
    core_definition = core_def_match.group(0) if core_def_match else "核心定义"
    
    # 提取论证层次
    layers = []
    layer_pattern = r'###\s*第(\w+)层[：:]\s*(.+?)(?=###|---|\Z)'
    layer_matches = re.findall(layer_pattern, content, re.DOTALL)
    
    for level, layer_content in layer_matches:
        # 提取要点
        points = re.findall(r'-\s+(.+?)(?:\[搜索验证\]|\[常识\]|\[理论框架\]|\[分析\])?(?:\n|$)', layer_content)
        layers.append({
            'level': level,
            'points': [p.strip() for p in points[:3]]  # 每层最多3个要点
        })
    
    # 提取核心悖论
    paradoxes = []
    paradox_pattern = r'\*\*悖论\d+[：:]\s*(.+?)\*\*'
    paradox_matches = re.findall(paradox_pattern, content)
    paradoxes = paradox_matches[:3]  # 最多3个悖论
    
    # 提取方案
    solutions = []
    solution_pattern = r'\*\*第[一二三]，(.+?)\*\*'
    solution_matches = re.findall(solution_pattern, content)
    solutions = solution_matches[:3]
    
    return {
        'core_definition': core_definition,
        'layers': layers,
        'paradoxes': paradoxes,
        'solutions': solutions
    }


def sanitize_mermaid_text(text: str, max_len: int = 30) -> str:
    """清理文本以确保Mermaid语法兼容"""
    # 移除Mermaid不兼容的字符
    text = text.replace('"', '')
    text = text.replace("'", '')
    text = text.replace('*', '')
    text = text.replace('[', '『')
    text = text.replace(']', '』')
    text = text.replace('(', '「')
    text = text.replace(')', '」')
    text = text.replace('，', ' ')
    text = text.replace('：', ':')
    text = text.replace('；', ' ')
    # 截断
    if len(text) > max_len:
        text = text[:max_len] + "..."
    return text.strip()


def generate_mermaid(data: dict, topic: str) -> str:
    """生成 Mermaid 流程图"""
    
    # 清理核心定义
    core_def = sanitize_mermaid_text(data['core_definition'], 25)
    
    mermaid = f"""```mermaid
graph TB
    %% 《睡前消息》论证链条可视化
    %% 议题: {topic}
    %% 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    
    %% 样式定义
    classDef core fill:#e7f5ff,stroke:#1971c2,stroke-width:2px
    classDef layer1 fill:#d3f9d8,stroke:#2f9e44
    classDef layer2 fill:#fff4e6,stroke:#e67700
    classDef layer3 fill:#ffe3e3,stroke:#c92a2a
    classDef layer4 fill:#e5dbff,stroke:#5f3dc4
    classDef layer5 fill:#c5f6fa,stroke:#0c8599
    classDef paradox fill:#f3d9fa,stroke:#862e9c
    classDef solution fill:#d3f9d8,stroke:#2f9e44,stroke-width:2px
    
    %% 核心定义
    Core[{core_def}]:::core
"""
    
    # 添加论证层次
    layer_styles = ['layer1', 'layer2', 'layer3', 'layer4', 'layer5']
    prev_node = 'Core'
    
    for i, layer in enumerate(data['layers'][:5]):
        layer_id = f"L{i+1}"
        style = layer_styles[i] if i < len(layer_styles) else 'layer1'
        
        # 创建层节点
        layer_title = f"第{layer['level']}层"
        mermaid += f"    {layer_id}[{layer_title}]:::{style}\n"
        mermaid += f"    {prev_node} --> {layer_id}\n"
        
        # 添加要点（最多2个）
        for j, point in enumerate(layer['points'][:2]):
            point_id = f"P{i+1}{j+1}"
            point_text = sanitize_mermaid_text(point, 28)
            mermaid += f"    {point_id}[{point_text}]:::{style}\n"
            mermaid += f"    {layer_id} --> {point_id}\n"
        
        prev_node = layer_id
    
    # 添加核心悖论
    if data['paradoxes']:
        mermaid += "\n    %% 核心悖论\n"
        mermaid += f"    subgraph paradox[核心悖论]\n"
        for i, p in enumerate(data['paradoxes'][:2]):
            paradox_text = sanitize_mermaid_text(p, 32)
            mermaid += f"        Paradox{i+1}[{paradox_text}]:::paradox\n"
        mermaid += "    end\n"
        mermaid += f"    {prev_node} -.-> paradox\n"
    
    # 添加解决方案
    if data['solutions']:
        mermaid += "\n    %% 方案钩子\n"
        mermaid += f"    subgraph solutions[方案]\n"
        for i, s in enumerate(data['solutions'][:3]):
            sol_text = sanitize_mermaid_text(s, 28)
            mermaid += f"        Sol{i+1}[{sol_text}]:::solution\n"
        mermaid += "    end\n"
        mermaid += "    paradox -.-> solutions\n"
    
    mermaid += "```"
    return mermaid


def generate_canvas(data: dict, topic: str) -> dict:
    """生成 Obsidian Canvas JSON"""
    
    nodes = []
    edges = []
    
    x, y = 0, 0
    node_width = 300
    node_height = 80
    spacing_x = 350
    spacing_y = 120
    
    # 核心定义节点
    core_id = "core"
    nodes.append({
        "id": core_id,
        "type": "text",
        "text": f"## 核心定义\n{data['core_definition']}",
        "x": x,
        "y": y,
        "width": node_width + 100,
        "height": node_height + 20,
        "color": "1"  # 蓝色
    })
    
    prev_id = core_id
    y += spacing_y + 50
    
    # 论证层次
    for i, layer in enumerate(data['layers'][:5]):
        layer_id = f"layer_{i+1}"
        layer_text = f"### 第{layer['level']}层\n" + "\n".join([f"- {p[:50]}" for p in layer['points'][:3]])
        
        colors = ["4", "6", "2", "5", "3"]  # 绿/青/红/紫/橙
        
        nodes.append({
            "id": layer_id,
            "type": "text",
            "text": layer_text,
            "x": x,
            "y": y,
            "width": node_width,
            "height": node_height + 40,
            "color": colors[i % len(colors)]
        })
        
        edges.append({
            "id": f"edge_{prev_id}_{layer_id}",
            "fromNode": prev_id,
            "fromSide": "bottom",
            "toNode": layer_id,
            "toSide": "top"
        })
        
        prev_id = layer_id
        y += spacing_y
    
    # 悖论节点（右侧）
    if data['paradoxes']:
        paradox_id = "paradoxes"
        paradox_text = "## 核心悖论\n" + "\n".join([f"**{i+1}.** {p[:40]}" for i, p in enumerate(data['paradoxes'][:3])])
        
        nodes.append({
            "id": paradox_id,
            "type": "text",
            "text": paradox_text,
            "x": x + spacing_x,
            "y": y - spacing_y * 2,
            "width": node_width,
            "height": node_height + 60,
            "color": "5"  # 紫色
        })
        
        edges.append({
            "id": f"edge_{prev_id}_{paradox_id}",
            "fromNode": prev_id,
            "fromSide": "right",
            "toNode": paradox_id,
            "toSide": "left",
            "label": "揭示"
        })
    
    # 方案节点（底部）
    if data['solutions']:
        sol_id = "solutions"
        sol_text = "## 方案\n" + "\n".join([f"{i+1}. {s[:40]}" for i, s in enumerate(data['solutions'][:3])])
        
        nodes.append({
            "id": sol_id,
            "type": "text",
            "text": sol_text,
            "x": x,
            "y": y + 50,
            "width": node_width + 50,
            "height": node_height + 50,
            "color": "4"  # 绿色
        })
        
        edges.append({
            "id": f"edge_{prev_id}_{sol_id}",
            "fromNode": prev_id,
            "fromSide": "bottom",
            "toNode": sol_id,
            "toSide": "top",
            "label": "引出"
        })
    
    return {
        "nodes": nodes,
        "edges": edges
    }


def save_outputs(mermaid_content: str, canvas_data: dict, output_dir: str, topic: str, format_type: str):
    """保存输出文件"""
    os.makedirs(output_dir, exist_ok=True)
    
    safe_topic = re.sub(r'[\\/:*?"<>|]', '_', topic)
    
    if format_type in ['mermaid', 'both']:
        mermaid_path = os.path.join(output_dir, f"{safe_topic}_论证链条.md")
        with open(mermaid_path, 'w', encoding='utf-8') as f:
            f.write(f"# {topic} - 论证链条可视化\n\n")
            f.write(mermaid_content)
        print(f"✅ Mermaid 图表已保存: {mermaid_path}")
    
    if format_type in ['canvas', 'both']:
        canvas_path = os.path.join(output_dir, f"{safe_topic}_论证链条.canvas")
        with open(canvas_path, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Canvas 文件已保存: {canvas_path}")


def main():
    parser = argparse.ArgumentParser(description='《睡前消息》归档可视化生成')
    parser.add_argument('--blueprint', '-b', required=True, help='分析蓝图文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出目录')
    parser.add_argument('--topic', '-t', default='议题', help='议题名称')
    parser.add_argument('--format', '-f', choices=['mermaid', 'canvas', 'both'], default='both', help='输出格式')
    
    args = parser.parse_args()
    
    print(f"\n🎨 《睡前消息》可视化生成器")
    print(f"=" * 50)
    print(f"📄 蓝图文件: {args.blueprint}")
    print(f"📁 输出目录: {args.output}")
    print(f"📌 议题: {args.topic}")
    print(f"📊 格式: {args.format}")
    print()
    
    # 提取数据
    data = extract_argument_chain(args.blueprint)
    print(f"📊 提取到 {len(data['layers'])} 个论证层次")
    print(f"💡 提取到 {len(data['paradoxes'])} 个核心悖论")
    print(f"🎯 提取到 {len(data['solutions'])} 个解决方案")
    print()
    
    # 生成可视化
    mermaid_content = generate_mermaid(data, args.topic)
    canvas_data = generate_canvas(data, args.topic)
    
    # 保存
    save_outputs(mermaid_content, canvas_data, args.output, args.topic, args.format)
    
    print(f"\n✨ 可视化生成完成!")


if __name__ == "__main__":
    main()
