# -*- coding: utf-8 -*-
"""Decisao 215, etapa E6: o Editor da tela copia o layout de outra familia (vapt.tela.edicao.Editor).

  - origens_da_copia: as familias da mesma orientacao de onde a familia pode copiar, sem a propria, sem a de mestre
    propria (origem e destino), sem o arquivo devolvido por guarda, sem o formato com spec a confirmar e sem a escala
    abaixo de derivacao.grupo_escala_min; a ordem e estavel;
  - copia_entre_familias: a copia do layout de agora do arquivo de edicao da origem (com mover, escalar, texto,
    alinhamento das linhas, apagar e quebra de linha), conferida contra a derivacao do destino antes de devolver
    (M4); as recusas SEM_LAYOUT, ESCALA_PEQUENA, FONTE e ERRO_NA_COPIA; o copiado_de com a familia de antes (resposta 2
    do Duda: o Desfazer tira a copia inteira);
  - conferir: a previa com caixa diferente das gravadas e recusada; previa_gravada passa;
  - dois fios na previa e na copia ao mesmo tempo;
  - a previa igual ao Salvar: o destino copiado, confirmado e salvo pelas rotas da tela, com a derivacao gravada igual
    ao palco, a origem 'da' nos copiados e o caminho de antes.
Tudo sintetico: o KV da diagonal (sinteticos.kv_diagonal, em pe 1080 x 1920), numa pasta temporaria; nenhum job real.
"""
import copy
import json
import threading

import pytest

import test_familia_diagonal as tfd
from vapt import contratos, limites, plataforma
from vapt.derivacao import nucleo as nd
from vapt.derivacao import proposta
from vapt.tela import edicao
from vapt.tela import estado as te
from vapt.tela import rascunho as tr
from sinteticos import kv_diagonal as KD

PLAT = plataforma.obter()
FORMATOS = [('f1080x1920', 1080, 1920), ('f1080x1350', 1080, 1350), ('f300x600', 300, 600),
            ('f1920x1080', 1920, 1080)]


def _criar(base):
    if PLAT.nome in ('sem-suporte', 'mac'):
        pytest.skip('sem isolador neste sistema')
    j = KD.criar_job(base, FORMATOS)
    j['conteudo'] = te.montar(j['job'])
    j['el'] = {papel: 'el%d' % lid for papel, lid in j['ids'].items()}
    j['editor'] = j['conteudo']['editar'].__self__
    j['gid'] = {fid: tfd._familia_de(j['conteudo'], fid) for fid, _w, _h in FORMATOS}
    return j


@pytest.fixture(scope='module')
def job(tmp_path_factory):
    return _criar(tmp_path_factory.mktemp('copia-215'))


def _irmas(j, fid):
    gid = j['gid'][fid]
    return next([g['id'] for g in o['grupos']] for o in j['conteudo']['estado']['orientacoes']
                if any(g['id'] == gid for g in o['grupos']))


def _edicoes_o(el):
    return [{'elemento': el['assinatura'], 'acao': 'mover', 'dx': -0.02, 'dy': -0.01},
            {'elemento': el['titulo'], 'acao': 'escalar', 'fator': 0.9, 'fx': 0, 'fy': 0},
            {'elemento': el['texto'], 'acao': 'texto', 'texto': 'VOX AH\nHOAX VA AH'},
            {'elemento': el['titulo'], 'acao': 'alinhar_texto', 'alinhamento': 'centro'},
            {'elemento': el['verde'], 'acao': 'apagar'}]


def _quebras_o(j):
    # o titulo 'HOAX\rVA' numa linha so (a quebra de linha da familia do DA)
    return [{'elemento': j['el']['titulo'], 'layer_id': j['ids']['titulo'], 'manter': [], 'inseridas': [],
             'origem': 'da', 'aprovada': True}]


def _f(versao=None, edicoes=(), quebras=()):
    return {'versao': versao, 'confirmada': False, 'edicoes': list(edicoes), 'quebras': list(quebras)}


