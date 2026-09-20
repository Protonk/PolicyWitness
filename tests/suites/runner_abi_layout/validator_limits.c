/* Compile the same batch parser used by the shipped validator. */
#define main pw_validator_main
#include "../../../controller/tools/sb_api_validator/sb_api_validator.c"
#undef main

int main(int argc, char **argv) {
    if (argc == 1) {
        printf("validator_query_payload=%d\n", LINE_MAX_BYTES - 2);
        return 0;
    }
    return pw_validator_main(argc, argv);
}
