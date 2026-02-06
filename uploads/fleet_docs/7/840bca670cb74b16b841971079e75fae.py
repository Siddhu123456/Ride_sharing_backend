"""
This module demonstrates basic addition logic and is used
to practice pylint, docstrings, and code quality improvements.
"""


def calc(a, b):
    '''This function is used to add two number'''
    result = a + b
    if result is True:
        print("Result is true")
    return result


def main():
    '''This is main method'''
    x = 10
    y = "20"
    print(calc(x, y))


main()
