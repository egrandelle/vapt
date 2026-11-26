# -*- coding: utf-8 -*-
"""Os trechos do texto editado pelo DA (regra R3, derivacao.quebras.runs_do_editado): o texto editado nao perde a cor
dos trechos do KV. Base: o KV de tres linhas, as duas primeiras pretas ('L1 a', 'L2 b') e a ultima azul ('L3 c'), com
a quebra de paragrafo (CR) como o Photoshop grava. Cada caso diz as linhas do DA e os trechos que saem (texto, cor).
Tambem: o vao igual ao do KV entre duas palavras pareadas fica com o run do KV (o CR de uma linha nao tocada guarda o
run dela), e o espaco ou a quebra de um run sem tinta guarda o run so no mesmo papel (_no_mesmo_papel): a quebra que
continua quebra fica com o run dela (o respiro), em qualquer KV, de um estilo ou de varios, e a que vira espaco (ou o
contrario) herda o vizinho; a regra nao olha a cor. O vao so de quebras com mais ou menos linhas vazias alinha as
quebras (a primeira, a ultima e a do meio do KV); o vao antes da primeira palavra (as linhas vazias do comeco) conta
como pareado quando a primeira palavra pareia (rodada 5). O texto igual ao do KV sai com os runs do KV."""
import pytest

from vapt.derivacao import quebras as mq

PRETO, AZUL = '#000000', '#0000FF'


def _run(inicio, texto, cor, **mais):
    r = {'inicio': inicio, 'fim': inicio + len(texto), 'texto': texto, 'tem_tinta': True,
         'tem_caractere_visivel': True, 'fonte_ps': 'X', 'corpo_espaco_texto': 10.0, 'autoleading': True,
         'kerning': 3, 'cor_hex': cor}
    r.update(mais)
    return r


def _kv():
    return [_run(0, 'L1 a\rL2 b\r', PRETO), _run(10, 'L3 c', AZUL)]  # numero-neutro: o inicio do trecho azul


def _trechos(linhas, runs=None, separador='\r'):
    saida = mq.runs_do_editado(_kv() if runs is None else runs, linhas, separador)
    s = separador.join(linhas)
    # os trechos cobrem o texto novo inteiro, em ordem, sem kerning manual
    assert ''.join(r['texto'] for r in saida) == s
    assert all(s[r['inicio']:r['fim']] == r['texto'] for r in saida)
    assert all(r['kerning'] is None for r in saida)
    return [(r['texto'], r['cor_hex']) for r in saida]


def _cor_por_caractere(linhas, runs=None):
    saida = mq.runs_do_editado(_kv() if runs is None else runs, linhas)
    return ''.join(('P' if r['cor_hex'] == PRETO else 'A') * len(r['texto']) for r in saida)


