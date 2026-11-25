# -*- coding: utf-8 -*-
"""Decisao 209: a tabela "Formatos do job" do passo 1, um lugar so para as decisoes por formato (a spec da decisao 198,
item 3; o tipo de arquivo da decisao 205; o giro da revisao do M7a), sem mudar o que cada coluna grava.

Criterios cobertos aqui:
  - o motor monta specs['linhas'], uma por formato, com o estado de cada uma (o que falta: medida, spec, tipo, giro),
    nos casos: tudo confirmado; sem tipo; sem giro; valor divergente; formato com duas medidas; folha que diz o tipo e
    o giro; formato escrito na tela;
  - a lista do que falta ganha o item do tipo de arquivo, que leva ao passo 1;
  - na pagina, a 1280 x 800, a tabela cabe sem rolagem lateral, tem uma linha por formato, e o fluxo comum de um CSV
    so com medidas (marcar todos, confirmar os marcados, todos em JPEG, sem giro nos que faltam) deixa todas as linhas
    em "Pronto" e o que falta sem item de spec, tipo ou giro.
Tudo sintetico: linhas montadas a mao e um CSV de uma coluna."""
import sys

import pytest

import test_fontes_apoio as fap
import test_tela_escrita as tte
import test_tela_lido as tl
import test_tela_palco as tp
import test_tipo_de_arquivo as tta
from conftest import escolher_modo_do_da
from vapt.tela import atos as ta
from vapt.tela import estado as te
from vapt.tela import servidor as ts

ambiente_limpo = tte.ambiente_limpo
CHAVE = 'portal|geral|1080x1920'
CHAVE_2 = 'portal|sao-paulo|300x600'
ROT0 = {'graus': 0, 'sentido': None}


def _formato(chave, fid, rotacao=None, giro_da_folha=None, digitado=False, largura=1080, altura=1920):
    return {'id': fid, 'chave': chave, 'sem_folha': False, 'digitado': digitado, 'tem_spec': False,
            'largura': largura, 'altura': altura, 'rotacao': rotacao, 'giro_da_folha': giro_da_folha}


def _valor(vid, grupo, grupo_nome, campo='peso máximo', em_lote=True, leituras=()):
    return {'valor_id': vid, 'onde': grupo_nome, 'na_frase': 'formato %s' % grupo_nome, 'campo': campo,
            'descricao': '250 KB' if not leituras else 'as folhas trazem valores diferentes', 'trecho': '',
            'leituras': [{'indice': i, 'descricao': d, 'trecho': d} for i, d in enumerate(leituras)],
            'grupo': grupo, 'grupo_nome': grupo_nome, 'em_lote': em_lote}


def _linha(linhas, grupo):
    return next(x for x in linhas if x['grupo'] == grupo)


# ------------------------------------------------------------------ as linhas no motor
def test_linha_com_tudo_confirmado_fica_pronta():
    f = _formato(CHAVE, 'portal-geral-1080x1920', rotacao=ROT0)
    linhas = te.linhas_de_specs([f], [], [], [], tipos_folha={CHAVE: 'JPEG'}, confirmados={'f:' + CHAVE: 3})
    assert len(linhas) == 1
    li = linhas[0]
    assert li['nome'] == '1080 x 1920' and li['origem'] == te.ORIGEM_DA_FOLHA and li['id'] == f['id']
    assert li['spec'] == {'lote': [], 'avulsos': [], 'a_confirmar': 0, 'confirmados': 3}
    assert li['tipo'] == {'escolhe': False, 'tipos': [], 'texto': 'JPEG', 'da_folha': True}
    assert li['faltam'] == [] and li['pronto'] is True
    # o nome nunca leva o id interno da folha
    assert 'portal' not in li['nome'] and 'geral' not in li['nome']