def _valida_familia(f):
    prova = {'esquema': tr.ESQUEMA, 'job_id': '0' * 32, 'laudo_sha256': '0' * 64, 'origem': 'rascunho',
             'atualizado_em': '2026-11-26T10:00:00', 'familias': {'vertical-1': f}}
    contratos.validar(prova, tr.ESQUEMA)


# ------------------------------------------------------------------ origens_da_copia
def test_origens_da_copia_na_mesma_orientacao_com_a_escala_que_passa(job):
    ed, g = job['editor'], job['gid']
    minimo = float(limites.valor('derivacao.grupo_escala_min'))
    todas = list(g.values())
    o1350 = ed.origens_da_copia(g['f1080x1350'], todas)
    # a outra orientacao e a propria familia ficam de fora; do menor para o maior a copia vale (s = 1, resposta 1)
    assert [x['familia'] for x in o1350] == sorted([g['f1080x1920'], g['f300x600']],
                                                   key=lambda x: ed.arquivo_de_edicao(x))
    assert {x['arquivo'] for x in o1350} == {'f1080x1920', 'f300x600'}
    assert ed.escala_da_copia(g['f300x600'], g['f1080x1350']) == 1.0
    # do 1080x1920 para o 300x600 a escala fica abaixo do minimo: fora
    assert ed.escala_da_copia(g['f1080x1920'], g['f300x600']) < minimo
    assert ed.origens_da_copia(g['f300x600'], todas) == []
    assert ed.origens_da_copia(g['f1920x1080'], todas) == []
    # a ordem e estavel
    assert ed.origens_da_copia(g['f1080x1350'], list(reversed(todas))) == o1350


@pytest.mark.parametrize('mudanca', ['mestre_propria', 'guarda', 'por_confirmar'])
def test_origens_da_copia_sem_mestre_propria_guarda_nem_spec_a_confirmar(job, monkeypatch, mudanca):
    ed, g = job['editor'], job['gid']
    todas = list(g.values())
    d = copy.deepcopy(ed.derivados['f1080x1920'])
    if mudanca == 'mestre_propria':
        d['mestre'] = dict(d.get('mestre') or {}, tipo='propria')
    elif mudanca == 'guarda':
        d.update(situacao='devolvido', devolucao={'motivo': 'formato_sem_folha'})
    else:
        d.update(situacao='devolvido', devolucao={'motivo': nd.MOTIVO_SPEC_POR_CONFIRMAR})
    monkeypatch.setitem(ed.derivados, 'f1080x1920', d)
    # fora como origem e como destino
    assert g['f1080x1920'] not in [x['familia'] for x in ed.origens_da_copia(g['f1080x1350'], todas)]
    assert ed.origens_da_copia(g['f1080x1920'], todas) == []


# ------------------------------------------------------------------ copia_entre_familias
@pytest.fixture(scope='module')
def copia_1920_1350(job):
    ed, g = job['editor'], job['gid']
    f_o = _f(edicoes=_edicoes_o(job['el']), quebras=_quebras_o(job))
    f_d = _f(edicoes=[{'elemento': job['el']['assinatura'], 'acao': 'mover', 'dx': 0.01, 'dy': 0}])
    r = ed.copia_entre_familias(g['f1080x1350'], g['f1080x1920'], f_o, f_d)
    return f_o, f_d, r


