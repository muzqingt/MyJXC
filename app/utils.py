"""
通用工具函数 - 减少重复代码
"""
from flask import flash, redirect, url_for
from datetime import datetime

from decimal import Decimal, ROUND_HALF_UP


def to_decimal(value, default=Decimal('0')):
    """将任意值安全转换为 Decimal。保持便捷数据库切换（SQLAlchemy 会自动处理）。"""
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        try:
            return Decimal(value)
        except Exception:
            return default
    try:
        return Decimal(str(value))
    except Exception:
        return default


def add_balance(customer_or_supplier, field_name, amount):
    """原子增加余额（使用 SQL 表达式防止并发丢更新）。支持所有主流数据库。"""
    from sqlalchemy import update
    from app.models import Customer, Supplier
    Model = Customer if hasattr(customer_or_supplier, 'receivable_balance') else Supplier
    delta = to_decimal(amount)
    # 构建 SET 表达式：column + delta（数据库层原子操作）
    set_expr = getattr(Model, field_name) + delta
    stmt = (
        update(Model)
        .where(Model.id == customer_or_supplier.id)
        .values({field_name: set_expr})
    )
    db.session.execute(stmt)
    # 刷新 ORM 对象，防止后续 commit() 用脏数据覆盖刚写入的数据库值
    db.session.refresh(customer_or_supplier)


def sub_balance(customer_or_supplier, field_name, amount):
    """原子减少余额（使用 SQL 表达式防止并发丢更新）。支持所有主流数据库。"""
    from sqlalchemy import update
    from app.models import Customer, Supplier
    Model = Customer if hasattr(customer_or_supplier, 'receivable_balance') else Supplier
    delta = to_decimal(amount)
    set_expr = getattr(Model, field_name) - delta
    stmt = (
        update(Model)
        .where(Model.id == customer_or_supplier.id)
        .values({field_name: set_expr})
    )
    db.session.execute(stmt)
    # 刷新 ORM 对象，防止后续 commit() 用脏数据覆盖刚写入的数据库值
    db.session.refresh(customer_or_supplier)

from app import db


def generate_order_number(prefix, model_class, date_field_name='created_at'):
    """
    生成订单编号，如 PO20240101001
    
    Args:
        prefix: 订单前缀，如 'PO', 'SI', 'SO', 'OUT'
        model_class: 模型类
        date_field_name: 日期字段名（用于构建like查询）
    """
    today = datetime.now().strftime('%Y%m%d')
    like_pattern = f'{prefix}{today}%'
    
    # 使用filter通过字段名构建查询
    filter_field = getattr(model_class, 'order_number', None) or \
                   getattr(model_class, 'receipt_number', None) or \
                   getattr(model_class, 'delivery_number', None) or \
                   getattr(model_class, 'return_number', None)
    
    if filter_field:
        last_order = model_class.query.filter(filter_field.like(like_pattern)).order_by(
            model_class.id.desc()
        ).first()
    else:
        last_order = None
    
    if last_order:
        # 尝试从订单号提取序号
        order_str = str(last_order.order_number or last_order.receipt_number or last_order.delivery_number or last_order.return_number)
        prefix_len = len(prefix) + len(today)
        if len(order_str) > prefix_len:
            try:
                last_num = int(order_str[prefix_len:])
                return f'{prefix}{today}{last_num + 1:03d}'
            except (ValueError, IndexError):
                pass
        return f'{prefix}{today}001'
    return f'{prefix}{today}001'


def build_products_data(products, include_purchase_price=True, include_sale_price=True):
    """构建商品下拉数据"""
    result = []
    for p in products:
        item = {
            'id': p.id,
            'code': p.code,
            'name': p.name,
            'specification': p.specification or '',
            'unit': p.unit,
            'stock_quantity': float(p.stock_quantity) if p.stock_quantity else 0
        }
        if include_purchase_price and hasattr(p, 'purchase_price'):
            item['purchase_price'] = float(p.purchase_price) if p.purchase_price else 0
        if include_sale_price and hasattr(p, 'sale_price'):
            item['sale_price'] = float(p.sale_price) if p.sale_price else 0
        result.append(item)
    return result


