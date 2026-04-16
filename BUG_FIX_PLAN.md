# MyJXC 全面查错报告

## ✅ 已检查模块

| 模块 | 状态 | 说明 |
|------|------|------|
| models.py | ✅ 无问题 | 外键关系正确 |
| auth.py | ✅ 无问题 | 密码、CSRF 正常 |
| purchase.py | ✅ 无问题 | 入库逻辑正确 |
| sales.py | ✅ 无问题 | 出库逻辑正确 |
| report.py | 🟡 小问题 | 期初库存 = 0 |
| finance.py | ✅ 无问题 | 利润计算正确 |
| 模板 div 闭合 | ✅ 全部平衡 | - |
| Python 语法 | ✅ 全部通过 | - |

---

## 🚨 发现的 Bug

### 🔴 Bug #1: 库存调拨逻辑错误 (inventory.py)

**位置:** `app/routes/inventory.py` 第 111-208 行

**问题:**
1. 调拨时错误地减少了 product.stock_quantity（但这是全局库存，不应该改变）
2. 只创建了"出库"日志，缺少"入库"日志

**代码问题:**
```python
# 错误：全局库存不应该被减少！
product.stock_quantity -= quantity  # BUG!
log_out = StockLog(
    ...
    change_type='out',
    ...
)
# 缺少：目的地仓库的 'in' 日志
```

**正确逻辑:**
- 调拨只记录库存流水（两条：出库+入库）
- product.stock_quantity 不应该改变（因为是全局库存，位置变化不影响总量）

---

### 🟡 Bug #2: 利润分析图表数据不对齐 (profit_analysis.html)

**位置:** `app/templates/finance/profit_analysis.html`

**问题:** 图表使用索引位置匹配月份，当销售和采购月份不一致时会错位

**已修复（待确认）:** 改为字典对齐

---

### 🟡 Bug #3: Enter 键与搜索选择器冲突 (base.html)

**位置:** `app/templates/base.html`

**问题:** 全局 Enter 处理器可能干扰搜索下拉框的确认行为

**待修复:** 需要排除搜索输入框

---

### 🟡 Bug #4: 期初库存未实现 (report.py)

**位置:** `app/routes/report.py` 第 83 行

**问题:** beginning_stock 始终为 0，注释说"需要实现期初库存计算"

---

### 🟢 Bug #5: stock_transfer.html 使用废弃的 e.which

**位置:** `app/templates/inventory/stock_transfer.html` 第 495 行

**问题:** 使用 e.which === 13，应该用 e.key === 'Enter'

---

## 修复优先级

1. 🔴 Bug #1: 库存调拨 - 影响数据完整性
2. 🟡 Bug #3: Enter 键冲突 - 影响用户体验
3. 🟡 Bug #2: 图表对齐 - 影响报表准确性
4. 🟡 Bug #4: 期初库存 - 影响进销存报表
5. 🟢 Bug #5: e.which 废弃 - 代码规范
