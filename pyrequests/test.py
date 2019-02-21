# coding: utf8 
import asyncio
from pyrequests import PyRequests

pr = PyRequests(workers_num=5)
url = 'http://www.baidu.com'

# 单个请求
r = pr.get(url, timeout=3)
print(r)

# 并发请求
r = pr.mget([url+'#%d'%i for i in range(5)], timeout=3)
print(r)

# 协程请求
r = asyncio.run(pr.aget(url, timeout=3))
print(r)


