# Native compilation for PolicyWitness: the C worker and validator, the C shim
# and the two Swift executables that build.sh assembles into the app bundle.
# The compile policy lives here. build.sh maps its two public knobs onto the
# two options in meson.options and otherwise passes nothing; Cargo, bundle
# assembly, signing, evidence and release stay in build.sh.
#
# default_options only initialize a build directory. The assertions below are
# the policy: they refuse a configured directory that departs from it, on
# setup, reconfiguration and compile-triggered regeneration alike.
project('PolicyWitness', 'c',
  meson_version: '>=1.12.1',
  default_options: ['buildtype=plain', 'warning_level=0', 'b_ndebug=false'])

# Fixed native policy, checked as effective settings rather than through the
# buildtype label. Optimization, debug and warning flags are declared per
# target below; argument injection through the *_args options, instrumentation
# and link-time rewriting are refused.
fixed_options = {
  'optimization': 'plain',
  'debug': false,
  'warning_level': '0',
  'werror': false,
  'strip': false,
  'unity': 'off',
  'b_ndebug': 'false',
  'b_lto': false,
  'b_coverage': false,
  'b_pgo': 'off',
  'b_bitcode': false,
  'b_pie': false,
  'b_staticpic': true,
  'b_lundef': true,
  'b_sanitize': 'none',
  'c_std': 'none',
  'c_args': [],
  'c_link_args': [],
}
foreach name, expected : fixed_options
  assert(get_option(name) == expected,
    'fixed native policy: @0@ must be @1@ (got @2@); only inspection and xpc are configurable'.format(
      name, expected, get_option(name)))
endforeach

# Executables are linked without Meson's -dead_strip_dylibs, so the linker
# sees the same library list build.sh passed. Declared per target: a global
# b_asneeded value cannot reach these links.
executable_options = ['b_asneeded=false']

# The two C executables keep the flags build.sh used for them.
c_executable_flags = ['-Wall', '-Wextra', '-O2', '-std=c11']

# Host-side sandbox_check validator; embedded beside the worker in the XPC bundle.
sb_api_validator = executable('sb_api_validator',
  files('controller/tools/sb_api_validator/sb_api_validator.c'),
  c_args: c_executable_flags,
  override_options: executable_options)

# The sandboxed C worker. sandbox_compile_string and sandbox_apply are SPI
# that live in libsandbox, linked dynamically as before. Its included headers
# (the ABI header, worker evidence and profile capture) are tracked through
# the compiler's dependency output, so editing one rebuilds the worker.
pw_probe_runner = executable('pw-probe-runner',
  files('controller/tools/pw_probe_runner/pw_probe_runner.c'),
  c_args: c_executable_flags,
  link_args: ['-lsandbox'],
  override_options: executable_options)

if get_option('xpc')
  # Swift is registered only when the XPC pieces are built, so xpc=false
  # never discovers a Swift compiler.
  add_languages('swift', required: true, native: false)
  foreach name, expected : {'swift_args': [], 'swift_link_args': []}
    assert(get_option(name) == expected,
      'fixed native policy: @0@ must be @1@ (got @2@); only inspection and xpc are configurable'.format(
        name, expected, get_option(name)))
  endforeach

  # Module caches live under the build directory, which is writable wherever
  # Meson can build at all. The inspection option selects the Swift flavour.
  swift_flags = ['-module-cache-path', meson.current_build_dir() / 'swift-module-cache']
  swift_flags += get_option('inspection') ? ['-Onone', '-g'] : ['-O']

  # The C shim the host links. build.sh compiled it with a bare `clang -c`,
  # which buildtype=plain and warning_level=0 reproduce; it is not a product.
  # A Meson Swift target cannot carry C sources, hence the static library.
  cworker_shim = static_library('PWCWorkerShim',
    files('runner/Sources/PWCWorkerShim/PWCWorkerShim.c'))

  # build.sh named this output pw-runner-client, which is not a Swift module
  # identifier, so swiftc fell back to the module name `main`; keep it.
  pw_runner_client = executable('pw-runner-client',
    files('runner/Sources/PWRunnerCore/PWRunnerAPI.swift',
          'runner/Clients/PWRunnerClient/main.swift'),
    swift_module_name: 'main',
    swift_args: swift_flags,
    override_options: executable_options)

  # The XPC host: the core sources in build.sh's order, then the service
  # entry point. The source_drift suite compares this list with the tree.
  pwrunner_core = files(
    'runner/Sources/PWRunnerCore/PWRunnerAPI.swift',
    'runner/Sources/PWRunnerCore/SandboxApply.swift',
    'runner/Sources/PWRunnerCore/ProbeRunner.swift',
    'runner/Sources/PWRunnerCore/PathUtils.swift',
    'runner/Sources/PWRunnerCore/CWorker.swift',
    'runner/Sources/PWRunnerCore/MonotonicDeadline.swift',
    'runner/Sources/PWRunnerCore/ValidatorClient.swift',
    'runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift',
    'runner/Sources/PWRunnerCore/PWRunnerService.swift',
    'runner/Sources/PWRunnerCore/PWRunnerListener.swift',
  )
  pwrunner = executable('PWRunner',
    pwrunner_core, files('runner/Services/PWRunner/main.swift'),
    swift_args: swift_flags,
    link_with: cworker_shim,
    override_options: executable_options)
endif
