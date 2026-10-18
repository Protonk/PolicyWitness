#include <fcntl.h>
#include <sys/mman.h>
int pw_setup_shm_open_existing(const char *name) {
    return shm_open(name, O_RDWR, 0);
}
