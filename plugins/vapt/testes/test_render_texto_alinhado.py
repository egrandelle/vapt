# -*- coding: utf-8 -*-
"""0.12.0: o render desenha o alinhamento das linhas que o DA escolheu no palco.

O KV sintetico de duas linhas (HH em cima, HHH embaixo, alinhado a esquerda, na fonte de autoteste do motor): com o
texto alinhado a direita ou ao centro, a derivacao mede o desvio da ancora (a linha mais larga fica no lugar) e a
caixa da tinta com o alinhamento novo; o render inteiro passa (a tinta cabe na caixa validada) e, no master, a linha
HHH fica onde estava no KV e a linha HH termina na borda direita dela, ou fica no meio dela. Tambem no texto editado
pelo DA. Tudo sintetico."""
import io
import sys

import numpy as np
import pytest
from PIL import Image

import test_render_texto_editado as tre
import test_tela_palco as tp
from vapt import contratos, humano
from vapt.briefing import modelo as mb
from vapt.derivacao import medida_quebras
from vapt.render import derivado as rd
from vapt.render import execucao

modelo = tre.modelo
job = tre.job
# o H da fonte de autoteste no documento: corpo 25 na escala 2 da matriz (50 px), avanco 34 px
C = tp.CORPO_DUAS * tp.ESCALA_DUAS
AVANCO = tp.H_AVANCO * C
BASES = (tp.ORIGEM_DUAS[1], tp.ORIGEM_DUAS[1] + tp.ENTRELINHA_DUAS * tp.ESCALA_DUAS)
TOL_PX = 1.5  # numero-neutro: px do master, o antialias da borda do glifo
ESCURO = 200  # numero-neutro: a media do RGB abaixo da qual o pixel e tinta do texto (o fundo e claro)


def _alinhar(job, valor, texto=None):
    conteudo = tre.te.montar(job)
    gid = tre._familia_de(conteudo, 'mesma')
    el = tre._titulo(conteudo, gid)
    eds = [{'elemento': el, 'acao': 'texto', 'texto': texto}] if texto is not None else []
    eds.append({'elemento': el, 'acao': 'alinhar_texto', 'alinhamento': valor})
    return tre._editar(job, None, edicoes=eds)


def _tinta_da_linha(img, tr, n, janela):
    """(esq, dir) da tinta da linha n no master, dentro da janela x [x0, x1] (o logo fica fora dela): as colunas
    escuras na faixa do meio do H daquela linha."""
    meio_doc = BASES[n] - tp.H_ALTURA * C / 2.0  # numero-neutro: o meio da altura do H
    _x, ya, _x1, yb = rd._caixa(tr, [0, meio_doc - 4, 0, meio_doc + 4])
    x0, x1 = max(int(round(janela[0])), 0), min(int(round(janela[1])), img.shape[1])
    faixa = img[int(round(ya)):int(round(yb)) + 1, x0:x1, :3].astype(float).mean(axis=2)
    cols = np.where((faixa < ESCURO).any(axis=0))[0]
    assert cols.size, 'sem tinta na linha %d' % n
    return float(cols[0] + x0), float(cols[-1] + 1 + x0)


