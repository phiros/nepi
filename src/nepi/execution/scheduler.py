#
#    NEPI, a framework to manage network experiments
#    Copyright (C) 2013 INRIA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Alina Quereilhac <alina.quereilhac@inria.fr>

import itertools
import heapq

class TaskStatus:
    """ Execution state of the Task
    """
    NEW = 0
    DONE = 1
    ERROR = 2

class Task(object):
    """ A Task represents an operation to be executed by the 
    ExperimentController scheduler
    """

    def __init__(self, timestamp, callback):
        """
        :param timestamp: Future execution date of the operation
        :type timestamp: str

        :param callback: A function to invoke in order to execute the operation
        :type callback: function

        """ 
        self.id = None 
        self.timestamp = timestamp
        self.callback = callback
        self.result = None
        self.status = TaskStatus.NEW

class HeapScheduler(object):
    """ Create a Heap Scheduler

    .. note::

        This class is thread safe.
        All calls to C Extensions are made atomic by the GIL in the CPython implementation.
        heapq.heappush, heapq.heappop, and list access are therefore thread-safe.

    """

    def __init__(self):
        super(HeapScheduler, self).__init__()
        self._queue = list() 
        self._valid = set()
        self._idgen = itertools.count(1)

    @property
    def pending(self):
        """ Returns the list of pending task ids """
        return self._valid

    def schedule(self, task):
        """ Add a task to the queue ordered by task.timestamp and arrival order

        :param task: task to schedule
        :type task: task
        """
        if task.id == None:
            task.id = self._idgen.next()

        entry = (task.timestamp, task.id, task)
        self._valid.add(task.id)
        heapq.heappush(self._queue, entry)
        return task

    def remove(self, tid):
        """ Remove a task form the queue

        :param tid: Id of the task to be removed
        :type tid: int

        """
        try:
            self._valid.remove(tid)
        except:
            pass

    def next(self):
        """ Get the next task in the queue by timestamp and arrival order
        """
        while self._queue:
            try:
                timestamp, tid, task = heapq.heappop(self._queue)
                if tid in self._valid:
                    self.remove(tid)
                    return task
            except IndexError:
                # heap empty
                pass
        return None

