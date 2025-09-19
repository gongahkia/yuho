#!/usr/bin/env python3
"""
Setup script for Yuho v3.0
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="yuho",
    version="3.0.0",
    author="Yuho Contributors",
    description="A domain-specific language for simplifying legal reasoning",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gongahkia/yuho",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Legal Industry",
        "Intended Audience :: Education",
        "Topic :: Software Development :: Compilers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "lark-parser>=1.1.7",
        "click>=8.0.0",
        "colorama>=0.4.6",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
    },
    entry_points={
        "console_scripts": [
            "yuho=yuho_v3.cli.main:cli",
            "yuho-repl=yuho_v3.repl:YuhoREPL",
        ],
    },
    include_package_data=True,
    package_data={
        "yuho_v3": ["grammar.lark"],
    },
)