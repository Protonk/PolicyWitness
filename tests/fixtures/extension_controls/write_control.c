/* Execute the production fresh-write actions with independently scripted native
 * returns. No sandbox or token is involved; these are syscall/publication controls. */
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

enum { FAIL_OPEN=1, FAIL_OPENED=2, FAIL_TRUNCATE=4, FAIL_TRUNCATED=8,
       FAIL_WRITE=16, SHORT_WRITE=32, FAIL_WRITTEN=64, FAIL_CLOSE=128,
       FAIL_PREOPEN=256, EXISTING_CHILD=512 };
static int faults, creating, stats;
static off_t size_now;
static char calls[32];
static unsigned call_count;
static void called(char value) { assert(call_count < sizeof(calls)-1); calls[call_count++] = value; }
static void metadata(struct stat *out) {
    memset(out, 0, sizeof(*out));
    out->st_dev=3; out->st_ino=42; out->st_mode=S_IFREG|0600;
    out->st_uid=501; out->st_gid=20; out->st_size=size_now;
}
static int controlled_open(const char *path, int flags, ...) {
    assert(!strcmp(path, "/controlled/write")); called('O');
    assert(flags == (O_WRONLY|O_CLOEXEC|(creating ? O_CREAT|O_EXCL : 0)));
    if (creating) {
        va_list ap; va_start(ap, flags); assert(va_arg(ap, int) == 0600); va_end(ap);
    }
    if (faults & (FAIL_OPEN|EXISTING_CHILD)) { errno=(faults & EXISTING_CHILD) ? EEXIST : EACCES; return -1; }
    size_now = creating ? 0 : 9;
    errno=EINVAL; return 17;
}
static int controlled_lstat(const char *path, struct stat *out) {
    assert(!strcmp(path, "/controlled/write")); called('L');
    if (faults & EXISTING_CHILD) { metadata(out); return 0; }
    errno=(faults & FAIL_PREOPEN) ? EACCES : ENOENT; return -1;
}
static int controlled_fstat(int fd, struct stat *out) {
    assert(fd==17); called('S'); stats++;
    int failure=stats==1 ? FAIL_OPENED : !creating && stats==2 ? FAIL_TRUNCATED : FAIL_WRITTEN;
    if (faults & failure) { errno=EIO; return -1; }
    metadata(out); errno=EINVAL; return 0;
}
static int controlled_ftruncate(int fd, off_t length) {
    assert(fd==17 && length==0 && !creating); called('T');
    if (faults & FAIL_TRUNCATE) { errno=EPERM; return -1; }
    size_now=0; errno=EINVAL; return 0;
}
static ssize_t controlled_write(int fd, const void *bytes, size_t count) {
    assert(fd==17 && count==1 && *(const char *)bytes=='x'); called('W');
    if (faults & FAIL_WRITE) { errno=ENOSPC; return -1; }
    if (faults & SHORT_WRITE) { errno=EINVAL; return 0; }
    size_now=1; errno=EINVAL; return 1;
}
static int controlled_close(int fd) {
    assert(fd==17); called('C');
    if (faults & FAIL_CLOSE) { errno=EBADF; return -1; }
    errno=EINVAL; return 0;
}
#define open controlled_open
#define lstat controlled_lstat
#define fstat controlled_fstat
#define ftruncate controlled_ftruncate
#define write controlled_write
#define close controlled_close
#define main included_worker_main
#include "../../../controller/tools/pw_probe_runner/pw_probe_runner.c"
#undef main
#undef open
#undef lstat
#undef fstat
#undef ftruncate
#undef write
#undef close

