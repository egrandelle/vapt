# -*- coding: utf-8 -*-
"""Decisao 215, etapas E7 e E8: o rascunho, os atos e o estado da tela da copia do layout de outra familia.

  - rascunho._com_a_copia (M5 e resposta 2 do Duda): a pagina nunca cria nem muda uma caixa; o POST atrasado com a
    familia de antes da copia, ou sem a familia, e recusado ('copia'); o Desfazer da copia (copia_desfeita igual ao
    copiado_de.em) volta a familia de antes, com o copiado_de de antes quando havia; copia_desfeita nunca e gravado; o
    copiado_de que a pagina manda e jogado fora;
  - rascunho.copiar_layout: consome o Disparo; 'antes' diferente do gravado da ErroRascunho('mudou'); a confirmacao
    cai; saem cedidos, arquivo_trocado e layout_mudou; a outra familia com o formato ganha cedidos; o esquema vale;
  - o ato familia_copiar pelas rotas da tela: valido, a janela, o executar que grava, a Recusa com a frase de cada
    motivo, o POST velho da pagina recusado com a frase, e o Desfazer;
  - o texto da janela (respostas 1, 2 e 6 do Duda) e o do ato familia com a copia valendo;
  - o estado: copiar_de e a orientacao de cada familia, copiar, a origem menor e a frase da copia sem efeito;
  - humano.ATOS_DA_TELA com o comando novo.
Tudo sintetico: o KV da diagonal (sinteticos.kv_diagonal), numa pasta temporaria; nenhum job real.
"""
import copy
import json

import pytest

import test_copia_entre_familias_editor as tce
import test_tela_escrita as tte
import test_tela_servidor as tts
from vapt import contratos, humano
from vapt.tela import atos as ta
from vapt.tela import edicao
from vapt.tela import estado as te
from vapt.tela import rascunho as tr
from vapt.tela import servidor as ts


# ------------------------------------------------------------------ _com_a_copia (sem job)
def _cx(eid, x0=0.1):
    return {'elemento': eid, 'acao': 'caixa', 'arquivo': 'f1080x1350', 'medida': [1080.0, 1350.0],
            'caixa': [x0, 0.1, 0.5, 0.5], 'doc': [0.0, 0.0, 10.0, 10.0],
            'sangra': {'esq': False, 'topo': False, 'dir': False, 'base': False}}


ANTES = {'versao': None, 'edicoes': [{'elemento': 'el1', 'acao': 'mover', 'dx': 0.01, 'dy': 0}], 'quebras': []}
COPIA = [{'elemento': 'el2', 'acao': 'apagar'}, _cx('el1'), _cx('el3')]


def _gravada(edicoes=COPIA, em='2026-11-26T10:00:00', antes=ANTES):
    return {'versao': None, 'confirmada': False, 'edicoes': list(edicoes),
            'copiado_de': {'familia': 'vertical-1', 'arquivo': 'f1080x1920', 'para': 'f1080x1350', 's': 0.8,
                           'situacao': 'ajustado', 'em': em, 'antes': copy.deepcopy(antes)}}


def _pagina(edicoes, **extra):
    return dict({'versao': None, 'confirmada': False, 'edicoes': list(edicoes)}, **extra)


def test_com_a_copia_mantem_o_copiado_de_e_joga_fora_o_da_pagina():
    g = {'vertical-2': _gravada()}
    forjado = dict(g['vertical-2']['copiado_de'], s=1.0)
    for f in (_pagina(COPIA), _pagina(COPIA, copiado_de=forjado),
              _pagina(COPIA + [{'elemento': 'el1', 'acao': 'mover', 'dx': 0.02, 'dy': 0}])):
        saida = tr._com_a_copia({'vertical-2': f}, g)
        assert saida['vertical-2']['copiado_de'] == g['vertical-2']['copiado_de']
    # a familia sem copia fica como esta, e sem copiado_de
    saida = tr._com_a_copia({'vertical-3': _pagina([], copiado_de=forjado)}, {})
    assert saida == {'vertical-3': _pagina([])}


@pytest.mark.parametrize('pagina', [
    'caixa_nova', 'caixa_mudada', 'sem_caixas', 'sem_familia', 'desfeita_com_caixa'])
