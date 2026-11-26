# -*- coding: utf-8 -*-
"""M7b, A7: o render do texto editado pelo DA no palco (decisoes-v1.md, 169 e 171).

Criterios de pronto cobertos aqui:
  - a derivacao nunca junta as quebras da proposta com o texto editado: o texto do DA leva so as quebras dele (o \\n);
    Linhas do DA (0.9.4): nada quebra na largura da caixa, e a derivacao guarda a caixa medida da tinta
    (caixa_texto_editado), que o contrato usa como caixa validada;
  - o contrato do render leva o texto editado nos trechos da regra R3 (decisoes-v1.md, 214): cada caractere com o
    estilo e a cor de um trecho do KV, e o KV de uma cor (o PSD de duas linhas) num trecho so (a quebra sem tinta de
    outro estilo que continua quebra guarda o run dela, sem tinta, e a linha leva a entrelinha do KV); e confere o
    cmap da face do job de cada trecho como a edicao na tela: caractere que a fonte nao tem e recusado com motivo claro;
  - no Chromium, o texto com \\n sai exatamente nas linhas pedidas, e a linha mais larga que a caixa do KV fica numa
    linha so, com o mesmo corpo (0.9.4);
  - a tinta do render bate com a previa da tela dentro da tolerancia da tinta do texto (render.tolerancia_tinta_texto);
  - a quebra de linha da familia da tela (M7b, C2) chega a todo membro da familia: no texto do KV, a derivacao mede a
    caixa no Chromium e o render junta as linhas dentro dela; no texto editado, o render insere a quebra do DA no
    espaco do texto novo.
Tudo sintetico: o PSD de duas linhas de test_tela_palco e a fonte de autoteste do motor."""
import json
import shutil
import sys

import pytest

import test_derivacao_apoio as ap
import test_fontes_apoio as fap
import test_tela_palco as tp
from vapt import contratos, humano
from vapt.briefing import modelo as mb
from vapt.derivacao import nucleo as nd
from vapt.derivacao import quebras as mq
from vapt.render import derivado as rd
from vapt.render import execucao
from vapt.render import texto as rt
from vapt.tela import estado as te

ROT0 = {'graus': 0, 'sentido': None}
CONF = {'origem': 'da', 'meio': 'tela', 'em': '2026-11-06T10:00:00'}
# os glifos da fonte de autoteste em unidades por em (1000): avanco e tinta de cada um (vapt.render.autoteste)
AVANCOS = tp.AVANCOS
EM = 1000.0  # numero-neutro: unidades por em da fonte de autoteste
DUAS_LINHAS = 'HAH\nHOX'
REFLOW = 'H H H'


@pytest.fixture(scope='module')
def modelo(tmp_path_factory):
    """O job de duas linhas (a camada de pixels do tamanho da tinta do texto, a previa e o render no mesmo lugar)."""
    from vapt.job import nucleo
    from vapt.render import autoteste
    base = tmp_path_factory.mktemp('texto-editado')
    fontes = base / 'origem-fontes'
    fap.gravar(fontes, 'autoteste.ttf', autoteste.gerar_fonte())
    job = base / 'job'
    nucleo.criar(job, tp._psd_duas_linhas(base / 'origem' / 'kv.psd', autoteste.NOME_PS), 'c', fontes=[fontes])
    r = nucleo.proxima(job, todas=True)
    assert r.codigo == 0, (r.situacao, r.linhas_humanas)
    laudo = contratos.ler(job / mb.ARQUIVO_LAUDO, 'laudo/1')
    ids = {c['nome']: c['identidade']['layer_id'] for c in laudo['camadas']}
    funcoes = {ids['fundo-sintetico']: 'fundo', ids['duas-linhas']: 'titulo', ids['quadrado-sintetico']: 'logo_principal'}
    b = ap.briefing(funcoes=funcoes, formatos=[ap.formato(i, w, h, rotacao=ROT0) for i, w, h in tp.FORMATOS_DUAS])
    b.pop('cabecalho')
    b.pop('job_id')
    arq = base / 'fixture.json'
    arq.write_text(json.dumps(b), encoding='utf-8')
    mb.importar_teste(job, arq)
    return {'job': job, 'layer_id': ids['duas-linhas']}


@pytest.fixture
def job(modelo, tmp_path):
    destino = tmp_path / 'job'
    shutil.copytree(modelo['job'], destino)
    return destino


def _familia_de(conteudo, fid):
    return next(g for g, f in conteudo['familias'].items() if fid in f['formatos'])


