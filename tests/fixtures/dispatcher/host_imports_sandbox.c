/* The host-invariance control: links libsandbox and calls sandbox_check, the
 * import the host invariance rule forbids. Never runs. */
#include <stdint.h>
extern int sandbox_check(int, const char *, int, ...);
int main(void) { return sandbox_check(0, "file-read-data", 0); }
