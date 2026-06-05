"""
E2E 测试配置 — Selenium + Chromium
"""
import pytest
import time
import requests
from multiprocessing import Process
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


@pytest.fixture(scope="session")
def app_server():
    """启动 Flask 应用服务器"""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    server = Process(target=app.run, kwargs={
        'port': 5000,
        'use_reloader': False,
        'debug': False
    })
    server.start()

    # 等待服务器启动
    for _ in range(30):
        try:
            requests.get('http://localhost:5000/')
            break
        except:
            time.sleep(0.5)

    yield 'http://localhost:5000'
    server.terminate()
    server.join()


@pytest.fixture(scope="session")
def chrome_options():
    """Chrome 选项"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.binary_location = '/data/data/com.termux/files/usr/bin/chromium-browser'
    return options


@pytest.fixture
def driver(app_server, chrome_options):
    """创建 Selenium WebDriver"""
    service = Service('/data/data/com.termux/files/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()
