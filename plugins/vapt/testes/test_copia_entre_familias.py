# -*- coding: utf-8 -*-
"""Decisao 215: copiar o layout de outra familia da mesma orientacao (etapas E1 a E5 da especificacao).

A copia vira edicoes e quebras da familia destino: a 'caixa' de cada elemento (a caixa de geometria em fracao do
arquivo de edicao, com a caixa dele na mestre de onde saiu, a sangra, a sangria do DA, do_da e fundo), o texto, o
alinhamento das linhas e os apagados. Aqui so a conta pura, em memoria, sem job:
  - E1: familia.escala_unica da o mesmo s de transferir;
  - E2: a 'caixa' em edicao.aplicar e editar (a caixa exata, sem encaixe, fora das intencoes e do tamanho), a caixa
    levada a mestre de agora pela mesma transformacao (caixa_copiada) e os leitores das edicoes;
  - E3: os esquemas do rascunho, do briefing e da derivacao;
  - E4: edicoes_efetivas, caixas_que_valem, layout_do_membro (a sangra, a sangria do DA, o piso e o corte do copiado),
    layout_da_familia (a caixa sem efeito, a figura de fundo copiada) e os registros da derivacao;
  - E5: copia_entre_familias e edicoes_da_copia, ida e volta, no KV vertical (os dois arquivos derivados) e no KV
    deitado (os dois na galeria), com a conferencia M4 (edicao.conferir_copia); quebras_da_copia e quebras_neutras.
Tudo sintetico: os KVs de test_galeria_generalidade e de test_tela_piso_do_da, montados a mao."""
import copy

import pytest

import familia_geometria as G
import test_derivacao_apoio as ap
import test_galeria_generalidade as tgg
import test_tela_piso_do_da as tpd
from vapt import contratos, limites
from vapt.briefing import modelo as mb
from vapt.derivacao import familia as F
from vapt.derivacao import galeria as mg
from vapt.derivacao import nucleo as nd
from vapt.derivacao import proposta
from vapt.derivacao import quebras as mq
from vapt.derivacao import solver as mod_solver
from vapt.tela import edicao
from vapt.tela import rascunho

KW = {'specs': {}, 'arquivo_specs': None, 'params': None}
EXATO = 1e-9  # numero-neutro: px, a caixa copiada sai exata
TOL = edicao.TOL_COPIA
SANGRA_NADA = {'esq': False, 'topo': False, 'dir': False, 'base': False}


# ------------------------------------------------------------------ E1: a escala unica
@pytest.mark.parametrize('W,H,seg', [(300, 600, None), (1080, 1350, None), (1080, 1920, None), (2160, 3840, None),
                                     (1000, 1900, None), (1080, 1350, [60.0, 60.0, 1020.0, 1290.0]),
                                     (640, 360, None)])
def test_escala_unica_e_o_s_de_transferir(W, H, seg):
    ref, els, sil = G.caso_diagonal()
    m = F.extrair_modelo(ref, els, silhuetas=sil)
    membro = G.membro('m', W, H, area_segura=seg)
    assert F.escala_unica(F._quadros(membro), m['quadros']) == F.transferir(m, membro)['s']
    assert proposta.escala_da_copia(m['quadros'], F._quadros(membro)) == F.transferir(m, membro)['s']


def test_escala_unica_nunca_passa_de_1():
    pequeno, grande = G.quadros(1080.0, 1350.0), G.quadros(1080.0, 1920.0)
    assert proposta.escala_da_copia(pequeno, grande) == 1.0
    assert proposta.escala_da_copia(grande, pequeno) < 1.0


# ------------------------------------------------------------------ E2: a edicao 'caixa'
def _caixa(eid, c, W, H, doc=None, **extra):
    ed = {'elemento': eid, 'acao': 'caixa', 'arquivo': 'f%dx%d' % (W, H), 'medida': [float(W), float(H)],
          'caixa': [c[0] / W, c[1] / H, c[2] / W, c[3] / H], 'doc': list(doc or c), 'sangra': dict(SANGRA_NADA)}
    ed.update(extra)
    return ed


def test_caixa_sai_exata_sem_encaixe_nem_mexido():
    W, H = 1000.0, 500.0
    caixas = {'el1': [100.0, 100.0, 300.0, 200.0], 'el2': [500.0, 100.0, 700.0, 200.0]}
    # a caixa nova do el2 fica 0,5 px a direita da linha esquerda do el1: dentro da tolerancia da 185
    alvo = [100.5, 250.0, 260.5, 330.0]
    assert abs(alvo[0] - caixas['el1'][0]) < edicao.tolerancia(W, H)
    eds = [_caixa('el2', alvo, W, H, doc=[500.0, 100.0, 700.0, 200.0])]
    novas, apagados, textos, mexidos = edicao.aplicar(caixas, eds, W, H)
    assert novas['el2'] == pytest.approx(alvo, abs=EXATO) and mexidos == [] and apagados == [] and textos == {}
    novas, apagados, textos, mexidos, alinhados = edicao.editar(caixas, eds, W, H, kv_caixas=caixas,
                                                                 kv_tamanho=(W, H))
    assert novas['el2'] == pytest.approx(alvo, abs=EXATO)
    assert mexidos == [] and alinhados == []
    assert novas['el1'] == caixas['el1']


def test_caixa_apagada_antes_nao_volta():
    caixas = {'el1': [0.0, 0.0, 10.0, 10.0]}
    novas, apagados, _t, _m = edicao.aplicar(caixas, [{'elemento': 'el1', 'acao': 'apagar'},
                                                      _caixa('el1', [5.0, 5.0, 8.0, 8.0], 100, 100)], 100, 100)
    assert 'el1' not in novas and apagados == ['el1']


def test_caixa_sai_das_intencoes_e_volta_o_tamanho_a_1():
    eds = [{'elemento': 'el1', 'acao': 'alinhar', 'alvo': 'topo', 'referencia': 'margem'},
           {'elemento': 'el1', 'acao': 'escalar', 'fator': 0.5}]
    assert edicao.escalas(eds) == {'el1': 0.5}
    assert edicao.intencoes(eds[:1])
    eds.append(_caixa('el1', [0, 0, 10, 10], 100, 100))
    assert edicao.intencoes(eds) == []
    assert edicao.escalas(eds) == {}
    # o escalar depois multiplica a partir do tamanho copiado
    eds.append({'elemento': 'el1', 'acao': 'escalar', 'fator': 1.2})
    assert edicao.escalas(eds) == {'el1': pytest.approx(1.2)}
    assert edicao.escala_fora(eds) == []


