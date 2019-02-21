# coding: utf8 
import time
import asyncio
from queue import Queue, Empty, Full
from threading import Thread, Lock, Event
import requests
from pyobject import PyObject


class Worker(Thread, PyObject):
    def __init__(self, caller):
        Thread.__init__(self)
        PyObject.__init__(self)
        self.daemon = True
        self.caller = caller
        self._exit = Event()
        self.deadline = 0

    def run(self):
        while not self._exit.is_set():
            try:
                t = self.caller.request_queue.get(block=False)
                fut, wait_time, method, url, kwargs = t
            except Empty as e:
                time.sleep(0.001)
                continue
            
            #self.log.info('start open [{}]'.format(url))
            self.deadline = time.time() + wait_time
            try:
                r = requests.request(method, url, **kwargs)
                self.caller.result_queue.put((url, r, fut), block=False)
            except Exception as e:
                pass
            self.deadline = 0
    
    def exit(self):
        self._exit.set()

class Watcher(Thread, PyObject):
    def __init__(self, caller):
        Thread.__init__(self)
        PyObject.__init__(self)
        self.daemon = True
        self.caller = caller

    def run(self):
        while True:
            try:
                url, resp, fut = self.caller.result_queue.get(block=False)
                #self.log.info('get response of [{}]'.format(url))
                self.caller.put_response(url, resp, fut)
                continue
            except Empty as e:
                time.sleep(0.001)

            now = time.time()
            for idx,w in enumerate(self.caller.workers):
                if w.deadline and now > w.deadline:
                    #self.log.info('restart worker [{}]'.format(w.ident))
                    w.exit()
                    self.caller.workers[idx] = Worker(self.caller) 
                    self.caller.workers[idx].start()

class PyRequests(PyObject):
    def __init__(self, workers_num=4):
        PyObject.__init__(self)
        self.request_queue = Queue(maxsize=1000)
        self.result_queue = Queue()
        self.response_cache = {}
        self.lock = Lock()
        self.response_queue = asyncio.Queue()
        self.workers = [Worker(self) for i in range(workers_num)]
        for w in self.workers:
            w.start()
        self.watcher = Watcher(self)
        self.watcher.start()
        self.none_resp = requests.Response()

    def put_request(self, fut, method, url, **kwargs):
        timeout = kwargs.get('timeout', 2)
        if isinstance(timeout, tuple):
            try:
                connect_timeout, read_timeout = timeout
                wait_time = float(connect_timeout + read_timeout)
            except ValueError as e:
                wait_time = 4
        else:
            wait_time = 2 * float(timeout)
        try:
            self.request_queue.put((fut, wait_time, method, url,  
                    kwargs), block=False)
        except Full as e:
            self.log.warning('request queue is full')
            return -1
        return wait_time

    def request(self, method, url, **kwargs):
        wait_time = self.put_request(None, method, url, **kwargs)
        if wait_time < 0:
            return self.none_resp

        start = time.time()
        while time.time() - start < wait_time:
            time.sleep(0.001)
            resp = self.get_response(url)
            if resp:
                return resp
        return self.none_resp

    def get(self, url, params=None, **kwargs):
        kwargs.setdefault('allow_redirects', True)
        return self.request('get', url, params=params, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        return self.request('post', url, data=data, json=json, **kwargs)

    async def cancel_after(self, fut, wait_time):
        start = time.time()
        while time.time() - start < wait_time:
            await asyncio.sleep(0.001)
            if fut.done():
                return
        fut.cancel()

    async def arequest(self, method, url, **kwargs):
        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        wait_time = self.put_request(fut, method, url, **kwargs)
        loop.create_task(self.cancel_after(fut, wait_time))
        await fut
        return fut.result()
    
    async def aget(self, url, params=None, **kwargs):
        kwargs.setdefault('allow_redirects', True)
        return await self.arequest('get', url, params=params, **kwargs)

    async def apost(self, url, data=None, json=None, **kwargs):
        return await self.arequest('post', url, data=data, json=json, **kwargs)

    def mrequest(self, method, urls, **kwargs):
        wait_time = 0
        result = {}
        for url in urls:
            wait_time = self.put_request(None, method, url, **kwargs)
        if wait_time < 0:
            return result

        unfinished = [x for x in urls]
        start = time.time()
        while time.time() - start < wait_time:
            time.sleep(0.001)
            remain = []
            for url in unfinished:
                resp = self.get_response(url)
                if resp:
                    result[url] = resp
                else:
                    remain.append(url)
            unfinished = remain
            if not unfinished:
                break
        return result

    def mget(self, urls, params=None, **kwargs):
        kwargs.setdefault('allow_redirects', True)
        return self.mrequest('get', urls, params=params, **kwargs)

    def mpost(self, urls, data=None, json=None, **kwargs):
        return self.mrequest('post', urls, data=data, json=json, **kwargs)

    def get_response(self, url):
        if self.lock.acquire(blocking=False):
            resp = self.response_cache.pop(url, None)
            self.lock.release()
            return resp

    def put_response(self, url, resp, fut=None):
        if self.lock.acquire(blocking=True):
            if fut:
                fut.set_result(resp)
            else:
                self.response_cache[url] = resp
            self.lock.release()

