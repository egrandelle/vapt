# -*- coding: utf-8 -*-
"""0.12.0: o controle do alinhamento das linhas do texto no palco (pedido do Duda), no Chromium sem janela.

Criterios cobertos aqui:
  - os tres botoes (a esquerda, ao centro, a direita) ficam depois de Quebrar linha, so com o desenho, com o nome no
    title e no leitor de tela; sem escolha, ficam desligados, e com o texto escolhido o do alinhamento de agora fica
    marcado;
  - um clique grava uma edicao so no rascunho; no palco, a linha mais larga fica no lugar e a curta vai a borda
    direita dela, ou ao meio; a caixa da tinta do texto fica a mesma;
  - Desfazer volta ao KV; os cliques seguidos no mesmo texto ficam numa edicao so, e voltar ao do KV tira a edicao;
  - o grupo desliga os botoes com o motivo; as frases a vista nao tem travessao nem nome de programa; a barra cabe
    nas janelas comuns sem rolagem de lado.
Tudo sintetico: o KV de duas linhas (HH e HHH, a esquerda) e a fonte de autoteste do motor."""
import pytest

import test_render_texto_editado as tre
import test_tela_edicao as ted
import test_tela_galeria as tg
import test_tela_grupo as tgr
import test_tela_palco as tp
from vapt.tela import estado as te

modelo = tre.modelo
job = tre.job
BOTOES = ('ed-tx-esquerda', 'ed-tx-centro', 'ed-tx-direita')
TOL_PX = 1.0  # numero-neutro: px da tela, o arredondamento do desenho
# as linhas do texto escolhido no palco: o retangulo do texto de cada linha (o avanco), em px da tela
JS_LINHAS = '''id => Array.from(document.querySelectorAll('#palco .texto .linha')).filter(l =>
    l.closest('.recorte') && l.closest('.recorte').dataset.elemento === id).map(l => {
  const ts = Array.from(l.querySelectorAll('.trecho')).map(t => t.getBoundingClientRect());
  return [Math.min(...ts.map(r => r.left)), Math.max(...ts.map(r => r.right))]; })'''
JS_PRESSIONADO = '() => %r.filter(i => document.getElementById(i).getAttribute("aria-pressed") === "true")' % (
    list(BOTOES),)


def _linhas(pg, el):
    linhas = pg.evaluate(JS_LINHAS, el)
    if len(linhas) != 2:  # numero-neutro: as duas linhas do KV
        # o texto fica fora do recorte do elemento no palco: as linhas de todos os textos (so ha um)
        linhas = pg.evaluate('''() => Array.from(document.querySelectorAll('#palco .texto .linha')).map(l => {
          const ts = Array.from(l.querySelectorAll('.trecho')).map(t => t.getBoundingClientRect());
          return [Math.min(...ts.map(r => r.left)), Math.max(...ts.map(r => r.right))]; })''')
    assert len(linhas) == 2, linhas  # numero-neutro: as duas linhas do KV
    return linhas


def _clicar(pg, botao):
    pg.evaluate('i => document.getElementById(i).click()', botao)
    ted._esperar_salvo(pg)


def _caixa_tinta(pg):
    return [float(v) for v in pg.evaluate('() => document.querySelector("#palco .texto").dataset.caixaTinta')
            .split(',')]


