# -*- coding: utf-8 -*-
"""O tamanho como segunda chave do agrupamento da tela (decisao 208, revisao da 163 em 24/11; melhoria t3).

Dentro de cada grupo de proporcao (vapt.tela.estado.agrupar_por_proporcao), a composicao que copiaria o layout da
maior com escala abaixo de derivacao.grupo_escala_min vai para um grupo proprio, e os que sobram passam pela mesma
regra de novo (agrupar_por_tamanho). Criterios cobertos aqui:
  - o limite novo tem fonte na revisao da 163;
  - os quatro pares do Duda: 1920x1080 e 1280x720 juntos (0,67); 1280x720 e 640x360 juntos (0,5, o >= segura);
    1280x720 e 300x150 separam; 1080x1920 e 300x600 separam;
  - a recursao: 1920x1080, 1280x720, 640x360 e 300x150 viram tres grupos;
  - o grupo separado leva o motivo (separado_por_tamanho) e o id do grupo de onde saiu (separado_de), e e uma familia
    normal, com arquivo de edicao proprio;
  - o id da familia fica com a parte com mais formatos em comum, e a confirmacao da parte menor cai;
  - o que o DA juntou de volta (juntados) nao e separado de novo pela regra, nem quando a familia se monta de novo;
  - no job sintetico da diagonal: a tela separa o 640x360 girado e o 300x600 do 1080x1920, o ato "Juntar de volta" os
    devolve, o rascunho guarda juntados, e a familia montada de novo tem os quatro arquivos;
  - no Chromium sem janela: o cabecalho da familia separada diz a frase com o percentual inteiro, sem travessao, e
    tem o botao "Juntar de volta".
Tudo sintetico: derivacoes em memoria inventadas aqui (como test_tela_familia_estavel) e o KV da diagonal de
testes/sinteticos, numa pasta temporaria; nenhum job real."""
import json

import pytest

import test_familia_diagonal as tfd
import test_tela_escrita as tte
import test_tela_familia_estavel as tfe
import test_tela_servidor as tts
from vapt import contratos, limites, plataforma
from vapt.tela import atos as ta
from vapt.tela import estado as te
from vapt.tela import rascunho as tr
from vapt.tela import servidor as ts
from sinteticos import kv_diagonal as KD

PLAT = plataforma.obter()
TRAVESSOES = tfe.TRAVESSOES


def _comps(*medidas):
    return [{'id': 'c%dx%d' % (w, h), 'largura': w, 'altura': h, 'formatos': [{'id': 'f%dx%d' % (w, h)}]}
            for w, h in medidas]


def _medidas(partes):
    return [sorted((c['largura'], c['altura']) for c in p['composicoes']) for p in partes]


# ------------------------------------------------------------------ a regra, em Python puro
def test_limite_do_tamanho_tem_fonte_na_revisao_da_163():
    lim = limites.obter('derivacao.grupo_escala_min')
    assert lim.valor == 0.5 and lim.situacao == 'a_calibrar' and lim.efeito == 'registra'
    assert lim.fonte['arquivo'] == 'decisoes-v1.md' and '163' in lim.fonte['secao'] and '24/11' in lim.fonte['secao']


@pytest.mark.parametrize('maior, menor, juntos', [
    ((1920, 1080), (1280, 720), True),   # 0,67
    ((1280, 720), (640, 360), True),     # 0,5: o >= segura
    ((1280, 720), (300, 150), False),    # 0,21
    ((1080, 1920), (300, 600), False),   # 0,28
])
def test_os_quatro_pares_do_duda(maior, menor, juntos):
    partes = te.agrupar_por_tamanho(_comps(menor, maior))
    if juntos:
        assert _medidas(partes) == [sorted([menor, maior])]
        assert partes[0]['separado_por_tamanho'] is None and partes[0]['de'] is None
    else:
        assert _medidas(partes) == [[maior], [menor]]
        motivo = partes[1]['separado_por_tamanho']
        escala = round(te.escala_entre(_comps(menor)[0], _comps(maior)[0]), 4)
        assert motivo == {'de': '%dx%d' % maior, 'escala': escala, 'escala_menor': escala}
        assert motivo['escala'] < limites.valor('derivacao.grupo_escala_min')
        assert partes[1]['de'] == 0 and partes[0]['referencia'] == 'c%dx%d' % maior
    # a ordem da entrada nao muda o resultado
    assert _medidas(te.agrupar_por_tamanho(_comps(maior, menor))) == _medidas(partes)


