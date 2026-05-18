param (
    [string]$Topic,
    [string]$Category = "Uncategorized",
    [string]$Date = $(Get-Date -Format "yyyyMMdd"),
    [switch]$NoVisual  # 跳过可视化生成
)

# 1. Define Paths
$WorkspaceRoot = Get-Location
# v15.2: 从 skills 目录读取产物（迁移后的新路径）
$OutputDir = Join-Path $WorkspaceRoot ".agent\skills\bedtime-news\output"
$SourceScript = Join-Path $OutputDir "broadcast_script.md"
$SourceBlueprint = Join-Path $OutputDir "analysis_blueprint.md"
# 归档到用户指定的 Obsidian Vault 目录
$ArchiveRoot = "D:\a1114\aaa111\bedtime_news_archive"
$VisualScript = Join-Path $WorkspaceRoot ".agent\skills\bedtime-news\scripts\generate_visual.py"

# 2. Sanitize Filename
$SafeTopic = $Topic -replace '[\\/:*?"<>|]', '' -replace '\s+', '_'
$TargetFolder = Join-Path $ArchiveRoot "$Category"
$TargetSubFolder = Join-Path $TargetFolder "${Date}_${SafeTopic}"

# 3. Create Directories
if (-not (Test-Path $TargetFolder)) {
    New-Item -ItemType Directory -Path $TargetFolder -Force | Out-Null
    Write-Host "Created Category Folder: $Category"
}
if (-not (Test-Path $TargetSubFolder)) {
    New-Item -ItemType Directory -Path $TargetSubFolder -Force | Out-Null
    Write-Host "Created Topic Folder: $SafeTopic"
}

# 4. Copy Core Files
if (Test-Path $SourceScript) {
    Copy-Item $SourceScript -Destination (Join-Path $TargetSubFolder "Script.md") -Force
    Write-Host "Archived Script"
}
if (Test-Path $SourceBlueprint) {
    Copy-Item $SourceBlueprint -Destination (Join-Path $TargetSubFolder "Blueprint.md") -Force
    Write-Host "Archived Blueprint"
}

# 5. Generate Visualizations (new feature)
if (-not $NoVisual) {
    if ((Test-Path $SourceBlueprint) -and (Test-Path $VisualScript)) {
        Write-Host ""
        Write-Host "Generating Visualizations..."
        try {
            python $VisualScript --blueprint $SourceBlueprint --output $TargetSubFolder --topic $Topic --format both
            Write-Host "Visualization files generated"
        }
        catch {
            Write-Host "Warning: Could not generate visualizations - $_"
        }
    }
    else {
        Write-Host "Skipping visualization: Blueprint or script not found"
    }
}

# 6. Create Index Entry (for Obsidian linking)
# 原节目归档目录
$OriginalArchive = "D:\a1114\aaa111\睡前消息归档"

$IndexEntry = @"
---
topic: $Topic
category: $Category
date: $Date
created: $(Get-Date -Format "yyyy-MM-dd HH:mm")
original_archive: $OriginalArchive
---

# $Topic

[[Script|口播文稿]] | [[Blueprint|分析蓝图]] | [[${SafeTopic}_论证链条|论证可视化]]

## 核心结论
<!-- 请手动填写或由AI补充 -->

## 历史双链
<!-- 引用原节目时使用以下格式 -->
<!-- [[睡前消息归档/第XXX期|第XXX期：标题]] -->

**原节目库路径**: ``$OriginalArchive``

> 💡 在Obsidian中，使用 `[[睡前消息归档/第XXX期]]` 链接到原节目
"@

$IndexPath = Join-Path $TargetSubFolder "README.md"
$IndexEntry | Out-File -FilePath $IndexPath -Encoding utf8
Write-Host "Created Index: README.md"

Write-Host ""
Write-Host "Archiving Complete: $TargetSubFolder"
Write-Host "Original Archive: $OriginalArchive"
Write-Host "Files:"
Get-ChildItem $TargetSubFolder | ForEach-Object { Write-Host "  - $($_.Name)" }