def test_caixa_copiada_com_a_mestre_de_agora_guarda_a_transformacao():
    W, H = 1080.0, 1350.0
    doc = [100.0, 200.0, 500.0, 300.0]  # a caixa do texto na mestre da origem
    c = [54.0, 120.0, 270.0, 174.0]  # a caixa de geometria copiada: s = 216 / 400 = 0,54
    s = (c[2] - c[0]) / (doc[2] - doc[0])
    ed = _caixa('el1', c, W, H, doc=doc)
    for m in ([100.0, 180.0, 500.0, 330.0], [80.0, 200.0, 560.0, 300.0], [100.0, 200.0, 420.0, 260.0]):
        nova = edicao.caixa_copiada(ed, W, H, m)
        # o mesmo s e o mesmo ponto do documento (destino - s x origem)
        assert (nova[2] - nova[0]) / (m[2] - m[0]) == pytest.approx(s, rel=1e-9)
        assert nova[0] - s * m[0] == pytest.approx(c[0] - s * doc[0], abs=EXATO)
        assert nova[1] - s * m[1] == pytest.approx(c[1] - s * doc[1], abs=EXATO)
    # a mesma mestre (ou sem ela, o elemento que nao e texto): a propria caixa
    assert edicao.caixa_copiada(ed, W, H, doc) == pytest.approx(c, abs=EXATO)
    assert edicao.caixa_copiada(ed, W, H, None) == pytest.approx(c, abs=EXATO)


def test_caixa_copiada_na_mestre_mais_alta_pela_altura():
    ed = _caixa('el1', [10.0, 10.0, 10.0, 60.0], 100, 100, doc=[0.0, 0.0, 0.0, 100.0])
    nova = edicao.caixa_copiada(ed, 100, 100, [0.0, -20.0, 0.0, 120.0])
    assert nova == pytest.approx([10.0, 0.0, 10.0, 70.0], abs=EXATO)


def test_leitores_da_copia():
    a = _caixa('el1', [0, 0, 10, 10], 100, 100, do_da=True)
    b = _caixa('el2', [0, 0, 10, 10], 100, 100, fundo=True)
    b2 = _caixa('el2', [5, 5, 10, 10], 100, 100)
    c = _caixa('el3', [0, 0, 10, 10], 100, 100, do_da=True, fundo=True)
    eds = [{'elemento': 'el4', 'acao': 'texto', 'texto': 'X'}, a, b, b2, c, {'elemento': 'el3', 'acao': 'apagar'}]
    assert edicao.caixas_de(eds) == [a, b, b2, c]
    assert edicao.copiados(eds) == {'el1': a, 'el2': b2}  # vale a ultima; o apagar depois tira
    assert edicao.copiados_do_da(eds) == ['el1']
    assert edicao.fundo_copiado(eds) == ()
    assert edicao.fundo_copiado([a, b]) == ('el2',)
    assert edicao.fundo_copiado([{'elemento': 'el1', 'acao': 'apagar'}]) is None
    assert edicao.fundo_copiado([]) is None


# ------------------------------------------------------------------ E3: os esquemas
def _ed_caixa():
    return {'elemento': 'el12', 'acao': 'caixa', 'arquivo': 'f1080x1350', 'medida': [1080.0, 1350.0],
            'caixa': [0.1, 0.2, 0.5, 0.3], 'doc': [10.0, 20.0, 50.0, 30.0],
            'sangra': {'esq': False, 'topo': True, 'dir': False, 'base': False},
            'sangria_do_da': ['topo'], 'do_da': True, 'piso_do_da': True, 'fundo': True}


def _rascunho(edicoes, **familia):
    return {'esquema': rascunho.ESQUEMA, 'job_id': '0' * 32, 'laudo_sha256': '0' * 64, 'origem': 'rascunho',
            'atualizado_em': '2026-11-26T10:00:00', 'familias': {'vertical-1': dict(
                {'versao': None, 'confirmada': False, 'edicoes': edicoes}, **familia)}}


def _copiado_de(**extra):
    c = {'familia': 'vertical-2', 'arquivo': 'f1080x1920', 'para': 'f1080x1350', 's': 1.0, 'situacao': 'igual',
         'frases': ['Uma frase.'], 'em': '2026-11-26T10:00:00-03:00', 'quebras': [12],
         'antes': {'versao': None, 'edicoes': [{'elemento': 'el1', 'acao': 'apagar'}], 'quebras': []}}
    c.update(extra)
    return c


def _valida(doc, esquema):
    try:
        contratos.validar(doc, esquema)
    except contratos.ErroContrato:
        return False
    return True


def test_esquema_do_rascunho_aceita_a_caixa_completa_e_recusa_a_incompleta():
    assert _valida(_rascunho([_ed_caixa()]), rascunho.ESQUEMA)
    for falta in ('caixa', 'doc', 'arquivo', 'medida', 'sangra'):
        ed = _ed_caixa()
        ed.pop(falta)
        assert not _valida(_rascunho([ed]), rascunho.ESQUEMA), falta
    for campo, valor in (('caixa', [0, 0, 1, 1]), ('doc', [0, 0, 1, 1]), ('sangra', dict(SANGRA_NADA)),
                         ('do_da', True), ('piso_do_da', True), ('fundo', True), ('arquivo', 'f1'),
                         ('medida', [1, 1]),
                         ('sangria_do_da', ['esq'])):
        ed = {'elemento': 'el12', 'acao': 'apagar', campo: valor}
        assert not _valida(_rascunho([ed]), rascunho.ESQUEMA), campo
    ed = dict(_ed_caixa(), elementos=['el12', 'el13'])
    assert not _valida(_rascunho([ed]), rascunho.ESQUEMA)
    ed = dict(_ed_caixa(), caixa=[0, 0, 1])
    assert not _valida(_rascunho([ed]), rascunho.ESQUEMA)
    # a base que cresce em volta do ponto fixo (199, 2) passa muito da peca: a caixa nao tem limite
    ed = dict(_ed_caixa(), caixa=[-350.0, -330.0, 1.0, 161.0])
    assert _valida(_rascunho([ed]), rascunho.ESQUEMA)


