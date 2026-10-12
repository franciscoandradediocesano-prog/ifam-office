#!/usr/bin/env bash
# IFAM Office - compila o instalador .msi para Windows.
# Roda dentro do Cygwin (no GitHub Actions ou num PC Windows com Visual Studio 2022).
set -euo pipefail

LO_TAG="${LO_TAG:-libreoffice-26.2.7.1}"            # versao estavel do LibreOffice usada como base
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"             # pasta deste repositorio
FONTE="${FONTE:-/cygdrive/c/lo/core}"                # caminho curto e sem espacos (exigencia do Windows)
SAIDA="${SAIDA:-$RAIZ/saida}"
DOWNLOADS="${DOWNLOADS:-/cygdrive/c/lo/tarballs}"     # bibliotecas externas baixadas (guardadas em cache entre execucoes)
mkdir -p "$DOWNLOADS"

echo "== IFAM Office | base: $LO_TAG | fonte: $FONTE"
df -h /cygdrive/c || true

# 1) Ferramentas recomendadas pelo LibreOffice para Windows
mkdir -p /opt/lo/bin
[ -x /opt/lo/bin/make ] || { wget -q -O /opt/lo/bin/make https://dev-www.libreoffice.org/bin/cygwin/make-4.2.1-msvc.exe; chmod +x /opt/lo/bin/make; }
# o nasm precisa da extensao .exe para ser achado pelo cmd.exe do Windows (OpenSSL)
[ -x /opt/lo/bin/nasm.exe ] || { wget -q -O /opt/lo/bin/nasm.exe https://dev-www.libreoffice.org/bin/cygwin/nasm.exe; chmod +x /opt/lo/bin/nasm.exe; }
# Os processos nativos do Windows tambem precisam encontrar o sccache com .exe.
if [ -n "${SCCACHE_PATH:-}" ]; then
  cp "$(cygpath -u "$SCCACHE_PATH")" /opt/lo/bin/sccache.exe
  chmod +x /opt/lo/bin/sccache.exe
fi
export PATH="/opt/lo/bin:$PATH"
cmd.exe /d /c 'nasm -v'    # verifica o mesmo ambiente usado pelo OpenSSL

# 2) Codigo-fonte original
if [ ! -d "$FONTE/.git" ]; then
  mkdir -p "$(dirname "$FONTE")"
  git -c core.autocrlf=false clone --depth 1 --branch "$LO_TAG" https://github.com/LibreOffice/core.git "$FONTE"
fi
cd "$FONTE"
git -c core.autocrlf=false submodule update --init --depth 1 translations dictionaries

# O configure reutiliza o resultado negativo da busca por ccache ao buscar
# sccache. Limpar esse resultado permite detectar o cache instalado no runner.
python3 - "$FONTE/configure.ac" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
original = '                AC_PATH_PROG([CCACHE],[sccache],[not found])'
corrigido = '                unset ac_cv_path_CCACHE\n                CCACHE=""\n' + original
texto = path.read_text(encoding='utf-8')
if corrigido not in texto:
    if texto.count(original) != 1:
        sys.exit('ERRO: a deteccao de sccache mudou no configure.ac; revise a correcao.')
    path.write_text(texto.replace(original, corrigido, 1), encoding='utf-8', newline='\n')
PY

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
--with-external-tar=$(cygpath -m "$DOWNLOADS")
CFG
if command -v sccache >/dev/null; then
  echo '--enable-ccache' >> autogen.input  # mantem o cache tambem no C++ com PCH
fi
echo "== autogen.input:"; cat autogen.input
./autogen.sh    # reconfigura tambem quando o codigo-fonte ja existe
if command -v sccache >/dev/null; then
  for compilador in CC CXX; do
    grep -Eq "^export $compilador[[:space:]]*=.*sccache" config_host.mk || {
      echo "ERRO: sccache nao foi ativado para $compilador pelo configure." >&2
      exit 1
    }
  done
fi

# 5) Compilacao (demorada) e geracao do instalador
echo "== cache de compilacao:"; grep -E '^export (CC=|CXX=|CCACHE_DEPEND_MODE=)' config_host.mk
command -v sccache >/dev/null && sccache --show-stats | head -5 || echo "sccache nao encontrado no PATH"
echo "== downloads ja disponiveis: $(ls "$DOWNLOADS" | wc -l) arquivos"
make build      # compila tudo e gera o instalador (instsetoo_native)

# 6) Copia o .msi para a pasta de saida
find workdir/installation -name '*.msi' -exec cp -v {} "$SAIDA/" \;
compgen -G "$SAIDA/*.msi" >/dev/null || {
  echo 'ERRO: a compilacao terminou sem gerar o instalador .msi.' >&2
  exit 1
}
ls -la "$SAIDA"
