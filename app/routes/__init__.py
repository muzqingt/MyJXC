# 导入所有蓝图
from .auth import bp as auth_bp
from .main import bp as main_bp
from .product import bp as product_bp
from .partner import bp as partner_bp
from .purchase import bp as purchase_bp
from .sales import bp as sales_bp
from .inventory import bp as inventory_bp
from .finance import bp as finance_bp
from .report import bp as report_bp
from .system import bp as system_bp

__all__ = ['auth_bp', 'main_bp', 'product_bp', 'partner_bp', 'purchase_bp', 'sales_bp', 'inventory_bp', 'finance_bp', 'report_bp', 'system_bp']