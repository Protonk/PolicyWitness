#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
int sandbox_check(pid_t pid, const char *operation, int type, ...);
/* usage: chk2 PID OP EXTRAFLAGS_HEX PATH...  (filter type 1 = path, NO_REPORT always) */
int main(int argc, char **argv) {
  if (argc < 5) { fprintf(stderr, "usage\n"); return 2; }
  pid_t pid = (pid_t)atoi(argv[1]);
  int extra = (int)strtol(argv[3], NULL, 16);
  printf("# pid=%d sandboxed_rc=%d flags=0x%08x\n", pid, sandbox_check(pid, NULL, 0), 1 | 0x40000000 | extra);
  for (int i = 4; i < argc; i++) {
    errno = 0;
    int rc = sandbox_check(pid, argv[2], 1 | 0x40000000 | extra, argv[i]);
    int e = errno;
    printf("%s\t%s\trc=%d\terrno=%d\t%s\n", argv[2], argv[i], rc, e, rc==0?"allow":(rc==1?"deny":"error"));
  }
  return 0;
}
