from os import path, remove, popen
from sys import argv
from zipfile import ZipFile
from winreg import OpenKey, QueryValueEx, HKEY_CURRENT_USER
from requests import get
from pyperclip import copy
from datetime import datetime
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('log-level=3')

#去除webdriver特征
chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument("--disable-blink-features")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

url='https://registry.npmmirror.com/-/binary/chromedriver/' # chromedriver download link

def exitWait():
    getYourCode = input("请按回车键自动退出。")
    exit(0)

def get_path():
    return path.dirname(path.realpath(argv[0]))
    #return path.dirname(path.realpath(__file__))

def get_Chrome_version():
    key = OpenKey(HKEY_CURRENT_USER, r'Software\Google\Chrome\BLBeacon')
    version, types = QueryValueEx(key, 'version')
    return version

def get_server_chrome_versions():
    '''return all versions list'''
    versionList=[]
    version_url="https://registry.npmmirror.com/-/binary/chromedriver/"
    rep = get(version_url).json()
    for i in rep:                               
        version = i["name"].replace("/","")         # 提取版本号
        versionList.append(version)            # 将所有版本存入列表
    return versionList

def download_driver(download_url):
    '''下载文件'''
    file = get(download_url)
    with open("chromedriver.zip", 'wb') as zip_file:        # 保存文件到脚本所在目录
        zip_file.write(file.content)
        print('下载成功')

def download_lase_driver(download_url, chromeVersion, chrome_main_version):
    '''更新driver'''
    versionList=get_server_chrome_versions()
    if chromeVersion in versionList:
        download_url=f"{url}{chromeVersion}/chromedriver_win32.zip"
    else:
        for version in versionList:
            if version.startswith(str(chrome_main_version)):
                download_url=f"{url}{version}/chromedriver_win32.zip"
                break
        if download_url=="":
            print("暂无法找到与chrome兼容的chromedriver版本，请前往http://npm.taobao.org/mirrors/chromedriver/ 核实。")
    download_driver(download_url=download_url)
    path = get_path()
    print('当前路径为：', path)
    unzip_driver(path)
    remove("chromedriver.zip")
    dri_version = get_version()
    if dri_version == 0:
        return 0
    else:
        print('更新后的Chromedriver版本为：', dri_version)

def get_version():
    '''查询系统内的Chromedriver版本'''
    outstd2 = popen('chromedriver --version').read()
    try:
        out = outstd2.split(' ')[1]
    except:
        return 0
    return out

def unzip_driver(path):
    '''解压Chromedriver压缩包到指定目录'''
    f = ZipFile("chromedriver.zip",'r')
    for file in f.namelist():
        f.extract(file, path)

def check_update_chromedriver():
    try:
        chromeVersion=get_Chrome_version()
    except:
        print('未安装Chrome，请在GooGle Chrome官网：https://www.google.cn/chrome/ 下载。')
        return 0
    
    chrome_main_version=int(chromeVersion.split(".")[0]) # chrome主版本号

    try:
        driverVersion=get_version()
        driver_main_version=int(driverVersion.split(".")[0]) # chromedriver主版本号
    except:
        print(f"未安装Chromedriver，正在为您自动下载({chromeVersion})>>>")
        download_url=""
        if download_lase_driver(download_url, chromeVersion, chrome_main_version) == 0:
            return 0
        driverVersion=get_version()
        driver_main_version=int(driverVersion.split(".")[0]) # chromedriver主版本号
    
    download_url=""
    if driver_main_version!=chrome_main_version:
        print(f"chromedriver版本与chrome浏览器不兼容，更新中({chromeVersion})>>>",)
        if download_lase_driver(download_url, chromeVersion, chrome_main_version) == 0:
            return 0
    else:
       print(f"chromedriver版本已与chrome浏览器相兼容({chromeVersion})，无需更新chromedriver版本！") 

def find_and_paste(cookie):
    # 文件路径
    for item in cookie.split('; '):
        if 'pt_pin' in item:
            pt_pin = item
        if 'pt_key' in item:
            pt_key = item
    jd_cookie = pt_pin+';'+pt_key+';'
    copy(jd_cookie)
    return jd_cookie

def main():
    print('请在弹出的网页中登录账号。推荐使用账户密码形式登录。')

    ua = UserAgent().safari
    print('随机UA为：', ua)

    driver = webdriver.Chrome(executable_path=get_path()+'\chromedriver.exe', options=chrome_options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
            })
        """
    })

    print("当前浏览器内置user-agent为：", driver.execute_script('return navigator.userAgent'))

    driver.execute_cdp_cmd("Emulation.setUserAgentOverride", {
        "userAgent": ua
    })

    print("更改后浏览器user-agent为：", driver.execute_script('return navigator.userAgent'))

    driver.get('https://bean.m.jd.com/bean/signIndex.action')

    try:
        if WebDriverWait(driver, 600, poll_frequency=0.2, ignored_exceptions=None).until(EC.title_is(u"签到日历")):
            '''判断title,返回布尔值'''
            nowtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print('{} : 登录成功'.format(nowtime))

    except:
        print('超时退出')
        exitWait()
        exit(2)

    jd_cookies = driver.get_cookies()

    for cookie in jd_cookies:
        if cookie['name'] == "pt_key":
            pt_key ='{}={};'.format(cookie['name'], cookie['value'])
        elif cookie['name'] == "pt_pin":
            pt_pin = '{}={};'.format(cookie['name'], cookie['value'])

    result = pt_key + pt_pin
    copy(result)
    print('jd_cookie: ', result)
    input('按Enter键退出...')
    driver.close()

if __name__ == '__main__':
    check_update_chromedriver()
    main()
