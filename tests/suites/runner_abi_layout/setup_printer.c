#include <stdio.h>
#include "pw_authority_setup.h"
#define H(name, member) printf(#name "=%zu\n",offsetof(pw_authority_setup_t,member))
#define C(name, member) printf(#name "=%zu\n",offsetof(pw_authority_setup_operation_t,member))
int main(void) {
 printf("bytes=%zu\n",sizeof(pw_authority_setup_t));
 printf("capacity=%u\n",PW_AUTHORITY_SETUP_OPERATION_CAPACITY);
 printf("cellBytes=%zu\n",sizeof(pw_authority_setup_operation_t));
 H(cellsOffset,operations);H(decisionOffset,published);H(dispositionOffset,disposition);
 H(primaryOffset,primary_plus_one);H(requiredOffset,required);H(actorOffset,actor_index);
 C(publishedOffset,published);C(kindOffset,native_kind);C(operationOffset,operation);C(stateOffset,state);
 C(rcOffset,native_rc);C(errnoOffset,saved_errno);C(flagsOffset,flags);C(detailOffset,detail);C(reservedOffset,reserved);C(valueOffset,value);
 return 0;
}
