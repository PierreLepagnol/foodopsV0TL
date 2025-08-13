#!/bin/bash

# Compile LaTeX to PDF
# Usage: ./compile_latex.sh [file.tex]

file="${1:-main.tex}"

# Go to project root
cd "$(dirname "$0")/.."

# Create output directory
mkdir -p output

# Compile with latexmk
latexmk -xelatex -output-directory=output "$file"

echo "Done: output/$(basename "$file" .tex).pdf"