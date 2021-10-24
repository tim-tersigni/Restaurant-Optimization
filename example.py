import threading

gLock = threading.Semaphore(1)


def threadcode(id):
    gLock.acquire()
    print("Thread " + str(id) + " has count " + str(gCount))
    gLock.release()


for i in range(0, 5):
    t = threading.Thread(target=threadcode, args=(i,))
    t.start()
