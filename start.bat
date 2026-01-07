@echo off
REM 快速启动脚本 for Windows
chcp 65001 > nul

echo ╔══════════════════════════════════════════╗
echo ║        Boss Detect - 老板探测器          ║
echo ╚══════════════════════════════════════════╝
echo.

REM 检查配置文件
if not exist "config.ini" (
    echo ❌ 配置文件不存在！
    echo 正在创建配置文件...
    copy config.ini.example config.ini > nul
    echo ✅ 已创建 config.ini，请编辑该文件并填写必要信息
    echo.
    echo 必填项：
    echo   - boss_mac: 老板手机的MAC地址
    echo   - pushdeer_key: PushDeer推送Key (从 https://www.pushdeer.com 获取)
    echo.
    pause
    exit /b 1
)

REM 检查Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python 未安装，请先安装Python3
    pause
    exit /b 1
)

REM 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  建议以管理员权限运行以获得更好的扫描效果
    echo 请右键点击此脚本，选择"以管理员身份运行"
    echo.
    pause
)

REM 检查依赖
echo 📦 检查依赖...
python -c "import scapy" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  缺少依赖，正在安装...
    pip install -r requirements.txt
)

REM 运行程序
echo 🚀 启动Boss Detect...
echo.
python boss_detect.py

pause
