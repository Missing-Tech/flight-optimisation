# SuperFastPython.com
# example of calling submit with a function call
from time import sleep
from random import random
from concurrent.futures import ProcessPoolExecutor, as_completed


class Test:
    # custom task that will sleep for a variable amount of time
    def task(self, i):
        # sleep for less than a second
        print(f"started {i}", flush=True)
        sleep(random())
        return f"all done {i}"

    # entry point
    def main(self):
        solutions = []
        # start the process pool
        for i in range(10):
            with ProcessPoolExecutor(max_workers=4) as executor:
                # submit the task
                futures = [executor.submit(self.task, i) for i in range(20)]
            # get the result
            for future in as_completed(futures):
                result = future.result()
                solutions.append(result)
                print(result)


if __name__ == "__main__":
    test = Test()
    test.main()
