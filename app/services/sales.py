"""
销售服务 — 销售订单、出库、退货业务逻辑
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Tuple, List

from app import db
from app.models import (
    SalesOrder, SalesOrderItem, StockOut, StockOutItem,
    StockLog, SalesReturn, SalesReturnItem, Product,
)
from app.utils import to_decimal, generate_order_number, update_stock_and_log


class SalesService:
    """销售服务类"""

    @staticmethod
    def create_order(
        customer_id: int,
        warehouse_id: int,
        order_date: str,
        items: List[dict],
        notes: str = '',
        status: str = 'confirmed',
        user_id: int = None,
    ) -> Tuple[Optional[SalesOrder], Optional[str]]:
        """
        创建销售订单

        Args:
            customer_id: 客户ID
            warehouse_id: 仓库ID
            order_date: 订单日期 (YYYY-MM-DD)
            items: 商品明细列表 [{'product_id': int, 'quantity': float, 'unit_price': float}]
            notes: 备注
            status: 订单状态
            user_id: 创建用户ID

        Returns:
            (order, error_message)
        """
        if not customer_id or not warehouse_id or not order_date:
            return None, '请填写必填字段'

        order_number = generate_order_number('SO', SalesOrder)

        try:
            parsed_date = datetime.strptime(order_date, '%Y-%m-%d').date()
        except ValueError:
            return None, '日期格式无效'

        order = SalesOrder(
            order_number=order_number,
            customer_id=customer_id,
            warehouse_id=warehouse_id,
            order_date=parsed_date,
            notes=notes,
            created_by=user_id,
            status=status,
        )
        db.session.add(order)
        db.session.flush()

        total_amount = Decimal('0')
        for item_data in items:
            pid = item_data.get('product_id')
            qty = item_data.get('quantity')
            price = item_data.get('unit_price')

            if not pid or not qty or not price:
                continue

            product = db.session.get(Product, int(pid))
            if not product:
                continue

            quantity = to_decimal(qty)
            unit_price = to_decimal(price)
            amount = quantity * unit_price

            item = SalesOrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=unit_price,
                amount=amount,
            )
            db.session.add(item)
            total_amount += amount

        order.total_amount = total_amount
        return order, None

    @staticmethod
    def quick_stock_out(order_id: int, user_id: int = None) -> Tuple[bool, Optional[str]]:
        """
        快速出库

        Args:
            order_id: 销售订单ID
            user_id: 操作用户ID

        Returns:
            (success, error_message)
        """
        order = db.session.query(SalesOrder).filter(
            SalesOrder.id == order_id
        ).first()

        if not order:
            return False, '订单不存在'

        if order.status == 'completed':
            return False, '订单已完成，不能重复出库'

        if not order.items:
            return False, '订单没有商品明细'

        stock_out = StockOut(
            delivery_number=generate_order_number('OUT', StockOut),
            sales_order_id=order.id,
            warehouse_id=order.warehouse_id,
            delivery_date=datetime.now().date(),
            handler='快捷出库',
            created_by=user_id,
            status='completed',
        )
        db.session.add(stock_out)
        db.session.flush()

        for order_item in order.items:
            product = db.session.get(Product, order_item.product_id)
            if not product:
                continue

            quantity = to_decimal(order_item.quantity)
            before, after = update_stock_and_log(
                product, order.warehouse_id, quantity, 'out',
                stock_out.id, 'stock_out', f'销售出库: {order.order_number}', user_id
            )

            item = StockOutItem(
                stock_out_id=stock_out.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=order_item.unit_price,
                amount=order_item.amount,
            )
            db.session.add(item)
            order_item.delivered_quantity = quantity

        order.status = 'completed'
        return True, None

    @staticmethod
    def quick_return(order_id: int, user_id: int = None) -> Tuple[bool, Optional[str]]:
        """
        快速退货

        Args:
            order_id: 销售订单ID
            user_id: 操作用户ID

        Returns:
            (success, error_message)
        """
        order = db.session.query(SalesOrder).filter(
            SalesOrder.id == order_id
        ).first()

        if not order:
            return False, '订单不存在'

        if order.status != 'completed':
            return False, '只有已完成的订单可以退货'

        if not order.items:
            return False, '订单没有商品明细'

        return_number = generate_order_number('SR', SalesReturn)
        sales_return = SalesReturn(
            return_number=return_number,
            sales_order_id=order.id,
            warehouse_id=order.warehouse_id,
            return_date=datetime.now().date(),
            created_by=user_id,
            status='completed',
        )
        db.session.add(sales_return)
        db.session.flush()

        total_amount = Decimal('0')
        for order_item in order.items:
            product = db.session.get(Product, order_item.product_id)
            if not product:
                continue

            delivered_qty = to_decimal(order_item.delivered_quantity or 0)
            if delivered_qty <= 0:
                continue

            unit_price = to_decimal(order_item.unit_price)
            amount = delivered_qty * unit_price

            item = SalesReturnItem(
                return_id=sales_return.id,
                product_id=product.id,
                quantity=delivered_qty,
                unit_price=unit_price,
                amount=amount,
            )
            db.session.add(item)
            total_amount += amount

            update_stock_and_log(
                product, order.warehouse_id, delivered_qty, 'return_in',
                sales_return.id, 'sales_return',
                f'销售退货: {return_number}', user_id
            )

        sales_return.total_amount = total_amount
        return True, None
