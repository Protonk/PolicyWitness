"""Version gates shared by semantic readers of envelopes and runner replies."""
import contract


def _version_error(label, value, expected):
    if type(value) is not int:
        return f'malformed {label}: schema_version {value!r} is not an integer'
    if value != expected:
        return f'unsupported {label}: schema_version {value} (this reader accepts {expected})'
    return None


def is_envelope(document):
    """A controller envelope carries `kind` and `data`; a bare reply carries `steps`."""
    return isinstance(document, dict) and 'data' in document and 'steps' not in document


def version_errors(document):
    """One error for the first unsupported or malformed version, else []."""
    if not isinstance(document, dict):
        return ['document is not an object']
    if is_envelope(document):
        error = _version_error('controller envelope', document.get('schema_version'), contract.CONTROLLER_ENVELOPE)
        if error:
            return [error]
        data = document.get('data')
        runner = data.get('runner_result') if isinstance(data, dict) else None
        if runner is None:
            return []
        if not isinstance(runner, dict):
            return ['malformed runner reply: data.runner_result is not an object']
        error = _version_error('runner response', runner.get('schema_version'), contract.RESPONSE_SCHEMA)
        return [error] if error else []
    error = _version_error('runner response', document.get('schema_version'), contract.RESPONSE_SCHEMA)
    return [error] if error else []


def require_supported(document):
    errors = version_errors(document)
    if errors:
        raise ValueError(errors[0])