@pytest.mark.skipif(sys.platform != 'win32', reason='o isolador dos filhos roda no Windows')
@pytest.mark.parametrize('valor', ['direita', 'centro'])
@pytest.mark.parametrize('texto', [None, 'HH\nHHH'])
def test_render_desenha_o_alinhamento_com_a_linha_mais_larga_no_lugar(job, modelo, monkeypatch, valor, texto):
    medida_quebras.limpar_cache()
    el = _alinhar(job, valor, texto)
    d = tre._deriv(job, 'mesma')
    assert d['situacao'] == 'derivado', d.get('devolucao')
    x = next(e for e in d['elementos'] if e['id'] == el)
    [camada] = x['alinhamento_do_da']['camadas']
    larga = 3 * tp.H_AVANCO * tp.CORPO_DUAS  # numero-neutro: os tres H da linha mais larga, no espaco do texto
    assert camada['desvio'] == pytest.approx(larga * (1.0 if valor == 'direita' else 0.5), abs=0.05)
    tr = x['transformacao']
    laudo = contratos.ler(job / mb.ARQUIVO_LAUDO, 'laudo/1')
    ct = mb.camadas_do_laudo(laudo)[modelo['layer_id']]['geometria']['caixa_tinta']
    if texto is None:
        # a tinta medida com o alinhamento novo e a do KV: a linha mais larga define as bordas
        assert camada['caixa_doc'] == pytest.approx(ct, abs=1.0)
    monkeypatch.setattr(humano, 'console_interativo', lambda: (True, None))
    rel = execucao.renderizar(job, disparo=humano.exigir('render'), formato='mesma', aceites=('largura_divergente',))
    contrato = contratos.ler(job / 'render' / 'mesma' / 'contrato.json', 'composicao/1')
    e = tre._entrada_editada(contrato, modelo['layer_id'])
    assert e['alinhamento_do_da']['justificacao'] == {'direita': 'RIGHT', 'centro': 'CENTER'}[valor]
    assert any(r['codigo'] == 'texto_alinhado_pelo_da' for r in contrato['registros'])
    tinta = next(s['tinta'] for s in rel['entradas'] if s['id'] == e['id'])
    assert tinta == pytest.approx(rd._caixa(tr, ct), abs=rd._tolerancia_tinta(rd._caixa(tr, ct)))
    img = _master(job)
    caixa = rd._caixa(tr, ct)
    janela = (caixa[0] - AVANCO * float(tr['s']), caixa[2] + AVANCO * float(tr['s']))
    l1, l2 = _tinta_da_linha(img, tr, 0, janela), _tinta_da_linha(img, tr, 1, janela)
    # o mesmo formato sem o alinhamento (o KV, a esquerda), para comparar
    tre._editar(job, None, edicoes=[] if texto is None else [{'elemento': el, 'acao': 'texto', 'texto': texto}])
    if texto is not None:
        # a caixa medida do texto editado e a mesma com e sem o alinhamento: a linha mais larga define as bordas
        sem = next(e for e in tre._deriv(job, 'mesma')['elementos'] if e['id'] == el)
        assert 'alinhamento_do_da' not in sem
        assert x['caixa_texto_editado'] == pytest.approx(sem['caixa_texto_editado'], abs=1.0)
    execucao.renderizar(job, disparo=humano.exigir('render'), formato='mesma', aceites=('largura_divergente',))
    kv = _master(job)
    k1, k2 = _tinta_da_linha(kv, tr, 0, janela), _tinta_da_linha(kv, tr, 1, janela)
    # a linha mais larga (HHH) fica onde estava no KV
    assert l2 == pytest.approx(k2, abs=TOL_PX), (l2, k2)
    # a linha curta (HH) anda sem mudar de largura: termina na borda direita da mais larga, ou fica no meio dela
    assert l1[1] - l1[0] == pytest.approx(k1[1] - k1[0], abs=TOL_PX)
    assert k1[0] == pytest.approx(k2[0], abs=TOL_PX)
    if valor == 'direita':
        assert l1[1] == pytest.approx(l2[1], abs=TOL_PX), (l1, l2)
    else:
        assert (l1[0] + l1[1]) / 2 == pytest.approx((l2[0] + l2[1]) / 2, abs=TOL_PX), (l1, l2)
    assert l1[0] > k1[0] + AVANCO * float(tr['s']) / 3  # numero-neutro: a linha curta andou de verdade
    medida_quebras.limpar_cache()


def _master(job):
    return np.asarray(Image.open(io.BytesIO((job / 'render' / 'mesma' / 'master.png').read_bytes())).convert('RGB'))