static void scenario(const char *name, int create, int intervention, int expected_errno) {
    faults=intervention; creating=create; stats=0; call_count=0; size_now=9;
    memset(calls, 0, sizeof(calls));
    pw_shm_slot_t slot={0}; strcpy(slot.target, "/controlled/write");
    attempt_file_write_fresh(&slot, create);
    const pw_fresh_write_t *w=&slot.fresh_write;
    int failure=(intervention & ~(FAIL_PREOPEN)) != 0;
    assert(slot.rc == (failure ? -1 : 0) && slot.errno_val==expected_errno);
    assert(atomic_load(&slot.completed)==0); /* Dispatcher, not helper, publishes. */
    assert(w->preopen_stat.rc == (create ? (faults & EXISTING_CHILD ? 0 : -1) : -2));
    if (create && w->preopen_stat.rc==-1) assert(w->preopen_stat.errno_val == (faults & FAIL_PREOPEN ? EACCES : ENOENT));
    if (faults & (FAIL_OPEN|EXISTING_CHILD)) {
        assert(!strcmp(calls, create ? "LO" : "O"));
        assert(w->open_rc==-1 && w->open_errno==expected_errno);
        assert(w->opened_stat.rc== -2 && w->truncate_rc== -2 && w->truncated_stat.rc== -2);
        assert(w->write_rc== -2 && w->written_stat.rc== -2 && w->close_rc== -2);
    } else {
        assert(!strcmp(calls, create ? "LOSWSC" : faults & FAIL_TRUNCATE ? "OSTSC" : "OSTSWSC"));
        assert(w->open_rc==17 && w->open_errno==0);
        assert(w->opened_stat.rc == (faults & FAIL_OPENED ? -1 : 0));
        if (w->opened_stat.rc==0) assert(w->opened_stat.size==(create ? 0 : 9) && w->opened_stat.inode==42);
        assert(w->truncate_rc == (create ? -2 : faults & FAIL_TRUNCATE ? -1 : 0));
        assert(w->truncated_stat.rc == (create ? -2 : faults & FAIL_TRUNCATED ? -1 : 0));
        if (!create && w->truncated_stat.rc==0) assert(w->truncated_stat.size==(faults & FAIL_TRUNCATE ? 9 : 0));
        if (faults & FAIL_TRUNCATE) { assert(w->write_rc== -2 && w->written_stat.rc== -2); }
        else {
            assert(w->write_rc == (faults & FAIL_WRITE ? -1 : faults & SHORT_WRITE ? 0 : 1));
            assert(w->write_errno == (faults & FAIL_WRITE ? ENOSPC : 0));
            assert(w->written_stat.rc == (faults & FAIL_WRITTEN ? -1 : 0));
            if (w->written_stat.rc==0) assert(w->written_stat.size == (faults & (FAIL_WRITE|SHORT_WRITE) ? 0 : 1));
        }
        assert(w->close_rc == (faults & FAIL_CLOSE ? -1 : 0));
        assert(w->close_errno == (faults & FAIL_CLOSE ? EBADF : 0));
    }
    printf("%s: native sequence and separate observations passed\n", name);
}
int main(void) {
    scenario("existing_success",0,0,0); scenario("create_success",1,0,0);
    scenario("open_failure",0,FAIL_OPEN,EACCES); scenario("create_open_failure",1,FAIL_OPEN,EACCES);
    scenario("opened_stat_failure",0,FAIL_OPENED,EIO);
    scenario("truncate_failure",0,FAIL_TRUNCATE,EPERM);
    scenario("truncated_stat_failure",0,FAIL_TRUNCATED,EIO);
    scenario("write_failure",0,FAIL_WRITE,ENOSPC); scenario("short_write",0,SHORT_WRITE,0);
    scenario("written_stat_failure",0,FAIL_WRITTEN,EIO); scenario("close_failure",0,FAIL_CLOSE,EBADF);
    scenario("combined_failures",0,FAIL_OPENED|FAIL_WRITE|FAIL_CLOSE,EIO);
    scenario("existing_child",1,EXISTING_CHILD,EEXIST);
    scenario("preopen_diagnostic",1,FAIL_PREOPEN,0);
    scenario("create_short_write",1,SHORT_WRITE,0);
    puts("all 15 production fresh-write controls passed");
    return 0;
}
