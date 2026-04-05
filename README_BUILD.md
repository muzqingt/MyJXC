# 进销存管理系统 - 打包说明

## 📦 打包文件说明

本项目已配置好打包脚本，可将应用打包为独立可执行文件，无需安装Python环境即可运行。

### 文件清单

- `jxc.spec` - PyInstaller配置文件
- `build_linux.sh` - Linux系统打包脚本
- `build_windows.bat` - Windows系统打包脚本

---

## 🐧 Linux版本打包

### 自动打包（推荐）

```bash
./build_linux.sh
```

这将：
1. 激活虚拟环境
2. 安装PyInstaller
3. 清理旧的构建文件
4. 使用PyInstaller打包
5. 创建发布目录 `release/JXC/`

### 手动打包

```bash
# 1. 激活虚拟环境
source venv/bin/activate

# 2. 打包
pyinstaller jxc.spec

# 3. 移动到发布目录
mkdir -p release
mv dist/JXC release/
```

### 运行打包后的程序

```bash
cd release/JXC
./JXC
```

或使用启动脚本：
```bash
cd release/JXC
./start.sh
```

---

## 🪟 Windows版本打包

由于PyInstaller不支持跨平台编译，Windows版本需要在Windows系统上打包。

### 打包步骤

1. **准备Windows系统**
   - 安装Python 3.8+
   - 下载项目源码

2. **运行打包脚本**
   
   双击运行 `build_windows.bat` 或在命令提示符中执行：
   ```cmd
   build_windows.bat
   ```

3. **等待打包完成**
   - 脚本会自动创建虚拟环境
   - 安装所有依赖
   - 执行PyInstaller打包
   - 生成可执行文件

### 手动打包（Windows）

```cmd
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
venv\Scripts\activate.bat

# 3. 安装依赖
pip install -r requirements.txt
pip install pyinstaller

# 4. 打包
pyinstaller jxc.spec

# 5. 移动到发布目录
move dist\JXC release\
```

### 运行打包后的程序

```
release\JXC\JXC.exe
```

或双击 `release\JXC\start.bat`

---

## 📁 发布包内容

打包后的目录结构：

```
JXC/
├── JXC (Linux) / JXC.exe (Windows)  # 主程序
├── config.py                        # 配置文件
├── instance/                        # 数据库目录
│   └── store.db                     # SQLite数据库
├── app/                             # 应用资源
│   ├── templates/                    # 模板文件
│   └── static/                       # 静态文件
└── start.sh / start.bat            # 启动脚本
```

---

## ⚙️ 注意事项

### 数据库文件

- 数据库文件位于 `instance/store.db`
- 打包时会复制现有数据库
- 首次运行会自动创建默认管理员账号

### 默认账号

- 用户名: `admin`
- 密码: `admin123`

### 端口访问

- 启动后访问: http://127.0.0.1:5000
- 局域网访问: http://0.0.0.0:5000

### 数据迁移

如果需要迁移数据，只需复制 `instance/store.db` 文件到新环境的对应位置。

---

## 🛠️ 常见问题

### Q: 打包后缺少某些文件？

检查 `jxc.spec` 文件中的 `datas` 部分，确保所有资源文件都已包含。

### Q: 程序启动报错？

1. 检查是否所有依赖都已安装
2. 确认 `instance` 目录存在且可写
3. 查看终端输出的错误信息

### Q: Linux版本在某些发行版无法运行？

```bash
# 确保文件有执行权限
chmod +x JXC

# 安装必要的系统库
sudo apt install libpython3.x libc6
```

### Q: Windows版本杀毒软件报毒？

PyInstaller打包的程序可能被某些杀毒软件误报，这是正常现象。可将程序提交给杀毒软件厂商认证。

---

## 📝 技术栈

- **后端**: Flask, SQLAlchemy, Flask-Login
- **前端**: Bootstrap 3, HTML5, JavaScript
- **数据库**: SQLite
- **打包工具**: PyInstaller

---

## 📞 技术支持

如有问题，请提交Issue或联系开发者。

祝使用愉快！ 🚀
