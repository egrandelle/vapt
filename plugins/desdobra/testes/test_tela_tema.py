# -*- coding: utf-8 -*-
"""0.13.0: o tema claro ou escuro da tela no Chromium, com a pagina de verdade.

Criterios cobertos aqui:
  - sem tema guardado, a tela segue o esquema de cores do sistema (o Chromium em modo escuro): o botao "Tema escuro"
    fica pressionado e a moldura escurece;
  - o texto da peca sem cor propria herda a tinta fixa da peca (#18181b) nos dois temas, nunca a cor do texto da
    moldura: a peca nunca muda com o tema;
  - o clique em "Tema claro" troca o tema na hora e grava a escolha no arquivo de preferencias (fora do job).
Tudo sintetico: o KV A de testes/sinteticos e o arquivo de preferencias em tmp_path.
"""
import time

import pytest

import test_tela_palco as tp
from desdobra.tela import atos as ta
from desdobra.tela import estado as te
from desdobra.tela import preferencias as tpref
from desdobra.tela import servidor as ts
from sinteticos import kv_a_b as kv

TINTA_DA_PECA = 'rgb(24, 24, 27)'  # numero-neutro: #18181b, a tinta fixa da peca

# a cor herdada de cada .mundo do palco do KV e a de um trecho sem cor propria (a cor tirada do style, como no run do
# PSD sem FillColor, que o leitor deixa sem cor_hex)
JS_TINTAS = '''() => {
  const mundos = Array.from(document.querySelectorAll("#palco-kv .mundo")).map(m => getComputedStyle(m).color);
  const trecho = document.querySelector("#palco-kv .trecho");
  let herdada = null;
  if (trecho) { trecho.style.color = ""; herdada = getComputedStyle(trecho).color; }
  return {mundos: mundos, herdada: herdada, texto: getComputedStyle(document.body).color};
}'''


@pytest.fixture
def pw():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope='module')
def job_kv(tmp_path_factory):
    from desdobra.chromium import navegador
    navegador.apontar_playwright()
    return kv.criar_job(tmp_path_factory.mktemp('tema'), 'a')['job']


class _Tela:
    """O servidor da tela com o arquivo de preferencias e a pagina num Chromium com o esquema de cores escolhido."""

    def __init__(self, pw, job, preferencias, esquema):
        from desdobra.chromium import navegador
        conteudo = te.montar(job)
        self.srv = ts.ServidorTela(conteudo, pasta=job, modo_teste=True, atos=ta.atos_do_job(job, conteudo=conteudo),
                                   preferencias=preferencias)
        self.srv.__enter__()
        self.nav = pw.chromium.launch(headless=True, args=list(navegador.ARGUMENTOS))
        self.pg = self.nav.new_context(viewport={'width': 1366, 'height': 768}, device_scale_factor=1,
                                       color_scheme=esquema).new_page()
        try:
            self.pg.goto(self.srv.url_entrada, wait_until='commit')
        except Exception:  # noqa: BLE001 - o 204 nao completa a navegacao
            pass
        # com a maquina carregada, a resposta 204 da entrada as vezes chega depois e interrompe a pagina: uma tentativa
        # a mais
        for tentativa in range(2):  # numero-neutro: duas tentativas
            try:
                self.pg.goto(self.srv.url_pagina, wait_until='load')
                break
            except Exception:  # noqa: BLE001 - a navegacao interrompida pela 204 atrasada
                if tentativa:
                    raise
        tp._esperar(self.pg, tp.JS_PRONTO)

    def __enter__(self):
        return self.pg

    def __exit__(self, *exc):
        self.nav.close()
        self.srv.__exit__(None, None, None)


def _pressionado(pg):
    return pg.evaluate('() => Array.from(document.querySelectorAll("#tema [data-tema]"))'
                       '.filter(b => b.getAttribute("aria-pressed") === "true").map(b => b.dataset.tema)')


def _funcoes(pg):
    pg.evaluate('() => document.querySelector("#passos [data-passo=funcoes]").click()')
    tp._esperar(pg, '() => document.querySelector("#palco-kv .mundo") ? "1" : ""')
    time.sleep(0.3)  # numero-neutro: segundos, o palco termina de montar


def test_sem_tema_guardado_segue_o_sistema_e_a_peca_fica_com_a_tinta_dela(pw, job_kv, tmp_path):
    arq = tmp_path / 'dados-plugin' / tpref.ARQUIVO
    arq.parent.mkdir()
    with _Tela(pw, job_kv, arq, 'dark') as pg:
        assert pg.evaluate('() => document.documentElement.getAttribute("data-theme")') is None
        assert _pressionado(pg) == ['dark']
        _funcoes(pg)
        t = pg.evaluate(JS_TINTAS)
        # a moldura escureceu (o texto dela ficou claro), e a peca nao
        assert t['texto'] != TINTA_DA_PECA, t
        assert t['mundos'] and set(t['mundos']) == {TINTA_DA_PECA}, t
        assert t['herdada'] == TINTA_DA_PECA, t
    assert not arq.exists()  # so ver a tela nunca grava preferencia


def test_tema_claro_troca_na_hora_e_fica_guardado(pw, job_kv, tmp_path):
    arq = tmp_path / 'dados-plugin' / tpref.ARQUIVO
    arq.parent.mkdir()
    with _Tela(pw, job_kv, arq, 'dark') as pg:
        pg.evaluate('() => document.getElementById("tema-claro").click()')
        tp._esperar(pg, '() => document.documentElement.getAttribute("data-theme") || ""', 'light')
        assert _pressionado(pg) == ['light']
        fim = time.monotonic() + 10  # numero-neutro: segundos de espera pela gravacao
        while tpref.ler(arq) is None and time.monotonic() < fim:
            time.sleep(0.1)  # numero-neutro: intervalo do teste
        assert tpref.ler(arq) == 'claro'
        _funcoes(pg)
        t = pg.evaluate(JS_TINTAS)
        assert set(t['mundos']) == {TINTA_DA_PECA} and t['herdada'] == TINTA_DA_PECA, t
    # a proxima janela, ainda com o sistema escuro, abre clara
    with _Tela(pw, job_kv, arq, 'dark') as pg:
        assert pg.evaluate('() => document.documentElement.getAttribute("data-theme")') == 'light'
        assert _pressionado(pg) == ['light']
