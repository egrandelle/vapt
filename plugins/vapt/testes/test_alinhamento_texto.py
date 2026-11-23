# -*- coding: utf-8 -*-
"""0.12.0: o alinhamento das linhas do texto escolhido pelo DA no palco (pedido do Duda: "passar um texto que veio
centralizado para alinhado a esquerda ou a direita").

Funcoes puras, sem Chromium: a edicao alinhar_texto (o ultimo vale, apagar zera, o do KV volta ao KV), a conta do
desvio (a linha mais larga fica no lugar, as outras vao a borda esquerda, ao meio ou a borda direita), a camada e a
entrada do render com a justificacao nova e a matriz andada, a caixa do texto editado com o alinhamento, as chaves da
medida, a edicao no palco (nenhuma caixa anda), a frase da diferenca e os esquemas do rascunho e do briefing."""
import copy
import re

import pytest
from jsonschema.validators import validator_for

from vapt import contratos
from vapt.derivacao import diferenca
from vapt.derivacao import quebras as mq
from vapt.fontes import medicao
from vapt.render import derivado as rd
from vapt.render import texto as rt
from vapt.tela import atos as ta
from vapt.tela import edicao
from vapt.tela import rascunho

EL = 'el1'


def _camada(just='LEFT', paragrafos=None, matriz=(2.0, 0.0, 0.0, 2.0, 100.0, 50.0), caixa='ponto'):
    pars = paragrafos if paragrafos is not None else [{'inicio': 0, 'fim': 7, 'justificacao': just,
                                                        'auto_leading_fator': 1.2}]
    t = {'conteudo': 'HH\rHHH', 'matriz': list(matriz), 'tipo_caixa': caixa, 'justificacao': just,
         'box_bounds': None, 'paragrafos': pars,
         'runs': [{'inicio': 0, 'fim': 6, 'texto': 'HH\rHHH', 'tem_tinta': True, 'fonte_ps': 'X',
                   'corpo_espaco_texto': 25.0, 'autoleading': True, 'tracking': 0}]}
    return {'identidade': {'layer_id': 7}, 'tipo': 'texto', 'texto': t}


# a pagina de medida falsa: duas linhas (HH e HHH) de avanco 34 e 51 no espaco do texto, na escala 2 da pagina, com
# 1 px de espacamento do ultimo caractere (que o Photoshop nao conta)
ITEM = {'escala': 2.0, 'linhas': [{'id': 'l0_0', 'ls_ultimo_px': 1.0}, {'id': 'l0_1', 'ls_ultimo_px': 1.0}]}
LARGURAS = {'l0_0': 69.0, 'l0_1': 103.0}
# a tinta de cada linha a partir do inicio dela: 1 px de cada lado dentro do avanco
TINTAS = {'l0_0': [2.0, 66.0, 30.0, 4.0], 'l0_1': [2.0, 100.0, 30.0, 4.0]}


# ------------------------------------------------------------------ a edicao
def test_alinhamento_editado_vale_o_ultimo_e_apagar_zera():
    eds = [{'elemento': EL, 'acao': 'alinhar_texto', 'alinhamento': 'direita'},
           {'elemento': 'el2', 'acao': 'alinhar_texto', 'alinhamento': 'centro'},
           {'elemento': EL, 'acao': 'mover', 'dx': 0.1, 'dy': 0},
           {'elemento': EL, 'acao': 'alinhar_texto', 'alinhamento': 'centro'}]
    assert mq.alinhamento_editado(eds, EL) == 'centro'
    assert mq.alinhamento_editado(eds, 'el3') is None and mq.alinhamento_editado(eds, None) is None
    assert mq.alinhamento_editado(eds + [{'elemento': EL, 'acao': 'apagar'}], EL) is None


MISTA = [{'inicio': 0, 'fim': 3, 'justificacao': 'RIGHT'}, {'inicio': 3, 'fim': 7, 'justificacao': 'LEFT'}]


