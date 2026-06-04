#!/bin/bash
# Linux版本打包脚本

echo "开始打包Linux版本..."

# 激活虚拟环境
source venv/bin/activate

# 清理旧的构建文件
rm -rf build dist

# 使用PyInstaller打包
pyinstaller jxc.spec

# 创建发布目录
mkdir -p release
mv dist/JXC release/

# 复制数据库和配置
cp -r instance release/JXC/ 2>/dev/null || true
cp config.py release/JXC/ 2>/dev/null || true

# 创建启动脚本
cat > release/JXC/start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
./JXC "$@"
EOF
chmod +x release/JXC/start.sh

echo "Linux版本打包完成！"
echo "位置: release/JXC/"
echo ""
echo "使用方法："
echo "  cd release/JXC"
echo "  ./start.sh"
echo ""
echo "或直接运行："
echo "  ./JXC"