@pytest.mark.parametrize('linhas,esperado', [
    # so a quebra mudou: cada caractere com o trecho de mesma posicao
    (['L1 a', 'L2 b', 'L3 c'], [('L1 a\rL2 b\r', PRETO), ('L3 c', AZUL)]),
    # juntar as linhas 2 e 3 (o caso relatado): o azul fica
    (['L1 a', 'L2 b L3 c'], [('L1 a\rL2 b ', PRETO), ('L3 c', AZUL)]),
    # quebrar num espaco
    (['L1', 'a', 'L2 b', 'L3 c'], [('L1\ra\rL2 b\r', PRETO), ('L3 c', AZUL)]),
    # trocar a palavra azul: a nova fica com a cor da que estava no lugar
    (['L1 a', 'L2 b', 'L3 d'], [('L1 a\rL2 b\r', PRETO), ('L3 d', AZUL)]),
    # trocar na fronteira: a primeira nova herda a preta, a segunda a azul
    (['L1 a', 'L2 y', 'z c'], [('L1 a\rL2 y\r', PRETO), ('z c', AZUL)]),
    # inserir no meio: herda a palavra a esquerda
    (['L1 a', 'L2 x b', 'L3 c'], [('L1 a\rL2 x b\r', PRETO), ('L3 c', AZUL)]),
    (['L1 a', 'L2 b', 'L3 x c'], [('L1 a\rL2 b\r', PRETO), ('L3 x c', AZUL)]),
    # inserir no fim da linha 2: a esquerda e preta
    (['L1 a', 'L2 b x', 'L3 c'], [('L1 a\rL2 b x\r', PRETO), ('L3 c', AZUL)]),
    # inserir no comeco da linha 3: sem palavra a esquerda na linha, herda a da direita
    (['L1 a', 'L2 b', 'x L3 c'], [('L1 a\rL2 b\r', PRETO), ('x L3 c', AZUL)]),
    # apagar: o resto fica como estava
    (['L1 a', 'L2', 'L3 c'], [('L1 a\rL2\r', PRETO), ('L3 c', AZUL)]),
    (['L1 a', 'L2 b', 'L3'], [('L1 a\rL2 b\r', PRETO), ('L3', AZUL)]),
    # linha nova no meio: herda o ultimo caractere antes dela
    (['L1 a', 'L2 b', 'novo', 'L3 c'], [('L1 a\rL2 b\rnovo\r', PRETO), ('L3 c', AZUL)]),
    # linha nova no fim: herda o ultimo caractere antes dela, o azul
    (['L1 a', 'L2 b', 'L3 c', 'fim'], [('L1 a\rL2 b\r', PRETO), ('L3 c\rfim', AZUL)]),
    # texto todo novo: as novas herdam as antigas na ordem
    (['Outro', 'texto'], [('Outro\rtexto', PRETO)]),
])
def test_tabela_da_regra(linhas, esperado):
    assert _trechos(linhas) == esperado


def test_separador_lf_para_o_render():
    assert _trechos(['L1 a', 'L2 b L3 c'], separador='\n') == [('L1 a\nL2 b ', PRETO), ('L3 c', AZUL)]


def test_espaco_e_quebra_trocados_dao_o_mesmo_estilo():
    # a mesma edicao, com a quebra da familia aplicada ou nao (linhas_do_editado): o estilo de cada caractere e o mesmo
    cru = mq.linhas_editadas('L1 a\nL2 b\nL3 d')
    familia = mq.linhas_editadas('L1 a\nL2 b\nL3 d', {'aprovadas': [1], 'inseridas': [2]})
    assert familia == ['L1', 'a L2 b', 'L3 d']
    assert _cor_por_caractere(cru) == _cor_por_caractere(familia) == 'P' * 10 + 'A' * 4  # numero-neutro: os caracteres
    # so a quebra: o mesmo estilo em qualquer distribuicao das quebras
    assert _cor_por_caractere(['L1 a L2 b L3 c']) == _cor_por_caractere(['L1', 'a', 'L2', 'b', 'L3', 'c'])


def test_palavra_de_duas_cores_fica_de_duas_cores():
    runs = [_run(0, 'AB', PRETO), _run(2, 'CD', AZUL)]  # numero-neutro: o inicio do trecho azul
    assert _trechos(['ABCD x'], runs) == [('AB', PRETO), ('CD x', AZUL)]
    assert _trechos(['ABCD', 'x'], runs) == [('AB', PRETO), ('CD\rx', AZUL)]


def test_trechos_que_so_mudavam_o_kerning_viram_um():
    runs = [_run(0, 'AB', PRETO, kerning=5), _run(2, ' CD', PRETO, kerning=0)]  # numero-neutro: o kerning do par
    assert _trechos(['AB CD x'], runs) == [('AB CD x', PRETO)]


