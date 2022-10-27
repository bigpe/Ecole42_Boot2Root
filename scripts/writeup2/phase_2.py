def valid_number(i, n):
    print('By index', i, 'Number is', n)


def check_number(arr, j):
    if arr[j] != (arr[j - 1] * (j + 1)):
        arr[j] = arr[j] + 1
        if j == 0 and arr[j] == 1:
            valid_number(j, arr[j])
            return True
        return check_number(arr, j)
    else:
        valid_number(j, arr[j])
    return True


def main():
    i = 0
    input_numbers = [1] * 6

    while i <= 5:
        check_number(input_numbers, i)
        i += 1
    return input_numbers


if __name__ == '__main__':
    result = main()
    result = [str(r) for r in result]
    print(f"Result:{' '.join(result)}")
