# pyside-lang-comparison-graph
Execute R, Go, Python, Rust, Julia performance test and show result with PySide graph(chart) to compare with each other

If you don't want to test all of them, you can choose some of those languages to test from "Settings".

You can see the real-time log while running the test, pause/resume, stop the test.

You cannot close the app while test is running or paused. If you want to close the app during test, you can do it after clicking stop button or with task manager forcefully.

You can set the timeout if you want. Not quite recommended, it is incorrect for some reasons.

You can save it as png, jpg, pdf file.

See <a href="https://github.com/yjg30737/high-performance-lang-comparison.git">here</a> for detail about performance test

## Requirements
* R, Go, Python, Rust, Julia - for the test
* PySide6 - for GUI
* psutil - for show virtual memory data of your pc
* num2words - for show number as string name

## Usage
### Install
#### If you want to clone
* git clone ~
* python -m pip install psutil num2words
#### If you want to install this with pip
* python -m pip install git+https://github.com/yjg30737/pyside-lang-comparison-graph.git --upgrade
### Run Test
* python main.py
* Write the times you want to calculate
* Press "Run Test" and wait patiently till chart shows the result of test or you can pause it if you have urgent matter
* If you want to save the result, press save

## Preview

![image](https://user-images.githubusercontent.com/55078043/196132830-3bbeb2f9-7c70-4100-9cd1-b914d80ed57c.png)