def test_alinhamento_do_kv_e_o_das_linhas_e_none_no_texto_misto():
    assert mq.alinhamento_do_kv(_camada('CENTER')) == 'centro'
    assert mq.alinhamento_do_kv(_camada('RIGHT')) == 'direita'
    # a justificacao JUSTIFY_* o render desenha pelo inicio, e o palco a mostra a esquerda
    assert mq.alinhamento_do_kv(_camada('JUSTIFY_ALL')) == 'esquerda'
    # revisao 0.12.0: paragrafos de alinhamentos diferentes nao tem um alinhamento do KV (nenhum botao marcado)
    assert mq.alinhamento_do_kv(_camada(paragrafos=copy.deepcopy(MISTA))) is None
    # o paragrafo sem texto (o ultimo \r) nao conta
    so_o_fim = [{'inicio': 0, 'fim': 6, 'justificacao': 'CENTER'}, {'inicio': 6, 'fim': 7, 'justificacao': 'LEFT'}]
    assert mq.alinhamento_do_kv(_camada(paragrafos=so_o_fim)) == 'centro'
    # sem paragrafos, como o render e o palco desenham: a esquerda (render.texto.linhas_da_camada, estado.pecas_base)
    assert mq.alinhamento_do_kv(_camada('CENTER', paragrafos=[])) == 'esquerda'
    # no texto editado, o do paragrafo do primeiro trecho com tinta, que o render leva ao texto novo inteiro
    assert mq.alinhamento_do_kv(_camada(paragrafos=copy.deepcopy(MISTA)), editado=True) == 'direita'


def test_alinhamento_do_kv_de_novo_volta_ao_kv():
    kv = _camada('CENTER')
    ed = [{'elemento': EL, 'acao': 'alinhar_texto', 'alinhamento': 'direita'}]
    assert mq.alinhamento_efetivo(ed, EL, kv) == 'direita'
    assert mq.alinhamento_efetivo(ed + [dict(ed[0], alinhamento='centro')], EL, kv) is None
    assert mq.alinhamento_efetivo([], EL, kv) is None


@pytest.mark.parametrize('valor', ['esquerda', 'centro', 'direita'])
def test_no_texto_misto_toda_escolha_vale(valor):
    # revisao 0.12.0: o alinhamento do primeiro paragrafo tambem leva todas as linhas a ele
    mista = _camada(paragrafos=copy.deepcopy(MISTA))
    assert mq.alinhamento_efetivo([{'elemento': EL, 'acao': 'alinhar_texto', 'alinhamento': valor}], EL, mista) == valor


# ------------------------------------------------------------------ a conta: a linha mais larga fica no lugar
def test_bloco_das_linhas_sem_o_espacamento_do_ultimo_caractere():
    assert medicao.bloco_das_linhas(ITEM, LARGURAS, 'LEFT') == pytest.approx({'esq': 0.0, 'dir': 51.0})
    assert medicao.bloco_das_linhas(ITEM, LARGURAS, 'CENTER') == pytest.approx({'esq': -25.5, 'dir': 25.5})
    assert medicao.bloco_das_linhas(ITEM, LARGURAS, 'RIGHT') == pytest.approx({'esq': -51.0, 'dir': 0.0})
    # uma justificacao por linha (paragrafos de alinhamentos diferentes): a linha mais larga onde a justificacao dela
    # a poe (revisao 0.12.0: a uniao das linhas levaria a mais larga junto)
    assert medicao.bloco_das_linhas(ITEM, LARGURAS, {'l0_0': 'RIGHT', 'l0_1': 'LEFT'}) == \
        pytest.approx({'esq': 0.0, 'dir': 51.0})
    assert medicao.bloco_das_linhas(ITEM, LARGURAS, {'l0_0': 'LEFT', 'l0_1': 'CENTER'}) == \
        pytest.approx({'esq': -25.5, 'dir': 25.5})
    assert medicao.bloco_das_linhas(ITEM, {'l0_0': 69.0}, 'LEFT') is None
    # na mesma largura, a primeira linha
    iguais = {'l0_0': 103.0, 'l0_1': 103.0}
    assert medicao.bloco_das_linhas(ITEM, iguais, {'l0_0': 'RIGHT', 'l0_1': 'LEFT'}) == \
        pytest.approx({'esq': -51.0, 'dir': 0.0})


def test_tinta_do_bloco_por_linha_igual_ao_texto():
    um = medicao.tinta_do_bloco(ITEM, LARGURAS, TINTAS, 'RIGHT')
    assert medicao.tinta_do_bloco(ITEM, LARGURAS, TINTAS, {'l0_0': 'RIGHT', 'l0_1': 'RIGHT'}) == um
    assert um['esq'] == pytest.approx(-50.0) and um['dir'] == pytest.approx(-1.0)


