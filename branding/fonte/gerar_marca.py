#!/usr/bin/env python3
"""Gera as imagens de marca do IFAM Office (tela de abertura, logos, janela Sobre).
Requer: pip install fonttools cairosvg ; fonte Carlito (metricamente igual a Calibri).
Uso: python3 gerar_marca.py <pasta_saida>   (por padrao, a pasta branding/)"""
import os, re, sys, cairosvg
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

VERDE, VERMELHO, ESCURO, CINZA = '#32A041', '#C8191E', '#1F2A22', '#5C6660'
FONTES = {'b': '/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf',
          'r': '/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf'}
_cache = {}

def texto(s, x, y, size, peso='r', cor=ESCURO):
    """Converte texto em caminho SVG (nao depende de fontes instaladas). Retorna (svg, largura)."""
    f = _cache.setdefault(peso, TTFont(FONTES[peso]))
    gs, cmap, upm = f.getGlyphSet(), f.getBestCmap(), f['head'].unitsPerEm
    k = size / upm
    out, cx = [], x
    for ch in s:
        g = cmap.get(ord(ch))
        if g is None: continue
        pen = SVGPathPen(gs)
        gs[g].draw(TransformPen(pen, (k, 0, 0, -k, cx, y)))
        d = re.sub(r'-?\d+\.\d+', lambda m: ('%.1f' % float(m.group())).rstrip('0').rstrip('.'), pen.getCommands())
        if d: out.append(d)
        cx += gs[g].width * k
    return '<path fill="%s" d="%s"/>' % (cor, ' '.join(out)), cx - x

def simbolo(x, y, s):
    """Simbolo original: folha de documento sobre quadrado verde, com circulo vermelho."""
    k = s / 100.0
    return ('<g transform="translate(%g %g) scale(%g)">'
            '<rect width="100" height="100" rx="20" fill="%s"/>'
            '<path d="M28 18h32l14 14v50a4 4 0 0 1-4 4H28a4 4 0 0 1-4-4V22a4 4 0 0 1 4-4z" fill="#fff"/>'
            '<path d="M60 18v10a4 4 0 0 0 4 4h10z" fill="#D7EED9"/>'
            '<rect x="33" y="44" width="32" height="5" rx="2.5" fill="%s"/>'
            '<rect x="33" y="55" width="32" height="5" rx="2.5" fill="%s"/>'
            '<rect x="33" y="66" width="20" height="5" rx="2.5" fill="%s"/>'
            '<circle cx="80" cy="20" r="11" fill="%s" stroke="#fff" stroke-width="3"/>'
            '</g>') % (x, y, k, VERDE, VERDE, VERDE, VERDE, VERMELHO)

def svg(w, h, corpo, fundo=None):
    bg = '<rect width="%g" height="%g" fill="%s"/>' % (w, h, fundo) if fundo else ''
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" '
            'width="%g" height="%g" viewBox="0 0 %g %g">%s%s</svg>\n') % (w, h, w, h, bg, corpo)

def logo(invertido=False):
    # mesmo tamanho do logo original (345.611 x 71.5)
    c1, c2 = ('#FFFFFF', '#8FD69A') if invertido else (ESCURO, VERDE)
    t1, w1 = texto('IFAM', 84, 52, 50, 'b', c1)
    t2, w2 = texto(' Office', 84 + w1, 52, 50, 'r', c2)
    return svg(345.611, 71.5, simbolo(4, 2.5, 66) + t1 + t2)

def splash(w, h):
    s = w / 644.0
    faixa = ('<rect width="%g" height="%g" fill="%s"/><rect x="%g" width="%g" height="%g" fill="%s"/>'
             % (w * 0.82, 6 * s, VERDE, w * 0.82, w * 0.18, 6 * s, VERMELHO))
    t1, w1 = texto('IFAM', 168 * s, 98 * s, 64 * s, 'b', ESCURO)
    t2, _ = texto(' Office', 168 * s + w1, 98 * s, 64 * s, 'r', VERDE)
    t3, _ = texto('Instituto Federal do Amazonas', 170 * s, 128 * s, 17 * s, 'r', CINZA)
    t4, _ = texto('Campus São Gabriel da Cachoeira', 170 * s, 149 * s, 17 * s, 'r', CINZA)
    return svg(w, h, faixa + simbolo(40 * s, 38 * s, 108 * s) + t1 + t2 + t3 + t4, '#FFFFFF')

def sobre():
    w, h = 372.72406, 354.72815
    t1, w1 = texto('IFAM', 0, 0, 64, 'b', ESCURO)
    _, w2 = texto(' Office', 0, 0, 64, 'r', VERDE)
    x0 = (w - w1 - w2) / 2
    t1, _ = texto('IFAM', x0, 262, 64, 'b', ESCURO)
    t2, _ = texto(' Office', x0 + w1, 262, 64, 'r', VERDE)
    _, w3 = texto('Campus São Gabriel da Cachoeira', 0, 0, 19, 'r')
    t3, _ = texto('Campus São Gabriel da Cachoeira', (w - w3) / 2, 296, 19, 'r', CINZA)
    return svg(w, h, simbolo((w - 150) / 2, 40, 150) + t1 + t2 + t3)

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..')
    arquivos = {'logo.svg': logo(), 'logo-sc.svg': logo(), 'logo_inverted.svg': logo(True),
                'logo-sc_inverted.svg': logo(True), 'about.svg': sobre()}
    for nome, conteudo in arquivos.items():
        open(os.path.join(out, nome), 'w', encoding='utf-8').write(conteudo)
    cairosvg.svg2png(bytestring=splash(644, 199).encode(), write_to=os.path.join(out, 'intro.png'))
    cairosvg.svg2png(bytestring=splash(1288, 398).encode(), write_to=os.path.join(out, 'intro-highres.png'))
    try:   # reduz o tamanho dos PNG (opcional)
        from PIL import Image
        for n in ('intro.png', 'intro-highres.png'):
            f = os.path.join(out, n)
            Image.open(f).convert('RGB').quantize(64).save(f, optimize=True)
    except ImportError:
        pass
    open(os.path.join(out, 'progress.conf'), 'w').write('PROGRESSBARCOLOR="50,160,65"\nPROGRESSFRAMECOLOR="200,200,200"\nPROGRESSTEXTCOLOR="92,102,96"\n')
    print('Marca gerada em', os.path.abspath(out))