def test_esquema_do_rascunho_aceita_o_copiado_de_com_a_familia_de_antes():
    assert _valida(_rascunho([_ed_caixa()], copiado_de=_copiado_de()), rascunho.ESQUEMA)
    # a copia de antes vai junto, para o Desfazer a devolver tambem
    antes = dict(_copiado_de()['antes'], copiado_de=_copiado_de())
    assert _valida(_rascunho([_ed_caixa()], copiado_de=_copiado_de(antes=antes)), rascunho.ESQUEMA)
    assert _valida(_rascunho([], copiado_de={k: v for k, v in _copiado_de().items() if k != 'antes'}),
                   rascunho.ESQUEMA)
    for ruim in ({'s': 1.2}, {'s': 0}, {'situacao': 'outra'}, {'frases': ['x' * 501]}, {'outro': 1},
                 {'frases': ['x'] * 51}):
        assert not _valida(_rascunho([], copiado_de=_copiado_de(**ruim)), rascunho.ESQUEMA), ruim
    assert not _valida(_rascunho([], copiado_de={k: v for k, v in _copiado_de().items() if k != 'em'}),
                       rascunho.ESQUEMA)


def _briefing_valido(edicoes, **comp):
    b = ap.briefing(formatos=[ap.formato('f1080x1350', 1080, 1350)])
    b['composicoes'] = [dict({'familia': 'vertical-1', 'formatos': ['f1080x1350'], 'versao': None,
                              'edicoes': edicoes, 'confirmada': True,
                              'confirmacao': {'origem': 'fixture_de_teste', 'meio': 'tela',
                                              'em': '2026-11-26T10:00:00-03:00'}}, **comp)]
    return b


def test_esquema_do_briefing_aceita_a_caixa_e_o_copiado_de():
    cop = {'familia': 'vertical-2', 'arquivo': 'f1080x1920', 'para': 'f1080x1350', 's': 0.9,
           'situacao': 'ajustado'}
    assert _valida(_briefing_valido([_ed_caixa()], copiado_de=cop), mb.ESQUEMA)
    ed = _ed_caixa()
    ed.pop('doc')
    assert not _valida(_briefing_valido([ed]), mb.ESQUEMA)
    assert not _valida(_briefing_valido([{'elemento': 'el12', 'acao': 'texto', 'texto': 'X',
                                          'sangra': dict(SANGRA_NADA)}]), mb.ESQUEMA)
    assert not _valida(_briefing_valido([], copiado_de=dict(cop, s=2)), mb.ESQUEMA)
    assert not _valida(_briefing_valido([], copiado_de=dict(cop, antes={})), mb.ESQUEMA)


def test_esquema_da_derivacao_descreve_os_registros_novos():
    import json
    from conftest import PASTA_MOTOR
    esq = json.loads((PASTA_MOTOR / 'schemas' / 'derivacao-1.json').read_text(encoding='utf-8'))
    regras = esq['properties']['registros']['items']['allOf']
    codigos = {r['if']['properties']['codigo']['const']: r['then'] for r in regras}
    assert set(codigos['layout_de_outra_familia']['properties']['medidas']['required']) == \
        {'arquivo', 'para', 's', 'situacao', 'elementos'}
    assert set(codigos['layout_de_outra_familia_sem_efeito']['properties']['medidas']['required']) == \
        {'arquivo', 'medida'}
    assert '215' in esq['properties']['elementos']['items']['properties']['texto_editado']['description']


# ------------------------------------------------------------------ E4: o layout com a caixa copiada
def _membro(edicoes, fid='h1'):
    """(cf, layout) do membro fid do KV 400 x 200 de test_tela_piso_do_da com as edicoes."""
    ctx, antes = tpd._derivar([])
    kv = nd.mestre_do_kv(ctx)
    f = next(x for x in ctx['briefing']['formatos'] if x['id'] == fid)
    cf = mg.contexto_do_formato(ctx, proposta.mestre_do_membro(ctx, kv, f, antes[fid]), f, specs={})
    extra = {'kv_por_id': {e['id']: e for e in kv['elementos']},
             'conteudo': [e['id'] for e in kv['elementos'] if mod_solver.conteudo(e)],
             'kv_caixas': {e['id']: [float(x) for x in e['caixa']] for e in kv['elementos']},
             'kv_tamanho': (float(kv['largura']), float(kv['altura']))}
    return cf, proposta.layout_do_membro(cf, antes[fid]['elementos'], edicoes, **extra)


def _copia_de(cf, k, c, **extra):
    W, H = cf['W'], cf['H']
    doc = next(e['caixa'] for e in cf['kv']['elementos'] if e['id'] == k)
    sangra = extra.pop('sangra', None) or dict(next(e['sangra'] for e in cf['kv']['elementos'] if e['id'] == k))
    ed = {'elemento': k, 'acao': 'caixa', 'arquivo': cf['formato']['id'], 'medida': [W, H],
          'caixa': [c[0] / W, c[1] / H, c[2] / W, c[3] / H], 'doc': list(doc), 'sangra': sangra}
    ed.update(extra)
    return ed


def _piso(lay, k):
    return [f for f in lay['falhas'] if f['codigo'] == 'abaixo_do_piso_da_regra' and k in f['elementos']]


def _decisao_piso(lay, k):
    return [f for f in lay['decisoes_do_da'] if f['codigo'] == 'abaixo_do_piso_da_regra' and k in f['elementos']]


def test_layout_parte_da_caixa_copiada_com_a_sangra_dela():
    cf, lay0 = _membro([])
    A = tpd.A
    c = [x + 7.0 for x in lay0['caixas'][A]]
    sangra = dict(SANGRA_NADA, base=True)
    _cf, lay = _membro([_copia_de(cf, A, c, sangra=sangra)])
    assert lay['caixas'][A] == pytest.approx(c, abs=1e-6)
    assert lay['sangra'][A] == sangra
    assert lay['copiados'] == [A] and lay['copiados_do_da'] == [] and lay['mexidos'] == []
    assert next(e for e in lay['elementos'] if e['id'] == A)['transformacao']['sangra'] == sangra


def test_sangria_do_da_da_origem_volta_no_copiado():
    cf, lay0 = _membro([])
    A = tpd.A
    c = list(lay0['caixas'][A])
    W = cf['W']
    c = [W - 30.0, c[1], W + 30.0, c[3]]
    _cf, lay = _membro([_copia_de(cf, A, c, sangra=dict(SANGRA_NADA, dir=True), sangria_do_da=['dir'],
                                  do_da=True)])
    assert lay['sangria_do_da'] == {A: ['dir']}
    assert lay['copiados_do_da'] == [A]