@pytest.mark.parametrize('antes', ['LEFT', 'CENTER', 'RIGHT'])
@pytest.mark.parametrize('nova', ['LEFT', 'CENTER', 'RIGHT'])
def test_desvio_deixa_a_linha_mais_larga_no_lugar(antes, nova):
    f = mq.FRACAO_DA_JUSTIFICACAO
    bloco = medicao.bloco_das_linhas(ITEM, LARGURAS, antes)
    d = mq.desvio(bloco, nova)
    avancos = [34.0, 51.0]
    # o inicio de cada linha a partir da ancora de antes: antes e depois do alinhamento novo
    inicio_antes = [-f[antes] * a for a in avancos]
    inicio_depois = [d - f[nova] * a for a in avancos]
    assert inicio_depois[1] == pytest.approx(inicio_antes[1])  # a linha mais larga nao anda
    esq, dir_ = inicio_antes[1], inicio_antes[1] + avancos[1]
    curta = {'LEFT': esq, 'CENTER': (esq + dir_) / 2 - avancos[0] / 2, 'RIGHT': dir_ - avancos[0]}[nova]
    assert inicio_depois[0] == pytest.approx(curta)


@pytest.mark.parametrize('curta,larga', [('CENTER', 'LEFT'), ('RIGHT', 'LEFT'), ('LEFT', 'CENTER'),
                                         ('LEFT', 'RIGHT'), ('RIGHT', 'CENTER')])
@pytest.mark.parametrize('nova', ['LEFT', 'CENTER', 'RIGHT'])
def test_desvio_no_texto_misto_deixa_a_linha_mais_larga_no_lugar(curta, larga, nova):
    # revisao 0.12.0: HH (a curta) e HHH (a mais larga) em paragrafos de alinhamentos diferentes. A mais larga nao
    # anda, e a curta vai a borda esquerda, ao meio ou a borda direita dela (o exemplo da revisao: a curta ao centro e
    # a larga a esquerda, com a esquerda, levava a larga meia curta para a esquerda)
    f = mq.FRACAO_DA_JUSTIFICACAO
    d = mq.desvio(medicao.bloco_das_linhas(ITEM, LARGURAS, {'l0_0': curta, 'l0_1': larga}), nova)
    a_curta, a_larga = 34.0, 51.0
    ini_larga = -f[larga] * a_larga
    assert d - f[nova] * a_larga == pytest.approx(ini_larga)
    esperado = {'LEFT': ini_larga, 'CENTER': ini_larga + (a_larga - a_curta) / 2,
                'RIGHT': ini_larga + a_larga - a_curta}[nova]
    assert d - f[nova] * a_curta == pytest.approx(esperado)


def test_camada_alinhada_troca_todos_os_paragrafos_e_anda_a_matriz():
    mista = _camada(paragrafos=[{'inicio': 0, 'fim': 3, 'justificacao': 'CENTER'},
                                {'inicio': 3, 'fim': 7, 'justificacao': 'LEFT'}])
    c = mq.camada_alinhada(mista, 'RIGHT', 25.5)
    assert [p['justificacao'] for p in c['texto']['paragrafos']] == ['RIGHT', 'RIGHT']
    assert c['texto']['matriz'] == pytest.approx([2.0, 0.0, 0.0, 2.0, 151.0, 50.0])
    assert mista['texto']['paragrafos'][0]['justificacao'] == 'CENTER'  # a camada do laudo nao muda
    vazia = mq.camada_alinhada(_camada(paragrafos=[]), 'CENTER', 0)
    assert vazia['texto']['paragrafos'] == [{'inicio': 0, 'fim': 7, 'justificacao': 'CENTER'}]
    # a linha leva a justificacao nova no render
    assert {ln['just'] for ln in rt.linhas_da_camada(c['texto'])} == {'RIGHT'}


def test_caixa_do_editado_com_o_alinhamento_fica_no_lugar_da_linha_mais_larga():
    sint = mq.camada_do_editado(_camada('LEFT'), ['HH', 'HHH'])
    antes = mq.caixa_do_editado(sint, medicao.tinta_do_bloco(ITEM, LARGURAS, TINTAS, 'LEFT'), {})
    d = mq.desvio(medicao.bloco_das_linhas(ITEM, LARGURAS, 'LEFT'), 'RIGHT')
    depois = mq.caixa_do_editado(mq.camada_alinhada(sint, 'RIGHT', d),
                                 medicao.tinta_do_bloco(ITEM, LARGURAS, TINTAS, 'RIGHT'), {})
    # a linha mais larga define as bordas da tinta: a caixa e a mesma
    assert depois == pytest.approx(antes)