def test_tem_tinta_e_recalculado():
    # o espaco de um run sem tinta (de outra cor) que vira quebra herda o vizinho com tinta: um trecho so, com tinta
    runs = [_run(0, 'AB', PRETO), _run(2, ' ', AZUL, tem_tinta=False), _run(3, 'CD', PRETO)]  # numero-neutro: inicios
    saida = mq.runs_do_editado(runs, ['AB', 'CD'])
    assert [(r['texto'], r['tem_tinta']) for r in saida] == [('AB\rCD', True)]
    # o espaco que continua espaco (o texto igual ao do KV) guarda o run sem tinta dele, e tem_tinta sai False nele
    saida = mq.runs_do_editado(runs, ['AB CD'])
    assert [(r['texto'], r['tem_tinta'], r['cor_hex']) for r in saida] == \
        [('AB', True, PRETO), (' ', False, AZUL), ('CD', True, PRETO)]
    # o trecho so de separador que sobra (o texto novo sem tinta nenhuma) recalcula tem_tinta
    saida = mq.runs_do_editado([_run(0, 'AB', PRETO)], ['  '])
    assert [(r['texto'], r['tem_tinta']) for r in saida] == [('  ', False)]
    assert mq.runs_do_editado([_run(0, '\r', PRETO, tem_tinta=False)], ['AB']) is None


def _kv_cr_do_meio(fonte_do_cr):
    # o KV de uma cor na vista com a quebra do meio num run sem tinta de outro estilo (o CR que guardou a cor, a fonte
    # e o corpo de um texto apagado; fonte None: a fonte que nem esta no job)
    return [_run(0, 'HAH', PRETO),
            _run(3, '\r', AZUL, tem_tinta=False, tem_caractere_visivel=False, fonte_ps=fonte_do_cr,
                 corpo_espaco_texto=40.0), _run(4, 'HOX', PRETO)]  # numero-neutro: os inicios


@pytest.mark.parametrize('fonte_do_cr', ['Y', None])
@pytest.mark.parametrize('linhas', [['HAH HOX'], ['HAH novo HOX'], ['HAH', 'novo HOX']])
def test_cr_do_meio_sem_tinta_de_outro_estilo_herda_o_vizinho(linhas, fonte_do_cr):
    # a quebra que vira espaco, ou que fica fora do par (a palavra inserida junto dela), herda o vizinho com tinta, e o
    # texto editado sai num trecho so, o de antes da R3
    kv = _kv_cr_do_meio(fonte_do_cr)
    s = '\r'.join(linhas)
    assert mq.runs_do_editado(kv, linhas) == [dict(kv[0], inicio=0, fim=len(s), texto=s, kerning=None, tem_tinta=True)]
    assert mq.runs_do_editado(kv, linhas) == mq.runs_do_editado([kv[0]], linhas)


@pytest.mark.parametrize('fonte_do_cr', ['Y', None])
@pytest.mark.parametrize('linhas', [['HAH', 'HOX'], ['HAH', '', 'HOX'], ['HAH', '', '', 'HOX']])
def test_cr_do_meio_sem_tinta_que_continua_quebra_guarda_o_run(linhas, fonte_do_cr):
    # rodada 4 (_no_mesmo_papel): a quebra que continua quebra guarda o run sem tinta dela, mesmo no KV de um estilo
    # so na vista (o palco e o render seguem o KV nela: a entrelinha do KV); as linhas vazias que o DA poe alinham com
    # ela (o vao so de quebras)
    kv = _kv_cr_do_meio(fonte_do_cr)
    saida = mq.runs_do_editado(kv, linhas)
    quebras = '\r' * (len(linhas) - 1)
    assert [(r['texto'], r['tem_tinta'], r['fonte_ps'], r['corpo_espaco_texto']) for r in saida] == \
        [('HAH', True, 'X', 10.0), (quebras, False, fonte_do_cr, 40.0), ('HOX', True, 'X', 10.0)]
    assert [r['inicio'] for r in saida] == [0, 3, 3 + len(quebras)]  # numero-neutro: as posicoes no texto novo


