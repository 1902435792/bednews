# update_archive.ps1 - 自动更新睡前消息文稿库
# 可以手动运行，也可以通过 Windows 任务计划程序定时执行

param (
    [string]$ArchivePath = "$PSScriptRoot\..\archive",
    [string]$LogFile = "$PSScriptRoot\..\data\update_log.txt"
)

# 日志函数
function Log {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry -Encoding UTF8
}

# 确保日志目录存在
$LogDir = Split-Path $LogFile
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

Log "========== 开始更新 =========="

# 检查 archive 目录
if (-not (Test-Path $ArchivePath)) {
    Log "⚠️ archive 目录不存在，正在克隆..."
    git clone --depth 1 https://github.com/bedtimenews/bedtimenews-archive-contents.git $ArchivePath
    if ($LASTEXITCODE -eq 0) {
        Log "✅ 克隆完成"
    }
    else {
        Log "❌ 克隆失败"
        exit 1
    }
}
else {
    Log "📁 archive 目录: $ArchivePath"
    
    # 进入目录并拉取更新
    Push-Location $ArchivePath
    
    # 获取更新前的 commit
    $BeforeCommit = git rev-parse HEAD 2>$null
    
    Log "🔄 正在拉取更新..."
    git pull --ff-only
    
    if ($LASTEXITCODE -eq 0) {
        $AfterCommit = git rev-parse HEAD
        
        if ($BeforeCommit -eq $AfterCommit) {
            Log "✅ 已是最新版本"
        }
        else {
            # 统计更新的文件
            $ChangedFiles = git diff --name-only $BeforeCommit $AfterCommit | Measure-Object | Select-Object -ExpandProperty Count
            Log "✅ 更新成功，更新了 $ChangedFiles 个文件"
        }
    }
    else {
        Log "❌ 拉取失败，尝试重置..."
        git fetch origin
        git reset --hard origin/main
        Log "✅ 已重置到最新版本"
    }
    
    Pop-Location
}

Log "========== 更新完成 =========="
