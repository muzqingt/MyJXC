"""
订单相关工具函数 — 消除重复代码
"""
from decimal import Decimal
from typing import Optional, List

from app import db
from app.models import StockLog, Product
from app.utils import to_decimal


def parse_reference_ids(reference_id: Optional[str]) -> List[int]:
    """
    解析逗号分隔的关联单据 ID

    Args:
        reference_id: 逗号分隔的 ID 字符串，如 "1,2,3"

    Returns:
        ID 列表，如 [1, 2, 3]
    """
    if not reference_id:
        return []
    try:
        return [int(oid.strip()) for oid in reference_id.split(',') if oid.strip()]
    except ValueError:
        return []


def create_stock_log(
    product: Product,
    warehouse_id: int,
    change_type: str,
    quantity: Decimal,
    reference_id: int,
    reference_type: str,
    notes: str = '',
    user_id: int = None,
) -> StockLog:
    """
    统一创建库存变动日志

    Args:
        product: 商品对象
        warehouse_id: 仓库 ID
        change_type: 变动类型 (in, out, adjust_in, adjust_out, etc.)
        quantity: 变动数量
        reference_id: 关联单据 ID
        reference_type: 关联单据类型
        notes: 备注
        user_id: 操作用户 ID

    Returns:
        创建的 StockLog 对象
    """
    before_quantity = to_decimal(product.stock_quantity)
    delta = to_decimal(quantity)

    if change_type.endswith('_in') or change_type == 'in':
        after_quantity = before_quantity + delta
    else:
        after_quantity = before_quantity - delta

    product.stock_quantity = after_quantity

    log = StockLog(
        product_id=product.id,
        warehouse_id=warehouse_id,
        change_type=change_type,
        quantity=delta,
        before_quantity=before_quantity,
        after_quantity=after_quantity,
        reference_id=reference_id,
        reference_type=reference_type,
        notes=notes,
        created_by=user_id,
    )
    db.session.add(log)
    return log


def rebuild_items_on_error(
    product_ids: List[str],
    quantities: List[str],
    unit_prices: List[str],
    product_class: type = Product,
) -> List[dict]:
    """
    错误时重建商品明细数据（用于表单回填）

    Args:
        product_ids: 商品 ID 列表
        quantities: 数量列表
        unit_prices: 单价列表
        product_class: 商品模型类

    Returns:
        明细数据列表
    """
    items = []
    for i in range(len(product_ids)):
        if product_ids[i] and quantities[i] and unit_prices[i]:
            try:
                pid = int(product_ids[i])
            except ValueError:
                continue
            product = db.session.get(product_class, pid)
            if product:
                items.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'product_code': product.code,
                    'quantity': quantities[i],
                    'unit_price': unit_prices[i],
                })
    return items


def validate_order_items(
    product_ids: List[str],
    quantities: List[str],
    unit_prices: List[str],
) -> bool:
    """
    验证订单明细是否有效

    Args:
        product_ids: 商品 ID 列表
        quantities: 数量列表
        unit_prices: 单价列表

    Returns:
        True 如果至少有一个有效明细
    """
    if not product_ids:
        return False

    for i in range(len(product_ids)):
        if product_ids[i] and quantities[i] and unit_prices[i]:
            try:
                pid = int(product_ids[i])
                qty = to_decimal(quantities[i])
                price = to_decimal(unit_prices[i])
                if pid > 0 and qty > 0 and price >= 0:
                    return True
            except (ValueError, TypeError):
                continue

    return False
