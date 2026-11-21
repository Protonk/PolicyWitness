#include <stdio.h>
#include <string.h>
#include <mach/mach.h>
#include <servers/bootstrap.h>
int main(int c,char**v){ mach_port_t b; task_get_bootstrap_port(mach_task_self(),&b); char l[512];
 while(fgets(l,512,stdin)){ l[strcspn(l,"\n")]=0; mach_port_t p=0; kern_return_t k=bootstrap_look_up(b,l,&p); printf("%d %s\n",k,l);} return 0;}