def test_recursao_com_a_referencia_no_maior_dos_que_sobraram():
    # 640/1920 = 0,33 sai do primeiro grupo; 150/360 = 0,42 (o lado que aperta; 300/640 daria 0,47) sai do segundo
    partes = te.agrupar_por_tamanho(_comps((1920, 1080), (1280, 720), (640, 360), (300, 150)))
    assert _medidas(partes) == [[(1280, 720), (1920, 1080)], [(640, 360)], [(300, 150)]]
    assert partes[1]['separado_por_tamanho'] == {'de': '1920x1080', 'escala': 0.3333, 'escala_menor': 0.3333}
    assert partes[1]['de'] == 0
    assert partes[2]['separado_por_tamanho'] == {'de': '640x360', 'escala': 0.4167, 'escala_menor': 0.4167}
    assert partes[2]['de'] == 1


def test_a_escala_e_a_do_lado_que_aperta():
    # 1280x720 e 300x150: 300/1280 = 0,234 e 150/720 = 0,208; vale o menor
    assert te.escala_entre(_comps((300, 150))[0], _comps((1280, 720))[0]) == pytest.approx(150.0 / 720.0)


def test_a_parte_com_mais_de_um_membro_leva_a_escala_do_menor():
    # 1080x1920 de referencia; 360x640 (0,33) e 300x600 (0,28) saem juntos: a escala e a do maior deles (o arquivo de
    # edicao da parte), e escala_menor a do 300x600, para a frase dizer a faixa
    partes = te.agrupar_por_tamanho(_comps((1080, 1920), (360, 640), (300, 600)))
    assert _medidas(partes) == [[(1080, 1920)], [(300, 600), (360, 640)]]
    assert partes[1]['separado_por_tamanho'] == {'de': '1080x1920', 'escala': 0.3333, 'escala_menor': 0.2778}
    assert ta.quanto_do_tamanho(partes[1]['separado_por_tamanho']) == 'entre 28% e 33% do tamanho'
    assert ta.quanto_do_tamanho({'de': '1080x1920', 'escala': 0.3333, 'escala_menor': 0.3333}) == 'com 33% do tamanho'
    assert ta.quanto_do_tamanho({'de': '1080x1920', 'escala': 0.3333}) == 'com 33% do tamanho'


def test_a_presa_fica_com_o_irmao_e_e_referencia_quando_e_a_maior():
    g, m, p, pp = _comps((1920, 1080), (1280, 720), (640, 360), (300, 170))
    # pp juntado pelo DA a familia de p: fica com p (irmao), medido ou nao
    partes = te.agrupar_por_tamanho([g, m, p, pp], presas={'c300x170': {'f640x360'}})
    assert _medidas(partes) == [[(1280, 720), (1920, 1080)], [(300, 170), (640, 360)]]
    assert partes[1]['separado_por_tamanho'] == {'de': '1920x1080', 'escala': 0.3333, 'escala_menor': 0.1562}
    # p juntado a familia de g: fica com g, e pp e medido contra g
    partes = te.agrupar_por_tamanho([g, m, p, pp], presas={'c640x360': {'f1920x1080', 'f1280x720'}})
    assert _medidas(partes) == [[(640, 360), (1280, 720), (1920, 1080)], [(300, 170)]]
    assert partes[1]['separado_por_tamanho'] == {'de': '1920x1080', 'escala': 0.1562, 'escala_menor': 0.1562}
    # a isencao e do par: sem g e m no job, p e a maior e a referencia, e pp (0,47) sai dele
    partes = te.agrupar_por_tamanho([p, pp], presas={'c640x360': {'f1920x1080', 'f1280x720'}})
    assert _medidas(partes) == [[(640, 360)], [(300, 170)]]
    assert partes[1]['separado_por_tamanho'] == {'de': '640x360', 'escala': 0.4688, 'escala_menor': 0.4688}
    # a presa cujo irmao e outra presa puxada no mesmo passo vai junto
    partes = te.agrupar_por_tamanho([g, m, p, pp], presas={'c640x360': {'f1920x1080'}, 'c300x170': {'f640x360'}})
    assert _medidas(partes) == [[(300, 170), (640, 360), (1280, 720), (1920, 1080)]]