def _titulo(conteudo, gid):
    base = conteudo['editar']({'familia': gid, 'versao': None, 'edicoes': []})
    return next(e['id'] for e in base['membros'][0]['palco']['elementos'] if e['funcao'] == 'titulo')


def _editar(job, texto, fid='mesma', versao=None, edicoes=None):
    """Grava o briefing do DA com o texto editado na familia de fid (as outras confirmadas sem edicao) e deriva."""
    conteudo = te.montar(job)
    gid = _familia_de(conteudo, fid)
    el = _titulo(conteudo, gid)
    comps = []
    for g, f in conteudo['familias'].items():
        ed = (edicoes if edicoes is not None else [{'elemento': el, 'acao': 'texto', 'texto': texto}]) if g == gid else []
        comps.append({'familia': g, 'formatos': f['formatos'], 'versao': versao if g == gid else None, 'edicoes': ed,
                      'confirmada': True, 'confirmacao': dict(CONF)})
    b = contratos.ler(job / mb.ARQUIVO, 'briefing/1')
    b['cabecalho'].update(origem='da', meio='terminal')
    b['composicoes'] = comps
    contratos.gravar(job / mb.ARQUIVO, b, 'briefing/1')
    nd.derivar(job)
    return el


def _deriv(job, fid):
    return contratos.ler(job / nd.PASTA / ('%s.json' % fid), nd.ESQUEMA)


def _entrada_editada(contrato, layer_id):
    return next(e for e in contrato['entradas'] if e['tipo'] == 'texto' and e['layer_id'] == layer_id)


def _linhas(entrada):
    return [''.join(s for s, _r in ln['pedacos']) for ln in rt.linhas_da_camada(
        entrada['texto'], set(entrada.get('quebras_automaticas') or ()), entrada.get('quebras_juntadas'))]


# ------------------------------------------------------------------ derivacao e contrato
def test_derivacao_nao_junta_as_quebras_da_proposta_ao_texto_editado(job, modelo):
    # sem edicao, a familia leva as quebras aprovadas da proposta derivada (o titulo de duas linhas)
    el = _editar(job, None, edicoes=[])
    antes = next(e for e in _deriv(job, 'mesma')['elementos'] if e['id'] == el)
    _editar(job, DUAS_LINHAS)
    d = _deriv(job, 'mesma')
    x = next(e for e in d['elementos'] if e['id'] == el)
    assert x['texto_editado'] == DUAS_LINHAS and x['origem_geometria'] == 'da'
    # o texto do DA leva so as quebras dele: nenhuma quebra da proposta fica no elemento editado
    assert antes['quebras'] != 'do_texto_editado'
    assert x['quebras'] == 'do_texto_editado' and 'quebras_camada' not in x, x.get('quebras')


def test_contrato_leva_o_texto_editado_do_kv_de_uma_cor_num_trecho_so(job, modelo):
    # o PSD de duas linhas tem uma cor e um estilo: a regra R3 (214) junta tudo num trecho so, como antes
    el = _editar(job, DUAS_LINHAS)
    contrato, bloqueios, _c = rd.montar(job, 'mesma')
    assert bloqueios == [], bloqueios
    e = _entrada_editada(contrato, modelo['layer_id'])
    assert e['texto_editado'] is True and e['elemento'] == el
    assert [r['texto'] for r in e['texto']['runs']] == [DUAS_LINHAS]
    assert e['texto']['runs'][0]['inicio'] == 0 and e['texto']['runs'][0]['fim'] == len(DUAS_LINHAS)
    assert list(e['cores_por_trecho']) == ['0'] and e['cores'] == [e['cores_por_trecho']['0']]
    assert 'quebras_juntadas' not in e and 'quebras_inseridas' not in e
    # Linhas do DA (0.9.4): sem largura de quebra; a caixa validada e a tinta medida na derivacao, e a pagina a cobre
    # com folga (a tinta alem dela e conferida depois de compor, nunca cortada calada)
    assert 'largura_quebra' not in e and e['linhas_do_da'] is True
    x = next(y for y in _deriv(job, 'mesma')['elementos'] if y['id'] == el)
    assert e['caixa_validada'] == pytest.approx(x['caixa_texto_editado'], abs=0.01)
    W, H = contrato['formato']['largura'], contrato['formato']['altura']
    r, cv = e['regiao'], e['caixa_validada']
    assert 0 <= r[0] <= cv[0] and 0 <= r[1] <= cv[1] and cv[2] <= r[2] <= W and cv[3] <= r[3] <= H, (r, cv)
    assert any(r['codigo'] == 'texto_editado_desenhado' and r['layer_id'] == modelo['layer_id']
               for r in contrato['registros'])
    contratos.validar(contrato, 'composicao/1')
    # o texto vale so na familia editada (171): o outro formato desenha o texto do KV
    outro, b2, _c2 = rd.montar(job, 'perto')
    assert b2 == [] and not _entrada_editada(outro, modelo['layer_id']).get('texto_editado')


