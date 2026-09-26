/* Test-only native validator with explicit query, emission and closure gates.
 * Foundation handles JSON; no PW parser, ABI or classifier is linked here.
 * The caller selects --batch PID, as for the production validator. --gate PATH
 * is accepted by direct controls; the XPC path reads <executable>.gate instead.
 */
#import <Foundation/Foundation.h>
#include <errno.h>
#include <limits.h>
#include <mach-o/dyld.h>
#include <signal.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

extern int sandbox_check(pid_t, const char *, int, ...);

static void require(BOOL ok, NSString *message) {
    if (!ok) { fprintf(stderr, "validator bridge: %s\n", message.UTF8String); exit(70); }
}
static void write_all(int fd, NSData *data) {
    const char *p = data.bytes;
    size_t left = data.length;
    while (left) {
        ssize_t n = write(fd, p, left);
        if (n < 0 && errno == EINTR) continue;
        require(n > 0, @"write failed"); p += n; left -= (size_t)n;
    }
}
static void send_json(int fd, NSDictionary *object) {
    NSError *error = nil;
    NSMutableData *data = [[NSJSONSerialization dataWithJSONObject:object options:NSJSONWritingSortedKeys error:&error] mutableCopy];
    require(data != nil, error.description);
    [data appendBytes:"\n" length:1]; write_all(fd, data);
}
static NSString *gate_path(void) {
    char executable[PATH_MAX]; uint32_t size = sizeof(executable);
    require(_NSGetExecutablePath(executable, &size) == 0, @"executable path too long");
    NSString *path = [[NSString stringWithUTF8String:executable] stringByAppendingString:@".gate"];
    NSString *gate = [NSString stringWithContentsOfFile:path encoding:NSUTF8StringEncoding error:NULL];
    require(gate != nil, @"missing fixture .gate sidecar");
    return [gate stringByTrimmingCharactersInSet:NSCharacterSet.whitespaceAndNewlineCharacterSet];
}
int main(int argc, char **argv) {
    @autoreleasepool {
        signal(SIGALRM, SIG_DFL);
        sigset_t alarm_set; sigemptyset(&alarm_set); sigaddset(&alarm_set, SIGALRM);
        sigprocmask(SIG_UNBLOCK, &alarm_set, NULL);
        alarm(30); signal(SIGPIPE, SIG_IGN);
        require((argc == 3 || argc == 5) && !strcmp(argv[1], "--batch"), @"expected --batch PID [--gate PATH]");
        char *end = NULL; long parsed = strtol(argv[2], &end, 10);
        require(end && !*end && parsed > 0 && parsed <= INT_MAX, @"invalid target PID");
        pid_t target = (pid_t)parsed;
        NSString *gate = argc == 3 ? gate_path() : nil;
        if (argc == 5) {
            require(!strcmp(argv[3], "--gate"), @"expected --gate");
            gate = [NSString stringWithUTF8String:argv[4]];
        }
        // Drain before responding, so fixture gating cannot manufacture EPIPE.
        NSData *input = [NSFileHandle.fileHandleWithStandardInput readDataToEndOfFile];
        NSString *text = [[NSString alloc] initWithData:input encoding:NSUTF8StringEncoding];
        require(text != nil, @"input is not UTF-8");
        NSMutableArray *queries = [NSMutableArray array];
        for (NSString *line in [text componentsSeparatedByString:@"\n"]) {
            if (!line.length) continue;
            id q = [NSJSONSerialization JSONObjectWithData:[line dataUsingEncoding:NSUTF8StringEncoding] options:0 error:NULL];
            require([q isKindOfClass:NSDictionary.class], @"query is not an object");
            for (NSString *key in @[@"step_id", @"operation", @"filter_type"])
                require([q[key] isKindOfClass:NSString.class] && [q[key] length], @"missing query string");
            require([q[@"filter_type"] isEqual:@"PATH"] || [q[@"filter_type"] isEqual:@"NONE"], @"fixture supports PATH and NONE only");
            if ([q[@"filter_type"] isEqual:@"PATH"])
                require([q[@"filter_value"] isKindOfClass:NSString.class], @"PATH requires value");
            [queries addObject:q];
        }
        int fd = socket(AF_UNIX, SOCK_STREAM, 0);
        struct sockaddr_un address = { .sun_family = AF_UNIX };
        require(fd >= 0 && strlen(gate.UTF8String) < sizeof(address.sun_path), @"invalid socket path");
        strcpy(address.sun_path, gate.UTF8String);
        require(connect(fd, (struct sockaddr *)&address, sizeof(address)) == 0, @"gate connect failed");
        send_json(fd, @{@"event":@"ready", @"pid":@(getpid()), @"target_pid":@(target), @"queries":@(queries.count)});
        NSUInteger index = 0; NSDictionary *pending = nil; BOOL closed = NO;
        for (;;) {
            char command; ssize_t n;
            do { n = read(fd, &command, 1); } while (n < 0 && errno == EINTR);
            if (n == 0) { close(STDOUT_FILENO); close(fd); return 0; }
            require(n == 1, @"gate read failed");
            if (command == 'p') {
                send_json(fd, @{@"event":@"held", @"closed":@(closed), @"next":@(index), @"pending":(pending ? @YES : @NO)});
            } else if (command == 'x') {
                close(STDOUT_FILENO); close(fd); return 0;
            } else if (command == 'c') {
                if (!closed) close(STDOUT_FILENO);
                closed = YES; pending = nil;
                send_json(fd, @{@"event":@"closed"});
            } else if (closed) {
                // Closure is terminal even if commands subsequently arrive.
                send_json(fd, @{@"event":@"rejected", @"reason":@"collection_closed"});
            } else if (command == 'q') {
                require(!pending && index < queries.count, @"query out of sequence");
                NSDictionary *q = queries[index];
                int type = [q[@"filter_type"] isEqual:@"PATH"] ? 1 : 0;
                errno = 0;
                int rc = type ? sandbox_check(target, [q[@"operation"] UTF8String], type, [q[@"filter_value"] UTF8String])
                              : sandbox_check(target, [q[@"operation"] UTF8String], 0);
                int err = errno;
                NSMutableDictionary *record = [q mutableCopy];
                if (!type) [record removeObjectForKey:@"filter_value"];
                [record addEntriesFromDictionary:@{@"kind":@"sb_api_validator_verdict", @"schema_version":@1,
                    @"filter_type_id":@(type), @"rc":@(rc), @"errno":@(err),
                    @"outcome":rc == 0 ? @"allow" : rc == 1 && err == 0 ? @"deny" : rc == -1 && err == EINVAL ? @"unsupported_operation" : @"error"}];
                pending = record;
                send_json(fd, @{@"event":@"queried", @"index":@(index), @"record":record});
            } else if (command == 'e') {
                require(pending != nil, @"emit without query");
                send_json(STDOUT_FILENO, pending);
                send_json(fd, @{@"event":@"emitted", @"index":@(index)});
                index++; pending = nil;
            } else require(NO, @"unknown command");
        }
    }
}