def test_linha_sem_tipo_e_sem_giro_diz_o_que_falta():
    f = _formato(CHAVE_2, 'portal-sao-paulo-300x600', largura=300, altura=600)
    sem_tipo = [{'chave': CHAVE_2, 'nome': '300x600', 'tipos': [], 'texto': ''}]
    linhas = te.linhas_de_specs([f], [], [], sem_tipo, confirmados={'f:' + CHAVE_2: 1})
    li = linhas[0]
    assert li['nome'] == '300 x 600' and li['origem'] == 'sao paulo'
    assert li['tipo'] == {'escolhe': True, 'tipos': [], 'texto': '', 'da_folha': False}
    assert li['faltam'] == [te.FALTA_TIPO, te.FALTA_GIRO] and li['pronto'] is False
    # o tipo escolhido pelo DA e o giro de meia volta deixam a linha pronta
    sem_tipo[0].update(tipos=['jpg', 'png'], texto='JPEG e PNG')
    f['rotacao'] = {'graus': 180, 'sentido': None}
    li = te.linhas_de_specs([f], [], [], sem_tipo)[0]
    assert li['tipo']['tipos'] == ['jpg', 'png'] and li['faltam'] == [] and li['pronto']
    # o quarto de volta sem sentido ainda falta
    f['rotacao'] = {'graus': 90, 'sentido': None}
    assert te.linhas_de_specs([f], [], [], sem_tipo)[0]['faltam'] == [te.FALTA_GIRO]
    f['rotacao'] = {'graus': 90, 'sentido': 'horario'}
    assert te.linhas_de_specs([f], [], [], sem_tipo)[0]['faltam'] == []


def test_linha_com_spec_em_lote_e_divergente_na_propria_linha():
    f = _formato(CHAVE, 'portal-geral-1080x1920', rotacao=ROT0)
    lista = [_valor('v1', 'f:' + CHAVE, '1080 x 1920'),
             _valor('v2', 'f:' + CHAVE, '1080 x 1920', campo='área útil'),
             _valor('v3', 'f:' + CHAVE, '1080 x 1920', campo='peso máximo', em_lote=False,
                    leituras=('250 KB', '150 KB')),
             _valor('g1', 'geral', te.GRUPO_GERAL, campo='borda de 1 px')]
    linhas = te.linhas_de_specs([f], lista, [], [], tipos_folha={CHAVE: 'PNG'})
    li = _linha(linhas, 'f:' + CHAVE)
    assert [v['valor_id'] for v in li['spec']['lote']] == ['v1', 'v2']
    assert [v['valor_id'] for v in li['spec']['avulsos']] == ['v3'] and li['spec']['a_confirmar'] == 3
    assert li['faltam'] == [te.FALTA_SPEC]
    # os valores gerais da folha ficam por ultimo, so com a spec
    assert linhas[-1]['grupo'] == 'geral' and linhas[-1]['nome'] == te.GRUPO_GERAL
    assert linhas[-1]['tipo'] is None and linhas[-1]['faltam'] == [te.FALTA_SPEC]
    assert [v['valor_id'] for v in linhas[-1]['spec']['lote']] == ['g1']


def test_formato_com_duas_medidas_entra_com_tipo_e_giro_desligados():
    sem_medida = [{'formato': 'f9-e01', 'valor_id': 'd1', 'leituras': ['1080 x 1920 px', '1080 x 1350 px'],
                   'texto': '1080 x 1920 px ou 1080 x 1350 px'}]
    lista = [_valor('d1', 'm:f9-e01', sem_medida[0]['texto'], campo='dimensão', em_lote=False,
                    leituras=('1080 x 1920 px', '1080 x 1350 px')),
             _valor('p1', 'm:f9-e01', sem_medida[0]['texto'], em_lote=False)]
    linhas = te.linhas_de_specs([], lista, sem_medida, [])
    assert len(linhas) == 1
    li = linhas[0]
    assert li['grupo'] == 'm:f9-e01' and li['nome'] == sem_medida[0]['texto'] and li['sem_medida'] is True
    assert li['origem'] == te.ORIGEM_DUAS_MEDIDAS and li['tipo'] is None and li['rotacao'] is None
    assert li['faltam'] == [te.FALTA_MEDIDA, te.FALTA_SPEC] and li['pronto'] is False
    assert 'f9-e01' not in li['nome']
    # so a medida pendente: falta so ela
    so_medida = te.linhas_de_specs([], lista[:1], sem_medida, [])[0]
    assert so_medida['faltam'] == [te.FALTA_MEDIDA]


