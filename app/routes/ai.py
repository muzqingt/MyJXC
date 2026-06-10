"""
AI 单据识别路由
"""
import json
import base64
import requests
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import SystemSetting

bp = Blueprint('ai', __name__, url_prefix='/api/ai')

# 各单据类型的 prompt
PROMPTS = {
    'purchase': """你是一个单据识别助手。请识别图片中的采购单据（采购订单、采购发票等），返回以下JSON格式：
{
  "supplier_name": "供应商名称",
  "order_date": "YYYY-MM-DD",
  "items": [
    {"name": "商品名称", "quantity": 数量, "unit_price": 单价, "specification": "规格"}
  ],
  "notes": "备注"
}
如果某个字段无法识别，返回null。只返回JSON，不要其他文字。""",

    'sales': """你是一个单据识别助手。请识别图片中的销售单据（销售订单、销售发票等），返回以下JSON格式：
{
  "customer_name": "客户名称",
  "order_date": "YYYY-MM-DD",
  "items": [
    {"name": "商品名称", "quantity": 数量, "unit_price": 单价, "specification": "规格"}
  ],
  "notes": "备注"
}
如果某个字段无法识别，返回null。只返回JSON，不要其他文字。""",

    'stock_in': """你是一个单据识别助手。请识别图片中的入库单据（入库单、送货单等），返回以下JSON格式：
{
  "receipt_date": "YYYY-MM-DD",
  "items": [
    {"name": "商品名称", "quantity": 数量, "unit_price": 单价}
  ],
  "notes": "备注"
}
如果某个字段无法识别，返回null。只返回JSON，不要其他文字。""",

    'stock_out': """你是一个单据识别助手。请识别图片中的出库单据（出库单、发货单等），返回以下JSON格式：
{
  "delivery_date": "YYYY-MM-DD",
  "items": [
    {"name": "商品名称", "quantity": 数量, "unit_price": 单价}
  ],
  "notes": "备注"
}
如果某个字段无法识别，返回null。只返回JSON，不要其他文字。""",

    'receipt': """你是一个单据识别助手。请识别图片中的收款单据（收款单、收据等），返回以下JSON格式：
{
  "amount": 金额,
  "receipt_date": "YYYY-MM-DD",
  "payment_method": "cash/bank_transfer/wechat/alipay",
  "notes": "备注"
}
如果某个字段无法识别，返回null。只返回JSON，不要其他文字。""",

    'payment': """你是一个单据识别助手。请识别图片中的付款单据（付款单、付款凭证等），返回以下JSON格式：
{
  "amount": 金额,
  "payment_date": "YYYY-MM-DD",
  "payment_method": "cash/bank_transfer/wechat/alipay",
  "notes": "备注"
}
如果某个字段无法识别，返回null。只返回JSON，不要其他文字。""",

    'expense': """你是一个单据识别助手。请识别图片中的费用单据（费用报销单、发票等），返回以下JSON格式：
{
  "category": "费用类别",
  "amount": 金额,
  "expense_date": "YYYY-MM-DD",
  "payee": "收款方",
  "payment_method": "cash/bank_transfer/wechat/alipay",
  "notes": "备注"
}
如果某个字段无法识别，返回null。只返回JSON，不要其他文字。""",

    'return': """你是一个单据识别助手。请识别图片中的退货单据（退货单、退货申请等），返回以下JSON格式：
{
  "return_date": "YYYY-MM-DD",
  "items": [
    {"name": "商品名称", "quantity": 数量, "unit_price": 单价}
  ],
  "notes": "备注"
}
如果某个字段无法识别，返回null。只返回JSON，不要其他文字。""",
}


def _get_ai_config():
    """获取 AI 配置"""
    api_url = SystemSetting.get_value('AI_API_URL', '')
    api_key = SystemSetting.get_value('AI_API_KEY', '')
    model_name = SystemSetting.get_value('AI_MODEL_NAME', '')
    return api_url, api_key, model_name