def test_caractere_fora_do_cmap_e_recusado_no_contrato(job, modelo):
    # o briefing que chega sem passar pela tela (arquivo mexido) tambem e conferido: a fonte de autoteste nao tem o Ç
    el = _editar(job, 'HAÇ\nHOX')
    contrato, bloqueios, _c = rd.montar(job, 'mesma')
    assert contrato is None
    assert [b['codigo'] for b in bloqueios] == ['texto_editado_fora_da_fonte']
    assert bloqueios[0]['medidas'] == {'elementos': [el], 'caracteres': ['Ç']}
    texto = bloqueios[0]['descricao']
    assert 'fonte' in texto and '—' not in texto and '–' not in texto


def test_texto_editado_sem_bloqueio_antigo():
    assert 'texto_editado_sem_render' not in rd.DESCRICOES


# ------------------------------------------------------------------ duas cores (decisoes-v1.md, 214; regra R3)
PRETO_E_AZUL = {'c0': {'rgb': [0.0, 0.0, 0.0], 'alfa': 1.0}, 'c1': {'rgb': [0.0, 0.2, 0.9], 'alfa': 1.0}}
FACE_X = {'id': 'f01', 'peso_declarado': 700, 'metricas': None}


def _run(inicio, texto, **extra):
    r = {'inicio': inicio, 'fim': inicio + len(texto), 'texto': texto, 'fonte_ps': 'X', 'corpo_espaco_texto': 20,
         'tracking': 0, 'entrelinha': 24, 'autoleading': False, 'font_caps': None, 'autokerning': True,
         'kerning': None, 'ligaduras': True, 'tem_tinta': True, 'faux_bold': False}
    r.update(extra)
    return r


def _entrada_tres_linhas():
    """O KV do relato: tres linhas, as duas primeiras pretas e a ultima azul, como o contrato do render as leva (a cor
    fora do run, em cores_por_trecho)."""
    runs = [_run(0, 'L1 a\rL2 b\r'), _run(10, 'L3 c')]
    return {'id': 'e01', 'regiao': [0, 0, 128, 96],
            'texto': {'matriz': [1, 0, 0, 1, 2, 20], 'runs': runs,
                      'paragrafos': [{'inicio': 0, 'fim': 15, 'justificacao': 'LEFT'}]},
            'cores': ['c0', 'c1'], 'cores_por_trecho': {'0': 'c0', '10': 'c1'}, 'valores_cor': dict(PRETO_E_AZUL),
            'faces': {'X': 'f01'}, 'largura_quebra': 50.0}


def _por_cor(novo):
    return [(r['texto'], novo['cores_por_trecho'][str(r['inicio'])]) for r in novo['texto']['runs']]


@pytest.mark.parametrize('texto, esperado', [
    # so a quebra mudou (pelo campo de texto, CR LF ou CR viram LF): cada caractere com a cor dele
    ('L1 a\nL2 b\nL3 c', [('L1 a\nL2 b\n', 'c0'), ('L3 c', 'c1')]),
    ('L1 a\r\nL2 b\r\nL3 c', [('L1 a\nL2 b\n', 'c0'), ('L3 c', 'c1')]),
    # juntar as linhas 2 e 3: o espaco no lugar da quebra herda o preto da esquerda
    ('L1 a\nL2 b L3 c', [('L1 a\nL2 b ', 'c0'), ('L3 c', 'c1')]),
    # trocar a palavra azul: a nova fica azul
    ('L1 a\nL2 b\nL3 xyz', [('L1 a\nL2 b\n', 'c0'), ('L3 xyz', 'c1')]),
    # palavra nova no comeco da linha azul: herda a da direita
    ('L1 a\nL2 b\nnova L3 c', [('L1 a\nL2 b\n', 'c0'), ('nova L3 c', 'c1')]),
])
def test_texto_editado_de_duas_cores_leva_a_cor_de_cada_trecho(texto, esperado):
    entrada = _entrada_tres_linhas()
    novo = rd.texto_editado_na_entrada(entrada, texto)
    assert _por_cor(novo) == esperado
    runs = novo['texto']['runs']
    assert [(r['inicio'], r['fim']) for r in runs] == [(0, len(esperado[0][0])),
                                                       (len(esperado[0][0]), len(esperado[0][0] + esperado[1][0]))]
    assert all('cor' not in r and r['kerning'] is None and r['tem_tinta'] for r in runs)
    assert sorted(novo['cores_por_trecho']) == sorted(str(r['inicio']) for r in runs)
    assert novo['cores'] == ['c0', 'c1'] and novo['valores_cor'] == PRETO_E_AZUL and novo['faces'] == {'X': 'f01'}
    s = ''.join(r['texto'] for r in runs)
    assert novo['texto']['paragrafos'] == [{'inicio': 0, 'fim': len(s) + 1, 'justificacao': 'LEFT'}]
    assert 'largura_quebra' not in novo and novo['linhas_do_da'] is True and novo['texto_editado'] is True
    # a entrada do contrato fica como estava
    assert entrada == _entrada_tres_linhas()


