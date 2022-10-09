@echo off
Rscript a.R %1
go run a.go %1
python a.py %1
cargo run --release -- %1
REM cargo run --release
julia a.jl %1