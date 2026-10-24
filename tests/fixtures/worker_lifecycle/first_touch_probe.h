/*
 * first_touch_probe.h — the probe word shared by the C-worker harness and the
 * first-touch control (first_touch_control.c). The offset is page-aligned at
 * 16 KiB and its whole page lies inside the compiled-profile capture bytes,
 * which the worker writes only when a capture is requested, so under the
 * harness's skip-touch scenarios no process backs that page before the
 * worker's post-application store. Both sides include this header; the
 * harness also checks the placement at run time against its page size.
 */
#ifndef PW_FIRST_TOUCH_PROBE_H
#define PW_FIRST_TOUCH_PROBE_H

#include <stddef.h>
#include <stdint.h>

#include "pw_probe_runner_abi.h"

#define PW_FIRST_TOUCH_PAGE_BYTES 16384u
/* Page 200 of the 225-page production region. */
#define PW_FIRST_TOUCH_PROBE_OFFSET ((size_t)200u * PW_FIRST_TOUCH_PAGE_BYTES)
#define PW_FIRST_TOUCH_PATTERN 0x4650573146545031ull

#define PW_FIRST_TOUCH_CAPTURE_BYTES_START                                     \
    ((size_t)PW_SHM_HEADER_BYTES + (size_t)PW_SHM_MAX_STEPS * PW_SHM_SLOT_BYTES \
     + (size_t)PW_SHM_MAX_PARAMS * PW_SHM_PARAM_BYTES + PW_SHM_CAPTURE_HEADER_BYTES)
#define PW_FIRST_TOUCH_CAPTURE_BYTES_END (PW_FIRST_TOUCH_CAPTURE_BYTES_START + PW_SHM_CAPTURE_BYTES)

_Static_assert(PW_FIRST_TOUCH_PROBE_OFFSET % PW_FIRST_TOUCH_PAGE_BYTES == 0, "probe word must start a page");
_Static_assert(PW_FIRST_TOUCH_PROBE_OFFSET >= PW_FIRST_TOUCH_CAPTURE_BYTES_START,
               "probe page must lie inside the capture bytes");
_Static_assert(PW_FIRST_TOUCH_PROBE_OFFSET + PW_FIRST_TOUCH_PAGE_BYTES <= PW_FIRST_TOUCH_CAPTURE_BYTES_END,
               "probe page must end inside the capture bytes");

#endif
