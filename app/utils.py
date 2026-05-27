"""
通用工具函数 - 减少重复代码
"""
from flask import flash, redirect, url_for
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional, Tuple, Union

from app import db
from sqlalchemy.exc import SQLAlchemyError


def to_decimal(value: Any, default: Decimal = Decimal('0')) -> Decimal:
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


def add_balance(customer_or_supplier: Any, field_name: str, amount: Union[float, Decimal, str]) -> None:
    """
    原子增加余额（使用 SQL 表达式防止并发丢更新）。

    使用 UPDATE ... SET field = field + delta 的 SQL 表达式在数据库层完成加法运算，
    而非先读后写。这样即使多个请求并发修改同一行，也不会出现"丢失更新"问题。
    最后调用 session.refresh() 刷新 ORM 对象，确保后续代码读到的是数据库最新值。
    """
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


def sub_balance(customer_or_supplier: Any, field_name: str, amount: Union[float, Decimal, str]) -> None:
    """
    原子减少余额（使用 SQL 表达式防止并发丢更新）。

    与 add_balance 原理相同，使用 UPDATE ... SET field = field - delta 在数据库层
    完成减法运算，避免并发场景下的"丢失更新"问题。
    """
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


def generate_order_number(prefix: str, model_class: type, date_field_name: str = 'created_at') -> str:
    """
    生成订单编号。

    编号格式：{前缀}{日期}{序号}，例如 PO20240101001、SI20240115003。
    - 前缀：PO（采购）、SI（采购入库）、SO（销售）、OUT（出库）等
    - 日期：8 位年月日，如 20240101
    - 序号：3 位数字，从 001 开始，同一天自动递增

    通过 LIKE 查询当日最大编号，提取序号部分并 +1 实现自增。
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
                return f'{prefix}{today}{last_num + 1:04d}'
            except (ValueError, IndexError):
                pass
        return f'{prefix}{today}0001'
    return f'{prefix}{today}0001'


def build_products_data(products: list, include_purchase_price: bool = True, include_sale_price: bool = True) -> list[dict]:
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


def build_partners_data(partners: list) -> list[dict]:
    """构建合作伙伴（供应商/客户）下拉数据"""
    return [{
        'id': p.id,
        'code': p.code,
        'name': p.name
    } for p in partners]


def flash_success(message: str, endpoint: Optional[str] = None, **kwargs: Any) -> Optional[Any]:
    """成功消息并重定向"""
    flash(message, 'success')
    if endpoint:
        return redirect(url_for(endpoint, **kwargs))
    return None


def flash_error(message: str, endpoint: Optional[str] = None, **kwargs: Any) -> Optional[Any]:
    """错误消息并重定向"""
    flash(message, 'danger')
    if endpoint:
        return redirect(url_for(endpoint, **kwargs))
    return None


def update_stock_and_log(product: Any, warehouse_id: int, quantity: Union[float, Decimal, str],
                         change_type: str, reference_id: int, reference_type: str,
                         notes: str, user_id: int) -> Tuple[Decimal, Decimal]:
    """
    更新商品库存数量并记录一条库存变动流水。

    before_quantity 取自 product.stock_quantity 当前值（即数据库中该商品的库存），
    after_quantity 通过 before_quantity +/- quantity 计算得出：
      - change_type='in'  时：after = before + delta（入库）
      - change_type='out' 时：after = before - delta（出库）
    计算完成后将新值写回 product.stock_quantity，并创建 StockLog 记录完整快照。

    Returns:
        (before_quantity, after_quantity) - 变动前后的库存数量
    """
    from app.models import StockLog
    
    valid_change_types = ('in', 'out', 'adjust_in', 'adjust_out', 'check_in', 'check_out', 'return_in', 'return_out', 'stock_transfer')
    if change_type not in valid_change_types:
        raise ValueError(f"Invalid change_type: {change_type}")

    before_quantity = to_decimal(product.stock_quantity)
    delta = to_decimal(quantity)

    if change_type == 'in' or change_type.endswith('_in'):
        after_quantity = before_quantity + delta
    else:
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


def safe_commit() -> Tuple[bool, Optional[str]]:
    """
    安全提交数据库事务。

    Returns:
        (success, error_message)：
        - 成功时返回 (True, None)
        - 失败时自动回滚事务并返回 (False, 错误信息字符串)
    """
    try:
        db.session.commit()
        return True, None
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, str(e)


def localize_dt(dt: Any) -> Any:
    """将存储的UTC时间转换为本地时间（亚洲/上海）"""
    from datetime import timezone, timedelta
    if dt is None:
        return ''
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone(timedelta(hours=8)))


def format_local_dt(dt: Any, fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    """格式化本地时间，默认格式：2024-01-01 12:00:00"""
    if dt is None:
        return ''
    local = localize_dt(dt)
    return local.strftime(fmt)


def get_redirect_tab(status: Optional[str] = None) -> str:
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


def apply_excel_header_style(ws: Any, row: int, max_col: int) -> None:
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
