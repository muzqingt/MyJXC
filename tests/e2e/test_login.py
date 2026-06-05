"""
登录流程 E2E 测试
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_login_page_loads(driver, app_server):
    """登录页面加载"""
    driver.get(f'{app_server}/auth/login')
    assert '登录' in driver.title
    assert driver.find_element(By.NAME, 'username').is_displayed()
    assert driver.find_element(By.NAME, 'password').is_displayed()


def test_login_success(driver, app_server):
    """登录成功"""
    driver.get(f'{app_server}/auth/login')
    driver.find_element(By.NAME, 'username').send_keys('admin')
    driver.find_element(By.NAME, 'password').send_keys('admin123')
    driver.find_element(By.ID, 'submit').click()
    WebDriverWait(driver, 10).until(EC.url_changes(f'{app_server}/auth/login'))


def test_login_wrong_password(driver, app_server):
    """登录失败 - 错误密码"""
    driver.get(f'{app_server}/auth/login')
    driver.find_element(By.NAME, 'username').send_keys('admin')
    driver.find_element(By.NAME, 'password').send_keys('wrongpass')
    driver.find_element(By.ID, 'submit').click()
    alert = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'alert-danger'))
    )
    assert alert.is_displayed()


def test_login_nonexistent_user(driver, app_server):
    """登录失败 - 不存在的用户"""
    driver.get(f'{app_server}/auth/login')
    driver.find_element(By.NAME, 'username').send_keys('nonexistent')
    driver.find_element(By.NAME, 'password').send_keys('pass123')
    driver.find_element(By.ID, 'submit').click()
    alert = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'alert-danger'))
    )
    assert alert.is_displayed()


def test_unauthenticated_redirect(driver, app_server):
    """未登录访问受保护页面 -> 重定向到登录"""
    driver.get(f'{app_server}/product/')
    WebDriverWait(driver, 10).until(EC.url_contains('/auth/login'))


def test_logout(driver, app_server):
    """登出"""
    # 先登录
    driver.get(f'{app_server}/auth/login')
    driver.find_element(By.NAME, 'username').send_keys('admin')
    driver.find_element(By.NAME, 'password').send_keys('admin123')
    driver.find_element(By.ID, 'submit').click()
    WebDriverWait(driver, 10).until(EC.url_changes(f'{app_server}/auth/login'))

    # 使用 JavaScript 直接提交登出表单
    driver.execute_script("""
        var forms = document.querySelectorAll('form');
        for (var i = 0; i < forms.length; i++) {
            if (forms[i].action && forms[i].action.includes('logout')) {
                forms[i].submit();
                break;
            }
        }
    """)
    WebDriverWait(driver, 10).until(EC.url_contains('/auth/login'))
