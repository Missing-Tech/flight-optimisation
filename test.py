# SuperFastPython.com
# example of calling submit with a function call
from time import sleep
from random import random
from concurrent.futures import ProcessPoolExecutor, as_completed


# custom task that will sleep for a variable amount of time
def task(i):
    # sleep for less than a second
    sleep(random())
    print(i, flush=True)
    return "all done"


# entry point
def main():
    # start the process pool
    with ProcessPoolExecutor(max_workers=4) as executor:
        # submit the task
        futures = [executor.submit(task, i) for i in range(20)]
        # get the result
        for future in as_completed(futures):
            result = future.result()
            print(result)


if __name__ == "__main__":
    main()