def test_folha_que_diz_tipo_e_giro_e_o_formato_escrito_na_tela():
    folha = _formato(CHAVE, 'portal-geral-1080x1920', rotacao={'graus': 90, 'sentido': 'horario'},
                     giro_da_folha='girar 90 graus')
    escrito = _formato('digitado|tela|300x600', 'digitado-tela-300x600', rotacao=ROT0, digitado=True,
                       largura=300, altura=600)
    linhas = te.linhas_de_specs([folha, escrito], [], [], [], tipos_folha={CHAVE: 'JPEG e PNG'},
                                confirmados={'f:' + CHAVE: 2, 'f:digitado|tela|300x600': 1})
    assert [x['nome'] for x in linhas] == ['1080 x 1920', '300 x 600']
    assert linhas[0]['tipo']['texto'] == 'JPEG e PNG' and linhas[0]['tipo']['da_folha']
    assert linhas[0]['giro_da_folha'] == 'girar 90 graus' and linhas[0]['pronto']
    assert linhas[1]['origem'] == te.ORIGEM_ESCRITO and linhas[1]['digitado'] and linhas[1]['pronto']
    assert linhas[1]['tipo'] == {'escolhe': False, 'tipos': [], 'texto': '', 'da_folha': False}
    assert 'digitado' not in linhas[1]['nome']


def test_formato_da_folha_fora_do_briefing_entra_so_com_a_spec():
    lista = [_valor('x1', 'f:portal|geral|120mmx175mm', '120mm x 175mm', campo='dimensão')]
    linhas = te.linhas_de_specs([], lista, [], [])
    assert len(linhas) == 1 and linhas[0]['nome'] == '120mm x 175mm' and linhas[0]['faltam'] == [te.FALTA_SPEC]
    assert linhas[0]['tipo'] is None and linhas[0]['chave'] is None


def test_origem_tira_so_o_id_da_folha_do_circuito():
    """Revisao da tabela: do circuito sai so o token com a forma do id da folha ('f' e oito hexadecimais, como a
    importacao gera); um circuito nomeado por data ou por palavra hexadecimal continua inteiro, para o DA distinguir
    dois circuitos que diferem so por isso."""
    from vapt.specs import importar
    fid = importar.id_da_folha('0' * 64, 'portal/folha.csv')
    assert te.FORMA_DO_ID_DA_FOLHA.fullmatch(fid), fid
    # o CSV de uma coluna: o id da folha no circuito nunca chega ao DA
    assert te.partes_da_chave('portal|%s-geral|1080x1920' % fid) == ('1080 x 1920', '')
    assert te.partes_da_chave('portal|%s-campinas|300x600' % fid) == ('300 x 600', 'campinas')
    assert te.medida_da_chave('portal|%s-geral|1080x1920' % fid) == '1080 x 1920'
    # a data e a palavra hexadecimal no nome do circuito ficam
    assert te.partes_da_chave('portal|campanha-20241105|1080x1920') == ('1080 x 1920', 'campanha 20241105')
    assert te.partes_da_chave('portal|cafebabe|1080x1920') == ('1080 x 1920', 'cafebabe')
    assert te.medida_da_chave('portal|campanha-20241105|1080x1920') == '1080 x 1920 (campanha 20241105)'
    assert te.medida_da_chave('portal|campanha-20241106|1080x1920') == '1080 x 1920 (campanha 20241106)'


