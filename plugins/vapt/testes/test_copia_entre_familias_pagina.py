# -*- coding: utf-8 -*-
"""Decisao 215, etapa E9: "Copiar o layout de outra familia" na pagina, no Chromium sem janela (modo de teste).

  - o botao "Copiar layout de outra familia" no cabecalho da familia, com uma opcao por origem pelo nome do arquivo;
    a janela do servidor com o texto da copia; Cancelar nao grava nada; Copiar grava pelo ato e a familia volta com o
    layout copiado (a nota no cabecalho, o selo, o resumo e a mensagem);
  - o palco do destino e o da previa gravada (a mesma conta do Salvar) e, depois de confirmar e de "Salvar e seguir"
    pela pagina, o da derivacao gravada;
  - a galeria travada enquanto a copia vale: o clique numa versao e as setas nao mudam a escolha nem o rascunho;
  - o Desfazer (resposta 2 do Duda): a edicao do DA depois da copia sai num clique, e o clique seguinte tira a copia
    inteira e devolve a familia como estava (a versao escolhida, as edicoes), com a galeria destravada;
  - o "Salvar e seguir" (decisao 212): com o briefing salvo, abrir e cancelar a janela da copia o deixa apagado; a
    copia feita o liga de novo.
Tudo sintetico: o KV A deitado de sinteticos.kv_a_b (os dois arquivos em pe na galeria) e o KV da diagonal
(sinteticos.kv_diagonal, em pe, sem galeria), numa pasta temporaria; nenhum job real.
"""
import json

import pytest

import test_copia_entre_familias_editor as tce
import test_familia_diagonal as tfd
import test_tela_edicao as tted
import test_tela_escrita as tte
import test_tela_familia_0100 as tf
import test_tela_palco as tp
import test_tela_servidor as tts
from vapt import contratos, plataforma
from vapt.derivacao import nucleo as nd
from vapt.tela import atos as ta
from vapt.tela import estado as te
from vapt.tela import rascunho as tr
from vapt.tela import servidor as ts
from sinteticos import kv_a_b as KA

PLAT = plataforma.obter()
FORMATOS_A = [('v1080x1350', 1080, 1350), ('v1080x1920', 1080, 1920)]
TOL = 0.01  # numero-neutro: px, o arredondamento da caixa no palco e na derivacao
REL = 1e-5  # numero-neutro: o estilo do Chromium escreve o numero com 6 algarismos
SALVAR, SALVO = 'Salvar e seguir', 'Briefing salvo'  # os textos do botao (tela.js, SALVAR e SALVO)

# as caixas dos elementos no palco, em px do formato: o rotulo de cada elemento menos o canto do mundo (a sangria).
# O estilo guarda 6 algarismos da posicao no mundo: com a forma enorme que sangra (o azul da diagonal), o mundo comeca
# longe do formato e a posicao lida perde as casas; a conferencia leva isso em conta (_confere_palco)
JS_CAIXAS = '''() => {
  const f = document.querySelector("#palco .quadro-fundo");
  const x0 = -parseFloat(f.style.left), y0 = -parseFloat(f.style.top);
  return {mundo: [x0, y0], caixas: Object.fromEntries(Array.from(
    document.querySelectorAll("#palco .rotulo[data-elemento]")).map(r => {
      const x = parseFloat(r.style.left) + x0, y = parseFloat(r.style.top) + y0;
      return [r.dataset.elemento, [x, y, x + parseFloat(r.style.width), y + parseFloat(r.style.height)]]; }))}; }'''
JS_GALERIA = '''() => Array.from(document.querySelectorAll("#variantes [role=tab]")).map(b =>
  [b.dataset.variante, b.getAttribute("aria-selected"), b.getAttribute("aria-disabled")])'''
JS_VISTA = '''() => ({
  cabecalho: document.getElementById("cabecalho-familia").innerText,
  selo: document.getElementById("selo-palco").textContent,
  resumo: document.getElementById("resumo-edicao").textContent,
  mensagem: document.getElementById("ed-mensagem").textContent,
  nota: document.getElementById("nota-galeria").textContent,
  salvar: [document.getElementById("salvar-seguir").textContent, document.getElementById("salvar-seguir").disabled]})'''
# a familia redesenhada com a previa nova: o resumo (so a previa da familia o monta) diz ou nao a copia
JS_COM_A_COPIA = '''() => document.documentElement.dataset.previa === "pronta" &&
  document.getElementById("palco").dataset.pronto === "1" &&
  document.getElementById("resumo-edicao").textContent.indexOf("Layout copiado do") >= 0 ? "1" : ""'''
JS_SEM_A_COPIA = JS_COM_A_COPIA.replace('>= 0 ? "1"', '< 0 ? "1"')


def _job_deitado(base):
    if PLAT.nome in ('sem-suporte', 'mac'):
        pytest.skip('sem isolador neste sistema')
    antes = KA.FORMATOS
    KA.FORMATOS = FORMATOS_A
    try:
        j = KA.criar_job(base, 'a')
    finally:
        KA.FORMATOS = antes
    j['conteudo'] = te.montar(j['job'])
    j['el'] = {papel: 'el%d' % lid for papel, lid in j['ids'].items()}
    j['gid'] = {fid: tfd._familia_de(j['conteudo'], fid) for fid, _w, _h in FORMATOS_A}
    return j


def _rascunho(job):
    arq = job / tr.ARQUIVO
    return json.loads(arq.read_text(encoding='utf-8')) if arq.exists() else {}


def _familia(job, gid):
    return (_rascunho(job).get('familias') or {}).get(gid) or {}


def _escolhas(f):
    return f.get('versao'), f.get('edicoes') or [], f.get('quebras') or []


def _abrir_copiar(pg):
    """Abre a lista "Copiar layout de outra familia" e clica na unica origem; espera a janela do servidor."""
    pg.evaluate('() => document.querySelector("#cabecalho-familia .copiar-layout").open = true')
    pg.evaluate('() => document.querySelector(\'#cabecalho-familia .copiar-layout [data-ato="familia_copiar"]\')'
                '.click()')
    tp._esperar(pg, '() => document.getElementById("confirmacao").open ? "1" : ""')
    return pg.evaluate('''() => ({titulo: document.getElementById("confirmacao-titulo").textContent,
        texto: document.getElementById("confirmacao-texto").textContent,
        sim: document.querySelector("#confirmacao [data-resposta=sim]").textContent})''')


def _responder(pg, resposta):
    pg.evaluate('r => document.querySelector("#confirmacao [data-resposta=" + r + "]").click()', resposta)
    tp._esperar(pg, '() => ["feito", "cancelado", "erro"].indexOf(document.documentElement.dataset.estadoAto) >= 0 '
                    '? "1" : ""')
    assert pg.evaluate('() => document.documentElement.dataset.estadoAto') != 'erro'