def test_texto_editado_com_quebra_da_familia_pinta_como_a_tela_e_a_medida():
    # a R3 roda nas linhas finais (a familia junta a 2a quebra): a palavra nova fica na linha do 'b' e herda o preto
    # da esquerda, como em linhas_editadas na tela e na medida; os trechos levam o texto sem a quebra da familia,
    # que o render aplica depois (quebras_do_texto_editado)
    texto = 'L1 a\nL2 b\nNOVO L3 c'
    item = {'aprovadas': [0], 'inseridas': []}
    novo = rd.texto_editado_na_entrada(_entrada_tres_linhas(), texto, item)
    assert _por_cor(novo) == [('L1 a\nL2 b\nNOVO ', 'c0'), ('L3 c', 'c1')]
    kv = [dict(r, cor=c) for r, c in zip(_entrada_tres_linhas()['texto']['runs'], ('c0', 'c1'))]
    finais = mq.runs_do_editado(kv, mq.linhas_editadas(texto, item), '\n')
    assert [(r['inicio'], r['fim'], r['cor']) for r in finais] == \
        [(r['inicio'], r['fim'], novo['cores_por_trecho'][str(r['inicio'])]) for r in novo['texto']['runs']]
    # sem a quebra da familia, a palavra nova no comeco da linha azul herda a da direita
    assert _por_cor(rd.texto_editado_na_entrada(_entrada_tres_linhas(), texto)) == \
        [('L1 a\nL2 b\n', 'c0'), ('NOVO L3 c', 'c1')]


def test_texto_editado_so_com_cores_usadas_e_faces_de_todos_os_trechos():
    # o texto todo preto (a palavra azul apagada) leva so a cor preta; a face de cada trecho usado entra
    entrada = _entrada_tres_linhas()
    entrada['texto']['runs'][1]['fonte_ps'] = 'Y'
    entrada['faces']['Y'] = 'f02'
    novo = rd.texto_editado_na_entrada(entrada, 'L1 a\nL2 b')
    assert _por_cor(novo) == [('L1 a\nL2 b', 'c0')]
    assert novo['cores'] == ['c0'] and list(novo['valores_cor']) == ['c0'] and novo['faces'] == {'X': 'f01'}
    novo = rd.texto_editado_na_entrada(entrada, 'L1 a L2 b L3 c')
    assert novo['cores'] == ['c0', 'c1'] and novo['faces'] == {'X': 'f01', 'Y': 'f02'}
    assert [r['fonte_ps'] for r in novo['texto']['runs']] == ['X', 'Y']


def test_texto_editado_de_uma_cor_sai_como_antes():
    # o KV de uma cor (o kerning manual parte o run no Photoshop; a quebra do fim pode ter outra cor e nao ter tinta):
    # um trecho so, com o estilo do primeiro trecho com tinta, como antes da R3
    runs = [_run(0, 'HA', kerning=-20), _run(2, 'H\rHOX'), _run(7, '\r', tem_tinta=False)]
    entrada = {'id': 'e01', 'regiao': [0, 0, 128, 96],
               'texto': {'matriz': [1, 0, 0, 1, 2, 20], 'runs': runs,
                         'paragrafos': [{'inicio': 0, 'fim': 8, 'justificacao': 'CENTER'}]},
               'cores': ['c0', 'c1'], 'cores_por_trecho': {'0': 'c0', '2': 'c0', '7': 'c1'},
               'valores_cor': dict(PRETO_E_AZUL), 'faces': {'X': 'f01'}}
    for texto in (DUAS_LINHAS, 'HAH HOX', REFLOW, 'HAH\nHOX\nHAX'):
        novo = rd.texto_editado_na_entrada(entrada, texto)
        assert novo['texto']['runs'] == [dict(runs[0], inicio=0, fim=len(texto), texto=texto, kerning=None,
                                              tem_tinta=True)]
        assert novo['cores'] == ['c0'] and novo['cores_por_trecho'] == {'0': 'c0'}
        assert novo['valores_cor'] == {'c0': PRETO_E_AZUL['c0']} and novo['faces'] == {'X': 'f01'}


