# -*- coding: utf-8 -*-
"""O ato espera a gravacao do rascunho que ja saiu (achado antigo, de antes da decisao 215; pedido do Duda).

Antes, o ato so gravava o rascunho que esperava na fila ou que tinha falhado: com a gravacao ja em voo (POST
/api/rascunho sem resposta), o pedido do ato chegava ao servidor antes dela e era conferido contra o rascunho de antes
da ultima mexida do DA. Cobertos aqui, no Chromium sem janela (modo de teste):
  - o ato da janela (pedirAto) com a gravacao em voo: /api/ato/pedir so sai depois que ela volta, e o servidor ja tem a
    ultima escolha quando o pedido chega;
  - a mudanca feita durante a gravacao em voo tambem grava antes do ato, depois da gravacao em voo (nunca junto);
  - a gravacao em voo que falha: o ato nao vai, e o selo diz que o clique nao foi registrado;
  - o ato longo do painel (pedirAtoLongo) espera do mesmo jeito, e nao vai quando a gravacao falha (em voo ou na fila).
A pagina so pede o ato: a rota /api/ato/pedir e respondida pelo teste (recusa com motivo), e nada roda no servidor.
Tudo sintetico: o job de duas linhas de test_tela_ato_render (derivado, sem render) e o meio de teste da tela.
"""
import json
import re
import shutil
import sys

import pytest

import test_tela_ato_render as tar
import test_tela_palco as tp
from test_tela_ato_render import modelo  # noqa: F401 - o job de duas linhas derivado, sem render
from vapt.tela import rascunho as tr

pytestmark = pytest.mark.skipif(sys.platform != 'win32', reason='o isolador dos filhos roda no Windows')

MOTIVO_ATO = 'Pedido de teste: a rota do ato respondeu sem rodar nada.'
MOTIVO_RASCUNHO = 'O PSD foi lido de novo com esta janela aberta.'
CLIQUE_SEM_GRAVAR = 'O clique não foi registrado porque a sua última escolha não foi salva.'  # tela.js, pedirAto
PAINEL_SEM_GRAVAR = 'O trabalho não foi pedido porque a sua última escolha não foi salva.'  # tela.js, PAINEL_SEM_GRAVAR
ERRO_PEDIDO = 'A tela não conseguiu pedir o trabalho. Tente de novo.'  # tela.js, ERRO_PEDIDO
MODO = '#lido-modo button[data-ato=modo_dados][data-modo=b]'
ESPERA_MS = 1500  # numero-neutro: ms de folga, mais que a espera do rascunho (tela.rascunho_espera_ms)


@pytest.fixture
def job(modelo, tmp_path):  # noqa: F811
    destino = tmp_path / 'job'
    shutil.copytree(modelo, destino)
    return destino


def _so_a_funcao(funcoes):
    """As funcoes do passo 2 por camada, sem a observacao."""
    return {k: (v or {}).get('funcao') for k, v in (funcoes or {}).items()}


def _funcoes_no_disco(job):
    arq = job / tr.ARQUIVO
    return _so_a_funcao(json.loads(arq.read_text(encoding='utf-8')).get('funcoes')) if arq.exists() else {}


class _Rede:
    """As rotas da pagina que o teste segura: a gravacao do rascunho (POST) e o pedido do ato. eventos, na ordem:
    ('rascunho', funcoes do corpo), ('solto',), ('ato', gravacoes ainda presas, funcoes gravadas no servidor)."""

    def __init__(self, job):
        self.job = job
        self.segurar = False
        self.falhar = False
        # quantas gravacoes seguintes falham sem motivo (a falha passageira: erro do servidor, sem frase)
        self.sem_motivo = 0
        self.presos = []
        self.eventos = []

    def rascunho(self, r):
        if r.request.method != 'POST':
            return r.continue_()
        self.eventos.append(('rascunho', _so_a_funcao(json.loads(r.request.post_data or '{}').get('funcoes'))))
        if self.segurar:
            self.presos.append(r)
            return None
        return self._seguir(r)

    def _seguir(self, r):
        if self.sem_motivo:
            self.sem_motivo -= 1
            return r.fulfill(status=500, content_type='application/json; charset=utf-8',  # numero-neutro: HTTP
                             body='{}')
        if self.falhar:
            return r.fulfill(status=403, content_type='application/json; charset=utf-8',  # numero-neutro: HTTP
                             body=json.dumps({'motivo': MOTIVO_RASCUNHO}, ensure_ascii=False))
        return r.continue_()

    def soltar(self):
        """Solta a gravacao presa e as que chegarem depois."""
        self.segurar = False
        self.eventos.append(('solto',))
        while self.presos:
            self._seguir(self.presos.pop(0))

    def ato(self, r):
        self.eventos.append(('ato', len(self.presos), _funcoes_no_disco(self.job)))
        return r.fulfill(status=403, content_type='application/json; charset=utf-8',  # numero-neutro: HTTP
                         body=json.dumps({'motivo': MOTIVO_ATO}, ensure_ascii=False))

    def atos(self):
        return [e for e in self.eventos if e[0] == 'ato']


