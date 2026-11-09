"""Exact producer admission before semantic reading."""

def is_envelope(document):
    return isinstance(document, dict) and 'data' in document and 'steps' not in document


def _error(label, context, expected):
    value = context.get('contract') if isinstance(context, dict) else None
    if not isinstance(value, str):
        return f'malformed {label}: missing or nonstring contract'
    if expected == 'unbound' or value != expected:
        return f'unsupported {label}: contract {value!r} (expected {expected!r})'
    return None


def version_errors(document, expected_contract):
    if not isinstance(document, dict):
        return ['document is not an object']
    if is_envelope(document):
        error = _error('controller envelope', document.get('build'), expected_contract)
        if error:
            return [error]
        data = document.get('data')
        runner = data.get('runner_result') if isinstance(data, dict) else None
        if runner is None:
            return []
        if not isinstance(runner, dict):
            return ['malformed runner reply: data.runner_result is not an object']
        error = _error('runner response', runner.get('producer'), expected_contract)
    else:
        error = _error('runner response', document.get('producer'), expected_contract)
    return [error] if error else []


def require_supported(document, expected_contract):
    errors = version_errors(document, expected_contract)
    if errors:
        raise ValueError(errors[0])
