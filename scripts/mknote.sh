#!/bin/bash
if $(PWD)
mkdir -p notes
file="notes/$(date +%Y-%B-%d).txt"
echo -e "\n\n----------\n$(date +"%Y-%m-%d %H:%M:%S")\n----------\n" >> "$file"