def test_copia_do_maior_para_o_menor(job, copia_1920_1350):
    f_o, f_d, r = copia_1920_1350
    el, g = job['el'], job['gid']
    assert 'motivo' not in r, r
    acoes = [e['acao'] for e in r['edicoes']]
    assert acoes[:3] == ['texto', 'alinhar_texto', 'apagar'] and set(acoes[3:]) == {'caixa'}
    assert {e['elemento'] for e in r['edicoes'] if e['acao'] == 'apagar'} == {el['verde']}
    assert {e['elemento'] for e in r['edicoes'] if e.get('do_da')} >= {el['assinatura'], el['titulo'], el['texto']}
    assert all(e['arquivo'] == 'f1080x1350' and e['medida'] == [1080.0, 1350.0]
               for e in r['edicoes'] if e['acao'] == 'caixa')
    # a quebra do titulo vem junto
    assert [q['layer_id'] for q in r['quebras']] == [job['ids']['titulo']]
    assert 0.5 <= r['s'] < 1.0 and r['situacao'] in ('ajustado', 'pede_ajuste')
    c = r['copiado_de']
    assert c['familia'] == g['f1080x1920'] and c['arquivo'] == 'f1080x1920' and c['para'] == 'f1080x1350'
    assert c['s'] == r['s'] and c['situacao'] == r['situacao']
    assert c['quebras'] == [job['ids']['titulo']]
    # a familia de antes, para o Desfazer de um clique (resposta 2 do Duda)
    assert c['antes'] == {'versao': None, 'edicoes': f_d['edicoes'], 'quebras': []}
    _valida_familia(dict(_f(r['versao'], r['edicoes'], r['quebras']), copiado_de=c))
    # o destino com a copia: os copiados, o texto, o alinhamento e o apagado
    p = job['conteudo']['editar']({'familia': g['f1080x1350'], 'versao': r['versao'], 'edicoes': r['edicoes'],
                                   'quebras': r['quebras']}, antes=r['edicoes'])
    assert p is not None and p['copia_sem_efeito'] is None
    assert sorted(p['copiados']) == sorted(e['elemento'] for e in r['edicoes'] if e['acao'] == 'caixa')
    assert [x['elemento'] for x in p['textos_editados']] == [el['texto']]
    assert [x['elemento'] for x in p['apagados']] == [el['verde']]
    assert [x['elemento'] for x in p['alinhamentos_do_da']] == [el['titulo']]
    m = next(x for x in p['membros'] if x['formato'] == 'f1080x1350')
    assert len(m['falhas']) == r['n_piso'] + len(r['falhas_d'])


def test_copia_do_menor_para_o_maior_pede_ajuste(job):
    ed, g = job['editor'], job['gid']
    r = ed.copia_entre_familias(g['f1080x1920'], g['f1080x1350'], _f(edicoes=_edicoes_o(job['el'])[:2]), _f())
    assert 'motivo' not in r, r
    assert r['s'] == 1.0 and r['origem_menor'] is True
    p = job['conteudo']['editar']({'familia': g['f1080x1920'], 'versao': r['versao'], 'edicoes': r['edicoes'],
                                   'quebras': r['quebras']}, antes=r['edicoes'])
    m = next(x for x in p['membros'] if x['formato'] == 'f1080x1920')
    assert r['n_piso'] == sum(1 for f in m['falhas'] if f['codigo'] == 'abaixo_do_piso_da_regra')
    assert r['falhas_d'] == [f['texto'] for f in m['falhas'] if f['codigo'] != 'abaixo_do_piso_da_regra']
    # resposta 1 do Duda: do menor para o maior a copia pede ajuste, com ou sem piso furado
    assert r['situacao'] == 'pede_ajuste' and r['copiado_de']['situacao'] == 'pede_ajuste'
    # do maior para o menor, nunca origem_menor
    assert ed.copia_entre_familias(g['f1080x1350'], g['f1080x1920'], _f(), _f())['origem_menor'] is False


def test_copia_oferecida_do_300x600_para_o_1080x1920_passa_na_conferencia(job):
    # revisao 2 da 215: a fracao da caixa com 7 casas, ampliada pela ida a mestre (a caixa larga do el3), passava de
    # TOL_COPIA e a copia oferecida dava ERRO_NA_COPIA mesmo sem edicao
    ed, g = job['editor'], job['gid']
    destino = g['f1080x1920']
    assert {'familia': g['f300x600'], 'arquivo': 'f300x600'}.items() <= next(
        x for x in job['conteudo']['familias'][destino]['copiar_de'] if x['familia'] == g['f300x600']).items()
    for f_o in (_f(), _f(edicoes=_edicoes_o(job['el'])[:2])):
        r = ed.copia_entre_familias(destino, g['f300x600'], f_o, _f())
        assert r.get('motivo') != 'ERRO_NA_COPIA', r