def test_textos_das_linhas_para_o_da():
    for texto in (te.ORIGEM_DA_FOLHA, te.ORIGEM_ESCRITO, te.ORIGEM_TESTE, te.ORIGEM_DUAS_MEDIDAS,
                  te.TIPO_SEM_ESCOLHA):
        assert texto and not any(x in texto for x in tl.PROIBIDOS), texto
        assert '—' not in texto and '–' not in texto


# ------------------------------------------------------------------ o item do que falta
def _lido(sem_tipo):
    return {'modo_dados': {'escolhido': 'b'}, 'bloqueios': [], 'paradas': [], 'camadas_bloqueadas': [],
            'linkados': [], 'specs': {'pendentes': 0, 'formatos': [{'id': 'x', 'rotacao': ROT0}], 'folhas': 1,
                                      'sem_medida': [], 'sem_tipo': sem_tipo},
            'quadros': [], 'fontes_que_faltam': []}


def test_o_que_falta_pede_o_tipo_de_arquivo_dos_formatos_sem_escolha():
    sem_tipo = [{'chave': CHAVE, 'nome': '1080x1920', 'tipos': [], 'texto': ''},
                {'chave': CHAVE_2, 'nome': '300x600', 'tipos': ['jpg'], 'texto': 'JPEG'}]
    itens = [x for x in te.faltam(_lido(sem_tipo), {}) if x['texto'] == te.TIPO_SEM_ESCOLHA]
    assert itens == [{'texto': te.TIPO_SEM_ESCOLHA, 'detalhe': '1080x1920', 'ir': {'passo': 'lido'}}]
    # com o tipo de todos escolhido, o item some
    sem_tipo[0]['tipos'] = ['png']
    assert not [x for x in te.faltam(_lido(sem_tipo), {}) if x['texto'] == te.TIPO_SEM_ESCOLHA]
    # o estado de antes da decisao 209 (sem a chave sem_tipo) continua valendo
    lido_ = _lido([])
    del lido_['specs']['sem_tipo']
    assert not [x for x in te.faltam(lido_, {}) if x['texto'] == te.TIPO_SEM_ESCOLHA]


# ------------------------------------------------------------------ as linhas de um job de verdade
def _linhas_do_job(job):
    """As mesmas entradas que vapt.tela.estado.lido junta, a partir do rascunho das specs do job (o laudo do job de
    specs e de mentira, entao o passo 1 inteiro nao monta aqui)."""
    from vapt import contratos
    from vapt.briefing import modelo as mb
    doc = contratos.ler(job / 'specs' / 'rascunho.json', 'spec/1')
    formatos = [{'id': f['id'], 'chave': f['chave'], 'sem_folha': False, 'digitado': False, 'tem_spec': False,
                 'largura': f['largura'], 'altura': f['altura'], 'rotacao': None,
                 'giro_da_folha': te.giro_da_folha(doc, f['chave'])} for f in mb.formatos_das_specs(job)]
    sem_medida = te.formatos_sem_medida(job)
    return te.linhas_de_specs(formatos, te.specs_pendentes(job), sem_medida, te.formatos_sem_tipo(job),
                              te.tipos_da_folha(doc), te.confirmados_por_grupo(doc, {x['formato'] for x in sem_medida}))


def test_job_com_folha_so_de_medida_monta_as_linhas(tmp_path):
    job = tta._job(tmp_path, tta.SO_MEDIDA)
    linhas = _linhas_do_job(job)
    assert sorted(x['nome'] for x in linhas) == ['1080 x 1920', '300 x 600']
    # antes da confirmacao da medida: a spec espera, e o tipo ainda nao se pergunta
    assert all(x['faltam'] == [te.FALTA_SPEC, te.FALTA_GIRO] and not x['tipo']['escolhe'] for x in linhas), linhas
    assert all(len(x['spec']['lote']) == 1 and x['spec']['lote'][0]['campo'] == 'dimensão' for x in linhas), linhas
    tta._confirmar_tudo(job)
    linhas = _linhas_do_job(job)
    assert all(x['faltam'] == [te.FALTA_TIPO, te.FALTA_GIRO] and x['tipo']['escolhe'] for x in linhas), linhas
    assert all(x['spec']['confirmados'] >= 1 and x['spec']['a_confirmar'] == 0 for x in linhas)
    # a lista do que falta ganha o item do tipo, com a medida de cada formato
    sem_tipo = te.formatos_sem_tipo(job)
    item = next(x for x in te.faltam(_lido(sem_tipo), {}) if x['texto'] == te.TIPO_SEM_ESCOLHA)
    assert set(item['detalhe'].split(', ')) == {'1080x1920', '300x600'}


