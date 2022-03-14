import os

__all__ = [
    "NEGMAS_RUNALL_TESTS",
    "NEGMAS_ON_GITHUB",
    "NEGMAS_FASTRUN",
    "NEGMAS_RUN_GENIUS",
    "NEGMAS_RUN_TOURNAMENTS",
    "NEGMAS_RUN_TEMP_FAILING",
]

NEGMAS_RUNALL_TESTS = os.environ.get("NEGMAS_RUNALL_TESTS", False)
NEGMAS_ON_GITHUB = os.environ.get("GITHUB_ACTIONS", False)
NEGMAS_FASTRUN = os.environ.get(
    "NEGMAS_FASTRUN", NEGMAS_ON_GITHUB and not NEGMAS_RUNALL_TESTS
)
NEGMAS_RUN_TEMP_FAILING = os.environ.get(
    "NEGMAS_RUN_TEMP_FAILING", not NEGMAS_RUNALL_TESTS
)
NEGMAS_RUN_GENIUS = os.environ.get(
    "NEGMAS_RUN_GENIUS", not NEGMAS_FASTRUN or NEGMAS_RUNALL_TESTS
)
NEGMAS_RUN_TOURNAMENTS = os.environ.get(
    "NEGMAS_RUN_TOURNAMENTS", not NEGMAS_FASTRUN or NEGMAS_RUNALL_TESTS
)
