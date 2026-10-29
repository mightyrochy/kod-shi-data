import runpy
import sys
import threading

instrument = sys.argv[1]
sys.argv = sys.argv[1:]
module = runpy.run_path(instrument, run_name='review_import')
sys.setrecursionlimit(100000)
threading.stack_size(16 * 1024 * 1024)
errors = []

def run():
    try:
        module['main']()
    except SystemExit as exc:
        errors.append(exc.code or 0)
    except BaseException:
        import traceback
        traceback.print_exc()
        errors.append(1)

thread = threading.Thread(target=run)
thread.start()
thread.join()
sys.exit(errors[0] if errors else 0)
