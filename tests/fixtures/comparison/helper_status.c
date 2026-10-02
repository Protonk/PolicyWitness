/* A helper that exits with a fixed status; the matrix's spawn rows spawn copies of it.
 * Compiled by build.sh rather than copied from the system volume: copies of
 * some platform binaries are killed at launch. */
#ifndef PW_EXIT_STATUS
#define PW_EXIT_STATUS 0
#endif
int main(void) { return PW_EXIT_STATUS; }
