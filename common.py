__DEBUG__ = True

def debug(*args):
    """Equivalent to print if DEBUG is set to true. Null function if DEBUG is set to false"""
    if __DEBUG__:
        print(*args)