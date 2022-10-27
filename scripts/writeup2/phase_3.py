import random

first, second = 0, 'b'

i = 0
c = None

chars = ['q', 'b', 'b', 'k', 'o', 't', 'v', 'b', 'x']
numbers = [777, 214, 755, 251, 160, 458, 780, 524]

for third in numbers:
    while i <= 7:
        if third == numbers[i]:
            c = chars[i]
            break
        i += 1
        first += 1
    if c == second:
        print(first, second, third)
        break