def test_com_a_copia_recusa_a_caixa_da_pagina(pagina):
    g = {'vertical-2': _gravada()}
    em = g['vertical-2']['copiado_de']['em']
    familias = {
        'caixa_nova': {'vertical-2': _pagina(COPIA + [_cx('el4')])},
        'caixa_mudada': {'vertical-2': _pagina(COPIA[:2] + [_cx('el3', x0=0.2)])},
        # o POST atrasado da pagina, com a familia de antes da copia
        'sem_caixas': {'vertical-2': _pagina(ANTES['edicoes'])},
        'sem_familia': {'vertical-3': _pagina([])},
        # o Desfazer da copia com as caixas dela ainda la
        'desfeita_com_caixa': {'vertical-2': _pagina(COPIA, copia_desfeita=em)},
    }[pagina]
    with pytest.raises(tr.ErroRascunho) as e:
        tr._com_a_copia(familias, g)
    assert e.value.motivo == 'copia'
    # a familia sem copia gravada tambem nao recebe caixa da pagina
    with pytest.raises(tr.ErroRascunho):
        tr._com_a_copia({'vertical-3': _pagina([_cx('el1')])}, {})


def test_com_a_copia_o_desfazer_volta_a_familia_de_antes():
    g = {'vertical-2': _gravada()}
    em = g['vertical-2']['copiado_de']['em']
    saida = tr._com_a_copia({'vertical-2': _pagina(ANTES['edicoes'], copia_desfeita=em)}, g)
    assert saida['vertical-2'] == _pagina(ANTES['edicoes'])
    # a gravacao repetida da pagina depois do Desfazer (copia_desfeita velho) passa, e o campo nunca fica
    depois = {'vertical-2': dict(saida['vertical-2'])}
    saida = tr._com_a_copia({'vertical-2': _pagina(ANTES['edicoes'], copia_desfeita=em)}, depois)
    assert saida['vertical-2'] == _pagina(ANTES['edicoes'])
    # copia de copia: o Desfazer volta a copia de antes, com as caixas e o copiado_de dela
    velha = _gravada(edicoes=[_cx('el1', x0=0.3)], em='2026-11-26T09:00:00')
    antes2 = {'versao': None, 'edicoes': velha['edicoes'], 'quebras': [], 'copiado_de': velha['copiado_de']}
    g = {'vertical-2': _gravada(antes=antes2)}
    saida = tr._com_a_copia({'vertical-2': _pagina(velha['edicoes'], copia_desfeita=em)}, g)
    assert saida['vertical-2']['copiado_de'] == velha['copiado_de']
    assert 'copia_desfeita' not in saida['vertical-2']
    # o Desfazer de outra copia (em diferente) nao desfaz esta
    with pytest.raises(tr.ErroRascunho):
        tr._com_a_copia({'vertical-2': _pagina(velha['edicoes'], copia_desfeita='2026-11-26T08:00:00')}, g)


def test_com_a_copia_o_desfazer_devolve_o_arquivo_trocado_e_o_layout_mudou():
    # a copia tirou os avisos da familia (copiar_layout); o Desfazer os devolve, como estavam antes (nada calado)
    trocado, mudou = {'de': 'f300x600', 'para': 'f1080x1350'}, ['f1080x1350']
    antes = dict(ANTES, arquivo_trocado=trocado, layout_mudou=mudou)
    g = {'vertical-2': _gravada(antes=antes)}
    em = g['vertical-2']['copiado_de']['em']
    saida = tr._com_a_copia({'vertical-2': _pagina(ANTES['edicoes'], copia_desfeita=em)}, g)
    assert saida['vertical-2'] == _pagina(ANTES['edicoes'], arquivo_trocado=trocado, layout_mudou=mudou)
    # sem o Desfazer, nada volta
    saida = tr._com_a_copia({'vertical-2': _pagina(COPIA)}, g)
    assert 'arquivo_trocado' not in saida['vertical-2'] and 'layout_mudou' not in saida['vertical-2']
    # o esquema aceita os dois campos na familia de antes
    prova = {'esquema': tr.ESQUEMA, 'job_id': '0' * 32, 'laudo_sha256': '0' * 64, 'origem': 'rascunho',
             'atualizado_em': '2026-11-26T10:00:00', 'familias': g}
    contratos.validar(prova, tr.ESQUEMA)


def test_humano_tem_o_comando_da_copia():
    assert tr.COMANDO_COPIAR == 'familia copiar layout'
    assert tr.COMANDO_COPIAR in humano.ATOS_DA_TELA and tr.COMANDO_COPIAR not in humano.COMANDOS
    assert 'copiado_de' in tr.CAMPOS_DO_SERVIDOR


# ------------------------------------------------------------------ o job da diagonal
@pytest.fixture(scope='module')
def job(tmp_path_factory):
    return tce._criar(tmp_path_factory.mktemp('copia-215-tela'))


@pytest.fixture
def srv(job):
    (job['job'] / tr.ARQUIVO).unlink(missing_ok=True)
    job['editor']._copias.clear()
    s = ts.ServidorTela(job['conteudo'], pasta=job['job'], modo_teste=True,
                        atos=ta.atos_do_job(job['job'], conteudo=job['conteudo'])).iniciar()
    s.biscoito = tts._entrar(s)
    try:
        yield s
    finally:
        s.parar()
        (job['job'] / tr.ARQUIVO).unlink(missing_ok=True)


