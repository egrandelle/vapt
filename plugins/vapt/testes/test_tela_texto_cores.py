# -*- coding: utf-8 -*-
"""Decisao 214: o texto editado no palco fica com as cores do KV (relato do Duda: o texto de tres linhas, as duas
primeiras pretas e a ultima azul, ficava todo preto em qualquer edicao, ate so mudando a quebra pelo campo de texto).

Criterios de pronto cobertos aqui:
  - trocar_texto tira o estilo de cada caractere dos runs do KV (a peca base), pela regra por palavra
    (derivacao.quebras.runs_do_editado): so o Enter e a quebra da familia sobre o texto editado mantem o azul na
    ultima linha; a palavra azul trocada fica azul; o corpo de cada trecho vai na escala do formato; a linha vazia
    leva o estilo do vizinho;
  - as linhas do palco nao servem de base: com a quebra da familia elas ja tem posicoes do texto editado;
  - o KV de um estilo so da o mesmo palco de antes (o hash da familia confirmada nao muda), menos quando um espaco ou
    uma quebra sem tinta tem outro corpo ou fonte e continua no mesmo papel: o palco, a medida e o render seguem o KV
    nele (derivacao.quebras._no_mesmo_papel, rodada 4);
  - o texto igual ao do KV sai com os runs do KV no palco, na medida e no render, mesmo com um espaco sem tinta de
    outra fonte;
  - Editor._texto confere cada caractere na face do trecho dele, com a caixa alta desse trecho;
  - ponta a ponta: a previa da familia (Editor.previa) num PSD de tres linhas e duas cores leva o azul ao palco;
  - o vao igual ao do KV entre duas palavras pareadas fica com o run do KV: trocar a palavra de outra linha nao muda
    a entrelinha da linha 2 (o CR dela e do run da linha 3), no palco, na medida e no render;
  - o respiro: no KV de varios estilos, a quebra sem tinta que continua quebra guarda o corpo dela (a linha vazia de
    corpo menor entre paragrafos), no palco, na medida e no render, e a linha vazia leva o estilo do trecho com tinta
    antes dela; a regra nao olha a cor (o ColorOverlay e o alfa, que o contrato do render guarda de outro jeito que o
    laudo, dao o mesmo respiro); o DA pode por ou tirar linhas vazias (o vao so de quebras alinha a primeira, a ultima
    e a do meio do KV); a medida (medir_editados, no Chromium) confere a face so dos trechos com tinta, e a quebra sem
    tinta numa face fora do job abre a linha dela na pagina de medida (fontes.medicao.montar);
  - a ancora do texto editado no KV de varios estilos: ancora_kv leva os trechos da linha do KV, e a pagina mede a
    subida nas faces e corpos deles (a linha de base do texto editado cai na do KV, como no motor); a linha e a do PSD,
    sem a quebra da familia, em todo KV (rodada 5: tambem no de um estilo so, com o CR do comeco juntado ou a quebra
    inserida no espaco da linha); no KV de um estilo so, a pagina mede a subida no primeiro trecho com texto visivel
    (o espaco sem tinta do comeco pode ter outro corpo), e a linha de base bate com a do motor;
  - o vao do comeco (as linhas vazias antes da primeira palavra) guarda os runs do KV quando a primeira palavra pareia
    (rodada 5), e o Enter posto no comeco de um KV sem linha vazia herda a primeira palavra;
  - o espaco sem tinta numa fonte sem face no job e desenhado na face do vizinho com face, no palco, na medida e no
    render, no KV sem edicao e no editado (casamento.vizinho_com_face, rodada 5); a quebra sem tinta numa fonte fora
    do job continua guardando a entrelinha dela; rodada 6: o vizinho tem tinta e vem da mesma linha (o CR de outro
    corpo nao serve), igual nas tres camadas; o kerning 0.0 do laudo junta o espaco no tspan do vizinho no render, como
    na medida; a caixa de paragrafo com o espaco sem face quebra no espaco (render.texto.quebras_da_caixa);
  - a caixa de paragrafo: ancora_kv['caixa'] e quanto a primeira linha de base do texto editado desce em relacao a do
    KV pela ascendente da face da primeira linha (render.texto.origem_das_linhas), so quando nao e zero e quando a
    primeira linha do KV tem as metricas das faces dela;
  - o KV que comeca com uma quebra (a primeira linha do palco sem trecho) nao quebra trocar_texto.
Tudo sintetico: os runs feitos aqui e o PSD com a fonte de autoteste do motor."""
import copy
import json
import sys

import pytest

from vapt.derivacao import quebras as mq
from vapt.render import derivado as rd
from vapt.render import texto as rt
from vapt.tela import edicao
from vapt.tela import estado as te

PRETO, AZUL = '#000000', '#0000FF'
ESCALA = 0.5
FACES = {'X': 'fx', 'Y': 'fy'}


def _run(inicio, texto, cor, fonte='X', corpo=20.0, **extra):
    r = {'inicio': inicio, 'fim': inicio + len(texto), 'texto': texto, 'tem_tinta': bool(texto.strip()),
         'fonte_ps': fonte, 'cor_hex': cor, 'corpo_efetivo': corpo, 'corpo_espaco_texto': corpo / 2.0,
         'autoleading': True, 'tracking': 0, 'kerning': None}
    r.update(extra)
    return r


def _texto_kv(runs):
    conteudo = ''.join(r['texto'] for r in runs)
    return {'conteudo': conteudo, 'matriz': [2.0, 0.0, 0.0, 2.0, 0.0, 0.0], 'runs': runs,
            'paragrafos': [{'inicio': 0, 'fim': len(conteudo) + 1, 'justificacao': 'LEFT', 'auto_leading_fator': 1.2}]}


def _tres_linhas(corpo_azul=20.0, fonte_azul='X'):
    # o KV do relato: 'L1 a' e 'L2 b' pretas, 'L3 C' azul
    return _texto_kv([_run(0, 'L1 a\rL2 b\r', PRETO), _run(10, 'L3 C', AZUL, fonte=fonte_azul, corpo=corpo_azul)])


def _palco(texto_kv, linhas=None):
    """O palco com a peca de texto como estado._peca_no_formato a monta (o corpo e a entrelinha na escala), e as
    pecas base ({layer_id: peca})."""
    base = {7: {'camada': 7, '_texto': texto_kv, '_faces': dict(FACES)}}
    linhas = te._linhas(texto_kv, FACES.get) if linhas is None else linhas
    p = {'elemento': 'el1', 'tipo': 'texto', 'camada': 7, 'recorte': [0, 0, 1, 1],
         'linhas': [{'trechos': [dict(t, corpo=te._arred(t['corpo'] * ESCALA)) for t in ln['trechos']],
                     'entrelinha': None if ln['entrelinha'] is None else te._arred(ln['entrelinha'] * ESCALA)}
                    for ln in linhas]}
    return {'largura': 100, 'altura': 100, 'pecas': [p]}, base


def _trocar(texto_kv, texto, quebra=None, com_base=True):
    palco, base = _palco(texto_kv)
    if com_base:
        return edicao.trocar_texto(palco, 'el1', texto, quebra, base=base, escala=ESCALA)['pecas'][0]
    return edicao.trocar_texto(palco, 'el1', texto, quebra)['pecas'][0]


def _cores(p):
    return [[(t['texto'], t['cor']) for t in ln['trechos']] for ln in p['linhas']]


# ------------------------------------------------------------------ trocar_texto
def test_so_o_enter_mantem_o_azul_na_ultima_linha():
    p = _trocar(_tres_linhas(), 'L1 a L2 b\nL3 C')
    assert _cores(p) == [[('L1 a L2 b', PRETO)], [('L3 C', AZUL)]]
    # o mesmo texto do KV, com as mesmas quebras
    assert _cores(_trocar(_tres_linhas(), 'L1 a\nL2 b\nL3 C')) == [[('L1 a', PRETO)], [('L2 b', PRETO)],
                                                                    [('L3 C', AZUL)]]


def test_juntar_a_linha_azul_deixa_o_azul_so_nas_palavras_dela():
    p = _trocar(_tres_linhas(), 'L1 a\nL2 b L3 C')
    assert _cores(p) == [[('L1 a', PRETO)], [('L2 b ', PRETO), ('L3 C', AZUL)]]


@pytest.mark.parametrize('texto,quebra,linhas', [
    # o texto editado so com Enter, e a quebra da familia junta a segunda quebra dele
    ('L1 a\nL2 b\nL3 C', {'manter': [0], 'inseridas': []}, ['L1 a', 'L2 b L3 C']),
    # o texto editado numa linha so, e a quebra da familia insere a quebra de volta nos espacos
    ('L1 a L2 b L3 C', {'manter': [], 'inseridas': [4, 9]}, ['L1 a', 'L2 b', 'L3 C']),
    # o texto editado em duas linhas, e a familia insere uma
    ('L1 a L2 b\nL3 C', {'manter': [0], 'inseridas': [4]}, ['L1 a', 'L2 b', 'L3 C']),
])
def test_quebra_da_familia_sobre_o_texto_editado_mantem_o_azul(texto, quebra, linhas):
    p = _trocar(_tres_linhas(), texto, quebra)
    assert [''.join(t['texto'] for t in ln['trechos']) for ln in p['linhas']] == linhas
    azul = [t['texto'] for ln in p['linhas'] for t in ln['trechos'] if t['cor'] == AZUL]
    assert ''.join(azul) == 'L3 C' and p['linhas'][-1]['trechos'][-1]['cor'] == AZUL


def test_as_linhas_do_palco_com_a_quebra_aplicada_nao_sao_a_base():
    # as linhas do palco vem com a quebra da familia aplicada no texto do KV com posicoes do texto editado
    # (estado._linhas_no_formato): aqui, tudo numa linha preta. O estilo sai dos runs do KV
    kv = _tres_linhas()
    falsas = [{'trechos': [{'texto': 'L1 a L2 b L3 C', 'fonte_ps': 'X', 'face': 'fx', 'cor': PRETO, 'corpo': 20.0,
                            'tracking': 0}], 'entrelinha': 24.0}]
    palco, base = _palco(kv, falsas)
    p = edicao.trocar_texto(palco, 'el1', 'L1 a\nL2 b\nL3 C', {'manter': [0, 1], 'inseridas': []}, base=base,
                            escala=ESCALA)['pecas'][0]
    assert _cores(p) == [[('L1 a', PRETO)], [('L2 b', PRETO)], [('L3 C', AZUL)]]


def test_trocar_a_palavra_azul_fica_azul():
    p = _trocar(_tres_linhas(), 'L1 a\nL2 b\nL3 Z')
    assert _cores(p) == [[('L1 a', PRETO)], [('L2 b', PRETO)], [('L3 Z', AZUL)]]
    # a palavra nova no fim da linha azul herda a vizinha da esquerda
    assert _cores(_trocar(_tres_linhas(), 'L1 a\nL2 b\nL3 C D'))[-1] == [('L3 C D', AZUL)]


def test_cada_trecho_leva_o_corpo_e_a_face_dele_na_escala_do_formato():
    p = _trocar(_tres_linhas(corpo_azul=30.0, fonte_azul='Y'), 'L1 a L2 b\nL3 C')
    [preto], [azul] = (ln['trechos'] for ln in p['linhas'])
    assert (preto['corpo'], preto['face'], preto['fonte_ps']) == (10.0, 'fx', 'X')
    assert (azul['corpo'], azul['face'], azul['fonte_ps']) == (15.0, 'fy', 'Y')
    assert list(azul) == ['texto', 'fonte_ps', 'face', 'cor', 'corpo', 'tracking']
    # cada linha com a entrelinha do render (a maior dos runs dela): a linha azul so tem o trecho azul (a quebra que
    # termina a linha 1 e do 'b' preto), entao leva a do corpo azul
    assert [ln['entrelinha'] for ln in p['linhas']] == [te._arred(1.2 * 10.0 * 2.0 * ESCALA),
                                                        te._arred(1.2 * 15.0 * 2.0 * ESCALA)]


def test_linha_vazia_leva_o_estilo_do_vizinho():
    p = _trocar(_tres_linhas(), 'L1 a\nL2 b\nL3 C\n')
    assert _cores(p)[-1] == [('', AZUL)]
    p = _trocar(_tres_linhas(), '\nL1 a\nL2 b\nL3 C')
    assert _cores(p)[0] == [('', PRETO)]


@pytest.mark.parametrize('texto', ['HAX O', 'HAX O\nHOAXAV', '\nHAX O', 'HAX O\n\nOX', 'OX VA HOX\n', 'novo'])
def test_kv_de_um_estilo_so_da_o_palco_de_antes(texto):
    # um run com tinta e a quebra do fim num run sem tinta, e dois runs que so mudam de kerning: o palco igual ao da
    # regra de antes (o estilo do primeiro trecho), byte a byte
    kvs = [_texto_kv([_run(0, 'HAX O\rHOAXAV', PRETO), _run(12, '\r', PRETO, tem_tinta=False)]),
           _texto_kv([_run(0, 'HAX O\r', PRETO, kerning=40), _run(6, 'HOAXAV', PRETO, kerning=-20)])]
    for kv in kvs:
        novo = _trocar(copy.deepcopy(kv), texto)
        antes = _trocar(copy.deepcopy(kv), texto, com_base=False)
        assert json.dumps(novo, sort_keys=True) == json.dumps(antes, sort_keys=True)
        assert json.dumps(novo) == json.dumps(antes)


def test_sem_base_fica_o_estilo_do_primeiro_trecho():
    p = _trocar(_tres_linhas(), 'L1 a L2 b\nL3 C', com_base=False)
    assert _cores(p) == [[('L1 a L2 b', PRETO)], [('L3 C', PRETO)]]


@pytest.mark.parametrize('fonte_do_cr', ['Y', 'Z'])
@pytest.mark.parametrize('texto', ['HAH HOX', 'HAH\nHOX', 'HAH novo HOX'])
def test_cr_do_meio_sem_tinta_de_outro_estilo_nao_vira_trecho_no_palco(texto, fonte_do_cr):
    # o KV preto na vista com a quebra do meio num run sem tinta azul de outra fonte e outro corpo (Z: a fonte que nem
    # esta no job): cada linha do palco tem um trecho so, preto, na face X (o run sem tinta nunca vira trecho)
    kv = _texto_kv([_run(0, 'HAH', PRETO), _run(3, '\r', AZUL, fonte=fonte_do_cr, corpo=80.0), _run(4, 'HOX', PRETO)])
    p = _trocar(copy.deepcopy(kv), texto)
    assert _cores(p) == [[(ln, PRETO)] for ln in texto.split('\n')]
    assert {(t['fonte_ps'], t['face'], t['corpo']) for ln in p['linhas'] for t in ln['trechos']} == {('X', 'fx', 10.0)}
    entrelinhas = [ln['entrelinha'] for ln in p['linhas']]
    assert entrelinhas == _entrelinhas_do_render(copy.deepcopy(kv), mq.linhas_editadas(texto)) == \
        _entrelinhas_no_render(copy.deepcopy(kv), texto)
    if '\n' in texto:
        # rodada 4: a quebra que continua quebra guarda o run sem tinta dela, e a linha 1 fica com a entrelinha do KV
        # (a do corpo 80 do CR), como o palco do KV
        palco_kv, _base = _palco(copy.deepcopy(kv))
        assert entrelinhas == [ln['entrelinha'] for ln in palco_kv['pecas'][0]['linhas']] == \
            [te._arred(1.2 * 40.0 * 2.0 * ESCALA), te._arred(1.2 * 10.0 * 2.0 * ESCALA)]
    else:
        # a quebra que vira espaco (ou fica fora do par) herda o vizinho com tinta: a entrelinha do corpo preto
        assert entrelinhas == [te._arred(1.2 * 10.0 * 2.0 * ESCALA)]