def test_copia_guarda_na_familia_de_antes_os_avisos_que_tira(job):
    # o Desfazer devolve o aviso de arquivo trocado e o de layout mudado (nada calado)
    ed, g = job['editor'], job['gid']
    trocado, mudou = {'de': 'f300x600', 'para': 'f1080x1350'}, ['f1080x1350']
    f_d = dict(_f(edicoes=[{'elemento': job['el']['assinatura'], 'acao': 'mover', 'dx': 0.01, 'dy': 0}]),
               arquivo_trocado=trocado, layout_mudou=mudou)
    r = ed.copia_entre_familias(g['f1080x1350'], g['f1080x1920'], _f(), f_d)
    assert 'motivo' not in r, r
    antes = r['copiado_de']['antes']
    assert antes['arquivo_trocado'] == trocado and antes['layout_mudou'] == mudou
    _valida_familia(dict(_f(r['versao'], r['edicoes'], r['quebras']), copiado_de=r['copiado_de']))
    # sem os avisos, a familia de antes nao leva os campos
    r = ed.copia_entre_familias(g['f1080x1350'], g['f1080x1920'], _f(), _f())
    assert 'arquivo_trocado' not in r['copiado_de']['antes'] and 'layout_mudou' not in r['copiado_de']['antes']


def test_copia_com_escala_pequena_e_recusada(job):
    ed, g = job['editor'], job['gid']
    r = ed.copia_entre_familias(g['f300x600'], g['f1080x1920'], _f(), _f())
    assert r['motivo'] == 'ESCALA_PEQUENA' and r['s'] < float(limites.valor('derivacao.grupo_escala_min'))


def test_copia_guardada_por_editor_e_refeita_com_outra_origem(job):
    ed, g = job['editor'], job['gid']
    a = ed.copia_entre_familias(g['f1080x1350'], g['f1080x1920'], _f(), _f())
    assert ed.copia_entre_familias(g['f1080x1350'], g['f1080x1920'], _f(), _f()) is a
    b = ed.copia_entre_familias(g['f1080x1350'], g['f1080x1920'], _f(edicoes=_edicoes_o(job['el'])[:1]), _f())
    assert b is not a and b['edicoes'] != a['edicoes']


def test_copia_congelada_o_destino_nao_le_a_origem(job, copia_1920_1350):
    _o, _d, r = copia_1920_1350
    g = job['gid']
    dados = {'familia': g['f1080x1350'], 'versao': r['versao'], 'edicoes': r['edicoes'], 'quebras': r['quebras']}
    h = edicao.hash_dos_layouts(job['conteudo']['editar'](dados, antes=r['edicoes']))
    # a origem muda depois (outra copia dela e calculada): o destino gravado nao muda
    job['editor'].copia_entre_familias(g['f1080x1350'], g['f1080x1920'], _f(edicoes=_edicoes_o(job['el'])[:2]),
                                       _f())
    assert edicao.hash_dos_layouts(job['conteudo']['editar'](dados, antes=r['edicoes'])) == h


def test_conferir_recusa_a_caixa_diferente_da_gravada(job, copia_1920_1350):
    _o, _d, r = copia_1920_1350
    g, editar = job['gid'], job['conteudo']['editar']
    dados = {'familia': g['f1080x1350'], 'versao': r['versao'], 'edicoes': r['edicoes'], 'quebras': r['quebras']}
    assert editar(dados) is None
    assert editar(dados, antes=r['edicoes']) is not None
    assert edicao.previa_gravada(editar, g['f1080x1350'], dados) is not None
    mudada = copy.deepcopy(r['edicoes'])
    k = next(n for n, e in enumerate(mudada) if e['acao'] == 'caixa')
    mudada[k]['caixa'][0] += 0.001
    assert editar(dict(dados, edicoes=mudada), antes=r['edicoes']) is None
    # o DA mexe depois da copia: as caixas sao as mesmas, e a previa passa
    mais = r['edicoes'] + [{'elemento': job['el']['assinatura'], 'acao': 'mover', 'dx': 0.01, 'dy': 0}]
    assert editar(dict(dados, edicoes=mais), antes=r['edicoes']) is not None


