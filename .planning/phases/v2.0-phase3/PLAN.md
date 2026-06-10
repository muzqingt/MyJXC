# PLAN: Phase 3 — 采购/销售订单集成

## 目标
采购订单和销售订单创建页集成 AI 识别功能

## 需求
R4.1, R4.2

---

## Task 1: 采购订单页集成 AI 识别

**文件：** `app/templates/purchase/order_items.html`

### 步骤
1. 在表单上方添加 AI 识别按钮区域
2. 使用 `{% if ai_enabled %}` 条件显示
3. 初始化 AIRecognize 组件，docType='purchase'
4. 实现 onResult 回调：
   - 匹配供应商：根据 `supplier_name` 模糊匹配已有供应商
   - 填充商品明细：根据 `items` 数组调用 `addItemRow()`
   - 填充日期和备注

### 验证
- [ ] AI 按钮在配置了 AI 时显示
- [ ] 未配置 AI 时按钮不显示
- [ ] 识别结果可正确填充表单

---

## Task 2: 供应商匹配逻辑

**文件：** `app/templates/purchase/order_items.html`

### 步骤
1. 在 onResult 回调中，遍历供应商列表
2. 根据 `supplier_name` 模糊匹配（包含匹配）
3. 匹配成功：设置供应商下拉框选中值
4. 匹配失败：提示用户手动选择

### 验证
- [ ] 供应商名称可正确匹配
- [ ] 无匹配时提示用户

---

## Task 3: 商品明细填充逻辑

**文件：** `app/templates/purchase/order_items.html`

### 步骤
1. 遍历识别结果的 `items` 数组
2. 对每个商品，根据 `name` 模糊匹配已有商品列表
3. 匹配成功：调用 `addItemRow(productId, quantity, unitPrice)`
4. 匹配失败：跳过该商品，提示用户
5. 更新总金额

### 验证
- [ ] 商品可正确匹配并添加
- [ ] 数量和单价正确填充
- [ ] 总金额自动计算

---

## Task 4: 销售订单页集成 AI 识别

**文件：** `app/templates/sales/order_items.html`

### 步骤
1. 同 Task 1，但 docType='sales'
2. 匹配客户而非供应商
3. 其余逻辑相同

### 验证
- [ ] AI 按钮正确显示
- [ ] 客户可正确匹配
- [ ] 商品明细正确填充

---

## Task 5: 测试

### 步骤
1. 采购订单 AI 识别集成测试
2. 销售订单 AI 识别集成测试
3. 供应商/客户匹配测试
4. 商品匹配测试
5. 边界情况测试（无匹配、部分匹配）

### 验证
- [ ] 所有测试通过
- [ ] 现有测试无回归

---

## 执行顺序
1 → 2 → 3 → 4 → 5

## 预估
2-3 天