def test_alinhar_o_texto_na_tela_do_chromium(job, modelo):
    from playwright.sync_api import sync_playwright

    from vapt.chromium import navegador
    from vapt.tela import atos as ta
    from vapt.tela import servidor as ts
    conteudo = te.montar(job)
    gid = tre._familia_de(conteudo, 'mesma')
    el = tre._titulo(conteudo, gid)
    navegador.apontar_playwright()
    with ts.ServidorTela(conteudo, pasta=job, modo_teste=True,
                         atos=ta.atos_do_job(job, conteudo=conteudo)) as srv, sync_playwright() as pw:
        nav, pg = tp._pagina_da_tela(pw, srv, 1600, 900)  # numero-neutro: janela do teste
        try:
            tg._abrir(pg, conteudo['estado'], 'mesma')
            tp._esperar(pg, '() => document.documentElement.dataset.previa === "pronta" ? "1" : ""')
            # sem nada escolhido, os tres botoes ficam desligados, com o nome no title e no leitor de tela
            assert all(pg.evaluate('i => document.getElementById(i).disabled', b) for b in BOTOES)
            nomes = [pg.evaluate('i => [document.getElementById(i).title, document.getElementById(i)'
                                 '.getAttribute("aria-label")]', b) for b in BOTOES]
            assert nomes == [['Alinhar o texto à esquerda'] * 2, ['Alinhar o texto ao centro'] * 2,
                             ['Alinhar o texto à direita'] * 2]
            # o grupo fica depois de Quebrar linha, na mesma linha dos botoes do elemento
            ordem = pg.evaluate('() => Array.from(document.querySelector(".barra-grupo").children).map(n => n.id)')
            assert ordem.index('ed-alinhar-texto') == ordem.index('ed-quebra') + 1
            x, y = tgr._ponto(pg, el)
            pg.mouse.click(x, y)
            tp._esperar(pg, '() => document.getElementById("ed-tx-esquerda").disabled ? "" : "1"')
            assert pg.evaluate(JS_PRESSIONADO) == ['ed-tx-esquerda']
            antes = _linhas(pg, el)
            tinta_antes = _caixa_tinta(pg)
            # no KV, a esquerda: as duas linhas comecam no mesmo x
            assert antes[0][0] == pytest.approx(antes[1][0], abs=TOL_PX)
            # a direita: uma edicao so; a linha mais larga fica no lugar, e a curta termina na borda direita dela
            _clicar(pg, 'ed-tx-direita')
            assert tgr._edicoes(job, gid) == [{'elemento': el, 'acao': 'alinhar_texto', 'alinhamento': 'direita'}]
            depois = _linhas(pg, el)
            assert depois[1] == pytest.approx(antes[1], abs=TOL_PX), (depois, antes)
            assert depois[0][1] == pytest.approx(depois[1][1], abs=TOL_PX), depois
            assert depois[0][1] - depois[0][0] == pytest.approx(antes[0][1] - antes[0][0], abs=TOL_PX)
            assert _caixa_tinta(pg) == pytest.approx(tinta_antes, abs=TOL_PX)
            assert pg.evaluate(JS_PRESSIONADO) == ['ed-tx-direita']
            assert 'à direita' in pg.evaluate('() => document.getElementById("ed-mensagem").textContent')
            # o clique no alinhamento de agora nao grava nada
            pg.evaluate('() => document.getElementById("ed-tx-direita").click()')
            assert 'já está' in pg.evaluate('() => document.getElementById("ed-mensagem").textContent')
            assert len(tgr._edicoes(job, gid)) == 1
            # o clique seguido no mesmo texto fica na mesma edicao: ao centro
            _clicar(pg, 'ed-tx-centro')
            assert tgr._edicoes(job, gid) == [{'elemento': el, 'acao': 'alinhar_texto', 'alinhamento': 'centro'}]
            meio = _linhas(pg, el)
            assert meio[1] == pytest.approx(antes[1], abs=TOL_PX)
            assert (meio[0][0] + meio[0][1]) / 2 == pytest.approx((meio[1][0] + meio[1][1]) / 2, abs=TOL_PX)
            # voltar ao do KV tira a edicao
            _clicar(pg, 'ed-tx-esquerda')
            assert tgr._edicoes(job, gid) == []
            assert 'voltou ao alinhamento do KV' in pg.evaluate(
                '() => document.getElementById("ed-mensagem").textContent')
            assert sum(_linhas(pg, el), []) == pytest.approx(sum(antes, []), abs=TOL_PX)
            # Desfazer volta ao KV
            _clicar(pg, 'ed-tx-direita')
            assert len(tgr._edicoes(job, gid)) == 1
            pg.evaluate('() => document.getElementById("ed-desfazer").click()')
            ted._esperar_salvo(pg)
            assert tgr._edicoes(job, gid) == []
            tp._esperar(pg, '() => document.getElementById("ed-tx-esquerda").getAttribute("aria-pressed") === "true"'
                            ' ? "1" : ""')
            assert sum(_linhas(pg, el), []) == pytest.approx(sum(antes, []), abs=TOL_PX)
            # com o grupo (o texto e o quadrado), os botoes desligam e dizem por que
            outro = next(e['id'] for e in conteudo['editar']({'familia': gid, 'versao': None, 'edicoes': []})
                         ['membros'][0]['palco']['elementos'] if e['funcao'] == 'logo_principal')
            tgr._shift_clique(pg, outro)
            tp._esperar(pg, '() => document.getElementById("ed-tx-esquerda").disabled ? "1" : ""')
            assert pg.evaluate('() => document.getElementById("ed-tx-centro").title') == \
                'Para alinhar o texto, escolha um elemento só.'
            # o logo sozinho nao tem texto para alinhar
            x, y = tgr._ponto(pg, outro)
            pg.mouse.click(x, y)
            tp._esperar(pg, '() => document.getElementById("ed-tx-esquerda").disabled ? "1" : ""')
            assert pg.evaluate('() => document.getElementById("ed-tx-centro").title') == \
                'Este elemento não tem texto para alinhar.'
            texto = pg.evaluate(tp.JS_TEXTO_DA_MOLDURA)
            assert not tp.IDENTIFICADOR.findall(texto), tp.IDENTIFICADOR.findall(texto)
            assert '—' not in texto and '–' not in texto
            # a barra cabe nas janelas comuns, sem rolagem de lado
            for w, h in ((1280, 800), (1366, 768)):  # numero-neutro: as janelas comuns
                pg.set_viewport_size({'width': w, 'height': h})
                assert pg.evaluate('() => document.documentElement.scrollWidth <= '
                                   'document.documentElement.clientWidth'), (w, h)
                assert pg.evaluate('() => { const b = document.getElementById("ed-alinhar-texto")'
                                   '.getBoundingClientRect(); return b.right <= window.innerWidth && b.width > 0; }')
        finally:
            nav.close()
        contagem = dict(srv.contagem)
    assert contagem['proibido'] == 0 and contagem['csrf_recusado'] == 0 and contagem['dado_recusado'] == 0