def test_justificacoes_das_linhas_pela_conta_do_render():
    mista = _camada(paragrafos=[{'inicio': 0, 'fim': 3, 'justificacao': 'CENTER'},
                                {'inicio': 3, 'fim': 7, 'justificacao': 'RIGHT'}])
    assert mq.justificacoes_das_linhas(mista, ITEM) == {'l0_0': 'CENTER', 'l0_1': 'RIGHT'}


def test_chaves_da_medida_separam_o_alinhamento():
    assert mq.chave_editado(7, ['A']) == mq.chave_editado(7, ['A'], None)
    assert re.fullmatch(r'ed:7:[0-9a-f]{64}', mq.chave_editado(7, ['A']))
    assert mq.chave_editado(7, ['A'], 'RIGHT') != mq.chave_editado(7, ['A'], 'LEFT') != mq.chave_editado(7, ['A'])
    assert mq.chave_alinhado(7, [1, 0], [], 'RIGHT') == 'al:7:0,1::RIGHT'
    assert mq.chave_alinhado(7, [0], [], 'RIGHT') != mq.chave_alinhado(7, [0], [], 'CENTER')


# ------------------------------------------------------------------ o render
def _entrada(just='LEFT'):
    runs = [{'inicio': 0, 'fim': 6, 'texto': 'HH\rHHH', 'fonte_ps': 'X', 'corpo_espaco_texto': 25.0, 'tracking': 0}]
    return {'id': 'e01', 'regiao': [0, 0, 300, 200], 'cores': ['c0'], 'cores_por_trecho': {'0': 'c0'},
            'texto': {'matriz': [2.0, 0.0, 0.0, 2.0, 40.0, 120.0], 'runs': runs,
                      'paragrafos': [{'inicio': 0, 'fim': 7, 'justificacao': just}]}}


@pytest.mark.parametrize('nova,ancora', [('CENTER', 'middle'), ('RIGHT', 'end')])
def test_alinhar_na_entrada_troca_a_justificacao_e_anda_a_origem(nova, ancora):
    face = {'id': 'f01', 'peso_declarado': 400, 'metricas': None}
    d = mq.desvio({'esq': 0.0, 'dir': 51.0}, nova)
    e = _entrada()
    novo = rd.alinhar_na_entrada(e, {'layer_id': 7, 'justificacao': nova, 'desvio': d})
    assert e['texto']['matriz'][4] == 40.0  # a entrada de antes fica igual
    assert novo['texto']['matriz'] == pytest.approx([2.0, 0.0, 0.0, 2.0, 40.0 + 2.0 * d, 120.0])
    assert novo['alinhamento_do_da'] == {'justificacao': nova, 'desvio': d}
    svg, _spans, _l = rt.montar_svg(novo, {'X': face}, 'p')
    # as duas linhas na ancora nova, na origem andada (a pagina do texto nao muda)
    assert svg.count('text-anchor="%s"' % ancora) == 2
    assert 'matrix(2.0000000000 0.0000000000 0.0000000000 2.0000000000 %.6f 120.000000)' % (40.0 + 2.0 * d) in svg
    assert _vale(novo['alinhamento_do_da'], _esquema_da_entrada())


def _vale(dados, esquema):
    return not list(validator_for(esquema)(esquema).iter_errors(dados))


def _esquema_da_entrada():
    return contratos.carregar_esquema('composicao/1')['properties']['entradas']['items']['properties'][
        'alinhamento_do_da']


def test_caixa_validada_do_texto_alinhado_e_a_medida():
    tr = {'s': 0.5, 'origem_doc': [0, 0], 'destino': [10, 10], 'recorte_doc': [0, 0, 100, 100]}
    el = {'transformacao': tr, 'alinhamento_do_da': {'alinhamento': 'direita', 'camadas': [
        {'layer_id': 7, 'justificacao': 'RIGHT', 'desvio': 51.0, 'caixa_doc': [20, 20, 60, 40]}]}}
    assert rd.caixa_validada_do_texto(el, 7, [0, 0, 1, 1]) == pytest.approx([20, 20, 40, 30])
    # sem a caixa medida, a de antes
    el['alinhamento_do_da']['camadas'][0].pop('caixa_doc')
    assert rd.caixa_validada_do_texto(el, 7, [0, 0, 40, 40]) == pytest.approx([10, 10, 30, 30])


