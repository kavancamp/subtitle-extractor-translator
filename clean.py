#!/usr/bin/env python3
import subprocess
import sys


def run_check(description, command, check_output=False):
    print(f"🔍 Running {description}...")

    try:
        if check_output:
            output = subprocess.check_output(
                command,
                shell=True,
                text=True,
                stderr=subprocess.STDOUT,
            )
            print(output)
        else:
            subprocess.run(
                command,
                shell=True,
                check=True,
                stderr=subprocess.STDOUT,
            )
        print(f"{description} completed successfully.\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}:\n{e.output}")
        sys.exit(1)


# Run isort with profile and exclusions
run_check(
    "isort (import sorting)",
    "isort . --profile=black --line-length=72 --skip='venv' --skip='locales'",
    check_output=True,
)

# Run black to check formatting
run_check(
    "black (formatting)",
    "black . --line-length=72 --extend-exclude=tests ",
    check_output=True,
)

# Run flake8 with exclusions
run_check(
    "flake8 (linting)",
    "flake8 . --max-line-length=100 --ignore=E128,W503 --exclude=venv,tests,locales",
    check_output=True,
)

run_check("pytest (testing)", "pytest", check_output=True)

print("✅ All checks passed. Proceed with commit.")
