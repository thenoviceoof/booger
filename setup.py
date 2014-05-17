from setuptools import setup

setup(
    name='booger',
    version='0.1.0',
    author='thenoviceoof',
    author_email='thenoviceoof@gmail.com',
    packages=['booger'],
    scripts=['bin/booger'],
    url='https://github.com/thenoviceoof/booger',
    license='Beerware',
    description='Pretty curses-based nose frontend',
    long_description=open('README.md').read(),
    install_requires=[
        'nose',
    ],
    entry_points = {
        'nose.plugins.0.10': [
            'booger = booger:BoogerPlugin'
        ]
    },
)
