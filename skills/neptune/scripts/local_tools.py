"""Small local check/log/usage tools. No model calls or task database."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import uuid


def save_details(value):
    folder = Path.home() / '.local/state/neptune/details'
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = folder / (uuid.uuid4().hex + '.json')
    path.touch(mode=0o600, exist_ok=False)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    return str(path)


def excerpt(text, offset=0, limit=2000):
    if offset < 0 or not 1 <= limit <= 12000:
        raise ValueError('Use offset >= 0 and limit 1..12000 characters')
    end = min(offset + limit, len(text))
    return {'text': text[offset:end], 'offset': offset, 'total_characters': len(text),
            'shortened': offset > 0 or end < len(text),
            'next_offset': end if end < len(text) else None}


def details(path, field=None, offset=0, limit=2000):
    path = Path(path).resolve()
    root = (Path.home() / '.local/state/neptune/details').resolve()
    if not path.is_relative_to(root) or path.suffix != '.json':
        raise ValueError('Use a details_path returned by NEPTUNE')
    value = json.loads(path.read_text(encoding='utf-8'))
    if field:
        value = value[field]
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
    return {'details_path': str(path), **excerpt(text, offset, limit)}


def run_check(argv, cwd=None, timeout=120):
    if not argv or any(not isinstance(arg, str) for arg in argv):
        raise ValueError('Provide an executable and arguments after --')
    if timeout <= 0:
        raise ValueError('Timeout must be positive')
    result = {'argv': argv, 'cwd': str(Path(cwd or Path.cwd()).resolve()), 'timed_out': False}
    try:
        run = subprocess.run(argv, cwd=result['cwd'], capture_output=True, text=True,
                             encoding='utf-8', errors='replace', timeout=timeout)
        result.update(exit_code=run.returncode, stdout=run.stdout, stderr=run.stderr)
    except subprocess.TimeoutExpired as error:
        def decode(text):
            return text.decode('utf-8', errors='replace') if isinstance(text, bytes) else text or ''
        result.update(exit_code=None, timed_out=True, stdout=decode(error.stdout), stderr=decode(error.stderr))
    except OSError as error:
        result.update(exit_code=None, launch_error=str(error), stdout='', stderr=str(error))
    path = save_details(result)
    # Keep separate excerpts so verbose stdout cannot bury a short stderr failure.
    preview = {stream: excerpt(result[stream], offset=max(0,len(result[stream])-1000), limit=1000)
               for stream in ('stdout', 'stderr')}
    return {'exit_code': result['exit_code'], 'timed_out': result['timed_out'],
            'passed': result['exit_code'] == 0, 'details_path': path, **preview}


def usage(logs):
    """Read explicit native Codex JSONL logs; never sum cumulative events twice."""
    reports = []
    for log in logs:
        latest = None
        rates = None
        with Path(log).open(encoding='utf-8') as stream:
            for line in stream:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(event, dict): continue
                payload = event.get('payload', {})
                if event.get('type') != 'event_msg' or not isinstance(payload, dict) or payload.get('type') != 'token_count':
                    continue
                info = payload.get('info') or {}
                totals = info.get('total_token_usage') if isinstance(info, dict) else None
                if isinstance(totals, dict):
                    latest = {k: v for k, v in totals.items() if k in
                              ('input_tokens', 'cached_input_tokens', 'output_tokens', 'reasoning_output_tokens', 'total_tokens')
                              and type(v) is int and v >= 0}
                if isinstance(payload.get('rate_limits'), dict):
                    rates = payload['rate_limits']
        reports.append({'log': str(Path(log).resolve()), 'native_token_usage': latest,
                        'native_rate_limits': rates,
                        'subscription_savings': 'Not established; token counts are not subscription allowance.'})
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    check = sub.add_parser('check')
    check.add_argument('--cwd'); check.add_argument('--timeout', type=float, default=120)
    check.add_argument('argv', nargs=argparse.REMAINDER)
    read = sub.add_parser('details'); read.add_argument('path'); read.add_argument('--field')
    read.add_argument('--offset', type=int, default=0); read.add_argument('--limit', type=int, default=2000)
    measure = sub.add_parser('usage'); measure.add_argument('logs', nargs='+')
    args = parser.parse_args()
    try:
        if args.command == 'check':
            argv = args.argv[1:] if args.argv[:1] == ['--'] else args.argv
            value = run_check(argv, args.cwd, args.timeout)
        elif args.command == 'details':
            value = details(args.path, args.field, args.offset, args.limit)
        else:
            value = usage(args.logs)
        print(json.dumps(value, ensure_ascii=False, separators=(',', ':')))
        if args.command == 'check' and not value['passed']:
            sys.exit(value['exit_code'] if isinstance(value['exit_code'], int) and 1 <= value['exit_code'] <= 125 else 1)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(2, 'NEPTUNE: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
