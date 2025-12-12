#!/bin/bash
cd "$(dirname "$0")"

echo "Building documentation..."
quarto render
echo "Documentation built in _site/"
