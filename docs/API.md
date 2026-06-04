# API 文档

my-jxc 进销存系统 API 端点文档。

所有 API 需要登录认证（Cookie-based session）。未认证请求将返回 302 重定向到登录页。

---

## 商品模块

### GET /product/api/products

获取所有商品列表。

**响应:**
```json
[
  {
    "id": 1,
    "code": "SKU001",
    "name": "商品名称",
    "category_id": 1,
    "unit": "个",
    "sale_price": "100.00",
    "purchase_price": "50.00",
    "stock_quantity": "50"
  }
]
```

### GET /product/api/categories

获取所有分类列表。

**响应:**
```json
[
  {
    "id": 1,
    "name": "分类名称",
    "parent_id": null
  }
]
```

### POST /product/api/product/price

获取商品价格。

**请求体:**
```json
{
  "product_id": 1,
  "price_type": "sale_price"
}
```

**响应:**
```json
{
  "price": "100.00"
}
```

---

## 采购模块

### GET /purchase/api/purchase-orders/{order_id}/items

获取采购订单明细。

**参数:**
- `order_id` (int): 采购订单ID

**响应:**
```json
[
  {
    "product_id": 1,
    "product_name": "商品名称",
    "quantity": "10",
    "unit_price": "50.00",
    "amount": "500.00"
  }
]
```

---

## 销售模块

### GET /sales/api/sales-orders/{order_id}/items

获取销售订单明细。

**参数:**
- `order_id` (int): 销售订单ID

**响应:**
```json
[
  {
    "product_id": 1,
    "product_name": "商品名称",
    "quantity": "5",
    "unit_price": "100.00",
    "amount": "500.00"
  }
]
```

---

## 库存模块

### GET /inventory/api/low-stock

获取低库存商品列表。

**响应:**
```json
[
  {
    "id": 1,
    "code": "SKU001",
    "name": "商品名称",
    "stock_quantity": "5",
    "safety_stock": "10"
  }
]
```

### POST /inventory/api/stock-check

库存盘点 API。

**请求体:**
```json
{
  "product_id": 1,
  "warehouse_id": 1,
  "actual_quantity": 100
}
```

### GET /inventory/api/logs-statistics

获取库存日志统计。

---

## 财务模块

### GET /finance/api/financial-summary

获取财务汇总信息。

**响应:**
```json
{
  "total_receivable": "10000.00",
  "total_payable": "5000.00",
  "total_expense": "2000.00",
  "profit": "3000.00"
}
```

### GET /finance/api/customer-ar/{customer_id}

获取客户应收明细。

**参数:**
- `customer_id` (int): 客户ID

### GET /finance/api/supplier-ap/{supplier_id}

获取供应商应付明细。

**参数:**
- `supplier_id` (int): 供应商ID

---

## 报表模块

### GET /report/api/sales-trend

获取销售趋势数据。

**查询参数:**
- `days` (int, 可选): 天数，默认 30

**响应:**
```json
[
  {
    "date": "2026-06-01",
    "amount": "5000.00"
  }
]
```

---

## 系统模块

### GET /system/api/system-info

获取系统信息。

**响应:**
```json
{
  "version": "1.0.0",
  "database_size": "1024 KB",
  "user_count": 5,
  "product_count": 100
}
```

### GET /system/api/system/recent-logs

获取最近操作日志。

### POST /system/api/system/optimize-db

优化数据库（需要管理员权限）。

### POST /system/api/system/clean-logs

清理旧日志（需要管理员权限）。

### GET /system/api/system/export-db

导出数据库文件。

### POST /system/api/system/settings

保存系统设置。

**请求体:**
```json
{
  "COMPANY_NAME": "公司名称",
  "DEFAULT_WAREHOUSE": "1"
}
```

---

## 导出端点

所有导出端点返回 Excel 文件（.xlsx）。

| 端点 | 说明 |
|------|------|
| GET /finance/export-receipts | 导出收款记录 |
| GET /finance/export-payments | 导出付款记录 |
| GET /finance/export-expenses | 导出费用记录 |
| GET /finance/export-profit-analysis | 导出利润分析 |
| GET /report/export/inventory | 导出库存报表 |
| GET /report/export/sales-ranking | 导出销售排行 |
| GET /report/export/customer | 导出客户统计 |
| GET /report/export/supplier | 导出供应商统计 |
| GET /report/export-products | 导出商品报表 |
| GET /report/export/daily | 导出日报 |
| GET /system/api/system/export-db | 导出数据库 |

---

## 错误响应

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 302 | 未认证，重定向到登录页 |
| 400 | 请求参数错误 |
| 403 | 权限不足（非管理员） |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 注意事项

1. 所有金额字段返回字符串格式的 Decimal，避免精度丢失
2. 日期字段返回 `YYYY-MM-DD` 格式
3. 分页参数：`page`（页码，从1开始）、`per_page`（每页数量，默认20）
4. CSRF 保护：API 端点使用 header-based token（`X-CSRFToken`）