def test_job_com_folha_que_diz_o_tipo_mostra_o_tipo_da_folha(tmp_path):
    job = tta._job(tmp_path, tta.COM_TIPO)
    tta._confirmar_tudo(job)
    linhas = _linhas_do_job(job)
    li = next(x for x in linhas if x['nome'] == '1080 x 1920')
    assert li['tipo'] == {'escolhe': False, 'tipos': [], 'texto': 'JPEG', 'da_folha': True}
    assert li['faltam'] == [te.FALTA_GIRO]
    assert not [x for x in te.faltam(_lido(te.formatos_sem_tipo(job)), {}) if x['texto'] == te.TIPO_SEM_ESCOLHA]


# ------------------------------------------------------------------ a pagina no Chromium
CSV_SO_MEDIDA = 'Formato\n1080x1920\n300x600\n'


@pytest.fixture
def job_csv(tmp_path, ambiente_limpo):  # noqa: F811
    from vapt.job import nucleo
    from vapt.render import autoteste
    fontes = tmp_path / 'origem-fontes'
    fap.gravar(fontes, 'autoteste.ttf', autoteste.gerar_fonte())
    specs = tmp_path / 'origem-specs'
    (specs / 'portal').mkdir(parents=True)
    (specs / 'portal' / 'folha.csv').write_text(CSV_SO_MEDIDA, encoding='utf-8')
    job = tmp_path / 'job'
    nucleo.criar(job, tp._psd_hostil(tmp_path / 'origem' / 'kv.psd', autoteste.NOME_PS), 'b', fontes=[fontes],
                 specs=specs)
    escolher_modo_do_da(job, 'b')
    r = nucleo.proxima(job, todas=True)
    assert r.codigo == 0, (r.situacao, r.linhas_humanas)
    return job


JS_SEM_ROLAGEM = '''() => { const n = document.getElementById("lido-formatos"), t = n.querySelector(".formatos-tabela");
    return [n.scrollWidth, n.clientWidth, t ? t.scrollWidth : 0, t ? t.clientWidth : 0,
            document.documentElement.scrollWidth, window.innerWidth]; }'''
JS_ESTADOS = '''() => Array.from(document.querySelectorAll("#lido-formatos tr[data-formato] .cel-estado .chip"))
    .map(n => n.textContent)'''
JS_FALTAM = '() => Array.from(document.querySelectorAll("#itens-faltam .texto-item")).map(n => n.textContent)'


def _confirmar_janela(pg):
    tp._esperar(pg, '() => document.getElementById("confirmacao").open ? "1" : ""')
    pg.evaluate('''() => Array.from(document.querySelectorAll("#confirmacao button"))
        .find(b => b.textContent === "Confirmar").click()''')
    tp._esperar(pg, '() => document.documentElement.dataset.estadoAto === "feito" ? "1" : ""')
    pg.evaluate('() => { document.documentElement.dataset.estadoAto = ""; }')


