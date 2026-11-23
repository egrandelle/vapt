# -*- coding: utf-8 -*-
"""0.13.0, o visual Vidro, segunda rodada: as pendencias que o Duda aprovou ("ok" a cada uma), cada uma com a prova no
Chromium.

Criterios cobertos aqui:
  - P1: a parte da peca fora do formato fica na sangria do mockup 03 (o tom --bleed e o tracejado --bleed-stroke), nos
    dois temas; a sangria nunca pega o clique, sai no Ver limpo, e a peca dentro do formato nao muda com o tema;
  - P2: a tecla Enter ao lado de "Salvar e seguir", e o Enter aciona o botao pelo mesmo caminho do clique (um pedido
    por Enter); o Enter nao aciona nada quando tem outro dono (campo, botao, aba, palco, janela, painel, lista do que
    falta), com tecla junto, com o botao desligado ou ja conferindo;
  - P3: a frase do rascunho (#selo) mora no rodape, logo depois do passo, em todos os estados, sem cobrir nada e sem
    rolagem lateral; o rodape segue com 46 px nas janelas baixas (P4);
  - P5: a lupa na busca das camadas, a legenda "Enviado ao Claude" com o nivel de cada modo, o ponto da cor da classe
    nas etiquetas do palco e o quadro de raio 14 com a mesa em volta do palco das Familias;
  - revisao da 0.13.0: a etiqueta alargada pelo ponto nunca sai do palco (faixa 1920x192 a 1024), a frase do erro do
    rascunho inteira no rodape a 1024, a frase de sempre a 1280, o tracejado so nos lados da sangria, e o Enter sem
    efeito com o editor de texto ou o controle da quebra abertos.
Tudo sintetico: o KV A de testes/sinteticos/kv_a_b, o PSD de test_tela_palco e a galeria de test_tela_galeria.
"""
import json
import pathlib
import re
import shutil

import pytest

import test_tela_palco as tp
import test_tela_revisao_092 as rv
import test_tela_revisao_093 as r93
from vapt.tela import estado as te
from vapt.tela import servidor as ts
from sinteticos import kv_a_b as kv
from test_tela_palco import job_palco  # noqa: F401 - a fixture do PSD com o fundo que sangra
from test_tela_galeria import job_galeria  # noqa: F401 - a galeria com a faixa 1920x192 (revisao da 0.13.0)

PASTA_TELA = pathlib.Path(tp.__file__).resolve().parents[1] / 'tela'
PEDIR = re.compile(r'.*/api/ato/pedir$')
MOTIVO = 'O Vapt recusou o pedido de teste.'
# a cor resolvida de um token da moldura, pelo mesmo caminho do CSS (light-dark no tema da pagina)
JS_COR = '''t => { const s = document.createElement("span"); s.style.color = "var(" + t + ")";
  document.body.appendChild(s); const c = getComputedStyle(s).color; s.remove(); return c; }'''
JS_CAIXA = '''s => { const n = typeof s === "string" ? document.querySelector(s) : s; if (!n) return null;
  const r = n.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; }'''


@pytest.fixture(scope='module')
def base(tmp_path_factory):
    from vapt.chromium import navegador
    navegador.apontar_playwright()
    raiz = tmp_path_factory.mktemp('vidro-0130')
    a = kv.criar_job(raiz, 'a')
    r93._antes(a['job'])
    return {'kva': (a['job'], a['funcoes'])}


@pytest.fixture
def pw():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        yield p


def _copia(base, tmp_path):
    job, funcoes = base['kva']
    destino = tmp_path / 'kva'
    shutil.copytree(job.parent, destino)
    return destino / job.name, funcoes


def _soltar_foco(pg):
    pg.evaluate('() => { if (document.activeElement && document.activeElement !== document.body) '
                'document.activeElement.blur(); }')


def _ligado(pg):
    return pg.evaluate('() => { const b = document.getElementById("salvar-seguir"); '
                       'return !b.disabled && b.getAttribute("aria-busy") !== "true"; }')


class _Contador:
    """Conta os pedidos do ato "salvar" que chegam ao servidor. Recusa cada um com um motivo (a tela volta ao estado de
    antes) ou, com segurar, deixa o pedido parado ate o teste soltar."""

    def __init__(self, pg):
        self.pg = pg
        self.pedidos = []
        self.segurar = False
        self.parados = []
        pg.route(PEDIR, self._tratar)

    def _tratar(self, r):
        try:
            corpo = json.loads(r.request.post_data or '{}')
        except ValueError:
            corpo = {}
        if corpo.get('ato') != 'salvar':
            r.continue_()
            return
        self.pedidos.append(corpo)
        if self.segurar:
            self.parados.append(r)
        else:
            _recusar(r)

    def depois_de(self, tecla='Enter', espera_ms=700):
        antes = len(self.pedidos)
        self.pg.keyboard.press(tecla)
        self.pg.wait_for_timeout(espera_ms)
        tp._esperar(self.pg, '() => document.getElementById("salvar-seguir").getAttribute("aria-busy") === "true" '
                             '? "" : "1"', teto_s=10)
        return len(self.pedidos) - antes

    def soltar(self):
        for r in self.parados:
            _recusar(r)
        self.parados = []

    def parar(self):
        self.pg.unroute(PEDIR)