# ------------------------------------------------------------------ nas abas
# horizontais de proporcao 1,78 a 1,76 (um grupo de proporcao so): o 300x170 copia o 640x360 a 0,47 e o 1920x1080 a 0,16
G, M, P, PP = ('g', 1920, 1080), ('m', 1280, 720), ('p', 640, 360), ('pp', 300, 170)
V, VP = ('v', 1080, 1920), ('vp', 300, 600)


def _grupos(orientacoes):
    return {g['id']: g for o in orientacoes for g in o['grupos']}


def test_abas_separam_por_tamanho_com_o_motivo_e_familia_propria():
    abas = tfe._abas([G, M, P, PP])
    grupos = _grupos(abas)
    assert tfe._ids(abas) == {'horizontal-1': ['g', 'm'], 'horizontal-2': ['p'], 'horizontal-3': ['pp']}
    assert 'separado_por_tamanho' not in grupos['horizontal-1'] and 'separado_de' not in grupos['horizontal-1']
    # o motivo leva o arquivo de referencia (o da regra do arquivo de edicao na composicao), que a tela nomeia
    assert grupos['horizontal-2']['separado_por_tamanho'] == {'de': '1920x1080', 'arquivo': 'g', 'escala': 0.3333,
                                                              'escala_menor': 0.3333}
    assert grupos['horizontal-2']['separado_de'] == 'horizontal-1'
    assert grupos['horizontal-3']['separado_por_tamanho'] == {'de': '640x360', 'arquivo': 'p', 'escala': 0.4688,
                                                              'escala_menor': 0.4688}
    assert grupos['horizontal-3']['separado_de'] == 'horizontal-2'
    # cada grupo e uma familia normal: o arquivo de edicao e o maior dele, sem separados do DA e sem aviso
    assert [grupos[g]['arquivo_de_edicao'] for g in ('horizontal-1', 'horizontal-2', 'horizontal-3')] == ['g', 'p', 'pp']
    assert all(grupos[g]['separados'] == [] and grupos[g]['aviso'] == '' for g in grupos)
    # o vertical do Duda: 1080x1920 e 300x600 separam
    abas = tfe._abas([V, VP])
    grupos = _grupos(abas)
    assert tfe._ids(abas) == {'vertical-1': ['v'], 'vertical-2': ['vp']}
    assert grupos['vertical-2']['separado_por_tamanho'] == {'de': '1080x1920', 'arquivo': 'v', 'escala': 0.2778,
                                                            'escala_menor': 0.2778}
    assert grupos['vertical-2']['separado_de'] == 'vertical-1'
    json.dumps(abas)
    assert not any(k.startswith('_') for g in grupos.values() for k in g)


def test_id_fica_com_a_parte_maior_e_a_confirmacao_da_menor_cai(tmp_path):
    # o job de antes desta regra conhecia a familia com os quatro formatos, confirmada
    conhecidas = {'horizontal-1': ['g', 'm', 'p', 'pp']}
    abas = tfe._abas([G, M, P, PP], conhecidas=conhecidas)
    assert tfe._ids(abas) == {'horizontal-1': ['g', 'm'], 'horizontal-2': ['p'], 'horizontal-3': ['pp']}
    av = tfe._avisos(abas)
    assert 'saíram os formatos 640x360 e 300x170' in av['horizontal-1'] and 'confirme' in av['horizontal-1']
    assert 'outra família' in av['horizontal-2'] and 'outra família' in av['horizontal-3']
    assert not any(t in texto for texto in av.values() for t in TRAVESSOES)
    # a confirmacao feita com os quatro nao vale para nenhuma das partes
    conf = {'origem': 'da', 'meio': 'tela', 'em': 'x', 'formatos': ['g', 'm', 'p', 'pp'], 'arquivo_de_edicao': 'g'}
    f = {'versao': None, 'confirmada': True, 'edicoes': [], 'confirmacao': conf, 'formatos': ['g', 'm', 'p', 'pp']}
    assert tr.confirmada_para(f, ['g', 'm']) is False and tr.confirmada_para(f, ['p']) is False


