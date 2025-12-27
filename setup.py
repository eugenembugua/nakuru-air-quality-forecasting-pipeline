from setuptools import find_packages, setup
from typing import List

def get_requirement() -> List[str]:
    requirements_lst: List[str] = []
    try:
        with open("requirements.txt", "r") as file:
            lines = file.readlines()
            for line in lines:
                requirement = line.strip()
                # Ignore empty lines and the editable install flag
                if requirement and requirement != "-e .":
                    requirements_lst.append(requirement)
    except FileNotFoundError:
        print("requirements.txt file not found")

    return requirements_lst

setup(
    name="Nakuru-Air-Quality",
    version="0.0.1",
    author="Eugene Githinji Mbugua",
    author_email="eugenembugua02@gmail.com",
    packages=find_packages(),
    install_requires=get_requirement()
)