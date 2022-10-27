expected = "giants"
alpha = "abcdefghijklmnopqrstuvwxyz"


def phase_5(line):
    static_string = "isrveawhobpnutfg"
    r = ""
    for c in line:
        i = ord(c) & 0xf
        r += static_string[i]
    return r


char_mapping = {phase_5(c): c for c in alpha}

result = ""
for c in expected:
    result += char_mapping[c]

print(result)
