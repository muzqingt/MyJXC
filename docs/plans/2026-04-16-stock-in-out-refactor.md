# 入库/出库操作重构设计

## 一、现状全流程图

### 采购入库（Purchase）

**路径A：新建订单时直接入库** (`new_order` + `order_status='completed'`)
```
POST new_order
  → 创建 PurchaseOrder(status='completed') + PurchaseOrderItem
  → 创建 StockIn(status='completed') + StockInItem
  → 更新 Product.stock_quantity (+)
  → 创建 StockLog(type='in')
  → 更新 Supplier.payable_balance
  → 更新 PurchaseOrderItem.received_quantity = quantity
  → 刷新 Supplier.receivable_balance
```

**路径B：二步入库**
```
Step1: POST new_order (order_status='confirmed')
  → 创建 PurchaseOrder(status='confirmed') + PurchaseOrderItem
  → 不触碰库存

Step2a: POST quick_stock_in
  → 创建 StockIn(status='completed') + StockInItem
  → 更新 Product.stock_quantity (+)
  → 创建 StockLog(type='in')
  → 更新 Supplier.payable_balance
  → 更新 PurchaseOrderItem.received_quantity = 全量
  → 刷新 order.status='completed'

Step2b: POST new_stock_in_from_order → GET edit_stock_in_items → POST complete_stock_in
  new_stock_in_from_order:
    → 创建 StockIn(status='unstocked') + StockInItem(从订单商品取剩余数量)
    → 不触碰库存
    → 重定向到 edit_stock_in_items

  edit_stock_in_items:
    → 保存/编辑 StockInItem（删除旧明细，插入新明细）
    → 不触碰库存
    → 不更新 PurchaseOrderItem.received_quantity

  complete_stock_in:
    → 更新 Product.stock_quantity (+)
    → 创建 StockLog(type='in')
    → 更新 Supplier.payable_balance
    → 更新 PurchaseOrderItem.received_quantity（累加本次入库数量）
    → 更新 order.status='completed'/'partial'
```

**路径C：新建空白入库单（无订单）**
```
new_stock_in → edit_stock_in_items → complete_stock_in
（不关联订单，不更新供应商余额）
```

---

### 销售出库（Sales）

**路径A：新建订单时直接出库** (`new_order` + `order_status='completed'`)
```
POST new_order
  → 创建 SalesOrder(status='completed') + SalesOrderItem
  → 库存校验（如不足则回滚）
  → 创建 StockOut(status='completed') + StockOutItem
  → 更新 Product.stock_quantity (-)
  → 创建 StockLog(type='out')
  → 更新 Customer.receivable_balance
  → 更新 SalesOrderItem.delivered_quantity = 全量
```

**路径B：二步出库**
```
Step1: POST new_order (order_status='confirmed')
  → 创建 SalesOrder(status='confirmed') + SalesOrderItem
  → 不触碰库存

Step2a: POST quick_stock_out
  → 创建 StockOut(status='completed') + StockOutItem
  → 更新 Product.stock_quantity (-)
  → 创建 StockLog(type='out')
  → 更新 Customer.receivable_balance
  → 更新 SalesOrderItem.delivered_quantity = 全量
  → 刷新 order.status='completed'

Step2b: POST new_stock_out_from_order → GET edit_stock_out_items → POST complete_stock_out
  new_stock_out_from_order:
    → 创建 StockOut(status='draft') + StockOutItem
    → 不触碰库存
    → 重定向到 edit_stock_out_items

  edit_stock_out_items:
    → 保存/编辑 StockOutItem（删除旧明细，插入新明细）
    → 不触碰库存
    → 不更新 SalesOrderItem.delivered_quantity

  complete_stock_out:
    → 库存校验
    → 更新 Product.stock_quantity (-)
    → 创建 StockLog(type='out')
    → 更新 Customer.receivable_balance
    → 更新 SalesOrderItem.delivered_quantity（累加本次出库数量）
    → 更新 order.status='completed'/'partial'
```

---

## 二、问题清单

### 问题1：直接入库/出库 与 快捷入库/出库 功能重复（高）

| 路径 | 操作 | 代码 |
|------|------|------|
| `new_order` (order_status='completed') | 创建订单时同步完成入库/出库 | `purchase.py new_order` 整个 `if order_status == 'completed'` 块 |
| `quick_stock_in` | 已有订单→快捷入库 | `purchase.py quick_stock_in` |
| `new_order` (order_status='completed') | 创建订单时同步完成出库 | `sales.py new_order` 整个 `if order_status == 'completed'` 块 |
| `quick_stock_out` | 已有订单→快捷出库 | `sales.py quick_stock_out` |

