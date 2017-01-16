#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import dns.resolver
import requests
import pymongo
import threading
import time
import argparse
from bs4 import BeautifulSoup


reload(sys)
sys.setdefaultencoding("utf-8")

# 关闭https证书警告
from openpyxl import Workbook

# 关闭requests警告
requests.packages.urllib3.disable_warnings()


def get_web_info(domain, protocol, timeout):
    max_threads.acquire()  # 线程数控制，加锁

    # 定义参数的默认值
    title = None
    con_status = 'Connect Success'
    http_status = None
    http_history_status = None
    url = protocol + '://' + domain
    final_url = url
    ip_group = None

    # 定义http headers
    headers = {
        'user-agent': 'googlebot/2.1'
    }

    # 定义http代理
    '''
    proxies = {
        "http": "http://10.10.1.10:3128",
        "https": "http://10.10.1.10:1080",
    }
    '''

    # 获取域名ip地址
    try:
        req = dns.resolver.Resolver()
        req.nameservers = ['192.168.45.10', '223.5.5.5']  # 配置DNS解析服务器列表
        anwser = req.query(domain, 'A')
        # print anwser
        ip_group = [i.address.encode('utf-8') for i in anwser]
        # 获取网页信息
        try:
            web_data = requests.get(url, verify=False, timeout=timeout, headers=headers)
            web_data.encoding = 'utf-8'
            soup = BeautifulSoup(web_data.text, 'lxml')
            title = soup.title.string if soup.title else None
            http_status = web_data.status_code
            http_history_status = [str(i)[11:14] for i in web_data.history]
            final_url = web_data.url
        except requests.exceptions.ConnectTimeout as e:
            con_status = 'Connect Timeout'  # 连接超时
        except requests.exceptions.ReadTimeout as e:
            con_status = 'Read Timeout'  # 读取超时
        except requests.exceptions.ConnectionError as e:
            con_status = 'Connect Error'  # 连接错误
        except:
            con_status = 'Other Error'  # 其他错误

    except dns.resolver.NoAnswer as e:
        ip_group = 'No A record'
        con_status = 'Connect Fail'  # 没有A记录时，返回连接失败状态
    except dns.resolver.NXDOMAIN as e:
        ip_group = 'Non-existent domain'
        con_status = 'Connect Fail'  # 域名不存在时，返回连接失败状态
    except dns.resolver.Timeout as e:
        ip_group = 'Time out'
        con_status = 'Connect Fail'  # 查询超时时，返回连接失败状态
    except:
        ip_group = 'Other error'
        con_status = 'Connect Fail'  # 其他错误，返回连接失败状态
    finally:
        # 创建网站访问信息字典
        web_info = {
            'domain': domain,
            'ip': ip_group,
            'title': title,
            'con_status': con_status,
            'http_status': http_status,
            'http_history_status': http_history_status if http_history_status else None,
            'final_url': final_url
        }

        # 增量保存字段内容，便于保存到excel
        ws.append([domain, str(ip_group) if ip_group else '', title, con_status, http_status,
                   str(http_history_status) if http_history_status else '', final_url])

        lock.acquire()  # 对输出的动作，加锁，防止输出信息错乱
        print(u'domain:{},\tip:{},\ttitle:{},\tcon_status:{},\thttp_status:{},\thttp_history_status:{},\tfinal_url:{}'
            .format(
            web_info['domain'],
            web_info['ip'],
            web_info['title'],
            web_info['con_status'],
            web_info['http_status'],
            web_info['http_history_status'],
            web_info['final_url']
        )
        )
        lock.release()  # 对输出的动作，释放锁

        # 向MongoDB插入数据
        test_info_tab.insert_one(web_info)

    max_threads.release()  # 线程数控制，释放锁


# 获取域名列表
def get_domain(domain_list=[]):
    with open(domain_file, 'r') as f:
        for i in f:
            domain_list.append(i.strip())
        return domain_list


if __name__ == '__main__':
    # 命令行选项
    parser = argparse.ArgumentParser(description=u'【该工具用于获取域名及对应网站的相关信息】', version='1.0')
    parser.add_argument('-p', dest='protocol', help='http/https，默认http', default='http', choices=('http', 'https'))
    parser.add_argument('-f', dest='domain_file', help='存放域名的文件')
    parser.add_argument('-o', dest='output_file', help='保存结果到excel中,推荐xlsx保存')
    parser.add_argument('--timeout', dest='timeout', help='超时时间，默认5秒', default=5, type=int)
    parser.add_argument('--threads', dest='threads', help='线程数，默认10线程', default=10, type=int)
    parsers = parser.parse_args()

    protocol = parsers.protocol
    domain_file = parsers.domain_file
    output_file = parsers.output_file
    timeout = parsers.timeout
    threads = parsers.threads

    if domain_file == None:
        print parser.parse_args(['-h'])
    elif os.path.exists(domain_file) == False:
        print('Please enter the correct file path')
        exit()
    else:
        # 开始时间
        start_time = time.time()
        print('>>>>> Start time: {} <<<<<'.format(time.strftime('%Y-%m-%d %X', time.localtime())))

        # 打开数据库
        client = pymongo.MongoClient('localhost', 27017)
        testdb = client['testdb']
        test_info_tab = testdb['test_info_tab']

        # 创建excel表格
        wb = Workbook()
        ws = wb.active
        ws.title = u'域名及网站信息'
        ws.append(['域名', 'ip', '网站名', '网络连接状态', 'http状态码', '网页跳转历史', '最终着陆页'])

        # 线程锁
        lock = threading.Lock()

        # 最大线程数
        max_threads = threading.BoundedSemaphore(threads)

        # 线程任务
        threads = []
        for i in get_domain():
            t = threading.Thread(target=get_web_info, args=(i, protocol, timeout), name=i)
            t.start()
            threads.append(t)

        for i in threads:
            i.join()

        # 保存excel结果
        if output_file != None:
            wb.save(output_file)

        # 结束时间
        finish_time = time.time()
        print(
            '>>>>> Finish time: {}, total time: {:,.2f} seconds <<<<<'.format(
                time.strftime('%Y-%m-%d %X', time.localtime()),
                finish_time - start_time))

        # # 查看数据库数据
        # for i in test_info_tab.find():
        #     print i
