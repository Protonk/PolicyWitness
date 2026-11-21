#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
/* usage: try ACTION PATH... ; ACTION = open_read | access | stat */
#include <sys/stat.h>
int main(int argc, char **argv) {
  for (int i = 2; i < argc; i++) {
    int rc; errno = 0; char extra[128] = "";
    if (!strcmp(argv[1], "open_read")) {
      int fd = open(argv[i], O_RDONLY);
      rc = fd < 0 ? -1 : 0;
      if (fd >= 0) { char c; ssize_t n = read(fd, &c, 1); snprintf(extra, sizeof extra, "read=%zd", n); close(fd); }
    } else if (!strcmp(argv[1], "access")) {
      rc = access(argv[i], R_OK);
    } else if (!strcmp(argv[1], "stat")) {
      struct stat st; rc = stat(argv[i], &st);
    } else { fprintf(stderr, "bad action\n"); return 2; }
    int e = rc ? errno : 0;
    printf("%s\t%s\trc=%d\terrno=%d(%s)\t%s\n", argv[1], argv[i], rc, e, e?strerror(e):"-", extra);
  }
  return 0;
}
