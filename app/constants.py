"""
业务常量定义 - 消除魔法字符串
"""


class OrderStatus:
    """订单状态"""
    DRAFT = 'draft'
    CONFIRMED = 'confirmed'
    PARTIAL = 'partial'      # 部分入库/出库
    COMPLETED = 'completed'

    ALL = (DRAFT, CONFIRMED, PARTIAL, COMPLETED)

    @classmethod
    def label(cls, status):
        """返回状态的中文标签"""
        return {
            cls.DRAFT: '草稿',
            cls.CONFIRMED: '已确认',
            cls.PARTIAL: '部分完成',
            cls.COMPLETED: '已完成',
        }.get(status, status)


class ChangeType:
    """库存变动类型"""
    IN = 'in'                   # 入库
    OUT = 'out'                 # 出库
    ADJUST_IN = 'adjust_in'     # 盘点盈余
    ADJUST_OUT = 'adjust_out'   # 盘点亏损
    CHECK_IN = 'check_in'       # 盘点入库
    CHECK_OUT = 'check_out'     # 盘点出库
    RETURN_IN = 'return_in'     # 退货入库
    RETURN_OUT = 'return_out'   # 退货出库
    TRANSFER = 'stock_transfer' # 调拨

    # 入库类变动（增加库存）
    IN_TYPES = (IN, ADJUST_IN, CHECK_IN, RETURN_IN)
    # 出库类变动（减少库存）
    OUT_TYPES = (OUT, ADJUST_OUT, CHECK_OUT, RETURN_OUT, TRANSFER)


class PaymentMethod:
    """支付方式"""
    CASH = 'cash'
    BANK_TRANSFER = 'bank_transfer'
    CHECK = 'check'
    WECHAT = 'wechat'
    ALIPAY = 'alipay'
    OTHER = 'other'

    LABELS = {
        CASH: '现金',
        BANK_TRANSFER: '银行转账',
        CHECK: '支票',
        WECHAT: '微信',
        ALIPAY: '支付宝',
        OTHER: '其他',
    }

    @classmethod
    def label(cls, method):
        return cls.LABELS.get(method, method)


VALID_CHANGE_TYPES = (
    ChangeType.IN, ChangeType.OUT,
    ChangeType.ADJUST_IN, ChangeType.ADJUST_OUT,
    ChangeType.CHECK_IN, ChangeType.CHECK_OUT,
    ChangeType.RETURN_IN, ChangeType.RETURN_OUT,
    ChangeType.TRANSFER,
)


class UserRole:
    """用户角色"""
    ADMIN = 'admin'
    USER = 'user'