def test_piso_furado_pelo_copiado_do_da_e_decisao_e_o_sem_do_da_e_falha():
    cf, pequeno = _membro(tpd.PEQUENA)
    A = tpd.A
    assert _decisao_piso(pequeno, A)  # na origem, decisao do DA
    c = pequeno['caixas'][A]
    _cf, com = _membro([_copia_de(cf, A, c, do_da=True, piso_do_da=True)])
    assert _decisao_piso(com, A) and not _piso(com, A), (com['falhas'], com['decisoes_do_da'])
    # so do_da (o DA mexeu o elemento na origem, mas o piso nao era decisao dele la): o piso que a copia fura e falha
    _cf, so_da = _membro([_copia_de(cf, A, c, do_da=True)])
    assert _piso(so_da, A) and not _decisao_piso(so_da, A), (so_da['falhas'], so_da['decisoes_do_da'])
    _cf, sem = _membro([_copia_de(cf, A, c)])
    assert _piso(sem, A) and not _decisao_piso(sem, A)
    # mexer meio px no copiado sem do_da: o piso que a copia ja furava continua falha (a partida e a copia)
    _cf, mexido = _membro([_copia_de(cf, A, c), {'elemento': A, 'acao': 'mover', 'dx': 0.5 / cf['W'], 'dy': 0}])
    assert _piso(mexido, A) and not _decisao_piso(mexido, A)


def test_piso_do_da_copiado_continua_decisao_depois_de_mexer():
    # revisao 2 da 215: o piso que ja era decisao do DA na origem (piso_do_da) continua decisao depois que o DA anda o
    # copiado meio px, como na origem; sem piso_do_da, o piso que a copia fura continua falha com o mesmo mover
    cf, pequeno = _membro(tpd.PEQUENA)
    A = tpd.A
    c = pequeno['caixas'][A]
    mover = {'elemento': A, 'acao': 'mover', 'dx': 0.5 / cf['W'], 'dy': 0}
    _cf, origem = _membro(list(tpd.PEQUENA) + [mover])
    assert _decisao_piso(origem, A) and not _piso(origem, A)
    _cf, com = _membro([_copia_de(cf, A, c, do_da=True, piso_do_da=True), mover])
    assert _decisao_piso(com, A) and not _piso(com, A), (com['falhas'], com['decisoes_do_da'])
    _cf, so_da = _membro([_copia_de(cf, A, c, do_da=True), mover])
    assert _piso(so_da, A) and not _decisao_piso(so_da, A), (so_da['falhas'], so_da['decisoes_do_da'])


def test_corte_do_copiado_do_da_e_corte_a_mostra():
    cf, lay0 = _membro([])
    fundo = 'el%d' % tpd.FUNDO
    W, H = cf['W'], cf['H']
    dentro = [20.0, 20.0, W - 20.0, H - 20.0]
    sangra = {'esq': True, 'topo': True, 'dir': True, 'base': True}
    _cf, lay = _membro([_copia_de(cf, fundo, dentro, sangra=sangra, do_da=True)])
    cortes = [f for f in lay['falhas'] if f['codigo'] == 'corte_a_mostra']
    assert cortes and cortes[0]['elementos'] == [fundo], lay['falhas']
    assert not [f for f in lay['falhas'] if f['codigo'] == 'validacao_reprova' and f['elementos'] == [fundo] and
                (f.get('medidas') or {}).get('validacao') == 'enquadramento']


def test_edicoes_efetivas_a_caixa_devolve_o_tirado():
    caixa = _caixa('el5', [0, 0, 1, 1], 10, 10)
    assert proposta.edicoes_efetivas(['el5', 'el6'], [caixa]) == [{'elemento': 'el6', 'acao': 'apagar'}, caixa]
    apaga = {'elemento': 'el5', 'acao': 'apagar'}
    assert proposta.edicoes_efetivas(['el5'], [caixa, apaga]) == [caixa, apaga]


def test_caixas_que_valem():
    boa = _caixa('el1', [0, 0, 10, 10], 1080, 1350)
    outro = dict(boa, arquivo='f1080x1920')
    girada = dict(boa, medida=[1350.0, 1080.0])
    perto = dict(boa, medida=[1080.4, 1350.0])
    texto = {'elemento': 'el2', 'acao': 'texto', 'texto': 'X'}
    assert proposta.caixas_que_valem([texto, boa, perto], 'f1080x1350', [1080.0, 1350.0]) == ([texto, boa, perto],
                                                                                             None)
    eds, sem = proposta.caixas_que_valem([texto, outro, boa], 'f1080x1350', [1080.0, 1350.0])
    assert eds == [texto, boa] and sem == {'arquivo': 'f1080x1920', 'medida': [1080.0, 1350.0]}
    eds, sem = proposta.caixas_que_valem([girada, texto], 'f1080x1350', [1080.0, 1350.0])
    assert eds == [texto] and sem == {'arquivo': 'f1080x1350', 'medida': [1350.0, 1080.0]}


def test_layout_da_familia_com_a_caixa_de_outro_arquivo_fica_sem_efeito():
    ctx, antes = tpd._derivar([])
    kv = nd.mestre_do_kv(ctx)
    ref = proposta.arquivo_de_edicao([f for f in ctx['briefing']['formatos'] if f['id'] in ('h1', 'h2')])
    outro = 'h1' if ref == 'h2' else 'h2'
    P = 'el%d' % tpd.PRODUTO
    caixa = dict(_caixa(tpd.A, [1, 1, 20, 20], 840, 420), arquivo=outro)
    eds = [{'elemento': P, 'acao': 'apagar'}, caixa]
    lays = proposta.layout_da_familia(ctx, kv, {'familia': 'horizontal', 'formatos': ['h1', 'h2'], 'versao': None,
                                                'edicoes': eds}, derivados=antes, **KW)
    lay = lays[ref]
    assert lay['copia_sem_efeito'] == {'arquivo': outro, 'medida': [840.0, 420.0]}
    assert lay['copiados'] == [] and lay['copiado_de'] is None
    assert P in lay['apagados'] and P in lays[outro]['apagados']
    # sem a caixa, nada muda
    lays2 = proposta.layout_da_familia(ctx, kv, {'familia': 'horizontal', 'formatos': ['h1', 'h2'], 'versao': None,
                                                 'edicoes': eds[:1]}, derivados=antes, **KW)
    assert lays2[ref]['caixas'] == lay['caixas'] and lays2[ref]['copia_sem_efeito'] is None


def _com_composicao(b, edicoes, **comp):
    b['composicoes'] = [dict({'familia': 'horizontal', 'formatos': ['h1', 'h2'], 'versao': None, 'edicoes': edicoes,
                              'confirmada': True, 'confirmacao': dict(tpd.CONF)}, **comp)]
    return b