# ------------------------------------------------------------------ a entrelinha de cada linha, a do render
def _entrelinhas_do_render(texto_kv, linhas):
    # a medida e o render: as linhas da camada do texto editado (render.texto.linhas_da_camada sobre
    # derivacao.quebras.camada_do_editado), vezes a escala da matriz e a do formato, como estado._linhas e
    # estado._peca_no_formato
    m = texto_kv['matriz']
    sy = (float(m[2]) ** 2 + float(m[3]) ** 2) ** 0.5
    t = mq.camada_do_editado({'texto': texto_kv}, linhas)['texto']
    return [te._arred(te._arred(ln['entrelinha'] * sy) * ESCALA) for ln in rt.linhas_da_camada(t)]


def _quarenta_e_vinte_e_quatro():
    # as linhas pretas a 40 pt e a azul a 24 pt (o corpo no texto; a matriz dobra), entrelinha automatica (1,2)
    return _texto_kv([_run(0, 'L1 a\rL2 b\r', PRETO, corpo=80.0), _run(10, 'L3 C', AZUL, corpo=48.0)])


@pytest.mark.parametrize('texto,quebra,esperado', [
    # so a quebra mudou: a quebra que termina a linha 1 e do 'b' preto, e a linha azul fica so com o azul
    ('L1 a L2 b\nL3 C', None, [48.0, 28.8]),
    ('L1 a\nL2 b\nL3 C', None, [48.0, 48.0, 28.8]),
    # a linha azul juntada a preta: a maior das duas
    ('L1 a\nL2 b L3 C', None, [48.0, 48.0]),
    # a palavra nova no comeco da linha azul fica azul
    ('L1 a\nL2 b\nx L3 C', None, [48.0, 48.0, 28.8]),
    # a quebra da familia junta a segunda quebra do texto editado, e insere uma
    ('L1 a\nL2 b\nL3 C', {'manter': [0], 'inseridas': []}, [48.0, 48.0]),
    ('L1 a L2 b L3 C', {'manter': [], 'inseridas': [9]}, [48.0, 28.8]),
])
def test_entrelinha_de_cada_linha_e_a_do_render(texto, quebra, esperado):
    kv = _quarenta_e_vinte_e_quatro()
    p = _trocar(kv, texto, quebra)
    linhas = mq.linhas_editadas(texto) if quebra is None else mq.linhas_do_editado(texto, quebra['manter'],
                                                                                    quebra['inseridas'])
    assert [ln['entrelinha'] for ln in p['linhas']] == _entrelinhas_do_render(copy.deepcopy(kv), linhas) == esperado


@pytest.mark.parametrize('texto', ['HAX O HOAXAV', 'HAX O\nHOAXAV', 'HAX\nO\nHOAXAV\nnovo', 'HAX O\n\nOX'])
def test_entrelinha_do_kv_de_um_estilo_so_e_a_de_antes(texto):
    # o KV de um estilo so (40 pt, automatica, a quebra do fim num run sem tinta): a mesma entrelinha da regra de antes
    # (a da primeira linha do KV em todas) e a do render
    kv = _texto_kv([_run(0, 'HAX O\rHOAXAV', PRETO, corpo=80.0), _run(12, '\r', PRETO, corpo=80.0, tem_tinta=False)])
    novo = _trocar(copy.deepcopy(kv), texto)
    antes = _trocar(copy.deepcopy(kv), texto, com_base=False)
    assert [ln['entrelinha'] for ln in novo['linhas']] == [ln['entrelinha'] for ln in antes['linhas']] == \
        _entrelinhas_do_render(kv, mq.linhas_editadas(texto)) == [48.0] * len(texto.split('\n'))


# ------------------------------------------------------------------ o palco e o render: as mesmas cores por linha
COR_DE = {PRETO: 'c0', AZUL: 'c1'}


def _no_render(texto_kv, texto, quebra):
    """A entrada do contrato do render com o texto editado: a do KV (a cor fora do run, em cores_por_trecho),
    texto_editado_na_entrada com o item da familia e a quebra dela por posicao (quebras_do_texto_editado)."""
    runs = [{k: v for k, v in r.items() if k != 'cor_hex'} for r in texto_kv['runs']]
    entrada = {'id': 'e01', 'regiao': [0, 0, 100, 100],
               'texto': {'matriz': list(texto_kv['matriz']), 'runs': runs,
                         'paragrafos': copy.deepcopy(texto_kv['paragrafos'])},
               'cores': ['c0', 'c1'], 'cores_por_trecho': {str(r['inicio']): COR_DE[r['cor_hex']]
                                                           for r in texto_kv['runs']},
               'valores_cor': {'c0': {'rgb': [0, 0, 0], 'alfa': 1.0}, 'c1': {'rgb': [0, 0, 1], 'alfa': 1.0}},
               'faces': {'X': 'fx', 'Y': 'fy'}}
    item = None if quebra is None else {'aprovadas': quebra['manter'], 'inseridas': quebra['inseridas']}
    novo = rd.texto_editado_na_entrada(entrada, texto, item)
    el = {'texto_editado': texto, 'quebras': {'familia': [] if item is None else [dict(item, layer_id=7)]}}
    novo.update(rd.quebras_do_texto_editado(el, 7))
    return novo


def _linhas_do_render(novo):
    return rt.linhas_da_camada(novo['texto'], novo.get('quebras_inseridas') or (), novo.get('quebras_juntadas'))


def _entrelinhas_no_render(texto_kv, texto, quebra=None):
    """A entrelinha de cada linha que o render desenha (no espaco do texto), levada ao palco como estado._linhas e
    estado._peca_no_formato (a escala da matriz e a do formato)."""
    m = texto_kv['matriz']
    sy = (float(m[2]) ** 2 + float(m[3]) ** 2) ** 0.5
    return [te._arred(te._arred(ln['entrelinha'] * sy) * ESCALA)
            for ln in _linhas_do_render(_no_render(texto_kv, texto, quebra))]


def _cores_do_render(texto_kv, texto, quebra):
    """[[(texto, cor)] de cada linha] como o render desenha: a entrada do contrato com o texto editado (_no_render) e
    as linhas de render.texto.linhas_da_camada."""
    novo = _no_render(texto_kv, texto, quebra)
    hex_de = {v: k for k, v in COR_DE.items()}
    saida = []
    for ln in _linhas_do_render(novo):
        trechos = []
        for parte, r in ln['pedacos']:
            cor = hex_de[novo['cores_por_trecho'][str(r['inicio'])]]
            if trechos and trechos[-1][1] == cor:
                trechos[-1] = (trechos[-1][0] + parte, cor)
            else:
                trechos.append((parte, cor))
        saida.append(trechos)
    return saida


@pytest.mark.parametrize('texto,quebra', [
    # a familia junta a segunda quebra: NOVO fica na linha do 'b' (preto)
    ('L1 a\nL2 b\nNOVO L3 C', {'manter': [0], 'inseridas': []}),
    # a familia insere a quebra antes de NOVO: NOVO abre a linha azul (azul)
    ('L1 a\nL2 b NOVO L3 C', {'manter': [0], 'inseridas': [9]}),
    # o espaco no comeco da linha azul, com a quebra juntada
    ('L1 a\nL2 b\n L3 C', {'manter': [0], 'inseridas': []}),
    # so a quebra mudou, e sem quebra da familia
    ('L1 a L2 b\nL3 C', {'manter': [0], 'inseridas': [4]}),
    ('L1 a\nL2 b\nx L3 C', None),
])
def test_palco_e_render_dao_as_mesmas_cores_por_linha(texto, quebra):
    kv = _tres_linhas()
    palco = _cores(_trocar(copy.deepcopy(kv), texto, quebra))
    assert palco == _cores_do_render(kv, texto, quebra)
    # a cor de NOVO segue a linha final
    if 'NOVO' in texto:
        cor_novo = next(c for ln in palco for s, c in ln if 'NOVO' in s)
        assert cor_novo == (PRETO if quebra['inseridas'] == [] else AZUL)


# ------------------------------------------------------------------ Editor._texto
def _editor(texto_kv):
    ed = edicao.Editor.__new__(edicao.Editor)
    ed.kv_por_id = {'el1': {'id': 'el1', 'layer_ids': [7]}}
    linhas = te._linhas(texto_kv, FACES.get)
    ed.base = {7: {'camada': 7, 'linhas': linhas, '_texto': texto_kv, '_faces': dict(FACES)}}
    # fx: maiusculas, minusculas e algarismos; fy: so maiusculas e algarismos
    ed.faces = {'fx': {'id': 'fx', 'cmap': [[48, 57], [65, 90], [97, 122]]},
                'fy': {'id': 'fy', 'cmap': [[48, 57], [65, 90]]}}
    return ed


def test_texto_confere_cada_caractere_na_face_do_trecho_dele():
    ed = _editor(_tres_linhas(fonte_azul='Y'))
    # a minuscula nas linhas pretas (fx) passa
    assert ed._texto('el1', 'L1 xyz\nL2 b\nL3 C') == ('L1 xyz\nL2 b\nL3 C', None)
    # a minuscula na palavra azul (fy) e recusada
    texto, recusa = ed._texto('el1', 'L1 a\nL2 b\nL3 z')
    assert texto is None and ' z.' in recusa
    # o azul em caixa alta: a minuscula vira maiuscula e passa
    kv = _tres_linhas(fonte_azul='Y')
    kv['runs'][1]['font_caps'] = 'ALL_CAPS'
    assert _editor(kv)._texto('el1', 'L1 a\nL2 b\nL3 z')[1] is None


def test_texto_recusa_o_trecho_sem_face_no_job():
    ed = _editor(_tres_linhas(fonte_azul='Y'))
    del ed.faces['fy']
    texto, recusa = ed._texto('el1', 'L1 a\nL2 b\nL3 C')
    assert texto is None and 'não está no job' in recusa
    # o texto que so usa o trecho preto passa
    assert ed._texto('el1', 'L1 a')[1] is None


def test_texto_confere_a_palavra_inserida_nas_linhas_com_a_quebra_da_familia():
    # a azul (fy) sem minusculas: a palavra minuscula inserida no comeco da linha azul fica na face azul e e recusada;
    # com a quebra da familia que junta a linha azul a preta, ela fica depois do 'b' preto (fx) e passa, como o palco
    ed = _editor(_tres_linhas(fonte_azul='Y'))
    texto = 'L1 a\nL2 b\nnovo L3 C'
    assert ed._texto('el1', texto)[0] is None
    assert ed._texto('el1', texto, {'manter': [0], 'inseridas': []}) == (texto, None)
    # o inverso: o texto editado com a palavra na linha preta, e a familia insere a quebra antes dela
    texto = 'L1 a\nL2 b novo L3 C'
    assert ed._texto('el1', texto) == (texto, None)
    _t, recusa = ed._texto('el1', texto, {'manter': [0], 'inseridas': [9]})
    assert _t is None and ' n, o, v.' in recusa
    # a face conferida e a do trecho que o palco desenha com a mesma quebra
    p = _trocar(_tres_linhas(fonte_azul='Y'), texto, {'manter': [0], 'inseridas': [9]})
    assert next(t['face'] for ln in p['linhas'] for t in ln['trechos'] if 'novo' in t['texto']) == 'fy'


def test_previa_confere_a_fonte_com_a_quebra_so_na_ultima_edicao_de_texto():
    # as posicoes da quebra da familia contam na ultima edicao de texto do elemento: so ela leva o item
    class Parar(Exception):
        pass
    ed = edicao.Editor.__new__(edicao.Editor)
    chamadas = []
    ed.conferir = lambda dados, antes=None: True
    ed._texto = lambda eid, texto, quebra=None: (chamadas.append((eid, texto, quebra)), (texto, None))[1]

    def viva(*_a):
        raise Parar()
    ed._viva = viva
    q1 = {'elemento': 'el1', 'manter': [0], 'inseridas': []}
    dados = {'familia': 'g1', 'versao': None, 'quebras': [q1],
             'edicoes': [{'elemento': 'el1', 'acao': 'texto', 'texto': 'a\nb'},
                         {'elemento': 'el2', 'acao': 'texto', 'texto': 'c'},
                         {'elemento': 'el1', 'acao': 'texto', 'texto': 'a\nb\nc'}]}
    with pytest.raises(Parar):
        ed.previa(dados)
    assert chamadas == [('el1', 'a\nb', None), ('el2', 'c', None), ('el1', 'a\nb\nc', q1)]


# ------------------------------------------------------------------ ponta a ponta: Editor.previa
LINHAS_PRETAS, LINHA_AZUL = ('HAX O', 'HOAXAV'), 'OX VA'
COR_PRETA, COR_AZUL = (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)