def _mover(pg, eid):
    tted._focar(pg, eid)
    pg.keyboard.press('ArrowRight')
    tted._esperar_salvo(pg)


def _desfazer(pg):
    pg.evaluate('() => document.getElementById("ed-desfazer").click()')
    tted._esperar_salvo(pg)


def _caixas_paradas(pg):
    """As caixas do palco depois que a familia foi redesenhada de vez: depois do ato, o passo 3 e montado de novo e a
    familia abre mais de uma vez; vale o palco que fica igual em duas leituras seguidas, com a previa pronta."""
    antes = None
    for _ in range(40):  # numero-neutro: tentativas, cerca de 30 s
        tp._esperar(pg, JS_COM_A_COPIA)
        agora = pg.evaluate(JS_CAIXAS)
        if agora == antes:
            return agora
        antes = agora
        pg.wait_for_timeout(700)  # numero-neutro: ms entre as leituras
    raise AssertionError('o palco nao parou: %r' % antes)


def _confere_palco(lido, esperadas, fora=()):
    """As caixas do palco (JS_CAIXAS) e as esperadas (a previa gravada ou a derivacao), sem os textos (o rotulo do
    texto cresce com a tinta medida no palco). A folga de cada numero: TOL mais os 6 algarismos do estilo, contados da
    posicao no mundo e do canto dele."""
    pal = {k: v for k, v in lido['caixas'].items() if k not in fora}
    esp = {k: v for k, v in esperadas.items() if k not in fora}
    assert sorted(pal) == sorted(esp)
    for k, c in esp.items():
        for i, v in enumerate(c):
            canto = lido['mundo'][i % 2]
            assert abs(pal[k][i] - v) <= TOL + REL * (abs(canto) + abs(v - canto)), (k, pal[k], c)


# ------------------------------------------------------------------ KV deitado: a galeria, o palco e o Desfazer
def test_copiar_na_pagina_trava_a_galeria_e_o_desfazer_volta_tudo(tmp_path):
    from playwright.sync_api import sync_playwright

    from vapt.chromium import navegador
    j = _job_deitado(tmp_path)
    job, conteudo, g, el = j['job'], j['conteudo'], j['gid'], j['el']
    destino, origem = g['v1080x1350'], g['v1080x1920']
    grupo = next(x for o in conteudo['estado']['orientacoes'] for x in o['grupos'] if x['id'] == destino)
    assert [o['familia'] for o in grupo['copiar_de']] == [origem]
    textos = {el['titulo'], el['apoio']}
    navegador.apontar_playwright()
    with ts.ServidorTela(conteudo, pasta=job, modo_teste=True,
                         atos=ta.atos_do_job(job, conteudo=conteudo)) as srv, sync_playwright() as pw:
        nav, pg = tf._pagina(pw, srv)
        try:
            tf._abrir_familia(pg, conteudo['estado'], destino)
            # antes da copia, o DA escolhe a segunda versao e mexe na assinatura
            pg.evaluate('() => document.querySelectorAll("#variantes [role=tab]")[1].click()')
            tted._esperar_salvo(pg)
            escolhida = pg.evaluate(JS_GALERIA)[1][0]
            _mover(pg, el['assinatura'])
            antes = _escolhas(_familia(job, destino))
            assert antes[0] == escolhida and antes[1]
            # o botao, com a origem pelo nome do arquivo e sem porcentagem
            opcoes = pg.evaluate('''() => Array.from(document.querySelectorAll(
                "#cabecalho-familia .copiar-layout [data-ato=familia_copiar]")).map(b => b.textContent)''')
            assert opcoes == ['Copiar do 1080x1920']
            # Cancelar nao grava nada
            janela = _abrir_copiar(pg)
            assert janela['titulo'] == 'Copiar o layout de outra família' and janela['sim'] == 'Copiar'
            assert janela['texto'].startswith('O 1080x1350 passa a partir do layout que o 1080x1920 tem agora')
            assert 'As edições e as quebras de linha que você fez nesta família saem.' in janela['texto']
            assert '% do tamanho que tem no 1080x1920.' in janela['texto']
            _responder(pg, 'nao')
            assert _escolhas(_familia(job, destino)) == antes and 'copiado_de' not in _familia(job, destino)
            # Copiar grava pelo ato; a familia volta com o layout copiado
            _abrir_copiar(pg)
            _responder(pg, 'sim')
            tp._esperar(pg, JS_COM_A_COPIA)
            f = _familia(job, destino)
            assert f['copiado_de']['familia'] == origem and f['copiado_de']['antes'] == {
                'versao': antes[0], 'edicoes': antes[1], 'quebras': antes[2]}
            copia = _escolhas(f)
            vista = pg.evaluate(JS_VISTA)
            assert 'O layout deste arquivo veio do 1080x1920.' in vista['cabecalho']
            assert vista['selo'] == 'O layout deste arquivo veio do 1080x1920.'
            assert vista['resumo'].startswith('Layout copiado do 1080x1920.')
            assert vista['mensagem'] == ('O layout do 1080x1920 foi copiado para o 1080x1350. Ajuste no palco o que '
                                         'precisar e confirme a família.')
            assert vista['nota'].startswith('Este arquivo segue o layout copiado do 1080x1920.')
            # o palco e a previa gravada do destino (a conta do Salvar)
            esperada = conteudo['editar']({'familia': destino, 'versao': copia[0], 'edicoes': copia[1],
                                           'quebras': copia[2]}, antes=copia[1])
            m = next(x for x in esperada['membros'] if x['formato'] == 'v1080x1350')
            _confere_palco(_caixas_paradas(pg), tfd._caixas_previa(m), textos)
            # a galeria travada: o clique numa versao e as setas nao mudam a escolha nem o rascunho
            galeria = pg.evaluate(JS_GALERIA)
            assert all(x[2] == 'true' for x in galeria)
            outra = next(i for i, x in enumerate(galeria) if x[1] != 'true')
            pg.evaluate('i => document.querySelectorAll("#variantes [role=tab]")[i].click()', outra)
            pg.evaluate('''() => document.querySelector('#variantes [role=tab][aria-selected="true"]').focus()''')
            pg.keyboard.press('ArrowDown')
            pg.wait_for_timeout(1500)  # numero-neutro: ms, mais que a espera do rascunho
            assert pg.evaluate(JS_GALERIA) == galeria
            assert _escolhas(_familia(job, destino)) == copia
            assert pg.evaluate('() => document.getElementById("ed-mensagem").textContent').startswith(
                'Este arquivo segue o layout copiado do 1080x1920.')
            # o DA mexe depois da copia: o primeiro Desfazer tira so a edicao dele
            _mover(pg, el['assinatura'])
            assert len(_familia(job, destino)['edicoes']) == len(copia[1]) + 1
            _desfazer(pg)
            assert _escolhas(_familia(job, destino)) == copia and _familia(job, destino).get('copiado_de')
            # o clique seguinte tira a copia inteira e devolve a familia como estava
            _desfazer(pg)
            tp._esperar(pg, JS_SEM_A_COPIA)
            f = _familia(job, destino)
            assert _escolhas(f) == antes and 'copiado_de' not in f and 'copia_desfeita' not in f
            vista = pg.evaluate(JS_VISTA)
            assert vista['mensagem'] == 'A cópia do layout do 1080x1920 saiu. A família voltou a ser como era antes dela.'
            assert 'veio do' not in vista['cabecalho'] and 'veio do' not in vista['selo']
            galeria = pg.evaluate(JS_GALERIA)
            assert all(x[2] is None for x in galeria)
            assert [x[0] for x in galeria if x[1] == 'true'] == [escolhida]
            # e o Desfazer segue um a um, como antes da copia
            _desfazer(pg)
            assert _escolhas(_familia(job, destino)) == (escolhida, [], [])
            # M5: a copia gravada por outro caminho (as rotas, com a pagina parada) e a pagina que grava a familia de
            # antes dela: o servidor recusa, e a pagina le o rascunho gravado e mostra a copia
            # o biscoito da sessao da pagina (a entrada da tela vale uma vez so)
            biscoito = '; '.join('%s=%s' % (c['name'], c['value']) for c in pg.context.cookies())
            fams = _rascunho(job)['familias']
            vista = {k: dict(zip(('versao', 'edicoes', 'quebras'), _escolhas(fams.get(gid) or {})))
                     for k, gid in (('de', origem), ('para', destino))}
            tfd._ato(srv, biscoito, 'familia_copiar', {'familia': destino, 'de': origem, 'vista': vista})
            copia = _escolhas(_familia(job, destino))
            tted._focar(pg, el['assinatura'])
            pg.keyboard.press('ArrowRight')
            tp._esperar(pg, '() => document.getElementById("ed-mensagem").textContent.indexOf("mudou no Vapt") >= 0 '
                            '? "1" : ""')
            tp._esperar(pg, JS_COM_A_COPIA)
            assert _escolhas(_familia(job, destino)) == copia
            assert pg.evaluate('() => document.getElementById("ed-mensagem").textContent') == ts.MOTIVO_COPIA_MUDOU
            assert pg.evaluate(JS_GALERIA)[0][2] == 'true'
        finally:
            nav.close()


