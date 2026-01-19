import os
import sys
import subprocess
import importlib

# Configure environment for tests
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')
os.environ.setdefault('PRESENCE_BACKEND', 'redis')
os.environ.setdefault('PYTHONPATH', '.')

print('ENV REDIS_URL=', os.environ.get('REDIS_URL'))
print('ENV PRESENCE_BACKEND=', os.environ.get('PRESENCE_BACKEND'))

# Run pytest full suite
print('\n=== Running pytest full suite ===')
ret = subprocess.run([sys.executable, '-m', 'pytest', '-q'], cwd=os.path.dirname(__file__) + '..')
print('pytest exit code:', ret.returncode)

# Run Redis-specific test
print('\n=== Running Redis-specific test ===')
ret2 = subprocess.run([sys.executable, '-m', 'pytest', 'tests/test_presence_redis.py', '-q'], cwd=os.path.dirname(__file__) + '..')
print('redis test exit code:', ret2.returncode)

# Run internal comprehensive script
print('\n=== Running comprehensive_internal.py ===')
try:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    import scripts.comprehensive_internal as ci
    ci.run_internal_checks()
    print('comprehensive_internal completed successfully')
except Exception as e:
    print('comprehensive_internal failed:', e)

# Exit with pytest's exit code if non-zero
if ret.returncode != 0:
    sys.exit(ret.returncode)
sys.exit(0)
