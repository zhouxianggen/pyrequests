pyrequests
![](https://img.shields.io/badge/python%20-%203.7-brightgreen.svg)
========
> 对requests的封装，提供绝对超时、线程池访问、协程访问功能 

## `Install`
` pip install git+https://github.com/zhouxianggen/pyrequests.git`

## `Upgrade`
` pip install --upgrade git+https://github.com/zhouxianggen/pyrequests.git`

## `Uninstall`
` pip uninstall pyrequests`

## `Basic Usage`
```python
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

```
