import os


def is_running_in_linux_container():
    """Checks if the script is likely running inside a Linux container (Docker or similar)."""
    return os.path.exists('/.dockerenv') or 'docker' in open('/proc/self/cgroup').read() or 'container' in os.environ or 'DOCKER' in os.environ


if is_running_in_linux_container():
    print("The script is likely running inside a Linux container.")
else:
    print("The script is likely running outside a Linux container.")


def is_running_in_github_actions():
    """Checks if the script is likely running inside a GitHub Actions environment."""
    return 'GITHUB_ACTIONS' in os.environ


if is_running_in_github_actions():
    print("The script is likely running inside a GitHub Actions environment.")
else:
    print("The script is likely running outside a GitHub Actions environment.")