def _recusar(r):
    r.fulfill(status=403, content_type='application/json; charset=utf-8',
              body=json.dumps({'motivo': MOTIVO}, ensure_ascii=False))


# ------------------------------------------------------------------ P2: a tecla Enter do "Salvar e seguir"
def test_tecla_enter_fica_ao_lado_do_salvar_e_o_botao_diz_o_atalho():
    """O HTML: a tecla (kbd, escondida do leitor de tela) logo antes do botao, no grupo da direita; o botao anuncia o
    atalho e o texto dele continua so "Salvar e seguir"."""
    html = (PASTA_TELA / 'tela.html').read_text(encoding='utf-8')
    grupo = re.search(r'<div class="acoes-direita">(.*?)</div>', html, re.S).group(1)
    assert re.search(r'<kbd id="tecla-salvar" class="tecla" aria-hidden="true">Enter</kbd>\s*'
                     r'<button type="button" id="salvar-seguir"[^>]*\saria-keyshortcuts="Enter"[^>]*>Salvar e seguir'
                     r'</button>', grupo), grupo


def test_enter_aciona_o_salvar_como_o_clique_e_so_quando_nao_tem_outro_dono(base, pw, tmp_path):
    """Com as familias confirmadas, o Enter sem foco em nada manda exatamente um pedido do "Salvar e seguir", como o
    clique, e abre a mesma janela. Nos lugares em que o Enter tem outro dono, com tecla junto, com o botao desligado ou
    conferindo, nenhum pedido sai."""
    job, funcoes = _copia(base, tmp_path)
    with rv._Tela(pw, job, 1600, 900, rascunho_kv=funcoes) as pg:
        conta = _Contador(pg)
        rv._passo(pg, 'pecas')
        # o botao desligado (as familias por confirmar): nem pedido, nem a tecla
        assert not _ligado(pg)
        assert pg.evaluate('() => getComputedStyle(document.getElementById("tecla-salvar")).display') == 'none'
        _soltar_foco(pg)
        assert conta.depois_de() == 0
        conta.parar()
        r93._confirmar_familias(pg)
        conta = _Contador(pg)
        # a tecla aparece colada no botao, e o botao segue com o texto dele
        tecla = pg.evaluate(JS_CAIXA, '#tecla-salvar')
        botao = pg.evaluate(JS_CAIXA, '#salvar-seguir')
        assert tecla[2] <= botao[0] and botao[0] - tecla[2] <= 16, (tecla, botao)  # numero-neutro: o espaco do grupo
        assert pg.evaluate('() => document.getElementById("salvar-seguir").textContent') == 'Salvar e seguir'
        # a tecla cabe no rodape das janelas do Duda, sem cobrir nada e sem rolagem lateral
        for largura, altura in JANELAS:
            pg.set_viewport_size({'width': largura, 'height': altura})
            pg.wait_for_timeout(400)
            _conferir_rodape(pg.evaluate(JS_RODAPE), largura, altura)
            assert pg.evaluate('() => getComputedStyle(document.getElementById("tecla-salvar")).display') != 'none'
        pg.set_viewport_size({'width': 1600, 'height': 900})
        pg.wait_for_timeout(400)

        # o Enter sem foco: um pedido, recusado, e o motivo aparece no rodape como no clique
        _soltar_foco(pg)
        assert conta.depois_de() == 1
        assert r93._legivel_perto_do_salvar(pg) == 'ok'
        assert MOTIVO in pg.evaluate('() => document.getElementById("aviso-acoes").textContent')
        # o Enter no proprio botao: o do botao vale, e sai um pedido so
        pg.focus('#salvar-seguir')
        assert conta.depois_de() == 1

        # conferindo: o segundo Enter nao manda outro pedido, e a tecla sai
        conta.segurar = True
        _soltar_foco(pg)
        n = len(conta.pedidos)
        pg.keyboard.press('Enter')
        tp._esperar(pg, '() => document.getElementById("salvar-seguir").getAttribute("aria-busy") === "true" '
                        '? "1" : ""', teto_s=10)
        pg.wait_for_timeout(400)
        assert len(conta.pedidos) == n + 1
        assert pg.evaluate('() => getComputedStyle(document.getElementById("tecla-salvar")).display') == 'none'
        n = len(conta.pedidos)
        _soltar_foco(pg)
        pg.keyboard.press('Enter')
        pg.wait_for_timeout(600)
        assert len(conta.pedidos) == n
        conta.segurar = False
        conta.soltar()
        tp._esperar(pg, '() => document.getElementById("salvar-seguir").getAttribute("aria-busy") === "true" '
                        '? "" : "1"', teto_s=10)

        # com tecla junto
        for tecla_junto in ('Control+Enter', 'Shift+Enter', 'Alt+Enter'):
            _soltar_foco(pg)
            assert _ligado(pg)
            assert conta.depois_de(tecla_junto) == 0, tecla_junto

        # a lista do que falta aberta
        r93._clicar(pg, '#faltam')
        _soltar_foco(pg)
        assert conta.depois_de() == 0
        r93._clicar(pg, '#faltam')
        # o painel "Como editar" aberto
        assert pg.evaluate('() => !document.getElementById("barra-edicao").hidden')
        r93._clicar(pg, '#ed-ajuda')
        _soltar_foco(pg)
        assert conta.depois_de() == 0
        r93._clicar(pg, '#ed-ajuda-fechar')
        # uma janela aberta (Ver grande), com o foco no titulo dela
        pg.evaluate('() => { const d = document.getElementById("ver-grande"); d.showModal(); '
                    'document.getElementById("ver-grande-titulo").focus(); }')
        assert conta.depois_de() == 0
        pg.evaluate('() => document.getElementById("ver-grande").close()')
        # a aba do passo
        assert _ligado(pg)
        pg.focus('#passos [data-passo=pecas]')
        assert conta.depois_de() == 0
        # os campos: a busca das camadas, o campo dos formatos escritos
        rv._passo(pg, 'funcoes')
        pg.focus('#arvore-busca')
        assert conta.depois_de() == 0
        rv._passo(pg, 'lido')
        pg.focus('#digitados-campo')
        assert conta.depois_de() == 0
        # o palco: o elemento em foco (o Enter escolhe o elemento) e o campo Tamanho dele
        rv._passo(pg, 'pecas')
        assert _ligado(pg)
        pg.focus('#palco .rotulo[data-elemento]')
        assert conta.depois_de() == 0
        assert pg.evaluate('() => !!document.querySelector("#palco .rotulo.selecionado")')
        assert _ligado(pg)
        pg.focus('#ed-tamanho')
        assert conta.depois_de() == 0
        assert pg.evaluate('() => document.activeElement.id') == 'ed-tamanho'
        # revisao da 0.13.0: o editor de texto e o controle da quebra abertos, com o foco solto (o clique numa parte da
        # tela sem foco, o controle redesenhado): o Enter e deles, nenhum pedido sai, e a tecla sai junto
        pg.keyboard.press('Escape')
        pg.focus('#palco .rotulo[aria-keyshortcuts=F2]')
        pg.keyboard.press('Enter')
        pg.wait_for_timeout(300)
        abertos = 0
        for botao, painel, fechar in (('#ed-texto', 'editor-texto', '#ed-texto-cancelar'),
                                      ('#ed-quebra', 'editor-quebra', '#ed-quebra-fechar')):
            if pg.evaluate('b => document.querySelector(b).disabled', botao):
                continue
            r93._clicar(pg, botao)
            tp._esperar(pg, f'() => document.getElementById("{painel}").hidden ? "" : "1"', teto_s=10)
            assert _ligado(pg)
            _soltar_foco(pg)
            assert pg.evaluate('() => getComputedStyle(document.getElementById("tecla-salvar")).display') == 'none'
            assert conta.depois_de() == 0, painel
            assert not pg.evaluate(f'() => document.getElementById("{painel}").hidden'), painel
            r93._clicar(pg, fechar)
            tp._esperar(pg, f'() => document.getElementById("{painel}").hidden ? "1" : ""', teto_s=10)
            abertos += 1
        assert abertos >= 1
        conta.parar()

        # sem o contador: o Enter abre a mesma janela do clique, e o Enter dentro dela nao confirma
        pg.keyboard.press('Escape')
        _soltar_foco(pg)
        tp._esperar(pg, '() => document.getElementById("salvar-seguir").disabled ? "" : "1"', teto_s=20)
        _soltar_foco(pg)
        pg.keyboard.press('Enter')
        pg.wait_for_selector('#confirmacao[open]', timeout=60000)
        pg.keyboard.press('Enter')
        pg.wait_for_timeout(500)
        assert pg.evaluate('() => document.getElementById("confirmacao").open')
        pg.evaluate('() => document.querySelector("#confirmacao [data-resposta=nao]").click()')
        tp._esperar(pg, '() => document.documentElement.dataset.estadoAto === "cancelado" ? "1" : ""', teto_s=30)