def test_derivacao_grava_a_origem_da_e_os_registros_da_copia():
    ctx0, antes = tpd._derivar([])
    kv = nd.mestre_do_kv(ctx0)
    ref = proposta.arquivo_de_edicao([f for f in ctx0['briefing']['formatos'] if f['id'] in ('h1', 'h2')])
    outro = 'h1' if ref == 'h2' else 'h2'
    lays = proposta.layout_da_familia(ctx0, kv, {'familia': 'horizontal', 'formatos': ['h1', 'h2'], 'versao': None,
                                                 'edicoes': []}, derivados=antes, **KW)
    cf = lays[ref]['cf']
    A = tpd.A
    c = [x + 4.0 for x in lays[ref]['caixas'][A]]
    cop = {'familia': 'vertical-9', 'arquivo': 'v9', 'para': ref, 's': 0.8, 'situacao': 'ajustado'}
    b = _com_composicao(tpd._briefing([]), [_copia_de(cf, A, c)], copiado_de=cop)
    contratos.validar(b, mb.ESQUEMA)
    ctx = nd.contexto(tpd._laudo(), b)
    r = nd.derivar_em_memoria(ctx, specs={})['formatos']
    d = r[ref]
    contratos.validar(d, nd.ESQUEMA)
    x = next(e for e in d['elementos'] if e['id'] == A)
    assert x['origem_geometria'] == 'da'
    assert x['caixa'] == pytest.approx(c, abs=0.01)
    reg = next(g for g in d['registros'] if g['codigo'] == 'layout_de_outra_familia')
    assert reg['medidas'] == dict(cop, elementos=[A])
    assert d['caminho'] == antes[ref]['caminho']
    assert not [g for g in r[outro]['registros'] if g['codigo'] == 'layout_de_outra_familia']
    # a caixa de outro arquivo: o registro da caixa sem efeito
    b = _com_composicao(tpd._briefing([]), [dict(_copia_de(cf, A, c), arquivo=outro)])
    contratos.validar(b, mb.ESQUEMA)
    d = nd.derivar_em_memoria(nd.contexto(tpd._laudo(), b), specs={})['formatos'][ref]
    contratos.validar(d, nd.ESQUEMA)
    reg = next(g for g in d['registros'] if g['codigo'] == 'layout_de_outra_familia_sem_efeito')
    assert reg['medidas']['arquivo'] == outro
    assert not [g for g in d['registros'] if g['codigo'] == 'layout_de_outra_familia']


# ------------------------------------------------------------------ E5: a copia entre familias
def _kv(laudo_funcoes, formatos):
    laudo, funcoes, ancoras, _fmts = laudo_funcoes
    b = ap.briefing(funcoes=funcoes, regras=tgg.REGRAS, ancoras=ancoras,
                    formatos=[ap.formato(i, w, h) for i, w, h in formatos])
    ctx = nd.contexto(laudo, b)
    r = nd.derivar_em_memoria(ctx, specs={})
    return {'ctx': ctx, 'kv': r['kv'], 'derivados': r['formatos'], 'formatos': {f['id']: f for f in b['formatos']},
            'laudo': laudo}


def _lays(j, gid, fids, edicoes, versao=None, fundo_da_versao=None):
    fs = [j['formatos'][f] for f in fids]
    gal, _m, _s = proposta.galeria_dos_devolvidos(j['ctx'], j['kv'], j['derivados'], fs, **KW)
    versoes = {fid: {v['id']: v for _n, v in pares} for fid, pares in gal.items()}
    ref = proposta.arquivo_de_edicao(fs)
    if fundo_da_versao is not None and versoes.get(ref):
        # a primeira versao com (ou sem) a figura de fundo (n 202)
        cf = mg.contexto_do_formato(j['ctx'], proposta.mestre_do_membro(j['ctx'], j['kv'], j['formatos'][ref],
                                                                        j['derivados'][ref]), j['formatos'][ref],
                                    **KW)
        versao = next(v for v in versoes[ref] if bool(mg.fundo_da_versao(cf, v)) == fundo_da_versao)
    return proposta.layout_da_familia(j['ctx'], j['kv'], {'familia': gid, 'formatos': fids, 'versao': versao,
                                                          'edicoes': edicoes},
                                      derivados=j['derivados'], versoes=versoes, **KW), versao


def _copiar(j, de, para, edicoes, versao_o=None, versao_d=None, fundo_o=None, fundo_d=None):
    """(lay_o, lay_t, edicoes da copia, lay_d): a origem com as edicoes, a copia, e o destino com elas."""
    lays_o, _v = _lays(j, 'o', [de], edicoes, versao_o, fundo_o)
    lay_o = lays_o[de]
    lay_t = proposta.copia_entre_familias(j['ctx'], j['kv'], lay_o, j['formatos'][para], **KW)
    eds = proposta.edicoes_da_copia(lay_t, lay_o, j['kv'])
    lays_d, vd = _lays(j, 'd', [para], eds, versao_d, fundo_d)
    return lay_o, lay_t, eds, lays_d[para]


VERTICAIS = [('v1080x1350', 1080, 1350), ('v1080x1920', 1080, 1920), ('v2160x3840', 2160, 3840)]


@pytest.fixture(scope='module')
def kv_em_pe():
    j = _kv(tgg.kv_b(), VERTICAIS)
    assert all(j['derivados'][f]['situacao'] == 'derivado' for f, _w, _h in VERTICAIS)
    return j


@pytest.fixture(scope='module')
def kv_deitado():
    j = _kv(tgg.kv_a(), VERTICAIS)
    assert all(proposta.usa_galeria(j['derivados'][f]) for f, _w, _h in VERTICAIS)
    return j


EDICOES_O = [{'elemento': 'el2', 'acao': 'mover', 'dx': 0.03, 'dy': 0.01},
             {'elemento': 'el9', 'acao': 'escalar', 'fator': 0.9},
             {'elemento': 'el3', 'acao': 'texto', 'texto': 'HOAX\nVOX'},
             {'elemento': 'el8', 'acao': 'apagar'}]


def _confere(lay_t, lay_d):
    assert edicao.conferir_copia(lay_t, lay_d) == []


@pytest.mark.parametrize('de,para', [('v1080x1350', 'v1080x1920'), ('v1080x1920', 'v1080x1350'),
                                     ('v1080x1350', 'v2160x3840'), ('v2160x3840', 'v1080x1350')])
