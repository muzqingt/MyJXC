@echo off
:: Windows版本打包脚本
:: 在Windows系统上运行此脚本

echo 开始打包Windows版本...

:: 创建虚拟环境并安装依赖
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
pip install pyinstaller

:: 清理旧的构建文件
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

:: 使用PyInstaller打包
pyinstaller jxc.spec

:: 创建发布目录
if not exist release mkdir release
move dist\JXC release\

:: 复制数据库和配置
if exist instance\xcopy instance release\JXC\ /e /i
if exist config.py copy config.py release\JXC\

:: 创建启动批处理文件
echo @echo off > release\JXC\start.bat
echo cd /d "%%~dp0" >> release\JXC\start.bat
echo start JXC.exe >> release\JXC\start.bat

echo.
echo Windows版本打包完成！
echo 位置: release\JXC\
echo.
echo 使用方法：
echo   双击 start.bat 或直接运行 JXC.exe
pause