@pytest.mark.parametrize('runs', [
    _kv(),
    _kv_cr_do_meio('Y'),
    # o espaco sem tinta de outra fonte e outro corpo
    [_run(0, 'HAH', PRETO), _run(3, ' ', AZUL, tem_tinta=False, fonte_ps='Z', corpo_espaco_texto=40.0),
     _run(4, 'HOX', PRETO)],  # numero-neutro: o inicio
    # a quebra sem tinta do fim nao abre linha e sai
    [_run(0, 'AB CD', PRETO), _run(5, '\r', AZUL, tem_tinta=False)],  # numero-neutro: o inicio
])
def test_texto_igual_ao_do_kv_sai_com_os_runs_do_kv(runs):
    # o texto igual ao do KV (cada caractere no mesmo papel) da os runs do KV, sem o kerning manual
    texto = ''.join(r['texto'] for r in runs).rstrip('\r')
    esperado = [dict(r, kerning=None) for r in runs if r['inicio'] < len(texto)]
    assert mq.runs_do_editado(runs, texto.split('\r')) == esperado


def test_regra_nao_olha_a_cor():
    # o mesmo KV com a cor do respiro trocada, ou sem a cor nos runs (o contrato do render guarda a cor fora deles):
    # os donos de cada caractere sao os mesmos
    def donos(kv, linhas):
        return [(r['inicio'], r['fim'], r['corpo_espaco_texto'], r['tem_tinta'])
                for r in mq.runs_do_editado(kv, linhas)]
    for linhas in (['TITULO', '', 'corpo do', 'texto'], ['TITULO', '', '', 'corpo do texto'], ['TITULO', 'corpo']):
        sem_cor = [{k: v for k, v in r.items() if k != 'cor_hex'} for r in _kv_com_respiro()]
        assert donos(_kv_com_respiro(PRETO), linhas) == donos(_kv_com_respiro(AZUL), linhas) == donos(sem_cor, linhas)


# o vao so de quebras: o KV com quatro quebras seguidas de corpos diferentes ('A' e 'B' com tinta)
def _kv_quatro_quebras():
    return [_run(0, 'A\r', PRETO), _run(2, '\r', PRETO, corpo_espaco_texto=1.0, tem_tinta=False),
            _run(3, '\r', PRETO, corpo_espaco_texto=2.0, tem_tinta=False),
            _run(4, '\r', PRETO, corpo_espaco_texto=3.0, tem_tinta=False),
            _run(5, 'B', PRETO, corpo_espaco_texto=20.0)]  # numero-neutro: os inicios


@pytest.mark.parametrize('n,esperado', [
    # a primeira com a primeira, a ultima com a ultima, as do meio com a do meio do KV (dos dois do meio, o segundo)
    (6, [10.0, 2.0, 2.0, 2.0, 2.0, 3.0]),
    (5, [10.0, 2.0, 2.0, 2.0, 3.0]),
    (3, [10.0, 2.0, 3.0]),
    (2, [10.0, 3.0]),
    # uma quebra so: a primeira
    (1, [10.0]),
    # o mesmo numero de quebras (o vao igual ao do KV): caractere a caractere
    (4, [10.0, 1.0, 2.0, 3.0]),
])
def test_vao_so_de_quebras_alinha_a_primeira_a_ultima_e_a_do_meio(n, esperado):
    linhas = ['A'] + [''] * (n - 1) + ['B x']  # 'x' inserida: a regra por palavra
    saida = mq.runs_do_editado(_kv_quatro_quebras(), linhas)
    por_caractere = [r['corpo_espaco_texto'] for r in saida for _ch in r['texto']]
    assert por_caractere[1:1 + n] == esperado
    assert por_caractere[0] == 10.0 and por_caractere[1 + n:] == [20.0] * 3


