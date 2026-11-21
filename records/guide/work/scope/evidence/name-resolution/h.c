#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
int main(int c,char**v){
 const char*mode=v[1]; int port=atoi(v[2]);
 if(!strcmp(mode,"name")){
  struct addrinfo h={0},*r; h.ai_socktype=SOCK_STREAM; char p[8]; snprintf(p,8,"%d",port);
  int g=getaddrinfo(v[3],p,&h,&r);
  printf("getaddrinfo rc=%d (%s)\n",g,g?gai_strerror(g):"ok"); if(g) return 3;
  int n=0; for(struct addrinfo*a=r;a;a=a->ai_next){
   int s=socket(a->ai_family,SOCK_STREAM,0); int rc=connect(s,a->ai_addr,a->ai_addrlen);
   printf("fam=%d connect rc=%d errno=%d %s\n",a->ai_family,rc,rc?errno:0,rc?strerror(errno):""); close(s); n++; if(!rc) return 0;}
  return 4;}
 int fam=!strcmp(mode,"c6")||!strcmp(mode,"b6")?AF_INET6:AF_INET;
 int s=socket(fam,SOCK_STREAM,0); printf("socket rc=%d errno=%d\n",s,s<0?errno:0); if(s<0)return 2;
 struct sockaddr_storage ss={0}; socklen_t l;
 if(fam==AF_INET){struct sockaddr_in*a=(void*)&ss;a->sin_family=AF_INET;a->sin_port=htons(port);inet_pton(AF_INET,"127.0.0.1",&a->sin_addr);l=sizeof*a;}
 else{struct sockaddr_in6*a=(void*)&ss;a->sin6_family=AF_INET6;a->sin6_port=htons(port);inet_pton(AF_INET6,"::1",&a->sin6_addr);l=sizeof*a;}
 int rc;
 if(mode[0]=='b'){rc=bind(s,(void*)&ss,l);printf("bind rc=%d errno=%d %s\n",rc,rc?errno:0,rc?strerror(errno):"");if(!rc){rc=listen(s,1);printf("listen rc=%d errno=%d\n",rc,rc?errno:0);}}
 else{rc=connect(s,(void*)&ss,l);printf("connect rc=%d errno=%d %s\n",rc,rc?errno:0,rc?strerror(errno):"");}
 return rc?1:0;}