# ------------------------------------------------------------------ P3: o selo do rascunho no rodape
JS_RODAPE = '''() => {
  const caixa = n => { const r = n.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; };
  const vis = n => n && !n.hidden && n.getClientRects().length > 0 && getComputedStyle(n).display !== "none" &&
    getComputedStyle(n).visibility !== "hidden" && n.getBoundingClientRect().width > 0;
  const ids = ["passos-trilho", "passo-atual", "selo", "salvo", "dica-acoes", "dica-ir", "confirmar-familia",
               "tecla-salvar", "salvar-seguir"];
  const nos = ids.map(i => [i, document.getElementById(i)]).filter(p => vis(p[1]));
  const cobre = [];
  for (let i = 0; i < nos.length; i++) for (let j = i + 1; j < nos.length; j++) {
    const a = caixa(nos[i][1]), b = caixa(nos[j][1]);
    const w = Math.min(a[2], b[2]) - Math.max(a[0], b[0]), h = Math.min(a[3], b[3]) - Math.max(a[1], b[1]);
    if (w > 1 && h > 1) cobre.push([nos[i][0], nos[j][0]]);
  }
  const s = document.getElementById("selo"), f = document.querySelector("footer.acoes");
  const cs = getComputedStyle(s);
  return {cobre: cobre, selo: caixa(s), rodape: caixa(f), altura: f.getBoundingClientRect().height,
    janela: [innerWidth, innerHeight], visivel: vis(s), letra: parseFloat(cs.fontSize), estado: s.dataset.estado || "",
    texto: s.textContent, cortado_lado: s.scrollWidth > s.clientWidth + 1,
    cortado_alto: s.scrollHeight > s.clientHeight + 1,
    rola_pagina: document.documentElement.scrollWidth > document.documentElement.clientWidth,
    rola_rodape: f.scrollWidth > f.clientWidth, no_topo: !!s.closest("header.topo"),
    no_rodape: !!s.closest("footer.acoes .acoes-esquerda"),
    depois_do_passo: s.previousElementSibling && s.previousElementSibling.classList.contains("acoes-divisor") &&
      s.previousElementSibling.previousElementSibling === document.getElementById("passo-atual"),
    regiao: [s.getAttribute("role"), s.getAttribute("aria-live")]};
}'''
JANELAS = [(1024, 768), (1280, 800), (1600, 900), (2048, 720)]  # numero-neutro: as janelas do Duda e dos testes


