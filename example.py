import threading
import time

gLock = threading.Semaphore(1)
gCount = 0


def test_func(s, id):
    global gCount
    s.acquire()
    print("Thread " + str(id) + " has count " + str(gCount))
    gCount = gCount+1
    time.sleep(1)
    gLock.release()


def threadcode(id):
    test_func(gLock, id)
    gLock.acquire()
    print("Thread " + str(id) + " has count " + str(gCount))
    gLock.release()


for i in range(0, 5):
    t = threading.Thread(target=threadcode, args=(i,))
    t.start()