# ------------------------------------------------------------------ KV da diagonal: o Salvar e a derivacao
def _salvar_sem_copia(j, f_o):
    """O briefing salvo antes da copia, pelas rotas da tela (como test_copia_entre_familias_editor, sem a copia): o
    rascunho com a origem (1080x1920) editada, o modo de dados, todas as familias confirmadas e "Salvar e seguir"."""
    conteudo = j['conteudo']
    s = ts.ServidorTela(conteudo, pasta=j['job'], modo_teste=True,
                        atos=ta.atos_do_job(j['job'], conteudo=conteudo)).iniciar()
    try:
        biscoito = tts._entrar(s)
        familias = {gid: tce._f(tfd._versao_limpa(conteudo, gid)) for gid in conteudo['familias']}
        familias[j['gid']['f1080x1920']] = f_o
        corpo = dict({'job_id': s.job_id, 'laudo_sha256': s.laudo_sha256, 'familias': familias},
                     **tfd._passo_2_diagonal(j['funcoes']))
        assert tte._escrever(s, '/api/rascunho', corpo, cookie=biscoito)[0] == 200
        tfd._ato(s, biscoito, 'modo_dados', {'modo': 'c'})
        dados = _rascunho(j['job'])
        for gid, f in dados['familias'].items():
            tfd._ato(s, biscoito, 'familia', {'familia': gid, 'versao': f['versao'], 'edicoes': f['edicoes'],
                                              'quebras': f.get('quebras') or []})
        dados = _rascunho(j['job'])
        vista = {k: dados[k] for k in ('job_id', 'laudo_sha256', 'familias', 'funcoes', 'cobertas', 'design',
                                       'design_camadas') if k in dados}
        tfd._ato(s, biscoito, 'salvar', {'rascunho': vista})
    finally:
        s.parar()


def test_copiar_na_pagina_o_salvar_e_o_palco_igual_a_derivacao(tmp_path):
    from playwright.sync_api import sync_playwright

    from vapt.chromium import navegador
    j = tce._criar(tmp_path)
    # o 300x600 juntado de volta ao 1080x1920 (decisao 208), como em test_tela_familia_0100 (com ele separado pelo
    # tamanho, a situacao do briefing na tela tambem diz "salvo": test_copia_entre_familias_tela,
    # test_briefing_salvo_com_a_familia_separada_pelo_tamanho)
    j['conteudo'] = tfd._com_os_pequenos_juntados(j['job'], j['conteudo'])
    j['gid'] = {fid: tfd._familia_de(j['conteudo'], fid) for fid, _w, _h in tce.FORMATOS}
    _salvar_sem_copia(j, tce._f(edicoes=tce._edicoes_o(j['el']), quebras=tce._quebras_o(j)))
    # a tela aberta de novo, com o briefing salvo
    j['conteudo'] = te.montar(j['job'])
    j['gid'] = {fid: tfd._familia_de(j['conteudo'], fid) for fid, _w, _h in tce.FORMATOS}
    job, conteudo, g, el = j['job'], j['conteudo'], j['gid'], j['el']
    destino, origem = g['f1080x1350'], g['f1080x1920']
    assert conteudo['estado']['briefing']['salvo'] is True
    textos = {el['titulo'], el['texto']}
    navegador.apontar_playwright()
    with ts.ServidorTela(conteudo, pasta=job, modo_teste=True,
                         atos=ta.atos_do_job(job, conteudo=conteudo)) as srv, sync_playwright() as pw:
        nav, pg = tf._pagina(pw, srv)
        try:
            tf._abrir_familia(pg, conteudo['estado'], destino)
            # decisao 212: com o briefing salvo, o botao fica apagado; abrir e cancelar a janela nao muda nada
            assert pg.evaluate(JS_VISTA)['salvar'] == [SALVO, True]
            antes = _rascunho(job)
            _abrir_copiar(pg)
            _responder(pg, 'nao')
            pg.wait_for_timeout(1500)  # numero-neutro: ms, mais que a espera do rascunho
            assert pg.evaluate(JS_VISTA)['salvar'] == [SALVO, True]
            assert _rascunho(job)['familias'] == antes['familias']
            # a copia liga o "Salvar e seguir" de novo (a familia pede a confirmacao)
            janela = _abrir_copiar(pg)
            assert 'Esta família pede a sua confirmação de novo.' in janela['texto']
            _responder(pg, 'sim')
            tp._esperar(pg, JS_COM_A_COPIA)
            assert pg.evaluate(JS_VISTA)['salvar'][0] == SALVAR
            caixas = _caixas_paradas(pg)
            copia = _escolhas(_familia(job, destino))
            esperada = conteudo['editar']({'familia': destino, 'versao': copia[0], 'edicoes': copia[1],
                                           'quebras': copia[2]}, antes=copia[1])
            m = next(x for x in esperada['membros'] if x['formato'] == 'f1080x1350')
            _confere_palco(caixas, tfd._caixas_previa(m), textos)
            # confirmar a familia e "Salvar e seguir" pela pagina
            pg.evaluate('() => document.getElementById("confirmar-familia").click()')
            tp._esperar(pg, '() => document.getElementById("confirmacao").open ? "1" : ""')
            _responder(pg, 'sim')
            assert _familia(job, destino)['confirmada'] is True
            tp._esperar(pg, '() => document.getElementById("salvar-seguir").disabled ? "" : "1"')
            pg.evaluate('() => document.getElementById("salvar-seguir").click()')
            tp._esperar(pg, '() => document.getElementById("confirmacao").open ? "1" : ""')
            pg.evaluate('() => document.querySelector("#confirmacao [data-resposta=sim]").click()')
            tp._esperar(pg, '() => document.getElementById("salvar-seguir").textContent', SALVO, teto_s=600)
        finally:
            nav.close()
    # o palco que o DA viu e a derivacao gravada do destino
    d = contratos.ler(job / nd.PASTA / 'f1080x1350.json', nd.ESQUEMA)
    _confere_palco(caixas, tfd._caixas_gravadas(d), textos)
    reg = next(x for x in d['registros'] if x['codigo'] == 'layout_de_outra_familia')
    assert reg['medidas']['familia'] == origem and reg['medidas']['arquivo'] == 'f1080x1920'
    assert _familia(job, destino)['copiado_de']['familia'] == origem


