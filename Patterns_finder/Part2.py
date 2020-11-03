import queue
import urllib.request

import Part1
import threading
import time


def execution_function(workers_amount, max_workers_per_sec, url, encoding, keyword_filename, sec_limit_amount):
    """
    made for initialization of parameters values

    :param workers_amount: number of working threads in total.
    :param max_workers_per_sec: the rate limit in a single time unit.
    :param url: the url to which the workers will send requests to
    :param encoding: is the type of the decryption needed to read the response from the request.
    :param keyword_filename: is the filename from which we read the keywords.
    :param sec_limit_amount: defines the time unit for the rate limiting.
    :return: void
    """
    workers_amount[0] = 12
    max_workers_per_sec[0] = 7
    url[0] = "https://en.wikipedia.org/wiki/Special:Random"
    encoding[0] = "utf-8"
    keyword_filename[0] = "keywords.txt"
    sec_limit_amount[0] = 1


def print_worker(worker_id, url, matches):
    print("Worker: " + str(worker_id) + "\nRandom URL: " + url + "\nMatches: " + str(
        matches) + "\n-----------------------------")


def main():
    workers_amount = [0]
    max_workers_per_sec = [0]
    url = [""]
    encoding = [""]
    keyword_filename = [""]
    sec_limit_amount = [0]
    execution_function(workers_amount, max_workers_per_sec, url, encoding, keyword_filename, sec_limit_amount)
    scheduler = Scheduler(workers_amount[0], max_workers_per_sec[0], url[0], encoding[0], keyword_filename[0],
                          sec_limit_amount[0])
    scheduler.create_threads()
    scheduler.activate_threads()


class Shared_Resource:
    def __init__(self):
        self.last_time = time.time()
        self.total_requests_sent = 0
        self.permission = False  # signs if workers can send a request
        self.terminate = False  # signs if workers should terminate
        self.terminated_workers = 0


class My_Thread(threading.Thread):
    def __init__(self, resource_lock, resource):
        threading.Thread.__init__(self)
        self.resource_lock = resource_lock
        self.resource = resource


class Worker_Thread(My_Thread):
    def __init__(self, worker_id, resource_lock, url, encoding, keyword_filename, resource):
        """

        :param worker_id: Worker serial number
        :param resource_lock: The lock for access and modify the resource
        :param url: Url request
        :param encoding: Encoding type of the response
        :param keyword_filename: Keywords filename
        :param resource: Pointer to the shared resource
        """
        My_Thread.__init__(self, resource_lock, resource)
        self.worker_id = worker_id
        self.resource_lock = resource_lock
        self.requested = False
        self.url = url
        self.encoding = encoding
        self.keyword_filename = keyword_filename

    def run(self) -> None:
        response = None
        while not self.resource.terminate:  # while didn't get a sign to terminate
            while not self.requested:  # while didn't send yet a request, keep trying to get permission
                self.resource_lock.acquire()
                if self.resource.permission:  # if timer allowed to sent a request
                    self.resource.permission = False
                    self.resource.last_time = time.time()
                    # no need in try\except because we already check the url is suitable
                    response = urllib.request.urlopen(self.url)
                    self.resource.total_requests_sent += 1
                    self.requested = True
                    self.resource_lock.release()
                else:
                    self.resource_lock.release()
            if self.requested:  # treat the response
                wiki_text = response.read().decode(self.encoding)
                finder = Part1.Patterns_Finder(self.keyword_filename, wiki_text)
                output_list = finder.find_patterns()
                print_worker(self.worker_id, response.url, output_list)
                self.requested = False
        self.resource_lock.acquire()
        self.resource.terminated_workers += 1  # updates the number of terminated workers
        self.resource_lock.release()


class Timer_Thread(My_Thread):
    def __init__(self, resource_lock, number_of_workers, max_req_per_sec, sec_limit_amount, resource):
        """

        :param resource_lock: The lock for access and modify the resource
        :param number_of_workers: How much workers total should work
        :param max_req_per_sec: How much requests are legal in one time unit
        :param sec_limit_amount: Number of seconds which represents the time unit
        :param resource: Pointer to the shared resource
        """
        My_Thread.__init__(self, resource_lock, resource)
        self.number_of_workers = number_of_workers
        self.max_req_per_sec = max_req_per_sec
        self.sec_limit_amount = sec_limit_amount

    def run(self) -> None:
        """Timer terminates only after all workers terminated"""
        while self.resource.terminated_workers < self.number_of_workers:
            current_time = time.time()
            self.resource_lock.acquire()
            interval = current_time - self.resource.last_time  # how much time passed since last request
            if interval > self.sec_limit_amount:  # new time unit
                self.resource.total_requests_sent = 0
                self.resource.permission = True
            elif self.resource.total_requests_sent < self.max_req_per_sec:  # didn't reach the limit of requests in
                # time unit
                self.resource.permission = True
            else:
                self.resource.permission = False
            self.resource_lock.release()


class Scheduler:
    def __init__(self, number_of_workers, max_req_per_sec, url, encoding, keyword_filename, sec_limit_amount):
        """

        :param number_of_workers: How much workers total should work
        :param max_req_per_sec: How much requests are legal in one time unit
        :param url: Url request
        :param encoding: Encoding type of the response
        :param keyword_filename: Keywords filename
        :param sec_limit_amount: Number of seconds which represents the time unit
        """
        self.resource = Shared_Resource()
        self.workers_threads = queue.Queue(number_of_workers)
        self.resource_lock = threading.Lock()
        self.timer = Timer_Thread(self.resource_lock, number_of_workers,
                                  max_req_per_sec, sec_limit_amount, self.resource)
        self.number_of_workers = number_of_workers
        self.max_req_per_sec = max_req_per_sec
        self.url = url
        self.encoding = encoding
        self.keyword_filename = keyword_filename

    def create_threads(self):
        for i in range(self.number_of_workers):
            self.workers_threads.put(Worker_Thread(i + 1, self.resource_lock, self.url, self.encoding,
                                                   self.keyword_filename, self.resource))

    def activate_threads(self):
        """Activate the timer thread and all workers thread, wait for any input to terminate all threads"""
        if self.max_req_per_sec < 1:
            # if it's not possible to send even 1 request per time unit then there's nothing to do
            return
        try:
            urllib.request.urlopen(self.url)  # try to get a request to check if the url is suitable
            self.resource.total_requests_sent += 1
        except Exception as e:  # if url isn't suitable
            print(e)
            return
        self.timer.start()
        while not self.workers_threads.empty():
            self.workers_threads.get().start()
        input()  # wait for any input to terminate all threads
        self.resource.terminate = True


if __name__ == "__main__":
    main()
