# MyJXC 进销存管理系统

基于 Flask 的中小企业进销存管理系统，覆盖采购、销售、库存、财务、报表五大业务模块。

## 快速开始

### 环境要求

- Python 3.13 或更高版本
- pip 包管理器

### 安装步骤

```bash
# 安装依赖
pip install -r requirements.txt

# 首次运行（自动创建数据库和默认管理员）
python run.py
```

打开浏览器访问：**http://127.0.0.1:5000**

默认管理员账号：`admin` / `admin123`

### 启动模式

```bash
# 开发模式（默认，带热重载）
FLASK_DEBUG=1 python run.py

# 生产模式（waitress，多线程稳定）
MODE=prod python run.py

# 自定义端口
PORT=8080 MODE=prod python run.py
```

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `MODE` | `dev` | `dev` = Flask 开发服务器，`prod` = waitress 生产服务器 |
| `PORT` | `5000` | 监听端口 |
| `FLASK_DEBUG` | `0` | 仅 dev 模式有效，`1` 开启调试和热重载 |

---

## 功能模块

### 基础资料管理
- 商品管理（支持图片上传）
- 商品分类管理
- 供应商管理
- 客户管理
- 仓库管理

### 采购管理
- 采购订单管理
- 采购入库管理
- 库存自动更新

### 销售管理
- 销售订单管理
- 销售出库管理
- 库存自动扣减

### 库存管理
- 实时库存查询
- 库存预警
- 库存盘点
- 库存调拨
- 库存流水记录

### 财务管理
- 收款管理
- 付款管理
- 费用支出管理
- 利润统计分析

### 报表分析
- 进销存报表
- 销售排行榜
- 客户/供应商统计
- 经营日报/月报

### 系统功能
- 操作日志
- 数据备份/恢复
- 用户管理
- 系统设置

---

## 运行测试

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

## 技术栈

- **后端**: Flask 2.3 + SQLAlchemy 2.0 + Flask-Login + Flask-WTF
- **前端**: Bootstrap 5 + jQuery 3.6 + Chart.js
- **数据库**: SQLite
- **生产服务器**: waitress（跨平台，Windows/Linux 均可用）

## 项目结构

```
my-jxc/
├── app/
│   ├── __init__.py          # 应用工厂（create_app）
│   ├── constants.py         # 业务常量（OrderStatus、ChangeType 等）
│   ├── forms.py             # WTForms 表单定义
│   ├── utils.py             # 通用工具函数
│   ├── utils_order.py       # 订单相关工具函数
│   ├── models/              # SQLAlchemy 数据模型
│   │   ├── user.py          # 用户、操作日志
│   │   ├── product.py       # 商品、分类
│   │   ├── partner.py       # 供应商、客户、仓库
│   │   ├── purchase.py      # 采购订单、入库单
│   │   ├── sales.py         # 销售订单、出库单
│   │   ├── inventory.py     # 库存流水
│   │   ├── finance.py       # 收款、付款、费用
│   │   ├── returns.py       # 采购退货、销售退货
│   │   └── system.py        # 系统设置
│   ├── routes/              # 路由模块（10 个蓝图）
│   ├── templates/           # Jinja2 模板
│   └── static/              # 静态资源
├── tests/                   # 测试用例
├── docs/                    # 文档
├── config.py                # 配置文件
├── run.py                   # 启动入口
└── requirements.txt         # 依赖列表
```

---

## 配置说明

### 安全建议

1. **修改密码**: 首次登录后及时修改管理员密码
2. **生产部署**: 使用 `MODE=prod` 启动，外层可加 Nginx 反向代理
3. **定期备份**: 通过系统后台 "系统功能 → 数据备份" 或直接复制 `instance/store.db`

### 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `MODE` | 启动模式：`dev` / `prod` | `dev` |
| `PORT` | 监听端口 | `5000` |
| `FLASK_DEBUG` | 调试模式（仅 dev） | `0` |
| `SECRET_KEY` | Flask 密钥 | 自动生成并持久化到 `instance/.flask_secret_key` |
| `DATABASE_URL` | 数据库连接 | `sqlite:///instance/store.db` |

---

## 注意事项

1. **首次运行**: 系统会自动创建数据库和默认管理员账户
2. **数据库文件**: 位于 `instance/store.db`，请定期备份
3. **上传文件**: 图片等上传文件保存在 `app/static/uploads/`
4. **操作日志**: 系统记录所有操作，建议定期查看

---

## 常见问题

### 启动时报错 "ModuleNotFoundError"
确保已安装所有依赖：`pip install -r requirements.txt`

### 如何备份/恢复数据？
- 备份：系统后台 → 系统功能 → 数据备份
- 恢复：系统后台 → 系统功能 → 数据恢复
- 手动：直接复制/替换 `instance/store.db` 文件

### 端口被占用？
```bash
PORT=8080 python run.py
```

### 生产环境如何部署？
```bash
MODE=prod PORT=5000 python run.py
```
外层可加 Nginx 反向代理处理静态文件和 HTTPS。

---

## 技术支持

如有问题或建议，请联系开发者。

---

## 许可证

MIT License