# ------------------------------------------------------------------ revisao da etapa E9: o Desfazer e a trava M5
# o caminho da previa na pagina, desde agora: cada valor que data-previa toma fica numa lista (a previa recusada entre
# um clique e a gravacao aparece nela, mesmo que outra previa venha depois)
JS_OUVIR_PREVIAS = '''() => { window.__previas = [];
  if (window.__ouvinte) window.__ouvinte.disconnect();
  window.__ouvinte = new MutationObserver(() => window.__previas.push(document.documentElement.dataset.previa));
  window.__ouvinte.observe(document.documentElement, {attributes: true, attributeFilter: ["data-previa"]}); }'''
# a previa pedida depois do clique ja voltou (pronta ou recusada), e o rascunho esta gravado
JS_PREVIA_DEPOIS = '''() => { const p = window.__previas; const fim = p[p.length - 1];
  return p.indexOf("pedindo") >= 0 && (fim === "pronta" || fim === "erro") &&
    document.documentElement.dataset.rascunho === "salvo" && document.getElementById("palco").dataset.pronto === "1"
    ? "1" : ""; }'''
# o pedido do ato devagar (ms) ou recusado sem motivo (ms < 0): o clique do DA cabe no meio da conferencia
JS_PEDIR_DEVAGAR = '''ms => { const f = window.__fetch || window.fetch; window.__fetch = f;
  window.fetch = function (u, o) {
    if (String(u).indexOf("/api/ato/pedir") < 0) return f(u, o);
    if (ms < 0) return Promise.resolve(new Response("", {status: 403}));
    return new Promise(r => setTimeout(r, ms)).then(() => f(u, o)); }; }'''
PEDIR_MS = 2500  # numero-neutro: ms, o pedido do ato devagar, mais que a espera do rascunho (500 ms)
# so a proxima gravacao do rascunho chega devagar (ms): uma gravacao seguinte, se sair antes de ela voltar, chega
# primeiro ao servidor (a rede nao garante a ordem de dois pedidos ao mesmo tempo)
JS_RASCUNHO_DEVAGAR = '''ms => { const f = window.fetch; let uma = true;
  window.fetch = function (u, o) {
    if (!uma || String(u).indexOf("/api/rascunho") < 0) return f(u, o);
    uma = false;
    return new Promise(r => setTimeout(r, ms)).then(() => f(u, o)); }; }'''
RASCUNHO_MS = 1500  # numero-neutro: ms, a gravacao do primeiro Desfazer devagar


def _copiar(pg):
    _abrir_copiar(pg)
    _responder(pg, 'sim')
    tp._esperar(pg, JS_COM_A_COPIA)


def _ate(cond, teto_s=20):
    """Espera a condicao do lado do servidor (o rascunho gravado)."""
    import time
    fim = time.monotonic() + teto_s
    while not cond():
        assert time.monotonic() < fim, 'o rascunho gravado nao chegou ao esperado'
        time.sleep(0.1)  # numero-neutro: intervalo do teste


def test_desfazer_da_copia_de_copia_na_pagina_grava_antes_da_previa(tmp_path):
    """A copia de copia (copiar, mexer na origem e copiar de novo): o Desfazer volta a primeira copia sem a previa
    recusada (antes, ela ia antes da gravacao e o servidor a recusava). Dois Desfazer seguidos: o segundo espera a
    gravacao do primeiro e tira a primeira copia, sem a frase de que a copia mudou no Vapt."""
    from playwright.sync_api import sync_playwright

    from vapt.chromium import navegador
    j = _job_deitado(tmp_path)
    job, conteudo, g, el = j['job'], j['conteudo'], j['gid'], j['el']
    destino, origem = g['v1080x1350'], g['v1080x1920']
    navegador.apontar_playwright()
    with ts.ServidorTela(conteudo, pasta=job, modo_teste=True,
                         atos=ta.atos_do_job(job, conteudo=conteudo)) as srv, sync_playwright() as pw:
        nav, pg = tf._pagina(pw, srv)
        try:
            tf._abrir_familia(pg, conteudo['estado'], destino)
            _mover(pg, el['assinatura'])
            a1 = _escolhas(_familia(job, destino))
            _copiar(pg)
            c1 = _familia(job, destino)
            # o DA mexe na origem e copia de novo
            tf._abrir_familia(pg, conteudo['estado'], origem)
            _mover(pg, el['assinatura'])
            tf._abrir_familia(pg, conteudo['estado'], destino)
            _copiar(pg)
            f = _familia(job, destino)
            assert f['copiado_de']['antes'].get('copiado_de') == c1['copiado_de']
            caixas = lambda eds: [e for e in eds if e['acao'] == 'caixa']  # noqa: E731
            assert caixas(f['edicoes']) != caixas(c1['edicoes'])
            # um Desfazer: a familia volta a primeira copia, e a previa dela vem pronta
            pg.evaluate(JS_OUVIR_PREVIAS)
            pg.evaluate('() => document.getElementById("ed-desfazer").click()')
            tp._esperar(pg, JS_PREVIA_DEPOIS)
            assert 'erro' not in pg.evaluate('() => window.__previas')
            f = _familia(job, destino)
            assert _escolhas(f) == _escolhas(c1) and f['copiado_de']['em'] == c1['copiado_de']['em']
            tp._esperar(pg, JS_COM_A_COPIA)
            assert pg.evaluate(JS_VISTA)['mensagem'] == ('A cópia do layout do 1080x1920 saiu. A família voltou a ser '
                                                         'como era antes dela.')
            # copia de novo e dois Desfazer no mesmo instante, com a gravacao do primeiro devagar: o segundo espera o
            # primeiro gravar (sem a espera, a gravacao do segundo chegava antes e o servidor a recusava)
            _copiar(pg)
            assert _familia(job, destino)['copiado_de']['antes'].get('copiado_de')
            pg.evaluate(JS_RASCUNHO_DEVAGAR, RASCUNHO_MS)
            pg.evaluate(JS_OUVIR_PREVIAS)
            pg.evaluate('() => { const b = document.getElementById("ed-desfazer"); b.click(); b.click(); }')
            _ate(lambda: 'copiado_de' not in _familia(job, destino))
            tp._esperar(pg, JS_SEM_A_COPIA)
            tted._esperar_salvo(pg)
            f = _familia(job, destino)
            assert _escolhas(f) == a1 and 'copia_desfeita' not in f
            assert 'erro' not in pg.evaluate('() => window.__previas')
            assert pg.evaluate('() => document.getElementById("ed-mensagem").textContent') != ts.MOTIVO_COPIA_MUDOU
            assert pg.evaluate('() => document.getElementById("aviso-acoes").textContent').find('mudou no Vapt') < 0
        finally:
            nav.close()


