# MyJXC

一个简单的进销存管理系统，支持采购管理、销售管理、库存管理、财务管理、报表分析功能。

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本
- pip 包管理器

### 安装步骤

#### 1. 解压发布包

```bash
tar -xzf myjxc_v1.0.0.tar.gz
cd myjxc
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 首次运行

```bash
python run.py
```

首次运行会自动：
- 创建 SQLite 数据库文件
- 创建默认管理员账户

#### 4. 访问系统

打开浏览器访问：**http://127.0.0.1:5000**

默认管理员账号：
- **用户名**: `admin`
- **密码**: `admin123`

---

## 📋 功能模块

### ✅ 基础资料管理
- 商品管理（支持图片上传）
- 商品分类管理
- 供应商管理
- 客户管理
- 仓库管理

### ✅ 采购管理
- 采购订单管理
- 采购入库管理
- 库存自动更新

### ✅ 销售管理
- 销售订单管理
- 销售出库管理
- 库存自动扣减

### ✅ 库存管理
- 实时库存查询
- 库存预警
- 库存盘点
- 库存调拨
- 库存流水记录

### ✅ 财务管理
- 收款管理
- 付款管理
- 费用支出管理
- 利润统计分析

### ✅ 报表分析
- 进销存报表
- 销售排行榜
- 客户/供应商统计
- 经营日报/月报

### ✅ 系统功能
- 操作日志
- 数据备份/恢复
- 用户管理
- 系统设置

---

## 🧪 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-cov

# 运行所有测试
python -m pytest tests/ -v

# 运行测试并查看覆盖率
python -m pytest tests/ --cov=app --cov-report=term

# 运行单个模块测试
python -m pytest tests/test_purchase.py -v
```

---

## 🛠 技术栈

- **后端**: Flask + SQLAlchemy + Flask-Login + Flask-WTF
- **前端**: Bootstrap 5 + jQuery
- **数据库**: SQLite
- **图表**: Chart.js

---

## 📁 项目结构

```
myjxc/
├── app/                  # 应用主目录
│   ├── routes/          # 路由模块
│   ├── templates/       # HTML模板
│   ├── static/          # 静态文件
│   │   ├── css/         # 样式文件
│   │   ├── js/          # JavaScript文件
│   │   └── uploads/     # 上传文件目录
│   ├── models.py        # 数据模型
│   └── forms.py         # 表单定义
├── instance/            # 数据库目录（运行时创建）
├── config.py            # 配置文件
├── run.py               # 启动文件
└── requirements.txt     # 依赖列表
```

---

## ⚙️ 配置说明

### 修改密码

首次使用后，请及时修改管理员密码：
1. 登录系统
2. 点击右上角用户头像
3. 选择"个人信息"
4. 修改密码

### 安全建议

1. **修改 SECRET_KEY**: 编辑 `config.py`，将 `SECRET_KEY` 修改为随机字符串
2. **生产环境**: 建议使用 Nginx + Gunicorn 部署
3. **数据库**: 定期备份 `instance/store.db` 文件

### 数据库迁移

如需迁移到其他数据库（如 PostgreSQL、MySQL），请修改 `config.py` 中的 `SQLALCHEMY_DATABASE_URI`。

---

## 🔒 注意事项

1. **首次运行**: 系统会自动创建数据库和默认管理员账户
2. **数据库文件**: 位于 `instance/store.db`，请定期备份
3. **上传文件**: 图片等上传文件保存在 `app/static/uploads/`
4. **操作日志**: 系统记录所有操作，建议定期查看

---

## 🐛 常见问题

### Q: 启动时报错 "ModuleNotFoundError"
A: 请确保已安装所有依赖：`pip install -r requirements.txt`

### Q: 如何备份数据？
A: 
- 方式一：通过系统后台 "系统功能 → 数据备份"
- 方式二：直接复制 `instance/store.db` 文件

### Q: 如何恢复数据？
A: 通过系统后台 "系统功能 → 数据恢复"，或直接替换 `instance/store.db` 文件

### Q: 默认端口5000被占用？
A: 修改 `run.py` 中的端口号，或设置环境变量 `PORT`

---

## 📞 技术支持

如有问题或建议，请联系开发者。

---

## 📄 许可证

MIT License