def _conferir_rodape(r, largura, altura):
    assert r['no_rodape'] and not r['no_topo'] and r['depois_do_passo'], r
    assert r['regiao'] == ['status', 'polite'], r
    assert r['visivel'], r
    assert r['cobre'] == [], (largura, r)
    assert not r['rola_pagina'] and not r['rola_rodape'], (largura, r)
    s, f = r['selo'], r['rodape']
    assert s[0] >= f[0] - 1 and s[2] <= f[2] + 1 and s[1] >= f[1] - 1 and s[3] <= f[3] + 1, (largura, r)
    assert s[2] <= largura and s[3] <= altura, (largura, r)
    # P4 fica como esta: 46 px nas janelas de ate 800 de altura, 68 nas outras
    assert round(r['altura']) == (46 if altura <= 800 else 68), (largura, altura, r['altura'])  # numero-neutro: o mockup


def test_selo_do_rascunho_mora_no_rodape_em_todos_os_estados(base, pw, tmp_path):
    """O selo fica no rodape, logo depois do passo, nas janelas de 1024 a 2048: na frase de sempre, na escolha que nao
    gravou (em frase legivel ate a 1024) e na escolha que gravou. Nada no rodape se cobre e nada rola de lado."""
    job, funcoes = _copia(base, tmp_path)
    with rv._Tela(pw, job, 1600, 900, rascunho_kv=funcoes) as pg:
        rv._passo(pg, 'pecas')
        tp._esperar(pg, '() => document.getElementById("palco").dataset.pronto || ""', teto_s=20)
        for largura, altura in JANELAS:
            pg.set_viewport_size({'width': largura, 'height': altura})
            pg.wait_for_timeout(500)
            r = pg.evaluate(JS_RODAPE)
            assert r['estado'] == 'pronto' and r['texto'] == 'Suas escolhas ficam salvas no rascunho', r
            _conferir_rodape(r, largura, altura)
            # revisao da 0.13.0: no rodape a frase cabe a 1280; o ponto (B6) fica so abaixo de 1100
            if largura >= 1280:  # numero-neutro: a janela do Duda
                assert not r['cortado_lado'] and r['letra'] >= 13, (largura, r)  # numero-neutro: o tom do passo
            else:
                assert r['selo'][2] - r['selo'][0] <= 10, (largura, r)  # numero-neutro: o ponto de 8 px
        # a escolha que nao grava
        pg.set_viewport_size({'width': 1600, 'height': 900})
        # recusada com motivo: a tela para de tentar sozinha, e o selo fica no erro enquanto o teste mede
        pg.route(re.compile(r'.*/api/rascunho.*'), lambda q: r93._recusar_rascunho(q)
                 if q.request.method != 'GET' else q.continue_())
        rv._passo(pg, 'funcoes')
        pg.evaluate('() => document.querySelector("#arvore button").click()')
        pg.wait_for_timeout(200)
        pg.evaluate('() => document.querySelector("#detalhe button[data-funcao=imagem]").click()')
        tp._esperar(pg, '() => document.getElementById("selo").dataset.estado === "erro" ? "1" : ""', teto_s=15)
        rv._passo(pg, 'pecas')
        for largura, altura in JANELAS:
            pg.set_viewport_size({'width': largura, 'height': altura})
            pg.wait_for_timeout(500)
            r = pg.evaluate(JS_RODAPE)
            assert r['estado'] == 'erro' and 'Não foi possível salvar' in r['texto'], r
            _conferir_rodape(r, largura, altura)
            s = r['selo']
            assert r['letra'] >= 12 and s[2] - s[0] > 80 and s[3] - s[1] > 10, (largura, r)  # numero-neutro: D3
            # revisao da 0.13.0: a frase inteira aparece, sem corte em altura nem de lado, tambem a 1024
            assert not r['cortado_alto'] and not r['cortado_lado'], (largura, r)
        pg.unroute(re.compile(r'.*/api/rascunho.*'))
        # a escolha que grava
        pg.set_viewport_size({'width': 1600, 'height': 900})
        rv._passo(pg, 'funcoes')
        pg.evaluate('() => document.querySelector("#arvore button").click()')
        pg.wait_for_timeout(200)
        pg.evaluate('() => document.querySelector("#detalhe button[data-funcao=fundo]").click()')
        tp._esperar(pg, '() => document.getElementById("selo").dataset.estado === "salvo" ? "1" : ""', teto_s=30)
        for largura, altura in JANELAS:
            pg.set_viewport_size({'width': largura, 'height': altura})
            pg.wait_for_timeout(500)
            r = pg.evaluate(JS_RODAPE)
            assert r['texto'] == 'Salvo no rascunho', r
            _conferir_rodape(r, largura, altura)