def test_juntado_pelo_da_nao_e_separado_de_novo():
    # o DA juntou pp de volta a familia de p (horizontal-2): pp fica com p, e a regra nao o tira de la
    conhecidas = {'horizontal-1': ['g', 'm'], 'horizontal-2': ['p', 'pp']}
    abas = tfe._abas([G, M, P, PP], conhecidas=conhecidas, juntados={'horizontal-2': ['pp']})
    grupos = _grupos(abas)
    assert tfe._ids(abas) == {'horizontal-1': ['g', 'm'], 'horizontal-2': ['p', 'pp']}
    # a faixa da frase vai ate o pp (0,16 contra o 1920x1080), que o DA levou para la
    assert grupos['horizontal-2']['separado_por_tamanho'] == {'de': '1920x1080', 'arquivo': 'g', 'escala': 0.3333,
                                                              'escala_menor': 0.1562}
    assert grupos['horizontal-2']['separado_de'] == 'horizontal-1' and grupos['horizontal-2']['aviso'] == ''
    # o DA juntou p (e pp) de volta a familia maior: tudo num grupo so, sem motivo
    conhecidas = {'horizontal-1': ['g', 'm', 'p', 'pp']}
    abas = tfe._abas([G, M, P, PP], conhecidas=conhecidas, juntados={'horizontal-1': ['p', 'pp']})
    grupos = _grupos(abas)
    assert tfe._ids(abas) == {'horizontal-1': ['g', 'm', 'p', 'pp']}
    assert 'separado_por_tamanho' not in grupos['horizontal-1'] and 'separado_de' not in grupos['horizontal-1']
    # so p juntado a familia maior: pp e medido contra o 1920x1080, e nao contra o 640x360 que o DA levou
    conhecidas = {'horizontal-1': ['g', 'm', 'p'], 'horizontal-3': ['pp']}
    abas = tfe._abas([G, M, P, PP], conhecidas=conhecidas, juntados={'horizontal-1': ['p']})
    grupos = _grupos(abas)
    assert tfe._ids(abas) == {'horizontal-1': ['g', 'm', 'p'], 'horizontal-3': ['pp']}
    assert grupos['horizontal-3']['separado_por_tamanho'] == {'de': '1920x1080', 'arquivo': 'g', 'escala': 0.1562,
                                                              'escala_menor': 0.1562}
    assert grupos['horizontal-3']['separado_de'] == 'horizontal-1'


def test_juntado_vira_referencia_quando_o_maior_sai_do_job():
    # a isencao e do par, nao do formato: p foi juntado a familia de g e m; com os dois fora do job, p e a maior e o
    # pp (0,47 contra o 640x360) e medido contra ele e vai para grupo proprio, com o motivo
    conhecidas = {'horizontal-1': ['g', 'm', 'p']}
    abas = tfe._abas([P, PP], conhecidas=conhecidas, juntados={'horizontal-1': ['p']})
    grupos = _grupos(abas)
    assert tfe._ids(abas) == {'horizontal-1': ['p'], 'horizontal-2': ['pp']}
    assert grupos['horizontal-2']['separado_por_tamanho'] == {'de': '640x360', 'arquivo': 'p', 'escala': 0.4688,
                                                              'escala_menor': 0.4688}
    assert grupos['horizontal-2']['separado_de'] == 'horizontal-1'
    # a presa sem irmao nenhum no job segue a regra: pp foi juntado a p, que saiu; contra o g, pp sai
    conhecidas = {'horizontal-2': ['p', 'pp']}
    abas = tfe._abas([G, PP], conhecidas=conhecidas, juntados={'horizontal-2': ['pp']})
    grupos = _grupos(abas)
    assert tfe._ids(abas) == {'horizontal-1': ['g'], 'horizontal-2': ['pp']}
    assert grupos['horizontal-2']['separado_por_tamanho']['de'] == '1920x1080'
    assert grupos['horizontal-2']['separado_de'] == 'horizontal-1'