def test_edicao_durante_a_conferencia_da_copia_espera_a_janela(tmp_path):
    """M5: a edicao feita enquanto o Vapt confere o pedido da copia nao vai ao rascunho com a janela aberta. Cancelar
    grava a edicao; Copiar faz a copia (antes, o rascunho gravado no meio da conferencia fazia o servidor recusar a
    copia sem frase). O pedido recusado nao deixa a trava presa: a edicao seguinte grava."""
    from playwright.sync_api import sync_playwright

    from vapt.chromium import navegador
    j = _job_deitado(tmp_path)
    job, conteudo, g, el = j['job'], j['conteudo'], j['gid'], j['el']
    destino = g['v1080x1350']
    navegador.apontar_playwright()

    def edicoes():
        # a seta seguida no mesmo elemento soma no mesmo "mover": vale a lista inteira, nao a contagem
        return _familia(job, destino).get('edicoes') or []

    def mover_no_meio():
        tted._focar(pg, el['assinatura'])
        pg.keyboard.press('ArrowRight')
        pg.wait_for_timeout(1200)  # numero-neutro: ms, mais que a espera do rascunho e menos que PEDIR_MS

    with ts.ServidorTela(conteudo, pasta=job, modo_teste=True,
                         atos=ta.atos_do_job(job, conteudo=conteudo)) as srv, sync_playwright() as pw:
        nav, pg = tf._pagina(pw, srv)
        try:
            tf._abrir_familia(pg, conteudo['estado'], destino)
            # o pedido recusado: a trava sai, e a edicao seguinte grava
            pg.evaluate(JS_PEDIR_DEVAGAR, -1)
            pg.evaluate('() => document.querySelector("#cabecalho-familia .copiar-layout").open = true')
            pg.evaluate('() => document.querySelector(\'#cabecalho-familia .copiar-layout '
                        '[data-ato="familia_copiar"]\').click()')
            tp._esperar(pg, '() => document.documentElement.dataset.estadoAto', 'erro')
            antes = edicoes()
            _mover(pg, el['assinatura'])
            assert edicoes() != antes
            # o pedido devagar: a edicao no meio da conferencia espera a janela, e Cancelar a grava
            pg.evaluate(JS_PEDIR_DEVAGAR, PEDIR_MS)
            pg.evaluate('() => document.querySelector("#cabecalho-familia .copiar-layout").open = true')
            pg.evaluate('() => document.querySelector(\'#cabecalho-familia .copiar-layout '
                        '[data-ato="familia_copiar"]\').click()')
            antes = edicoes()
            mover_no_meio()
            assert edicoes() == antes
            tp._esperar(pg, '() => document.getElementById("confirmacao").open ? "1" : ""')
            _responder(pg, 'nao')
            _ate(lambda: edicoes() != antes)
            tted._esperar_salvo(pg)
            # de novo, agora com Copiar: a copia passa, e a edicao do meio (de antes dela) sai
            pg.evaluate('() => document.querySelector("#cabecalho-familia .copiar-layout").open = true')
            pg.evaluate('() => document.querySelector(\'#cabecalho-familia .copiar-layout '
                        '[data-ato="familia_copiar"]\').click()')
            antes = edicoes()
            mover_no_meio()
            assert edicoes() == antes
            tp._esperar(pg, '() => document.getElementById("confirmacao").open ? "1" : ""')
            _responder(pg, 'sim')
            tp._esperar(pg, JS_COM_A_COPIA)
            f = _familia(job, destino)
            assert f.get('copiado_de') and f['edicoes'][-1]['acao'] == 'caixa'
            pg.wait_for_timeout(1500)  # numero-neutro: ms, mais que a espera do rascunho
            assert _familia(job, destino) == f
        finally:
            nav.close()


# ------------------------------------------------------------------ revisao 2 da 215: os consertos da pagina
JS_AVISO = '() => document.getElementById("aviso-familia").textContent'
FRASE_TROCADO = 'saiu dela'  # a frase do arquivo trocado (vapt.tela.estado.frase_do_arquivo_trocado)
FRASE_MUDOU = 'ficou diferente do que você confirmou'  # a do layout mudado (tela.js, avisoDoLayoutMudado)
JS_DOIS_AVISOS = ('() => { const t = document.getElementById("aviso-familia").textContent; return t.indexOf("%s") >= 0'
                  ' && t.indexOf("%s") >= 0 ? "1" : ""; }' % (FRASE_TROCADO, FRASE_MUDOU))
# so a proxima gravacao do rascunho falha (500): a tentativa sozinha seguinte grava
JS_RASCUNHO_FALHA_UMA = '''() => { const f = window.fetch; let uma = true;
  window.fetch = function (u, o) {
    if (!uma || String(u).indexOf("/api/rascunho") < 0 || !o || o.method !== "POST") return f(u, o);
    uma = false;
    return Promise.resolve(new Response("", {status: 500})); }; }'''
MSG_DESFAZER_NAO_SALVO = 'O Desfazer anterior ainda não foi salvo. Espere o Vapt salvar e desfaça de novo.'