def _psd_tres_linhas(destino, ps):
    """PSD 640 x 320: fundo, o texto de tres linhas (as duas primeiras numa cor, a ultima em outra) e um quadrado."""
    from PIL import Image
    from psd_tools import PSDImage

    import test_fontes_apoio as fap
    import test_render_apoio as rap
    p = PSDImage.new('RGB', (640, 320), color=(255, 255, 255))
    p.create_pixel_layer(Image.new('RGBA', (640, 320), (240, 236, 220, 255)), name='fundo-sintetico')
    t = p.create_pixel_layer(Image.new('RGBA', (220, 180), (20, 20, 20, 255)), name='tres-linhas', top=20, left=20)
    trechos = ['\r'.join(LINHAS_PRETAS) + '\r', LINHA_AZUL]
    bruto = fap._engine([(s, 0, 25.0, 0) for s in trechos], [ps])
    partes = bruto.split(b'/Values [ 1.0 0.1 0.2 0.3 ]')
    assert len(partes) == len(trechos) + 1
    ed = partes[0]
    for cor, resto in zip((COR_PRETA, COR_AZUL), partes[1:]):
        ed += b'/Values [ 1.0 %s ]' % b' '.join(b'%.3f' % x for x in cor) + resto
    texto = ''.join(trechos)
    bounds = fap.Descriptor(name='', classID=b'bounds', items=[
        (b'Left', fap.Double(0.0)), (b'Top ', fap.Double(-20.0)), (b'Rght', fap.Double(120.0)),
        (b'Btom', fap.Double(80.0))])
    td = fap.DescriptorBlock(name='', classID=b'TxLr', items=[
        (b'Txt ', fap.String(value=texto + '\r')), (b'AntA', fap.Enumerated(typeID=b'Annt', enum=b'antiAliasSharp')),
        (b'bounds', bounds), (b'EngineData', fap.RawData(value=fap.EngineData.frombytes(ed)))])
    warp = fap.DescriptorBlock(name='', classID=b'warp', items=[
        (b'warpStyle', fap.Enumerated(typeID=b'warpStyle', enum=b'warpNone')), (b'warpValue', fap.Double(0.0)),
        (b'warpPerspective', fap.Double(0.0)), (b'warpPerspectiveOther', fap.Double(0.0)),
        (b'warpRotate', fap.Enumerated(typeID=b'Ornt', enum=b'Hrzn'))])
    tysh = fap.TypeToolObjectSetting(version=1, transform=(2.0, 0.0, 0.0, 2.0, 20.0, 70.0), text_version=50,
                                     text_data=td, warp_version=1, warp=warp, left=0, top=0, right=t.width,
                                     bottom=t.height)
    t._record.tagged_blocks[fap.Tag.TYPE_TOOL_OBJECT_SETTING] = fap.TaggedBlock(
        key=fap.Tag.TYPE_TOOL_OBJECT_SETTING, data=tysh)
    p.create_pixel_layer(Image.new('RGBA', (60, 60), (0, 120, 60, 255)), name='quadrado-sintetico', top=240, left=560)
    return rap._salvar(p, destino)


@pytest.fixture(scope='module')
def job_tres_linhas(tmp_path_factory):
    import test_derivacao_apoio as ap
    import test_fontes_apoio as fap
    from vapt import contratos
    from vapt.briefing import modelo as mb
    from vapt.job import nucleo
    from vapt.render import autoteste
    base = tmp_path_factory.mktemp('tres-cores')
    fontes = base / 'origem-fontes'
    fap.gravar(fontes, 'autoteste.ttf', autoteste.gerar_fonte())
    job = base / 'job'
    nucleo.criar(job, _psd_tres_linhas(base / 'origem' / 'kv.psd', autoteste.NOME_PS), 'c', fontes=[fontes])
    r = nucleo.proxima(job, todas=True)
    assert r.codigo == 0, (r.situacao, r.linhas_humanas)
    laudo = contratos.ler(job / mb.ARQUIVO_LAUDO, 'laudo/1')
    ids = {c['nome']: c['identidade']['layer_id'] for c in laudo['camadas']}
    funcoes = {ids['fundo-sintetico']: 'fundo', ids['tres-linhas']: 'titulo', ids['quadrado-sintetico']: 'logo_principal'}
    b = ap.briefing(funcoes=funcoes, formatos=[ap.formato('mesma', 640, 320, rotacao={'graus': 0, 'sentido': None})])
    b.pop('cabecalho')
    b.pop('job_id')
    arq = base / 'fixture.json'
    arq.write_text(json.dumps(b), encoding='utf-8')
    mb.importar_teste(job, arq)
    return job


def _peca_do_titulo(membro, eid):
    return next(p for p in membro['palco']['pecas'] if p['elemento'] == eid and p['tipo'] == 'texto')


def test_previa_da_familia_leva_o_azul_ao_texto_editado(job_tres_linhas):
    conteudo = te.montar(job_tres_linhas)
    gid = next(g for g, f in conteudo['familias'].items() if 'mesma' in f['formatos'])
    sem = conteudo['editar']({'familia': gid, 'versao': None, 'edicoes': []})
    eid = next(e['id'] for e in sem['membros'][0]['palco']['elementos'] if e['funcao'] == 'titulo')
    kv = _peca_do_titulo(sem['membros'][0], eid)
    preta, azul = kv['linhas'][0]['trechos'][0]['cor'], kv['linhas'][-1]['trechos'][0]['cor']
    assert preta != azul and azul is not None
    # so o Enter (o DA tirou a primeira quebra pelo campo de texto) e a palavra azul trocada
    for texto, esperado in [('HAX O HOAXAV\nOX VA', [[('HAX O HOAXAV', preta)], [('OX VA', azul)]]),
                            ('HAX O\nHOAXAV\nOX HOX', [[('HAX O', preta)], [('HOAXAV', preta)], [('OX HOX', azul)]])]:
        r = conteudo['editar']({'familia': gid, 'versao': None,
                                'edicoes': [{'elemento': eid, 'acao': 'texto', 'texto': texto}]})
        assert r['recusas'] == [], r['recusas']
        p = _peca_do_titulo(r['membros'][0], eid)
        assert p['texto_editado'] is True
        assert _cores(p) == esperado
        # o corpo e a face de cada trecho sao os do KV no formato
        assert {(t['face'], t['corpo']) for ln in p['linhas'] for t in ln['trechos']} == \
            {(t['face'], t['corpo']) for ln in kv['linhas'] for t in ln['trechos']}


# ------------------------------------------------------------------ o CR de outra linha (o vao igual ao do KV)
def _cr_de_outra_linha():
    # 'L1 a' e 'L3 c' pretos a 10 pt (no texto; a matriz dobra e o formato divide por dois), 'L2 b' azul a 5 pt, e o
    # CR que termina a linha 2 no run preto da linha 3: no KV, a entrelinha da linha 2 e a do CR preto
    return _texto_kv([_run(0, 'L1 a\r', PRETO), _run(5, 'L2 b', AZUL, corpo=10.0), _run(9, '\rL3 c', PRETO)])


@pytest.mark.parametrize('texto', ['L1 a\nL2 b\nL3 d', 'L1 x\nL2 b\nL3 c', 'L1 a\nL2 b\nx c', 'L1 a\nL2 y\nL3 c'])
def test_trocar_palavra_de_outra_linha_nao_muda_a_entrelinha_da_linha_2(texto):
    kv = _cr_de_outra_linha()
    palco_kv, _base = _palco(copy.deepcopy(kv))
    assert [ln['entrelinha'] for ln in palco_kv['pecas'][0]['linhas']] == [12.0, 12.0, 12.0]
    p = _trocar(copy.deepcopy(kv), texto)
    linhas = mq.linhas_editadas(texto)
    # antes a quebra da linha 2 herdava o 'b' azul da esquerda e a linha 2 ficava com a entrelinha do corpo azul (6)
    assert [ln['entrelinha'] for ln in p['linhas']] == _entrelinhas_do_render(copy.deepcopy(kv), linhas) == \
        _entrelinhas_no_render(copy.deepcopy(kv), texto) == [12.0, 12.0, 12.0]
    assert _cores(p) == _cores_do_render(copy.deepcopy(kv), texto, None) == \
        [[(linhas[0], PRETO)], [(linhas[1], AZUL)], [(linhas[2], PRETO)]]
    # no render, o CR que termina a linha 2 fica no run preto de corpo 10, o do KV
    novo = _no_render(copy.deepcopy(kv), texto, None)
    pos = len(linhas[0]) + 1 + len(linhas[1])
    [dono] = [r for r in novo['texto']['runs'] if r['inicio'] <= pos < r['fim']]
    assert dono['texto'][pos - dono['inicio']] == '\n' and dono['corpo_espaco_texto'] == 10.0
    assert novo['cores_por_trecho'][str(dono['inicio'])] == COR_DE[PRETO]


def test_insercao_junto_ao_cr_herda_a_esquerda_nas_tres_camadas():
    # fora da regra do vao, por desenho: a palavra nova no fim da linha 2 desfaz o par, o CR herda a esquerda (o azul
    # de corpo 5) e a linha 2 fica com a entrelinha dele, igual no palco, na medida e no render
    kv, texto = _cr_de_outra_linha(), 'L1 a\nL2 b x\nL3 c'
    p = _trocar(copy.deepcopy(kv), texto)
    assert [ln['entrelinha'] for ln in p['linhas']] == _entrelinhas_do_render(kv, mq.linhas_editadas(texto)) == \
        _entrelinhas_no_render(kv, texto) == [12.0, 6.0, 12.0]


# ------------------------------------------------------------------ o respiro (o CR sem tinta entre paragrafos)
def _com_respiro(cor_titulo=PRETO, cor_respiro=PRETO, cor_corpo=PRETO, fonte_respiro='X'):
    # o titulo a 40 pt, a linha vazia de 10 pt (o CR sem tinta, o respiro) e o corpo a 20 pt (no texto; a matriz
    # dobra), entrelinha automatica (1,2): no KV, [48, 12, 24]
    return _texto_kv([_run(0, 'TITULO\r', cor_titulo, corpo=80.0),
                      _run(7, '\r', cor_respiro, fonte=fonte_respiro, corpo=20.0),
                      _run(8, 'corpo do texto', cor_corpo, corpo=40.0)])


RESPIROS = [
    # sem cores: o KV todo preto, numa face so, so o corpo muda
    {},
    # com cores: o titulo preto, o respiro e o corpo azuis, o respiro numa face que nem esta no job
    {'cor_respiro': AZUL, 'cor_corpo': AZUL, 'fonte_respiro': 'Z'},
    # o respiro de outra cor e outra face (do job), o resto preto
    {'cor_respiro': AZUL, 'fonte_respiro': 'Y'},
]


@pytest.mark.parametrize('cores', RESPIROS)
@pytest.mark.parametrize('texto,esperado', [
    # o texto do KV
    ('TITULO\n\ncorpo do texto', [48.0, 12.0, 24.0]),
    # o DA so poe um Enter (antes o respiro herdava o vizinho e a linha vazia ficava com a entrelinha do corpo)
    ('TITULO\n\ncorpo do\ntexto', [48.0, 12.0, 24.0, 24.0]),
    # a palavra do corpo trocada
    ('TITULO\n\ncorpo novo', [48.0, 12.0, 24.0]),
])
def test_respiro_fica_no_palco_na_medida_e_no_render(cores, texto, esperado):
    kv = _com_respiro(**cores)
    palco_kv, _base = _palco(copy.deepcopy(kv))
    assert [ln['entrelinha'] for ln in palco_kv['pecas'][0]['linhas']] == [48.0, 12.0, 24.0]
    p = _trocar(copy.deepcopy(kv), texto)
    assert [ln['entrelinha'] for ln in p['linhas']] == \
        _entrelinhas_do_render(copy.deepcopy(kv), mq.linhas_editadas(texto)) == \
        _entrelinhas_no_render(copy.deepcopy(kv), texto) == esperado
    # a linha vazia leva o estilo do trecho com tinta antes dela (o titulo), nunca o do run sem tinta
    assert p['linhas'][1]['trechos'] == [{'texto': '', 'fonte_ps': 'X', 'face': 'fx', 'cor': PRETO, 'corpo': 40.0,
                                          'tracking': 0}]
    # no render, o respiro e um trecho sem tinta com a cor dele, e a face que nao esta no job fica de fora
    novo = _no_render(copy.deepcopy(kv), texto, None)
    [respiro] = [r for r in novo['texto']['runs'] if not r['tem_tinta']]
    assert respiro['texto'] == '\n' and respiro['inicio'] == len('TITULO\n')
    assert novo['cores_por_trecho'][str(respiro['inicio'])] == COR_DE[cores.get('cor_respiro', PRETO)]
    assert 'Z' not in novo['faces']


def test_linha_vazia_no_comeco_e_o_respiro_levam_o_trecho_com_tinta():
    # a linha vazia antes do titulo (o DA poe um Enter no comeco) leva o primeiro trecho com tinta; a do respiro, o
    # trecho com tinta antes dela; nenhuma o run sem tinta (preto, na face que nem esta no job)
    p = _trocar(_com_respiro(cor_titulo=AZUL, cor_respiro=PRETO, fonte_respiro='Z'), '\nTITULO\n\ncorpo do texto')
    for n in (0, 2):
        assert [(t['texto'], t['cor'], t['face'], t['corpo']) for t in p['linhas'][n]['trechos']] == \
            [('', AZUL, 'fx', 40.0)]
    assert p['linhas'][2]['entrelinha'] == 12.0


def _tres_camadas(kv, texto):
    """As entrelinhas de cada linha no palco, na medida e no render, que tem de bater."""
    p = _trocar(copy.deepcopy(kv), texto)
    palco = [ln['entrelinha'] for ln in p['linhas']]
    assert palco == _entrelinhas_do_render(copy.deepcopy(kv), mq.linhas_editadas(texto)) == \
        _entrelinhas_no_render(copy.deepcopy(kv), texto)
    return palco


@pytest.mark.parametrize('kv,texto,esperado', [
    # o CR sem tinta de corpo 80 no comeco (a linha vazia de cima com a entrelinha 48) e o titulo e o corpo a 20: o DA
    # troca uma palavra do corpo
    ([('\r', 80.0), ('TITULO X\rcorpo Y', 20.0)], '\nTITULO X\ncorpo Z', [48.0, 12.0, 12.0]),
    # duas linhas vazias no comeco, a segunda no CR de corpo 80
    ([('\r', 20.0), ('\r', 80.0), ('TITULO X\rcorpo Y', 20.0)], '\n\nTITULO X\ncorpo Z', [12.0, 48.0, 12.0, 12.0]),
    # o vao do comeco so de quebras com mais linhas vazias que o do KV: a primeira e a ultima com a do KV
    ([('\r', 80.0), ('TITULO X\rcorpo Y', 20.0)], '\n\nTITULO X\ncorpo Z', [48.0, 48.0, 12.0, 12.0]),
])
def test_vao_do_comeco_guarda_a_entrelinha_do_kv_nas_tres_camadas(kv, texto, esperado):
    # rodada 5: o vao antes da primeira palavra (as linhas vazias do comeco) conta como vao pareado quando a primeira
    # palavra nova pareia com a primeira do KV; antes as quebras dele herdavam a palavra da direita (o corpo 20) e o
    # 48 sumia
    runs, inicio = [], 0
    for s, corpo in kv:
        runs.append(_run(inicio, s, PRETO, corpo=corpo))
        inicio += len(s)
    kv = _texto_kv(runs)
    palco_kv, _base = _palco(copy.deepcopy(kv))
    assert 48.0 in [ln['entrelinha'] for ln in palco_kv['pecas'][0]['linhas']]
    assert _tres_camadas(kv, texto) == esperado


