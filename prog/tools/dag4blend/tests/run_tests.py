"""Run the Blender verification suite and write a compact machine-readable report."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender', required=True, type=Path)
    parser.add_argument('--jobs', type=int, default=3)
    parser.add_argument('--report', type=Path, default=Path(__file__).parent / 'verification.json')
    args = parser.parse_args()
    tests = sorted(Path(__file__).resolve().parent.glob('test_*.py'))

    def run(path):
        started = time.monotonic()
        try:
            result = subprocess.run([str(args.blender), '--background', '--factory-startup',
                '--python-exit-code', '1', '--python', str(path)], capture_output=True,
                text=True, errors='replace', timeout=600 if path.name == 'test_sample_assets.py' else 120,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            output = result.stdout + result.stderr
            passed = result.returncode == 0 and 'Traceback (most recent call last)' not in output and 'registration error:' not in output
            evidence = [line for line in output.splitlines()
                        if line.startswith(('PASS:', 'SKIP:', 'Blender ')) or 'successfully built to' in line]
            return {'test': path.name, 'passed': passed, 'exit_code': result.returncode,
                    'seconds': round(time.monotonic() - started, 2), 'evidence': evidence,
                    **({'failure_output': output[-12000:]} if not passed else {})}
        except (OSError, subprocess.TimeoutExpired) as error:
            return {'test': path.name, 'passed': False, 'failure_output': str(error)}

    results = []
    with ThreadPoolExecutor(max_workers=max(1, min(args.jobs, 4))) as pool:
        for future in as_completed([pool.submit(run, path) for path in tests]):
            result = future.result()
            results.append(result)
            print(('PASS ' if result['passed'] else 'FAIL ') + result['test'], flush=True)
            if not result['passed']:
                print(result['failure_output'], flush=True)
    results.sort(key=lambda result: result['test'])
    report = {'generated_at_utc': datetime.now(timezone.utc).isoformat(),
              'blender': str(args.blender), 'passed': sum(result['passed'] for result in results),
              'total': len(results), 'results': results}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding='utf8')
    print(f"{report['passed']}/{report['total']} verification scripts passed; report: {args.report}")
    return 0 if report['passed'] == report['total'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
