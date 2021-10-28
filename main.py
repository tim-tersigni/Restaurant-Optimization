import logging
import threading
import queue
from queue import Queue
import time
import concurrent.futures
import random
import sys

if __name__ == "__main__":

    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.DEBUG, datefmt="%H:%M:%S")

#: Door 1
s_door_1 = threading.Semaphore(1)

#: Door 2
s_door_2 = threading.Semaphore(1)

#: Table assignment semaphore
s_table_pick = threading.Semaphore(1)

#: Customer count semaphore
s_customer_count = threading.Semaphore(1)

#: Kitchen
s_kitchen = threading.Semaphore(1)

#: Pay Station
s_payment = threading.Semaphore(1)

#: Waiters
s_waiters = threading.Semaphore(3)

#: Waiter / customer pipeline


class Pipeline():
    def __init__(self, table):
        self.order = None
        self.l_set = threading.Lock()
        self.l_get = threading.Lock()
        self.l_get.acquire()

    def set_order(self, id):
        logging.debug("Pipeline: %s about to acquire setlock", id)
        self.l_set.acquire()
        logging.debug("Pipeline: %s has setlock", id)
        self.order = id
        logging.debug("Pipeline: %s about to release getlock", id)
        self.l_get.release()
        logging.debug("Pipeline: %s getlock released", id)

    def get_order(self, id):
        logging.debug("Pipeline: %s about to acquire getlock", id)
        self.l_get.acquire()
        logging.debug("Pipeline: %s: has getlock", id)
        order = self.order
        logging.debug("Pipeline: %s about to release setlock", id)
        self.l_set.release()
        logging.debug("Pipeline: %s setlock released", id)
        return order


test = threading.Semaphore(0)

#: Table A
table_a = {'string': 'A',
           'semaphore': threading.Semaphore(4),
           's_customer': threading.Semaphore(0),
           's_waiter': threading.Semaphore(0),
           'pipeline': Pipeline('A'),
           'seated': 0,
           'line': 0,
           'food': 'seafood',
           'waiter': None}

#: Table B
table_b = {'string': 'B',
           'semaphore': threading.Semaphore(4),
           's_customer': threading.Semaphore(0),
           's_waiter': threading.Semaphore(0),
           'pipeline': Pipeline('B'),
           'seated': 0,
           'line': 0,
           'food': 'steak',
           'waiter': None}

#: Table C
table_c = {'string': 'C',
           'semaphore': threading.Semaphore(4),
           's_customer': threading.Semaphore(0),
           's_waiter': threading.Semaphore(0),
           'pipeline': Pipeline('C'),
           'seated': 0,
           'line': 0,
           'food': 'pasta',
           'waiter': None}

customer_count = 0
end = False


def t_customer(id):
    global customer_count
    #: customer enters door
    #: determine which door to try based on id odd / even
    if id % 2 == 0:
        s_door_1.acquire()
        logging.info("T_Customer %s: entered door 1", id)
        s_door_1.release()

    else:
        s_door_2.acquire()
        logging.info("T_Customer %s: entered door 2", id)
        s_door_2.release()

    customer_count += 1

    #: determine table choice order randomly
    table_choices = [table_a, table_b, table_c]
    random.shuffle(table_choices)

    logging.info("T_Customer %s: table order is %s, %s, %s", id, table_choices[0].get(
        'string'), table_choices[1].get('string'), table_choices[2].get('string'))

    #: sit down
    table = table_choices[0]
    for i in table_choices:
        #: if the line is short enough or at the last table choice, sit
        if i['line'] < 7 or table_choices.index(i) == len(table_choices):
            i['line'] += 1
            i['semaphore'].acquire()
            i['line'] -= 1
            table = i
            logging.info("T_Customer %s: sat at table %s", id, i['string'])
            table['seated'] += 1
            break

    #: call waiter
    table['pipeline'].set_order(id)
    # table['s_customer'].acquire()
    test.acquire()

    #: wait on food
    table['s_waiter'].release()
    table['s_customer'].acquire()

    #: eat food
    wait_time = random.randint(200, 1000) / 1000
    time.sleep(wait_time)

    #: leave
    table['semaphore'].release()
    logging.info("T_Customer %s: left table %s", id, i['string'])
    table['seated'] -= 1

    #: pay bill
    s_payment.acquire()
    logging.info("T_Customer %s: paid their bill", id)
    s_payment.release()

    #: leave restaurant
    if id % 2 == 0:
        s_door_1.acquire()
        logging.info("T_Customer %s: left through door 1", id)
        s_door_1.release()

    else:
        s_door_2.acquire()
        logging.info("T_Customer %s: left through door 2", id)
        s_door_2.release()

    s_customer_count.acquire()
    customer_count -= 1
    logging.info("Main: customer count: %s", customer_count)
    if customer_count == 0:
        end.set()
    s_customer_count.release()

    sys.exit()


def t_waiter(id):

    #: waiter enters door
    #: determine which door to try based on id odd / even
    if id % 2 == 0:
        s_door_1.acquire()
        logging.info("T_Waiter %s: entered door 1", id)
        s_door_1.release()

    else:
        s_door_2.acquire()
        logging.info("T_Waiter %s: entered door 2", id)
        s_door_2.release()

    #: choose table
    s_table_pick.acquire()
    if table_a['waiter'] == None:
        table_a['waiter'] = id
        table = table_a
        logging.info("T_Waiter %s: chose table a", id)
    elif table_b['waiter'] == None:
        table_b['waiter'] = id
        table = table_b
        logging.info("T_Waiter %s: chose table b", id)
    else:
        table_c['waiter'] = id
        table = table_c
        logging.info("T_Waiter %s: chose table c", id)
    s_table_pick.release()

    table['s_waiter'].acquire()

    while end.isSet() == False:
        table['s_waiter'].acquire()

        order = table['pipeline'].get_order(id)
        logging.info("T_Waiter %s: took customer %s's order", id, order)

        #: deliver order
        s_kitchen.acquire()
        wait_time = random.randint(100, 500) / 1000
        time.sleep(wait_time)
        logging.info(
            "T_Waiter %s: delivered order %s to the kitchen", id, order)
        s_kitchen.release()

        #: wait for order
        wait_time = random.randint(300, 1000) / 1000
        time.sleep(wait_time)

        #: get order
        s_kitchen.acquire()
        wait_time = random.randint(100, 500) / 1000
        time.sleep(wait_time)
        logging.info(
            "T_Waiter %s: received order %s from the kitchen", id, order)
        s_kitchen.release()

        #: deliver order
        logging.info(
            "T_Waiter %s: delivered customer %s's order", id, order)

        table['s_waiter'].release()
        table['s_customer'].release()

    #: clean table and exit
    logging.info("T_Waiter %s: cleaned table %s", id, table['string'])

    if id % 2 == 0:
        s_door_1.acquire()
        logging.info("T_Waiter %s: left through door 1", id)
        s_door_1.release()

    else:
        s_door_2.acquire()
        logging.info("T_Waiter %s: left through door 2", id)
        s_door_2.release()

    sys.exit()


end = threading.Event()


s_waiter_spawn = threading.Semaphore(3)
s_waiter_spawn.acquire()
s_waiter_spawn.acquire()
s_waiter_spawn.acquire()


#: customer thread spawner
# with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
#     executor.map(t_customer, range(3))
for i in range(0, 3):
    t = threading.Thread(target=t_customer(i,))
    t.start()


print('hello')

#: waiter thread spawner
for i in range(0, 3):
    t = threading.Thread(target=t_waiter(i,))
    t.start()