@pytest.mark.parametrize('texto,esperado', [
    ('\nTITULO X\ncorpo Z', [48.0, 48.0, 12.0]),
    ('\n\nTITULO X\ncorpo Y', [48.0, 48.0, 48.0, 12.0]),
])
def test_enter_no_comeco_do_kv_sem_linha_vazia_herda_a_primeira_palavra(texto, esperado):
    # o KV sem linha vazia no comeco (o vao do KV antes da primeira palavra e vazio): a linha vazia que o DA poe no
    # comeco fica com o run da primeira palavra ('TITULO X' a 80), como antes, nas tres camadas
    kv = _texto_kv([_run(0, 'TITULO X\r', PRETO, corpo=80.0), _run(9, 'corpo Y', AZUL, corpo=20.0)])
    runs = mq.runs_do_editado(kv['runs'], mq.linhas_editadas(texto), '\n')
    assert runs[0]['texto'].startswith('\n') and runs[0]['corpo_efetivo'] == 80.0 and runs[0]['cor_hex'] == PRETO
    assert _tres_camadas(kv, texto) == esperado
    p = _trocar(copy.deepcopy(kv), texto)
    assert p['linhas'][0]['trechos'] == [dict(p['linhas'][-2]['trechos'][0], texto='')]


def test_texto_aceita_o_respiro_numa_face_fora_do_job():
    # o run sem tinta (o respiro) numa face que nao esta no job nao recusa o texto: so os trechos com tinta sao
    # conferidos na face
    ed = _editor(_com_respiro(cor_respiro=AZUL, fonte_respiro='Z'))
    for texto in ('TITULO\n\ncorpo do\ntexto', 'TITULO\n\ncorpo do texto'):
        assert ed._texto('el1', texto) == (texto, None)
    # a palavra com tinta numa face fora do job continua recusada
    kv = _com_respiro()
    kv['runs'][2]['fonte_ps'] = 'Z'
    texto, recusa = _editor(kv)._texto('el1', 'TITULO\n\ncorpo do\ntexto')
    assert texto is None and 'não está no job' in recusa


# ------------------------------------------------------------------ rodada 4: o respiro nao olha a cor
def _cor_valores(hexa, alfa=1.0):
    # (alfa, r, g, b) como o laudo grava, a partir do hex
    return [alfa] + [int(hexa[k:k + 2], 16) / 255.0 for k in (1, 3, 5)]


def _respiro_com_cor_valores(alfas=None, **cores):
    """O KV do respiro (_com_respiro) com a cor tambem em cor_valores, como o laudo grava. alfas: {inicio: alfa}."""
    kv = _com_respiro(**cores)
    for r in kv['runs']:
        r['cor_valores'] = _cor_valores(r['cor_hex'], (alfas or {}).get(r['inicio'], 1.0))
    return kv


def _entrada_do_contrato(texto_kv, overlay):
    """A entrada de texto do contrato do render pelo caminho de verdade (render.contrato._entrada_texto): a cor fora
    do run, pelos cor_valores ou pelo ColorOverlay (que unifica a cor e ignora o alfa)."""
    from vapt.render import contrato as mc
    reg = {'texto': copy.deepcopy(texto_kv), 'layer_id': 7, 'indice': 0, 'caixa': [0, 0, 50, 50], 'blend': 'NORMAL',
           'opacidade': 255, 'preenchimento': 255}
    if overlay:
        reg['efeitos'] = [{'tipo': 'ColorOverlay', 'ativo': True, 'medidas': {'blend': 'NORMAL', 'opacity': 100.0}}]
        reg['cores_descritores'] = [{'descritor': 'overlay', 'ativo': True, 'classe': 'RGBC', 'indice_efeito': 0,
                                     'valores': {'Rd': 255.0, 'Grn': 255.0, 'Bl': 255.0}}]
    registros = []
    e = mc._entrada_texto(reg, 'e01', {}, {'X': {'id': 'fx'}, 'Y': {'id': 'fy'}}, {'largura': 100, 'altura': 100},
                          registros)
    assert e is not None, registros
    return e


def _entrelinhas_do_contrato(texto_kv, texto, overlay):
    e = _entrada_do_contrato(texto_kv, overlay)
    novo = rd.texto_editado_na_entrada(e, texto, None)
    m = texto_kv['matriz']
    sy = (float(m[2]) ** 2 + float(m[3]) ** 2) ** 0.5
    return [te._arred(te._arred(ln['entrelinha'] * sy) * ESCALA) for ln in rt.linhas_da_camada(novo['texto'])]


@pytest.mark.parametrize('caso', ['overlay', 'so_o_alfa', 'cores'])
@pytest.mark.parametrize('texto,esperado', [
    ('TITULO\n\ncorpo do texto', [48.0, 12.0, 24.0]),
    ('TITULO\n\ncorpo do\ntexto', [48.0, 12.0, 24.0, 24.0]),
    ('TITULO\n\n\ncorpo do texto', [48.0, 12.0, 12.0, 24.0]),
])
def test_respiro_igual_nas_tres_camadas_com_overlay_ou_so_o_alfa(caso, texto, esperado):
    # antes (o um_estilo da rodada 3) o estilo dependia da cor, que o laudo guarda em cor_hex e cor_valores e o
    # contrato do render em cores_por_trecho (o ColorOverlay unifica, e ignora o alfa): o KV de duas cores na vista
    # do laudo era de uma no render, e o respiro sumia so no PNG
    if caso == 'overlay':
        kv, overlay = _respiro_com_cor_valores(cor_respiro=AZUL, cor_corpo=AZUL), True
    elif caso == 'so_o_alfa':
        kv, overlay = _respiro_com_cor_valores({7: 0.5, 8: 0.5}), False  # numero-neutro: os inicios dos runs
    else:
        kv, overlay = _respiro_com_cor_valores(cor_respiro=AZUL, cor_corpo=AZUL), False
    cores_do_contrato = set(_entrada_do_contrato(kv, overlay)['cores_por_trecho'].values())
    assert len(cores_do_contrato) == (2 if caso == 'cores' else 1)
    p = _trocar(copy.deepcopy(kv), texto)
    assert [ln['entrelinha'] for ln in p['linhas']] == \
        _entrelinhas_do_render(copy.deepcopy(kv), mq.linhas_editadas(texto)) == \
        _entrelinhas_do_contrato(kv, texto, overlay) == esperado


def _cr_multiplo():
    # o titulo a 40 pt com o CR dele, duas linhas vazias de 10 pt (um run sem tinta com dois CR) e o corpo azul a 20 pt
    # (no texto; a matriz dobra): no KV, [48, 12, 12, 24]
    return _texto_kv([_run(0, 'TITULO\r', PRETO, corpo=80.0), _run(7, '\r\r', PRETO, corpo=20.0),
                      _run(9, 'corpo do texto', AZUL, corpo=40.0)])


@pytest.mark.parametrize('kv,texto,esperado', [
    # o respiro de uma linha vazia, e o DA poe mais uma ou duas
    (_com_respiro(), 'TITULO\n\n\ncorpo do texto', [48.0, 12.0, 12.0, 24.0]),
    (_com_respiro(), 'TITULO\n\n\n\ncorpo do texto', [48.0, 12.0, 12.0, 12.0, 24.0]),
    (_com_respiro(cor_respiro=AZUL, fonte_respiro='Z'), 'TITULO\n\n\ncorpo do\ntexto', [48.0, 12.0, 12.0, 24.0, 24.0]),
    # o CR multiplo: o DA tira uma linha vazia, mantem as duas ou poe mais uma
    (_cr_multiplo(), 'TITULO\n\ncorpo do texto', [48.0, 12.0, 24.0]),
    (_cr_multiplo(), 'TITULO\n\n\ncorpo do texto', [48.0, 12.0, 12.0, 24.0]),
    (_cr_multiplo(), 'TITULO\n\n\n\ncorpo do texto', [48.0, 12.0, 12.0, 12.0, 24.0]),
    # tirar as linhas vazias todas: a quebra que fica e a primeira (a do titulo)
    (_cr_multiplo(), 'TITULO\ncorpo do texto', [48.0, 24.0]),
])
def test_linhas_vazias_postas_ou_tiradas_guardam_o_respiro(kv, texto, esperado):
    palco_kv, _base = _palco(copy.deepcopy(kv))
    vazias_no_kv = len(kv['runs'][1]['texto'])
    assert [ln['entrelinha'] for ln in palco_kv['pecas'][0]['linhas']] == [48.0] + [12.0] * vazias_no_kv + [24.0]
    p = _trocar(copy.deepcopy(kv), texto)
    assert [ln['entrelinha'] for ln in p['linhas']] == \
        _entrelinhas_do_render(copy.deepcopy(kv), mq.linhas_editadas(texto)) == \
        _entrelinhas_no_render(copy.deepcopy(kv), texto) == esperado
    # as linhas vazias levam o estilo do titulo, e o corpo azul fica azul
    assert all(ln['trechos'] == [dict(p['linhas'][0]['trechos'][0], texto='')] for ln in p['linhas'][1:-1]
               if not ln['trechos'][0]['texto'])
    assert p['linhas'][-1]['trechos'][-1]['cor'] == kv['runs'][2]['cor_hex']


def _estilo_do_trecho(t):
    return {k: v for k, v in t.items() if k != 'texto'}


@pytest.mark.parametrize('kv', [
    _tres_linhas(),
    _com_respiro(cor_respiro=AZUL, cor_corpo=AZUL, fonte_respiro='Z'),
    _cr_multiplo(),
    # o espaco sem tinta de outra fonte (fora do job) e outro corpo, no KV de uma cor
    _texto_kv([_run(0, 'HAH', PRETO), _run(3, ' ', AZUL, fonte='Z', corpo=80.0), _run(4, 'HOX', PRETO)]),
])
def test_texto_igual_ao_do_kv_sai_com_os_runs_do_kv_nas_tres_camadas(kv):
    texto = kv['conteudo'].replace('\r', '\n')
    palco_kv, _base = _palco(copy.deepcopy(kv))
    # o palco: as linhas do KV (a linha vazia do texto editado leva um trecho vazio, com o estilo do vizinho, para a
    # pagina medir a altura dela; no KV ela vem sem trecho)
    p = _trocar(copy.deepcopy(kv), texto)

    def com_texto(linhas):
        return [([t for t in ln['trechos'] if t['texto']], ln['entrelinha']) for ln in linhas]
    if any(t['face'] is None for ln in palco_kv['pecas'][0]['linhas'] for t in ln['trechos']):
        # rodada 5 (casamento.vizinho_com_face): o espaco sem tinta da fonte fora do job vai no trecho do vizinho com
        # face; o palco do KV sem edicao (a imagem da camada) guarda o trecho sem face
        [[a, espaco, b]] = [ln['trechos'] for ln in palco_kv['pecas'][0]['linhas']]
        assert (espaco['texto'], espaco['face'], a['face'], _estilo_do_trecho(a)) == (' ', None, 'fx', _estilo_do_trecho(b))
        assert com_texto(p['linhas']) == [([dict(a, texto=a['texto'] + espaco['texto'] + b['texto'])],
                                           palco_kv['pecas'][0]['linhas'][0]['entrelinha'])]
    else:
        assert com_texto(p['linhas']) == com_texto(palco_kv['pecas'][0]['linhas'])
    assert all(ln['trechos'] for ln in p['linhas'])
    # a medida: os runs do KV, sem o kerning manual
    t = mq.camada_do_editado({'texto': copy.deepcopy(kv)}, mq.linhas_editadas(texto))['texto']
    assert t['runs'] == [dict(r, kerning=None) for r in kv['runs']]
    # o render: os runs do contrato do KV e as cores dele
    entrada = _no_render(copy.deepcopy(kv), texto, None)
    kv_no_contrato = [{k: v for k, v in r.items() if k != 'cor_hex'} for r in kv['runs']]
    assert entrada['texto']['runs'] == [dict(r, kerning=None, texto=r['texto'].replace('\r', '\n'))
                                        for r in kv_no_contrato]
    assert entrada['cores_por_trecho'] == {str(r['inicio']): COR_DE[r['cor_hex']] for r in kv['runs']}


FACE_X_DO_RENDER = {'X': {'id': 'fx', 'peso_declarado': 400, 'metricas': None}}


def _tspans(svg):
    """[(font-size em px, texto)] de cada tspan do SVG do render."""
    import re
    return [(float(m.group(1)), m.group(2)) for m in
            re.finditer(r'<tspan [^>]*style="[^"]*font-size:([0-9.]+)px[^"]*"[^>]*>([^<]*)</tspan>', svg)]


@pytest.mark.parametrize('texto', ['HAH HOX', 'HAH HOX novo'])
def test_espaco_sem_tinta_fora_do_job_sai_igual_no_palco_e_no_render(texto):
    # rodada 5 (casamento.vizinho_com_face): o espaco sem tinta numa fonte fora do job que continua espaco guarda o run
    # dele, e o palco, a medida e o render o desenham no run com face antes dele (antes o render pulava o run sem face
    # e as palavras colavam no PNG)
    kv = _texto_kv([_run(0, 'HAH', PRETO), _run(3, ' ', AZUL, fonte='Z', corpo=80.0), _run(4, 'HOX', PRETO)])
    p = _trocar(copy.deepcopy(kv), texto)
    no_palco = [''.join(t['texto'] for t in ln['trechos']) for ln in p['linhas']]
    novo = _no_render(copy.deepcopy(kv), texto, None)
    # o run do espaco continua no texto do render, na fonte dele (fora do job)
    assert [(r['texto'], r['fonte_ps']) for r in novo['texto']['runs']][1] == (' ', 'Z')
    svg, spans, cores = rt.montar_svg(novo, FACE_X_DO_RENDER, 'p')
    # os caracteres que o render desenha em cada linha (uma cor por caractere desenhado) sao os do palco
    assert [len(c) for c in cores.values()] == [len(s) for s in no_palco]
    # o espaco vai na face e no corpo do vizinho (o 'HAH', X a 10 no texto), no palco e no render: um trecho so na
    # linha, e o mesmo corpo no formato (o do texto vezes a matriz e a escala do formato)
    assert [[(t['texto'], t['fonte_ps'], t['face'], t['corpo']) for t in ln['trechos']] for ln in p['linhas']] == \
        [[(texto, 'X', 'fx', 10.0)]]
    assert _tspans(svg) == [(10.0, texto)] and [s['fonte_ps'] for s in spans] == ['X']
    assert 10.0 * 2.0 * ESCALA == p['linhas'][0]['trechos'][0]['corpo']


