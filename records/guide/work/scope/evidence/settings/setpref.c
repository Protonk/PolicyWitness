#include <CoreFoundation/CoreFoundation.h>
#include <stdio.h>
#include <string.h>
int main(int argc,char**argv){
 // argv[1]=abs plist path (without .plist), argv[2]=value, argv[3]= "sync"/"nosync"
 CFStringRef app=CFStringCreateWithCString(0,argv[1],kCFStringEncodingUTF8);
 CFStringRef key=CFSTR("PWTestKey");
 CFStringRef val=CFStringCreateWithCString(0,argv[2],kCFStringEncodingUTF8);
 CFPreferencesSetValue(key,val,app,kCFPreferencesCurrentUser,kCFPreferencesAnyHost);
 Boolean ok=1;
 if(strcmp(argv[3],"sync")==0) ok=CFPreferencesSynchronize(app,kCFPreferencesCurrentUser,kCFPreferencesAnyHost);
 CFPropertyListRef back=CFPreferencesCopyValue(key,app,kCFPreferencesCurrentUser,kCFPreferencesAnyHost);
 char b[256]="(null)"; if(back&&CFGetTypeID(back)==CFStringGetTypeID()) CFStringGetCString(back,b,256,kCFStringEncodingUTF8);
 printf("sync_ok=%d readback=%s\n",ok,b);
 return 0;}
