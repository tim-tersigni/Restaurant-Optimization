import threading
import sys
import time
import random


queue = []
orders = []
condition = threading.Condition()

table_a = {'string': 'A',
           'semaphore': threading.Semaphore(4),
           's_customer': threading.Semaphore(0),
           's_waiter': threading.Semaphore(0),
           'seated': 0,
           'line': 0,
           'food': 'seafood',
           'waiter': None}


def t_customer_pre(id):
    global queue
    condition.acquire()
    queue.append(id)
    print('set ' + str(id))
    condition.notify()
    condition.release()
    print('customer ' + str(id) + ' waiting on order')


def t_customer_post(id):
    global queue
    print(str(id) + ' got food yay')
    time.sleep(random.random())
    print(str(id) + ' left')


def t_waiter(id):
    global queue
    while True:
        condition.acquire()
        if not queue:
            print('nothing in queue, waiter is waiting')
            condition.wait()
            print('consumer set to queue and called waiter')
        order = queue.pop()
        print('get ' + str(order))
        condition.release()
        c = threading.Thread(target=t_customer_post(order,))
        c.start


for i in range(0, 2):
    t = threading.Thread(target=t_customer_pre(i,))
    t.start()

for i in range(0, 1):
    t = threading.Thread(target=t_waiter(i,))
    t.start()
