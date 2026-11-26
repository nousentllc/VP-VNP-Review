#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p build/cache
export TEXMFVAR="$PWD/build/cache"
export TEXMFCACHE="$PWD/build/cache"
export SOURCE_DATE_EPOCH=1795708800
export FORCE_SOURCE_DATE=1
publication_engine="${LATEX_ENGINE:-lualatex}"
for publication_pass in 1 2 3; do
  "$publication_engine" -no-shell-escape -interaction=nonstopmode -halt-on-error -output-directory=build VP_VNP_Expanded_Academic_Audit.tex > "build/compile-$publication_pass.stdout" 2>&1
done
cp build/VP_VNP_Expanded_Academic_Audit.pdf VP_VNP_Expanded_Academic_Audit.pdf