def _kv_quebras_no_comeco():
    # duas linhas vazias no comeco: a primeira quebra num run sem tinta de corpo 1, a segunda num de corpo 2, e 'A B' a 20
    return [_run(0, '\r', PRETO, corpo_espaco_texto=1.0, tem_tinta=False),
            _run(1, '\r', PRETO, corpo_espaco_texto=2.0, tem_tinta=False),
            _run(2, 'A B', PRETO, corpo_espaco_texto=20.0)]  # numero-neutro: os inicios


@pytest.mark.parametrize('linhas,esperado', [
    # rodada 5: o vao antes da primeira palavra pareada, igual ao do KV, fica caractere a caractere com os runs do KV
    (['', '', 'A C'], [1.0, 2.0]),
    (['', '', 'X B'], [1.0, 2.0]),
    # so de quebras com outra contagem: a primeira, a ultima e a do meio do KV
    (['', '', '', 'A C'], [1.0, 2.0, 2.0]),
    (['', 'A C'], [1.0]),
])
def test_vao_do_comeco_pareado_guarda_os_runs_do_kv(linhas, esperado):
    saida = mq.runs_do_editado(_kv_quebras_no_comeco(), linhas)
    por_caractere = [r['corpo_espaco_texto'] for r in saida for _ch in r['texto']]
    n = len(esperado)
    assert por_caractere[:n] == esperado and por_caractere[n:] == [20.0] * 3


@pytest.mark.parametrize('linhas', [['', 'A B novo'], ['', '', 'A B']])
def test_enter_no_comeco_do_kv_sem_vao_herda_a_primeira_palavra(linhas):
    # o KV sem linha vazia no comeco (o vao dele antes da primeira palavra e vazio): as quebras que o DA poe no comeco
    # herdam a palavra da direita, como antes
    kv = [_run(0, 'A\r', PRETO, corpo_espaco_texto=20.0), _run(2, 'B', AZUL, corpo_espaco_texto=5.0)]
    saida = mq.runs_do_editado(kv, linhas)
    assert saida[0]['texto'].startswith('\r') and saida[0]['corpo_espaco_texto'] == 20.0
    assert saida[0]['cor_hex'] == PRETO


def test_kv_de_um_trecho_da_o_trecho_de_antes():
    # antes da R3: um trecho so, com o estilo do primeiro trecho com tinta, kerning None e tem_tinta True
    r0 = _run(0, 'HAX O\rHOAXAV\r', PRETO)
    for linhas in (['HAX O', 'HOAXAV'], ['HAX O HOAXAV'], ['HAX', 'O', 'HOAXAV', 'novo'], ['outro texto'], ['AB', '', 'CD']):
        s = '\r'.join(linhas)
        antes = [dict(r0, inicio=0, fim=len(s), texto=s, kerning=None, tem_tinta=True)]
        assert mq.runs_do_editado([r0], linhas) == antes, linhas
    # o trecho sem tinta do fim (a quebra do fim) nao conta
    fim = _run(13, '\r', AZUL, tem_tinta=False)  # numero-neutro: o fim do texto
    assert mq.runs_do_editado([r0, fim], ['HAX O', 'HOAXAV']) == mq.runs_do_editado([r0], ['HAX O', 'HOAXAV'])


def test_camada_do_editado_com_duas_cores():
    camada = {'identidade': {'layer_id': 7}, 'tipo': 'texto',
              'texto': {'conteudo': 'L1 a\rL2 b\rL3 c', 'matriz': [1.0, 0.0, 0.0, 1.0, 0.0, 0.0], 'tipo_caixa': 'ponto',
                        'runs': _kv(),
                        'paragrafos': [{'inicio': 0, 'fim': 5, 'justificacao': 'CENTER'},  # numero-neutro: paragrafos
                                       {'inicio': 5, 'fim': 10, 'justificacao': 'CENTER'},  # numero-neutro: paragrafos
                                       {'inicio': 10, 'fim': 15, 'justificacao': 'CENTER'}]}}  # numero-neutro: idem
    c = mq.camada_do_editado(camada, ['L1 a', 'L2 b L3 c'])
    t = c['texto']
    assert t['conteudo'] == 'L1 a\rL2 b L3 c'
    assert [(r['inicio'], r['fim'], r['texto'], r['cor_hex']) for r in t['runs']] == \
        [(0, 10, 'L1 a\rL2 b ', PRETO), (10, 14, 'L3 c', AZUL)]  # numero-neutro: as posicoes no texto novo
    assert all(r['kerning'] is None and r['tem_tinta'] for r in t['runs'])
    assert t['paragrafos'] == [{'inicio': 0, 'fim': 15, 'justificacao': 'CENTER'}]  # numero-neutro: o texto + 1
    # a camada do laudo nao muda
    assert camada['texto']['runs'] == _kv()


