from setuptools import setup, find_packages

setup(
    name='pyside-lang-comparison-graph',
    version='0.0.14',
    author='Jung Gyu Yoon',
    author_email='yjg30737@gmail.com',
    license='MIT',
    packages=find_packages(),
    description='Execute R, Go, Python, Rust, Julia performance test and show result with PySide graph to compare with each other',
    url='https://github.com/yjg30737/pyside-database-chart-example.git',
    install_requires=[
        'PySide6',
        'psutil',
        'num2words'
    ]
)