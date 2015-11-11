from functools import wraps
import errno
import os
import signal
import time


class TimeoutError(Exception):
    pass


def settimeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator


class timeout:
    def __init__(self, seconds, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, type, value, traceback):
        signal.alarm(0)


@settimeout(2)
def test2():
    time.sleep()


if __name__ == "__main__":
    try:
        with timeout(2):
            time.sleep(3)
    except TimeoutError:
        print("test 1 timeout")
    try:
        test2()
    except TimeoutError:
        print("test 2 timeout")
