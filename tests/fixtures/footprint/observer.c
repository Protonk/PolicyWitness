/* Test-only persistent libproc meter. One JSON response per bounded command. */
#include <errno.h>
#include <inttypes.h>
#include <libproc.h>
#include <mach/mach_time.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <unistd.h>

static mach_timebase_info_data_t tb;
static uint64_t ns(uint64_t ticks) { return (uint64_t)((__uint128_t)ticks * tb.numer / tb.denom); }
static uint64_t now(void) { return ns(mach_continuous_time()); }
static void quoted(const char *s) {
    putchar('"');
    for (const unsigned char *p = (const unsigned char *)s; *p; p++) {
        if (*p == '"' || *p == '\\') printf("\\%c", *p);
        else if (*p < 32 || *p >= 127) printf("\\u%04x", *p);
        else putchar(*p);
    }
    putchar('"');
}
struct call { uint64_t begin, end; int rc, error; };
static void receipt(const struct call *c) {
    printf("{\"begin_ns\":%" PRIu64 ",\"end_ns\":%" PRIu64 ",\"rc\":%d,\"errno\":%d}", c->begin,c->end,c->rc,c->error);
}
static struct call identity(pid_t pid, struct proc_bsdinfo *b) {
    struct call c = {.begin=now()}; errno=0;
    c.rc=proc_pidinfo(pid,PROC_PIDTBSDINFO,0,b,sizeof(*b)); c.error=errno; c.end=now(); return c;
}
static void generation(pid_t pid,const struct proc_bsdinfo *b,int valid) {
    if (!valid) { printf("null"); return; }
    printf("{\"pid\":%d,\"ppid\":%u,\"start_sec\":%" PRIu64 ",\"start_usec\":%" PRIu64 "}",pid,b->pbi_ppid,b->pbi_start_tvsec,b->pbi_start_tvusec);
}
static void sample(pid_t pid) {
    struct proc_bsdinfo a={0},b={0}; struct rusage_info_v0 r={0}; char path[PROC_PIDPATHINFO_MAXSIZE]={0};
    uint64_t begin=now(); struct call ca=identity(pid,&a),cr={.begin=now()}; errno=0;
    cr.rc=proc_pid_rusage(pid,RUSAGE_INFO_V0,(rusage_info_t *)&r);cr.error=errno;cr.end=now();
    struct call cp={.begin=now()};errno=0;cp.rc=proc_pidpath(pid,path,sizeof(path));cp.error=errno;cp.end=now();
    struct call cb=identity(pid,&b);
    int av=ca.rc==(int)sizeof(a),bv=cb.rc==(int)sizeof(b);
    int same=av&&bv&&a.pbi_start_tvsec==b.pbi_start_tvsec&&a.pbi_start_tvusec==b.pbi_start_tvusec;
    int ok=same&&cr.rc==0&&cp.rc>0;
    printf("{\"pid\":%d,\"begin_ns\":%" PRIu64 ",\"end_ns\":%" PRIu64 ",\"status\":\"%s\",\"generation_before\":",pid,begin,now(),ok?"ok":av&&bv&&!same?"generation_changed":"error");
    generation(pid,&a,av);printf(",\"generation_after\":");generation(pid,&b,bv);
    printf(",\"path\":");if(cp.rc>0)quoted(path);else printf("null");
    printf(",\"calls\":{\"generation_before\":");receipt(&ca);printf(",\"rusage\":");receipt(&cr);printf(",\"path\":");receipt(&cp);printf(",\"generation_after\":");receipt(&cb);printf("}");
    printf(",\"timebase_numer\":%u,\"timebase_denom\":%u,\"raw_cpu_unit\":\"mach_absolute_time_ticks\"",tb.numer,tb.denom);
    if(ok) printf(",\"user_ticks\":%" PRIu64 ",\"system_ticks\":%" PRIu64 ",\"user_ns\":%" PRIu64 ",\"system_ns\":%" PRIu64 ",\"resident_bytes\":%" PRIu64 ",\"phys_footprint_bytes\":%" PRIu64,r.ri_user_time,r.ri_system_time,ns(r.ri_user_time),ns(r.ri_system_time),r.ri_resident_size,r.ri_phys_footprint);
    else printf(",\"user_ticks\":null,\"system_ticks\":null,\"user_ns\":null,\"system_ns\":null,\"resident_bytes\":null,\"phys_footprint_bytes\":null");
    printf("}");
}
static int child(const char *mode) {
    volatile unsigned char *allocation=NULL;size_t size=0; volatile uint64_t work=0;
    printf("{\"ack\":\"ready\",\"pid\":%d,\"mode\":",getpid());quoted(mode);printf("}\n");fflush(stdout);
    for(;;) {
        struct pollfd fd={.fd=STDIN_FILENO,.events=POLLIN};
        int rc=poll(&fd,1,strcmp(mode,"busy")==0?0:-1);
        if(rc<0) return 2;
        if(rc>0) {
            char line[128];if(!fgets(line,sizeof(line),stdin))break;
            if(!strcmp(line,"quit\n"))break;
            if(!strcmp(line,"cpu\n")) {
                struct rusage usage={0};uint64_t begin=now();errno=0;
                int result=getrusage(RUSAGE_SELF,&usage),error=errno;uint64_t end=now();
                printf("{\"ack\":\"cpu\",\"source\":\"getrusage_RUSAGE_SELF_timeval\",\"rc\":%d,\"errno\":%d,\"begin_ns\":%" PRIu64 ",\"end_ns\":%" PRIu64 ",\"user_sec\":%lld,\"user_usec\":%d,\"system_sec\":%lld,\"system_usec\":%d}\n",result,error,begin,end,(long long)usage.ru_utime.tv_sec,(int)usage.ru_utime.tv_usec,(long long)usage.ru_stime.tv_sec,(int)usage.ru_stime.tv_usec);fflush(stdout);
                continue;
            }
            unsigned long long bytes=0;
            if(sscanf(line,"touch %llu",&bytes)!=1||bytes==0||bytes>268435456||allocation) return 3;
            size=(size_t)bytes;allocation=malloc(size);if(!allocation)return 4;
            for(size_t i=0;i<size;i+=4096)allocation[i]=1;
            allocation[size-1]=1;
            printf("{\"ack\":\"touched\",\"bytes\":%zu}\n",size);fflush(stdout);
        }
        if(!strcmp(mode,"busy"))for(unsigned i=0;i<10000;i++)work++;
    }
    free((void *)allocation);return work==UINT64_MAX?5:0;
}
int main(int argc,char **argv) {
    if(mach_timebase_info(&tb)!=KERN_SUCCESS)return 1;
    if(argc==3&&!strcmp(argv[1],"--child")) {
        if(strcmp(argv[2],"busy")&&strcmp(argv[2],"sleep")&&strcmp(argv[2],"allocation"))return 2;
        return child(argv[2]);
    }
    char line[4096];
    while(fgets(line,sizeof(line),stdin)) {
        if(!strcmp(line,"quit\n"))break;
        if(!strcmp(line,"clock\n")) {
            uint64_t begin=now(),uptime=ns(mach_absolute_time()),end=now();
            printf("{\"version\":1,\"clock\":\"mach_continuous_time_ns\",\"begin_ns\":%" PRIu64 ",\"continuous_ns\":%" PRIu64 ",\"uptime_ns\":%" PRIu64 ",\"end_ns\":%" PRIu64 "}\n",begin,end,uptime,end);
        } else if(!strncmp(line,"sample ",7)) {
            pid_t pids[64];size_t count=0;char *save=NULL,*token=strtok_r(line+7," \n",&save);
            while(token) { char *end;long p=strtol(token,&end,10);if(*end||p<=0||p>INT32_MAX||count==64)return 3;pids[count++]=(pid_t)p;token=strtok_r(NULL," \n",&save); }
            if(!count)return 3;
            uint64_t begin=now();printf("{\"version\":1,\"clock\":\"mach_continuous_time_ns\",\"cpu_unit\":\"ns\",\"memory_unit\":\"bytes\",\"begin_ns\":%" PRIu64 ",\"samples\":[",begin);
            for(size_t i=0;i<count;i++){if(i)putchar(',');sample(pids[i]);}
            printf("],\"end_ns\":%" PRIu64 "}\n",now());
        } else return 3;
        fflush(stdout);
    }
    return 0;
}