def test_ida_e_volta_no_kv_em_pe(kv_em_pe, de, para):
    lay_o, lay_t, eds, lay_d = _copiar(kv_em_pe, de, para, EDICOES_O)
    _confere(lay_t, lay_d)
    assert sorted(lay_d['copiados']) == sorted(lay_t['caixas'])
    assert lay_d['textos'] == {'el3': 'HOAX\nVOX'} and 'el8' in lay_d['apagados']
    assert [e['acao'] for e in eds][:2] == ['texto', 'apagar']
    # as caixas em fracao com 10 casas (proposta.CASAS_FRACAO)
    for e in eds:
        if e['acao'] == 'caixa':
            assert all(round(v, proposta.CASAS_FRACAO) == v for v in e['caixa'])
    # os decididos pelo DA na origem levam do_da
    assert {e['elemento'] for e in eds if e.get('do_da')} >= {'el2', 'el9', 'el3'}
    s = lay_t['transferencia']['s']
    W_o, W_d = kv_em_pe['formatos'][de]['largura'], kv_em_pe['formatos'][para]['largura']
    assert s <= 1.0 and (W_d >= W_o or s < 1.0)


def test_s_vem_dos_quadros_nunca_da_medida(kv_em_pe):
    _o, lay_t, _e, _d = _copiar(kv_em_pe, 'v1080x1920', 'v1080x1350', [])
    j = kv_em_pe
    cfs = {}
    for f in ('v1080x1920', 'v1080x1350'):
        m = proposta.mestre_do_membro(j['ctx'], j['kv'], j['formatos'][f], j['derivados'][f])
        cfs[f] = mg.contexto_do_formato(j['ctx'], m, j['formatos'][f], **KW)
    s = proposta.escala_da_copia(proposta.quadros_do_membro(cfs['v1080x1920']),
                                 proposta.quadros_do_membro(cfs['v1080x1350']))
    assert lay_t['transferencia']['s'] == pytest.approx(s, abs=1e-6)
    assert s != pytest.approx(1350.0 / 1920.0, abs=1e-3)


def test_copia_de_copia_e_volta_nao_liga_nada(kv_em_pe):
    j = kv_em_pe
    _o, lay_t, eds, lay_b = _copiar(j, 'v1080x1350', 'v1080x1920', EDICOES_O)
    # B (com a copia) para C: a copia de B e a origem
    lay_t2 = proposta.copia_entre_familias(j['ctx'], j['kv'], lay_b, j['formatos']['v2160x3840'], **KW)
    eds2 = proposta.edicoes_da_copia(lay_t2, lay_b, j['kv'])
    lays_c, _v = _lays(j, 'c', ['v2160x3840'], eds2)
    _confere(lay_t2, lays_c['v2160x3840'])
    # os decididos pelo DA na origem continuam decisao na copia da copia
    assert {e['elemento'] for e in eds2 if e.get('do_da')} >= {'el2', 'el9', 'el3'}


EDICOES_SO_MOVIDA = [{'elemento': k, 'acao': 'mover', 'dx': 0.0, 'dy': 0.002} for k in ('el2', 'el3', 'el9', 'el10')]


def _copia_so_movida(j, de):
    # o DA so andou 0,2% com os elementos na origem, sem piso nenhum la
    lay_o, lay_t, eds, lay_d = _copiar(j, de, 'v2160x3840', EDICOES_SO_MOVIDA)
    assert not [f for f in lay_o['falhas'] + lay_o['decisoes_do_da'] if f['codigo'] in mg.PISOS_DO_DA]
    assert {e['elemento'] for e in eds if e.get('do_da')} >= {'el2', 'el3', 'el9', 'el10'}
    assert not [e for e in eds if e.get('piso_do_da')]
    assert not [f for f in lay_d['decisoes_do_da'] if f['codigo'] in mg.PISOS_DO_DA]
    return lay_d


def _editor_em_pe(j):
    # o Editor da tela montado a mao sobre o KV em pe: uma familia por formato, sem versao da galeria
    familias = {'g' + f: [f] for f, _w, _h in VERTICAIS}
    return edicao.Editor(j['ctx'], j['kv'], j['laudo'], None, j['derivados'], {}, familias, [], **KW)


def test_origem_so_movida_para_o_arquivo_maior_o_piso_da_copia_e_falha(kv_em_pe):
    # o piso que so a copia fura no arquivo maior (o 1080x1350 vai a 35% no 2160x3840) continua falha (pede
    # ajuste), e nao vira decisao do DA (revisao da 215, resposta 1 do Duda)
    lay_d = _copia_so_movida(kv_em_pe, 'v1080x1350')
    n_piso = [f for f in lay_d['falhas'] if f['codigo'] == 'abaixo_do_piso_da_regra']
    assert n_piso, lay_d['decisoes_do_da']
    r = _editor_em_pe(kv_em_pe)._copiar('gv2160x3840', 'gv1080x1350', {'edicoes': EDICOES_SO_MOVIDA}, {})
    assert r['n_piso'] == len(n_piso) and r['situacao'] == 'pede_ajuste'


def test_origem_so_movida_duas_vezes_menor_fica_no_piso_sem_falha_e_pede_ajuste_pela_janela(kv_em_pe):
    # o 1080x1920 para o 2160x3840 e exatamente 2x: a copia fica no mesmo ponto da origem, exatamente no piso
    # (fracao 0,5, minimo 0,5). Com as 10 casas (proposta.CASAS_FRACAO) a caixa sai exata: nenhuma falha nem
    # decisao de piso no destino. A resposta 1 do Duda (do menor para o maior pede ajuste) vale pela janela e pelo
    # copiado_de: o Editor marca pede_ajuste so pela origem menor
    lay_d = _copia_so_movida(kv_em_pe, 'v1080x1920')
    assert not [f for f in lay_d['falhas'] if f['codigo'] in mg.PISOS_DO_DA], lay_d['falhas']
    r = _editor_em_pe(kv_em_pe)._copiar('gv2160x3840', 'gv1080x1920', {'edicoes': EDICOES_SO_MOVIDA}, {})
    assert 'motivo' not in r, r
    assert r['n_piso'] == 0 and r['falhas_d'] == []
    assert r['s'] == 1.0 and r['origem_menor'] is True
    assert r['situacao'] == 'pede_ajuste' and r['copiado_de']['situacao'] == 'pede_ajuste'


def test_piso_que_era_decisao_na_origem_leva_piso_do_da_na_copia():
    # a origem com o piso decidido pelo DA (tpd.PEQUENA): a caixa copiada leva piso_do_da, e o piso continua decisao
    ctx, antes = tpd._derivar([])
    kv = nd.mestre_do_kv(ctx)
    lays = proposta.layout_da_familia(ctx, kv, {'familia': 'horizontal', 'formatos': ['h1', 'h2'], 'versao': None,
                                                'edicoes': list(tpd.PEQUENA)}, derivados=antes, **KW)
    ref = proposta.arquivo_de_edicao([f for f in ctx['briefing']['formatos'] if f['id'] in ('h1', 'h2')])
    lay_o = lays[ref]
    assert _decisao_piso(lay_o, tpd.A)
    eds = proposta.edicoes_da_copia(lay_o, lay_o, kv)
    marcados = [e['elemento'] for e in eds if e.get('piso_do_da')]
    assert tpd.A in marcados
    assert all(e.get('do_da') for e in eds if e.get('piso_do_da'))