def test_rascunho_guarda_os_juntados_so_pelo_servidor(tmp_path):
    mover = {'elemento': 'el1', 'acao': 'mover', 'dx': 0.1, 'dy': 0.0}
    gravadas = {'v': {'versao': None, 'confirmada': False, 'edicoes': [], 'juntados': ['c']}}
    pagina = {'v': {'versao': None, 'confirmada': False, 'edicoes': [mover], 'juntados': []}}
    # o que a pagina manda sai em _familias_com_a_confirmacao; _com_a_estrutura devolve o gravado
    limpa = {g: {k: v for k, v in f.items() if k not in tr.CAMPOS_DO_SERVIDOR} for g, f in pagina.items()}
    assert 'juntados' not in limpa['v']
    saida = tr._com_a_estrutura(limpa, gravadas, {'v': ['a', 'b', 'c']}, {'v': 'a'})
    assert saida['v']['juntados'] == ['c']
    # e o esquema aceita o campo
    dados = {'esquema': tr.ESQUEMA, 'job_id': 'a' * 32, 'laudo_sha256': '1' * 64, 'origem': 'rascunho',
             'atualizado_em': '2026-11-24T10:00:00-03:00', 'familias': saida}
    contratos.validar(dados, tr.ESQUEMA)
    assert tr.estrutura(tmp_path) == ({}, {}, {})


# ------------------------------------------------------------------ o job sintetico da diagonal
@pytest.fixture(scope='module')
def diag(tmp_path_factory):
    """O job da diagonal como a tela o monta pela primeira vez, sem o DA juntar nada (test_familia_diagonal junta)."""
    if PLAT.nome in ('sem-suporte', 'mac'):
        pytest.skip('sem isolador neste sistema')
    j = KD.criar_job(tmp_path_factory.mktemp('grupo-por-tamanho'), tfd.FORMATOS)
    j['conteudo'] = te.montar(j['job'])
    return j


# ------------------------------------------------------------------ no Chromium sem janela (antes do juntar: o ato
# muda o job da fixture)
def test_cabecalho_da_familia_separada_diz_o_motivo_e_tem_o_botao(diag):
    from playwright.sync_api import sync_playwright

    import test_tela_familia_0100 as tf
    from vapt.chromium import navegador
    job, conteudo = diag['job'], diag['conteudo']
    menor = tfd._familia_de(conteudo, 'f300x600')
    navegador.apontar_playwright()
    with ts.ServidorTela(conteudo, pasta=job, modo_teste=True,
                         atos=ta.atos_do_job(job, conteudo=conteudo)) as srv, sync_playwright() as pw:
        nav, pg = tf._pagina(pw, srv)
        try:
            tf._abrir_familia(pg, conteudo['estado'], menor)
            vista = pg.evaluate('''() => ({
                nota: (document.querySelector("#cabecalho-familia .cabecalho-nota") || {}).textContent || "",
                botao: !!document.querySelector('#cabecalho-familia [data-ato="familia_juntar"]'),
                cabecalho: document.querySelector("#cabecalho-familia .cabecalho-texto").textContent})''')
            # o arquivo de referencia pelo nome que o DA ve e a faixa do 300x600 (28%) ao 640x360 girado (33%)
            assert vista['nota'] == ('O Vapt separou este grupo do 1080x1920: copiado, o conteúdo ficaria entre 28% e '
                                     '33% do tamanho.'), vista
            assert vista['botao'] and not any(t in vista['nota'] for t in TRAVESSOES)
            assert vista['cabecalho'].startswith('Você edita o 640x360')
        finally:
            nav.close()


