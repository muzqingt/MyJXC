from datetime import datetime
from app import db


class SystemSetting(db.Model):
    """系统配置项"""
    __tablename__ = 'system_settings'
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column('key', db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)
    description = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    @classmethod
    def get_value(cls, key, default=None):
        """获取设置值"""
        setting = cls.query.filter_by(setting_key=key).first()
        return setting.value if setting else default

    @classmethod
    def set_value(cls, key, value):
        """设置值"""
        setting = cls.query.filter_by(setting_key=key).first()
        if setting:
            setting.value = value if value else ''
        else:
            setting = cls(setting_key=key, value=value if value else '')
            db.session.add(setting)
        db.session.commit()

    def __repr__(self):
        return f'<SystemSetting {self.setting_key}>'
