"""
通用工具函数 - 减少重复代码
"""
from flask import flash, redirect, url_for
from datetime import datetime
from app import db


def get_redirect_tab(default='orders'):
    """从referer获取当前tab，默认返回指定值"""
    from flask import request
    referer = request.referrer
    if referer:
        try:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(referer)
            query_params = parse_qs(parsed.query)
            if 'tab' in query_params:
                return query_params['tab'][0]
        except Exception:
            pass
    return default


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
                   getattr(model_class, 'delivery_number', None)
    
    if filter_field:
        last_order = model_class.query.filter(filter_field.like(like_pattern)).order_by(
            model_class.id.desc()
        ).first()
    else:
        last_order = None
    
    if last_order:
        # 尝试从订单号提取序号
        order_str = str(last_order.order_number or last_order.receipt_number or last_order.delivery_number)
        prefix_len = len(prefix) + len(today)
        if len(order_str) > prefix_len:
            try:
                last_num = int(order_str[prefix_len:])
                return f'{prefix}{today}{last_num + 1:03d}'
            except (ValueError, IndexError):
                pass
        return f'{prefix}{today}001'
    return f'{prefix}{today}001'


def generate_purchase_order_number():
    """生成采购订单编号"""
    today = datetime.now().strftime('%Y%m%d')
    like_pattern = f'PO{today}%'
    last_order = PurchaseOrder.query.filter(
        PurchaseOrder.order_number.like(like_pattern)
    ).order_by(PurchaseOrder.id.desc()).first()
    
    if last_order and len(last_order.order_number) > 10:
        try:
            last_num = int(last_order.order_number[10:])
            return f'PO{today}{last_num + 1:03d}'
        except (ValueError, IndexError):
            pass
    return f'PO{today}001'


def generate_sales_order_number():
    """生成销售订单编号"""
    today = datetime.now().strftime('%Y%m%d')
    like_pattern = f'SO{today}%'
    last_order = SalesOrder.query.filter(
        SalesOrder.order_number.like(like_pattern)
    ).order_by(SalesOrder.id.desc()).first()
    
    if last_order and len(last_order.order_number) > 10:
        try:
            last_num = int(last_order.order_number[10:])
            return f'SO{today}{last_num + 1:03d}'
        except (ValueError, IndexError):
            pass
    return f'SO{today}001'


def generate_stock_in_number():
    """生成入库单编号"""
    today = datetime.now().strftime('%Y%m%d')
    like_pattern = f'SI{today}%'
    last_order = StockIn.query.filter(
        StockIn.receipt_number.like(like_pattern)
    ).order_by(StockIn.id.desc()).first()
    
    if last_order and len(last_order.receipt_number) > 10:
        try:
            last_num = int(last_order.receipt_number[10:])
            return f'SI{today}{last_num + 1:03d}'
        except (ValueError, IndexError):
            pass
    return f'SI{today}001'


def generate_stock_out_number():
    """生成出库单编号"""
    today = datetime.now().strftime('%Y%m%d')
    like_pattern = f'OUT{today}%'
    last_order = StockOut.query.filter(
        StockOut.delivery_number.like(like_pattern)
    ).order_by(StockOut.id.desc()).first()
    
    if last_order and len(last_order.delivery_number) > 11:
        try:
            last_num = int(last_order.delivery_number[11:])
            return f'OUT{today}{last_num + 1:03d}'
        except (ValueError, IndexError):
            pass
    return f'OUT{today}001'


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
    
    before_quantity = float(product.stock_quantity)
    
    if change_type == 'in':
        after_quantity = before_quantity + quantity
    else:  # out
        after_quantity = before_quantity - quantity
    
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


# 延迟导入避免循环引用
from app.models import PurchaseOrder, SalesOrder, StockIn, StockOut
