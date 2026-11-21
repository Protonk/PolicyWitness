#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
int main(int c,char**v){ int fd=open(CFG,O_RDONLY); if(fd<0){fprintf(stderr,"open failed: %s\n",strerror(errno));return 2;}
 char b[256]; ssize_t n=read(fd,b,sizeof b); if(n<0){fprintf(stderr,"read failed: %s\n",strerror(errno));return 3;} fwrite(b,1,n,stdout); return 0;}