# ------------------------------------------------------------------ o ato "Juntar de volta" no job da diagonal
def test_a_tela_separa_os_pequenos_e_o_juntar_de_volta_os_devolve(diag):
    job, conteudo = diag['job'], diag['conteudo']
    gid = tfd._familia_de(conteudo, tfd.REF)
    # o 1920x1080 girado 270 e um 1080x1920 (escala 1,0) e fica; o 640x360 girado 90 (360x640, 0,33) e o 300x600 (0,28)
    # saem juntos, com a referencia no 360x640 (o 300x600 fica com ele: 0,83)
    assert sorted(conteudo['familias'][gid]['formatos']) == ['f1080x1920', 'g1920x1080r270']
    menor = tfd._familia_de(conteudo, 'f300x600')
    fam = conteudo['familias'][menor]
    assert sorted(fam['formatos']) == ['f300x600', 'g640x360r90'] and fam['arquivo_de_edicao'] == 'g640x360r90'
    # o arquivo de referencia e o sem giro (1080x1920 e 1920x1080 girado empatam na area em pe); a faixa vai do 300x600
    assert fam['separado_de'] == gid
    assert fam['separado_por_tamanho'] == {'de': '1080x1920', 'arquivo': tfd.REF, 'escala': 0.3333, 'escala_menor': 0.2778}
    assert conteudo['familias'][gid]['separado_por_tamanho'] is None
    grupo = next(g for o in conteudo['estado']['orientacoes'] for g in o['grupos'] if g['id'] == menor)
    assert grupo['separado_por_tamanho'] == fam['separado_por_tamanho'] and grupo['separado_de'] == gid
    # a familia separada tem a previa propria, editada no arquivo de edicao dela
    r = conteudo['editar']({'familia': menor, 'versao': None, 'edicoes': []}, 'fixture_de_teste')
    assert r['arquivo_de_edicao'] == 'g640x360r90'
    assert sorted(m['formato'] for m in r['membros']) == ['f300x600', 'g640x360r90']
    s = ts.ServidorTela(conteudo, pasta=job, modo_teste=True, atos=ta.atos_do_job(job, conteudo=conteudo)).iniciar()
    try:
        biscoito = tts._entrar(s)
        codigo, p = tte._pedir_ato(s, biscoito, nome='familia_juntar', dados={'familia': menor})
        assert codigo == 200, p
        # a janela diz os arquivos pela medida, a familia pela do arquivo de edicao dela e o percentual inteiro
        assert 'voltam para a família do 1080x1920' in p['texto'], p['texto']
        assert 'fica entre 28% e 33% do tamanho' in p['texto'], p['texto']
        assert '300x600' in p['texto'] and '640x360 girado 90 graus' in p['texto'], p['texto']
        assert 'g640x360r90' not in p['texto'] and not any(t in p['texto'] for t in TRAVESSOES)
        tfd._ato(s, biscoito, 'familia_juntar', {'familia': menor})
        f = json.loads((job / tr.ARQUIVO).read_text(encoding='utf-8'))['familias'][gid]
        assert f['juntados'] == ['f300x600', 'g640x360r90'] and f['confirmada'] is False
        assert sorted(f['formatos']) == sorted(tfd.VERTICAIS)
        # a tela monta as familias de novo: os quatro juntos, sem motivo, e o pedido do estado traz isso
        estado = json.loads(tts._pedir(s, '/api/estado', cookie=biscoito)[2])
        grupos = {x['id']: x for o in estado['orientacoes'] for x in o['grupos']}
        g = grupos[gid]
        assert sorted(x['id'] for c in g['composicoes'] for x in c['formatos']) == sorted(tfd.VERTICAIS)
        assert 'separado_por_tamanho' not in g and 'separado_de' not in g and g['aviso'] == ''
        assert menor not in grupos
    finally:
        s.parar()
    # montada de novo do zero, a regra respeita o que o DA juntou
    novo = te.montar(job)
    assert sorted(novo['familias'][gid]['formatos']) == sorted(tfd.VERTICAIS)
    assert novo['familias'][gid]['separado_por_tamanho'] is None
    assert tr.estrutura(job)[2] == {gid: ['f300x600', 'g640x360r90']}


