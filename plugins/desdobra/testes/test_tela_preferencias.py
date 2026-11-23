# -*- coding: utf-8 -*-
"""0.13.0: o tema claro ou escuro da tela, lembrado entre sessoes (desdobra.tela.preferencias e o servidor da tela).

Criterios cobertos aqui:
  - o arquivo de preferencias (preferencias-tela/1) fica na pasta de dados do plugin, fora do job, so com o esquema e
    o tema; arquivo que falta, ilegivel ou fora do esquema vale como sem tema, sem erro;
  - com tema guardado, a pagina servida em / leva data-theme="light" ou "dark" no <html>; sem tema, o <html> vai sem
    data-theme (a tela segue o tema do Windows), e o servidor sem arquivo de preferencias nunca grava nada;
  - POST /preferencias aceita so {"tema": "light"} ou {"tema": "dark"}, com as mesmas conferencias das outras escritas
    e um teto de corpo menor; toda recusa e 403 ou 404 sem corpo e nada e gravado; erro do disco nao chega ao DA;
  - o servidor so de leitura aplica o tema guardado, mas nao tem a rota (404);
  - a janela segue o tema do Windows (OPCOES_JANELA, test_tela_janela.py).
Tudo sintetico: o job de mentira de test_tela_escrita e o arquivo de preferencias em tmp_path.
"""
import json
import threading

import pytest

import test_tela_escrita as tte
import test_tela_servidor as tts
from desdobra.tela import preferencias as tp
from desdobra.tela import servidor as ts

LIGHT = b'<html lang="pt-BR" data-theme="light">'
DARK = b'<html lang="pt-BR" data-theme="dark">'
SEM_TEMA = b'<html lang="pt-BR">'


@pytest.fixture
def job(tmp_path):
    j = tmp_path / 'job'
    (j / 'laudo').mkdir(parents=True)
    (j / 'laudo' / 'laudo.json').write_text('{"laudo": "sintetico"}', encoding='utf-8')
    return j


@pytest.fixture
def dados_plugin(tmp_path):
    """A pasta de dados do plugin de mentira, separada do job."""
    p = tmp_path / 'dados-plugin'
    p.mkdir()
    return p


def _servidor(job=None, preferencias=None):
    opcoes = {'pasta': job, 'modo_teste': True, 'atos': tte._atos([])} if job is not None else {}
    if preferencias is not None:
        opcoes['preferencias'] = preferencias
    return ts.ServidorTela(tts._conteudo(), **opcoes).iniciar()


def _pagina(s, biscoito):
    codigo, _cab, corpo = tts._pedir(s, '/', cookie=biscoito)
    assert codigo == 200  # numero-neutro: codigo HTTP
    return corpo


def _tema(s, valor, biscoito, **kw):
    return tte._escrever(s, '/preferencias', {'tema': valor}, cookie=biscoito, **kw)


# ------------------------------------------------------------------ o arquivo
def test_arquivo_fica_na_pasta_de_dados_do_plugin(monkeypatch, dados_plugin):
    from desdobra import chromium
    monkeypatch.setattr(chromium, 'pasta_dados_do_plugin', lambda: dados_plugin)
    assert tp.arquivo() == dados_plugin / 'preferencias-tela.json'
    monkeypatch.setattr(chromium, 'pasta_dados_do_plugin', lambda: None)
    assert tp.arquivo() is None


def test_sem_ambiente_do_plugin_nao_ha_arquivo():
    # o .venv do repositorio nao tem interpretador.json na pasta-mae: nos testes, nada e gravado fora do tmp_path
    assert tp.arquivo() is None


def test_ida_e_volta_so_com_esquema_e_tema(dados_plugin):
    arq = dados_plugin / tp.ARQUIVO
    for tema in tp.TEMAS:
        tp.gravar(arq, tema)
        assert tp.ler(arq) == tema
        assert json.loads(arq.read_text(encoding='utf-8')) == {'esquema': 'preferencias-tela/1', 'tema': tema}
    assert sorted(p.name for p in dados_plugin.iterdir()) == [tp.ARQUIVO]  # sem temporario esquecido
    with pytest.raises(ValueError):
        tp.gravar(arq, 'dark')