def test_desfazer_da_copia_devolve_os_avisos_sem_abrir_a_tela_de_novo(tmp_path):
    """O Desfazer da copia devolve os avisos de layout mudado e de arquivo trocado que a familia tinha antes dela: o
    servidor os grava de novo (rascunho._com_a_copia), e a pagina os mostra logo, sem abrir a tela de novo."""
    from playwright.sync_api import sync_playwright

    from vapt.chromium import navegador
    j = _job_deitado(tmp_path)
    job, conteudo, g, el = j['job'], j['conteudo'], j['gid'], j['el']
    destino = g['v1080x1350']
    navegador.apontar_playwright()
    with ts.ServidorTela(conteudo, pasta=job, modo_teste=True,
                         atos=ta.atos_do_job(job, conteudo=conteudo)) as srv, sync_playwright() as pw:
        nav, pg = tf._pagina(pw, srv)
        try:
            tf._abrir_familia(pg, conteudo['estado'], destino)
            _mover(pg, el['assinatura'])
        finally:
            nav.close()
    # os avisos que o servidor grava no destino (derrubar_por_layout e _com_a_estrutura)
    dados = _rascunho(job)
    f = dados['familias'][destino]
    f.update(layout_mudou=['v1080x1350'], arquivo_trocado={'de': 'v1080x1920', 'para': 'v1080x1350'},
             confirmada=False)
    contratos.gravar(job / tr.ARQUIVO, dados, tr.ESQUEMA)
    conteudo = te.montar(job)
    with ts.ServidorTela(conteudo, pasta=job, modo_teste=True,
                         atos=ta.atos_do_job(job, conteudo=conteudo)) as srv, sync_playwright() as pw:
        nav, pg = tf._pagina(pw, srv)
        try:
            tf._abrir_familia(pg, conteudo['estado'], destino)
            tp._esperar(pg, JS_DOIS_AVISOS)
            _copiar(pg)
            depois_da_copia = pg.evaluate(JS_AVISO)
            assert FRASE_TROCADO not in depois_da_copia and FRASE_MUDOU not in depois_da_copia
            pg.evaluate('() => document.getElementById("ed-desfazer").click()')
            tp._esperar(pg, JS_SEM_A_COPIA)
            tted._esperar_salvo(pg)
            gravada = _familia(job, destino)
            assert gravada.get('layout_mudou') and gravada.get('arquivo_trocado') and 'copiado_de' not in gravada
            # as duas frases voltam na mesma tela
            tp._esperar(pg, JS_DOIS_AVISOS, teto_s=20)
        finally:
            nav.close()


def test_edicao_na_origem_durante_a_conferencia_fica(tmp_path):
    """A edicao que o DA faz em outra familia (a origem) enquanto o Vapt confere a copia fica: com Copiar, so a
    mudanca do destino era de antes da copia e sai; a da origem vai ao rascunho depois do ato."""
    from playwright.sync_api import sync_playwright

    from vapt.chromium import navegador
    j = _job_deitado(tmp_path)
    job, conteudo, g, el = j['job'], j['conteudo'], j['gid'], j['el']
    destino, origem = g['v1080x1350'], g['v1080x1920']
    navegador.apontar_playwright()
    with ts.ServidorTela(conteudo, pasta=job, modo_teste=True,
                         atos=ta.atos_do_job(job, conteudo=conteudo)) as srv, sync_playwright() as pw:
        nav, pg = tf._pagina(pw, srv)
        try:
            tf._abrir_familia(pg, conteudo['estado'], destino)
            _mover(pg, el['assinatura'])  # o rascunho existe
            antes = _familia(job, origem).get('edicoes') or []
            pg.evaluate(JS_PEDIR_DEVAGAR, 4000)
            pg.evaluate('() => document.querySelector("#cabecalho-familia .copiar-layout").open = true')
            pg.evaluate('() => document.querySelector(\'#cabecalho-familia .copiar-layout '
                        '[data-ato="familia_copiar"]\').click()')
            # enquanto o Vapt confere, o DA vai a origem e mexe nela (a edicao nao e travada)
            tf._abrir_familia(pg, conteudo['estado'], origem)
            tted._focar(pg, el['apoio'])
            pg.keyboard.press('ArrowRight')
            pg.wait_for_timeout(300)
            assert not pg.evaluate('() => document.getElementById("confirmacao").open')
            tp._esperar(pg, '() => document.getElementById("confirmacao").open ? "1" : ""')
            _responder(pg, 'sim')
            tp._esperar(pg, JS_COM_A_COPIA)
            # a edicao da origem chega ao rascunho gravado depois do ato; a copia do destino fica
            _ate(lambda: (_familia(job, origem).get('edicoes') or []) != antes)
            tted._esperar_salvo(pg)
            ed_origem = _familia(job, origem)['edicoes']
            assert ed_origem[-1]['elemento'] == el['apoio'] and ed_origem[-1]['acao'] == 'mover'
            assert _familia(job, destino).get('copiado_de')
        finally:
            nav.close()


def test_segundo_desfazer_espera_a_gravacao_que_falhou(tmp_path):
    """Copia de copia: a gravacao do primeiro Desfazer falha (500). O segundo Desfazer, antes da nova tentativa
    sozinha, e recusado com a frase; a tentativa grava o primeiro, a frase sai, e o Desfazer seguinte tira a primeira
    copia, sem a frase de que a copia mudou no Vapt."""
    from playwright.sync_api import sync_playwright

    from vapt.chromium import navegador
    j = _job_deitado(tmp_path)
    job, conteudo, g, el = j['job'], j['conteudo'], j['gid'], j['el']
    destino, origem = g['v1080x1350'], g['v1080x1920']
    navegador.apontar_playwright()
    msg = '() => document.getElementById("ed-mensagem").textContent'
    with ts.ServidorTela(conteudo, pasta=job, modo_teste=True,
                         atos=ta.atos_do_job(job, conteudo=conteudo)) as srv, sync_playwright() as pw:
        nav, pg = tf._pagina(pw, srv)
        try:
            tf._abrir_familia(pg, conteudo['estado'], destino)
            _mover(pg, el['assinatura'])
            _copiar(pg)
            c1 = _familia(job, destino)['copiado_de']
            tf._abrir_familia(pg, conteudo['estado'], origem)
            _mover(pg, el['assinatura'])
            tf._abrir_familia(pg, conteudo['estado'], destino)
            _copiar(pg)
            assert _familia(job, destino)['copiado_de']['antes'].get('copiado_de') == c1
            pg.evaluate(JS_RASCUNHO_FALHA_UMA)
            pg.evaluate('() => document.getElementById("ed-desfazer").click()')
            tp._esperar(pg, '() => document.documentElement.dataset.rascunho', 'erro')
            # o segundo clique antes da tentativa sozinha: recusado com a frase
            pg.evaluate('() => document.getElementById("ed-desfazer").click()')
            assert pg.evaluate(msg) == MSG_DESFAZER_NAO_SALVO
            # a tentativa sozinha grava o primeiro Desfazer: o servidor fica na primeira copia, e a frase sai
            _ate(lambda: (_familia(job, destino).get('copiado_de') or {}).get('em') == c1['em'])
            tted._esperar_salvo(pg)
            assert _familia(job, destino)['copiado_de'] == c1
            tp._esperar(pg, '() => document.getElementById("ed-mensagem").textContent === "%s" ? "" : "1"'
                        % MSG_DESFAZER_NAO_SALVO)
            # o Desfazer seguinte tira a primeira copia
            _desfazer(pg)
            _ate(lambda: 'copiado_de' not in _familia(job, destino))
            tp._esperar(pg, JS_SEM_A_COPIA)
            assert pg.evaluate(msg) != ts.MOTIVO_COPIA_MUDOU
            assert pg.evaluate('() => document.getElementById("aviso-acoes").textContent').find('mudou no Vapt') < 0
        finally:
            nav.close()


