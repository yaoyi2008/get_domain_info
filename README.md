# get_domain_info
用于批量获取域名相关信息，IP地址、网站标题、连接状态、http状态码、http跳转历史、最终着陆页

# 参数解释
```
usage: client.py [-h] [-v] [-p {http,https}] [-f DOMAIN_FILE] [-o OUTPUT_FILE] 
                 [--timeout TIMEOUT] [--threads THREADS]
```
```
optional arguments:
  -h, --help         show this help message and exit  
  -v, --version      show program's version number and exit  
  -p {http,https}    http/https，默认http  
  -f DOMAIN_FILE     存放域名的文件  
  -o OUTPUT_FILE     保存结果到excel中,推荐xlsx保存  
  --timeout TIMEOUT  超时时间，默认5秒  
  --threads THREADS  线程数，默认10线程  `
```

# 功能说明
* 当前支持将域名存放在文本中，每行一个
* 支持结果方式：`命令提示符窗口中实时显示（默认输出方式）`、`excel（需带-o参数及值）`、`MongoDB（需取消代码中的相关注释）`
* 支持自定义`dnsserver`、`headers`、`proxy（需要手工添加到请求中）`

# 已知问题
* 还不能中途使用Ctrl+C结束多线程
