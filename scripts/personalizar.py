#!/usr/bin/env python3
"""
IFAM Office - aplica as personalizacoes no codigo-fonte do LibreOffice.

Uso:  python3 scripts/personalizar.py /caminho/para/libreoffice-core

Altera os padroes de fabrica (arquivos de configuracao do officecfg):
  * atalhos do Microsoft Office em portugues (Writer, Calc, Impress);
  * interface em abas (faixa de opcoes) ativada;
  * formatos padrao .docx / .xlsx / .pptx, sem aviso de "manter formato";
  * tema de icones Colibre (estilo Office);
  * fonte padrao Calibri 11 pt no Writer.
"""
import os, re, sys
import xml.etree.ElementTree as ET


FIND = 'vnd.sun.star.findbar:FocusToFindbar'
COMUNS = {
    'N_MOD1': '.uno:Bold', 'S_MOD1': '.uno:Underline', 'B_MOD1': '.uno:Save',
    'T_MOD1': '.uno:SelectAll', 'O_MOD1': '.uno:AddDirect', 'L_MOD1': FIND,
    'U_MOD1': '.uno:SearchDialog', 'K_MOD1': '.uno:HyperlinkDialog', 'F12': '.uno:SaveAs',
}
ALINHAR = {'E_MOD1': '.uno:CenterPara', 'J_MOD1': '.uno:JustifyPara',
           'Q_MOD1': '.uno:LeftPara', 'G_MOD1': '.uno:RightPara'}
ATALHOS = {
    'com.sun.star.text.TextDocument': {**COMUNS, **ALINHAR,
        'A_MOD1': '.uno:OpenFromWriter', 'R_MOD1': '.uno:Redo', 'D_MOD1': '.uno:FontDialog',
        'M_MOD1': '.uno:IncrementIndent', 'M_SHIFT_MOD1': '.uno:DecrementIndent', 'F5': '.uno:GotoPage'},
    'com.sun.star.sheet.SpreadsheetDocument': {**COMUNS,
        'A_MOD1': '.uno:OpenFromCalc', 'R_MOD1': '.uno:FillRight', 'D_MOD1': '.uno:FillDown'},
    'com.sun.star.presentation.PresentationDocument': {**COMUNS, **ALINHAR,
        'A_MOD1': '.uno:Open', 'R_MOD1': '.uno:Redo', 'M_MOD1': '.uno:InsertPage'},
}
IDIOMAS = ['en-US', 'pt-BR', 'pt']   # o IFAM Office usa os atalhos do Office em qualquer idioma


# ---------------------------------------------------------------------------
# Edicoes pontuais no texto: o restante do arquivo (licenca, DOCTYPE,
# namespaces, formatacao) fica intacto.
# ---------------------------------------------------------------------------
def ler(path):
    with open(path, encoding='utf-8', newline='') as f:
        return f.read()


def gravar(path, txt):
    ET.fromstring(txt.encode('utf-8'))          # garante XML valido
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(txt)
    print('  modificado:', path)


def achar(txt, ancoras, ini=0):
    """Posicao logo apos a ultima ancora, procurando-as em sequencia."""
    pos = ini
    for a in ancoras:
        i = txt.find(a, pos)
        if i < 0:
            raise SystemExit('ERRO: nao encontrei %r (o codigo-fonte mudou?)' % a)
        pos = i + len(a)
    return pos


def trocar_valor(txt, ancoras, novo):
    """Troca o primeiro <value>...</value> apos as ancoras, ou cria um antes de </prop>."""
    pos = achar(txt, ancoras)
    fim_prop = txt.index('</prop>', pos)
    m = re.compile(r'<value>[^<]*</value>|<value/>').search(txt, pos, fim_prop)
    if m:
        return txt[:m.start()] + '<value>%s</value>' % novo + txt[m.end():]
    linha = txt.rfind('\n', 0, fim_prop)
    indent = txt[linha + 1:fim_prop]
    return txt[:fim_prop] + '  <value>%s</value>\n%s' % (novo, indent) + txt[fim_prop:]


def span_modulo(txt, secao, modulo):
    ini = achar(txt, ['<node oor:name="%s">' % secao, '<node oor:name="Modules">',
                      '<node oor:name="%s"' % modulo])
    fim = txt.index('\n      </node>', ini)          # modulos ficam com 6 espacos de recuo
    return ini, fim


