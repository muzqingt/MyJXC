进销存管理系统 - Linux版本
=============================

版本信息:
- 主程序: JXC (Linux x86_64)
- 无需Python环境
- 独立可执行文件

快速开始:
1. 直接运行: ./JXC
2. 访问: http://127.0.0.1:5000

默认账号:
- 用户名: admin
- 密码: admin123

文件说明:
- JXC: 主程序可执行文件
- config.py: 配置文件
- instance/: 数据库存储目录
- app/: 应用资源文件

注意事项:
- 确保程序有执行权限: chmod +x JXC
- 首次运行会自动初始化数据库
- 数据库文件: instance/store.db

详细说明请查看: README_BUILD.md
