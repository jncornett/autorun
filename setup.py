from setuptools import setup

setup(
    name='autorun',
    version='0.0.1',
    packages=['autorun'],
    entry_points={
        'console_scripts': [
            'autorun = autorun.__main__:main'
        ]
    },
    install_requires=[
        'watchdog'
    ]
)

