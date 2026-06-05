"""
E2E 测试数据工厂
"""
import requests


class E2EFactories:
    """通过 HTTP 请求创建测试数据"""

    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()

    def login(self, username='admin', password='admin123'):
        """登录获取 session"""
        self.session.post(f'{self.base_url}/auth/login', data={
            'username': username,
            'password': password
        })

    def create_product(self, code, name, **kwargs):
        """创建商品"""
        data = {
            'code': code,
            'name': name,
            'unit': '个',
            'purchase_price': '50.00',
            'sale_price': '100.00',
            **kwargs
        }
        return self.session.post(f'{self.base_url}/product/products/new', data=data)

    def create_supplier(self, code, name, **kwargs):
        """创建供应商"""
        data = {
            'code': code,
            'name': name,
            'contact_person': '联系人',
            'phone': '13800000000',
            **kwargs
        }
        return self.session.post(f'{self.base_url}/partner/suppliers/new', data=data)

    def create_customer(self, code, name, **kwargs):
        """创建客户"""
        data = {
            'code': code,
            'name': name,
            'contact_person': '联系人',
            'phone': '13900000000',
            **kwargs
        }
        return self.session.post(f'{self.base_url}/partner/customers/new', data=data)

    def create_warehouse(self, code, name, **kwargs):
        """创建仓库"""
        data = {
            'code': code,
            'name': name,
            'address': '测试地址',
            **kwargs
        }
        return self.session.post(f'{self.base_url}/partner/warehouses/new', data=data)