def test_ida_e_volta_no_kv_deitado_com_a_figura_de_fundo(kv_deitado):
    j = kv_deitado
    fig = mg.figura(j['kv'])['id']
    for de, para in (('v1080x1350', 'v1080x1920'), ('v1080x1920', 'v1080x1350')):
        # a origem na versao com a figura de fundo; o destino numa versao com banda
        lay_o, lay_t, eds, lay_d = _copiar(j, de, para, EDICOES_O[:1], fundo_o=True, fundo_d=False)
        assert lay_o['figura_de_fundo'] == fig
        assert [e['elemento'] for e in eds if e.get('fundo')] == [fig]
        assert lay_d['figura_de_fundo'] == fig
        _confere(lay_t, lay_d)
        # a origem com banda e o destino na versao de fundo: a copia sem fundo nao liga a figura
        lay_o, lay_t, eds, lay_d = _copiar(j, de, para, [], fundo_o=False, fundo_d=True)
        assert lay_o['figura_de_fundo'] is None
        assert not [e for e in eds if e.get('fundo')]
        assert lay_d['figura_de_fundo'] is None
        _confere(lay_t, lay_d)


def test_figura_de_fundo_copiada_vai_ao_irmao_em_pe(kv_deitado):
    j = kv_deitado
    fig = mg.figura(j['kv'])['id']
    lay_o, lay_t, eds, _d = _copiar(j, 'v1080x1350', 'v2160x3840', [], fundo_o=True)
    # o destino com um irmao em pe (o 1080x1920 copia o arquivo de edicao 2160x3840)
    lays, _v = _lays(j, 'd', ['v2160x3840', 'v1080x1920'], eds)
    assert lays['v2160x3840']['figura_de_fundo'] == fig
    assert lays['v1080x1920']['figura_de_fundo'] == fig


def test_tirados_da_origem_chegam_apagados(kv_deitado, monkeypatch):
    j = kv_deitado
    lays_o, v = _lays(j, 'o', ['v1080x1350'], [])
    vid = lays_o['v1080x1350']['versao']
    # a versao de partida com um grafismo tirado (n 204), como a galeria a monta quando o grafismo nao cabe
    real = proposta.galeria_dos_devolvidos

    def com_tirado(*a, **k):
        gal, m, s = real(*a, **k)
        gal = {f: [(n, dict(x, tirados=['el5']) if x['id'] == vid and f == 'v1080x1350' else x) for n, x in pares]
               for f, pares in gal.items()}
        return gal, m, s
    monkeypatch.setattr(proposta, 'galeria_dos_devolvidos', com_tirado)
    lays_o, _v = _lays(j, 'o', ['v1080x1350'], [], vid)
    lay_o = lays_o['v1080x1350']
    assert lay_o['tirados'] == ['el5']
    lay_t = proposta.copia_entre_familias(j['ctx'], j['kv'], lay_o, j['formatos']['v1080x1920'], **KW)
    eds = proposta.edicoes_da_copia(lay_t, lay_o, j['kv'])
    assert {'elemento': 'el5', 'acao': 'apagar'} in eds
    assert 'el5' not in {e['elemento'] for e in eds if e['acao'] == 'caixa'}
    # no destino o tirado chega como apagado pelo DA (sem o Devolver: nao e tirado da versao do destino)
    lays_d, _v = _lays(j, 'd', ['v1080x1920'], eds)
    assert 'el5' in lays_d['v1080x1920']['apagados'] and 'el5' not in lays_d['v1080x1920']['tirados']
    _confere(lay_t, lays_d['v1080x1920'])


def test_conferencia_m4_pega_a_diferenca(kv_em_pe, monkeypatch):
    j = kv_em_pe
    _o, lay_t, _e, lay_d = _copiar(j, 'v1080x1350', 'v2160x3840', EDICOES_O)
    _confere(lay_t, lay_d)
    for campo, mudar in (('caixas', lambda c: [c[0] + 0.01, c[1], c[2] + 0.01, c[3]]),
                         ('caixas_visiveis', lambda c: [c[0], c[1], c[2], c[3] + 0.01])):
        d2 = copy.deepcopy(lay_d)
        k = sorted(d2[campo])[0]
        d2[campo][k] = mudar(d2[campo][k])
        assert edicao.conferir_copia(lay_t, d2), campo
    d2 = copy.deepcopy(lay_d)
    d2['apagados'] = []
    assert edicao.conferir_copia(lay_t, d2)
    # a fracao com 3 casas nao fecha no arquivo de 3840 px: as casas de CASAS_FRACAO sao precisas
    monkeypatch.setattr(proposta, 'CASAS_FRACAO', 3)
    _o, lay_t, _e, lay_d = _copiar(j, 'v1080x1350', 'v2160x3840', EDICOES_O)
    assert edicao.conferir_copia(lay_t, lay_d)


# ------------------------------------------------------------------ E5: as quebras da copia
LID = 5
EDITADO = 'NOVO\nTEXTO\nAQUI'


def _ctx_quebras(quebras_por_familia, comps=()):
    camada = {'identidade': {'layer_id': LID}, 'tipo': 'texto',
              'texto': {'conteudo': 'AAAA\rBBBB\rCCCC',
                        'runs': [{'inicio': 0, 'texto': 'AAAA\rBBBB\rCCCC', 'entrelinha_efetiva_px': 50.0,
                                  'tem_tinta': True}]},
              'geometria': {'caixa_tinta': [100.0, 100.0, 500.0, 250.0], 'caixa': [100.0, 100.0, 500.0, 250.0]}}
    return {'briefing': {'quebras_por_familia': list(quebras_por_familia), 'composicoes': list(comps)},
            'laudo': {'camadas': [camada]}}, camada


FAIXA = {'layer_id': LID, 'razao_max': 0.7, 'quebras': {'situacao': 'confirmado', 'valor': [0],
                                                         'origem': {'tipo': 'fixture_de_teste', 'ref': None}}}
KV_Q = {'elementos': [{'id': 'el1', 'layer_ids': [LID]}, {'id': 'el2', 'layer_ids': [9]}]}
DERIVADO = {'situacao': 'derivado', 'mestre': {'tipo': 'kv'}}
F1920 = {'id': 'f1080x1920', 'largura': 1080, 'altura': 1920}
F1350 = {'id': 'f1080x1350', 'largura': 1080, 'altura': 1350}


