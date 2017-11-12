#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import multiprocessing
import sys
sys.path.insert(0, "..//..")


def start_consumers(num_consumers, task_queue, result_queue):
    consumers = [Consumer(task_queue, result_queue) for i in xrange(num_consumers)]
    for w in consumers:
        w.start()


def add_poison_pills(processes, task_queue):
    for i in xrange(processes):
        task_queue.put(None)


def get_tasks_intervals(elements, num_processes):
    elements.sort()
    chunk_size = len(elements)/num_processes

    if len(elements) % num_processes != 0:
        chunk_size += 1

    if chunk_size == 0:
        chunks = [elements]
    else:
        chunks = [elements[i:i + chunk_size] for i in range(0, len(elements), chunk_size)]

    intervals = []
    for chunk in chunks:
        intervals.append(chunk)

    return intervals


class Consumer(multiprocessing.Process):
    """
    This class provides multiprocessing utilities
    """

    def __init__(self, task_queue, result_queue):
        """
        :type task_queue: Object
        :param task_queue: the queue of the tasks

        :type result_queue: Object
        :param result_queue: the queue of the results
        """
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue

    def run(self):
        """
        runs the consumer's task
        """
        while True:
            next_task = self.task_queue.get()
            if next_task is None:
                self.task_queue.task_done()
                break

            next_task()
            self.task_queue.task_done()

        return
