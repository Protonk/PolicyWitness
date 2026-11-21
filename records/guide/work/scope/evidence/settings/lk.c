#include <mach/mach.h>
#include <servers/bootstrap.h>
#include <stdio.h>
int main(int c,char**v){for(int i=1;i<c;i++){mach_port_t p=0;kern_return_t k=bootstrap_look_up(bootstrap_port,v[i],&p);printf("%s kr=%d\n",v[i],k);}return 0;}
