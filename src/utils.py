import time


def func_cost(func):
    def fun(*args, **kwargs):
        st = time.time()
        result = func(*args, **kwargs)
        print(f'func {func.__name__} cost time: {time.time() - st}s')
        return result
    return fun