def test_vizinho_com_face():
    from vapt.fontes import casamento
    runs = [{'texto': 'AB', 'fonte_ps': 'X'}, {'texto': '', 'fonte_ps': 'Y'}, {'texto': ' ', 'fonte_ps': 'Z'},
            {'texto': 'CD', 'fonte_ps': 'Y'}, {'texto': '\r', 'fonte_ps': 'Z'}, {'texto': 'E', 'fonte_ps': 'Z'}]

    def tem_face(r):
        return r['fonte_ps'] in ('X', 'Y')
    # o run com texto e face antes dele (o vazio nao serve)
    assert casamento.vizinho_com_face(runs, 2, tem_face) is runs[0]
    assert casamento.vizinho_com_face(runs, 4, tem_face) is runs[3]
    # sem nenhum antes, o depois
    assert casamento.vizinho_com_face(runs[2:], 0, tem_face) is runs[3]
    # o run com face, o run com tinta (sem face) e o run sem vizinho com face: None
    assert casamento.vizinho_com_face(runs, 0, tem_face) is None
    assert casamento.vizinho_com_face(runs, 5, tem_face) is None
    assert casamento.vizinho_com_face([runs[2], runs[4]], 0, tem_face) is None


def _rv(texto, fonte, corpo):
    return {'texto': texto, 'fonte_ps': fonte, 'corpo_espaco_texto': corpo}


VIZINHO_NA_LINHA = {
    # rodada 6: o vizinho do espaco sem face (Z) tem tinta e vem da mesma linha (o da esquerda, no comeco da linha o
    # da direita); a quebra (o CR) de outra fonte e outro corpo nao serve, nem a linha de antes
    'linha anterior (CR proprio)': ([_rv('TITULO', 'X', 48), _rv('\r', 'X', 48), _rv(' ', 'Z', 0),
                                     _rv('corpo', 'X', 10)], 3),
    'linha anterior (CR no run)': ([_rv('TITULO\r', 'X', 48), _rv(' ', 'Z', 0), _rv('corpo', 'X', 10)], 2),
    'meio da linha': ([_rv('Hello', 'X', 10), _rv('\r', 'Y', 100), _rv('a', 'Y', 20), _rv(' ', 'Z', 0),
                       _rv('World', 'X', 10)], 2),
    # no fim da linha, sem nada depois na linha: o da esquerda
    'fim da linha': ([_rv('Hello', 'X', 10), _rv(' ', 'Z', 0), _rv('\r', 'Y', 100), _rv('fim', 'Y', 30)], 0),
    # a linha so com o espaco: o com tinta mais perto antes (a linha de antes), nao o CR
    'linha so com o espaco': ([_rv('a', 'X', 10), _rv('\r', 'X', 10), _rv(' ', 'Z', 0), _rv('\r', 'X', 10),
                               _rv('b', 'Y', 30)], 0),
    # o achado: 'Hello' X 10, o CR Y 100, o espaco Z, 'World' X 10: o 'World', nao o CR
    'achado (Hello CR espaco World)': ([_rv('Hello', 'X', 10), _rv('\r', 'Y', 100), _rv(' ', 'Z', 0),
                                        _rv('World', 'X', 10)], 3),
    # o CR no run da direita: o trecho antes da primeira quebra dele
    'CR no run da direita': ([_rv('TITULO\r', 'Y', 100), _rv(' ', 'Z', 0), _rv('corpo\rfim', 'X', 10)], 2),
    # o run da esquerda com o CR no meio: o trecho depois da ultima quebra dele
    'CR no meio do run da esquerda': ([_rv('a\rcorpo', 'X', 10), _rv(' ', 'Z', 0), _rv('b', 'Y', 30)], 0),
    # a quebra dentro do proprio run sem face: '\r ' abre a linha de baixo (o da direita), ' \r' fecha a de cima (o
    # da esquerda), o run so de quebra fecha a de cima; o mesmo texto partido em dois runs da o mesmo vizinho
    'CR antes do espaco no run': ([_rv('TITULO', 'X', 100), _rv('\r ', 'Z', 0), _rv('corpo', 'Y', 10)], 2),
    'CR depois do espaco no run': ([_rv('TITULO', 'X', 100), _rv(' \r', 'Z', 0), _rv('corpo', 'Y', 10)], 0),
    'run so de quebra': ([_rv('TITULO', 'X', 100), _rv('\r', 'Z', 0), _rv('corpo', 'Y', 10)], 0),
}


@pytest.mark.parametrize('caso', sorted(VIZINHO_NA_LINHA))
def test_vizinho_com_face_tem_tinta_e_vem_da_mesma_linha(caso):
    from vapt.fontes import casamento
    runs, esperado = VIZINHO_NA_LINHA[caso]
    i = next(k for k, r in enumerate(runs) if r['fonte_ps'] == 'Z')
    assert casamento.vizinho_com_face(runs, i, lambda r: r['fonte_ps'] != 'Z') is runs[esperado]


def test_vizinho_com_face_sem_run_com_tinta_ou_sem_face():
    from vapt.fontes import casamento

    def tem_face(r):
        return r['fonte_ps'] != 'Z'
    # so o CR tem face: sem nenhum com tinta, o com texto e face mais perto (antes, sem nenhum o depois)
    runs = [_rv('\r', 'X', 48), _rv(' ', 'Z', 0)]
    assert casamento.vizinho_com_face(runs, 1, tem_face) is runs[0]
    runs = [_rv(' ', 'Z', 0), _rv('\r', 'Y', 48)]
    assert casamento.vizinho_com_face(runs, 0, tem_face) is runs[1]
    # na mesma linha, o com tinta vence o sem tinta mais perto (o espaco com face entre os dois)
    runs = [_rv('Hello', 'X', 10), _rv(' ', 'Y', 100), _rv(' ', 'Z', 0)]
    assert casamento.vizinho_com_face(runs, 2, tem_face) is runs[0]
    # nada com face: None
    assert casamento.vizinho_com_face([_rv(' ', 'Z', 0), _rv('a', 'Z', 0)], 0, tem_face) is None


KV_ESPACO_Z = {
    # o espaco sem tinta de uma fonte fora do job (Z) e outro corpo no meio, e no comeco do texto
    'meio': lambda: _texto_kv([_run(0, 'HAH', PRETO), _run(3, ' ', AZUL, fonte='Z', corpo=80.0),
                               _run(4, 'HOX', PRETO)]),
    'comeco': lambda: _texto_kv([_run(0, ' ', AZUL, fonte='Z', corpo=80.0), _run(1, 'HAH HOX', PRETO)]),
}


def _no_render_sem_edicao(texto_kv):
    """A entrada do contrato do render do KV sem edicao (os runs do KV, a cor fora do run)."""
    e = _no_render(copy.deepcopy(texto_kv), texto_kv['conteudo'], None)
    runs = [{k: v for k, v in r.items() if k != 'cor_hex'} for r in texto_kv['runs']]
    return dict(e, texto=dict(e['texto'], runs=runs))


@pytest.mark.parametrize('caso', sorted(KV_ESPACO_Z))
@pytest.mark.parametrize('editado', [False, True])
def test_render_e_medida_desenham_o_espaco_sem_face_na_face_do_vizinho(caso, editado):
    # rodada 5: o run sem tinta numa fonte sem face no job vai na face do run com face antes dele (no comeco, o depois),
    # com o estilo dele e sem kerning manual, no render (montar_svg) e na medida (fontes.medicao.montar), no KV sem
    # edicao e no texto editado; antes os dois pulavam o run e o espaco sumia (as palavras colavam)
    from vapt.fontes import medicao
    kv = KV_ESPACO_Z[caso]()
    texto = kv['conteudo'] + (' novo' if editado else '')
    entrada = _no_render(copy.deepcopy(kv), texto, None) if editado else _no_render_sem_edicao(kv)
    assert 'Z' in {r['fonte_ps'] for r in entrada['texto']['runs']}
    svg, spans, cores = rt.montar_svg(entrada, FACE_X_DO_RENDER, 'p')
    assert _tspans(svg) == [(10.0, texto)] and [s['fonte_ps'] for s in spans] == ['X']
    # a cor do espaco e a do vizinho (ele nao tem tinta)
    assert cores == {'L0': ['c0'] * len(texto)}
    # a medida: o espaco no span da face X, com o corpo dela
    face = {'id': 'fx', 'peso_declarado': 400, 'cmap': [[32, 126]]}
    camada = {'identidade': {'layer_id': 7}, 'texto': copy.deepcopy(kv)}
    if editado:
        camada = mq.camada_do_editado(camada, mq.linhas_editadas(texto))
    pagina, plano = medicao.montar([camada], {'X': face, 'Z': None}, [face], 'pp')
    [ln] = plano['camadas'][0]['linhas']
    assert [s['fonte_ps'] for s in plano['camadas'][0]['spans']] == ['X']
    assert '>%s</span>' % texto in pagina and pagina.count('font-size:') == 1
    assert ln['id'] == 'l0_0'
    # o palco do texto editado: o espaco no trecho do vizinho
    if editado:
        p = _trocar(copy.deepcopy(kv), texto)
        assert [[(t['texto'], t['face'], t['corpo']) for t in ln['trechos']] for ln in p['linhas']] == \
            [[(texto, 'fx', 10.0)]]


@pytest.mark.parametrize('editado', [False, True])
def test_quebra_sem_tinta_fora_do_job_no_svg_guarda_a_entrelinha(editado):
    # rodada 5: o respiro numa fonte fora do job (Z) e desenhado na face do vizinho, mas a entrelinha da linha dele
    # continua a do corpo dele: as linhas de base do SVG do render sao as do respiro na face do job (X), no KV sem
    # edicao e no texto editado (o DA so poe um Enter)
    import re

    def bases(fonte):
        kv = _com_respiro(cor_respiro=AZUL, fonte_respiro=fonte)
        texto = 'TITULO\n\ncorpo do\ntexto'
        entrada = _no_render(copy.deepcopy(kv), texto, None) if editado else _no_render_sem_edicao(kv)
        faces = {'X': FACE_X_DO_RENDER['X'], 'Y': FACE_X_DO_RENDER['X']}
        svg, _s, _c = rt.montar_svg(entrada, faces, 'p')
        return [float(y) for y in re.findall(r'<text id="L\d+" x="[^"]*" y="([^"]*)"', svg)], _tspans(svg)
    com_z, tspans_z = bases('Z')
    assert bases('Y')[0] == com_z
    # o titulo e o corpo (a linha vazia nao tem texto desenhado); do titulo ao corpo desce a entrelinha do respiro
    # (1,2 x 10, no texto) e a do corpo (1,2 x 20); se o respiro herdasse o vizinho, desceria 1,2 x 20 duas vezes
    assert [s for _c, s in tspans_z] == (['TITULO', 'corpo do', 'texto'] if editado else ['TITULO', 'corpo do texto'])
    assert com_z[1] - com_z[0] == pytest.approx(1.2 * 10.0 + 1.2 * 20.0)


def _kv_hello_world(kerning, autokerning=True):
    # o KV sem edicao como o laudo grava (leitor.extrair: num(stl.kerning, 4)): 'Hello', o espaco numa fonte fora do
    # job (Z) e 'World', com o kerning manual em cada run
    return _texto_kv([_run(0, 'Hello', PRETO, kerning=kerning, autokerning=autokerning),
                      _run(5, ' ', PRETO, fonte='Z', kerning=kerning, autokerning=autokerning),
                      _run(6, 'World', PRETO, kerning=kerning, autokerning=autokerning)])


def test_kerning_zero_do_laudo_junta_o_espaco_no_vizinho_no_render_e_na_medida():
    # rodada 6: o kerning 0.0 que o laudo grava e o None da copia do vizinho (sem kerning manual) sao o mesmo estilo
    # (render.texto._chave_estilo); antes o render separava o espaco num tspan dele e a medida juntava tudo num span
    from vapt.fontes import medicao
    kv = _kv_hello_world(0.0)
    svg, spans, cores = rt.montar_svg(_no_render_sem_edicao(kv), FACE_X_DO_RENDER, 'p')
    assert _tspans(svg) == [(10.0, 'Hello World')] and [s['fonte_ps'] for s in spans] == ['X']
    assert cores == {'L0': ['c0'] * len('Hello World')}
    face = {'id': 'fx', 'peso_declarado': 400, 'cmap': [[32, 126]]}
    pagina, plano = medicao.montar([{'identidade': {'layer_id': 7}, 'texto': copy.deepcopy(kv)}],
                                   {'X': face, 'Z': None}, [face], 'pp')
    assert '>Hello World</span>' in pagina and [s['fonte_ps'] for s in plano['camadas'][0]['spans']] == ['X']


def test_kerning_manual_do_kv_continua_separando_no_render():
    # o kerning manual (-20, sem o automatico) fica no tspan do run dele, com o dx: o espaco no vizinho vai sem ele
    # (a copia do vizinho nao leva o kerning manual), como antes da rodada 6
    import re
    kv = _kv_hello_world(-20.0, autokerning=False)
    svg, spans, _cores = rt.montar_svg(_no_render_sem_edicao(kv), FACE_X_DO_RENDER, 'p')
    assert [s for _c, s in _tspans(svg)] == ['Hello', ' ', 'World']
    dx = re.findall(r'<tspan [^>]*?(?: dx="([^"]*)")?>([^<]*)</tspan>', svg)
    assert [(float(d) if d else None, s) for d, s in dx] == [(-0.2, 'Hello'), (None, ' '), (-0.2, 'World')]
    # so o 'World' com o kerning manual: 'Hello' e o espaco num tspan, 'World' no dele
    kv['runs'][0].update(kerning=0.0)
    kv['runs'][1].update(kerning=0.0)
    svg, _s, _c = rt.montar_svg(_no_render_sem_edicao(kv), FACE_X_DO_RENDER, 'p')
    assert [s for _c, s in _tspans(svg)] == ['Hello ', 'World']


def _caixa_com_espaco_sem_face():
    # a entrada do render do KV sem edicao numa caixa de paragrafo (40 de largura, no espaco do texto) com o espaco
    # numa fonte fora do job
    kv = _texto_kv([_run(0, 'Hello', PRETO), _run(5, ' ', PRETO, fonte='Z'), _run(6, 'World', PRETO)])
    t = {'matriz': list(kv['matriz']), 'runs': [{k: v for k, v in r.items() if k != 'cor_hex'} for r in kv['runs']],
         'paragrafos': copy.deepcopy(kv['paragrafos']), 'tipo_caixa': 'paragrafo', 'box_bounds': [0, 0, 40, 50]}
    return {'id': 'e01', 'regiao': [0, 0, 100, 100], 'texto': t, 'cores': ['c0'],
            'cores_por_trecho': {str(r['inicio']): 'c0' for r in kv['runs']}}


def _posicoes_de(svg):
    # as posicoes que o Chromium devolveria em cada linha: uma por caractere desenhado, 6 de largura cada
    import re
    linhas = re.findall(r'<text id="(L\d+)"[^>]*>(.*?)</text>', svg)
    return {lid: [[6.0 * k, 0.0, 6.0 * (k + 1)] for k in range(len(''.join(re.findall(r'>([^<>]*)</tspan>', c))))]
            for lid, c in linhas}