@pytest.mark.parametrize('conteudo', [None, '', '{', '[]', '"escuro"', '{"tema": "escuro"}',
                                      '{"esquema": "preferencias-tela/1", "tema": "dark"}',
                                      '{"esquema": "preferencias-tela/1", "tema": "escuro", "job_id": "x"}',
                                      '{"esquema": "preferencias-tela/2", "tema": "escuro"}'])
def test_arquivo_que_falta_ou_fora_do_esquema_vale_como_sem_tema(dados_plugin, conteudo):
    arq = dados_plugin / tp.ARQUIVO
    if conteudo is not None:
        arq.write_text(conteudo, encoding='utf-8')
    assert tp.ler(arq) is None
    assert tp.ler(None) is None


def test_arquivo_que_e_pasta_vale_como_sem_tema(dados_plugin):
    (dados_plugin / tp.ARQUIVO).mkdir()
    assert tp.ler(dados_plugin / tp.ARQUIVO) is None


# ------------------------------------------------------------------ a pagina servida
def test_sem_preferencias_a_pagina_vai_sem_data_theme():
    s = _servidor()
    try:
        corpo = _pagina(s, tts._entrar(s))
        assert SEM_TEMA in corpo and b'data-theme' not in corpo and s.tema is None
    finally:
        s.parar()


def test_arquivo_que_falta_nao_poe_data_theme_nem_cria_arquivo(dados_plugin):
    s = _servidor(preferencias=dados_plugin / tp.ARQUIVO)
    try:
        assert b'data-theme' not in _pagina(s, tts._entrar(s))
    finally:
        s.parar()
    assert list(dados_plugin.iterdir()) == []


@pytest.mark.parametrize('tema,tag', [('claro', LIGHT), ('escuro', DARK)])
def test_tema_guardado_vai_no_html_tambem_no_so_de_leitura(dados_plugin, tema, tag):
    arq = dados_plugin / tp.ARQUIVO
    tp.gravar(arq, tema)
    s = _servidor(preferencias=arq)
    try:
        biscoito = tts._entrar(s)
        corpo = _pagina(s, biscoito)
        assert corpo.count(b'data-theme') == 1 and tag in corpo  # numero-neutro: um atributo so
        assert b'<meta name="dsd-csrf" content="">' in corpo
        # o so de leitura le o tema, mas nao tem a rota de gravacao
        assert _tema(s, 'light', biscoito, csrf='x')[0] == 404  # numero-neutro: codigo HTTP
    finally:
        s.parar()
    assert tp.ler(arq) == tema


@pytest.mark.parametrize('tema,valor', [(None, b'light dark'), ('claro', b'light'), ('escuro', b'dark')])
def test_a_meta_do_esquema_de_cores_segue_o_tema_guardado(dados_plugin, tema, valor):
    """A meta color-scheme diz ao Chromium o fundo antes do tela.css: os dois esquemas sem tema, so o guardado com ele."""
    arq = dados_plugin / tp.ARQUIVO
    if tema:
        tp.gravar(arq, tema)
    s = _servidor(preferencias=arq)
    try:
        corpo = _pagina(s, tts._entrar(s))
        assert corpo.count(b'name="color-scheme"') == 1  # numero-neutro: uma meta so
        assert b'<meta name="color-scheme" content="' + valor + b'">' in corpo
    finally:
        s.parar()


def test_o_valor_do_atributo_nunca_vem_do_texto_do_arquivo(dados_plugin):
    arq = dados_plugin / tp.ARQUIVO
    arq.write_text('{"esquema": "preferencias-tela/1", "tema": "escuro\\" onload=\\"x"}', encoding='utf-8')
    s = _servidor(preferencias=arq)
    try:
        corpo = _pagina(s, tts._entrar(s))
        assert b'data-theme' not in corpo and b'onload' not in corpo
    finally:
        s.parar()