def _post(s, familias):
    corpo = {'job_id': s.job_id, 'laudo_sha256': s.laudo_sha256, 'familias': familias}
    codigo, _cab, bruto = tte._escrever(s, '/api/rascunho', corpo, cookie=s.biscoito)
    return codigo, (json.loads(bruto) if bruto else None)


def _pedir(s, nome, dados):
    codigo, _cab, bruto = tte._escrever(s, '/api/ato/pedir', {'ato': nome, 'dados': dados}, cookie=s.biscoito)
    return codigo, (json.loads(bruto) if bruto else None)


def _confirmar(s, pedido):
    codigo, _cab, bruto = tte._escrever(s, '/api/ato/confirmar', {'pedido': pedido, 'resposta': 'confirmar'},
                                        cookie=s.biscoito)
    return codigo, (json.loads(bruto) if bruto else None)


def _rascunho(job):
    return contratos.ler(job['job'] / tr.ARQUIVO, tr.ESQUEMA)


def _vista(f):
    f = f or {}
    return {'versao': f.get('versao'), 'edicoes': f.get('edicoes') or [], 'quebras': f.get('quebras') or []}


def _dados(job, destino, origem):
    fams = _rascunho(job)['familias']
    return {'familia': destino, 'de': origem, 'vista': {'de': _vista(fams.get(origem)), 'para': _vista(fams.get(destino))}}


def _com_o_rascunho(s, job, destino_edicoes=()):
    """O rascunho com a origem (1080x1920) editada e o destino (1080x1350) com as edicoes dadas."""
    g, el = job['gid'], job['el']
    familias = {gid: tce._f() for gid in job['conteudo']['familias']}
    familias[g['f1080x1920']] = tce._f(edicoes=tce._edicoes_o(el), quebras=tce._quebras_o(job))
    familias[g['f1080x1350']] = tce._f(edicoes=list(destino_edicoes))
    assert _post(s, familias)[0] == 200
    return familias


def test_estado_tem_copiar_de_a_orientacao_e_a_copia(job):
    c, g = job['conteudo'], job['gid']
    assert callable(c['copiar'])
    fam = c['familias'][g['f1080x1350']]
    assert fam['orientacao'] == 'vertical'
    assert fam['copiar_de'] == job['editor'].origens_da_copia(g['f1080x1350'], list(g.values()))
    assert c['familias'][g['f1920x1080']]['copiar_de'] == []
    grupos = {x['id']: x for o in c['estado']['orientacoes'] for x in o['grupos']}
    assert all(grupos[gid]['copiar_de'] == c['familias'][gid]['copiar_de'] for gid in c['familias'])


def test_origem_menor_so_do_menor_para_o_maior(srv, job):
    g = job['gid']
    _com_o_rascunho(srv, job)
    menor = job['conteudo']['copiar'](g['f1080x1920'], g['f1080x1350'])
    maior = job['conteudo']['copiar'](g['f1080x1350'], g['f1080x1920'])
    assert 'motivo' not in menor and 'motivo' not in maior
    assert menor['s'] == 1.0 and menor['origem_menor'] is True
    assert maior['s'] < 1.0 and maior['origem_menor'] is False
    # resposta 1 do Duda: do menor para o maior a copia pede ajuste, mesmo sem piso furado
    assert menor['situacao'] == 'pede_ajuste' and menor['copiado_de']['situacao'] == 'pede_ajuste'
    # o corte na borda do encaixe e aviso deste arquivo, nao ajuste para caber
    assert menor['avisos'] and not menor['ajustes']
    codigo, p = _pedir(srv, 'familia_copiar', _dados(job, g['f1080x1920'], g['f1080x1350']))
    assert codigo == 200, p
    assert 'Neste arquivo: ' + ' '.join(menor['avisos']) in p['texto']
    assert 'Para caber, o Vapt fez' not in p['texto'] and 'Tudo ficou' not in p['texto']


