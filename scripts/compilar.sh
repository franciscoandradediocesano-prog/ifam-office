#!/usr/bin/env bash
# IFAM Office - compila o instalador .msi para Windows.
# Roda dentro do Cygwin (no GitHub Actions ou num PC Windows com Visual Studio 2022).
set -euo pipefail

LO_TAG="${LO_TAG:-libreoffice-26.2.7.1}"            # versao estavel do LibreOffice usada como base
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"             # pasta deste repositorio
FONTE="${FONTE:-/cygdrive/c/lo/core}"                # caminho curto e sem espacos (exigencia do Windows)
SAIDA="${SAIDA:-$RAIZ/saida}"

echo "== IFAM Office | base: $LO_TAG | fonte: $FONTE"
df -h /cygdrive/c || true

# 1) Ferramentas recomendadas pelo LibreOffice para Windows
mkdir -p /opt/lo/bin
[ -x /opt/lo/bin/make ] || { wget -q -O /opt/lo/bin/make https://dev-www.libreoffice.org/bin/cygwin/make-4.2.1-msvc.exe; chmod +x /opt/lo/bin/make; }
[ -x /opt/lo/bin/nasm ] || { wget -q -O /opt/lo/bin/nasm https://dev-www.libreoffice.org/bin/cygwin/nasm.exe; chmod +x /opt/lo/bin/nasm; }
export PATH="/opt/lo/bin:$PATH"

# 2) Codigo-fonte original
if [ ! -d "$FONTE/.git" ]; then
  mkdir -p "$(dirname "$FONTE")"
  git -c core.autocrlf=false clone --depth 1 --branch "$LO_TAG" https://github.com/LibreOffice/core.git "$FONTE"
fi
cd "$FONTE"
git -c core.autocrlf=false submodule update --init --depth 1 translations dictionaries

# 3) Modificacoes do IFAM Office (atalhos, interface em abas, formatos, icones, fonte)
python3 "$RAIZ/scripts/personalizar.py" "$FONTE"
mkdir -p "$SAIDA" && git diff > "$SAIDA/ifam-office-mudancas-$LO_TAG.diff"   # registro publico das mudancas (MPL)
rm -rf "$FONTE/ifam-branding" && cp -r "$RAIZ/branding" "$FONTE/ifam-branding" && rm -rf "$FONTE/ifam-branding/fonte"

# 4) Configuracao da compilacao (nome, marca, idioma e formato do instalador)
cat > autogen.input <<CFG
--with-visual-studio=2022
--enable-release-build
--with-product-name=IFAM Office
--with-vendor=IFAM - Campus Sao Gabriel da Cachoeira
--with-branding=$(cygpath -m "$FONTE/ifam-branding")
--with-lang=pt-BR
--with-myspell-dicts
--with-package-format=msi
--without-help
--without-helppack-integration
--without-java
--without-junit
--without-doxygen
--without-dotnet
--disable-cli
--disable-online-update
--disable-report-builder
--disable-firebird-sdbc
--disable-cve-tests
--disable-dependency-tracking
CFG
echo "== autogen.input:"; cat autogen.input
[ -f config_host.mk ] || ./autogen.sh

# 5) Compilacao (demorada) e geracao do instalador
make build      # compila tudo e gera o instalador (instsetoo_native)

# 6) Copia o .msi para a pasta de saida
find workdir/installation -name '*.msi' -exec cp -v {} "$SAIDA/" \;
ls -la "$SAIDA"
