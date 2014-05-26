from setuptools import setup

setup(
    name='booger',
    version='0.4.1',
    author='thenoviceoof',
    author_email='thenoviceoof@gmail.com',
    packages=['booger'],
    scripts=['bin/booger'],
    url='https://github.com/thenoviceoof/booger',
    license='MIT',
    description='Pretty curses-based nose frontend',
    long_description=open('README.rst').read(),
    install_requires=[
        'nose',
    ],
    entry_points = {
        'nose.plugins.0.10': [
            'booger = booger:BoogerPlugin'
        ]
    },
)
