import distutils.core
import sys

import ebslib  # import version info

with open('README') as fh:
    long_description = fh.read()

distutils.core.setup(
    name='ebs',
    version=ebslib.version,
    description='Evidence Based Scheduling program',
    author='Fraser Tweedale',
    author_email='frase@frase.id.au',
    url='https://github.com/frasertweedale/ebs',
    packages=['ebslib'],
    scripts=['scripts/ebs'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Office/Business :: Scheduling',
    ],
    long_description=long_description,
)
