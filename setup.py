from setuptools import setup
import os

# Function to read dependencies from a requirements file.
# Skips blank lines, comments and pip directives (e.g. --extra-index-url),
# which are not valid PEP 508 requirement specifiers for setuptools.
def read_requirements(file_path):
    with open(file_path, "r") as f:
        return [
            line.strip()
            for line in f
            if line.strip()
            and not line.startswith("#")
            and not line.startswith("-")
        ]

# Define paths to requirements files
requirements_dir = "requirements"
core_reqs = read_requirements(os.path.join(requirements_dir, "requirements-core.txt"))
extras_reqs = read_requirements(os.path.join(requirements_dir, "requirements-extras.txt"))
llms_reqs = read_requirements(os.path.join(requirements_dir, "requirements-llms.txt"))
tensorflow_reqs = read_requirements(os.path.join(requirements_dir, "requirements-tensorflow.txt"))
torch_reqs = read_requirements(os.path.join(requirements_dir, "requirements-torch.txt"))
docs_reqs = read_requirements(os.path.join(requirements_dir, "requirements-docs.txt"))

# Combine all extras for the "all" category
all_reqs = extras_reqs + llms_reqs + tensorflow_reqs + torch_reqs

setup(
    install_requires=core_reqs,
    extras_require={
        "extras": extras_reqs,
        "llms": llms_reqs,
        "tensorflow": tensorflow_reqs,
        "torch": torch_reqs,
        "docs": docs_reqs,
        "all": all_reqs
    },
)