def test_render_sem_desvio_desenha_como_o_kv_com_registro():
    el = {'id': EL, 'alinhamento_do_da': {'alinhamento': 'direita', 'camadas': [{'layer_id': 7,
                                                                                  'justificacao': 'RIGHT'}]}}
    regs = []
    e = _entrada()
    assert rd._com_alinhamento(e, el, 7, regs) is e
    assert [r['codigo'] for r in regs] == ['texto_alinhado_sem_medida']
    el['alinhamento_do_da']['camadas'][0]['desvio'] = 51.0
    novo = rd._com_alinhamento(e, el, 7, regs)
    assert regs[-1]['codigo'] == 'texto_alinhado_pelo_da' and novo['texto']['paragrafos'][0]['justificacao'] == 'RIGHT'
    assert rd._com_alinhamento(e, {'id': EL}, 7, regs) is e


# ------------------------------------------------------------------ a edicao no palco
def test_aplicar_e_editar_nao_mexem_em_caixa_nenhuma():
    caixas = {EL: [10, 10, 50, 30], 'el2': [60, 10, 90, 30]}
    eds = [{'elemento': EL, 'acao': 'alinhar_texto', 'alinhamento': 'direita'}]
    c, ap, tx, mx = edicao.aplicar(caixas, eds, 100, 100)
    assert c == {k: [float(v) for v in x] for k, x in caixas.items()} and ap == [] and tx == {} and mx == []
    atual, ap, tx, mx, al = edicao.editar(caixas, eds + [{'elemento': 'el9', 'acao': 'alinhar_texto',
                                                          'alinhamento': 'centro'}], 100, 100)
    assert atual == c and mx == [] and al == []
    # o elemento apagado nao leva alinhamento
    c2, ap2, _t, _m = edicao.aplicar(caixas, [{'elemento': EL, 'acao': 'apagar'}] + eds, 100, 100)
    assert ap2 == [EL] and EL not in c2
    assert edicao.membros(eds[0]) == [EL] and edicao.grupos(eds) == [] and edicao.escalas(eds) == {}
    assert edicao.intencoes(eds) == []


def test_alinhar_texto_no_palco_so_no_elemento():
    palco = {'pecas': [{'elemento': EL, 'tipo': 'texto', 'linhas': [{}], 'alinhamento': 'centro'},
                       {'elemento': 'el2', 'tipo': 'texto', 'linhas': [{}], 'alinhamento': 'centro'},
                       {'elemento': EL, 'tipo': 'imagem'}]}
    edicao.alinhar_texto(palco, EL, 'direita')
    assert palco['pecas'][0] == {'elemento': EL, 'tipo': 'texto', 'linhas': [{}], 'alinhamento': 'direita',
                                 'alinhamento_kv': 'centro'}
    assert 'alinhamento_kv' not in palco['pecas'][1] and palco['pecas'][2] == {'elemento': EL, 'tipo': 'imagem'}
    # a segunda vez guarda o do KV de antes
    edicao.alinhar_texto(palco, EL, 'esquerda')
    assert palco['pecas'][0]['alinhamento_kv'] == 'centro' and palco['pecas'][0]['alinhamento'] == 'esquerda'


def test_alinhar_texto_leva_o_alinhamento_de_cada_linha_do_kv():
    # revisao 0.12.0: a pagina poe a linha mais larga onde o KV a poe, linha a linha (o texto misto)
    linhas = [{}, {}]
    palco = {'pecas': [{'elemento': EL, 'camada': 7, 'tipo': 'texto', 'linhas': linhas, 'alinhamento': 'direita'},
                       {'elemento': EL, 'camada': 8, 'tipo': 'texto', 'linhas': [{}], 'alinhamento': 'esquerda',
                        'texto_editado': True}]}
    edicao.alinhar_texto(palco, EL, 'centro', {7: ['RIGHT', 'JUSTIFY_ALL'], 8: ['LEFT']})
    assert palco['pecas'][0]['alinhamento_kv_linhas'] == ['direita', 'esquerda']
    # o texto editado leva o alinhamento do KV inteiro (alinhamento_kv), sem as linhas do KV
    assert 'alinhamento_kv_linhas' not in palco['pecas'][1]
    # a conta errada (outro numero de linhas) fica de fora
    outro = {'pecas': [{'elemento': EL, 'camada': 7, 'tipo': 'texto', 'linhas': [{}], 'alinhamento': 'direita'}]}
    edicao.alinhar_texto(outro, EL, 'centro', {7: ['RIGHT', 'LEFT']})
    assert 'alinhamento_kv_linhas' not in outro['pecas'][0]


