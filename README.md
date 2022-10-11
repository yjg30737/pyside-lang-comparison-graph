# pyside-lang-comparison-graph
Execute R, Go, Python, Rust, Julia performance test and show result with PySide graph(chart) to compare with each other

You can save it as png, jpg, pdf file.

See <a href="https://github.com/yjg30737/high-performance-lang-comparison.git">here</a> for detail about performance test

## Requirements
* R, Go, Python, Rust, Julia - for the test
* PySide6 - for graph GUI
* psutil - for show virtual memory data of your pc
* num2words - for show number as string name

## Usage
### First
#### If you want to clone
* git clone ~
* python -m pip install psutil num2words
#### If you want to install this with pip
* python -m pip install git+https://github.com/yjg30737/pyside-lang-comparison-graph.git --upgrade
### Second
* python main.py
* Write the times you want to calculate
* Press "Run Test" and wait patiently till chart shows the result of test
* If you want to save the result, press save

## Preview

![image](https://user-images.githubusercontent.com/55078043/194853301-83c1e399-aa4d-463e-83e2-8b8bcc5c0483.png)
