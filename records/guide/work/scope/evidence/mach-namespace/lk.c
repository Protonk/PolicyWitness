#include <stdio.h>
#include <mach/mach.h>
#include <servers/bootstrap.h>
#include <unistd.h>
int sandbox_check(pid_t, const char*, int, ...);
int main(int c,char**v){
 mach_port_t b; task_get_bootstrap_port(mach_task_self(),&b);
 for(int i=1;i<c;i++){
  mach_port_t p=0; kern_return_t k=bootstrap_look_up(b,v[i],&p);
  int sc=sandbox_check(getpid(),"mach-lookup",2|0x40000000,v[i]);
  printf("%s lookup kr=%d (%s) sandbox_check=%d\n",v[i],k,mach_error_string(k),sc);
 }
 return 0;}