def _call_ai_api(api_url, api_key, model_name, prompt, image_base64, timeout=30):
    """调用 OpenAI 兼容 API"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }

    # 确保 URL 以 /v1/chat/completions 结尾
    if not api_url.endswith('/'):
        api_url += '/'
    if not api_url.endswith('chat/completions'):
        api_url += 'chat/completions'

    data = {
        'model': model_name,
        'messages': [
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': [
                {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{image_base64}'}}
            ]}
        ],
        'max_tokens': 2000,
        'temperature': 0.1,
    }

    response = requests.post(api_url, headers=headers, json=data, timeout=timeout)
    response.raise_for_status()

    result = response.json()
    content = result['choices'][0]['message']['content']

    # 尝试解析 JSON
    # 处理可能的 markdown 代码块
    content = content.strip()
    if content.startswith('```'):
        content = content.split('\n', 1)[1] if '\n' in content else content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()

    return json.loads(content)


@bp.route('/recognize', methods=['POST'])
@login_required
def recognize():
    """AI 单据识别"""
    api_url, api_key, model_name = _get_ai_config()

    if not api_url or not api_key or not model_name:
        return jsonify({'success': False, 'message': '请先在系统设置中配置 AI 服务'}), 400

    image_base64 = request.form.get('image_base64', '')
    doc_type = request.form.get('doc_type', '')

    if not image_base64:
        return jsonify({'success': False, 'message': '请提供图片'}), 400

    if doc_type not in PROMPTS:
        return jsonify({'success': False, 'message': f'不支持的单据类型: {doc_type}'}), 400

    # 移除 data:image/xxx;base64, 前缀
    if ',' in image_base64:
        image_base64 = image_base64.split(',', 1)[1]

    prompt = PROMPTS[doc_type]

    try:
        result = _call_ai_api(api_url, api_key, model_name, prompt, image_base64)
        return jsonify({'success': True, 'data': result})
    except requests.Timeout:
        return jsonify({'success': False, 'message': 'AI 服务响应超时，请重试'}), 504
    except requests.ConnectionError:
        return jsonify({'success': False, 'message': '无法连接到 AI 服务，请检查 API 地址'}), 502
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            return jsonify({'success': False, 'message': 'API 密钥无效，请检查配置'}), 401
        return jsonify({'success': False, 'message': f'AI 服务返回错误: {e.response.status_code}'}), 502
    except (json.JSONDecodeError, KeyError, IndexError):
        return jsonify({'success': False, 'message': 'AI 返回的数据格式无法解析，请重试'}), 500
    except Exception as e:
        current_app.logger.error(f'AI 识别失败: {e}')
        return jsonify({'success': False, 'message': f'识别失败: {str(e)}'}), 500


@bp.route('/test-connection', methods=['POST'])
@login_required
def test_connection():
    """测试 AI 连接"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '仅管理员可执行此操作'}), 403

    api_url = request.form.get('api_url', '')
    api_key = request.form.get('api_key', '')
    model_name = request.form.get('model_name', '')

    if not api_url or not api_key or not model_name:
        return jsonify({'success': False, 'message': '请填写完整的 AI 配置'}), 400

    # 发送一个简单的文本请求测试连接
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }

    if not api_url.endswith('/'):
        api_url += '/'
    if not api_url.endswith('chat/completions'):
        api_url += 'chat/completions'

    data = {
        'model': model_name,
        'messages': [
            {'role': 'user', 'content': '请回复"连接成功"四个字'}
        ],
        'max_tokens': 50,
    }

    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        content = result['choices'][0]['message']['content']
        return jsonify({'success': True, 'message': f'连接成功！模型响应: {content[:50]}'})
    except requests.Timeout:
        return jsonify({'success': False, 'message': '连接超时，请检查 API 地址'})
    except requests.ConnectionError:
        return jsonify({'success': False, 'message': '无法连接到 API，请检查地址是否正确'})
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            return jsonify({'success': False, 'message': 'API 密钥无效'})
        return jsonify({'success': False, 'message': f'API 返回错误: {e.response.status_code}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'连接失败: {str(e)}'})
