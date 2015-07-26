from setuptools import setup

setup(
    name='yaddle',
    version='0.0.2',
    url='https://github.com/zweifisch/yaddle-py',
    keywords='json schema',
    license='MIT',
    description='yet another data format description language',
    long_description=open('README.rst').read(),
    author='Feng Zhou',
    author_email='zf.pascal@gmail.com',
    packages=['yaddle'],
    install_requires=['funcparserlib'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
    ]
)