def _entrada_cr_do_meio():
    # o KV preto na vista com a quebra do meio num run sem tinta azul, numa fonte que nao esta no job (Y), com outro
    # corpo e outra entrelinha
    runs = [_run(0, 'HAH'), _run(3, '\r', fonte_ps='Y', corpo_espaco_texto=40, entrelinha=60, tem_tinta=False),
            _run(4, 'HOX')]
    return {'id': 'e01', 'regiao': [0, 0, 128, 96],
            'texto': {'matriz': [1, 0, 0, 1, 2, 20], 'runs': runs,
                      'paragrafos': [{'inicio': 0, 'fim': 8, 'justificacao': 'LEFT'}]},
            'cores': ['c0', 'c1'], 'cores_por_trecho': {'0': 'c0', '3': 'c1', '4': 'c0'},
            'valores_cor': dict(PRETO_E_AZUL), 'faces': {'X': 'f01'}}


@pytest.mark.parametrize('texto', ['HAH HOX', 'HAH\nHOX', 'HAH novo HOX'])
def test_cr_do_meio_sem_tinta_de_outra_cor_e_fonte_nao_vira_trecho(texto):
    # so a face X e desenhada, preta, em todo caractere; a quebra que vira espaco (ou fica fora do par, com a palavra
    # inserida) herda o vizinho e o texto editado sai num trecho so, com o espaco desenhado
    entrada = _entrada_cr_do_meio()
    runs = entrada['texto']['runs']
    novo = rd.texto_editado_na_entrada(entrada, texto)
    assert novo['faces'] == {'X': 'f01'}
    _svg, _spans, linhas = rt.montar_svg(novo, {'X': FACE_X}, 'p')
    assert [c for ln in linhas.values() for c in ln] == ['c0'] * len(texto.replace('\n', ''))
    assert rd.caracteres_fora_da_face(novo, [{'id': 'f01', 'cmap': [[32, 32], [65, 90], [97, 122]]}]) == []
    if '\n' not in texto:
        assert novo['texto']['runs'] == [dict(runs[0], inicio=0, fim=len(texto), texto=texto, kerning=None,
                                              tem_tinta=True)]
        assert novo['cores'] == ['c0'] and novo['cores_por_trecho'] == {'0': 'c0'}
        return
    # rodada 4 (_no_mesmo_papel): a quebra que continua quebra guarda o run sem tinta dela (um run so de '\n', sem
    # tinta, com a cor, a fonte e a entrelinha do KV); ela nao e desenhada, e a linha 1 fica com a entrelinha do KV
    assert novo['texto']['runs'] == [dict(runs[0], kerning=None), dict(runs[1], texto='\n', kerning=None),
                                     dict(runs[2], kerning=None)]
    assert novo['cores'] == ['c0', 'c1'] and novo['cores_por_trecho'] == {'0': 'c0', '3': 'c1', '4': 'c0'}
    kv = rt.linhas_da_camada(entrada['texto'])
    assert [ln['entrelinha'] for ln in rt.linhas_da_camada(novo['texto'])] == [ln['entrelinha'] for ln in kv]
    assert [ln['entrelinha'] for ln in kv][0] == 60  # numero-neutro: a entrelinha do run sem tinta


