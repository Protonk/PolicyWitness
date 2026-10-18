/* Independent range observation around the production owner's munmap. No
 * intervening allocation may replace a hole before the post-unmap scan. */
#include <errno.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/mman.h>
#include <mach/mach.h>
#include <mach/mach_vm.h>
#include <mach/vm_region.h>

/* calls, address, acquired bytes, rounded bytes, before complete/mapped bytes,
 * native rc/errno, after complete/mapped bytes, requested unmap bytes. */
static int64_t words[11];
static void *acquired_address;
static size_t acquired_length;
void pw_descriptor_map_acquired(void *address, size_t length) {
    acquired_address = address;
    acquired_length = length;
}
static int scan(mach_vm_address_t start, mach_vm_size_t length, int64_t *bytes) {
    mach_vm_address_t cursor = start, end = start + length;
    for (int query = 0; cursor < end && query < 64; query++) {
        mach_vm_address_t region = cursor;
        mach_vm_size_t size = 0;
        vm_region_basic_info_data_64_t info = {0};
        mach_msg_type_number_t count = VM_REGION_BASIC_INFO_COUNT_64;
        mach_port_t object = MACH_PORT_NULL;
        kern_return_t rc = mach_vm_region(mach_task_self(), &region, &size,
            VM_REGION_BASIC_INFO_64, (vm_region_info_t)&info, &count, &object);
        if (MACH_PORT_VALID(object) && mach_port_deallocate(mach_task_self(), object) != KERN_SUCCESS) return 0;
        if (rc == KERN_INVALID_ADDRESS) return 1;
        if (rc != KERN_SUCCESS || count != VM_REGION_BASIC_INFO_COUNT_64 ||
            size == 0 || region > UINT64_MAX - size) return 0;
        if (region >= end) return 1;
        mach_vm_address_t next = region + size;
        if (next <= cursor) return 0;
        mach_vm_address_t lower = region > cursor ? region : cursor;
        mach_vm_address_t upper = next < end ? next : end;
        *bytes += (int64_t)(upper - lower);
        cursor = upper;
    }
    return cursor == end;
}
int pw_descriptor_unmap(void *address, size_t length) {
    int saved = errno;
    long page = sysconf(_SC_PAGESIZE);
    words[0]++;
    words[1] = (int64_t)(uintptr_t)address;
    words[2] = (int64_t)acquired_length;
    words[10] = (int64_t)length;
    if (address != acquired_address || page <= 0 || acquired_length > SIZE_MAX - (size_t)page) return -1;
    size_t extent = ((acquired_length + (size_t)page - 1) / (size_t)page) * (size_t)page;
    words[3] = (int64_t)extent;
    words[4] = scan((mach_vm_address_t)(uintptr_t)address, extent, &words[5]);
    errno = saved;
    int rc = munmap(address, length);
    saved = errno;
    words[6] = rc; words[7] = rc < 0 ? saved : 0;
    words[8] = scan((mach_vm_address_t)(uintptr_t)address, extent, &words[9]);
    errno = saved;
    return rc;
}
int64_t pw_descriptor_map_word(int32_t index) {
    return index >= 0 && index < 11 ? words[index] : -1;
}