def test_recusas_sem_layout_fonte_e_erro_na_copia(job, monkeypatch):
    ed, g = job['editor'], job['gid']
    destino, origem = g['f1080x1350'], g['f1080x1920']
    f_o = _f(edicoes=_edicoes_o(job['el'])[:3])
    # SEM_LAYOUT: o arquivo de edicao da origem sem layout
    real = proposta.layout_da_familia

    def sem_origem(ctx, kv, familia, **kw):
        saida = real(ctx, kv, familia, **kw)
        return {f: None for f in saida} if familia['familia'] == origem else saida
    monkeypatch.setattr(proposta, 'layout_da_familia', sem_origem)
    ed._copias.clear()
    assert ed.copia_entre_familias(destino, origem, f_o, _f()) == {'motivo': 'SEM_LAYOUT'}
    monkeypatch.setattr(proposta, 'layout_da_familia', real)
    # FONTE (214): o texto copiado que a face nao cobre nas linhas do destino
    real_texto = ed._texto
    estado = {'destino': False}
    real_eds = proposta.edicoes_da_copia

    def eds(*a, **k):
        estado['destino'] = True
        return real_eds(*a, **k)

    def texto(eid, t, quebra=None):
        if estado['destino']:
            return None, 'A fonte deste texto não tem o caractere X.'
        return real_texto(eid, t, quebra)
    monkeypatch.setattr(proposta, 'edicoes_da_copia', eds)
    monkeypatch.setattr(ed, '_texto', texto)
    ed._copias.clear()
    r = ed.copia_entre_familias(destino, origem, f_o, _f())
    assert r['motivo'] == 'FONTE' and r['elemento'] == job['el']['texto'] and 'caractere X' in r['texto']
    monkeypatch.setattr(ed, '_texto', real_texto)
    monkeypatch.setattr(proposta, 'edicoes_da_copia', real_eds)
    # ERRO_NA_COPIA (M4): a copia que nao bate com o destino derivado
    real_copia = proposta.copia_entre_familias

    def torta(*a, **k):
        lay_t = real_copia(*a, **k)
        k0 = sorted(lay_t['caixas_visiveis'])[0]
        lay_t['caixas_visiveis'][k0] = [v + 1.0 for v in lay_t['caixas_visiveis'][k0]]
        return lay_t
    monkeypatch.setattr(proposta, 'copia_entre_familias', torta)
    ed._copias.clear()
    r = ed.copia_entre_familias(destino, origem, f_o, _f())
    assert r['motivo'] == 'ERRO_NA_COPIA' and r['detalhe']
    monkeypatch.setattr(proposta, 'copia_entre_familias', real_copia)
    ed._copias.clear()


def test_dois_fios_na_previa_e_na_copia(job):
    ed, g = job['editor'], job['gid']
    dados = {'familia': g['f1080x1920'], 'versao': None, 'edicoes': _edicoes_o(job['el'])[:2], 'quebras': []}
    sozinha = edicao.hash_dos_layouts(job['conteudo']['editar'](dados))
    ed._copias.clear()
    args = (g['f1080x1350'], g['f1080x1920'], _f(edicoes=_edicoes_o(job['el'])[:1]), _f())
    copia_sozinha = ed.copia_entre_familias(*args)
    ed._copias.clear()
    saida, erros = {}, []

    def previa():
        try:
            saida['previa'] = edicao.hash_dos_layouts(job['conteudo']['editar'](dados))
        except Exception as e:  # noqa: BLE001 - o teste conta o erro
            erros.append(e)

    def copiar():
        try:
            saida['copia'] = ed.copia_entre_familias(*args)
        except Exception as e:  # noqa: BLE001 - o teste conta o erro
            erros.append(e)
    fios = [threading.Thread(target=previa), threading.Thread(target=copiar)]
    for f in fios:
        f.start()
    for f in fios:
        f.join()
    assert erros == []
    assert saida['previa'] == sozinha
    assert {k: v for k, v in saida['copia'].items() if k != 'copiado_de'} == \
        {k: v for k, v in copia_sozinha.items() if k != 'copiado_de'}


