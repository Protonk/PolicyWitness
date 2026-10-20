# Sourced by each shell entry point; never trust an inherited PW_PYTHON.
source "$(dirname "${BASH_SOURCE[0]}")/sdk_guard.sh" || exit 2
pw_sdk_guard || exit 2
# xcode-select normalizes DEVELOPER_DIR without starting a developer-tool shim.
if ! PW_DEVELOPER_DIRECTORY="$(/usr/bin/xcode-select -p)"; then
  echo "ERROR: direct Python unavailable: cannot resolve ${DEVELOPER_DIR+DEVELOPER_DIR=${DEVELOPER_DIR}; }xcode-select's selection" >&2
  exit 2
fi
PW_PYTHON="${PW_DEVELOPER_DIRECTORY}/usr/bin/python3"
if [[ ! -x "${PW_PYTHON}" ]]; then
  echo "ERROR: direct Python unavailable: ${DEVELOPER_DIR+DEVELOPER_DIR=${DEVELOPER_DIR}; }xcode-select selected ${PW_DEVELOPER_DIRECTORY}; no executable usr/bin/python3" >&2
  exit 2
fi
export PW_PYTHON PYTHONCOERCECLOCALE=0
unset PW_DEVELOPER_DIRECTORY
