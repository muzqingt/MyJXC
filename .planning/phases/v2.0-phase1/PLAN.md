# PLAN: Phase 1 — AI 基础设施

## 目标
后端 AI 识别引擎 + 系统配置

## 需求
R1.1, R1.2, R2.1, R2.2, R2.3, R5.1

---

## Task 1: AI 配置数据模型

**文件：** `app/routes/system.py`

### 步骤
1. 在 `settings()` 函数中添加 AI 配置读取：
   - `AI_API_URL` — API 地址
   - `AI_API_KEY` — API 密钥
   - `AI_MODEL_NAME` — 模型名称
2. 在 `save_settings()` 函数中添加 AI 配置保存
3. 密钥脱敏：读取时只显示前 4 位 + `****`

### 验证
- [ ] AI 配置可保存到数据库
- [ ] 密钥脱敏显示

---

## Task 2: 系统设置页 AI 配置区域

**文件：** `app/templates/system/settings.html`

### 步骤
1. 添加"AI 识别配置"卡片区域
2. 表单字段：
   - API 地址（text，placeholder: https://api.openai.com/v1）
   - API 密钥（password，显示脱敏值）
   - 模型名称（text，placeholder: gpt-4o）
3. "测试连接"按钮
4. 未配置时显示提示信息

### 验证
- [ ] AI 配置区域正常显示
- [ ] 密钥字段脱敏显示
- [ ] 表单可保存

---

## Task 3: 测试连接 API

**文件：** `app/routes/system.py`

### 步骤
1. 新增路由 `POST /system/api/test-ai-connection`
2. 读取 AI 配置
3. 调用 API 发送简单请求验证连接
4. 返回 JSON `{success, message}`

### 验证
- [ ] 有效配置可连接成功
- [ ] 无效配置返回错误信息
- [ ] 未配置时返回提示

---

## Task 4: AI 识别后端 API

**文件：** `app/routes/system.py`（或新建 `app/routes/ai.py`）

### 步骤
1. 新增路由 `POST /api/ai/recognize`
2. 接收参数：
   - `image_base64` — 图片 base64 数据
   - `doc_type` — 单据类型（purchase/sales/stock_in/stock_out/receipt/payment/expense/return）
3. 根据 doc_type 选择 prompt
4. 调用 OpenAI 兼容 API：
   ```python
   POST {api_url}/chat/completions
   Authorization: Bearer {api_key}
   Body: {
     "model": model_name,
     "messages": [
       {"role": "system", "content": prompt},
       {"role": "user", "content": [
         {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,{base64}"}}
       ]}
     ],
     "max_tokens": 2000
   }
   ```
5. 解析返回的 JSON
6. 返回结构化数据

### 验证
- [ ] 图片可正确发送到 API
- [ ] 返回结果可解析
- [ ] 错误情况正确处理

---

## Task 5: Prompt 设计

**文件：** `app/routes/ai.py`（或 `app/ai_prompts.py`）

### 步骤
1. 设计各单据类型的 system prompt
2. 要求返回固定 JSON 格式
3. 示例 prompt（采购订单）：
   ```
   你是一个单据识别助手。请识别图片中的采购单据，返回以下JSON格式：
   {
     "supplier_name": "供应商名称",
     "order_date": "YYYY-MM-DD",
     "items": [
       {"name": "商品名称", "quantity": 数量, "unit_price": 单价}
     ],
     "notes": "备注"
   }
   如果某个字段无法识别，返回null。只返回JSON，不要其他文字。
   ```
4. 为每种单据类型设计对应 prompt

### 验证
- [ ] Prompt 可引导 AI 返回正确格式
- [ ] 各字段映射清晰

---

## Task 6: 错误处理

**文件：** `app/routes/ai.py`

### 步骤
1. API 超时处理（10 秒超时）
2. API 密钥无效处理
3. 网络错误处理
4. AI 返回格式错误处理
5. 图片过大处理
6. 统一错误响应格式：`{success: false, message: "错误信息"}`

### 验证
- [ ] 超时返回友好提示
- [ ] 密钥无效返回提示
- [ ] 网络错误返回提示

---

## Task 7: 测试

### 步骤
1. AI 配置保存/读取测试
2. 测试连接 API 测试
3. 识别 API 测试（mock AI 响应）
4. 错误处理测试
5. 权限测试（仅管理员可配置）

### 验证
- [ ] 所有新测试通过
- [ ] 现有测试无回归

---

## 执行顺序
1 → 2 → 3 → 4 → 5 → 6 → 7

## 预估
2-3 天