**结果**：两套代码做完全相同的事，重复、维护困难。

### 问题2：edit_stock_in_items 编辑已关联订单的入库单时，不更新 PurchaseOrderItem.received_quantity（高）

**场景**：用户从采购订单创建入库单后，编辑了明细数量并完成入库：
- `edit_stock_in_items` 保存新明细（删旧插新） → **不更新 received_quantity**
- `complete_stock_in` 执行 `received_quantity += 本次入库数量`
- **结果**：`received_quantity` 只记录了最后一次完成的数量，而非累计

**正确行为**：
- `edit_stock_in_items` 保存后，`received_quantity` 应该反映当前 `StockInItem` 的总数量
- 或者 `received_quantity` 仅在 `complete_stock_in` 时更新，且**基于当前实际入库数量计算**（不是增量加）

### 问题3：edit_stock_out_items 同样不更新 SalesOrderItem.delivered_quantity（中）

同问题2，对称存在于出库流程。

### 问题4：StockIn/StockOut 状态值命名不一致（中）

| 实体 | 草稿/未完成状态 | 完成状态 |
|------|---------------|---------|
| StockIn | `unstocked` ("待入库") | `completed` |
| StockOut | `draft` ("草稿") | `completed` |

**建议**：统一为 `pending` / `completed`。

### 问题5：new_stock_out_from_order 跳过了 status 参数（中）

`purchase.py new_stock_in_from_order`：
```python
stock_in = StockIn(..., status='unstocked')  # ✓ 有
```

`sales.py new_stock_out_from_order`：
```python
stock_out = StockOut(...)  # ✗ 漏了 status，默认 'draft'
```
导致行为不一致。

### 问题6：new_order 直接出库时，status 校验不一致（低）

采购新建订单：无论 `order_status` 值如何，`status` 硬编码为 `'confirmed'`，但 `order_status='completed'` 时才创建入库单（最终状态覆盖）。

---

## 三、重构方案

### 方案A（推荐）：合并重复代码，统一 StockIn/StockOut 状态

**1. 移除 `new_order` 中的直接入库/出库逻辑**
- 删除 `new_order` 中 `if order_status == 'completed'` 的整个代码块
- 用户必须走二步流程（先建订单 → 再入库/出库）
- 理由：直接入库跳过确认步骤，风险高；二步流程更清晰

**2. 移除 `quick_stock_in` 和 `quick_stock_out`**
- 理由：与"新建订单时直接入库/出库"功能完全重复
- 移除后保留：`new_stock_in_from_order` + `edit_stock_in_items` + `complete_stock_in`

**3. 统一 StockIn/StockOut 状态值**
```python
StockIn.status:  'pending'   # 待确认（替代 'unstocked'）
                'completed' # 已完成

StockOut.status: 'pending'   # 待确认（替代 'draft'）
                'completed' # 已完成
```

**4. 修复 `new_stock_out_from_order` 添加 status='pending'**

**5. 修复 `edit_stock_in_items` 和 `edit_stock_out_items` 的 received_quantity/delivered_quantity 问题**

**方案A优点**：
- 单一代码路径，易维护
- 状态值统一
- 每步操作语义清晰：创建 → 编辑明细 → 确认完成
- 用户界面更清晰（没有重复入口）

---

### 方案B：保留所有路径，统一状态值

- 不删除任何现有功能
- 统一 StockIn.status: `unstocked` → `pending`
- 统一 StockOut.status: `draft` → `pending`
- 修复 `new_stock_out_from_order` 的 status 遗漏

**方案B缺点**：保留重复代码，长期维护负担重。

---

## 四、推荐方案（方案A）实施步骤

### Step 1: 统一状态值
- `StockIn`：`unstocked` → `pending`
- `StockOut`：`draft` → `pending`
- 涉及所有路由和模板中的硬编码字符串

### Step 2: 移除 new_order 中的直接入库/出库块
- 删除 `purchase.py new_order` 中的 `if order_status == 'completed'` 块
- 删除 `sales.py new_order` 中的 `if order_status == 'completed'` 块

### Step 3: 移除 quick_stock_in 和 quick_stock_out
- 删除 `purchase.py` 中的 `quick_stock_in` 路由
- 删除 `sales.py` 中的 `quick_stock_out` 路由

### Step 4: 修复 new_stock_out_from_order 的 status
- 添加 `status='pending'`

### Step 5: 修复 edit_stock_in_items 和 edit_stock_out_items
- `complete_stock_in/out` 基于当前 `StockInItem.quantity` 累加到 `received/delivered_quantity`
- 避免删除旧明细后数量丢失的问题
