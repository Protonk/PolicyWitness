#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <stdint.h>
extern char *sandbox_extension_issue_file(const char *, const char *, uint32_t);
extern int64_t sandbox_extension_consume(const char *);
extern int sandbox_extension_release(int64_t);
extern int sandbox_init(const char *, uint64_t, char **);
static void rdfd(const char*tag,int fd){char b[64];ssize_t n=pread(fd,b,sizeof b,0);printf("%s fd read n=%zd errno=%d\n",tag,n,n<0?errno:0);}
static void fresh(const char*tag,const char*p){int fd=open(p,O_RDONLY);if(fd<0){printf("%s fresh open errno=%d\n",tag,errno);return;}rdfd(tag,fd);close(fd);}
int main(int c,char**v){const char*p=v[1];
 char*tok=sandbox_extension_issue_file("com.apple.app-sandbox.read",p,0);
 if(!tok){printf("issue null\n");return 1;}
 char*err=0;
 if(sandbox_init("(version 1)(allow default)(deny file-read-data)(deny file-write*)(allow file-read-data (extension \"com.apple.app-sandbox.read\"))",0,&err)){printf("init: %s\n",err);return 1;}
 fresh("before",p);
 int64_t h=sandbox_extension_consume(tok); printf("consume=%lld\n",(long long)h);
 int fd=open(p,O_RDONLY); printf("held open fd=%d errno=%d\n",fd,fd<0?errno:0);
 fresh("after-consume",p); rdfd("held after-consume",fd);
 printf("release=%d\n",sandbox_extension_release(h));
 fresh("after-release",p); rdfd("held after-release",fd);
 return 0;}