# ------------------------------------------------------------------ P1: a sangria, e o selo so de ver (P3)
JS_SANGRIA = '''() => {
  const fora = Array.from(document.querySelectorAll("#palco .fora"));
  const esc = document.querySelector("#palco .escala"), cs = getComputedStyle(esc, "::before");
  const no_ponto = fora.map(f => { const r = f.getBoundingClientRect();
    const n = document.elementFromPoint((r.left + r.right) / 2, (r.top + r.bottom) / 2);
    return n ? n.className : ""; });
  // revisao da 0.13.0: o tracejado e a borda do ::before da escala, so nos lados em que a peca passa do formato
  const e = esc.getBoundingClientRect(), m = document.querySelector("#palco .moldura").getBoundingClientRect();
  const passa = {Top: e.top < m.top - 0.5, Bottom: e.bottom > m.bottom + 0.5, Left: e.left < m.left - 0.5,
    Right: e.right > m.right + 0.5};
  const lados = Object.keys(passa).map(l => [l, passa[l], cs["border" + l + "Style"], cs["border" + l + "Width"],
    cs["border" + l + "Color"]]);
  return {n: fora.length, fundos: fora.map(f => getComputedStyle(f).backgroundImage),
    eventos: fora.map(f => getComputedStyle(f).pointerEvents), no_ponto: no_ponto, lados: lados,
    traco: [cs.display, cs.pointerEvents], mundo: getComputedStyle(document.querySelector(
      "#palco .mundo")).color, limpo: fora.map(f => getComputedStyle(f).display)};
}'''


def _conferir_traco(s, traco):
    """O tracejado so nos lados em que a peca passa do formato, em --bleed-stroke; nos outros, nenhum traco."""
    assert s['traco'] == ['block', 'none'], s
    assert any(lado[1] for lado in s['lados']), s
    for _l, passa, estilo, espessura, cor in s['lados']:
        if passa:
            # 1,5 px no CSS; o Chromium desenha a borda em pixel inteiro na tela de densidade 1
            assert estilo == 'dashed' and cor == traco and float(espessura.replace('px', '')) >= 1, s
        else:
            assert float(espessura.replace('px', '')) == 0, s
