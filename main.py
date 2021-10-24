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
s_table_a = threading.Semaphore(4)
table_a_line = 0

#: Table B
s_table_b = threading.Semaphore(4)
table_b_line = 0

#: Table C
s_table_c = threading.Semaphore(4)
table_c_line = 0


def t_customer_code(id):
    def pick_table(table_choices):
        if table_choices[0] == 'A':
            if table_a_line < 7:
                s_table_a.acquire()
                table_a_line += 1
            else:
                #: go to second choice
                if table_choices[1] == 'B':
                    if table_b_line < 7:
                        s_table_b.acquire()
                        table_b_line += 1
                    else:
                        #: go to last choice
                        s_table_c.acquire()
                        table_c_line += 1

                else:  # : table_choices[1] == 'C'
                    if table_c_line < 7:
                        s_table_c.acquire()
                        table_c_line += 1
                    else:
                        #: go to last choice
                        s_table_b.acquire()
                        table_b_line += 1

        if table_choices[0] == 'B':
            if table_b_line < 7:
                s_table_b.acquire()
                table_b_line += 1
            else:
                #: go to second choice
                if table_choices[1] == 'A':
                    if table_a_line < 7:
                        s_table_a.acquire()
                        table_a_line += 1
                    else:
                        #: go to last choice
                        s_table_c.acquire()
                        table_c_line += 1

                else:  # : table_choices[1] == 'C'
                    if table_c_line < 7:
                        s_table_c.acquire()
                        table_c_line += 1
                    else:
                        #: go to last choice
                        s_table_a.acquire()
                        table_a_line += 1

        if table_choices[0] == 'C':
            if table_c_line < 7:
                s_table_c.acquire()
                table_c_line += 1
            else:
                #: go to second choice
                if table_choices[1] == 'A':
                    if table_a_line < 7:
                        s_table_a.acquire()
                        table_a_line += 1
                    else:
                        #: go to last choice
                        s_table_b.acquire()
                        table_b_line += 1

                else:  # : table_choices[1] == 'B'
                    if table_b_line < 7:
                        s_table_b.acquire()
                        table_b_line += 1
                    else:
                        #: go to last choice
                        s_table_a.acquire()
                        table_a_line += 1
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
    table_choices = ['A', 'B', 'C']
    random.shuffle(tables)

    logging.info("T_Customer %s: table order is %s, %s, %s", id,
                 table_choices, table_choices, table_choices)

    #: look for table
    pick_table(table_choices)


#: customer thread spawner
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    executor.map(t_customer_code, range(5))