@pytest.mark.skipif(sys.platform != 'win32', reason='o isolador dos filhos roda no Windows')
def test_tabela_a_1280_cabe_e_o_fluxo_comum_deixa_tudo_pronto(job_csv):
    from playwright.sync_api import sync_playwright

    from vapt.chromium import navegador
    conteudo = te.montar(job_csv)
    n_formatos = len(conteudo['estado']['lido']['specs']['formatos'])
    assert n_formatos == 2
    navegador.apontar_playwright()
    with ts.ServidorTela(conteudo, pasta=job_csv, modo_teste=False,
                         atos=ta.atos_do_job(job_csv, conteudo=conteudo)) as srv, sync_playwright() as pw:
        nav = pw.chromium.launch(headless=True, args=list(navegador.ARGUMENTOS))
        pg = nav.new_context(viewport={'width': 1280, 'height': 800}, device_scale_factor=1).new_page()
        try:
            try:
                pg.goto(srv.url_entrada, wait_until='commit')
            except Exception:  # noqa: BLE001 - o 204 nao completa a navegacao
                pass
            pg.goto(srv.url_pagina, wait_until='load')
            tp._esperar(pg, tp.JS_PRONTO)
            tp._esperar(pg, '() => document.getElementById("spec-lote") ? "1" : ""')
            # uma linha por formato, a tabela cabe na coluna e a pagina nao corre para o lado
            assert pg.evaluate('() => document.querySelectorAll("#lido-formatos tr[data-formato]").length') == n_formatos
            larguras = pg.evaluate(JS_SEM_ROLAGEM)
            assert larguras[0] <= larguras[1] and larguras[2] <= larguras[3] and larguras[4] <= larguras[5], larguras
            cabecas = pg.evaluate('() => Array.from(document.querySelectorAll("#lido-formatos th[scope=col]")).map(t => t.firstChild.textContent)')
            assert cabecas == ['Formato', 'Spec', 'Tipo', 'Giro', 'Estado'], cabecas
            # os dois caminhos de gravacao, ditos no cabecalho
            notas = pg.evaluate('() => Array.from(document.querySelectorAll("#lido-formatos th .col-nota")).map(t => t.textContent)')
            assert notas == ['pede Confirmar', 'pede Confirmar', 'salvo no rascunho'], notas
            assert all(e.startswith('Falta: spec') for e in pg.evaluate(JS_ESTADOS))
            # os segmentados sao acessiveis e nada vem marcado
            assert pg.evaluate('() => document.querySelectorAll("#lido-formatos [role=group][aria-label]").length') >= n_formatos
            assert pg.evaluate('() => document.querySelectorAll("#lido-formatos button[aria-pressed=true]").length') == 0
            # a barra de lote segue a vista enquanto o DA rola a tabela
            assert pg.evaluate('() => getComputedStyle(document.querySelector("#lido-formatos .lote-barra")).position') == 'sticky'
            texto = pg.evaluate('() => document.getElementById("lido-formatos").innerText')
            assert not any(x in texto for x in tl.PROIBIDOS) and '—' not in texto, texto
            # 1. marcar todos e confirmar os marcados (uma janela so)
            pg.evaluate('() => document.getElementById("spec-lote-todos").click()')
            pg.evaluate('() => document.getElementById("spec-lote-confirmar").click()')
            _confirmar_janela(pg)
            tp._esperar(pg, '() => document.getElementById("spec-lote") ? "" : "1"')
            tp._esperar(pg, '() => document.getElementById("tipo-lote") ? "1" : ""')
            assert all(e == 'Falta: tipo, giro' for e in pg.evaluate(JS_ESTADOS)), pg.evaluate(JS_ESTADOS)
            # 2. todos em JPEG, pela janela. Os botoes do lote sao acoes, nao escolhas: sem aria-pressed, com o nome
            # inteiro (0.17.3)
            assert pg.evaluate('() => document.querySelectorAll("#tipo-lote button[aria-pressed]").length') == 0
            assert pg.evaluate('() => document.querySelectorAll("#tipo-lote button[data-ato=spec_tipos]").length') == 3
            assert pg.evaluate('() => Array.from(document.querySelectorAll("#tipo-lote button")).map(b => b.textContent)') == \
                ['Todos em JPEG', 'Todos em PNG', 'Todos em JPEG e PNG']
            pg.evaluate('() => document.querySelector("#tipo-lote button[data-tipos=jpg]").click()')
            _confirmar_janela(pg)
            # 0.17.3: o lote fica, para trocar todos de uma vez; o do tipo que todos ja tem fica desligado e diz por que
            tp._esperar(pg, '() => document.querySelector("#tipo-lote button[data-tipos=jpg]").disabled ? "1" : ""')
            assert pg.evaluate('() => document.querySelector("#tipo-lote button[data-tipos=jpg]").title') == \
                'Todos os formatos já estão em JPEG.'
            assert pg.evaluate('() => document.querySelectorAll("#tipo-lote button[data-ato=spec_tipos]").length') == 2
            assert pg.evaluate('''() => Array.from(document.querySelectorAll("#lido-formatos tr[data-formato] .cel-tipo button[aria-pressed=true]"))
                .map(b => b.textContent)''') == ['JPEG'] * n_formatos
            # trocar todos para PNG: a janela diz quais tinham outro tipo
            pg.evaluate('() => document.querySelector("#tipo-lote button[data-tipos=png]").click()')
            tp._esperar(pg, '() => document.getElementById("confirmacao").open ? "1" : ""')
            janela = pg.evaluate('() => document.getElementById("confirmacao").innerText')
            assert 'Muda o tipo de' in janela and '(era JPEG)' in janela and 'pedem render e aprovação de novo' in janela, janela
            _confirmar_janela(pg)
            tp._esperar(pg, '() => document.querySelector("#tipo-lote button[data-tipos=png]").disabled ? "1" : ""')
            assert pg.evaluate('''() => Array.from(document.querySelectorAll("#lido-formatos tr[data-formato] .cel-tipo button[aria-pressed=true]"))
                .map(b => b.textContent)''') == ['PNG'] * n_formatos
            # o tipo ja escolhido e so o indicador: sem ato, o clique nele nao abre a janela nem grava de novo
            assert pg.evaluate('() => document.querySelectorAll("#lido-formatos .cel-tipo button[aria-pressed=true][data-ato]").length') == 0
            assert pg.evaluate('() => document.querySelectorAll("#lido-formatos .cel-tipo button[aria-pressed=false][data-ato=spec_tipos]").length') == 2 * n_formatos
            pg.evaluate('() => document.querySelector("#lido-formatos .cel-tipo button[aria-pressed=true]").click()')
            assert pg.evaluate('() => document.getElementById("confirmacao").open') is False
            assert srv.contagem['ato_confirmar'] == 3
            assert all(e == 'Falta: giro' for e in pg.evaluate(JS_ESTADOS)), pg.evaluate(JS_ESTADOS)
            # 3. sem giro nos que faltam: grava no rascunho, sem janela
            pg.evaluate('() => document.getElementById("giro-lote").click()')
            tp._esperar(pg, '() => document.getElementById("giro-lote") ? "" : "1"')
            assert pg.evaluate(JS_ESTADOS) == ['Pronto'] * n_formatos
            assert pg.evaluate('() => document.querySelectorAll("#lido-formatos tr[data-giro=feito]").length') == n_formatos
            tp._esperar(pg, '() => document.documentElement.dataset.rascunho === "salvo" ? "1" : ""')
            tp._esperar(pg, '() => Array.from(document.querySelectorAll("#itens-faltam .texto-item")).some(n => n.textContent.includes("giro")) ? "" : "1"')
            faltam = pg.evaluate(JS_FALTAM)
            assert not any('spec' in t or 'tipo de arquivo' in t or 'giro' in t for t in faltam), faltam
            larguras = pg.evaluate(JS_SEM_ROLAGEM)
            assert larguras[0] <= larguras[1] and larguras[2] <= larguras[3] and larguras[4] <= larguras[5], larguras
        finally:
            nav.close()
        assert srv.contagem['ato_confirmar'] == 3 and srv.contagem['csrf_recusado'] == 0
    assert all(x['tipos'] == ['png'] for x in te.formatos_sem_tipo(job_csv))