# ------------------------------------------------------------------ o vao entre palavras pareadas (o CR da linha 2)
def _kv_cr_de_outra_linha():
    # o CR que termina a linha 2 (azul, corpo menor) e do run da linha 3 (preto): ele leva a entrelinha da linha 2
    return [_run(0, 'L1 a\r', PRETO), _run(5, 'L2 b', AZUL, corpo_espaco_texto=5.0),  # numero-neutro: o inicio
            _run(9, '\rL3 c', PRETO)]  # numero-neutro: o inicio do trecho


@pytest.mark.parametrize('linhas,esperado', [
    # trocar uma palavra de outra linha (bloco replace de mesmo tamanho, ou equal em volta): o CR da linha 2 nao muda
    (['L1 a', 'L2 b', 'L3 d'], [('L1 a\r', PRETO), ('L2 b', AZUL), ('\rL3 d', PRETO)]),
    (['L1 x', 'L2 b', 'L3 c'], [('L1 x\r', PRETO), ('L2 b', AZUL), ('\rL3 c', PRETO)]),
    (['L1 a', 'L2 b', 'x c'], [('L1 a\r', PRETO), ('L2 b', AZUL), ('\rx c', PRETO)]),
    (['L1 a', 'L2 y', 'L3 c'], [('L1 a\r', PRETO), ('L2 y', AZUL), ('\rL3 c', PRETO)]),
])
def test_vao_igual_ao_do_kv_guarda_o_run_do_kv(linhas, esperado):
    assert _trechos(linhas, _kv_cr_de_outra_linha()) == esperado
    saida = mq.runs_do_editado(_kv_cr_de_outra_linha(), linhas)
    # o CR que termina a linha 2 fica no run preto de corpo 10, como no KV (antes herdava o azul de corpo 5 da esquerda)
    pos = len(linhas[0]) + 1 + len(linhas[1])
    [dono] = [r for r in saida if r['inicio'] <= pos < r['fim']]
    assert (dono['cor_hex'], dono['corpo_espaco_texto']) == (PRETO, 10.0)


def test_insercao_junto_ao_cr_fica_com_a_esquerda():
    # fora da regra do vao, por desenho: a palavra inserida no fim da linha 2 quebra o par, e o vao dela ate a linha 3
    # herda a esquerda (o azul, corpo 5)
    assert _trechos(['L1 a', 'L2 b x', 'L3 c'], _kv_cr_de_outra_linha()) == \
        [('L1 a\r', PRETO), ('L2 b x\r', AZUL), ('L3 c', PRETO)]


