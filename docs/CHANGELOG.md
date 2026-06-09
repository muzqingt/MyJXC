# Changelog

## [1.1.0] - 2026-06-08

### Added
- 自定义错误页面（403/404/500），继承 base.html 统一风格
- `payment_method` Jinja2 过滤器，统一支付方式中文显示
- 商品/供应商/客户导入页面入口按钮
- 生产服务器支持（waitress），通过 `MODE=prod` 环境变量切换
- `auth.py` 日志记录失败时写入 `current_app.logger`

### Fixed
- 库存流水导出 Excel 中 `stock_transfer` 显示为英文（type_mapping key 不匹配）
- 应收应付导出 Excel 中支付方式显示为英文
- `flash(str(e))` 泄露原始数据库错误信息（finance.py 3处、system.py 3处）
- 导入功能错误信息泄露原始异常详情（product.py、partner.py 3处）
- 7 处未保护的 `db.session.commit()` 添加 try/except（sales.py 4处、system.py 1处、finance.py 2处）
- 模板中 `aria-label` 使用英文（4处）
- JavaScript `console.log` 使用英文（4处）
- `ValueError` 异常消息使用英文

### Removed
- 未使用的服务层 `app/services/`（PurchaseService、SalesService、InventoryService）
- 未使用的工具函数：`flash_success`、`flash_error`、`flash_warning`、`generate_order_number_safe`、`validate_order_items`
- 未使用的 model property：`StockLog.stock_in`、`StockLog.stock_out`
- 未使用的 import（finance.py、report.py、partner.py、main.py、sales.py）
- `purchase.py` 中 `edit_order` 的不可达代码（供应商余额调整）
- `routes/__init__.py` 中未被消费的 `__all__`

## [1.0.0] - 2026-06-03

### Added
- 采购管理模块（订单、入库、退货）
- 销售管理模块（订单、出库、退货）
- 库存管理模块（盘点、调拨、调整、日志）
- 财务管理模块（收款、付款、费用、利润分析）
- 报表分析模块（进销存报表、销售排行、客户/供应商统计）
- 系统管理模块（用户、设置、备份、日志）
- pytest 测试基础设施（fixtures、工厂函数）
- 188 个自动化测试用例
- 核心业务逻辑 ~85% 测试覆盖率

### Fixed
- `generate_order_number()` 处理 PurchaseReturn 时的属性访问错误
- 测试数据库隔离问题（DATABASE_URL 环境变量）

### Changed
- 核心模型方法添加类型提示
- 统一错误处理模式（SQLAlchemyError）