BLEED = {'light': ('rgba(120, 120, 230, 0.26)', 'rgba(60, 60, 200, 0.55)'),
         'dark': ('rgba(120, 120, 255, 0.2)', 'rgba(150, 150, 255, 0.6)')}


def test_sangria_do_mockup_nos_dois_temas_e_a_peca_nao_muda(job_palco, pw):
    """O formato 400x240 do PSD de test_tela_palco tem o fundo que sangra: a parte de fora fica no tom --bleed, com o
    tracejado --bleed-stroke em volta, nos dois temas. A sangria nunca pega o clique e sai no Ver limpo. A peca dentro
    do formato e a mesma imagem nos dois temas. O selo so de ver fica no rodape, depois do passo."""
    conteudo = te.montar(job_palco)
    fotos = {}
    with ts.ServidorTela(conteudo) as srv:
        nav, pg = tp._pagina_da_tela(pw, srv, 1440, 1000)  # numero-neutro: a janela do mockup
        try:
            r = pg.evaluate(JS_RODAPE)
            assert r['texto'] == 'Só para ver, nada é gravado' and r['estado'] == '', r
            _conferir_rodape(r, 1440, 1000)  # numero-neutro: a janela do mockup
            tp._abrir_formato(pg, conteudo['estado'], 'perto')
            for tema in ('light', 'dark'):
                pg.emulate_media(color_scheme=tema)
                pg.wait_for_timeout(500)
                s = pg.evaluate(JS_SANGRIA)
                assert s['n'] > 0, s
                bleed, traco = BLEED[tema]
                assert pg.evaluate(JS_COR, '--bleed') == bleed and pg.evaluate(JS_COR, '--bleed-stroke') == traco
                assert all(bleed in f for f in s['fundos']), (tema, s)
                assert set(s['eventos']) == {'none'} and 'fora' not in ' '.join(s['no_ponto']), s
                _conferir_traco(s, traco)
                assert s['mundo'] == 'rgb(24, 24, 27)', s
                # o Ver limpo tira a sangria e o tracejado; a foto da peca dentro do formato, sem nada por cima
                pg.evaluate('() => document.getElementById("ver-limpo").click()')
                pg.wait_for_timeout(300)
                limpo = pg.evaluate(JS_SANGRIA)
                assert set(limpo['limpo']) == {'none'} and limpo['traco'][0] == 'none', limpo
                c = pg.evaluate(JS_CAIXA, '#palco .moldura')
                fotos[tema] = pg.screenshot(clip={'x': c[0] + 2, 'y': c[1] + 2, 'width': c[2] - c[0] - 4,
                                                  'height': c[3] - c[1] - 4})
                pg.evaluate('() => document.getElementById("ver-limpo").click()')
        finally:
            nav.close()
    assert fotos['light'] == fotos['dark']


# ------------------------------------------------------------------ P5: lupa, nivel do modo, ponto e quadro
JS_MODOS = '''() => {
  const cor = n => getComputedStyle(n).backgroundColor;
  return Array.from(document.querySelectorAll("#lido-modo .modo[data-modo]")).map(b => {
    const nv = b.querySelector(".nivel"), corpo = b.querySelector(".modo-corpo"), marca = b.querySelector(".modo-marca");
    const r = x => x.getBoundingClientRect();
    return {modo: b.dataset.modo, escolhido: b.getAttribute("aria-pressed") === "true",
      papel: nv && nv.getAttribute("role"), nome: nv && nv.getAttribute("aria-label"),
      ligadas: nv ? nv.querySelectorAll(".nivel-on").length : -1, barras: nv ? nv.children.length : -1,
      cores: nv ? Array.from(nv.querySelectorAll(".nivel-on")).map(cor) : [],
      entre: nv ? r(corpo).right <= r(nv).left && r(nv).right <= r(marca).left : false, texto: b.innerText};
  });
}'''
NIVEL = {'a': (3, 'Envia textos e miniaturas'), 'b': (2, 'Envia só textos'), 'c': (1, 'Envia só contagens e medidas')}
JS_ETIQUETAS = '''() => Array.from(document.querySelectorAll("#palco .etiqueta"))
  .filter(n => n.getClientRects().length && getComputedStyle(n).visibility !== "hidden").map(n => {
    const p = getComputedStyle(n, "::before"), r = n.getBoundingClientRect(), a = document.getElementById("palco")
      .getBoundingClientRect(), rot = n.closest(".rotulo");
    return {classe: n.dataset.classe || "", cor: p.backgroundColor, largura: p.width, texto: n.textContent,
      cheia: rot.classList.contains("selecionado") || rot.classList.contains("destaque"),
      dentro: r.left >= a.left - 1 && r.right <= a.right + 1 && r.top >= a.top - 1 && r.bottom <= a.bottom + 1};
  })'''