def test_svg_do_texto_editado_de_duas_cores_pinta_o_azul_nos_caracteres_dele():
    novo = rd.texto_editado_na_entrada(_entrada_tres_linhas(), 'L1 a\nL2 b L3 c')
    svg, spans, linhas = rt.montar_svg(novo, {'X': FACE_X}, 'p')
    # cada linha num tspan so (os trechos so mudam de cor), e a cor por caractere
    assert linhas == {'L0': ['c0'] * 4, 'L1': ['c0'] * 5 + ['c1'] * 4}
    assert svg.count('<tspan') == 2 and len(spans) == 2
    pos = {'L0': [[10 * k, 0, 10 * k + 9] for k in range(4)], 'L1': [[10 * k, 0, 10 * k + 9] for k in range(9)]}
    azul, _s, _l = rt.montar_svg(novo, {'X': FACE_X}, 'p', 'c1', pos)
    # na passada azul, a linha preta fica transparente e a linha 2 leva o gradiente na fronteira
    assert 'url(#gL1)' in azul and '<linearGradient id="gL1"' in azul and 'gL0' not in azul
    paginas = rt.paginas_da_entrada(novo, {'X': FACE_X}, [FACE_X], 'p')
    assert len(paginas) == 1 and paginas[0]['posicoes'] and not paginas[0]['pdf']
    assert [p['cor'] for p in rt.paginas_de_cor(novo, {'X': FACE_X}, [FACE_X], 'p', pos)] == ['c0', 'c1']


def test_caracteres_fora_da_face_confere_cada_trecho_na_sua_face():
    entrada = {'texto': {'runs': [_run(0, 'AC', fonte_ps='X'), _run(2, 'ac', fonte_ps='Y', font_caps='ALL_CAPS'),
                                  _run(4, 'Z', fonte_ps='W')]},
               'faces': {'X': 'f01', 'Y': 'f02'}}
    faces_do_job = [{'id': 'f01', 'cmap': [[65, 66]]}, {'id': 'f02', 'cmap': [[97, 99]]}]
    # X nao tem o C; Y so tem minusculas e o trecho e caixa alta (o C ja contado sai uma vez so); W nao tem face no job
    assert rd.caracteres_fora_da_face(entrada, faces_do_job) == ['C', 'A']
    entrada['texto']['runs'][1]['font_caps'] = None
    assert rd.caracteres_fora_da_face(entrada, faces_do_job) == ['C']


def test_tinta_do_texto_editado_cortada_na_borda_do_formato_reprova():
    e = {'id': 'e01', 'tipo': 'texto', 'layer_id': 7, 'regiao': [0, 0, 100, 50], 'caixa_validada': [0, 0, 100, 50],
         'texto_editado': True}
    st = {'id': 'e01', 'tipo': 'texto', 'tinta': [10, 10, 100, 40], 'toca_regiao': ['dir']}
    assert [x['cortada_na_regiao'] for x in rd.tinta_fora_da_caixa([e], [st], 100, 50)] == [['dir']]
    assert rd.tinta_fora_da_caixa([e], [dict(st, toca_regiao=[])], 100, 50) == []


# ------------------------------------------------------------------ no Chromium: as linhas
def _texto_no_chromium(job, contrato):
    estado = contratos.ler(job / 'estado.json', 'estado/1')
    servidos = execucao.bytes_das_faces(job, contrato, estado)
    return execucao.texto_no_chromium(contrato, servidos, 'dsd-teste')


def _avanco(s, corpo):
    return sum(AVANCOS[c] for c in s) / EM * corpo


def test_texto_com_quebra_sai_exatamente_nas_linhas_pedidas(job, modelo):
    _editar(job, DUAS_LINHAS)
    contrato, _b, _c = rd.montar(job, 'mesma')
    pdfs, paginas, cdp, _cache, _v = _texto_no_chromium(job, contrato)
    e = _entrada_editada(contrato, modelo['layer_id'])
    assert _linhas(e) == ['HAH', 'HOX']
    assert cdp['diverge'] == 0 and cdp['faces_nao_carregadas'] == 0
    assert any(p['entrada'] == e['id'] for p in paginas)


def test_linha_mais_larga_que_a_caixa_fica_numa_linha_so(job, modelo):
    # Linhas do DA (0.9.4; antes a terceira palavra descia na largura da caixa): o texto editado nunca quebra sozinho
    el = _editar(job, REFLOW)
    contrato, bloqueios, _c = rd.montar(job, 'mesma')
    assert bloqueios == [], bloqueios
    e = _entrada_editada(contrato, modelo['layer_id'])
    corpo = e['texto']['runs'][0]['corpo_espaco_texto']
    laudo = contratos.ler(job / mb.ARQUIVO_LAUDO, 'laudo/1')
    ct = mb.camadas_do_laudo(laudo)[modelo['layer_id']]['geometria']['caixa_tinta']
    # a linha passa da largura da caixa de tinta do KV no espaco do texto, com o mesmo corpo
    assert _avanco(REFLOW, corpo) > (ct[2] - ct[0]) / tp.ESCALA_DUAS
    x = next(y for y in _deriv(job, 'mesma')['elementos'] if y['id'] == el)
    tinta_kv = rd._caixa(x['transformacao'], ct)
    cx = x['caixa_texto_editado']
    assert cx[2] - cx[0] > tinta_kv[2] - tinta_kv[0]
    # uma linha so: a caixa fica mais baixa que a tinta das duas linhas do KV
    assert cx[3] - cx[1] < tinta_kv[3] - tinta_kv[1]
    _texto_no_chromium(job, contrato)
    assert _linhas(e) == [REFLOW] and not e.get('quebras_automaticas')


