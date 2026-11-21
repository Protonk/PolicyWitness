#include <CoreFoundation/CoreFoundation.h>
#include <stdio.h>
int main(int c,char**v){
 CFStringRef app=CFStringCreateWithCString(0,v[1],kCFStringEncodingUTF8);
 CFStringRef key=CFStringCreateWithCString(0,v[2],kCFStringEncodingUTF8);
 CFPropertyListRef r=CFPreferencesCopyAppValue(key,app);
 if(!r){puts("(null)");return 0;}
 CFStringRef d=CFCopyDescription(r); char b[512]; CFStringGetCString(d,b,512,kCFStringEncodingUTF8); puts(b); return 0;}
