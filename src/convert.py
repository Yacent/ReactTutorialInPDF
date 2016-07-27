# coding=utf-8

# 实现主要思路
# 1. 获取网页教程的内容
# 2. 获取主页当中的ul-list
# 3. 根据获取的ul-list 当中的a 不断发送请求，获取数据，并写入

import os
import logging
import requests
import pickle
from weasyprint import HTML
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

# global variable
INDEX_URL = 'https://facebook.github.io/react/docs/getting-started.html'
BASE_URL = 'https://facebook.github.io'
TRY_LIMITED = 5

# 配置日志模块，并且输出到屏幕和文件
logger = logging.getLogger('pdf_logger')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %('
                              'message)s')
fh = logging.FileHandler('../log/pdf.log')
sh = logging.StreamHandler()
fh.setFormatter(formatter)
sh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(sh)

# 配置浏览器选项，提高抓取速度
cap = dict(DesiredCapabilities.PHANTOMJS)
cap['phantomjs.page.settings.loadImages'] = False  # 禁止加载图片
cap['phantomjs.page.settings.userAgent'] = ('Mozilla/5.0 (Windows NT 10.0; '
                                            'WOW64) AppleWebKit/537.36 ('
                                            'KHTML, like Gecko) '
                                            'Chrome/45.0.2454.101 '
                                            'Safari/537.36')  # 设置useragent
cap['phantomjs.page.settings.diskCache'] = True  # 设置浏览器开启缓存
# service_args = [
#     '--proxy=127.0.0.1:1080',
#     '--proxy-type=socks5',
#     ]
#  设置忽略https
service_args=['--ignore-ssl-errors=true',
              '--ssl-protocol=any',
              '--proxy=127.0.0.1:1080',
              '--proxy-type=socks5']
browser = webdriver.PhantomJS(desired_capabilities=cap, service_args=service_args)
browser.set_page_load_timeout(180)  # 超时时间


def fetch_url_list():
    """
    从react官网教程主页当中抓取页面的URL 列表
    :return: 获取到的ul-list当中的所有li
    """
    try:
        page = requests.get(INDEX_URL, verify=True)
        content = page.text
        soup = BeautifulSoup(content, 'lxml')
        url_list = [item['href'] for item in soup.select('.nav-docs-section ul li a')
                    if item['href'].find('https') == -1]
        return url_list
    except Exception as e:
        logger.error('fetch url list failed')
        logger.error(e)

def fetch_page(url, index):
    """
    根据给定的URL抓取页面 即url_list当中的
    :param url:要抓取页面的地址
    :param index:页面地址在url_list当中的位置，调式时使用，方便查看哪个出错
    :return:返回抓到页面的源代码，失败则返回none
    """
    try:
        browser.get(url)
        return browser.page_source
    except Exception as e:
        logger.warning('get page %d %s failed' % (index, url))
        logger.warning(e)
        return None

def build_content():
    """
    处理每一个url当中爬到页面，按顺序写入到文件当中
    :return: None
    """
    url_list = fetch_url_list()
    print(url_list)
    output = []
    logger.info('there are %s pages' % len(url_list))

    for url_index in range(len(url_list)):
        # 爬页面时可能会因为网络等原因而失败，失败后可以尝试重新抓取，最多五次
        try_count = 0
        temp = BASE_URL + url_list[url_index]
        html = fetch_page(temp, url_index)
        while try_count < TRY_LIMITED and html is None:
            html = fetch_page(BASE_URL + url_list[url_index], url_index)
            try_count += 1
        try:
            if html is not None:
                soup = BeautifulSoup(html, 'lxml')
                title = soup.select(".inner-content")[0]
                output.append(str(title))
                logger.info('get page %s success' % url_index)
            # 页面抓取比较耗时，且中途失败的几率较大，每抓取到页面可以把迄今为止的结果
            # 序列化存储，程序异常退出后前面的结果不会丢失，可以反序列化后接着使用
            # with open('output.dump', 'wb') as f:
            #     pickle.dump(output, f)
        except Exception as e:
            logger.warning('deal page %s %s failed' % (url_index,
                                                       url_list[url_index]))
            logger.warning(e)

    with open('../html/pages.html', 'w') as f:
        f.write('<head><meta charset="utf-8"/></head><body>' + ''.join(
            output) + '</body>')

if not os.path.exists('../html/pages.html'):
    build_content()

if browser:
    browser.quit()

css = [
    '../css/codemirror.css',
    '../css/react.css',
    '../css/syntax.css'
]


HTML('../html/pages.html').write_pdf('../React教程.pdf', stylesheets=css)