# ------------------------------------------------------------------ a quebra de linha da familia (M7b, C2)
def _com_quebra(job, modelo, texto, manter=(), inseridas=(), fid='mesma'):
    """Grava o briefing do DA com a quebra de linha da familia de fid (feita pelo DA) e, com texto, o texto editado
    nela; as outras familias confirmadas sem edicao. Deriva. Devolve (elemento, formatos da familia)."""
    conteudo = te.montar(job)
    gid = _familia_de(conteudo, fid)
    el = _titulo(conteudo, gid)
    comps = []
    for g, f in conteudo['familias'].items():
        ed = [{'elemento': el, 'acao': 'texto', 'texto': texto}] if g == gid and texto is not None else []
        comps.append({'familia': g, 'formatos': f['formatos'], 'versao': None, 'edicoes': ed, 'confirmada': True,
                      'confirmacao': dict(CONF)})
    membros = list(conteudo['familias'][gid]['formatos'])
    b = contratos.ler(job / mb.ARQUIVO, 'briefing/1')
    b['cabecalho'].update(origem='da', meio='terminal')
    b['composicoes'] = comps
    b['quebras_por_familia'] = [{'layer_id': modelo['layer_id'], 'familia': gid, 'formatos': membros,
                                 'quebras': ap.decisao(list(manter)), 'inseridas': list(inseridas), 'origem': 'da',
                                 'aprovada': True}]
    contratos.gravar(job / mb.ARQUIVO, b, 'briefing/1')
    nd.derivar(job)
    return el, membros


@pytest.mark.skipif(sys.platform != 'win32', reason='o isolador dos filhos roda no Windows')
def test_quebra_da_familia_junta_as_linhas_do_kv_em_todo_membro(job, modelo, monkeypatch):
    el, membros = _com_quebra(job, modelo, None, manter=())
    for fid in membros:
        d = _deriv(job, fid)
        assert d['situacao'] == 'derivado', d['devolucao']
        x = next(e for e in d['elementos'] if e['id'] == el)
        assert x['quebras_origem'] == 'da' and x['origem_geometria'] == 'da'
        [item] = x['quebras']['familia']
        assert item['layer_id'] == modelo['layer_id'] and item['aprovadas'] == [] and item['inseridas'] == []
        assert len(item['caixa_doc']) == 4
    # o formato de fora da familia fica com as quebras do KV
    for fid in {f for f, _w, _h in tp.FORMATOS_DUAS} - set(membros):
        x = next(e for e in _deriv(job, fid)['elementos'] if e['id'] == el)
        assert 'quebras_origem' not in x
    contrato, bloqueios, _c = rd.montar(job, 'mesma')
    assert bloqueios == [], bloqueios
    e = _entrada_editada(contrato, modelo['layer_id'])
    assert e['quebras_juntadas'] == [len(tp.LINHAS_DUAS[0])] and not e.get('texto_editado')
    assert rt.linhas_desenhadas(e) == [' '.join(tp.LINHAS_DUAS)]
    # o render inteiro: a tinta da linha juntada cabe na caixa que a derivacao mediu (tinta_fora_da_caixa_validada)
    monkeypatch.setattr(humano, 'console_interativo', lambda: (True, None))
    rel = execucao.renderizar(job, disparo=humano.exigir('render'), formato='mesma', aceites=('largura_divergente',))
    assert rel['derivacao']['impressao_formato'] == _deriv(job, 'mesma')['impressao_formato']


