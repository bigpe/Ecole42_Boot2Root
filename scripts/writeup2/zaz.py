import sys

import paramiko
from paramiko import SSHClient

PATTERN = 'AAAABBBBCCCCDDDDEEEEFFFFGGGGHHHHIIIIJJJJKKKKLLLLMMMMNNNNOOOOPPPPQQQQRRRRSSSSTTTT' \
          'UUUUVVVVWWWWXXXXYYYYZZZZaaaabbbbccccddddeeeeffffgggghhhhiiiijjjjkkkkllll' \
          'mmmmnnnnooooppppqqqqrrrrssssttttuuuuvvvvwwwwxxxxyyyyzzzz'


def exec(client: SSHClient, command: str, err=False, read_method='readlines', silent=False):
    stdin, stdout, stderr = client.exec_command(command)

    read_from = 'stdout'
    if err:
        read_from = 'stderr'

    def read(stdin, stdout, stderr):
        return [line.strip() if read_method == 'readlines' else line for line in
                getattr(locals()[read_from], read_method)()]

    return read(stdin, stdout, stderr)


def get_connect_command(user, password, ip):
    command = f'sshpass -p {password} ssh {user}@{ip} -oStrictHostKeyChecking=no'
    return command


def connect(user: str, password: str, ip: str):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=ip, username=user, password=password, port=22)
    except OSError:
        print('Host is down, connection impossible')
        exit()
    return client


def find_offset(client, binary_name, register='eip', pattern=PATTERN, env=None,
                stdin=False, command_after_pattern=None, before_run=None):
    stdin_prefix = f'echo "{pattern}" | '
    address = exec(client, f'echo "y" | {stdin_prefix if stdin else ""}'
                           f'{command_after_pattern + " |" if command_after_pattern else ""}'
                           f'{env if env else ""} gdb ./{binary_name} -q '
                           f'{"-ex " + before_run + " " if before_run else ""}'
                           f'-ex "r{"" if stdin else f" {pattern}"} " '
                           f'-ex "i r" '
                           f'-ex "q" | '
                           f'grep "{register}" | '
                           f'sed \'s/(gdb)//\' | '
                           f'awk \'{{print $2}}\''
                   )
    if address:
        address_short = bytes.fromhex(address[0].split('x')[1][:2]).decode('ascii')
        num = 65
        if address_short.islower():
            num = num + 6
        offset = (ord(address_short[0]) - num) * 4
        return offset
    return 0


def address_to_string(address):
    if isinstance(address, bytes):
        address = str(address)
    if ' ' in address:
        address = address.split(' ')[1]
    address = address.replace("'", '')
    address = address[2:]
    address = address[::-1]
    res = []
    for i, x in enumerate(address):
        if not i % 2:
            if len(address) > i + 1:
                res.append(f'\\x{address[i + 1]}{x}')
            else:
                res.append(f'\\x0{x}')
    return ''.join(res)


if __name__ == '__main__':
    if sys.argv[1] == 'offset':
        client = connect(sys.argv[2], sys.argv[3], sys.argv[4])
        print(find_offset(client, 'exploit_me'))
    if sys.argv[1] == 'address':
        print(address_to_string(sys.argv[2]))
