import logging
import threading
from queue import Queue
import time
import random


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
           'semaphore': threading.Semaphore(1),
           'queue': Queue(4),
           'seated': 0,
           'line': 0,
           'q_line': Queue(30),
           'food': 'seafood',
           'waiter': None}

#: Table B
table_b = {'string': 'B',
           'semaphore': threading.Semaphore(1),
           'queue': Queue(4),
           'seated': 0,
           'line': 0,
           'q_line': Queue(30),
           'food': 'steak',
           'waiter': None}

#: Table C
table_c = {'string': 'C',
           'semaphore': threading.Semaphore(1),
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
    table['semaphore'].acquire()
    if table['seated'] < 4:
        #: sit
        table['seated'] += 1
        
        #: call waiter
        table['queue'].put(id)
        logging.info("T_Customer %s: placed order", id)
        table['semaphore'].release()
    else:
        #: enter line
        table['line'] += 1
        table['q_line'].put(id)
    table['semaphore'].release()


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

    #: allow next customer in line
    if table['line'] > 0:
        table['semaphore'].acquire()
        table['line'] -= 1
        id = table['q_line'].get()
        if table['seated'] < 4:
        #: sit
            table['seated'] += 1
            
            #: call waiter
            table['queue'].put(id)
            logging.info("T_Customer %s: placed order", id)
            table['semaphore'].release()
        else:
            #: enter line
            table['line'] += 1
            table['q_line'].put(id)
        table['semaphore'].release()
    


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



end = threading.Event()

#: waiters enter
#: determine which door to try based on id odd / even
for id in range(0, 3):
    if id % 2 == 0:
        s_door_1.acquire()
        logging.info("T_Waiter %s: entered door 1", id)
        s_door_1.release()

    else:
        s_door_2.acquire()
        logging.info("T_Waiter %s: entered door 2", id)
        s_door_2.release()

#: customer thread spawner
for i in range(0, 30):
    t = threading.Thread(target=t_customer(i,))
    t.start()

#: waiter thread spawner
for i in range(0, 3):
    t = threading.Thread(target=t_waiter(i,))
    t.start()

#: waiters can leave
logging.info("T_Waiter %s: cleaned table a", table_a['waiter'])
logging.info("T_Waiter %s: cleaned table b", table_b['waiter'])
logging.info("T_Waiter %s: cleaned table c", table_c['waiter'])

for id in range(0, 3):

    if id % 2 == 0:
        s_door_1.acquire()
        logging.info("T_Waiter %s: left through door 1", id)
        s_door_1.release()

    else:
        s_door_2.acquire()
        logging.info("T_Waiter %s: left through door 2", id)
        s_door_2.release()