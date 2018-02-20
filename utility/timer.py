import time


def time_func(the_function, *args):
    before = time.time()
    to_return = the_function(*args)
    after = time.time()

    return to_return, after-before

timer_running = False
start_time = 0


def toggle_timer():
    global timer_running
    global start_time

    if not timer_running:
        timer_running = True
        start_time = time.time()

    else:
        timer_running = False
        print(f"Elapsed time: {time.time() - start_time}")


def compare_functions(func1, func2, *args):
    first_r, first_time = time_func(func1, *args)
    second_r, second_time = time_func(func2, *args)

    print(f"First function took {first_time} seconds to complete.")
    print(f"Second function took {second_time} seconds to complete.")

    if first_time == second_time:
        print(f"The functions took the same amount of time to complete!")

    elif first_time > second_time:
        print(f"\nSecond function was {first_time - second_time} seconds faster.")

    else:
        print(f"\nFirst function was {second_time - first_time} seconds faster.")

    return first_r, second_r