def test_quebra_da_familia_no_texto_editado_sai_nas_linhas_do_da(job, modelo):
    # o texto editado de tres palavras: sem a quebra do DA, as duas primeiras cabem na caixa e a terceira desce
    el, membros = _com_quebra(job, modelo, REFLOW, manter=(), inseridas=(1,))
    for fid in membros:
        x = next(e for e in _deriv(job, fid)['elementos'] if e['id'] == el)
        assert x['texto_editado'] == REFLOW and x['quebras_origem'] == 'da' and x['origem_geometria'] == 'da'
        assert x['quebras'] == {'familia': [{'layer_id': modelo['layer_id'], 'aprovadas': [], 'inseridas': [1]}]}
    contrato, bloqueios, _c = rd.montar(job, 'mesma')
    assert bloqueios == [], bloqueios
    e = _entrada_editada(contrato, modelo['layer_id'])
    assert e['texto_editado'] is True and e['quebras_inseridas'] == [1] and e['quebras_juntadas'] == []
    _texto_no_chromium(job, contrato)
    palavra = REFLOW.split(' ')[0]
    assert rt.linhas_desenhadas(e) == [palavra, palavra + ' ' + palavra]


# ------------------------------------------------------------------ o render e a previa da tela
@pytest.mark.skipif(sys.platform != 'win32', reason='o isolador dos filhos roda no Windows')
def test_tinta_do_render_bate_com_a_previa_da_tela(job, modelo, monkeypatch):
    from playwright.sync_api import sync_playwright

    import test_tela_edicao as ted
    import test_tela_galeria as tg
    from vapt.chromium import navegador
    from vapt.tela import atos as ta
    from vapt.tela import rascunho as tr
    from vapt.tela import servidor as ts
    conteudo = te.montar(job)
    gid = _familia_de(conteudo, 'mesma')
    el = _titulo(conteudo, gid)
    navegador.apontar_playwright()
    with ts.ServidorTela(conteudo, pasta=job, modo_teste=True,
                         atos=ta.atos_do_job(job, conteudo=conteudo)) as srv, sync_playwright() as pw:
        nav, pg = tp._pagina_da_tela(pw, srv, 1600, 900)  # numero-neutro: janela do teste
        try:
            tg._abrir(pg, conteudo['estado'], 'mesma')
            ted._focar(pg, el)
            pg.keyboard.press('Enter')
            pg.evaluate('() => document.getElementById("ed-texto").click()')
            pg.fill('#ed-campo-texto', DUAS_LINHAS)
            pg.evaluate('() => document.getElementById("ed-texto-aplicar").click()')
            tp._esperar(pg, '() => document.getElementById("editor-texto").hidden ? "1" : ""')
            ted._esperar_salvo(pg)
            tp._esperar(pg, '() => (document.querySelector("#palco .texto.editado") || {dataset: {}}).dataset'
                            '.caixaTinta ? "1" : ""')
            previa = [float(x) for x in pg.evaluate(
                '() => document.querySelector("#palco .texto.editado").dataset.caixaTinta').split(',')]
            linhas_previa = pg.evaluate('() => Array.from(document.querySelectorAll("#palco .texto.editado .linha"))'
                                        '.map(l => l.textContent)')
        finally:
            nav.close()
    assert linhas_previa == DUAS_LINHAS.split('\n')
    f = json.loads((job / tr.ARQUIVO).read_text(encoding='utf-8'))['familias'][gid]
    assert [x['texto'] for x in f['edicoes'] if x['acao'] == 'texto'] == [DUAS_LINHAS]
    _editar(job, None, versao=f['versao'], edicoes=f['edicoes'])
    monkeypatch.setattr(humano, 'console_interativo', lambda: (True, None))
    # a caixa TySh do PSD sintetico nao confere com a largura da fonte de autoteste: decisao do DA, aceita no teste
    rel = execucao.renderizar(job, disparo=humano.exigir('render'), formato='mesma', aceites=('largura_divergente',))
    contrato = contratos.ler(job / 'render' / 'mesma' / 'contrato.json', 'composicao/1')
    e = _entrada_editada(contrato, modelo['layer_id'])
    assert [x['linhas'] for x in rel['textos']['editados'] if x['entrada'] == e['id']] == [DUAS_LINHAS.split('\n')]
    tinta = next(s['tinta'] for s in rel['entradas'] if s['id'] == e['id'])
    # a tolerancia da tinta do texto do render (render.tolerancia_tinta_texto, com o piso em px): a mesma que confere
    # a tinta contra a caixa validada
    tol = rd._tolerancia_tinta(previa)
    assert tinta == pytest.approx(previa, abs=tol), (tinta, previa, tol)
    # o render nao tirou nada da pagina: a tinta nao encosta na borda do formato
    assert rel['textos']['camadas'] >= 1 and all(s['toca_regiao'] == [] for s in rel['entradas'] if s['id'] == e['id'])