def test_copiar_pelo_ato_grava_e_o_desfazer_volta(srv, job):
    g, el = job['gid'], job['el']
    destino, origem = g['f1080x1350'], g['f1080x1920']
    mexida = [{'elemento': el['assinatura'], 'acao': 'mover', 'dx': 0.01, 'dy': 0}]
    _com_o_rascunho(srv, job, mexida)
    # o destino confirmado antes da copia: a janela diz que a confirmacao cai
    codigo, p = _pedir(srv, 'familia', {'familia': destino, 'versao': None, 'edicoes': mexida, 'quebras': []})
    assert codigo == 200 and _confirmar(srv, p['pedido'])[0] == 200
    assert _rascunho(job)['familias'][destino]['confirmada'] is True
    dados = _dados(job, destino, origem)
    codigo, p = _pedir(srv, 'familia_copiar', dados)
    assert codigo == 200, p
    assert p['titulo'] == 'Copiar o layout de outra família' and p['sim'] == 'Copiar'
    assert 'O 1080x1350 passa a partir do layout que o 1080x1920 tem agora' in p['texto']
    assert 'As edições e as quebras de linha que você fez nesta família saem.' in p['texto']
    assert '% do tamanho que tem no 1080x1920' in p['texto']
    assert 'É uma cópia' in p['texto'] and 'Esta família pede a sua confirmação de novo.' in p['texto']
    r = job['conteudo']['copiar'](destino, origem)
    codigo, resp = _confirmar(srv, p['pedido'])
    assert codigo == 200 and resp == {'familia': destino, 'de': origem, 'situacao': r['situacao'],
                                      'mensagem': 'O layout do 1080x1920 foi copiado para o 1080x1350. Ajuste no '
                                                  'palco o que precisar e confirme a família.'}
    f = _rascunho(job)['familias'][destino]
    assert f['edicoes'] == r['edicoes'] and f.get('quebras', []) == r['quebras'] and f['versao'] == r['versao']
    assert f['confirmada'] is False and 'confirmacao' not in f
    c = f['copiado_de']
    assert {k: v for k, v in c.items() if k != 'em'} == {k: v for k, v in r['copiado_de'].items() if k != 'em'}
    assert c['antes'] == {'versao': None, 'edicoes': mexida, 'quebras': []}
    assert f['arquivo_de_edicao'] == 'f1080x1350'
    # o POST atrasado da pagina, com a familia de antes da copia: recusado com a frase, e nada muda
    fams = _rascunho(job)['familias']
    velho = {gid: tce._f(x.get('versao'), x.get('edicoes'), x.get('quebras')) for gid, x in fams.items()}
    velho[destino] = tce._f(edicoes=mexida)
    codigo, corpo = _post(srv, velho)
    assert codigo == 403 and corpo == {'motivo': ts.MOTIVO_COPIA_MUDOU}
    assert _rascunho(job)['familias'][destino] == f
    # a pagina que releu o rascunho grava de novo: o copiado_de que ela manda e jogado fora
    agora = {gid: tce._f(x.get('versao'), x.get('edicoes'), x.get('quebras')) for gid, x in fams.items()}
    agora[destino] = dict(agora[destino], copiado_de=dict(c, s=1.0))
    assert _post(srv, agora)[0] == 200
    assert _rascunho(job)['familias'][destino]['copiado_de'] == c
    # o Desfazer da copia: a pagina manda a familia de antes e copia_desfeita; volta tudo, sem copiado_de
    agora[destino] = dict(tce._f(edicoes=mexida), copia_desfeita=c['em'])
    assert _post(srv, agora)[0] == 200
    f = _rascunho(job)['familias'][destino]
    assert f['edicoes'] == mexida and not f.get('quebras') and 'copiado_de' not in f and 'copia_desfeita' not in f
    # a gravacao repetida, ainda com copia_desfeita, passa
    assert _post(srv, agora)[0] == 200


def test_desfazer_devolve_o_aviso_de_arquivo_trocado_que_so_existia_calculado(srv, job):
    # revisao 2 da 215: o arquivo de edicao gravado saiu da familia (o DA editava no f300x600) e nao houve POST depois:
    # o aviso de arquivo trocado so existia calculado. A copia troca o arquivo de edicao pelo 'para'; o Desfazer
    # devolve as edicoes e tambem o aviso
    g, el = job['gid'], job['el']
    destino, origem = g['f1080x1350'], g['f1080x1920']
    mexida = [{'elemento': el['assinatura'], 'acao': 'mover', 'dx': 0.01, 'dy': 0}]
    _com_o_rascunho(srv, job, mexida)
    dados = _rascunho(job)
    dados['familias'][destino]['arquivo_de_edicao'] = 'f300x600'
    contratos.gravar(job['job'] / tr.ARQUIVO, dados, tr.ESQUEMA)
    grupo = next(x for o in job['conteudo']['estado']['orientacoes'] for x in o['grupos'] if x['id'] == destino)
    aviso = {'de': 'f300x600', 'para': 'f1080x1350'}
    assert te.arquivo_trocado(_rascunho(job)['familias'][destino], grupo) == aviso
    codigo, p = _pedir(srv, 'familia_copiar', _dados(job, destino, origem))
    assert codigo == 200, p
    assert _confirmar(srv, p['pedido'])[0] == 200
    f = _rascunho(job)['familias'][destino]
    assert f['arquivo_de_edicao'] == 'f1080x1350' and f['copiado_de']['antes']['arquivo_trocado'] == aviso
    fams = _rascunho(job)['familias']
    pagina = {gid: tce._f(x.get('versao'), x.get('edicoes'), x.get('quebras')) for gid, x in fams.items()}
    pagina[destino] = dict(tce._f(edicoes=mexida), copia_desfeita=f['copiado_de']['em'])
    assert _post(srv, pagina)[0] == 200
    f = _rascunho(job)['familias'][destino]
    assert f['edicoes'] == mexida and f['arquivo_trocado'] == aviso
    assert te.arquivo_trocado(f, grupo) == aviso


