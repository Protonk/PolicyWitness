#include <stdio.h>
#include <dlfcn.h>
#include <unistd.h>
#include <stdlib.h>
int sandbox_check(pid_t pid, const char *operation, int type, ...);
int main(int argc, char **argv) {
  const char *names[] = {"SANDBOX_CHECK_ALLOW_APPROVAL","SANDBOX_CHECK_CANONICAL","SANDBOX_CHECK_NOFOLLOW","SANDBOX_CHECK_NO_APPROVAL","SANDBOX_CHECK_NO_REPORT","SANDBOX_CHECK_POSIX_READABLE","SANDBOX_CHECK_POSIX_WRITEABLE", 0};
  for (int i = 0; names[i]; i++) {
    int *p = (int*)dlsym(RTLD_DEFAULT, names[i]);
    if (p) printf("%s = 0x%08x\n", names[i], *p); else printf("%s missing\n", names[i]);
  }
  if (argc > 1) { pid_t pid = atoi(argv[1]); printf("pid %d sandboxed rc=%d\n", pid, sandbox_check(pid, NULL, 0)); }
  return 0;
}
