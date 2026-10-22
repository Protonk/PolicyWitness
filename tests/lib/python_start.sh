# Sourced by each shell entry point and by testlib.sh; never trust an inherited PW_PYTHON.
# The helpers run on Homebrew's python@3.14 at its keg path, the one interpreter the
# pin below names. pw_python_start checks the path, the keg its real path lies in and
# the version that keg names, refuses any PYTHON* variable the helpers do not own, and
# exports PW_PYTHON with PYTHONCOERCECLOCALE=0 so the interpreter preserves the
# caller's locale environment. pw_python_probe, which the entry points run once,
# starts the interpreter in isolation and compares the version it reports. Helpers
# start with -B -S (and -P for an inline or stdin start), so site-packages, .pth files
# and the working directory are not on their path; -E and -I are not used because they
# ignore PYTHONCOERCECLOCALE. Both functions take explicit arguments only for controls.
source "$(dirname "${BASH_SOURCE[0]}")/sdk_guard.sh" || exit 2
pw_sdk_guard || exit 2
PW_PYTHON_REQUIRED=3.14
PW_PYTHON_PIN=/opt/homebrew/opt/python@3.14/bin/python3.14
PW_PYTHON_CELLAR=/opt/homebrew/Cellar/python@3.14

# pw_python_start [PATH [CELLAR]]: select and check the interpreter without starting it.
# Status 2 and an ERROR line name the refusal: python_environment_set, direct Python
# unavailable, or python_version_mismatch.
pw_python_start() {
  local path="${1:-${PW_PYTHON_PIN}}" cellar="${2:-${PW_PYTHON_CELLAR}}" name directory keg
  for name in "${!PYTHON@}"; do
    case "${name}" in
      PYTHONCOERCECLOCALE|PYTHONDONTWRITEBYTECODE|PYTHONOPTIMIZE) ;;
      *)
        echo "ERROR: python_environment_set: ${name} is set; the helpers take no Python environment (unset it)" >&2
        return 2 ;;
    esac
  done
  if [[ ! -f "${path}" || ! -x "${path}" ]]; then
    echo "ERROR: direct Python unavailable: ${path} is not an executable file (brew install python@3.14)" >&2
    return 2
  fi
  # Resolve the directory physically with builtins: the opt link leads into the Cellar keg.
  if ! directory="$(cd -P "${path%/*}" 2>/dev/null && pwd -P)"; then
    echo "ERROR: direct Python unavailable: the directory of ${path} cannot be resolved" >&2
    return 2
  fi
  if [[ "${directory}" != "${cellar}/"*/* ]]; then
    echo "ERROR: direct Python unavailable: ${path} resolves to ${directory}, not inside ${cellar} (brew install python@3.14)" >&2
    return 2
  fi
  keg="${directory#"${cellar}"/}"
  keg="${keg%%/*}"
  if [[ ! "${keg}" =~ ^([0-9]+\.[0-9]+\.[0-9]+)(_[0-9]+)?$ ]]; then
    echo "ERROR: python_version_mismatch: ${cellar}/${keg} does not name a Python version; ${PW_PYTHON_REQUIRED} is required" >&2
    return 2
  fi
  PW_PYTHON_VERSION="${BASH_REMATCH[1]}"
  if [[ "${PW_PYTHON_VERSION%.*}" != "${PW_PYTHON_REQUIRED}" ]]; then
    echo "ERROR: python_version_mismatch: ${path} is Python ${PW_PYTHON_VERSION} (keg ${keg}); ${PW_PYTHON_REQUIRED} is required" >&2
    return 2
  fi
  PW_PYTHON="${path}"
  PW_PYTHON_REALPATH="${directory}/${path##*/}"
  export PW_PYTHON PW_PYTHON_REALPATH PW_PYTHON_VERSION PYTHONCOERCECLOCALE=0
}

# pw_python_probe [PYTHON]: start the selected interpreter once, isolated, and compare the
# version it reports with the keg's. A probe that cannot run or prints no version is
# direct Python unavailable; a different version is python_version_mismatch.
pw_python_probe() {
  local python="${1:-${PW_PYTHON}}" output status=0
  output="$("${python}" -I -S -B -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>&1)" || status=$?
  if [[ "${status}" -ne 0 ]]; then
    echo "ERROR: direct Python unavailable: ${python} did not report its version (status ${status}): ${output:0:200}" >&2
    return 2
  fi
  if [[ ! "${output}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "ERROR: direct Python unavailable: ${python} printed '${output:0:200}' instead of a version" >&2
    return 2
  fi
  if [[ "${output}" != "${PW_PYTHON_VERSION}" ]]; then
    echo "ERROR: python_version_mismatch: ${python} reports ${output}; its keg names ${PW_PYTHON_VERSION}" >&2
    return 2
  fi
}