COR_DA_CLASSE = {'base': '--c-img', 'texto': '--c-txt', 'marca': '--c-brand', 'global': '--c-all', 'fora': '--c-all',
                 'indeterminado': '--c-all'}


def test_lupa_nivel_do_modo_ponto_nas_etiquetas_e_quadro_do_palco(base, pw, tmp_path):
    """Passo 1: a legenda "Enviado ao Claude" ao lado do titulo do modo e o nivel de cada modo entre o texto e o
    circulo, no azul so na linha escolhida. Passo 2: a lupa dentro da busca, sem cobrir o texto. Familias: o ponto da
    cor da classe em cada etiqueta, a etiqueta inteira no palco, e o palco num quadro de raio 14 com a mesa em volta,
    sem rolagem em Ajustar."""
    job, funcoes = _copia(base, tmp_path)
    with rv._Tela(pw, job, 1440, 1000, rascunho_kv=funcoes) as pg:  # numero-neutro: a janela do mockup
        rv._passo(pg, 'lido')
        leg = pg.evaluate('''() => { const n = document.getElementById("enviado-legenda"),
            t = document.getElementById("t-modo"), a = n.getBoundingClientRect(), b = t.getBoundingClientRect();
          return {texto: n.textContent, barras: n.querySelectorAll(".nivel-legenda > span").length,
            escondida: n.querySelector(".nivel-legenda").getAttribute("aria-hidden"),
            fora: !n.closest("#faixa-lido") && !n.closest("#lido-modo"), lado: a.left > b.right,
            linha: a.top < b.bottom && a.bottom > b.top, modo: n.querySelectorAll("[data-modo]").length}; }''')
        assert leg == {'texto': 'Enviado ao Claude', 'barras': 3, 'escondida': 'true', 'fora': True, 'lado': True,
                       'linha': True, 'modo': 0}, leg
        modos = pg.evaluate(JS_MODOS)
        assert {m['modo'] for m in modos} >= {'c'} and any(m['escolhido'] for m in modos), modos
        acento, cinza = pg.evaluate(JS_COR, '--accent'), pg.evaluate(JS_COR, '--m-on')
        for m in modos:
            assert (m['ligadas'], m['nome']) == NIVEL[m['modo']] and m['barras'] == 3, m
            assert m['papel'] == 'img' and m['entre'], m
            assert set(m['cores']) == {acento if m['escolhido'] else cinza}, m
            assert 'Enviado' not in m['texto'], m
        # passo 2: a lupa
        rv._passo(pg, 'funcoes')
        lupa = pg.evaluate('''() => { const s = document.querySelector(".arvore-ferramentas .busca-lupa"),
            i = document.getElementById("arvore-busca"), a = s.getBoundingClientRect(), b = i.getBoundingClientRect();
          return {escondida: s.getAttribute("aria-hidden"), visivel: a.width > 0 && a.height > 0,
            dentro: a.left >= b.left && a.right <= b.right && a.top >= b.top && a.bottom <= b.bottom,
            antes_do_texto: a.right <= b.left + parseFloat(getComputedStyle(i).paddingLeft)}; }''')
        assert lupa == {'escondida': 'true', 'visivel': True, 'dentro': True, 'antes_do_texto': True}, lupa
        vistas = '() => Array.from(document.querySelectorAll("#arvore button")).filter(b => b.getClientRects().length).length'
        antes = pg.evaluate(vistas)
        rv._valor(pg, '#arvore-busca', 'nenhuma-camada-assim')
        pg.wait_for_timeout(300)
        assert pg.evaluate(vistas) < antes
        rv._valor(pg, '#arvore-busca', '')
        # Familias: o ponto nas etiquetas e o quadro
        rv._passo(pg, 'pecas')
        tp._esperar(pg, '() => document.getElementById("palco").dataset.pronto || ""', teto_s=20)
        pg.wait_for_timeout(600)
        etiquetas = pg.evaluate(JS_ETIQUETAS)
        assert etiquetas, etiquetas
        branco = pg.evaluate(JS_COR, '--on-acao')
        for e in etiquetas:
            assert e['classe'] in COR_DA_CLASSE and e['largura'] == '6px', e
            assert e['cor'] == (branco if e['cheia'] else pg.evaluate(JS_COR, COR_DA_CLASSE[e['classe']])), e
            assert e['dentro'], e
            assert e['texto'][:1].isalpha(), e
        quadro = pg.evaluate('''() => { const a = document.getElementById("palco"), m = a.closest(".mesa-palco"),
            s = getComputedStyle(a), r = a.getBoundingClientRect(), q = m.getBoundingClientRect();
          return {raio: s.borderTopLeftRadius, margem: [parseFloat(s.marginTop), parseFloat(s.marginRight),
            parseFloat(s.marginLeft)], esquerda: r.left - q.left, direita: q.right - r.right,
            molduras: a.querySelectorAll(".moldura").length, vista: a.dataset.vista,
            rola: a.scrollWidth > a.clientWidth || a.scrollHeight > a.clientHeight}; }''')
        assert quadro['raio'] == '14px' and min(quadro['margem']) > 0, quadro  # numero-neutro: o raio do mockup
        assert quadro['esquerda'] > 0 and quadro['direita'] > 0, quadro
        assert quadro['molduras'] == 1 and quadro['vista'] == 'ajustar' and not quadro['rola'], quadro
        mold = pg.evaluate(JS_CAIXA, '#palco .moldura')
        area = pg.evaluate(JS_CAIXA, '#palco')
        assert mold[0] >= area[0] and mold[1] >= area[1] and mold[2] <= area[2] and mold[3] <= area[3], (mold, area)


