import sys
sys.path.insert(0, ".")

from tests.random_generator import run_random_tests

print("Testing random generator...")
report = run_random_tests(3)
print("Results:", report["summary"])
print("Tests run!")