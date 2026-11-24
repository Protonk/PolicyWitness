/* Compare three envp arguments to the local spawn API and a subsequent unsetenv.
   The controller invokes this parent with only the harmless marker in environ. */
#include <crt_externs.h>
#include <errno.h>
#include <sandbox.h>
#include <spawn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>
extern char **environ;
static void sample(const char *phase) {
    int n=0;
    for (char **p=*_NSGetEnviron(); p && *p; ++p) n++;
    printf("{\"phase\":\"%s\",\"pid\":%d,\"entries\":%d,\"marker_present\":%s}\n",
           phase,getpid(),n,getenv("PW_FINDINGS_CANARY")?"true":"false");
    fflush(stdout);
}
int main(int argc,char **argv) {
    if(argc!=3) return 2;
    if(!strcmp(argv[1],"child")) {
        sample("entry");
        char *err=NULL;
        if(sandbox_init("(version 1)(allow default)",0,&err)) return 3;
        if(!strcmp(argv[2],"cleared") && unsetenv("PW_FINDINGS_CANARY")) return 4;
        sample("post_apply");
        char byte;
        return read(STDIN_FILENO,&byte,1)==1 ? 0 : 5;
    }
    char *args[]={argv[0],"child",argv[2],NULL};
    char *empty[]={NULL};
    char **envp=!strcmp(argv[2],"nil") ? NULL : !strcmp(argv[2],"empty") ? empty : environ;
    pid_t child;
    int rc=posix_spawn(&child,argv[0],NULL,NULL,args,envp);
    if(rc) return rc;
    int status;
    if(waitpid(child,&status,0)!=child || !WIFEXITED(status)) return 6;
    return WEXITSTATUS(status);
}
