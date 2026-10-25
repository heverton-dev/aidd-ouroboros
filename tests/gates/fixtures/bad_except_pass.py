def bad_handler():
    try:
        val = 1 / 0
    except ZeroDivisionError:
        pass
