#!/usr/bin/env python

from distutils.core import setup

setup(
    name="MaMuTTrackingExport",
    version="0.1.0",
    author="Jonas Massa",
    author_email="massa.jonas@iwr.uni-heidelberg.com",
    description=("Export tracking results (from ilastik) in the format required by MaMuT"),
    license="MIT",
    keywords="cell tracking ilastik fiji",
    url="https://github.com/Beinabih/MaMutConverter",
    packages=['mamutexport'],
    package_data={'mamutexport': ['raw_input.xml']},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 2.7"
    ],
)