def test_linha_mais_larga_fica_no_lugar_no_palco_e_o_foco_fica_no_tamanho(job, modelo):
    """Revisao 0.12.0. (1) O palco poe a linha mais larga onde o render a poe: pelo avanco dela, nunca pela borda da
    tinta do bloco. O texto editado HH sobre ' HHH' (a mais larga comeca com um espaco, avanco sem tinta): a esquerda, a
    tinta do bloco comeca no HH; a direita, o HH sai da borda, e a conta pela tinta do bloco levava a linha mais larga
    meio corpo para a esquerda (a mesma diferenca, menor, da folga de cada letra: um texto que comeca com A sobre um
    que comeca com H). (2) O clique no alinhamento que ja vale nao pede previa, e o foco pedido nao fica para a
    proxima: o Tamanho digitado depois continua com o foco."""
    from playwright.sync_api import sync_playwright

    from vapt.chromium import navegador
    from vapt.tela import atos as ta
    from vapt.tela import servidor as ts
    conteudo = te.montar(job)
    gid = tre._familia_de(conteudo, 'mesma')
    el = tre._titulo(conteudo, gid)
    navegador.apontar_playwright()
    with ts.ServidorTela(conteudo, pasta=job, modo_teste=True,
                         atos=ta.atos_do_job(job, conteudo=conteudo)) as srv, sync_playwright() as pw:
        nav, pg = tp._pagina_da_tela(pw, srv, 1600, 900)  # numero-neutro: janela do teste
        try:
            tg._abrir(pg, conteudo['estado'], 'mesma')
            tp._esperar(pg, '() => document.documentElement.dataset.previa === "pronta" ? "1" : ""')
            x, y = tgr._ponto(pg, el)
            pg.mouse.click(x, y)
            tp._esperar(pg, '() => document.getElementById("ed-tx-esquerda").disabled ? "" : "1"')
            # (2) o foco: o Tamanho com Enter fica com o foco; o clique no alinhamento que ja vale nao o tira depois
            pg.evaluate('() => document.getElementById("ed-tx-esquerda").click()')
            assert 'já está' in pg.evaluate('() => document.getElementById("ed-mensagem").textContent')
            pg.fill('#ed-tamanho', '90')
            pg.keyboard.press('Enter')
            ted._esperar_salvo(pg)
            tp._esperar(pg, '() => document.documentElement.dataset.previa === "pronta" ? "1" : ""')
            assert pg.evaluate('() => document.activeElement.id') == 'ed-tamanho'
            pg.evaluate('() => document.getElementById("ed-desfazer").click()')
            ted._esperar_salvo(pg)
            # (1) o texto editado HH sobre ' HHH'
            pg.evaluate('() => document.getElementById("ed-texto").click()')
            pg.fill('#ed-campo-texto', 'HH\n HHH')
            pg.evaluate('() => document.getElementById("ed-texto-aplicar").click()')
            tp._esperar(pg, '() => document.getElementById("editor-texto").hidden ? "1" : ""')
            ted._esperar_salvo(pg)
            tp._esperar(pg, '() => document.documentElement.dataset.previa === "pronta" ? "1" : ""')
            antes = _linhas(pg, el)
            for botao in ('ed-tx-direita', 'ed-tx-centro'):
                _clicar(pg, botao)
                tp._esperar(pg, '() => document.documentElement.dataset.previa === "pronta" ? "1" : ""')
                depois = _linhas(pg, el)
                # a linha mais larga (' HHH') fica no lugar
                assert depois[1] == pytest.approx(antes[1], abs=0.5), (botao, depois, antes)  # numero-neutro: px
                if botao == 'ed-tx-direita':
                    assert depois[0][1] == pytest.approx(depois[1][1], abs=TOL_PX), depois
            assert [e['acao'] for e in tgr._edicoes(job, gid)] == ['texto', 'alinhar_texto']
        finally:
            nav.close()