# ------------------------------------------------------------------ revisao 3 da 215: os consertos da pagina
# toda gravacao do rascunho falha (500) enquanto window.__falhar for true
JS_RASCUNHO_FALHA = '''() => { const f = window.fetch; window.__falhar = true;
  window.fetch = function (u, o) {
    if (!window.__falhar || String(u).indexOf("/api/rascunho") < 0 || !o || o.method !== "POST") return f(u, o);
    return Promise.resolve(new Response("", {status: 500})); }; }'''
# o selo quando as tentativas sozinhas param (tela.js, TEXTO_RASCUNHO.erro_parado)
ERRO_PARADO = 'Não foi possível salvar a última escolha. Ela continua na tela. Faça uma mudança para tentar de novo.'
JS_MSG = '() => document.getElementById("ed-mensagem").textContent'
JS_RODAPE = '() => document.getElementById("aviso-acoes").textContent'


def _copia_de_copia(pg, j):
    """Na pagina: a copia c1 no destino, uma edicao na origem e a copia c2 de novo. Devolve (c1, c2) gravados."""
    job, conteudo, g, el = j['job'], j['conteudo'], j['gid'], j['el']
    destino, origem = g['v1080x1350'], g['v1080x1920']
    tf._abrir_familia(pg, conteudo['estado'], destino)
    _mover(pg, el['assinatura'])
    _copiar(pg)
    c1 = _familia(job, destino)['copiado_de']
    tf._abrir_familia(pg, conteudo['estado'], origem)
    _mover(pg, el['assinatura'])
    tf._abrir_familia(pg, conteudo['estado'], destino)
    _copiar(pg)
    c2 = _familia(job, destino)['copiado_de']
    assert c2['em'] != c1['em'] and c2['antes'].get('copiado_de') == c1
    return c1, c2


def test_desfazer_da_copia_com_outra_mudanca_esperando_nao_passa_a_frente(tmp_path):
    """Copia de copia: a gravacao do primeiro Desfazer falha (500). O DA anda um elemento (o rascunho fica pendente,
    com a espera), desfaz a seta e da mais um Desfazer dentro da espera: o clique e recusado com a frase, a gravacao
    em espera leva o primeiro Desfazer, e o servidor termina na primeira copia, sem a frase de copia mudada."""
    from playwright.sync_api import sync_playwright

    from vapt.chromium import navegador
    j = _job_deitado(tmp_path)
    job, conteudo, g, el = j['job'], j['conteudo'], j['gid'], j['el']
    destino = g['v1080x1350']
    navegador.apontar_playwright()
    with ts.ServidorTela(conteudo, pasta=job, modo_teste=True,
                         atos=ta.atos_do_job(job, conteudo=conteudo)) as srv, sync_playwright() as pw:
        nav, pg = tf._pagina(pw, srv)
        try:
            c1, _c2 = _copia_de_copia(pg, j)
            pg.evaluate(JS_RASCUNHO_FALHA_UMA)
            pg.evaluate('() => document.getElementById("ed-desfazer").click()')
            tp._esperar(pg, '() => document.documentElement.dataset.rascunho', 'erro')
            # a seta e, dentro da espera de 500 ms, o Desfazer dela e mais um Desfazer
            tted._focar(pg, el['apoio'])
            pg.keyboard.press('ArrowRight')
            assert pg.evaluate('() => document.documentElement.dataset.rascunho') == 'pendente'
            # a frase lida no mesmo passo dos cliques: a previa pedida pela seta, quando volta, troca a mensagem
            logo = pg.evaluate('() => { const b = document.getElementById("ed-desfazer"); b.click(); b.click(); '
                               'return document.getElementById("ed-mensagem").textContent; }')
            assert logo == MSG_DESFAZER_NAO_SALVO
            # a gravacao em espera leva o primeiro Desfazer: o servidor fica na primeira copia
            _ate(lambda: (_familia(job, destino).get('copiado_de') or {}).get('em') == c1['em'])
            # so o rascunho: a previa da seta, pedida com o servidor ainda na segunda copia, fica recusada ate o
            # Desfazer seguinte (outro assunto, fora deste conserto)
            tp._esperar(pg, '() => document.documentElement.dataset.rascunho', 'salvo')
            pg.wait_for_timeout(1500)
            assert _familia(job, destino)['copiado_de'] == c1
            assert pg.evaluate(JS_MSG) != ts.MOTIVO_COPIA_MUDOU
            assert pg.evaluate(JS_RODAPE).find('mudou no Vapt') < 0
            # o Desfazer seguinte tira a primeira copia
            pg.evaluate('() => document.getElementById("ed-desfazer").click()')
            _ate(lambda: 'copiado_de' not in _familia(job, destino))
            tted._esperar_salvo(pg)
            assert pg.evaluate(JS_MSG) != ts.MOTIVO_COPIA_MUDOU
        finally:
            nav.close()