class _Tela:
    """O servidor da tela em modo de teste e a pagina no Chromium, com as rotas presas pela _Rede."""

    def __init__(self, job):
        from playwright.sync_api import sync_playwright

        from vapt.chromium import navegador
        navegador.apontar_playwright()
        self.rede = _Rede(job)
        self.srv = tar._servidor(job).iniciar()
        self.pw = sync_playwright().start()
        self.nav = self.pw.chromium.launch(headless=True, args=list(navegador.ARGUMENTOS))
        self.pg = self.nav.new_context(viewport={'width': 1366, 'height': 768}, device_scale_factor=1).new_page()
        try:
            self.pg.goto(self.srv.url_entrada, wait_until='commit')
        except Exception:  # noqa: BLE001 - o 204 nao completa a navegacao
            pass
        self.pg.goto(self.srv.url_pagina, wait_until='load')
        tp._esperar(self.pg, tp.JS_PRONTO)
        tp._esperar(self.pg, '() => document.documentElement.dataset.rascunho || ""', 'pronto')
        self.pg.route(re.compile(r'.*/api/rascunho$'), self.rede.rascunho)
        self.pg.route(re.compile(r'.*/api/ato/pedir$'), self.rede.ato)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.nav.close()
        self.pw.stop()
        self.srv.parar()

    def js(self, expressao, arg=None):
        return self.pg.evaluate(expressao, arg)

    def passo(self, passo):
        self.js('p => document.querySelector("#passos [data-passo=" + p + "]").click()', passo)
        self.pg.wait_for_timeout(300)  # numero-neutro: ms para o passo montar

    def esperar(self, cond, teto_ms=15000):  # numero-neutro: ms, teto do teste
        """Espera uma condicao do lado do teste, com o laco da pagina rodando (as rotas so andam assim)."""
        passos = teto_ms // 50  # numero-neutro: ms por volta
        for _ in range(passos):
            if cond():
                return
            self.pg.wait_for_timeout(50)  # numero-neutro: ms por volta
        raise AssertionError('a condicao nao chegou: %r' % (self.rede.eventos,))

    def camada(self):
        """A primeira camada do passo 2: o id dela (a chave em funcoes)."""
        self.passo('funcoes')
        self.js('() => document.querySelector("#arvore button[data-camada]").click()')
        self.pg.wait_for_timeout(200)  # numero-neutro: ms para o detalhe montar
        return self.js('() => document.querySelector("#arvore button[data-camada]").dataset.camada')

    def funcao(self, f):
        self.js('f => document.querySelector("#detalhe button[data-funcao=" + f + "]").click()', f)

    def gravacao_presa(self):
        """A mudanca do DA espera a pausa e sai: a gravacao fica presa, em voo."""
        self.esperar(lambda: len(self.rede.presos) == 1 and self.js('() => document.documentElement.dataset.rascunho')
                     == 'salvando')

    def ocupado(self, seletor):
        return self.js('s => document.querySelector(s).getAttribute("aria-busy") === "true"', seletor)