FACE_X_COM_METRICAS = {'X': {'id': 'fx', 'peso_declarado': 400, 'metricas': {'ascender': 800, 'unidades_por_em': 1000}}}


def test_caixa_de_paragrafo_quebra_no_espaco_sem_face():
    # rodada 6: a pagina de quebra desenha o espaco sem face no vizinho, e quebras_da_caixa le a linha do mesmo jeito
    # (render.texto._runs_no_vizinho); antes ela tirava o espaco da linha e caia em 'linha com trecho sem face'
    entrada = _caixa_com_espaco_sem_face()
    assert rt.largura_da_quebra(entrada) == 40.0
    svg, _s, _c = rt.montar_svg(entrada, FACE_X_COM_METRICAS, 'p')
    assert [s for _c, s in _tspans(svg)] == ['Hello World']
    # 'Hello World' passa dos 40 no 'W' (6 x 7 = 42): a quebra cai no espaco
    assert rt.quebras_da_caixa(entrada, _posicoes_de(svg), FACE_X_COM_METRICAS) == [5]
    # com a quebra, cada palavra na linha dela
    svg, _s, _c = rt.montar_svg(dict(entrada, quebras_automaticas=[5]), FACE_X_COM_METRICAS, 'p')
    assert [s for _c, s in _tspans(svg)] == ['Hello', 'World']


def test_texto_editado_com_largura_quebra_quebra_no_espaco_sem_face():
    # a entrada da derivacao de antes da 0.9.4 (largura_quebra, sem linhas_do_da): o mesmo, no texto editado
    kv = _texto_kv([_run(0, 'Hello', PRETO), _run(5, ' ', PRETO, fonte='Z'), _run(6, 'World', PRETO)])
    entrada = _no_render(copy.deepcopy(kv), 'Hello World novo', None)
    assert [(r['texto'], r['fonte_ps']) for r in entrada['texto']['runs']][1] == (' ', 'Z')
    entrada.pop('linhas_do_da')
    entrada['largura_quebra'] = 40.0
    svg, _s, _c = rt.montar_svg(entrada, FACE_X_DO_RENDER, 'p')
    assert [s for _c, s in _tspans(svg)] == ['Hello World novo']
    assert rt.quebras_da_caixa(entrada, _posicoes_de(svg), FACE_X_DO_RENDER) == [5, 11]


@pytest.mark.parametrize('texto', ['Hello\n World', 'Hello\n World novo'])
def test_espaco_sem_face_depois_do_cr_de_outro_corpo_vai_no_mesmo_vizinho_nas_tres_camadas(texto):
    # rodada 6, o achado: 'Hello' (X a 10, no texto), o CR (Y a 100, so a quebra), o espaco numa fonte fora do job e
    # 'World' (X a 10). O espaco vai no 'World', da mesma linha, no palco, na medida e no render; antes ia no CR, de
    # outra linha e corpo 10 vezes maior
    import re
    from vapt.fontes import medicao
    kv = _texto_kv([_run(0, 'Hello', PRETO), _run(5, '\r', AZUL, fonte='Y', corpo=200.0),
                    _run(6, ' ', AZUL, fonte='Z', corpo=80.0), _run(7, 'World', PRETO)])
    editado = texto != kv['conteudo'].replace('\r', '\n')
    segunda = texto.split('\n')[1]
    # o palco
    p = _trocar(copy.deepcopy(kv), texto)
    assert [[(t['texto'], t['fonte_ps'], t['face'], t['corpo']) for t in ln['trechos']] for ln in p['linhas']] == \
        [[('Hello', 'X', 'fx', 10.0)], [(segunda, 'X', 'fx', 10.0)]]
    # o render: a segunda linha num tspan so, no corpo do 'World', e na cor dele
    entrada = _no_render(copy.deepcopy(kv), texto, None) if editado else _no_render_sem_edicao(kv)
    faces = {'X': FACE_X_DO_RENDER['X'], 'Y': {'id': 'fy', 'peso_declarado': 400, 'metricas': None}}
    svg, spans, cores = rt.montar_svg(entrada, faces, 'p')
    assert _tspans(svg) == [(10.0, 'Hello'), (10.0, segunda)] and [s['fonte_ps'] for s in spans] == ['X', 'X']
    assert cores == {'L0': ['c0'] * 5, 'L1': ['c0'] * len(segunda)}
    # a medida: a segunda linha num span so, na face e no corpo do 'World' (o mesmo da primeira linha)
    fx = {'id': 'fx', 'peso_declarado': 400, 'cmap': [[32, 126]]}
    fy = {'id': 'fy', 'peso_declarado': 400, 'cmap': [[32, 126]]}
    camada = {'identidade': {'layer_id': 7}, 'texto': copy.deepcopy(kv)}
    if editado:
        camada = mq.camada_do_editado(camada, mq.linhas_editadas(texto))
    pagina, plano = medicao.montar([camada], {'X': fx, 'Y': fy, 'Z': None}, [fx, fy], 'pp')
    linhas = dict(re.findall(r'<div class="l" id="([^"]*)">(.*?)</div>', pagina))
    assert sorted(linhas) == ['l0_0', 'l0_1'] and '>%s</span>' % segunda in linhas['l0_1']
    assert [s['fonte_ps'] for s in plano['camadas'][0]['spans']] == ['X', 'X']
    assert len(set(re.findall(r'font-size:([0-9.]+)px', pagina))) == 1


# ------------------------------------------------------------------ a ancora do texto editado no KV de varios estilos
def test_ancora_do_kv_de_varios_estilos_leva_os_trechos_da_linha_do_kv():
    # 'L1 a' e 'L2 b' na face X a 40 pt (no formato), 'L3 c' na face Y a 24 pt; o DA deixa so a linha azul: o primeiro
    # trecho do texto editado e o azul, e a subida da linha do KV sai do trecho preto dela
    kv = _texto_kv([_run(0, 'L1 a\rL2 b\r', PRETO, corpo=80.0), _run(10, 'L3 c', AZUL, fonte='Y', corpo=48.0)])
    p = _trocar(kv, 'L3 c')
    assert p['ancora_kv'] == {'texto': 'L1 a', 'acima': 0.0,
                              'trechos': [{'texto': 'L1 a', 'face': 'fx', 'corpo': 40.0}]}
    assert (p['linhas'][0]['trechos'][0]['face'], p['linhas'][0]['trechos'][0]['corpo']) == ('fy', 24.0)
    # a mesma face, so o corpo muda: tambem leva os trechos
    kv = _texto_kv([_run(0, 'L1 a\rL2 b\r', PRETO, corpo=80.0), _run(10, 'L3 c', AZUL, corpo=48.0)])
    assert _trocar(kv, 'L3 c')['ancora_kv']['trechos'] == [{'texto': 'L1 a', 'face': 'fx', 'corpo': 40.0}]


def test_ancora_leva_todos_os_trechos_com_texto_da_linha_do_kv():
    # a primeira linha do KV sem tinta (so um espaco) e a primeira com tinta de duas faces: os trechos dela, sem o que
    # e so espaco
    kv = _texto_kv([_run(0, ' \rAB', PRETO, corpo=80.0), _run(4, ' ', AZUL, corpo=80.0),
                    _run(5, 'CD\rEF', AZUL, fonte='Y', corpo=48.0)])
    p = _trocar(kv, 'EF')
    assert p['ancora_kv']['texto'] == 'AB CD'
    assert p['ancora_kv']['trechos'] == [{'texto': 'AB', 'face': 'fx', 'corpo': 40.0},
                                         {'texto': 'CD', 'face': 'fy', 'corpo': 24.0}]


@pytest.mark.parametrize('kv', [
    # duas cores numa face e num corpo (o relato)
    _tres_linhas(),
    # o espaco solto de outra face e outro corpo nao conta como estilo
    _texto_kv([_run(0, 'HAX', PRETO), _run(3, ' ', AZUL, fonte='Y', corpo=80.0), _run(4, 'HOX', PRETO)]),
])
def test_ancora_do_kv_de_um_estilo_so_fica_sem_trechos(kv):
    p = _trocar(kv, 'OX')
    assert set(p['ancora_kv']) == {'texto', 'acima'}


def _kv_y_e_x():
    # 'L1 a' na face Y a 12 pt (no formato), 'L2 b' na face X a 40 pt e 'L3 c' azul na X a 20 pt
    return _texto_kv([_run(0, 'L1 a\r', PRETO, fonte='Y', corpo=24.0), _run(5, 'L2 b\r', PRETO, corpo=80.0),
                      _run(10, 'L3 c', AZUL, corpo=40.0)])


def _trocar_na_familia(texto_kv, texto, manter, inseridas, com_base=True):
    """trocar_texto com o palco como estado._linhas_no_formato o monta na familia: as linhas do KV ja com a quebra da
    familia (as juntadas e as inseridas), e o texto editado com a mesma quebra."""
    linhas = te._linhas(texto_kv, FACES.get, juntar=mq.juntadas({'texto': texto_kv}, manter), inserir=inseridas)
    palco, base = _palco(copy.deepcopy(texto_kv), linhas)
    quebra = {'manter': list(manter), 'inseridas': list(inseridas)}
    if com_base:
        return edicao.trocar_texto(palco, 'el1', texto, quebra, base=base, escala=ESCALA)['pecas'][0], linhas
    return edicao.trocar_texto(palco, 'el1', texto, quebra)['pecas'][0], linhas


@pytest.mark.parametrize('inseridas,linha_0_do_palco', [
    # a familia junta a linha 1 (Y 12) a linha 2 (X 40)
    ([], ['L1 a ', 'L2 b']),
    # e tambem insere a quebra no espaco de 'L1 a'
    ([2], ['L1']),
])
def test_ancora_do_kv_de_varios_estilos_sai_das_linhas_do_psd(inseridas, linha_0_do_palco):
    # rodada 4: a ancora e a primeira linha do KV no PSD (a caixa de tinta do KV e a do PSD), sem a quebra da familia;
    # antes ela saia das linhas do palco, e juntar a linha 0 a outra de outro corpo dava a subida errada
    p, linhas = _trocar_na_familia(_kv_y_e_x(), 'L3 c', [1], inseridas)
    assert [t['texto'] for t in linhas[0]['trechos']] == linha_0_do_palco
    assert p['ancora_kv'] == {'texto': 'L1 a', 'acima': 0.0,
                              'trechos': [{'texto': 'L1 a', 'face': 'fy', 'corpo': 12.0}]}


def test_ancora_da_primeira_linha_do_psd_com_dois_estilos_e_a_quebra_inserida():
    # a primeira linha do PSD tem os dois estilos, e a familia insere a quebra entre eles: a ancora leva a linha
    # inteira do PSD, com os trechos dela (a subida maior), e nao so a parte que ficou na linha 0 do palco
    kv = _texto_kv([_run(0, 'L1 a ', PRETO, fonte='Y', corpo=24.0), _run(5, 'L2 b\r', PRETO, corpo=80.0),
                    _run(10, 'L3 c', AZUL, corpo=40.0)])
    p, linhas = _trocar_na_familia(kv, 'L3 c', [0], [4])
    assert [t['texto'] for t in linhas[0]['trechos']] == ['L1 a']
    assert p['ancora_kv'] == {'texto': 'L1 a L2 b', 'acima': 0.0,
                              'trechos': [{'texto': 'L1 a ', 'face': 'fy', 'corpo': 12.0},
                                          {'texto': 'L2 b', 'face': 'fx', 'corpo': 40.0}]}


def test_ancora_do_kv_de_um_estilo_so_com_a_quebra_da_familia_sai_das_linhas_do_psd():
    # rodada 5: no KV de um estilo so (duas cores na mesma face e no mesmo corpo) a ancora tambem sai das linhas do PSD,
    # sem a quebra da familia (a caixa de tinta do KV e a do PSD); sem as pecas base, a das linhas do palco, como antes
    kv = _texto_kv([_run(0, 'L1 a\rL2 b\r', PRETO, corpo=80.0), _run(10, 'L3 c', AZUL, corpo=80.0)])
    novo, linhas = _trocar_na_familia(kv, 'L3 c', [1], [])
    antes, _l = _trocar_na_familia(kv, 'L3 c', [1], [], com_base=False)
    assert [''.join(t['texto'] for t in ln['trechos']) for ln in linhas][0] == 'L1 a L2 b'
    assert novo['ancora_kv'] == {'texto': 'L1 a', 'acima': 0.0}
    assert antes['ancora_kv'] == {'texto': 'L1 a L2 b', 'acima': 0.0}


def test_ancora_do_kv_de_um_estilo_so_com_o_cr_do_comeco_juntado():
    # o KV comeca com CR (a primeira linha do PSD vazia) e a familia junta essa quebra: no palco 'TITULO' sobe para a
    # linha 0, mas a primeira linha de base do render continua uma entrelinha acima da de 'TITULO' no KV. A ancora e a
    # linha do PSD, uma entrelinha (48) abaixo; antes (das linhas do palco) o 0 punha o texto uma entrelinha abaixo
    kv = _texto_kv([_run(0, '\rTITULO\r', PRETO, corpo=80.0), _run(8, 'sub', AZUL, corpo=80.0)])
    novo, linhas = _trocar_na_familia(kv, '\nTITULO\nsub', [1], [])
    antes, _l = _trocar_na_familia(kv, '\nTITULO\nsub', [1], [], com_base=False)
    assert [''.join(t['texto'] for t in ln['trechos']) for ln in linhas] == [' TITULO', 'sub']
    assert novo['ancora_kv'] == {'texto': 'TITULO', 'acima': 48.0}
    assert antes['ancora_kv'] == {'texto': ' TITULO', 'acima': 0.0}
    # a entrelinha da linha do PSD, na escala do formato
    assert [ln['entrelinha'] for ln in edicao._linhas_do_psd({'_texto': kv, '_faces': FACES}, ESCALA)] == [48.0] * 3


def test_ancora_do_kv_de_um_estilo_so_com_a_quebra_inserida_no_espaco():
    # a familia insere a quebra no espaco da linha do PSD ('aceso' e 'ÁGIL', duas cores no mesmo estilo): a ancora
    # e a linha inteira do PSD (a tinta do KV comeca no topo do acento, que so a linha inteira tem), nao so 'aceso'
    agil = 'ÁGIL'
    kv = _texto_kv([_run(0, 'aceso ', PRETO, corpo=80.0), _run(6, agil, AZUL, corpo=80.0)])
    novo, linhas = _trocar_na_familia(kv, 'aceso %s novo' % agil, [], [5])
    antes, _l = _trocar_na_familia(kv, 'aceso %s novo' % agil, [], [5], com_base=False)
    assert [''.join(t['texto'] for t in ln['trechos']) for ln in linhas] == ['aceso', agil]
    assert novo['ancora_kv'] == {'texto': 'aceso ' + agil, 'acima': 0.0}
    assert antes['ancora_kv'] == {'texto': 'aceso', 'acima': 0.0}
    # o texto editado continua nas linhas da familia, com as cores do KV
    assert _cores(novo) == [[('aceso', PRETO)], [(agil + ' novo', AZUL)]]


