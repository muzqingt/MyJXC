# PLAN: Phase 4 — 其他单据集成

## 目标
入库/出库/收付款/费用/退货页面集成 AI 识别

## 需求
R4.3, R4.4, R4.5

---

## Task 1: 入库单页面集成

**文件：** `app/templates/purchase/stock_in_items.html`

### 步骤
1. 在表单上方添加 AI 识别按钮区域（`{% if ai_enabled and not stock_in %}`）
2. 初始化 AIRecognize 组件，docType='stock_in'
3. 实现 onResult 回调：
   - 填充商品明细
   - 填充日期
   - 填充备注

### 验证
- [ ] AI 按钮正确显示
- [ ] 识别结果可正确填充表单

---

## Task 2: 出库单页面集成

**文件：** `app/templates/sales/stock_out_items.html`

### 步骤
1. 同 Task 1，但 docType='stock_out'
2. 填充逻辑相同

### 验证
- [ ] AI 按钮正确显示
- [ ] 识别结果可正确填充表单

---

## Task 3: 收款单页面集成

**文件：** `app/templates/finance/receipt_edit.html`

### 步骤
1. 在表单上方添加 AI 识别按钮区域
2. 初始化 AIRecognize 组件，docType='receipt'
3. 实现 onResult 回调：
   - 填充金额
   - 填充日期
   - 匹配支付方式
   - 填充备注

### 验证
- [ ] AI 按钮正确显示
- [ ] 识别结果可正确填充表单

---

## Task 4: 付款单页面集成

**文件：** `app/templates/finance/payment_edit.html`

### 步骤
1. 同 Task 3，但 docType='payment'
2. 填充逻辑相同

### 验证
- [ ] AI 按钮正确显示
- [ ] 识别结果可正确填充表单

---

## Task 5: 费用单页面集成

**文件：** `app/templates/finance/expense_edit.html`

### 步骤
1. 在表单上方添加 AI 识别按钮区域
2. 初始化 AIRecognize 组件，docType='expense'
3. 实现 onResult 回调：
   - 填充费用类别
   - 填充金额
   - 填充日期
   - 填充收款方
   - 匹配支付方式
   - 填充备注

### 验证
- [ ] AI 按钮正确显示
- [ ] 识别结果可正确填充表单

---

## Task 6: 采购退货页面集成

**文件：** `app/templates/purchase/return_view.html`（或新建表单页）

### 步骤
1. 检查是否有退货创建页面
2. 如果有，添加 AI 识别按钮
3. docType='return'
4. 填充退货商品明细

### 验证
- [ ] AI 按钮正确显示
- [ ] 识别结果可正确填充表单

---

## Task 7: 销售退货页面集成

**文件：** `app/templates/sales/return_view.html`（或新建表单页）

### 步骤
1. 同 Task 6

### 验证
- [ ] AI 按钮正确显示
- [ ] 识别结果可正确填充表单

---

## Task 8: 全量测试

### 步骤
1. 所有单据页面 AI 识别功能测试
2. 各字段填充测试
3. 边界情况测试
4. 现有测试回归测试

### 验证
- [ ] 所有测试通过
- [ ] 现有测试无回归

---

## Task 9: 文档更新

### 步骤
1. 更新 README.md 添加 AI 识别功能说明
2. 更新 CHANGELOG.md

### 验证
- [ ] 文档更新完成

---

## 执行顺序
1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9

## 预估
2-3 天