def test_justificacoes_no_formato_pelas_linhas_do_render():
    from vapt.tela import estado
    c = _camada(paragrafos=copy.deepcopy(MISTA))
    peca = {'camada': 7, '_texto': c['texto'], '_faces': {'X': 'f01'}, 'linhas': [{}, {}]}
    assert estado.justificacoes_no_formato(peca, {'id': EL}) == ['RIGHT', 'LEFT']
    # a quebra inserida na mestre propria: HHH vira duas linhas, as duas no paragrafo dele
    el = {'id': EL, 'quebras': [4], 'quebras_camada': 7}
    assert estado.justificacoes_no_formato(peca, el) == ['RIGHT', 'LEFT', 'LEFT']


# ------------------------------------------------------------------ a frase da diferenca
def test_diferenca_diz_o_alinhamento_em_palavras():
    a = {'id': EL, 'funcao': 'titulo', 'caixa': [0, 0, 1, 1]}
    b = dict(a, alinhamento_do_da={'alinhamento': 'direita', 'camadas': [{'layer_id': 7, 'justificacao': 'RIGHT',
                                                                          'desvio': 51.0}]})
    [x] = diferenca._do_elemento(EL, a, b, None)
    assert x['tipo'] == 'alinhamento' and x['frase'].startswith('Você alinhou o texto') and 'à direita' in x['frase']
    [y] = diferenca._do_elemento(EL, b, a, None)
    assert y['tipo'] == 'alinhamento' and 'voltou ao do KV' in y['frase']
    # o desvio medido de novo nao e mudanca do DA
    c = copy.deepcopy(b)
    c['alinhamento_do_da']['camadas'][0]['desvio'] = 51.5
    assert [i['tipo'] for i in diferenca._do_elemento(EL, b, c, None)] == ['detalhe']
    for frase in (x['frase'], y['frase'], ta.MOTIVOS_DO_SALVAR['alinhamento_recusado'], edicao.TEXTO_EM_CAIXA,
                  edicao.TEXTO_SEM_UM_TEXTO_PARA_ALINHAR, edicao.TEXTO_ALINHAR_SEM_FONTE):
        assert '—' not in frase and '–' not in frase and not re.search(r'não é .*, é ', frase), frase
    assert 'alinhamento_recusado' in ta.ORDEM_DO_SALVAR


# ------------------------------------------------------------------ os esquemas
def _rascunho(edicoes):
    return {'esquema': rascunho.ESQUEMA, 'job_id': '0' * 32, 'laudo_sha256': '0' * 64, 'origem': 'rascunho',
            'atualizado_em': '2026-11-21T10:00:00',
            'familias': {'g1': {'versao': None, 'confirmada': False, 'edicoes': edicoes}}}


@pytest.mark.parametrize('ed,vale', [
    ({'elemento': EL, 'acao': 'alinhar_texto', 'alinhamento': 'direita'}, True),
    ({'elemento': EL, 'acao': 'alinhar_texto'}, False),
    ({'elemento': EL, 'acao': 'alinhar_texto', 'alinhamento': 'justificado'}, False),
    ({'elemento': EL, 'acao': 'alinhar_texto', 'alinhamento': 'centro', 'elementos': [EL, 'el2']}, False),
    ({'elemento': EL, 'acao': 'texto', 'texto': 'A', 'alinhamento': 'centro'}, False),
])
def test_esquemas_do_rascunho_e_do_briefing(ed, vale):
    try:
        contratos.validar(_rascunho([ed]), rascunho.ESQUEMA)
        ok = True
    except contratos.ErroContrato:
        ok = False
    assert ok is vale
    item = contratos.carregar_esquema('briefing/1')['properties']['composicoes']['items']['properties']['edicoes'][
        'items']
    assert _vale(ed, item) is vale
