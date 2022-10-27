## ISO Extract

### Inspect ISO files

Declare ISO path
```shell
iso_path=~/Downloads/BornToSecHackMe-v1.1.iso
```

```shell
python3 ../scripts/writeup4/ls_iso.py "/" $iso_path
```

### A little deeper
```shell
python3 ../scripts/writeup4/ls_iso.py "/CASPER" $iso_path
```

### Extract squashfs and get Zaz password
```shell
python3 ../scripts/writeup4/extract_file_iso.py "/root/.bash_history" $iso_path
rm filesystem.squashfs
cat .bash_history | grep -A1 "adduser zaz"
ssh_login="zaz"
ssh_password=`cat .bash_history | grep -A1 "adduser zaz" | head -n 1`
echo $ssh_password
rm .bash_history
```

-> [Zaz Part Writeup2](../writeup2.md#Inspect Zaz)