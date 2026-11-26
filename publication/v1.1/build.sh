#!/bin/sh
set -eu
cd "$(dirname "$0")"
stem=VP_VNP_Audit_and_Dossier_v1.1
mkdir -p build/cache build/var build/config
cp "$stem.tex" nous-black.png build/
cd build
export TEXMFCACHE=cache TEXMFVAR=var TEXMFCONFIG=config
export SOURCE_DATE_EPOCH=1795734600 FORCE_SOURCE_DATE=1 TZ=UTC
for pass in 1 2 3; do
  lualatex -no-shell-escape -interaction=nonstopmode -halt-on-error "$stem.tex" > "compile-$pass.stdout"
done
cp "$stem.pdf" "../$stem.pdf"