def test_desfazer_da_copia_com_as_tentativas_paradas_grava_o_anterior(tmp_path):
    """Copia de copia: toda gravacao falha ate as tentativas sozinhas pararem (o selo pede uma mudanca). Com a rede de
    volta, o Desfazer e recusado com a frase de espera e grava o primeiro Desfazer na hora (a frase fica verdadeira);
    o clique seguinte tira a primeira copia, sem a frase de que a copia mudou no Vapt."""
    from playwright.sync_api import sync_playwright

    from vapt.chromium import navegador
    j = _job_deitado(tmp_path)
    job, conteudo, g = j['job'], j['conteudo'], j['gid']
    destino = g['v1080x1350']
    navegador.apontar_playwright()
    with ts.ServidorTela(conteudo, pasta=job, modo_teste=True,
                         atos=ta.atos_do_job(job, conteudo=conteudo)) as srv, sync_playwright() as pw:
        nav, pg = tf._pagina(pw, srv)
        try:
            c1, c2 = _copia_de_copia(pg, j)
            pg.evaluate(JS_RASCUNHO_FALHA)
            pg.evaluate('() => document.getElementById("ed-desfazer").click()')
            # as tentativas sozinhas (1 + 2 + 4 + 8 + 8 s) acabam
            tp._esperar(pg, '() => document.getElementById("selo").textContent', ERRO_PARADO, teto_s=45)
            assert _familia(job, destino)['copiado_de']['em'] == c2['em']
            # a rede volta; o Desfazer e recusado e grava o primeiro Desfazer
            pg.evaluate('() => { window.__falhar = false; }')
            pg.evaluate('() => document.getElementById("ed-desfazer").click()')
            assert pg.evaluate(JS_MSG) == MSG_DESFAZER_NAO_SALVO
            _ate(lambda: (_familia(job, destino).get('copiado_de') or {}).get('em') == c1['em'])
            tted._esperar_salvo(pg)
            tp._esperar(pg, '() => document.getElementById("ed-mensagem").textContent === "%s" ? "" : "1"'
                        % MSG_DESFAZER_NAO_SALVO)
            # o clique seguinte tira a primeira copia
            pg.evaluate('() => document.getElementById("ed-desfazer").click()')
            _ate(lambda: 'copiado_de' not in _familia(job, destino))
            tted._esperar_salvo(pg)
            assert pg.evaluate(JS_MSG).find('mudou') < 0, pg.evaluate(JS_MSG)
            assert pg.evaluate('() => document.documentElement.dataset.rascunho') == 'salvo'
        finally:
            nav.close()


def _pedir_na_origem_e_desfazer_no_destino(pg, conteudo, origem, destino):
    # na origem, o DA pede a copia do destino; enquanto o Vapt confere, ele volta ao destino e desfaz a copia; depois
    # confirma a copia na janela
    tf._abrir_familia(pg, conteudo['estado'], origem)
    pg.evaluate(JS_PEDIR_DEVAGAR, 4000)
    pg.evaluate('() => document.querySelector("#cabecalho-familia .copiar-layout").open = true')
    pg.evaluate('() => document.querySelector(\'#cabecalho-familia .copiar-layout '
                '[data-ato="familia_copiar"]\').click()')
    tf._abrir_familia(pg, conteudo['estado'], destino)
    pg.evaluate('() => document.getElementById("ed-desfazer").click()')
    pg.wait_for_timeout(300)
    assert not pg.evaluate('() => document.getElementById("confirmacao").open')
    tp._esperar(pg, '() => document.getElementById("confirmacao").open ? "1" : ""')
    _responder(pg, 'sim')


def test_desfazer_da_copia_em_outra_familia_durante_a_conferencia_fica_com_o_layout_mudou(tmp_path):
    """O Desfazer da copia numa familia que nao e a do ato, enquanto o Vapt confere o pedido: depois do ato, a familia
    fica com o aviso de layout mudado que o Desfazer devolveu (a pagina e o servidor)."""
    from playwright.sync_api import sync_playwright

    from vapt.chromium import navegador
    j = _job_deitado(tmp_path)
    job, conteudo, g, el = j['job'], j['conteudo'], j['gid'], j['el']
    destino, origem = g['v1080x1350'], g['v1080x1920']
    navegador.apontar_playwright()
    with ts.ServidorTela(conteudo, pasta=job, modo_teste=True,
                         atos=ta.atos_do_job(job, conteudo=conteudo)) as srv, sync_playwright() as pw:
        nav, pg = tf._pagina(pw, srv)
        try:
            tf._abrir_familia(pg, conteudo['estado'], destino)
            _mover(pg, el['assinatura'])
        finally:
            nav.close()
    dados = _rascunho(job)
    dados['familias'][destino].update(layout_mudou=['v1080x1350'], confirmada=False)
    contratos.gravar(job / tr.ARQUIVO, dados, tr.ESQUEMA)
    conteudo = te.montar(job)
    with ts.ServidorTela(conteudo, pasta=job, modo_teste=True,
                         atos=ta.atos_do_job(job, conteudo=conteudo)) as srv, sync_playwright() as pw:
        nav, pg = tf._pagina(pw, srv)
        try:
            tf._abrir_familia(pg, conteudo['estado'], destino)
            tp._esperar(pg, '() => document.getElementById("aviso-familia").textContent.indexOf("%s") >= 0 ? "1" : ""'
                        % FRASE_MUDOU)
            _copiar(pg)
            assert 'copiado_de' in _familia(job, destino)
            _pedir_na_origem_e_desfazer_no_destino(pg, conteudo, origem, destino)
            _ate(lambda: 'copiado_de' not in _familia(job, destino))
            tted._esperar_salvo(pg)
            gravada = _familia(job, destino)
            assert gravada.get('layout_mudou') == ['v1080x1350'] and not gravada.get('confirmada')
            assert _familia(job, origem).get('copiado_de')
            # o DA volta ao destino: a frase do layout mudado continua na familia
            tf._abrir_familia(pg, conteudo['estado'], destino)
            tp._esperar(pg, '() => document.getElementById("aviso-familia").textContent.indexOf("%s") >= 0 ? "1" : ""'
                        % FRASE_MUDOU)
        finally:
            nav.close()


def test_desfazer_da_copia_de_copia_em_outra_familia_durante_a_conferencia_fica_na_primeira(tmp_path):
    """Copia de copia: o Desfazer no destino enquanto o Vapt confere a copia pedida na origem. Depois do ato, a pagina
    fica com a primeira copia (o servidor tambem), e o Desfazer seguinte a tira."""
    from playwright.sync_api import sync_playwright

    from vapt.chromium import navegador
    j = _job_deitado(tmp_path)
    job, conteudo, g = j['job'], j['conteudo'], j['gid']
    destino, origem = g['v1080x1350'], g['v1080x1920']
    navegador.apontar_playwright()
    with ts.ServidorTela(conteudo, pasta=job, modo_teste=True,
                         atos=ta.atos_do_job(job, conteudo=conteudo)) as srv, sync_playwright() as pw:
        nav, pg = tf._pagina(pw, srv)
        try:
            c1, _c2 = _copia_de_copia(pg, j)
            _pedir_na_origem_e_desfazer_no_destino(pg, conteudo, origem, destino)
            _ate(lambda: (_familia(job, destino).get('copiado_de') or {}).get('em') == c1['em'])
            tted._esperar_salvo(pg)
            # o DA volta ao destino e desfaz de novo: sai a primeira copia (a pagina tinha a c1, nao a c2)
            tf._abrir_familia(pg, conteudo['estado'], destino)
            pg.wait_for_timeout(1000)
            pg.evaluate('() => document.getElementById("ed-desfazer").click()')
            _ate(lambda: 'copiado_de' not in _familia(job, destino))
            tted._esperar_salvo(pg)
            assert pg.evaluate(JS_MSG) != ts.MOTIVO_COPIA_MUDOU
        finally:
            nav.close()
