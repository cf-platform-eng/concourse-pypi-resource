import time


def retry_wrapper(count=3, delay_in_seconds=1):
    def decorator(function):
        def wrapper(*args, **kwargs):
            tries = 0
            while True:
                try:
                    tries += 1
                    print("Resiliently (%d/%d) trying `%s` from module `%s`" %
                          (tries, count, function.__name__, function.__module__))
                    print("-- with arguments: ", args, kwargs)
                    result = function(*args, **kwargs)
                    return result
                except Exception as e:
                    if tries >= count:
                        print("-- Failed retrying after %d tries with a %f second delay" %
                              (tries, delay_in_seconds))
                        raise e
                    time.sleep(delay_in_seconds)

        return wrapper

    return decorator