def build_partners_data(partners):
    """构建合作伙伴（供应商/客户）下拉数据"""
    return [{
        'id': p.id,
        'code': p.code,
        'name': p.name
    } for p in partners]


def flash_success(message, endpoint=None, **kwargs):
    """成功消息并重定向"""
    flash(message, 'success')
    if endpoint:
        return redirect(url_for(endpoint, **kwargs))
    return None


def flash_error(message, endpoint=None, **kwargs):
    """错误消息并重定向"""
    flash(message, 'danger')
    if endpoint:
        return redirect(url_for(endpoint, **kwargs))
    return None


def update_stock_and_log(product, warehouse_id, quantity, change_type, 
                         reference_id, reference_type, notes, user_id):
    """
    更新库存并记录库存流水
    
    Args:
        product: 商品对象
        warehouse_id: 仓库ID
        quantity: 变动数量
        change_type: 'in' 或 'out'
        reference_id: 相关单据ID
        reference_type: 相关单据类型
        notes: 备注
        user_id: 用户ID
    
    Returns:
        (before_quantity, after_quantity)
    """
    from app.models import StockLog
    
    before_quantity = to_decimal(product.stock_quantity)
    delta = to_decimal(quantity)

    if change_type == 'in':
        after_quantity = before_quantity + delta
    else:  # out
        after_quantity = before_quantity - delta
    
    product.stock_quantity = after_quantity
    
    log = StockLog(
        product_id=product.id,
        warehouse_id=warehouse_id,
        change_type=change_type,
        quantity=quantity,
        before_quantity=before_quantity,
        after_quantity=after_quantity,
        reference_id=reference_id,
        reference_type=reference_type,
        notes=notes,
        created_by=user_id
    )
    db.session.add(log)
    
    return before_quantity, after_quantity


def safe_commit():
    """安全提交事务"""
    try:
        db.session.commit()
        return True, None
    except Exception as e:
        db.session.rollback()
        return False, str(e)


def localize_dt(dt):
    """将存储的UTC时间转换为本地时间（亚洲/上海）"""
    from datetime import timezone, timedelta
    if dt is None:
        return ''
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone(timedelta(hours=8)))


def format_local_dt(dt, fmt='%Y-%m-%d %H:%M:%S'):
    """格式化本地时间，默认格式：2024-01-01 12:00:00"""
    if dt is None:
        return ''
    local = localize_dt(dt)
    return local.strftime(fmt)


def get_redirect_tab(status=None):
    """根据订单状态确定跳转的标签页"""
    if status == 'draft':
        return 'draft'
    elif status in ('confirmed', 'partial'):
        return 'confirmed'
    elif status == 'completed':
        return 'completed'
    return 'draft'


# Excel 导出样式常量
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment

EXCEL_HEADER_FONT = Font(bold=True, size=11)
EXCEL_HEADER_FILL = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')
EXCEL_THIN_BORDER = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)
EXCEL_HEADER_ALIGNMENT = Alignment(horizontal='center', vertical='center')


def apply_excel_header_style(ws, row, max_col):
    """为 Excel 表头行应用统一样式"""
    for col in range(1, max_col + 1):
        cell = ws.cell(row=row, column=col)
        cell.font = EXCEL_HEADER_FONT
        cell.fill = EXCEL_HEADER_FILL
        cell.border = EXCEL_THIN_BORDER
        cell.alignment = EXCEL_HEADER_ALIGNMENT


PAYMENT_METHOD_MAP = {
    'cash': '现金',
    'bank_transfer': '银行转账',
    'check': '支票',
    'wechat': '微信',
    'alipay': '支付宝',
    'other': '其他'
}
