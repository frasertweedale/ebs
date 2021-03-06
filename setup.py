import distutils.core

import ebslib  # import version info

with open('README.rst') as fh:
    long_description = fh.read()

distutils.core.setup(
    name='ebs',
    version=ebslib.version,
    description='evidence based scheduler',
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
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Office/Business :: Scheduling',
    ],
    long_description=long_description,
)
