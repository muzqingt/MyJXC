from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, DateField, DecimalField, IntegerField, FileField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional, NumberRange
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('邮箱', validators=[Optional(), Email()])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('注册')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('用户名已存在，请使用其他用户名。')
    
    def validate_email(self, email):
        if email.data:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('邮箱已存在，请使用其他邮箱。')

class CategoryForm(FlaskForm):
    name = StringField('分类名称', validators=[DataRequired(), Length(max=100)])
    parent_id = SelectField('父级分类', coerce=int, validators=[Optional()])
    description = TextAreaField('描述')
    submit = SubmitField('保存')

class ProductForm(FlaskForm):
    code = StringField('商品编码', validators=[DataRequired(), Length(max=50)])
    name = StringField('商品名称', validators=[DataRequired(), Length(max=200)])
    category_id = SelectField('商品分类', coerce=int, validators=[Optional()])
    specification = StringField('规格', validators=[Length(max=200)])
    unit = StringField('计量单位', validators=[DataRequired(), Length(max=20)], default='个')
    purchase_price = DecimalField('采购价', validators=[Optional(), NumberRange(min=0)], places=2)
    sale_price = DecimalField('销售价', validators=[Optional(), NumberRange(min=0)], places=2)
    safety_stock = DecimalField('安全库存', validators=[Optional(), NumberRange(min=0)], places=2)
    image = FileField('商品图片')
    description = TextAreaField('描述')
    submit = SubmitField('保存')

class SupplierForm(FlaskForm):
    code = StringField('供应商编码', validators=[DataRequired(), Length(max=50)])
    name = StringField('供应商名称', validators=[DataRequired(), Length(max=200)])
    contact_person = StringField('联系人', validators=[Length(max=100)])
    phone = StringField('电话', validators=[Length(max=50)])
    address = TextAreaField('地址')
    email = StringField('邮箱', validators=[Optional(), Email(), Length(max=120)])
    submit = SubmitField('保存')

class CustomerForm(FlaskForm):
    code = StringField('客户编码', validators=[DataRequired(), Length(max=50)])
    name = StringField('客户名称', validators=[DataRequired(), Length(max=200)])
    contact_person = StringField('联系人', validators=[Length(max=100)])
    phone = StringField('电话', validators=[Length(max=50)])
    address = TextAreaField('地址')
    email = StringField('邮箱', validators=[Optional(), Email(), Length(max=120)])
    submit = SubmitField('保存')

class WarehouseForm(FlaskForm):
    code = StringField('仓库编码', validators=[DataRequired(), Length(max=50)])
    name = StringField('仓库名称', validators=[DataRequired(), Length(max=200)])
    address = TextAreaField('地址')
    manager = StringField('负责人', validators=[Length(max=100)])
    phone = StringField('电话', validators=[Length(max=50)])
    submit = SubmitField('保存')

class PurchaseOrderForm(FlaskForm):
    supplier_id = SelectField('供应商', coerce=int, validators=[DataRequired()])
    warehouse_id = SelectField('仓库', coerce=int, validators=[DataRequired()])
    order_date = DateField('订单日期', validators=[DataRequired()])
    expected_date = DateField('预计到货日期', validators=[Optional()])
    notes = TextAreaField('备注')
    submit = SubmitField('保存订单')

