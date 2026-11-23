# -*- coding: utf-8 -*-
"""0.12.0 (revisao): o alinhamento do DA no texto de paragrafos com alinhamentos diferentes no PSD.

O KV sintetico de duas linhas com HH ao centro (o primeiro paragrafo) e HHH a esquerda (o segundo), na fonte de
autoteste do motor. Criterios:
  - o texto misto nao tem um alinhamento do KV: a previa diz None (a pagina nao marca botao nenhum) e toda escolha
    vale, tambem a do primeiro paragrafo (centro), e leva todas as linhas a ela;
  - o palco do texto alinhado leva o alinhamento de cada linha no KV, para a pagina por a linha mais larga onde o KV a
    poe;
  - a derivacao mede o desvio pela linha mais larga (HHH, que comeca na ancora): a esquerda o desvio e zero, ao centro
    meio avanco dela, a direita o avanco inteiro. A uniao das linhas (HH passa meia largura para a esquerda da
    ancora) levava a linha mais larga junto.
Tudo sintetico."""
import json
import shutil

import pytest

import test_derivacao_apoio as ap
import test_fontes_apoio as fap
import test_render_texto_editado as tre
import test_tela_palco as tp
from vapt import contratos
from vapt.briefing import modelo as mb
from vapt.derivacao import medida_quebras
from vapt.tela import estado as te

C = tp.CORPO_DUAS * tp.ESCALA_DUAS
ORIGEM = (60.0, 60.0)  # numero-neutro: a origem do texto, com lugar para o HH ao centro a esquerda dela
# o psd-tools grava a justificacao como 0 (esquerda), 1 (direita) e 2 (centro): HH\r ao centro e HHH\r a esquerda
PARAGRAFOS = [(3, 2), (4, 0)]  # numero-neutro: os comprimentos dos dois paragrafos
LARGA = 3 * tp.H_AVANCO * tp.CORPO_DUAS  # numero-neutro: o avanco de HHH no espaco do texto


def _tinta():
    """A tinta no documento: HH ao centro da ancora, HHH a partir dela (render/texto.py)."""
    x, y = ORIGEM
    curta = 2 * tp.H_AVANCO * C  # numero-neutro: o avanco de HH no documento
    return [x - curta / 2 + tp.H_ESQ * C, y - tp.H_ALTURA * C, x + (2 * tp.H_AVANCO + tp.H_DIR) * C,  # numero-neutro: o meio e os dois H antes do ultimo
            y + tp.ENTRELINHA_DUAS * tp.ESCALA_DUAS]


@pytest.fixture(scope='module')
def modelo(tmp_path_factory):
    from vapt.job import nucleo
    from vapt.render import autoteste
    base = tmp_path_factory.mktemp('texto-misto')
    fontes = base / 'origem-fontes'
    fap.gravar(fontes, 'autoteste.ttf', autoteste.gerar_fonte())
    job = base / 'job'
    psd = tp._psd_duas_linhas(base / 'origem' / 'kv.psd', autoteste.NOME_PS, paragrafos=PARAGRAFOS, origem=ORIGEM,
                              tinta=_tinta())
    nucleo.criar(job, psd, 'c', fontes=[fontes])
    r = nucleo.proxima(job, todas=True)
    assert r.codigo == 0, (r.situacao, r.linhas_humanas)
    laudo = contratos.ler(job / mb.ARQUIVO_LAUDO, 'laudo/1')
    ids = {c['nome']: c['identidade']['layer_id'] for c in laudo['camadas']}
    funcoes = {ids['fundo-sintetico']: 'fundo', ids['duas-linhas']: 'titulo', ids['quadrado-sintetico']: 'logo_principal'}
    b = ap.briefing(funcoes=funcoes, formatos=[ap.formato(i, w, h, rotacao=tre.ROT0) for i, w, h in tp.FORMATOS_DUAS])
    b.pop('cabecalho')
    b.pop('job_id')
    arq = base / 'fixture.json'
    arq.write_text(json.dumps(b), encoding='utf-8')
    mb.importar_teste(job, arq)
    return {'job': job, 'layer_id': ids['duas-linhas'], 'laudo': laudo}


@pytest.fixture
def job(modelo, tmp_path):
    destino = tmp_path / 'job'
    shutil.copytree(modelo['job'], destino)
    return destino


def test_o_laudo_tem_os_dois_alinhamentos(modelo):
    c = mb.camadas_do_laudo(modelo['laudo'])[modelo['layer_id']]
    assert [p['justificacao'] for p in c['texto']['paragrafos']][:2] == ['CENTER', 'LEFT']


def test_previa_do_texto_misto(job, modelo):
    conteudo = te.montar(job)
    gid = tre._familia_de(conteudo, 'mesma')
    el = tre._titulo(conteudo, gid)
    sem = conteudo['editar']({'familia': gid, 'versao': None, 'edicoes': []})
    [t] = [x for x in sem['textos_da_quebra'] if x['elemento'] == el]
    assert t['alinhamento_kv'] is None  # nenhum botao marcado
    # o centro (o do primeiro paragrafo) tambem vale: leva o HHH ao centro
    for valor in ('centro', 'esquerda'):
        r = conteudo['editar']({'familia': gid, 'versao': None,
                                'edicoes': [{'elemento': el, 'acao': 'alinhar_texto', 'alinhamento': valor}]})
        assert r['recusas'] == [] and [a['alinhamento'] for a in r['alinhamentos_do_da']] == [valor]
        for m in r['membros']:
            [p] = [x for x in m['palco']['pecas'] if x['elemento'] == el and x['tipo'] == 'texto']
            assert p['alinhamento'] == valor and p['alinhamento_kv'] == 'centro'
            assert p['alinhamento_kv_linhas'] == ['centro', 'esquerda']


@pytest.mark.parametrize('valor,fracao', [('esquerda', 0.0), ('centro', 0.5), ('direita', 1.0)])
def test_derivacao_mede_o_desvio_pela_linha_mais_larga(job, modelo, valor, fracao):
    medida_quebras.limpar_cache()
    conteudo = te.montar(job)
    el = tre._titulo(conteudo, tre._familia_de(conteudo, 'mesma'))
    assert tre._editar(job, None, edicoes=[{'elemento': el, 'acao': 'alinhar_texto', 'alinhamento': valor}]) == el
    x = next(e for e in tre._deriv(job, 'mesma')['elementos'] if e['id'] == el)
    [camada] = x['alinhamento_do_da']['camadas']
    # o HHH comeca na ancora no KV (a esquerda): o desvio e o lugar da ancora nova nele
    assert camada['desvio'] == pytest.approx(LARGA * fracao, abs=0.05), camada
    assert camada['justificacao'] == {'esquerda': 'LEFT', 'centro': 'CENTER', 'direita': 'RIGHT'}[valor]
    medida_quebras.limpar_cache()
