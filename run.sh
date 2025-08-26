#!/bin/bash

# 判断脚本是否在终端中运行
if [ ! -t 0 ]; then
    # 如果不是在终端中运行（比如双击），则使用终端模拟器重新运行此脚本
    if command -v x-terminal-emulator &> /dev/null; then
        # Debian/Ubuntu 系统
        exec x-terminal-emulator -e "$0" "$@"
    elif command -v gnome-terminal &> /dev/null; then
        # GNOME 桌面环境
        exec gnome-terminal -- "$0" "$@"
    elif command -v konsole &> /dev/null; then
        # KDE 桌面环境
        exec konsole -e "$0" "$@"
    elif command -v xfce4-terminal &> /dev/null; then
        # XFCE 桌面环境
        exec xfce4-terminal -e "$0" "$@"
    elif command -v xterm &> /dev/null; then
        # 几乎所有 X 系统都有 xterm
        exec xterm -e "$0" "$@"
    else
        echo "找不到终端模拟器，请在终端中运行此脚本"
        exit 1
    fi
fi

set -e
trap 'echo "发生错误，脚本终止"; exit 1' ERR
echo -e "\033]0;网易云批量下载器\007"

# 添加标志跟踪系统包是否已安装
SYSTEM_PACKAGES_INSTALLED=false

PKG_MANAGER=""
if command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
elif command -v yum &> /dev/null; then
    PKG_MANAGER="yum"
elif command -v pacman &> /dev/null; then
    PKG_MANAGER="pacman"
elif command -v zypper &> /dev/null; then
    PKG_MANAGER="zypper"
else
    echo "警告: 无法识别的包管理器，请手动安装 Python 3 和 python3-venv"
    if ! command -v python3 &> /dev/null; then
        echo "错误: 找不到 python3 命令，请先安装 Python 3"
        exit 1
    fi
fi

# 安装系统级 Python 包
install_system_packages() {
    # 如果已经安装过，则跳过
    if [ "$SYSTEM_PACKAGES_INSTALLED" = true ]; then
        echo "系统包已安装，跳过..."
        return
    fi
    
    echo "尝试通过系统包管理器安装依赖..."
    
    case $PKG_MANAGER in
        "apt")
            echo "使用 apt 安装系统级 Python 包..."
            sudo apt-get update
            sudo apt-get install -y python3-requests python3-pillow python3-pip python3-qrcode python3-venv python3-full python3-colorama python3-mutagen python3-selenium
            ;;
        "dnf"|"yum")
            echo "使用 ${PKG_MANAGER} 安装系统级 Python 包..."
            sudo $PKG_MANAGER install -y python3-requests python3-pillow python3-pip python3-qrcode python3-colorama python3-mutagen python3-selenium
            ;;
        "pacman")
            echo "使用 pacman 安装系统级 Python 包..."
            sudo pacman -Sy python-requests python-pillow python-pip python-qrcode  python-colorama python-mutagen python-selenium 
            ;;
        "zypper")
            echo "使用 zypper 安装系统级 Python 包..."
            sudo zypper install -y python3-requests python3-Pillow python3-pip python3-qrcode python3-colorama python3-mutagen python3-selenium 
            ;;
        *)
            echo "警告: 未知的包管理器，无法安装系统级 Python 包"
            ;;
    esac
    
    SYSTEM_PACKAGES_INSTALLED=true
}

echo "检查必要的依赖..."

# 1. 首先检查Python和pip是否安装
if ! command -v python3 &> /dev/null; then
    echo "未检测到 Python 3，尝试安装..."
    case $PKG_MANAGER in
        "apt")
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip
            ;;
        "dnf")
            sudo dnf install -y python3 python3-pip
            ;;
        "yum")
            sudo yum install -y python3 python3-pip
            ;;
        "pacman")
            sudo pacman -Sy python python-pip
            ;;
        "zypper")
            sudo zypper install -y python3 python3-pip
            ;;
    esac
fi