class PurchaseOrderItemForm(FlaskForm):
    product_id = SelectField('商品', coerce=int, validators=[DataRequired()])
    quantity = DecimalField('数量', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    unit_price = DecimalField('单价', validators=[DataRequired(), NumberRange(min=0)], places=2)

class StockInForm(FlaskForm):
    purchase_order_id = SelectField('采购订单', coerce=int, validators=[Optional()])
    warehouse_id = SelectField('仓库', coerce=int, validators=[DataRequired()])
    receipt_date = DateField('入库日期', validators=[DataRequired()])
    handler = StringField('经办人', validators=[Length(max=100)])
    notes = TextAreaField('备注')
    submit = SubmitField('保存入库单')

class SalesOrderForm(FlaskForm):
    customer_id = SelectField('客户', coerce=int, validators=[DataRequired()])
    warehouse_id = SelectField('仓库', coerce=int, validators=[DataRequired()])
    order_date = DateField('订单日期', validators=[DataRequired()])
    delivery_date = DateField('预计发货日期', validators=[Optional()])
    notes = TextAreaField('备注')
    submit = SubmitField('保存订单')

class SalesOrderItemForm(FlaskForm):
    product_id = SelectField('商品', coerce=int, validators=[DataRequired()])
    quantity = DecimalField('数量', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    unit_price = DecimalField('单价', validators=[DataRequired(), NumberRange(min=0)], places=2)

class StockOutForm(FlaskForm):
    sales_order_id = SelectField('销售订单', coerce=int, validators=[Optional()])
    warehouse_id = SelectField('仓库', coerce=int, validators=[DataRequired()])
    delivery_date = DateField('出库日期', validators=[DataRequired()])
    handler = StringField('经办人', validators=[Length(max=100)])
    notes = TextAreaField('备注')
    submit = SubmitField('保存出库单')

class ReceiptForm(FlaskForm):
    customer_id = SelectField('客户', coerce=int, validators=[DataRequired()])
    amount = DecimalField('收款金额', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    receipt_date = DateField('收款日期', validators=[DataRequired()])
    payment_method = SelectField('支付方式', choices=[
        ('cash', '现金'),
        ('bank_transfer', '银行转账'),
        ('wechat', '微信支付'),
        ('alipay', '支付宝')
    ], validators=[DataRequired()])
    reference_type = SelectField('关联类型', choices=[
        ('sales_order', '销售订单'),
        ('other', '其他')
    ], validators=[Optional()])
    reference_id = IntegerField('关联ID', validators=[Optional()])
    notes = TextAreaField('备注')
    submit = SubmitField('保存收款单')

class PaymentForm(FlaskForm):
    supplier_id = SelectField('供应商', coerce=int, validators=[DataRequired()])
    amount = DecimalField('付款金额', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    payment_date = DateField('付款日期', validators=[DataRequired()])
    payment_method = SelectField('支付方式', choices=[
        ('cash', '现金'),
        ('bank_transfer', '银行转账'),
        ('wechat', '微信支付'),
        ('alipay', '支付宝')
    ], validators=[DataRequired()])
    reference_type = SelectField('关联类型', choices=[
        ('purchase_order', '采购订单'),
        ('other', '其他')
    ], validators=[Optional()])
    reference_id = IntegerField('关联ID', validators=[Optional()])
    notes = TextAreaField('备注')
    submit = SubmitField('保存付款单')

class ExpenseForm(FlaskForm):
    category = StringField('费用类别', validators=[DataRequired(), Length(max=100)])
    amount = DecimalField('金额', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    expense_date = DateField('费用日期', validators=[DataRequired()])
    payee = StringField('收款方', validators=[Length(max=200)])
    payment_method = SelectField('支付方式', choices=[
        ('cash', '现金'),
        ('bank_transfer', '银行转账'),
        ('wechat', '微信支付'),
        ('alipay', '支付宝')
    ], validators=[DataRequired()])
    notes = TextAreaField('备注')
    submit = SubmitField('保存费用')

class StockAdjustForm(FlaskForm):
    product_id = SelectField('商品', coerce=int, validators=[DataRequired()])
    warehouse_id = SelectField('仓库', coerce=int, validators=[DataRequired()])
    adjust_type = SelectField('调整类型', choices=[
        ('adjust_in', '盘盈入库'),
        ('adjust_out', '盘亏出库')
    ], validators=[DataRequired()])
    quantity = DecimalField('数量', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    notes = TextAreaField('备注')
    submit = SubmitField('保存调整')

class SearchForm(FlaskForm):
    keyword = StringField('关键词', validators=[Optional()])
    start_date = DateField('开始日期', validators=[Optional()])
    end_date = DateField('结束日期', validators=[Optional()])
