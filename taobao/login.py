import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from getpass import getpass

LOGIN_URL = "https://login.taobao.com/member/login.jhtml"

"""
chrome版本号 107.0.5304.62
chrome 其他版本下载地址
http://chromedriver.storage.googleapis.com/index.html 
"""


def get_path(n):
    base_path = os.path.dirname(os.path.abspath(__file__))
    for i in range(n):
        base_path = os.path.dirname(base_path)
    return base_path


BASE_PATH = get_path(0)

sys.path.append(BASE_PATH)


class TaobaoSpider():
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.inint_browser()

    def inint_browser(self):
        options = webdriver.ChromeOptions()
        # 不加载图片，加快访问速度
        # options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
        # 设置为开发者模式，避免被识别
        # options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # options.add_experimental_option("debuggerAddress", "127.0.0.1:8888")
        browser = webdriver.Chrome(executable_path="./chromedriver", options=options)
        # 读取文件
        file_path = os.path.join(BASE_PATH, 'stealth.min.js')
        with open(file_path, 'r', encoding='utf-8') as f:
            js = f.read()
        # 调用函数在页面加载前执行脚本
        browser.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': js})
        self.browser = browser
        self.browser_wait = WebDriverWait(self.browser, 10)

    def _login(self):
        self.browser.get(LOGIN_URL)
        # 切换为帐号密码登录
        login_method_switch = self.browser_wait.until(
            expected_conditions.presence_of_element_located((By.CLASS_NAME, 'password-login-tab-item')))
        login_method_switch.click()

        # 找到用户名输入框并输入
        username_input = self.browser_wait.until(
            expected_conditions.presence_of_element_located((By.ID, 'fm-login-id')))
        username_input.send_keys(self.username)

        # 找到密码输入框并输入
        password_input = self.browser_wait.until(
            expected_conditions.presence_of_element_located((By.ID, 'fm-login-password')))
        password_input.send_keys(self.password)

        # 找到登录按钮并点击
        login_button = self.browser_wait.until(
            expected_conditions.presence_of_element_located((By.CLASS_NAME, 'password-login')))
        login_button.click()

        # 找到名字标签并打印内容
        taobao_name_tag = self.browser_wait.until(expected_conditions.presence_of_element_located(
            (By.CLASS_NAME, 'site-nav-user')))
        account_name = taobao_name_tag.find_element(By.TAG_NAME, "a").text
        print(f"登陆成功：{account_name}")

    def login(self):
        try:
            self._login()
        except Exception as e:
            print("登陆失败")
            print(e)


if __name__ == '__main__':
    username = input("请输入用户名：")
    password = getpass("请输入密码：")
    spider = TaobaoSpider(username, password)
    spider.login()