def test_copia_sem_aviso_calculado_nao_guarda_arquivo_trocado(srv, job):
    # o arquivo de edicao gravado ainda esta na familia, ou a familia nao tem edicoes: nada a guardar
    g = job['gid']
    destino, origem = g['f1080x1350'], g['f1080x1920']
    _com_o_rascunho(srv, job)
    dados = _rascunho(job)
    dados['familias'][destino]['arquivo_de_edicao'] = 'f300x600'
    contratos.gravar(job['job'] / tr.ARQUIVO, dados, tr.ESQUEMA)
    codigo, p = _pedir(srv, 'familia_copiar', _dados(job, destino, origem))
    assert codigo == 200 and _confirmar(srv, p['pedido'])[0] == 200
    assert 'arquivo_trocado' not in _rascunho(job)['familias'][destino]['copiado_de']['antes']


def test_ato_familia_diz_o_layout_copiado(srv, job):
    g = job['gid']
    destino, origem = g['f1080x1350'], g['f1080x1920']
    _com_o_rascunho(srv, job)
    codigo, p = _pedir(srv, 'familia_copiar', _dados(job, destino, origem))
    assert codigo == 200 and 'Confira e confirme a família depois.' in p['texto']
    assert _confirmar(srv, p['pedido'])[0] == 200
    f = _rascunho(job)['familias'][destino]
    codigo, p = _pedir(srv, 'familia', {'familia': destino, 'versao': f['versao'], 'edicoes': f['edicoes'],
                                        'quebras': f.get('quebras', [])})
    assert codigo == 200
    assert 'fica confirmado com o layout copiado do 1080x1920, como a tela mostra agora.' in p['texto']
    assert 'na versão' not in p['texto'] and 'com as suas edições' not in p['texto']
    assert _confirmar(srv, p['pedido'])[0] == 200
    assert _rascunho(job)['familias'][destino]['confirmada'] is True


def test_copiar_valido_recusa_o_pedido_torto(srv, job, monkeypatch):
    g = job['gid']
    destino, origem = g['f1080x1350'], g['f1080x1920']
    _com_o_rascunho(srv, job)
    certo = _dados(job, destino, origem)
    tortos = [dict(certo, x=1), {k: v for k, v in certo.items() if k != 'vista'}, dict(certo, familia='nao-existe'),
              dict(certo, de=destino), dict(certo, de=g['f1920x1080']), dict(certo, familia=1),
              dict(certo, vista={'de': certo['vista']['de']}),
              dict(certo, vista=dict(certo['vista'], para=dict(certo['vista']['para'], edicoes=[{'elemento': 'x',
                                                                                                  'acao': 'apagar'}]))),
              dict(certo, vista=dict(certo['vista'], de=dict(certo['vista']['de'], edicoes=[])))]
    for d in tortos:
        assert _pedir(srv, 'familia_copiar', d) == (403, None), d
    # sem a copia (na espera), nada
    monkeypatch.setitem(job['conteudo'], 'copiar', None)
    assert _pedir(srv, 'familia_copiar', certo) == (403, None)


@pytest.mark.parametrize('r, frase', [
    ({'motivo': 'SEM_LAYOUT'}, 'O arquivo de edição da família do 1080x1920 está sem layout agora, e a tela mostra o '
                               'motivo nele. Resolva lá ou copie de outra família.'),
    ({'motivo': 'ESCALA_PEQUENA', 's': 0.3}, 'No 1080x1350, o conteúdo do 1080x1920 ficaria com 30% do tamanho, '
                                             'pequeno demais. Escolha outra família.'),
    ({'motivo': 'FONTE', 'elemento': 'el1', 'nome': 'Chamada', 'texto': 'A fonte não tem o caractere ✓.'},
     'No 1080x1350, Chamada: A fonte não tem o caractere ✓. Nada foi gravado.'),
    ({'motivo': 'ERRO_NA_COPIA', 'detalhe': ['x']}, 'O Vapt não conseguiu montar a cópia no 1080x1350. Nada foi '
                                                    'gravado. Fale com a Trezion.'),
])
def test_copiar_recusa_com_a_frase_e_nada_e_gravado(srv, job, monkeypatch, r, frase):
    g = job['gid']
    destino, origem = g['f1080x1350'], g['f1080x1920']
    _com_o_rascunho(srv, job)
    antes = (job['job'] / tr.ARQUIVO).read_bytes()
    monkeypatch.setitem(job['conteudo'], 'copiar', lambda d, o: r)
    assert _pedir(srv, 'familia_copiar', _dados(job, destino, origem)) == (403, {'motivo': frase})
    assert (job['job'] / tr.ARQUIVO).read_bytes() == antes


