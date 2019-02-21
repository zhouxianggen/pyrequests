#!/usr/bin/env python
#coding=utf8

try:
    from  setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

setup(
        name = 'pyrequests',
        version = '1.0',
        install_requires = ['requests'], 
        description = '对requests的封装，提供绝对超时、线程池访问、协程访问功能',
        url = 'https://github.com/zhouxianggen/pyrequests', 
        author = 'zhouxianggen',
        author_email = 'zhouxianggen@gmail.com',
        classifiers = [ 'Programming Language :: Python :: 3.7',],
        packages = ['pyrequests'],
        data_files = [ ],  
        entry_points = { }   
        )
