# PLAN: Phase 2 — 前端拍照组件

## 目标
可复用的拍照/上传组件，支持图片压缩和识别结果确认

## 需求
R3.1, R3.2, R3.3

---

## Task 1: 创建 ai_recognize.js 组件

**文件：** `app/static/js/ai_recognize.js`

### 步骤
1. 创建 `AIRecognize` 类
2. 构造函数参数：
   - `docType` — 单据类型（purchase/sales/stock_in/stock_out/receipt/payment/expense/return）
   - `onResult` — 识别结果回调函数
   - `containerSelector` — 按钮容器选择器（可选）
3. 方法：
   - `init()` — 初始化按钮和事件
   - `openCamera()` — 打开拍照/文件选择
   - `compressImage(file)` — 压缩图片到 1MB 以内
   - `recognize(imageBase64)` — 调用后端 API 识别
   - `showConfirmDialog(data)` — 显示确认对话框
   - `showError(message)` — 显示错误提示

### 验证
- [ ] AIRecognize 类可实例化
- [ ] 按钮可正确渲染

---

## Task 2: 拍照/文件选择功能

**文件：** `app/static/js/ai_recognize.js`

### 步骤
1. 创建隐藏的 `<input type="file" accept="image/*" capture="camera">`
2. 移动端：支持直接调用摄像头拍照
3. 桌面端：支持选择本地图片文件
4. 点击按钮触发文件选择
5. 选择后预览图片

### 验证
- [ ] 移动端可调用摄像头
- [ ] 桌面端可选择文件
- [ ] 选择后显示预览

---

## Task 3: 图片压缩

**文件：** `app/static/js/ai_recognize.js`

### 步骤
1. 使用 Canvas API 压缩图片
2. 目标：宽度不超过 1024px，文件大小不超过 1MB
3. 压缩质量：0.8（可调整）
4. 输出 base64 格式

### 验证
- [ ] 大图片可正确压缩
- [ ] 压缩后图片质量可接受
- [ ] base64 数据可正确传递

---

## Task 4: 识别结果确认对话框

**文件：** `app/static/js/ai_recognize.js`

### 步骤
1. 使用 Bootstrap Modal 显示确认对话框
2. 显示识别结果摘要：
   - 采购订单：供应商、商品数量、总金额
   - 销售订单：客户、商品数量、总金额
   - 入库/出库单：商品数量
   - 收付款/费用：金额、日期
3. "确认填写"和"取消"按钮
4. 确认后调用回调函数

### 验证
- [ ] 对话框正确显示
- [ ] 识别结果正确展示
- [ ] 确认/取消按钮可用

---

## Task 5: 加载动画

**文件：** `app/static/js/ai_recognize.js`

### 步骤
1. 识别中显示加载动画
2. 覆盖在图片预览上
3. 显示"识别中..."文字
4. 禁用按钮防止重复提交

### 验证
- [ ] 加载动画正确显示
- [ ] 识别完成后动画消失
- [ ] 按钮状态正确切换

---

## Task 6: 测试

### 步骤
1. 组件初始化测试
2. 图片压缩测试
3. API 调用测试（mock）
4. 确认对话框测试
5. 错误处理测试

### 验证
- [ ] 所有测试通过
- [ ] 组件可正常使用

---

## 执行顺序
1 → 2 → 3 → 4 → 5 → 6

## 预估
2-3 天