# 2. 检查是否支持venv
VENV_SUPPORTED=true
if ! python3 -c "import venv" &> /dev/null; then
    echo "未检测到 venv 模块，尝试安装..."
    case $PKG_MANAGER in
        "apt")
            sudo apt-get install -y python3-venv python3-full || VENV_SUPPORTED=false
            ;;
        "dnf")
            sudo dnf install -y python3-venv || VENV_SUPPORTED=false
            ;;
        "yum")
            sudo yum install -y python3-venv || VENV_SUPPORTED=false
            ;;
        "pacman")
            sudo pacman -Sy python-virtualenv || VENV_SUPPORTED=false
            ;;
        "zypper")
            sudo zypper install -y python3-virtualenv || VENV_SUPPORTED=false
            ;;
        *)
            VENV_SUPPORTED=false
            ;;
    esac
    
    # 再次检查venv是否可用
    if ! python3 -c "import venv" &> /dev/null; then
        VENV_SUPPORTED=false
    fi
fi

# 3. 如果支持venv，优先使用虚拟环境
if [ "$VENV_SUPPORTED" = true ]; then
    VENV_DIR="venv"
    if [ ! -d "$VENV_DIR" ]; then
        echo "创建虚拟环境，这可能需要一段时间，并且只需要执行一次..."
        # 修复虚拟环境创建命令
        python3 -m venv "$VENV_DIR" || {
            echo "虚拟环境创建失败，尝试使用系统 Python..."
            VENV_SUPPORTED=false
        }
    fi

    if [ -f "$VENV_DIR/bin/activate" ] && [ "$VENV_SUPPORTED" = true ]; then
        echo "激活虚拟环境..."
        source "$VENV_DIR/bin/activate" || { 
            echo "激活虚拟环境失败，使用系统 Python"; 
            VENV_SUPPORTED=false
        }
        
        if [ "$VENV_SUPPORTED" = true ]; then
            # 在虚拟环境中安装依赖
            echo "检查虚拟环境中的依赖..."
            if ! python -c "import pyncm" > /dev/null 2>&1; then
                echo "安装依赖..."
                pip install -r requirements.txt 2>&1 || {
                    echo "警告: 无法安装部分依赖，脚本可能无法正常运行"
                }
            fi
            
            echo "运行脚本..."
            if [ -f "script.py" ]; then
                clear
                python script.py
            else
                echo "错误: script.py 文件不存在"
                deactivate
                exit 1
            fi
            
            deactivate
            echo "按回车键退出..."
            read
            exit 0
        fi
    else
        echo "虚拟环境创建不完整，将使用系统Python继续..."
        VENV_SUPPORTED=false
    fi
fi

# 4. 如果不支持venv或虚拟环境创建/激活失败，使用系统Python
if [ "$VENV_SUPPORTED" = false ]; then
    echo "将使用系统 Python..."
    # 检查全局是否已安装必要的包
    if ! python3 -c "import pyncm" > /dev/null 2>&1 || \
       ! python3 -c "import requests" > /dev/null 2>&1 || \
       ! python3 -c "import PIL" > /dev/null 2>&1 || \
       ! python3 -c "import qrcode" > /dev/null 2>&1 || \
       ! python3 -c "import mutagen" > /dev/null 2>&1; then
        
        echo "系统中缺少必要的Python包..."
        # 先尝试使用pip安装
        if pip install --user -r requirements.txt > /dev/null 2>&1; then
            echo "已成功通过pip安装所需包"
        else
            echo "pip安装失败，尝试使用系统包管理器安装..."
            install_system_packages
            
            # 再次尝试安装pyncm（因为系统包可能没有）
            pip install --user pyncm mutagen selenium > /dev/null 2>&1 || {
                echo "尝试系统级安装..."
                pip install -r requirements.txt --break-system-packages || {
                    echo "警告: 无法安装pyncm，脚本可能无法正常运行"
                }
            }
        fi
    fi
    
    echo "运行脚本（使用系统 Python）..."
    if [ -f "script.py" ]; then
        clear
        python3 script.py
    else
        echo "错误: script.py 文件不存在"
        exit 1
    fi
    
    echo "按回车键退出..."
    read
    exit 0
fi