def _lay_q(apagados=()):
    return {'apagados': list(apagados), 'caixas': {'el1': [0, 0, 1, 1], 'el2': [0, 0, 1, 1]}}


def test_quebras_da_copia_passo_1_copia_as_entradas_da_origem():
    ctx, _c = _ctx_quebras([])
    q = {'elemento': 'el1', 'layer_id': LID, 'manter': [1], 'inseridas': [], 'origem': 'da', 'aprovada': True}
    qs = proposta.quebras_da_copia(ctx, KV_Q, _lay_q(), [q], F1350, {'situacao': 'devolvido'}, [])
    assert qs == [q] and qs[0] is not q
    assert proposta.quebras_da_copia(ctx, KV_Q, _lay_q(['el1']), [q], F1350, DERIVADO, []) == []


def test_quebras_da_copia_passo_2_a_faixa_da_origem_derivada_so_no_texto_do_kv():
    ctx, camada = _ctx_quebras([FAIXA])
    qs = proposta.quebras_da_copia(ctx, KV_Q, _lay_q(), [], F1920, DERIVADO, [])
    assert qs == [{'elemento': 'el1', 'layer_id': LID, 'manter': [0], 'inseridas': [], 'origem': 'da',
                   'aprovada': True}]
    # a entrada passa nas conferencias do rascunho e do briefing
    assert mq.conferir_da_familia(camada, [0], []) is None
    # na origem da galeria (sem faixa) ou com mestre propria: nada
    assert proposta.quebras_da_copia(ctx, KV_Q, _lay_q(), [], F1920, {'situacao': 'devolvido'}, []) == []
    assert proposta.quebras_da_copia(ctx, KV_Q, _lay_q(), [], F1920,
                                     {'situacao': 'derivado', 'mestre': {'tipo': 'propria'}}, []) == []
    # o formato fora da faixa: nada
    assert proposta.quebras_da_copia(ctx, KV_Q, _lay_q(), [], F1350, DERIVADO, []) == []
    # o texto editado nunca ganha entrada de faixa (caso A da prova da mestre)
    eds = [{'elemento': 'el1', 'acao': 'texto', 'texto': EDITADO}]
    assert proposta.quebras_da_copia(ctx, KV_Q, _lay_q(), [], F1920, DERIVADO, eds) == []


def test_quebras_neutras_no_destino_derivado_so_no_texto_do_kv():
    ctx, camada = _ctx_quebras([FAIXA])
    novas = proposta.quebras_neutras(ctx, KV_Q, [], [], F1920, DERIVADO)
    assert novas == [{'elemento': 'el1', 'layer_id': LID, 'manter': [0, 1], 'inseridas': [], 'origem': 'da',
                      'aprovada': True}]
    assert mq.conferir_da_familia(camada, [0, 1], []) is None
    # com entrada, sem faixa, no editado, no apagado ou no destino da galeria: nada
    q = dict(novas[0], manter=[1])
    assert proposta.quebras_neutras(ctx, KV_Q, [q], [], F1920, DERIVADO) == []
    assert proposta.quebras_neutras(ctx, KV_Q, [], [], F1350, DERIVADO) == []
    assert proposta.quebras_neutras(ctx, KV_Q, [], [{'elemento': 'el1', 'acao': 'texto', 'texto': EDITADO}], F1920,
                                    DERIVADO) == []
    assert proposta.quebras_neutras(ctx, KV_Q, [], [{'elemento': 'el1', 'acao': 'apagar'}], F1920, DERIVADO) == []
    assert proposta.quebras_neutras(ctx, KV_Q, [], [], F1920, {'situacao': 'devolvido'}) == []


def test_quebras_da_copia_passam_no_rascunho_e_no_briefing():
    ctx, _c = _ctx_quebras([FAIXA])
    for qs in (proposta.quebras_da_copia(ctx, KV_Q, _lay_q(), [], F1920, DERIVADO, []),
               proposta.quebras_neutras(ctx, KV_Q, [], [], F1920, DERIVADO)):
        assert qs and _valida(_rascunho([], quebras=qs), rascunho.ESQUEMA)
        # e no briefing, como o "Salvar e seguir" as grava (quebras_por_familia da familia)
        from vapt.briefing import salvar
        for n in salvar.quebras_da_familia('vertical-1', ['f1080x1920'], {'quebras': qs}, mb.ORIGEM_DA):
            assert mq.conferir_da_familia(_c, n['quebras']['valor'], n.get('inseridas') or []) is None


def test_mestre_diferente_a_transformacao_do_texto_fica():
    """Casos A e B da prova da mestre: a mestre do destino com a caixa do texto diferente da da origem (a faixa so de
    um lado, ou a quebra mudada depois). A caixa copiada vai a mestre do destino com o mesmo s e o mesmo ponto."""
    from vapt.derivacao import nucleo
    medidas = {mq.chave(LID, [0]): {'largura_texto': 600.0, 'largura_texto_mestre': 400.0}}
    ctx, camada = _ctx_quebras([FAIXA])
    ctx['medidas_quebras'] = medidas
    el = {'id': 'el1', 'layer_ids': [LID], 'caixa': [100.0, 100.0, 500.0, 250.0], 'caixa_doc': [100.0, 100.0, 500.0,
                                                                                                 250.0], 'raiz': LID}
    mestre = {'tipo': 'kv', 'elementos': [el], 'canvas_doc': [0.0, 0.0, 1000.0, 1000.0]}
    m_faixa, _sem = nucleo._com_quebras(ctx, copy.deepcopy(mestre), F1920, 1080, 1920)
    doc_faixa = m_faixa['elementos'][0]['caixa']
    assert doc_faixa != el['caixa']
    for doc, agora in ((doc_faixa, el['caixa']), (el['caixa'], doc_faixa)):
        c = [50.0, 60.0, 50.0 + 0.7 * (doc[2] - doc[0]), 60.0 + 0.7 * (doc[3] - doc[1])]
        ed = _caixa('el1', c, 1080, 1920, doc=doc)
        nova = edicao.caixa_copiada(ed, 1080, 1920, agora)
        s = (nova[2] - nova[0]) / (agora[2] - agora[0])
        assert s == pytest.approx(0.7, rel=1e-6)
        assert nova[0] - s * agora[0] == pytest.approx(c[0] - 0.7 * doc[0], abs=1e-6)
        assert nova[1] - s * agora[1] == pytest.approx(c[1] - 0.7 * doc[1], abs=1e-6)


def test_grupo_escala_min_existe():
    assert 0 < float(limites.valor('derivacao.grupo_escala_min')) < 1