def _r(**k):
    base = {'edicoes': [], 'quebras': [], 'versao': None, 'copiado_de': {}, 's': 1.0, 'situacao': 'igual',
            'frases': [], 'ajustes': [], 'avisos': [], 'n_piso': 0, 'falhas_d': [], 'origem_menor': False}
    return dict(base, **k)


def test_texto_da_janela_em_cada_caso(srv, job, monkeypatch):
    g, el = job['gid'], job['el']
    destino, origem = g['f1080x1350'], g['f1080x1920']
    _com_o_rascunho(srv, job)
    ato = ta._atos_da_estrutura(job['job'], job['conteudo'])['familia_copiar']
    d = _dados(job, destino, origem)

    def texto(**k):
        monkeypatch.setitem(job['conteudo'], 'copiar', lambda _d, _o: _r(**k))
        return ato.texto(d)
    t = texto()
    assert 'O conteúdo fica do mesmo tamanho que tem no 1080x1920.' in t and 'Tudo ficou como no 1080x1920.' in t
    assert 'saem' not in t and 'Os outros arquivos' not in t and 'Confira e confirme a família depois.' in t
    # resposta 1 do Duda: do menor para o maior, copia e avisa
    t = texto(origem_menor=True, n_piso=3, situacao='pede_ajuste')
    assert 'O 1080x1920 é menor que o 1080x1350, e o Vapt não aumenta o conteúdo' in t
    assert 'copie dele para o menor' in t and 'mesmo tamanho' not in t
    assert 'No 1080x1350, 3 elementos ficam abaixo do tamanho mínimo deste arquivo.' in t
    assert 'Tudo ficou' not in t
    # do menor para o maior sem piso furado nem aviso: nunca 'Tudo ficou como no ...' (pede ajuste)
    t = texto(origem_menor=True, situacao='pede_ajuste')
    assert 'O 1080x1920 é menor que o 1080x1350' in t and 'Tudo ficou' not in t
    t = texto(n_piso=1)
    assert 'No 1080x1350, um elemento fica abaixo do tamanho mínimo deste arquivo. Aumente no palco se precisar.' in t
    t = texto(s=0.8123, frases=['O título andou 12 px para caber.'], ajustes=['O título andou 12 px para caber.'],
              situacao='ajustado')
    assert 'Para caber, o conteúdo fica com 81% do tamanho que tem no 1080x1920.' in t
    assert 'Para caber, o Vapt fez estes ajustes: O título andou 12 px para caber.' in t and 'Tudo ficou' not in t
    assert 'Neste arquivo:' not in t
    # o aviso do encaixe (o corte na borda) nao e ajuste para caber: fica sob 'Neste arquivo:'
    aviso = 'A forma chega até a borda de baixo neste arquivo e fica cortada ali.'
    t = texto(frases=['O título andou 12 px para caber.', aviso], ajustes=['O título andou 12 px para caber.'],
              avisos=[aviso], situacao='ajustado')
    assert 'Para caber, o Vapt fez estes ajustes: O título andou 12 px para caber. Neste arquivo: ' + aviso in t
    t = texto(frases=[aviso], avisos=[aviso])
    assert 'Neste arquivo: ' + aviso in t and 'Para caber, o Vapt fez' not in t and 'Tudo ficou' not in t
    t = texto(falhas_d=['Um.', 'Dois.', 'Tres.', 'Quatro.', 'Cinco.'], situacao='pede_ajuste')
    assert 'Estes pontos pedem ajuste seu no 1080x1350: Um. Dois. Tres. E mais 2.' in t
    # o destino com edicao e confirmado; a familia com mais arquivos
    mexida = [{'elemento': el['assinatura'], 'acao': 'mover', 'dx': 0.01, 'dy': 0}]
    _com_o_rascunho(srv, job, mexida)
    codigo, p = _pedir(srv, 'familia', {'familia': destino, 'versao': None, 'edicoes': mexida, 'quebras': []})
    assert codigo == 200 and _confirmar(srv, p['pedido'])[0] == 200
    d = _dados(job, destino, origem)
    fams = dict(job['conteudo']['familias'])
    fams[destino] = dict(fams[destino], formatos=list(fams[destino]['formatos']) + ['outro'])
    monkeypatch.setitem(job['conteudo'], 'familias', fams)
    t = texto()
    # o Desfazer devolve as edicoes e as quebras, mas nao a confirmacao
    assert 'As edições e as quebras de linha que você fez nesta família saem. Se mudar de ideia, Desfazer tira a ' \
           'cópia inteira de uma vez e devolve as suas edições e quebras de linha, mas não devolve a confirmação.' in t
    assert 'traz tudo de volta' not in t
    assert 'Os outros arquivos desta família seguem o layout novo do 1080x1350.' in t
    assert t.endswith('Esta família pede a sua confirmação de novo.')


