from setuptools import setup, find_packages


setup(
    name='lexibank',
    version='0.1.0.dev0',
    description='',
    author='',
    author_email='',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    keywords='',
    license='MIT',
    url='https://github.com/lexibank/lexibank-study',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "lexibank=lexibank.__main__:main",
            ],
        },
    platforms='any',
    python_requires='>=3.5',
        install_requires=[
        'pylexibank',
        'attrs>=18.2',
        'cldfbench>=1.2.3',
        'clldutils>=3.5',
        'cldfcatalog>=1.3',
        'csvw>=1.6',
        'pycldf',
        'uritemplate',
        'lingpy>=2.6.8',
        'pyclts>=3.1'
    ],
    extras_require={
        'dev': ['flake8', 'wheel', 'twine'],
        'test': [
            'pytest>=6',
            'pytest-mock',
            'pytest-cov',
            'coverage',
        ],
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
)