# ------------------------------------------------------------------ revisao da 0.13.0: etiquetas na faixa estreita
JS_PALCO_ETIQUETAS = '''() => { const a = document.getElementById("palco"), r = a.getBoundingClientRect();
  const l = r.left + a.clientLeft, t = r.top + a.clientTop;
  const vis = Array.from(document.querySelectorAll("#palco .etiqueta")).filter(n => n.getClientRects().length &&
    getComputedStyle(n).visibility !== "hidden" && getComputedStyle(n).display !== "none");
  const cx = vis.map(n => { const q = n.getBoundingClientRect(); return [q.left, q.top, q.right, q.bottom]; });
  const sobre = [];
  for (let i = 0; i < cx.length; i++) for (let j = i + 1; j < cx.length; j++) {
    const w = Math.min(cx[i][2], cx[j][2]) - Math.max(cx[i][0], cx[j][0]);
    const h = Math.min(cx[i][3], cx[j][3]) - Math.max(cx[i][1], cx[j][1]);
    if (w > 2 && h > 2) sobre.push([vis[i].textContent, vis[j].textContent]);
  }
  return {n: vis.length, vista: a.dataset.vista, rola: [a.scrollWidth, a.clientWidth, a.scrollHeight, a.clientHeight],
    fora: vis.filter((n, k) => cx[k][0] < l - 1 || cx[k][2] > l + a.clientWidth + 1 || cx[k][1] < t - 1 ||
      cx[k][3] > t + a.clientHeight + 1).map(n => n.textContent), sobre: sobre}; }'''


def test_etiqueta_com_ponto_nunca_sai_do_palco_na_faixa_estreita(job_galeria, pw):  # noqa: F811
    """A faixa 1920x192 da galeria (PSD de test_tela_palco) a 1024 e a 1280: o ponto alarga cada etiqueta, e a que
    passaria da borda do palco tenta outro lugar ou sai da vista, como a que cobriria outra. Nenhuma etiqueta visivel
    fica cortada na borda, nenhuma cobre outra, e o palco nao rola em Ajustar. O tracejado da sangria fica so nos lados
    em que a peca passa do formato."""
    import test_tela_galeria as tg
    from vapt.chromium import navegador
    navegador.apontar_playwright()
    job = job_galeria
    estado = te.montar(job)['estado']
    for largura, altura in ((1024, 768), (1280, 800)):  # numero-neutro: as janelas do Duda
        with rv._Tela(pw, job, largura, altura) as pg:
            rv._passo(pg, 'pecas')
            for fid in ('faixa', 'quadrado'):
                tg._abrir(pg, estado, fid)
                tp._esperar(pg, '() => document.documentElement.dataset.previa === "pronta" ? "1" : ""')
                pg.wait_for_timeout(600)
                r = pg.evaluate(JS_PALCO_ETIQUETAS)
                assert r['n'] > 0 and r['vista'] == 'ajustar', (largura, fid, r)
                assert r['fora'] == [] and r['sobre'] == [], (largura, fid, r)
                assert r['rola'][0] <= r['rola'][1] and r['rola'][2] <= r['rola'][3], (largura, fid, r)
                s = pg.evaluate(JS_SANGRIA)
                if s['n']:
                    _conferir_traco(s, pg.evaluate(JS_COR, '--bleed-stroke'))
