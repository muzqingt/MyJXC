"""
库存服务 — 盘点、调拨、调整业务逻辑
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Tuple, List

from app import db
from app.models import Product, StockLog, Warehouse
from app.utils import to_decimal


class InventoryService:
    """库存服务类"""

    @staticmethod
    def stock_check(
        warehouse_id: int,
        items: List[dict],
        notes: str = '',
        user_id: int = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        库存盘点

        Args:
            warehouse_id: 仓库ID
            items: 盘点明细 [{'product_id': int, 'actual_quantity': float}]
            notes: 备注
            user_id: 操作用户ID

        Returns:
            (success, error_message)
        """
        warehouse = db.session.get(Warehouse, warehouse_id)
        if not warehouse:
            return False, '仓库不存在'

        for item_data in items:
            pid = item_data.get('product_id')
            actual_qty = item_data.get('actual_quantity')

            if not pid or actual_qty is None:
                continue

            product = db.session.query(Product).filter(
                Product.id == int(pid)
            ).with_for_update().first()

            if not product:
                continue

            book_quantity = to_decimal(product.stock_quantity)
            actual_quantity = to_decimal(actual_qty)

            if book_quantity != actual_quantity:
                diff = actual_quantity - book_quantity
                change_type = 'check_in' if diff > 0 else 'check_out'

                product.stock_quantity = actual_quantity

                log = StockLog(
                    product_id=product.id,
                    warehouse_id=warehouse_id,
                    change_type=change_type,
                    quantity=abs(diff),
                    before_quantity=book_quantity,
                    after_quantity=actual_quantity,
                    reference_type='stock_check',
                    notes=f'库存盘点: {notes}',
                    created_by=user_id,
                )
                db.session.add(log)

        return True, None

    @staticmethod
    def stock_adjust(
        product_id: int,
        warehouse_id: int,
        adjust_type: str,
        quantity: float,
        notes: str = '',
        user_id: int = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        库存调整

        Args:
            product_id: 商品ID
            warehouse_id: 仓库ID
            adjust_type: 调整类型 ('adjust_in' 或 'adjust_out')
            quantity: 调整数量
            notes: 备注
            user_id: 操作用户ID

        Returns:
            (success, error_message)
        """
        product = db.session.query(Product).filter(
            Product.id == product_id
        ).with_for_update().first()

        if not product:
            return False, '商品不存在'

        before_quantity = to_decimal(product.stock_quantity)
        qty = to_decimal(quantity)

        if adjust_type == 'adjust_in':
            after_quantity = before_quantity + qty
        elif adjust_type == 'adjust_out':
            if before_quantity < qty:
                return False, '库存不足，无法调整'
            after_quantity = before_quantity - qty
        else:
            return False, '无效的调整类型'

        product.stock_quantity = after_quantity

        log = StockLog(
            product_id=product.id,
            warehouse_id=warehouse_id,
            change_type=adjust_type,
            quantity=qty,
            before_quantity=before_quantity,
            after_quantity=after_quantity,
            reference_type='stock_adjust',
            notes=notes,
            created_by=user_id,
        )
        db.session.add(log)

        return True, None