LANG_RE = re.compile(r'[ \t]*<value xml:lang="(?:%s)"[^>]*>[^<]*</value>\r?\n' % '|'.join(map(re.escape, IDIOMAS)))


def atalhos(src):
    path = os.path.join(src, 'officecfg/registry/data/org/openoffice/Office/Accelerators.xcu')
    txt = ler(path)
    for mod, keys in ATALHOS.items():
        # 1) remove ligacoes en-US/pt das mesmas teclas nas teclas secundarias
        ini, fim = span_modulo(txt, 'SecondaryKeys', mod)
        bloco = txt[ini:fim]
        for key in keys:
            m = re.search(r'\n {8}<node oor:name="%s"[^>]*>.*?\n {8}</node>' % key, bloco, re.S)
            if m:
                bloco = bloco[:m.start()] + LANG_RE.sub('', m.group(0)) + bloco[m.end():]
        txt = txt[:ini] + bloco + txt[fim:]
        # 2) define os atalhos do Office nas teclas primarias
        ini, fim = span_modulo(txt, 'PrimaryKeys', mod)
        bloco = txt[ini:fim]
        for key, cmd in keys.items():
            valores = ''.join('            <value xml:lang="%s">%s</value>\n' % (l, cmd) for l in IDIOMAS)
            m = re.search(r'\n {8}<node oor:name="%s"[^>]*>.*?\n {8}</node>' % key, bloco, re.S)
            if m:
                no = LANG_RE.sub('', m.group(0))
                p = no.index('          </prop>')
                no = no[:p] + valores + no[p:]
                bloco = bloco[:m.start()] + no + bloco[m.end():]
            else:
                bloco += ('\n        <node oor:name="%s" oor:op="replace">\n'
                          '          <prop oor:name="Command">\n'
                          '            <value xml:lang="x-no-translate">L10N SHORTCUTS - NO TRANSLATE</value>\n'
                          '%s          </prop>\n        </node>' % (key, valores))
        txt = txt[:ini] + bloco + txt[fim:]
    gravar(path, txt)


def interface_abas(src):
    path = os.path.join(src, 'officecfg/registry/data/org/openoffice/Office/UI/ToolbarMode.xcu')
    txt = ler(path)
    for app in ('Writer', 'Calc', 'Impress'):
        txt = trocar_valor(txt, ['<node oor:name="Applications">', '<node oor:name="%s"' % app,
                                 '<prop oor:name="Active">'], 'notebookbar.ui')
    gravar(path, txt)


def formatos_office(src):
    path = os.path.join(src, 'officecfg/registry/data/org/openoffice/Setup.xcu')
    txt = ler(path)
    for svc, flt in {'com.sun.star.text.TextDocument': 'MS Word 2007 XML',
                     'com.sun.star.sheet.SpreadsheetDocument': 'Calc MS Excel 2007 XML',
                     'com.sun.star.presentation.PresentationDocument': 'Impress MS PowerPoint 2007 XML'}.items():
        txt = trocar_valor(txt, ['<node oor:name="Factories">', '<node oor:name="%s"' % svc,
                                 '<prop oor:name="ooSetupFactoryDefaultFilter">'], flt)
    gravar(path, txt)


def common_schema(src):
    path = os.path.join(src, 'officecfg/registry/schema/org/openoffice/Office/Common.xcs')
    txt = ler(path)
    txt = trocar_valor(txt, ['<group oor:name="Save">', '<group oor:name="Document">',
                             '<prop oor:name="WarnAlienFormat"'], 'false')
    txt = trocar_valor(txt, ['<prop oor:name="SymbolStyle"'], 'colibre')
    gravar(path, txt)


def fonte_writer(src):
    path = os.path.join(src, 'officecfg/registry/schema/org/openoffice/Office/Writer.xcs')
    txt = ler(path)
    fontes = {'Standard': 'Calibri', 'Heading': 'Calibri Light', 'List': 'Calibri',
              'Caption': 'Calibri', 'Index': 'Calibri'}
    for prop, font in fontes.items():
        txt = trocar_valor(txt, ['<group oor:name="DefaultFont">', '<prop oor:name="%s"' % prop], font)
        txt = trocar_valor(txt, ['<group oor:name="DefaultFont">', '<prop oor:name="%sHeight"' % prop], '388')
    gravar(path, txt)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    print('IFAM Office: personalizando', src)
    for etapa in (atalhos, interface_abas, formatos_office, common_schema, fonte_writer):
        etapa(src)
    print('Pronto.')
