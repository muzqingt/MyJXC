"""重置数据库并生成测试数据"""
import sys
sys.path.insert(0, '.')
from app import create_app, db
from app.models import (
    User, Product, Category, Supplier, Customer, Warehouse,
    PurchaseOrder, PurchaseOrderItem, StockIn, StockInItem,
    SalesOrder, SalesOrderItem, StockOut, StockOutItem,
    Receipt, Payment, Expense, StockLog, Log, SystemSetting
)
from datetime import datetime, timedelta
from decimal import Decimal
import random

# 全局计数器
si_counter = 0
out_counter = 0
rc_counter = 0
py_counter = 0

app = create_app()
with app.app_context():
    print("删除旧表...")
    db.drop_all()
    db.create_all()
    print("建表完成")

    # 创建管理员
    admin = User(username='admin', email='admin@example.com', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)

    # 创建系统设置
    setting = SystemSetting(setting_key='default_warehouse', value='1')
    db.session.add(setting)

    # 分类
    categories = []
    for name in ['办公用品', '电子设备', '食品饮料', '五金工具', '清洁用品']:
        c = Category(name=name)
        db.session.add(c)
        categories.append(c)
    db.session.flush()

    # 仓库
    warehouses = []
    for code, name in [('WH01', '主仓库'), ('WH02', '北仓库'), ('WH03', '门店仓')]:
        w = Warehouse(code=code, name=name, manager='管理员', phone='13800000001')
        db.session.add(w)
        warehouses.append(w)
    db.session.flush()

    # 商品（每个分类3-5个）
    products_data = [
        # 办公用品
        ('A001', '中性笔', '支', 1.5, 2.5, 500, 'WH01'),
        ('A002', '笔记本', '本', 4.0, 7.0, 200, 'WH01'),
        ('A003', '订书机', '个', 8.0, 15.0, 80, 'WH01'),
        ('A004', '打印纸 A4', '包', 18.0, 32.0, 150, 'WH01'),
        ('A005', '文件袋', '个', 2.0, 4.0, 300, 'WH01'),
        # 电子设备
        ('E001', '鼠标', '个', 25.0, 55.0, 60, 'WH01'),
        ('E002', '键盘', '个', 45.0, 88.0, 40, 'WH01'),
        ('E003', 'U盘 32G', '个', 18.0, 38.0, 100, 'WH01'),
        ('E004', '移动硬盘', '个', 180.0, 320.0, 20, 'WH02'),
        # 食品饮料
        ('F001', '矿泉水', '瓶', 0.8, 2.0, 600, 'WH03'),
        ('F002', '方便面', '桶', 2.5, 5.0, 400, 'WH03'),
        ('F003', '饼干', '包', 4.0, 8.5, 250, 'WH03'),
        # 五金工具
        ('T001', '螺丝刀套装', '套', 15.0, 35.0, 30, 'WH02'),
        ('T002', '扳手', '把', 12.0, 28.0, 50, 'WH02'),
        ('T003', '电钻', '台', 120.0, 260.0, 10, 'WH02'),
        # 清洁用品
        ('C001', '洗洁精', '瓶', 3.5, 7.0, 180, 'WH01'),
        ('C002', '84消毒液', '瓶', 2.0, 5.0, 200, 'WH01'),
        ('C003', '拖把', '把', 8.0, 18.0, 60, 'WH01'),
        ('C004', '垃圾袋', '包', 5.0, 12.0, 150, 'WH01'),
    ]
    products = []
    for i, (code, name, unit, pp, sp, sq, _wh) in enumerate(products_data):
        p = Product(
            code=code, name=name, unit=unit,
            purchase_price=pp, sale_price=sp,
            stock_quantity=sq, category_id=categories[i % len(categories)].id
        )
        db.session.add(p)
        products.append(p)
    db.session.flush()

    # 为初始库存创建StockLog
    for p in products:
        log = StockLog(
            product_id=p.id,
            warehouse_id=1,
            change_type='in',
            quantity=float(p.stock_quantity),
            before_quantity=0,
            after_quantity=float(p.stock_quantity),
            reference_type='initial',
            notes='初始化库存',
            created_by=1
        )
        db.session.add(log)

    # 供应商
    suppliers_data = [
        ('S001', '北京办公用品批发', '李经理', '13800138001', 'li@bjbg.com'),
        ('S002', '深圳电子科技', '张工', '13800138002', 'zhang@szdz.com'),
        ('S003', '上海食品供应链', '王总', '13800138003', 'wang@shsp.com'),
        ('S004', '广州五金批发中心', '陈老板', '13800138004', 'chen@gzwj.com'),
    ]
    suppliers = []
    for code, name, contact, phone, email in suppliers_data:
        s = Supplier(code=code, name=name, contact_person=contact, phone=phone, email=email)
        db.session.add(s)
        suppliers.append(s)
    db.session.flush()

    # 客户
    customers_data = [
        ('C001', '杭州科技有限公司', '刘总', '13900139001', 'liu@hztech.com'),
        ('C002', '南京贸易公司', '赵经理', '13900139002', 'zhao@njmy.com'),
        ('C003', '武汉实业集团', '周总', '13900139003', 'zhou@whsy.com'),
        ('C004', '西安便利店连锁', '吴老板', '13900139004', 'wu@xabk.com'),
    ]
    customers = []
    for code, name, contact, phone, email in customers_data:
        c = Customer(code=code, name=name, contact_person=contact, phone=phone, email=email)
        db.session.add(c)
        customers.append(c)
    db.session.flush()

    print("基础数据创建完成，开始模拟历史数据...")

    today = datetime.now().date()
    start_date = today - timedelta(days=90)

    def next_date(days_offset=0):
        return (start_date + timedelta(days=random.randint(0, 90) + days_offset)).strftime('%Y%m%d')

    def gen_po_number(date):
        return f"PO{date}{random.randint(1, 999):03d}"

    def gen_so_number(date):
        return f"SO{date}{random.randint(1, 999):03d}"

    def gen_si_number(date):
        return f"SI{date}{random.randint(1, 999):03d}"

    def gen_out_number(date):
        return f"OUT{date}{random.randint(1, 999):03d}"

    def gen_rc_number(date):
        return f"RC{date}{random.randint(1, 999):03d}"

    def gen_py_number(date):
        return f"PY{date}{random.randint(1, 999):03d}"

    # 模拟90天内每天的业务
    po_count = si_count = so_count = out_count = 0
    for day in range(90):
        current_date = start_date + timedelta(days=day)
        date_str = current_date.strftime('%Y%m%d')

        # 每天1-3个采购订单
        for _ in range(random.randint(1, 3)):
            supplier = random.choice(suppliers)
            warehouse = random.choice(warehouses)
            po_num = gen_po_number(date_str)
            po = PurchaseOrder(
                order_number=po_num, supplier_id=supplier.id,
                warehouse_id=warehouse.id,
                order_date=current_date,
                expected_date=current_date + timedelta(days=random.randint(3, 7)),
                status=random.choice(['confirmed', 'confirmed', 'partial', 'completed']),
                total_amount=0, created_by=admin.id
            )
            db.session.add(po)
            db.session.flush()

            # 订单明细
            total = Decimal('0')
            sel_products = random.sample(products, random.randint(2, 5))
            for p in sel_products:
                qty = random.randint(10, 100)
                price = Decimal(str(p.purchase_price))
                amount = Decimal(qty) * price
                total += amount
                item = PurchaseOrderItem(
                    order_id=po.id, product_id=p.id,
                    quantity=qty, unit_price=price, amount=amount
                )
                db.session.add(item)
            po.total_amount = total
            po_count += 1

            # 供应商应付余额累加（confirmed/partial/completed才累加）
            if po.status in ['confirmed', 'partial', 'completed']:
                supplier.payable_balance = Decimal(str(supplier.payable_balance)) + total

        # 每天1-2个销售订单
        for _ in range(random.randint(1, 2)):
            customer = random.choice(customers)
            warehouse = random.choice(warehouses)
            so_num = gen_so_number(date_str)
            so = SalesOrder(
                order_number=so_num, customer_id=customer.id,
                warehouse_id=warehouse.id,
                order_date=current_date,
                delivery_date=current_date + timedelta(days=random.randint(1, 5)),
                status=random.choice(['confirmed', 'confirmed', 'partial', 'completed']),
                total_amount=0, created_by=admin.id
            )
            db.session.add(so)
            db.session.flush()

            total = Decimal('0')
            sel_products = random.sample(products, random.randint(1, 4))
            for p in sel_products:
                qty = random.randint(1, 20)
                price = Decimal(str(p.sale_price))
                amount = Decimal(qty) * price
                total += amount
                item = SalesOrderItem(
                    order_id=so.id, product_id=p.id,
                    quantity=qty, unit_price=price, amount=amount
                )
                db.session.add(item)
            so.total_amount = total
            so_count += 1

            # 客户应收余额累加
            if so.status in ['confirmed', 'partial', 'completed']:
                customer.receivable_balance = Decimal(str(customer.receivable_balance)) + total

    db.session.commit()
    print(f"创建了 {po_count} 个采购订单, {so_count} 个销售订单")

    # 重新查询所有订单，按日期排序
    all_pos = PurchaseOrder.query.order_by(PurchaseOrder.order_date).all()
    all_sos = SalesOrder.query.order_by(SalesOrder.order_date).all()

    # 入库：只为前70%的采购订单生成入库单
    po_si_map = {}  # po_id -> [stock_in_ids]
    for po in all_pos[:int(len(all_pos) * 0.7)]:
        date_str = po.order_date.strftime('%Y%m%d')
        si_counter += 1
        si_num = f"SI{date_str}{si_counter:03d}"
        si = StockIn(
            receipt_number=si_num, purchase_order_id=po.id,
            warehouse_id=po.warehouse_id,
            receipt_date=po.order_date + timedelta(days=random.randint(0, 2)),
            handler='admin', status='completed',
            total_amount=po.total_amount, created_by=admin.id
        )
        db.session.add(si)
        db.session.flush()

        if po.id not in po_si_map:
            po_si_map[po.id] = []
        po_si_map[po.id].append(si.id)

        for item in po.items:
            si_item = StockInItem(
                stock_in_id=si.id, product_id=item.product_id,
                quantity=item.quantity, unit_price=float(item.unit_price),
                amount=item.amount
            )
            db.session.add(si_item)
            # 更新库存
            p = item.product
            p.stock_quantity = float(p.stock_quantity) + float(item.quantity)
            # 库存流水
            before = float(p.stock_quantity) - float(item.quantity)
            log = StockLog(
                product_id=p.id, warehouse_id=po.warehouse_id,
                change_type='in', quantity=item.quantity,
                before_quantity=before, after_quantity=float(p.stock_quantity),
                reference_id=si.id, reference_type='stock_in',
                notes=f'入库: {si_num}', created_by=admin.id
            )
            db.session.add(log)
        # 更新订单状态
        po.status = 'completed'

    db.session.commit()
    print("入库单完成")

    # 出库：为前50%的销售订单生成出库单
    so_out_map = {}
    for so in all_sos[:int(len(all_sos) * 0.5)]:
        date_str = so.order_date.strftime('%Y%m%d')
        out_counter += 1
        out_num = f"OUT{date_str}{out_counter:03d}"
        sout = StockOut(
            delivery_number=out_num, sales_order_id=so.id,
            warehouse_id=so.warehouse_id,
            delivery_date=so.order_date + timedelta(days=random.randint(0, 2)),
            handler='admin', status='completed',
            total_amount=so.total_amount, created_by=admin.id
        )
        db.session.add(sout)
        db.session.flush()

        if so.id not in so_out_map:
            so_out_map[so.id] = []
        so_out_map[so.id].append(sout.id)

        for item in so.items:
            out_item = StockOutItem(
                stock_out_id=sout.id, product_id=item.product_id,
                quantity=item.quantity, unit_price=float(item.unit_price),
                amount=item.amount
            )
            db.session.add(out_item)
            p = item.product
            p.stock_quantity = float(p.stock_quantity) - float(item.quantity)
            before = float(p.stock_quantity) + float(item.quantity)
            log = StockLog(
                product_id=p.id, warehouse_id=so.warehouse_id,
                change_type='out', quantity=item.quantity,
                before_quantity=before, after_quantity=float(p.stock_quantity),
                reference_id=sout.id, reference_type='stock_out',
                notes=f'出库: {out_num}', created_by=admin.id
            )
            db.session.add(log)
        so.status = 'completed'

    db.session.commit()
    print("出库单完成")

    # 收款：随机给30%的销售订单收款
    all_so_with_amount = [(so, so.total_amount) for so in all_sos if so.total_amount > 0]
    sampled_sos = random.sample(all_so_with_amount, int(len(all_so_with_amount) * 0.3))
    for so, total in sampled_sos:
        # 部分收款（50-90%）
        receipt_amount = Decimal(str(float(total) * random.uniform(0.5, 0.95)))
        date_str = so.delivery_date.strftime('%Y%m%d') if so.delivery_date else so.order_date.strftime('%Y%m%d')
        rc_counter += 1
        rc_num = f"RC{date_str}{rc_counter:03d}"
        rc = Receipt(
            receipt_number=rc_num, customer_id=so.customer_id,
            amount=receipt_amount,
            receipt_date=so.delivery_date or so.order_date,
            payment_method=random.choice(['cash', 'bank_transfer', 'wechat', 'alipay']),
            reference_type='sales_order',
            reference_id=str(so.id),
            created_by=admin.id
        )
        db.session.add(rc)
        so.customer.receivable_balance = Decimal(str(so.customer.receivable_balance)) - receipt_amount

    db.session.commit()
    print("收款记录完成")

    # 付款：随机给30%的采购订单付款
    all_po_with_amount = [(po, po.total_amount) for po in all_pos if po.total_amount > 0]
    sampled_pos = random.sample(all_po_with_amount, int(len(all_po_with_amount) * 0.3))
    for po, total in sampled_pos:
        payment_amount = Decimal(str(float(total) * random.uniform(0.5, 0.95)))
        date_str = po.expected_date.strftime('%Y%m%d') if po.expected_date else po.order_date.strftime('%Y%m%d')
        py_counter += 1
        py_num = f"PY{date_str}{py_counter:03d}"
        py = Payment(
            payment_number=py_num, supplier_id=po.supplier_id,
            amount=payment_amount,
            payment_date=po.expected_date or po.order_date,
            payment_method=random.choice(['cash', 'bank_transfer', 'wechat', 'alipay']),
            reference_type='purchase_order',
            reference_id=str(po.id),
            created_by=admin.id
        )
        db.session.add(py)
        po.supplier.payable_balance = Decimal(str(po.supplier.payable_balance)) - payment_amount

    db.session.commit()
    print("付款记录完成")

    # 最终数据验证
    print("\n=== 最终数据统计 ===")
    print(f"用户: {User.query.count()}")
    print(f"商品: {Product.query.count()}")
    print(f"仓库: {Warehouse.query.count()}")
    print(f"供应商: {Supplier.query.count()} (应付余额: {sum(float(s.payable_balance) for s in Supplier.query.all()):.2f})")
    print(f"客户: {Customer.query.count()} (应收余额: {sum(float(c.receivable_balance) for c in Customer.query.all()):.2f})")
    print(f"采购订单: {PurchaseOrder.query.count()}")
    print(f"销售订单: {SalesOrder.query.count()}")
    print(f"入库单: {StockIn.query.count()}")
    print(f"出库单: {StockOut.query.count()}")
    print(f"收款单: {Receipt.query.count()}")
    print(f"付款单: {Payment.query.count()}")
    print(f"库存流水: {StockLog.query.count()}")

    # 库存和流水一致性验证
    print("\n=== 库存一致性验证 ===")
    all_ok = True
    for p in Product.query.all():
        last = StockLog.query.filter_by(product_id=p.id).order_by(StockLog.id.desc()).first()
        if last and abs(float(p.stock_quantity) - float(last.after_quantity)) > 0.01:
            print(f"库存不一致: {p.name} 库存={p.stock_quantity} 流水末条={last.after_quantity}")
            all_ok = False
    if all_ok:
        print("✓ 库存与流水一致")

    print("\n重置完成！")
