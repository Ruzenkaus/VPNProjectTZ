import threading
import queue
import requests

q = queue.Queue()
v_proxies = []

with open('all_proxies', 'r') as f:
    proxies = f.read().split("\n")
    for p in proxies:
        q.put(p)


def check_proxies():
    global q
    while not q.empty():
        proxy = q.get()
        try:
            resp = requests.get("http://ipinfo.io//json", proxies= {
                "http": proxy,
                "https": proxy
            })
        except:
            continue
        if resp.status_code == 200:
            print(proxy)


check_proxies()