#!/usr/bin/env python3
"""E4 prototype: two readers of the case corpus beside the execution checks.

usage: corpus_readers.py CASES.json CASE_ID

The first reader prints a case's steps as shell lines for documentation. The
second prints the same steps in the card layout. Both take the program name
and the redirection from this script, which is the point of the prototype: a
case holds argument vectors and a saved-output name, not a command line.
"""
import json
import shlex
import sys

PROGRAM = 'policy-witness'


def steps(case):
    return case.get('steps') or [case]


def shell_lines(case):
    lines = []
    for step in steps(case):
        words = [PROGRAM] + [shlex.quote(a.replace('{scratch}/', '')) for a in step['args'] if isinstance(a, str)]
        if step.get('save_stdout'):
            words += ['>', step['save_stdout']]
        lines.append(' '.join(words))
    return lines


def card_lines(case):
    first = steps(case)[0]['args'][0]
    return [first] + ['  ' + line for line in shell_lines(case)]


def main():
    corpus, wanted = json.load(open(sys.argv[1])), sys.argv[2]
    case = next(case for case in corpus['cases'] if case['id'] == wanted)
    print('documentation reader:')
    print('\n'.join('    $ ' + line for line in shell_lines(case)))
    print('card reader:')
    print(''.join(line + '\n' for line in card_lines(case)), end='')
    derived = sorted({a for step in steps(case) for a in step['args'] if isinstance(a, str)})
    print('tokens the case supplies:', derived)
    print('tokens this reader adds:', [PROGRAM, '>'] + sorted({s['save_stdout'] for s in steps(case) if s.get('save_stdout')}))


if __name__ == '__main__':
    main()
