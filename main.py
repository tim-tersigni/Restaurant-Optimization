import logging
import threading
import time
import concurrent.futures
import random

if __name__ == "__main__":

    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

#: Door 1
s_door_1 = threading.Semaphore(1)

#: Door 2
s_door_2 = threading.Semaphore(1)

#: Table A
table_a = {'string': 'A', 'semaphore': threading.Semaphore(4), 'line': 0}

#: Table B
table_b = {'string': 'B', 'semaphore': threading.Semaphore(4), 'line': 0}

#: Table C
table_c = {'string': 'C', 'semaphore': threading.Semaphore(4), 'line': 0}


def t_customer_code(id):
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

    #: determine table choice order randomly
    table_choices = [table_a, table_b, table_c]
    random.shuffle(table_choices)

    logging.info("T_Customer %s: table order is %s, %s, %s", id, table_choices[0].get(
        'string'), table_choices[1].get('string'), table_choices[2].get('string'))

    #: sit down
    table = None
    for i in table_choices:
        #: if the line is short enough or at the last table choice, sit
        if i['line'] < 7 or table_choices.index(i) == len(table_choices):
            i['line'] += 1
            i['semaphore'].acquire()
            i['line'] -= 1
            table = i
            logging.info("T_Customer %s: sat at table %s", id, i['string'])

    table['semaphore'].release()
    logging.info("T_Customer %s: left table %s", id, i['string'])


#: customer thread spawner
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    executor.map(t_customer_code, range(5))