def test_a_pagina_de_estaticos_com_data_theme_nao_ganha_outro(dados_plugin):
    arq = dados_plugin / tp.ARQUIVO
    tp.gravar(arq, 'escuro')
    pagina = b'<!doctype html>\n<html lang="pt-BR" data-theme="light">\n<meta name="dsd-csrf" content="">\n'
    conteudo = dict(tts._conteudo(), estaticos={'/': (pagina, 'text/html; charset=utf-8')})
    s = ts.ServidorTela(conteudo, preferencias=arq).iniciar()
    try:
        corpo = _pagina(s, tts._entrar(s))
        assert corpo.count(b'data-theme') == 1  # numero-neutro: um atributo so
    finally:
        s.parar()


# ------------------------------------------------------------------ a gravacao
def test_post_valido_grava_e_a_proxima_janela_abre_com_o_tema(job, dados_plugin):
    arq = dados_plugin / tp.ARQUIVO
    s = _servidor(job, arq)
    try:
        biscoito = tts._entrar(s)
        assert b'data-theme' not in _pagina(s, biscoito)
        codigo, cab, resto = _tema(s, 'dark', biscoito)
        assert codigo == 204 and resto == b''  # numero-neutro: codigo HTTP
        assert cab['content-security-policy'] == [tts.CSP]
        assert tp.ler(arq) == 'escuro' and DARK in _pagina(s, biscoito)
        assert _tema(s, 'light', biscoito)[0] == 204  # numero-neutro: codigo HTTP
        assert tp.ler(arq) == 'claro' and LIGHT in _pagina(s, biscoito)
        assert s.contagem['preferencias'] == 2  # numero-neutro: dois cliques
    finally:
        s.parar()
    # outra janela, com o mesmo arquivo, abre clara
    outro = _servidor(job, arq)
    try:
        assert LIGHT in _pagina(outro, tts._entrar(outro))
    finally:
        outro.parar()
    # nada do tema no job (nem no log de eventos)
    for f in job.rglob('*'):
        if f.is_file():
            texto = f.read_bytes()
            assert b'preferencias' not in texto and b'"dark"' not in texto, f.name


def test_sem_pasta_de_dados_o_tema_fica_so_na_janela(job, tmp_path):
    s = _servidor(job)
    try:
        biscoito = tts._entrar(s)
        assert _tema(s, 'dark', biscoito)[0] == 204  # numero-neutro: codigo HTTP
        assert DARK in _pagina(s, biscoito)
    finally:
        s.parar()
    assert not [p for p in tmp_path.rglob('*') if tp.ARQUIVO in p.name]


def test_erro_do_disco_nao_chega_ao_da(job, dados_plugin, monkeypatch):
    def falhar(caminho, tema):
        raise OSError('disco')
    monkeypatch.setattr(tp, 'gravar', falhar)
    s = _servidor(job, dados_plugin / tp.ARQUIVO)
    try:
        biscoito = tts._entrar(s)
        codigo, _cab, resto = _tema(s, 'dark', biscoito)
        assert codigo == 204 and resto == b''  # numero-neutro: codigo HTTP
        assert DARK in _pagina(s, biscoito) and s.contagem['erro_do_ato'] == 0
    finally:
        s.parar()
    assert list(dados_plugin.iterdir()) == []


def test_cliques_seguidos_em_fios_diferentes_gravam_um_arquivo_valido(job, dados_plugin):
    arq = dados_plugin / tp.ARQUIVO
    s = _servidor(job, arq)
    try:
        biscoito = tts._entrar(s)
        codigos = []

        def clicar(valor):
            codigos.append(_tema(s, valor, biscoito)[0])
        fios = [threading.Thread(target=clicar, args=(('light', 'dark')[i % 2],))  # numero-neutro: alterna os temas
                for i in range(8)]  # numero-neutro: cliques seguidos
        for f in fios:
            f.start()
        for f in fios:
            f.join()
        assert codigos == [204] * len(fios)  # numero-neutro: codigo HTTP
        assert tp.ler(arq) in tp.TEMAS and tp.ler(arq) == s.tema  # a ultima gravacao vence
    finally:
        s.parar()
    assert sorted(p.name for p in dados_plugin.iterdir()) == [tp.ARQUIVO]