# ------------------------------------------------------------------ o ato da janela (pedirAto)
def test_ato_espera_a_gravacao_em_voo(job):
    with _Tela(job) as t:
        cid = t.camada()
        t.rede.segurar = True
        t.funcao('imagem')
        t.gravacao_presa()
        t.passo('lido')
        t.js('s => document.querySelector(s).click()', MODO)
        t.pg.wait_for_timeout(ESPERA_MS)
        antes = list(t.rede.eventos)
        trabalhando = t.ocupado(MODO)
        t.rede.soltar()
        t.esperar(lambda: t.rede.atos() and not t.ocupado(MODO))
        aviso = t.js('() => document.getElementById("aviso-acoes").textContent')
        desligado = t.js('s => document.querySelector(s).disabled', MODO)
    # nada do ato enquanto a gravacao estava em voo; o botao mostrou que trabalhava
    assert not [e for e in antes if e[0] == 'ato'], antes
    assert trabalhando
    # o pedido saiu depois da gravacao, com a ultima escolha ja no servidor; o botao voltou
    assert t.rede.atos() == [('ato', 0, {cid: 'imagem'})], t.rede.eventos
    assert MOTIVO_ATO in aviso and desligado is False


def test_mudanca_durante_a_gravacao_em_voo_grava_antes_do_ato(job):
    with _Tela(job) as t:
        cid = t.camada()
        t.rede.segurar = True
        t.funcao('imagem')
        t.gravacao_presa()
        # a mudanca nova e o clique no ato, de uma vez, antes da pausa do rascunho
        t.js('([f, s]) => { document.querySelector("#detalhe button[data-funcao=" + f + "]").click();'
             ' document.querySelector(s).click(); }', ['grafismo', MODO])
        t.pg.wait_for_timeout(ESPERA_MS)
        antes = list(t.rede.eventos)
        t.rede.soltar()
        t.esperar(lambda: t.rede.atos() and not t.ocupado(MODO))
        t.esperar(lambda: t.js('() => document.documentElement.dataset.rascunho') == 'salvo')
    # enquanto a primeira gravacao estava em voo, nem a mudanca nova nem o ato sairam
    assert antes == [('rascunho', {cid: 'imagem'})], antes
    # depois dela, a mudanca nova, e so entao o ato, com ela gravada no servidor
    assert t.rede.eventos == [('rascunho', {cid: 'imagem'}), ('solto',), ('rascunho', {cid: 'grafismo'}),
                              ('ato', 0, {cid: 'grafismo'})], t.rede.eventos
    assert _funcoes_no_disco(job) == {cid: 'grafismo'}


def test_gravacao_em_voo_que_falha_nao_deixa_o_ato_ir(job):
    with _Tela(job) as t:
        t.camada()
        t.rede.segurar = True
        t.funcao('imagem')
        t.gravacao_presa()
        t.passo('lido')
        t.js('s => document.querySelector(s).click()', MODO)
        t.pg.wait_for_timeout(ESPERA_MS)
        t.rede.falhar = True
        t.rede.soltar()
        t.esperar(lambda: not t.ocupado(MODO))
        t.pg.wait_for_timeout(ESPERA_MS)
        selo = t.js('() => document.getElementById("selo").textContent')
        rascunho = t.js('() => document.documentElement.dataset.rascunho')
        aviso = t.js('() => document.getElementById("aviso-acoes").textContent')
        desligado = t.js('s => document.querySelector(s).disabled', MODO)
    assert t.rede.atos() == [], t.rede.eventos
    assert selo == CLIQUE_SEM_GRAVAR and rascunho == 'erro'
    assert MOTIVO_RASCUNHO in aviso and desligado is False
    assert _funcoes_no_disco(job) == {}


