"""oowlet-recommend-uc: recommendation engine for content and people."""

from setuptools import find_packages, setup

setup(
    name="oowlet-recommend-uc",
    version="0.1.0",
    description="Content and people recommendations for the Oowlet platform",
    packages=find_packages(include=["ruc", "ruc.*", "oowlet", "oowlet.*"]),
    python_requires=">=3.10",
    install_requires=[line.split("#")[0].strip() for line in open("requirements.txt", encoding="utf-8")
                      if line.split("#")[0].strip()],
    entry_points={"console_scripts": ["oowlet-recommend-uc=ruc.cli:main"]},
)