# ------------------------------------------------------------------ o KV que comeca com uma quebra
def _comeca_com_cr():
    # a primeira linha do KV vazia (o texto comeca com CR): a linha 0 do palco nao tem trecho
    return _texto_kv([_run(0, '\rL1 a\r', PRETO, corpo=80.0), _run(6, 'L2 b', AZUL, fonte='Y', corpo=40.0)])


@pytest.mark.parametrize('com_base', [True, False])
def test_kv_que_comeca_com_cr_nao_quebra_trocar_texto(com_base):
    # antes: IndexError em p['linhas'][0]['trechos'][0]
    palco_kv, _base = _palco(_comeca_com_cr())
    assert palco_kv['pecas'][0]['linhas'][0]['trechos'] == []
    p = _trocar(_comeca_com_cr(), 'novo\nL2 b', com_base=com_base)
    # com a base, as cores do KV; sem ela, o estilo do primeiro trecho do palco (o da linha 1 do KV)
    assert _cores(p) == [[('novo', PRETO)], [('L2 b', AZUL if com_base else PRETO)]]
    assert p['texto_editado'] is True
    # a ancora e a primeira linha do KV com texto, uma entrelinha abaixo da primeira linha de base
    assert (p['ancora_kv']['texto'], p['ancora_kv']['acima']) == ('L1 a', 48.0)


def test_peca_sem_trecho_nenhum_e_sem_base_fica_como_esta():
    # o palco sem trecho em linha nenhuma e sem a base para a regra R3: nada a trocar
    palco, _base = _palco(_comeca_com_cr(), [{'trechos': [], 'entrelinha': 24.0}])
    antes = copy.deepcopy(palco['pecas'][0])
    p = edicao.trocar_texto(palco, 'el1', 'novo')['pecas'][0]
    assert p == antes


# ------------------------------------------------------------------ a caixa de paragrafo (ancora_kv['caixa'])
# as faces servidas com as metricas: a ascendente de X e 0,8 do corpo, a de Y 0,9
FACES_COM_METRICAS = {'fx': {'id': 'fx', 'metricas': {'ascender': 800, 'unidades_por_em': 1000}},
                      'fy': {'id': 'fy', 'metricas': {'ascender': 900, 'unidades_por_em': 1000}}}


def _na_caixa(texto_kv):
    return dict(texto_kv, tipo_caixa='paragrafo', box_bounds=[0.0, 0.0, 200.0, 100.0])


def _topo_e_base(fonte_base='Y', corpo_base=40.0):
    # 'TOPO' preto na face X a 10 pt (no texto; a matriz dobra) e 'base' azul na face Y a 20 pt, na caixa de paragrafo
    return _na_caixa(_texto_kv([_run(0, 'TOPO\r', PRETO, corpo=20.0),
                                _run(5, 'base', AZUL, fonte=fonte_base, corpo=corpo_base)]))


def _de_ponto(texto_kv):
    return {k: v for k, v in texto_kv.items() if k not in ('tipo_caixa', 'box_bounds')}


# a primeira linha de base do texto que comeca em 'base' desce a ascendente de Y a 20 pt menos a de X a 10 pt, no
# espaco do texto, vezes a escala da matriz (2); a do elemento no formato multiplica depois
DESCE = (0.9 * 20.0 - 0.8 * 10.0) * 2.0


@pytest.mark.parametrize('linhas,esperado', [
    (['base'], DESCE),
    # a primeira linha vazia: vale a primeira linha cheia (render.texto.origem_das_linhas)
    (['', 'base'], DESCE),
    # a palavra nova no comeco da linha herda a da direita ('base')
    (['novo base'], DESCE),
    # a primeira linha do texto editado e a do KV
    (['TOPO', 'base'], 0.0),
    (['TOPO', 'novo'], 0.0),
    # a primeira linha com as duas faces: vale a maior ascendente ('novo' trocou 'base' e herda Y)
    (['TOPO novo'], DESCE),
])
@pytest.mark.parametrize('escala', [0.25, 1.0])
def test_desvio_da_caixa_de_paragrafo(linhas, esperado, escala):
    pb = {'_texto': _topo_e_base(), '_faces': dict(FACES)}
    assert edicao._desvio_da_caixa(pb, linhas, FACES_COM_METRICAS, escala) == pytest.approx(esperado * escala)


def test_desvio_da_caixa_e_zero_fora_da_caixa_ou_sem_o_que_medir():
    pb = {'_texto': _topo_e_base(), '_faces': dict(FACES)}
    # texto de ponto: a primeira linha de base e a origem da matriz
    ponto = dict(pb, _texto=_de_ponto(_topo_e_base()))
    assert edicao._desvio_da_caixa(ponto, ['base'], FACES_COM_METRICAS, 0.5) == 0.0
    # o KV de um estilo so na caixa (duas cores na mesma face e no mesmo corpo)
    um = {'_texto': _topo_e_base(fonte_base='X', corpo_base=20.0), '_faces': dict(FACES)}
    assert edicao._desvio_da_caixa(um, ['base'], FACES_COM_METRICAS, 0.5) == 0.0
    # sem as faces, sem a escala ou sem as metricas
    assert edicao._desvio_da_caixa(pb, ['base'], None, 0.5) == 0.0
    assert edicao._desvio_da_caixa(pb, ['base'], FACES_COM_METRICAS, None) == 0.0
    assert edicao._desvio_da_caixa(pb, ['base'], {'fx': {'id': 'fx'}, 'fy': {'id': 'fy'}}, 0.5) == 0.0
    assert edicao._desvio_da_caixa({}, ['base'], FACES_COM_METRICAS, 0.5) == 0.0


def _trocar_com_faces(texto_kv, texto, palco=None, faces=FACES_COM_METRICAS):
    palco, base = _palco(texto_kv) if palco is None else palco
    return edicao.trocar_texto(palco, 'el1', texto, base=base, escala=ESCALA, faces=faces)['pecas'][0]


def test_trocar_texto_grava_a_caixa_so_quando_nao_e_zero():
    mesmo = _palco(_topo_e_base())
    assert _trocar_com_faces(None, 'base', mesmo)['ancora_kv']['caixa'] == pytest.approx(DESCE * ESCALA)
    # o mesmo palco com a primeira linha do KV de volta: a caixa sai
    assert 'caixa' not in _trocar_com_faces(None, 'TOPO\nbase', mesmo)['ancora_kv']
    # sem as faces (a chamada de antes), no texto de ponto e no KV de um estilo so: sem a chave
    assert 'caixa' not in _trocar_com_faces(_topo_e_base(), 'base', faces=None)['ancora_kv']
    assert 'caixa' not in _trocar_com_faces(_de_ponto(_topo_e_base()), 'base')['ancora_kv']
    um = _trocar_com_faces(_topo_e_base(fonte_base='X', corpo_base=20.0), 'base')
    assert set(um['ancora_kv']) == {'texto', 'acima'}


@pytest.mark.parametrize('faces', [
    # a primeira linha do KV ('TOPO') numa fonte fora do job (W: sem face no palco)
    None,
    # ou na face X servida sem as metricas
    {'fx': {'id': 'fx'}, 'fy': FACES_COM_METRICAS['fy']},
])
def test_caixa_sem_as_metricas_da_primeira_linha_do_kv_fica_de_fora(faces):
    # rodada 4: sem a ascendente de um pedaco da primeira linha cheia do KV, o render conta 0 nele e o desvio sairia
    # de uma ascendente que o palco nao tem: 0, e o palco fica sem a 'caixa' (antes: a ascendente inteira de Y)
    kv = _topo_e_base()
    if faces is None:
        kv['runs'][0]['fonte_ps'] = 'W'
        faces = FACES_COM_METRICAS
    pb = {'_texto': kv, '_faces': dict(FACES)}
    assert edicao._desvio_da_caixa(pb, ['base'], faces, ESCALA) == 0.0
    p = _trocar_com_faces(copy.deepcopy(kv), 'base', faces=faces)
    assert 'caixa' not in p['ancora_kv']
    # a mesma conta com as metricas da primeira linha da a caixa
    kv['runs'][0]['fonte_ps'] = 'X'
    assert _trocar_com_faces(copy.deepcopy(kv), 'base')['ancora_kv']['caixa'] == pytest.approx(DESCE * ESCALA)


# ------------------------------------------------------------------ a medida no Chromium (medir_editados)
FORA_DO_JOB = 'FonteForaDoJob'


def _laudo_com_respiro(laudo, fonte_respiro, fonte_corpo, corpo_respiro=0.25, titulo='HAX O\r'):
    """Copia do laudo do job de tres linhas com o titulo trocado por 'HAX O' e a linha vazia (o CR sem tinta, o
    respiro, a corpo_respiro do corpo) e 'HOAXAV' a meio corpo: o KV de varios estilos. titulo 'HAX O' (sem o CR): o CR
    sem tinta e a quebra entre as duas linhas, sem linha vazia. Devolve (laudo, layer_id)."""
    lau = copy.deepcopy(laudo)
    c = next(c for c in lau['camadas'] if c.get('nome') == 'tres-linhas')
    t = c['texto']
    r0 = t['runs'][0]
    corpo = float(r0['corpo_espaco_texto'])
    n = len(titulo)
    t['conteudo'] = titulo + '\rHOAXAV'
    t['runs'] = [dict(r0, inicio=0, fim=n, texto=titulo, tem_tinta=True),
                 dict(r0, inicio=n, fim=n + 1, texto='\r', tem_tinta=False, tem_caractere_visivel=False,
                      fonte_ps=fonte_respiro, corpo_espaco_texto=corpo * corpo_respiro),
                 dict(r0, inicio=n + 1, fim=n + 7, texto='HOAXAV', tem_tinta=True, fonte_ps=fonte_corpo,
                      corpo_espaco_texto=corpo / 2.0)]
    t['paragrafos'] = [dict(t['paragrafos'][0], inicio=0, fim=n + 8)]
    return lau, c['identidade']['layer_id']


def _medir(job, pedidos):
    """{nome: (medida, laudo, layer_id)} de medir_editados para cada (nome, linhas, argumentos de _laudo_com_respiro),
    com o cache limpo antes e depois."""
    from vapt import contratos
    from vapt.briefing import modelo as mb
    from vapt.derivacao import medida_quebras
    laudo = contratos.ler(job / mb.ARQUIVO_LAUDO, 'laudo/1')
    estado = contratos.ler(job / 'estado.json', 'estado/1')
    medida_quebras.limpar_cache()
    try:
        saida = {}
        for nome, linhas, args in pedidos:
            lau, lid = _laudo_com_respiro(laudo, *args)
            [m] = medida_quebras.medir_editados(job, lau, estado, [(lid, linhas)]).values()
            saida[nome] = (m, lau, lid)
        return saida
    finally:
        medida_quebras.limpar_cache()


def test_medida_confere_a_face_so_dos_trechos_com_tinta(job_tres_linhas):
    from vapt.render import autoteste
    ps = autoteste.NOME_PS
    # o DA so poe um Enter (as palavras em volta do respiro ficam pareadas, e ele continua quebra)
    linhas = ['HAX', 'O', '', 'HOAXAV']
    medidas = _medir(job_tres_linhas, [('no_job', linhas, (ps, ps, 0.25)), ('fora', linhas, (FORA_DO_JOB, ps, 0.25)),
                                       ('cheio', linhas, (ps, ps, 1.0)),
                                       ('tinta_fora', linhas, (ps, FORA_DO_JOB, 0.25))])
    # o respiro numa face fora do job nao da face_ausente (antes: a face de todo trecho era conferida) e mede o mesmo
    # que o respiro na face do job: ele nao tem tinta. A linha vazia nao vai a pagina de medida
    assert 'erro' not in medidas['no_job'][0] and 'erro' not in medidas['fora'][0], medidas
    assert medidas['fora'][0] == medidas['no_job'][0]
    assert medidas['no_job'][0]['linhas'] == len([ln for ln in linhas if ln])
    # o trecho com tinta numa face fora do job continua dando face_ausente
    assert medidas['tinta_fora'][0] == {'erro': 'face_ausente'}
    # o respiro guarda o corpo dele na medida: a caixa do respiro cheio desce o que a entrelinha dele passa da do
    # respiro de um quarto do corpo
    def alto(nome):
        caixa = medidas[nome][0]['caixa_doc']
        return caixa[3] - caixa[1]

    def descidas(nome):
        _m, lau, lid = medidas[nome]
        camada = next(c for c in lau['camadas'] if c['identidade']['layer_id'] == lid)
        t = mq.camada_do_editado(camada, linhas)['texto']
        sy = (float(t['matriz'][2]) ** 2 + float(t['matriz'][3]) ** 2) ** 0.5
        return sum(ln['entrelinha'] for ln in rt.linhas_da_camada(t)[1:]) * sy
    assert descidas('cheio') > descidas('no_job')
    assert alto('cheio') - alto('no_job') == pytest.approx(descidas('cheio') - descidas('no_job'), abs=0.5)


def test_medida_da_quebra_sem_tinta_numa_face_fora_do_job_mantem_as_linhas(job_tres_linhas):
    # o CR sem tinta entre duas linhas com tinta, numa face fora do job (o CR que guardou a fonte de um texto apagado),
    # no KV de varios estilos: ele continua quebra (_no_mesmo_papel), e a medida sai com as duas linhas, como a do
    # mesmo CR na face do job (antes, fontes.medicao.montar pulava o run sem face inteiro, com a quebra dele, e as duas
    # linhas do DA viravam uma na medida, com a caixa larga)
    from vapt.render import autoteste
    ps = autoteste.NOME_PS
    linhas = ['HAX O', 'HOAXAV']
    medidas = _medir(job_tres_linhas, [('no_job', linhas, (ps, ps, 0.25, 'HAX O')),
                                       ('fora', linhas, (FORA_DO_JOB, ps, 0.25, 'HAX O'))])
    assert medidas['no_job'][0]['linhas'] == len(linhas), medidas
    assert medidas['fora'][0] == medidas['no_job'][0], medidas


