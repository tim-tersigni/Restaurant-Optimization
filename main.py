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
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

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

#: Table A
table_a = {'string': 'A',
           'semaphore': threading.Semaphore(4),
           'queue': Queue(4),
           'seated': 0,
           'line': 0,
           'q_line': Queue(30),
           'food': 'seafood',
           'waiter': None}

#: Table B
table_b = {'string': 'B',
           'semaphore': threading.Semaphore(4),
           'queue': Queue(4),
           'seated': 0,
           'line': 0,
           'q_line': Queue(30),
           'food': 'steak',
           'waiter': None}

#: Table C
table_c = {'string': 'C',
           'semaphore': threading.Semaphore(4),
           'queue': Queue(4),
           'seated': 0,
           'line': 0,
           'q_line': Queue(30),
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

    table_choices = table_choices[0:2]
    r = random.randint(0, 1)
    if r == 0:
        table_choices = table_choices[0:1]
        logging.info("T_Customer %s: table choices are %s", id, table_choices[0].get('string'))
    else:
        logging.info("T_Customer %s: table choices are %s, %s", id, table_choices[0].get('string'), table_choices[1].get('string'))


    #: pick table
    table = table_choices[0]
    if len(table_choices) > 1:
        if table['line'] > 7 and table_choices[1].get('line') < 7:
            table = table_choices[1]

    #: sit down if empty seat, otherwise enter line
    if table['seated'] < 4:
        #: sit
        table['semaphore'].acquire()
        table['seated'] += 1
        
        #: call waiter
        table['queue'].put(id)
        logging.info("T_Customer %s: placed order", id)
        table['semaphore'].release()
    else:
        #: enter line
        table['line'] += 1
        table['q_line'].set(id)



def t_customer_post(id, table):
    global customer_count

    #: eat food
    wait_time = random.randint(200, 1000) / 1000
    time.sleep(wait_time)

    #: leave
    table['semaphore'].release()
    logging.info("T_Customer %s: left table %s", id, table['string'])
    table['seated'] -= 1

    #: pay bill
    s_payment.acquire()
    logging.info("T_Customer %s: paid their bill", id)
    s_payment.release()

    #: leave table, allow next customer in line


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

    while table['line'] > 0 or table['seated'] > 0:
        #: getting order HERE TODO
        order = table['queue'].get()
        table['queue'].task_done()
        logging.debug("T_Waiter %s: got order %s", id, order)

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

        #: deliver order TODO
        logging.info(
            "T_Waiter %s: delivered customer %s's order", id, order)

        c = threading.Thread(target=t_customer_post(order, table))
        c.start()

        #: clean table
        logging.info("T_Waiter %s: cleaned table %s", id, table['string'])


end = threading.Event()


s_waiter_spawn = threading.Semaphore(3)
s_waiter_spawn.acquire()
s_waiter_spawn.acquire()
s_waiter_spawn.acquire()


#: customer thread spawner
for i in range(0, 30):
    t = threading.Thread(target=t_customer(i,))
    t.start()

#: waiter thread spawner
for i in range(0, 3):
    t = threading.Thread(target=t_waiter(i,))
    t.start()

#: waiters can leave
for id in range(0, 3):

    if id % 2 == 0:
        s_door_1.acquire()
        logging.info("T_Waiter %s: left through door 1", id)
        s_door_1.release()

    else:
        s_door_2.acquire()
        logging.info("T_Waiter %s: left through door 2", id)
        s_door_2.release()