def test_vao_diferente_do_kv_herda_a_esquerda():
    # o vao que o DA mudou (dois espacos no lugar de um) nao e o do KV: herda a esquerda
    runs = [_run(0, 'AB ', PRETO), _run(3, 'CD', AZUL)]  # numero-neutro: o inicio do trecho azul
    assert _trechos(['AB CD'], runs) == [('AB ', PRETO), ('CD', AZUL)]
    assert _trechos(['AB  CD'], runs) == [('AB  ', PRETO), ('CD', AZUL)]
    runs = [_run(0, 'AB', PRETO), _run(2, ' CD', AZUL)]  # numero-neutro: o inicio do trecho azul
    assert _trechos(['AB CD'], runs) == [('AB', PRETO), (' CD', AZUL)]
    assert _trechos(['AB  CD'], runs) == [('AB  ', PRETO), ('CD', AZUL)]
    # com outra edicao no texto (a regra por palavra), o vao igual ao do KV entre as palavras pareadas fica com o run
    # dele (o azul), e nao com a esquerda
    assert _trechos(['AB CD x'], runs) == [('AB', PRETO), (' CD x', AZUL)]
    assert _trechos(['AB', 'CD x'], runs) == [('AB', PRETO), ('\rCD x', AZUL)]


# ------------------------------------------------------------------ o respiro: o CR sem tinta no KV de varios estilos
def _kv_com_respiro(cor_respiro=PRETO, fonte_respiro='X'):
    # o titulo a 40 pt, a linha vazia de 10 pt (o CR sem tinta) e o corpo a 20 pt
    respiro = _run(7, '\r', cor_respiro, corpo_espaco_texto=10.0, tem_tinta=False,  # numero-neutro: o inicio
                   tem_caractere_visivel=False, fonte_ps=fonte_respiro)
    return [_run(0, 'TITULO\r', PRETO, corpo_espaco_texto=40.0), respiro,
            _run(8, 'corpo do texto', PRETO, corpo_espaco_texto=20.0)]  # numero-neutro: o inicio do trecho


@pytest.mark.parametrize('cor_respiro,fonte_respiro', [(PRETO, 'X'), (AZUL, 'Z')])
@pytest.mark.parametrize('linhas', [['TITULO', '', 'corpo do', 'texto'], ['TITULO', '', 'corpo do texto'],
                                    ['TITULO', '', 'corpo novo']])
def test_quebra_que_continua_quebra_guarda_o_run_sem_tinta(linhas, cor_respiro, fonte_respiro):
    kv = _kv_com_respiro(cor_respiro, fonte_respiro)
    saida = mq.runs_do_editado(kv, linhas)
    # a quebra da linha vazia fica no run sem tinta dela, com o corpo, a cor e a fonte dele
    [respiro] = [r for r in saida if r['inicio'] <= len('TITULO\r') < r['fim']]
    assert respiro['texto'] == '\r' and respiro['tem_tinta'] is False
    assert (respiro['corpo_espaco_texto'], respiro['cor_hex'], respiro['fonte_ps']) == \
        (10.0, cor_respiro, fonte_respiro)
    assert [r['corpo_espaco_texto'] for r in saida] == [40.0, 10.0, 20.0]


@pytest.mark.parametrize('linhas', [['TITULO', '', 'novo corpo do texto'], ['TITULO', '', 'cor po do texto']])
def test_insercao_junto_ao_respiro_fica_de_fora(linhas):
    # fora da regra do vao, por desenho (como a insercao junto ao CR): a palavra inserida, ou trocada por duas, logo
    # depois do respiro desfaz o par, e o respiro herda a palavra da direita (o corpo de 20 pt)
    saida = mq.runs_do_editado(_kv_com_respiro(), linhas)
    assert [(r['texto'][:2], r['corpo_espaco_texto']) for r in saida] == [('TI', 40.0), ('\r' + linhas[2][0], 20.0)]
    assert all(r['tem_tinta'] for r in saida)


def test_quebra_sem_tinta_que_vira_espaco_herda_o_vizinho():
    # a quebra sem tinta que o DA trocou por espaco (so a quebra mudou) nunca leva o run sem tinta para a linha, nem
    # no KV de varios estilos
    saida = mq.runs_do_editado(_kv_com_respiro(AZUL, 'Z'), ['TITULO', ' corpo do texto'])
    assert all(r['tem_tinta'] for r in saida)
    assert {r['fonte_ps'] for r in saida} == {'X'} and {r['cor_hex'] for r in saida} == {PRETO}