def test_conteudo_com_o_editor_se_copia_com_trava_nova(job):
    c = copy.deepcopy(job['conteudo'])
    novo = c['editar'].__self__
    assert novo is not job['editor'] and novo._trava is not job['editor']._trava
    g = job['gid']
    assert c['editar']({'familia': g['f1080x1350'], 'versao': None, 'edicoes': [], 'quebras': []}) is not None


# ------------------------------------------------------------------ a previa igual ao Salvar
def _copiar_confirmar_e_salvar(j, f_o):
    """Pelas rotas da tela (modo de teste), como test_familia_diagonal._salvar: grava o rascunho com a origem
    (1080x1920) editada, copia o layout dela para o 1080x1350 com o ato familia_copiar (decisao 215, E8), confirma
    todas as familias e clica "Salvar e seguir". Devolve o rascunho gravado."""
    from vapt.tela import atos as ta
    from vapt.tela import servidor as ts
    import test_tela_escrita as tte
    import test_tela_servidor as tts
    conteudo, g = j['conteudo'], j['gid']
    destino, origem = g['f1080x1350'], g['f1080x1920']
    s = ts.ServidorTela(conteudo, pasta=j['job'], modo_teste=True,
                        atos=ta.atos_do_job(j['job'], conteudo=conteudo)).iniciar()
    try:
        biscoito = tts._entrar(s)
        familias = {gid: _f(tfd._versao_limpa(conteudo, gid)) for gid in conteudo['familias']}
        familias[origem], familias[destino] = f_o, _f()
        corpo = dict({'job_id': s.job_id, 'laudo_sha256': s.laudo_sha256, 'familias': familias},
                     **tfd._passo_2_diagonal(j['funcoes']))
        assert tte._escrever(s, '/api/rascunho', corpo, cookie=biscoito)[0] == 200
        tfd._ato(s, biscoito, 'modo_dados', {'modo': 'c'})
        vista = {'de': {k: f_o[k] for k in ('versao', 'edicoes', 'quebras')},
                 'para': {'versao': None, 'edicoes': [], 'quebras': []}}
        tfd._ato(s, biscoito, 'familia_copiar', {'familia': destino, 'de': origem, 'vista': vista})
        dados = json.loads((j['job'] / tr.ARQUIVO).read_text(encoding='utf-8'))
        for gid, f in dados['familias'].items():
            tfd._ato(s, biscoito, 'familia', {'familia': gid, 'versao': f['versao'], 'edicoes': f['edicoes'],
                                              'quebras': f.get('quebras') or []})
        dados = json.loads((j['job'] / tr.ARQUIVO).read_text(encoding='utf-8'))
        vista = {k: dados[k] for k in ('job_id', 'laudo_sha256', 'familias', 'funcoes', 'cobertas', 'design',
                                       'design_camadas') if k in dados}
        tfd._ato(s, biscoito, 'salvar', {'rascunho': vista})
    finally:
        s.parar()
    return dados


