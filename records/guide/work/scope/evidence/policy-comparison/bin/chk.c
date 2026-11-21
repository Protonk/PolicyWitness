#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
int sandbox_check(pid_t pid, const char *operation, int type, ...);
#define NO_REPORT 0x40000000
/* usage: chk PID OP PATH [PATH...]  (filter type 1 = path) */
int main(int argc, char **argv) {
  if (argc < 4) { fprintf(stderr, "usage: chk PID OP PATH...\n"); return 2; }
  pid_t pid = (pid_t)atoi(argv[1]);
  for (int i = 3; i < argc; i++) {
    errno = 0;
    int rc = sandbox_check(pid, argv[2], 1 | NO_REPORT, argv[i]);
    int e = errno;
    printf("%s\t%s\trc=%d\terrno=%d\t%s\n", argv[2], argv[i], rc, e, rc==0?"allow":(rc==1?"deny":"error"));
  }
  return 0;
}