@pytest.mark.parametrize('falhas', [1, 2], ids=['a_nova_grava', 'a_nova_falha'])  # numero-neutro: gravacoes que falham
def test_gravacao_em_voo_que_falha_sem_motivo_tenta_de_novo(job, falhas):
    """A gravacao em voo falha sem motivo (passageira): o ato grava mais uma vez, como no clique feito com a pagina ja
    em erro. Se essa grava, o ato vai; se tambem falha, nao vai."""
    with _Tela(job) as t:
        cid = t.camada()
        t.rede.segurar = True
        t.funcao('imagem')
        t.gravacao_presa()
        t.passo('lido')
        t.js('s => document.querySelector(s).click()', MODO)
        t.pg.wait_for_timeout(ESPERA_MS)
        t.rede.sem_motivo = falhas
        t.rede.soltar()
        if falhas == 1:
            t.esperar(lambda: t.rede.atos() and not t.ocupado(MODO))
        else:
            # le logo: a nova tentativa sozinha do rascunho (2 s depois) gravaria e trocaria o selo
            t.esperar(lambda: len([e for e in t.rede.eventos if e[0] == 'rascunho']) == 2 and not t.ocupado(MODO))
        selo = t.js('() => document.getElementById("selo").textContent')
        rascunho = t.js('() => document.documentElement.dataset.rascunho')
    gravacoes = [('rascunho', {cid: 'imagem'}), ('solto',), ('rascunho', {cid: 'imagem'})]
    if falhas == 1:
        assert t.rede.eventos == gravacoes + [('ato', 0, {cid: 'imagem'})], t.rede.eventos
        assert _funcoes_no_disco(job) == {cid: 'imagem'}
    else:
        assert t.rede.eventos[:3] == gravacoes and t.rede.atos() == [], t.rede.eventos
        assert selo == CLIQUE_SEM_GRAVAR and rascunho == 'erro'


# ------------------------------------------------------------------ o ato longo do painel (pedirAtoLongo)
def _painel_pronto(t):
    t.passo('formatos')
    tp._esperar(t.pg, '() => document.documentElement.dataset.painel || ""', 'pronto')
    tp._esperar(t.pg, '() => document.getElementById("renderizar-afetados").disabled ? "" : "1"')


def _painel(t):
    return t.js('''() => ({mensagem: document.getElementById("painel-mensagem").textContent,
        desligado: document.getElementById("renderizar-afetados").disabled})''')


def test_ato_longo_espera_a_gravacao_em_voo(job):
    with _Tela(job) as t:
        _painel_pronto(t)
        cid = t.camada()
        t.rede.segurar = True
        t.funcao('imagem')
        t.gravacao_presa()
        _painel_pronto(t)
        t.js('() => document.getElementById("renderizar-afetados").click()')
        t.pg.wait_for_timeout(ESPERA_MS)
        antes = list(t.rede.eventos)
        t.rede.soltar()
        t.esperar(lambda: t.rede.atos() and _painel(t)['mensagem'])
        t.esperar(lambda: not _painel(t)['desligado'])
        p = _painel(t)
    assert not [e for e in antes if e[0] == 'ato'], antes
    assert t.rede.atos() == [('ato', 0, {cid: 'imagem'})], t.rede.eventos
    # a recusa do pedido de teste aparece como sempre, e o painel volta
    assert p['mensagem'] == ERRO_PEDIDO, p


@pytest.mark.parametrize('em_voo', [True, False], ids=['em_voo', 'na_fila'])
def test_ato_longo_nao_vai_quando_a_gravacao_falha(job, em_voo):
    with _Tela(job) as t:
        _painel_pronto(t)
        t.camada()
        if em_voo:
            t.rede.segurar = True
            t.funcao('imagem')
            t.gravacao_presa()
            _painel_pronto(t)
            t.js('() => document.getElementById("renderizar-afetados").click()')
            t.pg.wait_for_timeout(ESPERA_MS)
            t.rede.falhar = True
            t.rede.soltar()
        else:
            # a mudanca e o clique antes da pausa do rascunho: a gravacao que esperava na fila vai antes e falha
            t.rede.falhar = True
            t.js('() => { document.querySelector("#detalhe button[data-funcao=imagem]").click();'
                 ' document.querySelector("#passos [data-passo=formatos]").click();'
                 ' document.getElementById("renderizar-afetados").click(); }')
        t.esperar(lambda: _painel(t)['mensagem'])
        t.pg.wait_for_timeout(ESPERA_MS)
        p = _painel(t)
        rascunho = t.js('() => document.documentElement.dataset.rascunho')
    assert t.rede.atos() == [], t.rede.eventos
    assert p == {'mensagem': PAINEL_SEM_GRAVAR, 'desligado': False}, p
    assert rascunho == 'erro'