# ------------------------------------------------------------------ o arquivo que o DA separou da familia que a regra
# separou, quando ela volta (correcao da revisao do t3)
def _ato_e_montar(job, conteudo, nome, dados):
    """Pede e confirma o ato pelo servidor da tela e monta a tela de novo, como a pagina faz depois de um ato."""
    s = ts.ServidorTela(conteudo, pasta=job, modo_teste=True, atos=ta.atos_do_job(job, conteudo=conteudo)).iniciar()
    try:
        biscoito = tts._entrar(s)
        tfd._ato(s, biscoito, nome, dados)
    finally:
        s.parar()
    return te.montar(job)


def test_juntar_de_volta_leva_o_separado_pelo_da_para_a_familia_que_recebe(tmp_path):
    if PLAT.nome in ('sem-suporte', 'mac'):
        pytest.skip('sem isolador neste sistema')
    job = KD.criar_job(tmp_path, tfd.FORMATOS)['job']
    conteudo = te.montar(job)
    menor = tfd._familia_de(conteudo, 'f300x600')
    assert sorted(conteudo['familias'][menor]['formatos']) == ['f300x600', 'g640x360r90']
    # (1) o DA separa o 300x600 da familia que a regra do tamanho separou
    conteudo = _ato_e_montar(job, conteudo, 'familia_separar', {'familia': menor, 'arquivo': 'f300x600'})
    assert conteudo['familias'][menor]['formatos'] == ['g640x360r90']
    assert conteudo['familias'][menor]['separados'] == ['f300x600']
    assert conteudo['familias'][tfd._familia_de(conteudo, 'f300x600')]['separado_de'] == menor
    # (2) o DA junta a familia separada por tamanho de volta: a dela some da tela, e o arquivo que ele separou dela
    # passa a ser separado da familia que a recebeu, para o grupo dele continuar dizendo de onde saiu
    conteudo = _ato_e_montar(job, conteudo, 'familia_juntar', {'familia': menor})
    gid = tfd._familia_de(conteudo, tfd.REF)
    assert menor not in conteudo['familias']
    assert sorted(conteudo['familias'][gid]['formatos']) == ['f1080x1920', 'g1920x1080r270', 'g640x360r90']
    assert tr.estrutura(job)[1:] == ({gid: ['f300x600']}, {gid: ['g640x360r90']})
    sozinho = tfd._familia_de(conteudo, 'f300x600')
    fam = conteudo['familias'][sozinho]
    assert fam['separado_de'] == gid and not fam.get('separado_por_tamanho')
    # e o "Juntar de volta" dele vale: a janela abre com a frase do arquivo separado, e o ato o devolve
    s = ts.ServidorTela(conteudo, pasta=job, modo_teste=True, atos=ta.atos_do_job(job, conteudo=conteudo)).iniciar()
    try:
        biscoito = tts._entrar(s)
        codigo, p = tte._pedir_ato(s, biscoito, nome='familia_juntar', dados={'familia': sozinho})
        assert codigo == 200, p
        assert p['texto'].startswith('O 300x600 volta para a família de onde saiu'), p['texto']
        tfd._ato(s, biscoito, 'familia_juntar', {'familia': sozinho})
    finally:
        s.parar()
    f = json.loads((job / tr.ARQUIVO).read_text(encoding='utf-8'))['familias'][gid]
    assert 'separados' not in f and sorted(f['formatos']) == sorted(tfd.VERTICAIS)
    # o 300x600 volta pelo juntar de um arquivo separado, que nao o poe em juntados: a regra do tamanho o mede de novo
    # contra o 1080x1920 e o grupo dele diz o motivo, com o mesmo "Juntar de volta"
    novo = te.montar(job)
    fam = novo['familias'][tfd._familia_de(novo, 'f300x600')]
    assert fam['separado_de'] == gid and fam['separado_por_tamanho']['de'] == '1080x1920'
