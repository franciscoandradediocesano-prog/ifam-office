#!/usr/bin/env python3
"""Define os produtos do IFAM Office e valida com o parser real do instalador."""
from pathlib import Path
import re
import subprocess
import sys

PRODUTOS = {
    "IFAMOffice": """IFAMOffice : LibreOffice
{
    Settings
    {
        variables
        {
            WINDOWSBASISROOTNAME IFAMOffice
        }
        downloadname IFAMOffice_{productversion}_{os}_install_{languages}
        langpackdownloadname IFAMOffice_{productversion}_languagepack_{os}_install_{languages}
        helppackdownloadname IFAMOffice_{productversion}_helppack_{os}_install_{languages}
    }
}
""",
    "IFAMOffice_SDK": """IFAMOffice_SDK : LibreOffice_SDK
{
    Settings
    {
        variables
        {
            PRODUCTNAME @PRODUCTNAME@
            WINDOWSBASISROOTNAME IFAMOffice
        }
        downloadname IFAMOffice-SDK_{packageversion}_{os}_install_{languages}
    }
}
""",
}


def preparar(path):
    texto = path.read_text(encoding="utf-8")
    original = texto
    for produto, bloco in PRODUTOS.items():
        if not re.search(rf"^{re.escape(produto)}\s*(?::[^\n]*)?$", texto, re.M):
            texto = texto.rstrip() + "\n\n" + bloco
    if texto != original:
        path.write_text(texto, encoding="utf-8", newline="\n")
        print("Produto do instalador definido:", path)


def validar(src):
    lista = src / "instsetoo_native/util/openoffice.lst"
    if not lista.is_file():
        sys.exit("ERRO: execute autogen antes de validar o instalador.")
    # A mesma funcao que interrompeu a #9, incluindo a heranca dos produtos.
    codigo = r'''
        use strict;
        use warnings;
        $installer::globals::ziplistname = $ARGV[0];
        open my $fh, '<', $ARGV[0] or die "Lista do instalador: $!";
        my @linhas = <$fh>;
        for my $produto (qw(IFAMOffice IFAMOffice_SDK)) {
            $installer::globals::product = $produto;
            my $nome = $produto;
            my %visitados;
            while (defined $nome) {
                die "Heranca circular: $nome" if $visitados{$nome}++;
                my ($bloco, $pai) = installer::ziplist::getproductblock(\@linhas, $nome, 1);
                installer::ziplist::getproductblock($bloco, 'Settings', 0);
                $nome = $pai;
            }
            print "OK: produto $produto reconhecido pelo instalador.\n";
        }
    '''
    subprocess.run([
        "perl", "-I", str(src / "solenv/bin/modules"),
        "-Minstaller::ziplist", "-e", codigo, str(lista),
    ], check=True)


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3) or (len(sys.argv) == 3 and sys.argv[2] != "--validar"):
        sys.exit("Uso: preparar_instalador.py FONTE [--validar]")
    fonte = Path(sys.argv[1])
    if len(sys.argv) == 3:
        validar(fonte)
    else:
        preparar(fonte / "instsetoo_native/util/openoffice.lst.in")
        gerada = fonte / "instsetoo_native/util/openoffice.lst"
        if gerada.is_file():
            preparar(gerada)
