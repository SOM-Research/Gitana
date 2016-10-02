__author__ = 'valerio cosentino'

import sys
sys.path.insert(0, "..//..")

import multiprocessing
import time


def start_consumers(processes, task_queue, result_queue):
    num_consumers = processes
    consumers = [Consumer(task_queue, result_queue) for i in xrange(num_consumers)]
    for w in consumers:
        w.start()


class Consumer(multiprocessing.Process):

    def __init__(self, task_queue, result_queue):
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue

    def run(self):
        while not self.task_queue.empty():
            next_task = self.task_queue.get()
            answer = next_task()
            self.task_queue.task_done()
            #self.result_queue.put(answer)

        return