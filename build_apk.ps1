<#
.SYNOPSIS
    综合政务管理 APP - APK 一键构建脚本
.DESCRIPTION
    自动检查环境依赖并调用 buildozer 编译 Android APK
    支持 Linux (WSL/Ubuntu) 和 GitHub Codespaces
.NOTES
    需要: Python 3.11+, Buildozer, Java 17, Android SDK
    建议在 Ubuntu 22.04 / WSL2 中运行
#>

$ErrorActionPreference = "Stop"
$PROJECT_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $PROJECT_ROOT

function Write-Step($msg) {
    Write-Host "`n==> $msg" -ForegroundColor Cyan
}

function Write-OK($msg) {
    Write-Host "  [✓] $msg" -ForegroundColor Green
}

function Write-Warn($msg) {
    Write-Host "  [!] $msg" -ForegroundColor Yellow
}

function Write-Err($msg) {
    Write-Host "  [✗] $msg" -ForegroundColor Red
}

# ============================================
# 检测是否为 Linux 环境（WSL 或原生）
# ============================================
$isLinux = $IsLinux -or (uname -o 2>$null) -eq "GNU/Linux"

if (-not $isLinux) {
    Write-Warn "当前环境: Windows (PowerShell)"
    Write-Warn "Buildozer 在 Windows 上无法直接运行。"
    Write-Warn "请使用 WSL2 或 GitHub Codespaces 构建。"
    Write-Warn ""
    Write-Warn "WSL2 快速构建命令:"
    Write-Warn "  wsl --install -d Ubuntu"
    Write-Warn "  wsl"
    Write-Warn "  cd /mnt/f/自己做的软件/赶街的/mygov_app"
    Write-Warn "  ./build_apk.sh"
    Write-Host ""
    $choice = Read-Host "是否尝试在 WSL 中执行? (y/n)"
    if ($choice -eq 'y') {
        $wslDistro = (wsl -l -q 2>$null) -split "`n" | Select-Object -First 1
        if ($wslDistro) {
            Write-OK "找到 WSL 发行版: $wslDistro"
            wsl -d $wslDistro --cd $PROJECT_ROOT ./build_apk.sh
            exit $LASTEXITCODE
        } else {
            Write-Err "WSL 未安装。请先安装 WSL。"
            exit 1
        }
    }
    exit 0
}

# ============================================
# Linux 构建流程
# ============================================
Write-Step "1/5 — 安装系统依赖"
$sysDeps = @(
    "python3-pip", "python3-setuptools", "python3-dev",
    "git", "zip", "unzip", "build-essential", "ccache",
    "autoconf", "libtool", "pkg-config", "zlib1g-dev",
    "libncurses5-dev", "libncursesw5-dev", "libtinfo5",
    "cmake", "libffi-dev", "libssl-dev"
)

$missing = @()
foreach ($pkg in $sysDeps) {
    $check = dpkg -l $pkg 2>$null
    if (-not $check) { $missing += $pkg }
}

if ($missing.Count -gt 0) {
    Write-Host "  安装: $($missing -join ' ')"
    sudo apt update -qq
    sudo apt install -y $missing
    Write-OK "系统依赖已安装"
} else {
    Write-OK "系统依赖已满足"
}

Write-Step "2/5 — 安装 Python 依赖"
$pipPackages = @("buildozer", "cython", "virtualenv", "setuptools", "wheel")
pip install --upgrade pip
pip install $pipPackages
Write-OK "Python 依赖已安装"

Write-Step "3/5 — 清理旧构建缓存"
if (Test-Path ".buildozer") {
    Remove-Item -Recurse -Force ".buildozer" -ErrorAction SilentlyContinue
    Write-OK "旧缓存已清理"
} else {
    Write-OK "无需清理"
}

Write-Step "4/5 — 构建 APK"
Write-Host "  编译中（首次构建约 30-60 分钟，后续约 5 分钟）..." -ForegroundColor Yellow
python -m buildozer android debug 2>&1 | Tee-Object -FilePath "build_log.txt"

if ($LASTEXITCODE -ne 0) {
    Write-Err "构建失败！查看 build_log.txt 获取详情"
    exit 1
}

Write-Step "5/5 — 完成"
$apkFiles = Get-ChildItem -Path "bin" -Filter "*.apk" | Sort-Object LastWriteTime -Descending
if ($apkFiles) {
    $apk = $apkFiles[0]
    $sizeMB = [math]::Round($apk.Length / 1MB, 2)
    Write-OK "APK: $($apk.Name) ($sizeMB MB)"
    Write-OK "路径: $($apk.FullName)"
} else {
    Write-Warn "未找到 APK 文件，请检查 bin/ 目录"
}

Write-Host "`n=== 构建完成 ===" -ForegroundColor Green