def test_previa_igual_ao_salvar_com_a_copia(tmp_path):
    j = _criar(tmp_path)
    conteudo, el, g = j['conteudo'], j['el'], j['gid']
    f_o = _f(edicoes=_edicoes_o(el), quebras=_quebras_o(j))
    gravado = _copiar_confirmar_e_salvar(j, f_o)
    fd = gravado['familias'][g['f1080x1350']]
    r = {'versao': fd['versao'], 'edicoes': fd['edicoes'], 'quebras': fd.get('quebras') or []}
    assert edicao.caixas_de(r['edicoes']) and fd['copiado_de']['familia'] == g['f1080x1920']
    # a tela montada de novo pelo servidor (o passo 2 do rascunho) entrou no mesmo conteudo
    p = conteudo['editar']({'familia': g['f1080x1350'], 'versao': r['versao'], 'edicoes': r['edicoes'],
                            'quebras': r['quebras']}, antes=r['edicoes'])
    m = next(x for x in p['membros'] if x['formato'] == 'f1080x1350')
    fids = [f for f, _w, _h in FORMATOS]
    ds = {fid: contratos.ler(j['job'] / nd.PASTA / ('%s.json' % fid), nd.ESQUEMA) for fid in fids}
    d = ds['f1080x1350']
    # o briefing diz de onde veio o layout, e a derivacao grava o registro (E8, salvar.montar)
    b0 = json.loads((j['job'] / 'briefing' / 'briefing-confirmado.json').read_text(encoding='utf-8'))
    comp = next(c for c in b0['composicoes'] if c['familia'] == g['f1080x1350'])
    assert comp['copiado_de'] == {k: fd['copiado_de'][k] for k in ('familia', 'arquivo', 'para', 's', 'situacao')}
    reg = next(x for x in d['registros'] if x['codigo'] == 'layout_de_outra_familia')
    assert reg['medidas']['familia'] == g['f1080x1920'] and reg['medidas']['arquivo'] == 'f1080x1920'
    tfd._confere_igual(m, d)
    copiados = {e['elemento'] for e in r['edicoes'] if e['acao'] == 'caixa'}
    for x in d['elementos']:
        if x['id'] in copiados:
            assert x['origem_geometria'] == 'da', x['id']
    assert d['caminho'] == j['editor'].derivados['f1080x1350']['caminho']
    # o texto copiado e as quebras dele foram gravados como do destino (a revisao da 171)
    t = next(x for x in d['elementos'] if x['id'] == el['texto'])
    assert t['texto_editado'] == 'VOX AH\nHOAX VA AH'
    tit = next(x for x in d['elementos'] if x['id'] == el['titulo'])
    assert tit.get('quebras_origem') == 'da'
    b = json.loads((j['job'] / 'briefing' / 'briefing-confirmado.json').read_text(encoding='utf-8'))
    q = [x for x in b.get('quebras_por_familia') or [] if x.get('familia') == g['f1080x1350']]
    assert q and q[0]['formatos'] == ['f1080x1350'] and q[0]['layer_id'] == j['ids']['titulo']
    # a caixa medida do texto copiado e a do palco (a tinta medida no destino)
    pe = next(x for x in m['palco']['elementos'] if x['id'] == el['texto'])
    if pe.get('caixa_das_linhas'):
        assert t['caixa_texto_editado'] == pytest.approx(pe['caixa'], abs=0.5)
    # o contrato do render do destino: as linhas do texto copiado e o titulo numa linha so, sem bloqueio
    from vapt.render import derivado as rd
    from vapt.render import texto as rt
    contrato, bloqueios, _c = rd.montar(j['job'], 'f1080x1350')
    assert bloqueios == [], bloqueios

    def linhas(lid):
        e = next(x for x in contrato['entradas'] if x['tipo'] == 'texto' and x['layer_id'] == lid)
        return e, [''.join(s for s, _r in ln['pedacos']) for ln in rt.linhas_da_camada(
            e['texto'], set(e.get('quebras_automaticas') or ()), e.get('quebras_juntadas'))]
    e, ls = linhas(j['ids']['texto'])
    assert e['texto_editado'] is True and ls == ['VOX AH', 'HOAX VA AH']
    _e, ls = linhas(j['ids']['titulo'])
    assert ls == ['HOAX VA']