def test_copiar_layout_direto(srv, job):
    g = job['gid']
    destino, origem = g['f1080x1350'], g['f1080x1920']
    _com_o_rascunho(srv, job)
    r = job['conteudo']['copiar'](destino, origem)
    # o destino com os avisos de antes, e outra familia que ainda lista o formato do destino
    dados = _rascunho(job)
    f = dados['familias'][destino]
    # o arquivo de edicao gravado ja saiu da familia (o f300x600): a copia foi feita para o f1080x1350
    f.update(layout_mudou=['f1080x1350'], arquivo_trocado={'de': 'f1080x1920', 'para': 'f1080x1350'},
             cedidos=['f1080x1350'], formatos=['f1080x1350'], arquivo_de_edicao='f300x600')
    dados['familias']['vertical-9'] = {'versao': None, 'confirmada': False, 'edicoes': [],
                                       'formatos': ['f1080x1350', 'f300x600']}
    contratos.gravar(job['job'] / tr.ARQUIVO, dados, tr.ESQUEMA)
    kw = {'job_id': srv.job_id, 'laudo_atual': srv.laudo_sha256, 'formatos': ['f1080x1350'],
          'versao': r['versao'], 'edicoes': r['edicoes'], 'quebras': r['quebras'], 'copiado_de': r['copiado_de']}
    d = humano.exigir_tela(tr.COMANDO_COPIAR, srv._sessao_humana, confirmado=True)
    with pytest.raises(tr.ErroRascunho) as e:
        tr.copiar_layout(job['job'], destino, disparo=d, antes=(None, [{'elemento': 'x', 'acao': 'apagar'}], []), **kw)
    assert e.value.motivo == 'mudou'
    # o Disparo vale um ato so, mesmo o recusado
    with pytest.raises(humano.ErroHumano):
        tr.copiar_layout(job['job'], destino, disparo=d, antes=(None, [], []), **kw)
    d = humano.exigir_tela(tr.COMANDO_COPIAR, srv._sessao_humana, confirmado=True)
    gravada = tr.copiar_layout(job['job'], destino, disparo=d, antes=(None, [], []), **kw)
    assert {'layout_mudou', 'arquivo_trocado', 'cedidos', 'confirmacao'}.isdisjoint(gravada)
    assert gravada['copiado_de'] == r['copiado_de'] and gravada['formatos'] == ['f1080x1350']
    # o arquivo de edicao gravado passa a ser o da copia, nunca o velho que saiu da familia
    assert gravada['arquivo_de_edicao'] == r['copiado_de']['para'] == 'f1080x1350'
    novo = _rascunho(job)  # o esquema vale
    assert novo['familias']['vertical-9']['cedidos'] == ['f1080x1350']
    assert novo['familias'][destino] == gravada


def test_copia_de_copia_no_mesmo_segundo_tem_em_proprio(srv, job):
    # duas copias no mesmo segundo: o em da segunda nunca e igual ao da primeira, e a gravacao repetida do Desfazer
    # da segunda nunca desfaz a primeira
    g = job['gid']
    destino, origem = g['f1080x1350'], g['f1080x1920']
    _com_o_rascunho(srv, job)
    r = job['conteudo']['copiar'](destino, origem)
    kw = {'job_id': srv.job_id, 'laudo_atual': srv.laudo_sha256, 'formatos': ['f1080x1350'],
          'versao': r['versao'], 'edicoes': r['edicoes'], 'quebras': r['quebras']}
    em = '2026-11-26T10:00:00-03:00'
    d = humano.exigir_tela(tr.COMANDO_COPIAR, srv._sessao_humana, confirmado=True)
    c1 = tr.copiar_layout(job['job'], destino, disparo=d, antes=(None, [], []),
                          copiado_de=dict(r['copiado_de'], em=em), **kw)
    assert c1['copiado_de']['em'] == em
    # a segunda copia, com a primeira na familia de antes e a mesma hora
    antes2 = {'versao': c1['versao'], 'edicoes': c1['edicoes'], 'quebras': c1.get('quebras', []),
              'copiado_de': c1['copiado_de']}
    d = humano.exigir_tela(tr.COMANDO_COPIAR, srv._sessao_humana, confirmado=True)
    c2 = tr.copiar_layout(job['job'], destino, disparo=d,
                          antes=(c1['versao'], c1['edicoes'], c1.get('quebras', [])),
                          copiado_de=dict(r['copiado_de'], em=em, antes=antes2), **kw)
    assert c2['copiado_de']['em'] != em and c2['copiado_de']['em'].startswith(em)
    assert c2['copiado_de']['antes']['copiado_de']['em'] == em
    _rascunho(job)  # o esquema vale
    # o Desfazer da segunda volta a primeira; repetido, continua na primeira
    gravadas = {destino: c2}
    pagina = {destino: dict(tce._f(c1['versao'], c1['edicoes'], c1.get('quebras', [])),
                            copia_desfeita=c2['copiado_de']['em'])}
    saida = tr._com_a_copia(pagina, gravadas)
    assert saida[destino]['copiado_de'] == c1['copiado_de']
    saida2 = tr._com_a_copia(pagina, {destino: dict(saida[destino])})
    assert saida2[destino]['copiado_de'] == c1['copiado_de']