# ------------------------------------------------------------------ as recusas
@pytest.mark.parametrize('caso', sorted(tte.RECUSAS))
def test_cada_recusa_de_seguranca_e_403_ou_404_sem_corpo_e_nada_gravado(job, dados_plugin, caso):
    arq = dados_plugin / tp.ARQUIVO
    s = _servidor(job, arq)
    try:
        biscoito = tts._entrar(s)
        kw = dict(tte.RECUSAS[caso])
        corpo = kw.pop('corpo', None)
        dados = None if corpo is not None else {'tema': 'dark'}
        codigo, cab, resto = tte._escrever(s, '/preferencias', dados, cookie=biscoito, corpo=corpo, **kw)
        assert codigo in (403, 404), (caso, codigo)  # numero-neutro: codigos HTTP
        assert resto == b'' and cab['content-length'] == ['0']
        assert s.tema is None and b'data-theme' not in _pagina(s, biscoito)
    finally:
        s.parar()
    assert not arq.exists()


CORPOS_RECUSADOS = {
    'claro_em_portugues': {'tema': 'claro'},
    'escuro_em_portugues': {'tema': 'escuro'},
    'maiuscula': {'tema': 'Dark'},
    'com_espaco': {'tema': 'dark '},
    'vazio': {'tema': ''},
    'nulo': {'tema': None},
    'numero': {'tema': 1},
    'lista': {'tema': ['dark']},
    'campo_a_mais': {'tema': 'dark', 'job_id': 'x'},
    'outro_campo': {'cor': 'dark'},
    'sem_campo': {},
    'so_o_texto': 'dark',
    'lista_no_corpo': ['dark'],
}


@pytest.mark.parametrize('caso', sorted(CORPOS_RECUSADOS))
def test_corpo_fora_do_esquema_e_recusado_sem_gravar(job, dados_plugin, caso):
    arq = dados_plugin / tp.ARQUIVO
    s = _servidor(job, arq)
    try:
        biscoito = tts._entrar(s)
        codigo, _cab, resto = tte._escrever(s, '/preferencias', CORPOS_RECUSADOS[caso], cookie=biscoito)
        assert codigo == 403 and resto == b''  # numero-neutro: codigo HTTP
        assert s.contagem['dado_recusado'] == 1 and s.contagem['preferencias'] == 0  # numero-neutro: uma recusa
        assert s.tema is None
    finally:
        s.parar()
    assert not arq.exists()


def test_corpo_acima_do_teto_do_tema_e_recusado_sem_ler(job, dados_plugin):
    arq = dados_plugin / tp.ARQUIVO
    s = _servidor(job, arq)
    try:
        biscoito = tts._entrar(s)
        valido = json.dumps({'tema': 'dark'}).encode('utf-8')
        grande = valido[:-1] + b' ' * (ts.CORPO_MAX_PREFERENCIAS - len(valido) + 1) + b'}'  # numero-neutro: um byte acima
        assert len(grande) == ts.CORPO_MAX_PREFERENCIAS + 1  # numero-neutro: um byte acima do teto
        codigo, _cab, resto = tte._escrever(s, '/preferencias', cookie=biscoito, corpo=grande)
        assert codigo == 403 and resto == b''  # numero-neutro: codigo HTTP
        assert s.contagem['corpo_recusado'] == 1  # numero-neutro: uma recusa
        assert ts.CORPO_MAX_PREFERENCIAS < s.corpo_max
    finally:
        s.parar()
    assert not arq.exists()


def test_rota_do_tema_so_por_post_e_na_tabela_de_escrita(job, dados_plugin):
    assert ts.ESCRITAS['/preferencias'] == 'preferencias' and 'preferencias' in ts.ROTAS
    assert 'preferencias' not in ts.BLOQUEADAS_NA_TAREFA
    s = _servidor(job, dados_plugin / tp.ARQUIVO)
    try:
        biscoito = tts._entrar(s)
        assert tts._pedir(s, '/preferencias', cookie=biscoito)[0] == 404  # numero-neutro: codigo HTTP
        for rota in ('/preferencias/', '/api/preferencias', '/preferencias?tema=dark', '/api/tema'):
            assert tte._escrever(s, rota, {'tema': 'dark'}, cookie=biscoito)[0] == 404, rota  # numero-neutro: codigo HTTP
    finally:
        s.parar()
    assert list(dados_plugin.iterdir()) == []
