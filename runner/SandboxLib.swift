import Darwin

// Minimal dynamic loader for libsandbox. We resolve each symbol explicitly so
// inspection shows exactly which APIs we use.
struct SandboxLib {
    let handle: UnsafeMutableRawPointer

    typealias SandboxParams = UnsafeMutableRawPointer
    typealias SandboxProfile = UnsafeMutableRawPointer

    typealias CreateParamsFn = @convention(c) () -> SandboxParams?
    typealias FreeParamsFn = @convention(c) (SandboxParams?) -> Void
    typealias SetParamFn = @convention(c) (SandboxParams?, UnsafePointer<CChar>?, UnsafePointer<CChar>?) -> Int32

    typealias CompileStringFn = @convention(c) (UnsafePointer<CChar>?, SandboxParams?, UnsafeMutablePointer<UnsafeMutablePointer<CChar>?>?) -> SandboxProfile?
    typealias FreeProfileFn = @convention(c) (SandboxProfile?) -> Void
    typealias FreeErrorFn = @convention(c) (UnsafeMutablePointer<CChar>?) -> Void

    typealias ApplyFn = @convention(c) (SandboxProfile?) -> Int32

    let createParams: CreateParamsFn
    let freeParams: FreeParamsFn
    let setParam: SetParamFn
    let compileString: CompileStringFn
    let freeProfile: FreeProfileFn
    let freeError: FreeErrorFn
    let apply: ApplyFn

    struct LoadError: Error, CustomStringConvertible {
        var message: String

        var description: String { message }
    }

    static func load() -> Result<SandboxLib, LoadError> {
        let handle: UnsafeMutableRawPointer
        switch loadHandle() {
        case .success(let value):
            handle = value
        case .failure(let err):
            return .failure(err)
        }

        let createParams: CreateParamsFn
        switch loadCreateParams(handle: handle) {
        case .success(let value):
            createParams = value
        case .failure(let err):
            return .failure(err)
        }

        let freeParams: FreeParamsFn
        switch loadFreeParams(handle: handle) {
        case .success(let value):
            freeParams = value
        case .failure(let err):
            return .failure(err)
        }

        let setParam: SetParamFn
        switch loadSetParam(handle: handle) {
        case .success(let value):
            setParam = value
        case .failure(let err):
            return .failure(err)
        }

        let compileString: CompileStringFn
        switch loadCompileString(handle: handle) {
        case .success(let value):
            compileString = value
        case .failure(let err):
            return .failure(err)
        }

        let freeProfile: FreeProfileFn
        switch loadFreeProfile(handle: handle) {
        case .success(let value):
            freeProfile = value
        case .failure(let err):
            return .failure(err)
        }

        let freeError: FreeErrorFn
        switch loadFreeError(handle: handle) {
        case .success(let value):
            freeError = value
        case .failure(let err):
            return .failure(err)
        }

        let apply: ApplyFn
        switch loadApply(handle: handle) {
        case .success(let value):
            apply = value
        case .failure(let err):
            return .failure(err)
        }

        return .success(
            SandboxLib(
                handle: handle,
                createParams: createParams,
                freeParams: freeParams,
                setParam: setParam,
                compileString: compileString,
                freeProfile: freeProfile,
                freeError: freeError,
                apply: apply
            )
        )
    }

    private static func loadHandle() -> Result<UnsafeMutableRawPointer, LoadError> {
        guard let handle = dlopen("/usr/lib/libsandbox.dylib", RTLD_NOW) else {
            return .failure(LoadError(message: "dlopen(/usr/lib/libsandbox.dylib) failed"))
        }
        return .success(handle)
    }

    private static func loadSymbol<T>(
        handle: UnsafeMutableRawPointer,
        name: String,
        type: T.Type
    ) -> Result<T, LoadError> {
        let ptr = name.withCString { dlsym(handle, $0) }
        guard let ptr else {
            return .failure(LoadError(message: "dlsym(\(name)) failed"))
        }
        return .success(unsafeBitCast(ptr, to: T.self))
    }

    private static func loadCreateParams(handle: UnsafeMutableRawPointer) -> Result<CreateParamsFn, LoadError> {
        loadSymbol(handle: handle, name: "sandbox_create_params", type: CreateParamsFn.self)
    }

    private static func loadFreeParams(handle: UnsafeMutableRawPointer) -> Result<FreeParamsFn, LoadError> {
        loadSymbol(handle: handle, name: "sandbox_free_params", type: FreeParamsFn.self)
    }

    private static func loadSetParam(handle: UnsafeMutableRawPointer) -> Result<SetParamFn, LoadError> {
        loadSymbol(handle: handle, name: "sandbox_set_param", type: SetParamFn.self)
    }

    private static func loadCompileString(handle: UnsafeMutableRawPointer) -> Result<CompileStringFn, LoadError> {
        loadSymbol(handle: handle, name: "sandbox_compile_string", type: CompileStringFn.self)
    }

    private static func loadFreeProfile(handle: UnsafeMutableRawPointer) -> Result<FreeProfileFn, LoadError> {
        loadSymbol(handle: handle, name: "sandbox_free_profile", type: FreeProfileFn.self)
    }

    private static func loadFreeError(handle: UnsafeMutableRawPointer) -> Result<FreeErrorFn, LoadError> {
        loadSymbol(handle: handle, name: "sandbox_free_error", type: FreeErrorFn.self)
    }

    private static func loadApply(handle: UnsafeMutableRawPointer) -> Result<ApplyFn, LoadError> {
        loadSymbol(handle: handle, name: "sandbox_apply", type: ApplyFn.self)
    }
}
