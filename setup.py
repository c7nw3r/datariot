import os
# read the contents of your README file
from pathlib import Path

import pkg_resources
from setuptools import find_packages, setup

long_description = Path(__file__).with_name("README.md").read_text()

version = "0.3.8"
setup(
    name='datariot',
    packages=find_packages(exclude=("test")),
    version=version,
    license='Apache Software License',
    description='tbd',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='c7nw3r',
    url='https://github.com/c7nw3r/datariot',
    download_url=f'https://github.com/c7nw3r/datariot/archive/refs/tags/v{version}.tar.gz',
    setup_requires=['setuptools_scm'],
    include_package_data=True,
    install_requires=[
        str(r)
        for r in pkg_resources.parse_requirements(
            open(os.path.join(os.path.dirname(__file__), "requirements.txt"))
        )
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
    ],
    extras_require={
        'docx': [
            "python-docx==1.1.0"
        ],
        'pdf': [
            "pdfplumber==0.10.3"
        ],
        'ocr': [
            "pytesseract==0.3.10"
        ],
        'web': [
            "selenium==4.17.2",
            "beautifulsoup4==4.12.3",
            "webdriver_manager==4.0.1",
            "lxml==5.1.0"
        ],
        'xlsx': [
            "openpyxl==3.1.2"
        ],
        'camelot': [
            "camelot-py==0.11.0"
        ],
        'email': [
            "extract-msg==0.48.5"
        ],
        'stopwords': [
            "stopwordsiso",
        ]
    }
)