def _camada_de_medida(meio, fonte_do_meio='W'):
    # 'AB' e 'CD' na face X, e entre eles o run sem tinta 'meio' (quebras) numa fonte sem face (W)
    runs = [{'inicio': 0, 'fim': 2, 'texto': 'AB', 'fonte_ps': 'X', 'corpo_espaco_texto': 10.0, 'tem_tinta': True},
            {'inicio': 2, 'fim': 2 + len(meio), 'texto': meio, 'fonte_ps': fonte_do_meio, 'corpo_espaco_texto': 5.0,
             'tem_tinta': False},
            {'inicio': 2 + len(meio), 'fim': 4 + len(meio), 'texto': 'CD', 'fonte_ps': 'X', 'corpo_espaco_texto': 10.0,
             'tem_tinta': True}]
    return {'identidade': {'layer_id': 7}, 'texto': {'tipo_caixa': 'ponto', 'runs': runs}}


@pytest.mark.parametrize('meio,ids', [
    ('\r', ['l0_0', 'l0_1']),
    # dois CR: a linha vazia do meio (l0_1) nao vai a pagina, mas conta
    ('\r\r', ['l0_0', 'l0_2']),
    ('\n\r\r', ['l0_0', 'l0_3']),
])
def test_montar_abre_as_linhas_das_quebras_do_run_sem_face(meio, ids):
    # fontes.medicao.montar: o run sem face nao e desenhado, mas cada quebra dele abre uma linha, como no render
    # (render.texto.linhas_da_camada); antes 'AB' e 'CD' saiam numa linha so
    from vapt.fontes import medicao
    face = {'id': 'f1', 'peso_declarado': 400, 'cmap': [[32, 126]]}
    pagina, plano = medicao.montar([_camada_de_medida(meio)], {'X': face, 'W': None}, [], 'pp')
    assert [ln['id'] for ln in plano['camadas'][0]['linhas']] == ids
    assert [s['fonte_ps'] for s in plano['camadas'][0]['spans']] == ['X', 'X']
    # a mesma conta que o run das quebras com face
    _p, com_face = medicao.montar([_camada_de_medida(meio, 'X')], {'X': face}, [], 'pp')
    assert [ln['id'] for ln in com_face['camadas'][0]['linhas']] == ids
    assert pagina.count('class="l"') == 2


# ------------------------------------------------------------------ na pagina: a linha de base no KV de dois corpos
CORPO_GRANDE, CORPO_PEQUENO = 60.0, 36.0
LINHAS_DOIS_CORPOS = ('HAX O', 'HOAXAV', 'OX VA')


def _psd_dois_corpos(destino, ps):
    """PSD 540 x 960 como o do relato da 0.9.4 (test_tela_revisao_094._psd): o titulo de tres linhas, as duas primeiras
    a 60 pt e a ultima a 36 pt, com a camada de pixels no topo da tinta da primeira linha, e o logo."""
    from PIL import Image
    from psd_tools import PSDImage

    import test_fontes_apoio as fap
    import test_render_apoio as rap
    import test_tela_palco as tp
    p = PSDImage.new('RGB', (540, 960), color=(255, 255, 255))
    p.create_pixel_layer(Image.new('RGBA', (540, 960), (0, 140, 70, 255)), name='fundo-sintetico')
    corpos = (CORPO_GRANDE, CORPO_GRANDE, CORPO_PEQUENO)
    larga = max(fap.largura(t, c, avancos=tp.AVANCOS) for t, c in zip(LINHAS_DOIS_CORPOS, corpos))
    alto = int(1.2 * sum(corpos))
    topo, esq = 89, 30
    t = p.create_pixel_layer(Image.new('RGBA', (int(larga) + 2, alto), (20, 20, 20, 255)), name='titulo-sintetico',
                             top=topo, left=esq)
    trechos = [('\r'.join(LINHAS_DOIS_CORPOS[:2]) + '\r', 0, CORPO_GRANDE, 0),
               (LINHAS_DOIS_CORPOS[2], 0, CORPO_PEQUENO, 0)]
    fap._virar_texto(t, trechos, [ps], larga, x=float(esq), y=float(topo + CORPO_GRANDE * 0.7))
    p.create_pixel_layer(Image.new('RGBA', (140, 80), (255, 255, 255, 255)), name='logo-sintetico', top=850, left=380)
    return rap._salvar(p, destino)


@pytest.fixture(scope='module')
def dois_corpos(tmp_path_factory):
    import test_derivacao_apoio as ap
    import test_fontes_apoio as fap
    from vapt import contratos
    from vapt.briefing import modelo as mb
    from vapt.job import nucleo
    from vapt.render import autoteste
    base = tmp_path_factory.mktemp('dois-corpos')
    fontes = base / 'origem-fontes'
    fap.gravar(fontes, 'autoteste.ttf', autoteste.gerar_fonte())
    job = base / 'job'
    nucleo.criar(job, _psd_dois_corpos(base / 'origem' / 'kv.psd', autoteste.NOME_PS), 'c', fontes=[fontes])
    r = nucleo.proxima(job, todas=True)
    assert r.codigo == 0, (r.situacao, r.linhas_humanas)
    laudo = contratos.ler(job / mb.ARQUIVO_LAUDO, 'laudo/1')
    ids = {c['nome']: c['identidade']['layer_id'] for c in laudo['camadas']}
    funcoes = {ids['fundo-sintetico']: 'fundo', ids['titulo-sintetico']: 'titulo',
               ids['logo-sintetico']: 'logo_principal'}
    b = ap.briefing(funcoes=funcoes, formatos=[ap.formato('f1080x1080', 1080, 1080,
                                                          rotacao={'graus': 0, 'sentido': None})])
    b.pop('cabecalho')
    b.pop('job_id')
    arq = base / 'fixture.json'
    arq.write_text(json.dumps(b), encoding='utf-8')
    mb.importar_teste(job, arq)
    return {'job': job, 'layer_id': ids['titulo-sintetico']}


@pytest.mark.skipif(sys.platform != 'win32', reason='o isolador dos filhos roda no Windows')
def test_pagina_poe_a_base_do_texto_editado_na_do_kv_de_dois_corpos(dois_corpos, tmp_path):
    # o DA deixa so a linha de corpo menor: o primeiro trecho do texto editado tem outro corpo que a primeira linha do
    # KV, e a pagina mede a subida dela nos trechos dela (ancora_kv['trechos']); a caixa da tela bate com a do motor
    # (antes a tela punha o texto acima da linha de base do KV, o que a subida da linha do KV passa da do corpo menor)
    import test_tela_edicao as ted
    import test_tela_revisao_094 as r094
    texto = LINHAS_DOIS_CORPOS[2]
    vista = {}

    def corpo(pg, job, gid, titulo, _logo):
        r094._aplicar_no_editor(pg, ted, titulo, texto)
        vista['caixa'] = [float(v) for v in pg.evaluate(r094.JS_CAIXA_EDITADA).split(',')]

    r094._na_tela_do_relato(dois_corpos, tmp_path / 'tela', corpo)
    job = r094._copia(dois_corpos, tmp_path / 'motor')
    conteudo = r094._gravar(job, texto)
    no_motor = r094._editado(r094._deriv(job, 'f1080x1080'), dois_corpos['layer_id'])['caixa_texto_editado']
    assert vista['caixa'] == pytest.approx(no_motor, abs=3), (vista['caixa'], no_motor)  # numero-neutro: px
    # o palco levou os trechos da primeira linha do KV, e o texto de ponto nao tem a caixa
    gid = next(g for g, f in conteudo['familias'].items() if 'f1080x1080' in f['formatos'])
    eid = r094._titulo(conteudo, gid)
    r = conteudo['editar']({'familia': gid, 'versao': None,
                            'edicoes': [{'elemento': eid, 'acao': 'texto', 'texto': texto}]})
    ancora = _peca_do_titulo(r['membros'][0], eid)['ancora_kv']
    assert [t['texto'] for t in ancora['trechos']] == [LINHAS_DOIS_CORPOS[0]] and 'caixa' not in ancora, ancora


# ------------------------------------------------------------------ na pagina: o espaco sem tinta no comeco do KV
LINHAS_ESPACO = ('HAX O', 'HOAXAV')
CORPO_ESPACO = 3 * CORPO_GRANDE


def _psd_espaco_no_comeco(destino, ps):
    """PSD 540 x 960: o titulo de duas linhas numa face e num corpo (60 pt), com um espaco sem tinta no comeco da
    primeira linha na mesma face a 180 pt (o KV de um estilo so: o espaco nao conta como estilo), e o logo."""
    from PIL import Image
    from psd_tools import PSDImage

    import test_fontes_apoio as fap
    import test_render_apoio as rap
    import test_tela_palco as tp
    p = PSDImage.new('RGB', (540, 960), color=(255, 255, 255))
    p.create_pixel_layer(Image.new('RGBA', (540, 960), (0, 140, 70, 255)), name='fundo-sintetico')
    larga = max(fap.largura(' ', CORPO_ESPACO, avancos=tp.AVANCOS) + fap.largura(LINHAS_ESPACO[0], CORPO_GRANDE,
                                                                                 avancos=tp.AVANCOS),
                fap.largura(LINHAS_ESPACO[1], CORPO_GRANDE, avancos=tp.AVANCOS))
    alto = int(1.2 * CORPO_GRANDE * len(LINHAS_ESPACO))
    topo, esq = 89, 30
    t = p.create_pixel_layer(Image.new('RGBA', (int(larga) + 2, alto), (20, 20, 20, 255)), name='titulo-sintetico',
                             top=topo, left=esq)
    trechos = [(' ', 0, CORPO_ESPACO, 0), ('\r'.join(LINHAS_ESPACO), 0, CORPO_GRANDE, 0)]
    fap._virar_texto(t, trechos, [ps], larga, x=float(esq), y=float(topo + CORPO_GRANDE * 0.7))
    p.create_pixel_layer(Image.new('RGBA', (140, 80), (255, 255, 255, 255)), name='logo-sintetico', top=850, left=380)
    return rap._salvar(p, destino)


@pytest.fixture(scope='module')
def espaco_no_comeco(tmp_path_factory):
    import test_derivacao_apoio as ap
    import test_fontes_apoio as fap
    from vapt import contratos
    from vapt.briefing import modelo as mb
    from vapt.job import nucleo
    from vapt.render import autoteste
    base = tmp_path_factory.mktemp('espaco-no-comeco')
    fontes = base / 'origem-fontes'
    fap.gravar(fontes, 'autoteste.ttf', autoteste.gerar_fonte())
    job = base / 'job'
    nucleo.criar(job, _psd_espaco_no_comeco(base / 'origem' / 'kv.psd', autoteste.NOME_PS), 'c', fontes=[fontes])
    r = nucleo.proxima(job, todas=True)
    assert r.codigo == 0, (r.situacao, r.linhas_humanas)
    laudo = contratos.ler(job / mb.ARQUIVO_LAUDO, 'laudo/1')
    ids = {c['nome']: c['identidade']['layer_id'] for c in laudo['camadas']}
    funcoes = {ids['fundo-sintetico']: 'fundo', ids['titulo-sintetico']: 'titulo',
               ids['logo-sintetico']: 'logo_principal'}
    b = ap.briefing(funcoes=funcoes, formatos=[ap.formato('f1080x1080', 1080, 1080,
                                                          rotacao={'graus': 0, 'sentido': None})])
    b.pop('cabecalho')
    b.pop('job_id')
    arq = base / 'fixture.json'
    arq.write_text(json.dumps(b), encoding='utf-8')
    mb.importar_teste(job, arq)
    return {'job': job, 'layer_id': ids['titulo-sintetico']}


# o primeiro trecho do texto editado no palco e o primeiro com texto visivel, e a subida de cada um na fonte dele
JS_TRECHOS_DO_COMECO = '''() => {
  const ts = Array.from(document.querySelectorAll("#palco .texto.editado .trecho"));
  const cheio = ts.find(function (s) { return s.textContent.trim(); });
  return JSON.stringify([ts[0].textContent, parseFloat(getComputedStyle(ts[0]).fontSize),
                         cheio.textContent, parseFloat(getComputedStyle(cheio).fontSize)]);
}'''


@pytest.mark.skipif(sys.platform != 'win32', reason='o isolador dos filhos roda no Windows')
def test_pagina_mede_a_subida_no_primeiro_trecho_com_texto(espaco_no_comeco, tmp_path):
    # rodada 5 (medirTexto): no KV de um estilo so, o espaco sem tinta do comeco tem outro corpo e fica com o run dele
    # (o vao do comeco pareado, a palavra nova so no fim), e vira o primeiro trecho do texto editado no palco. A pagina
    # mede a subida da linha do KV no primeiro trecho com texto visivel; antes media no corpo do espaco (o triplo) e a
    # primeira linha de base do texto editado subia na tela. A caixa da tela bate com a do motor (a linha mais a
    # esquerda e 'HOAXAV', sem o espaco, como no KV)
    import test_tela_edicao as ted
    import test_tela_revisao_094 as r094
    texto = ' ' + '\n'.join(LINHAS_ESPACO) + '\nOX'
    vista = {}

    def corpo(pg, job, gid, titulo, _logo):
        r094._aplicar_no_editor(pg, ted, titulo, texto)
        vista['caixa'] = [float(v) for v in pg.evaluate(r094.JS_CAIXA_EDITADA).split(',')]
        vista['trechos'] = json.loads(pg.evaluate(JS_TRECHOS_DO_COMECO))

    r094._na_tela_do_relato(espaco_no_comeco, tmp_path / 'tela', corpo)
    # o cenario do conserto: o primeiro trecho do palco e o espaco, no triplo do corpo do primeiro com texto
    espaco, corpo_espaco, cheio, corpo_cheio = vista['trechos']
    assert espaco == ' ' and cheio.startswith(LINHAS_ESPACO[0]), vista['trechos']
    assert corpo_espaco == pytest.approx(3 * corpo_cheio, rel=0.01), vista['trechos']
    job = r094._copia(espaco_no_comeco, tmp_path / 'motor')
    conteudo = r094._gravar(job, texto)
    no_motor = r094._editado(r094._deriv(job, 'f1080x1080'), espaco_no_comeco['layer_id'])['caixa_texto_editado']
    assert vista['caixa'] == pytest.approx(no_motor, abs=3), (vista['caixa'], no_motor)  # numero-neutro: px
    # o palco: o KV de um estilo so (a ancora sem os trechos), e o espaco com o run dele no texto editado
    gid = next(g for g, f in conteudo['familias'].items() if 'f1080x1080' in f['formatos'])
    eid = r094._titulo(conteudo, gid)
    r = conteudo['editar']({'familia': gid, 'versao': None,
                            'edicoes': [{'elemento': eid, 'acao': 'texto', 'texto': texto}]})
    p = _peca_do_titulo(r['membros'][0], eid)
    assert set(p['ancora_kv']) == {'texto', 'acima'} and p['ancora_kv']['texto'] == ' ' + LINHAS_ESPACO[0], p
    [t0, t1] = p['linhas'][0]['trechos']
    assert (t0['texto'], t0['face']) == (' ', t1['face']) and t0['corpo'] == pytest.approx(3 * t1['corpo'])