def test_briefing_salvo_com_a_familia_separada_pelo_tamanho(tmp_path):
    # decisao 208: o 300x600 separado pelo tamanho do 1080x1920 (separado_de so a tela ve). Com o briefing salvo pelas
    # rotas e nada mudado, a tela diz "Briefing salvo" (o botao Salvar fica apagado, item 8 do Duda)
    import test_copia_entre_familias_pagina as tcp
    from vapt.briefing import salvar as bs
    j = tce._criar(tmp_path)
    fam = j['conteudo']['familias'][j['gid']['f300x600']]
    assert fam['separado_por_tamanho'] and fam['separado_de'] == j['gid']['f1080x1920']
    tcp._salvar_sem_copia(j, tce._f(edicoes=tce._edicoes_o(j['el']), quebras=tce._quebras_o(j)))
    conteudo = te.montar(j['job'])
    assert conteudo['familias'][j['gid']['f300x600']]['separado_de'] == j['gid']['f1080x1920']
    assert conteudo['estado']['briefing']['salvo'] is True
    familias = {gid: f['formatos'] for gid, f in conteudo['familias'].items()}
    # a conta sem o separado_de da tela nao ve a familia separada pelo tamanho
    assert bs.situacao_na_tela(j['job'], familias)['salvo'] is False
    sep = {gid: f['separado_de'] for gid, f in conteudo['familias'].items()}
    assert bs.situacao_na_tela(j['job'], familias, separado_de=sep)['salvo'] is True


def test_frase_da_copia_sem_efeito():
    grupo = {'composicoes': [{'formatos': [{'id': 'f300x600'}]}], 'arquivo_de_edicao': 'f300x600'}
    fam = {'arquivo_de_edicao': 'f1080x1350', 'edicoes': [_cx('el1')],
           'copiado_de': {'familia': 'vertical-1', 'arquivo': 'f1080x1920', 'para': 'f1080x1350', 's': 0.8,
                          'situacao': 'igual', 'em': '2026-11-26T10:00:00'}}
    t = te.arquivo_trocado(fam, grupo)
    assert t == {'de': 'f1080x1350', 'para': 'f300x600', 'copia': fam['copiado_de']}
    # sem as caixas, a copia ja saiu
    assert 'copia' not in te.arquivo_trocado(dict(fam, edicoes=[{'elemento': 'el1', 'acao': 'apagar'}]), grupo)
    nomes = {'f1080x1350': '1080x1350', 'f300x600': '300x600', 'f1080x1920': '1080x1920'}
    frase = te.frase_do_arquivo_trocado(t['de'], t['para'], nomes, t['copia'])
    assert frase.endswith('O layout copiado do 1080x1920 era do 1080x1350 e deixou de valer aqui, porque o arquivo '
                          'de edição ou a medida mudou. Use Desfazer para tirar a cópia, ou copie de novo.')
    assert te.frase_do_arquivo_trocado(t['de'], t['para'], nomes) == frase.split(' O layout copiado')[0]


def test_tela_montada_de_novo_usa_o_editor_novo(srv, job):
    g = job['gid']
    destino, origem = g['f1080x1350'], g['f1080x1920']
    _com_o_rascunho(srv, job)
    conteudo = dict(job['conteudo'])
    ato = ta._atos_da_estrutura(job['job'], conteudo)['familia_copiar']
    assert ato.validar(_dados(job, destino, origem)) is True
    velho = job['editor']
    assert velho._copias
    conteudo.update(te.montar(job['job']))  # como o servidor faz em _atualizar
    novo = conteudo['editar'].__self__
    assert novo is not velho and not novo._copias
    assert ato.validar(_dados(job, destino, origem)) is True and novo._copias
    assert edicao.caixas_de(conteudo['copiar'](destino, origem)['edicoes'])
