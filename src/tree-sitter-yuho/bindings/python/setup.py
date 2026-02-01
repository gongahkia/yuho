from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import subprocess
import os
from pathlib import Path


class TreeSitterBuildExt(build_ext):
    """Custom build extension that generates and compiles tree-sitter parser."""

    def run(self):
        # Get the grammar directory (parent of bindings/python)
        grammar_dir = Path(__file__).parent.parent.parent

        # Generate the parser
        subprocess.run(["tree-sitter", "generate"], cwd=grammar_dir, check=True)

        # Build the shared library
        subprocess.run(["tree-sitter", "build", "--wasm=false"], cwd=grammar_dir, check=True)

        super().run()


setup(
    name="tree-sitter-yuho",
    version="0.1.0",
    description="Tree-sitter grammar for the Yuho legal statute DSL",
    long_description=open(
        Path(__file__).parent.parent.parent / "README.md", encoding="utf-8"
    ).read() if (Path(__file__).parent.parent.parent / "README.md").exists() else "",
    long_description_content_type="text/markdown",
    author="gongahkia",
    url="https://github.com/gongahkia/yuho",
    license="MIT",
    packages=["tree_sitter_yuho"],
    package_dir={"tree_sitter_yuho": "tree_sitter_yuho"},
    python_requires=">=3.8",
    install_requires=[
        "tree-sitter>=0.21.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "tree-sitter-cli>=0.22.0",
        ],
    },
    cmdclass={"build_ext": TreeSitterBuildExt},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Compilers",
        "Topic :: Text Processing :: Linguistic",
    ],
)
