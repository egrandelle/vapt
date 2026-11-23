# -*- coding: utf-8 -*-
"""Medida das linhas juntadas das quebras aprovadas por familia (revisao 3 do M5).

O mesmo caminho da conferencia de fontes (fontes.conferencia e fontes.medicao): a pagina de medida com uma linha por
quebra que fica, cada trecho com a face do job servida pelo motor (o processo principal so copia os bytes que o filho
leu; nunca abre a fonte), medida no Chromium fixado. Para cada texto e cada conjunto de quebras aprovado, a pagina leva
o texto da mestre e o texto juntado; a medida e a linha mais larga dos dois, no espaco de texto, sem o espacamento do
ultimo caractere (como o Photoshop). A quebra da familia da tela (M7b, C2) tambem insere quebra nos espacos: o texto
juntado leva as duas. A quebra da familia cujas posicoes nao cabem no texto do KV (a do texto editado pelo DA na
familia, que o render quebra sem medida) fica sem medir.

Medida ao vivo, com cache (M7b, C3): a medida de cada texto com as suas quebras fica guardada no processo, pela
chave da medida (chave_da_medida: a camada do laudo, as quebras que ficam, as inseridas e as faces servidas, que sao
tudo o que a pagina de medida le). A segunda medida igual nao abre o Chromium, e so o texto cuja quebra mudou vai a
pagina. A previa da tela (vapt.tela.edicao) e a derivacao gravada passam por medir, entao usam a mesma medida. A
medida que falhou (Chromium que nao abriu, face ausente, sem largura) nao fica guardada: o proximo pedido tenta de
novo. O cache guarda ate CACHE_MAX medidas; a mais antiga sai primeiro.

Chromium aberto da tela (M7b, C3): com a tela aberta, o processo dela liga um vapt.chromium.aberto.NavegadorAberto
(usar_aberto), e a medida sem cache vai a ele: o Chromium fica aberto entre as medidas, e cada medida roda num
contexto sem perfil, com as mesmas linhas de medida do caminho frio. Quando o aberto nao mede (fechado, sem amarra,
caiu ou passou do teto), o pedido sai pelo caminho frio, o de sempre: o Chromium fixado abre com um perfil novo,
mede e fecha. Fora da tela (a CLI e a derivacao), nada fica ligado e toda medida e a do caminho frio.

Devolve {chave: {'largura_texto', 'largura_texto_mestre', 'linhas'}} ou, quando nao mede, {chave: {'erro': motivo}}.

O texto editado pelo DA (Linhas do DA, 0.9.4) passa pela mesma pagina e pelo mesmo cache em medir_editados: a tinta
das linhas do DA, com o mesmo corpo, da a caixa do texto editado (derivacao.quebras.caixa_do_editado).

O alinhamento das linhas escolhido pelo DA (0.12.0) passa pela mesma pagina: a medida nao depende da justificacao, e
dela saem o desvio da ancora (a linha mais larga fica no lugar; fontes.medicao.bloco_das_linhas e
derivacao.quebras.desvio) e a tinta com a justificacao nova. No texto editado, medir_editados recebe a justificacao no
pedido; no texto do KV, medir_alinhados mede com as quebras que o render aplica. A justificacao entra na chave do
cache e na chave da saida: a mesma linha em outro alinhamento e outra medida.
"""
import copy
import hashlib
import json
import threading
from collections import OrderedDict
from pathlib import Path

from vapt import arquivos, contratos
from vapt.briefing import modelo as mb
from vapt.chromium import navegador, servidor
from vapt.derivacao import quebras as mq
from vapt.fontes import casamento, conferencia, medicao

PERFIL = 'medida-quebras'
CACHE_MAX = 512  # numero-neutro: medidas guardadas no processo (cada uma e um dicionario pequeno)
INTERVALO_SERVIDOR_ABERTO_S = 0.01  # numero-neutro: intervalo de consulta do servidor da pagina, so com o aberto

_cache = OrderedDict()
_trava = threading.Lock()
_aberto = None  # o Chromium aberto da tela (vapt.chromium.aberto), ligado so pelo processo da tela


def usar_aberto(aberto):
    """Liga o Chromium aberto da tela na medida sem cache, ou desliga com None (o fecho da tela)."""
    global _aberto
    with _trava:
        _aberto = aberto


def limpar_cache():
    """Esquece as medidas guardadas (os testes e a medicao de latencia sem cache)."""
    with _trava:
        _cache.clear()


def chave_da_medida(camada, manter, inseridas, faces, espaco=None):
    """A chave do cache: o sha256 do texto canonico da camada do laudo, das quebras que ficam, das inseridas e das
    faces servidas [(id, sha256)]. Mudar qualquer um muda a chave. espaco separa as medidas de outra forma: o texto
    editado (medir_editados) guarda a caixa da tinta, e a camada sintetica dele pode ser igual a camada do laudo com
    todas as quebras juntas; sem o espaco, a medida de uma serviria a outra (revisao 0.9.4)."""
    dados = {'camada': camada, 'manter': sorted(int(x) for x in manter),
             'inseridas': sorted(int(x) for x in inseridas), 'faces': sorted([str(i), str(s)] for i, s in faces)}
    if espaco is not None:
        dados['espaco'] = str(espaco)
    texto = json.dumps(dados, sort_keys=True, ensure_ascii=False, separators=(',', ':'), default=str)
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()


def _guardada(chave):
    with _trava:
        medida = _cache.get(chave)
        if medida is None:
            return None
        _cache.move_to_end(chave)
        return copy.deepcopy(medida)


def _guardar(chave, medida):
    with _trava:
        _cache[chave] = copy.deepcopy(medida)
        _cache.move_to_end(chave)
        while len(_cache) > CACHE_MAX:
            _cache.popitem(last=False)


def _faces(pasta, estado):
    leituras, por_sha = [], {}
    for rel, reg in sorted(estado['entradas'].items()):
        if not rel.startswith(conferencia.PASTA_ENTRADA):
            continue
        arq = Path(pasta) / 'fontes' / 'bruto' / reg['sha256'] / 'leitura.json'
        if arq.is_file():
            leitura = contratos.ler(arq, 'leitura-fonte/1')
            if leitura.get('situacao') == 'lida':
                leituras.append((reg['sha256'], leitura))
                por_sha[reg['sha256']] = rel
    return casamento.montar_faces(leituras), por_sha


def _conferir(url_entrada, familias, servidos):
    """A pagina de medida no Chromium aberto da tela, quando ligado; senao, ou quando ele nao mede, no caminho frio
    (navegador.conferir com um perfil novo, apagado no fim)."""
    aberto = _aberto
    if aberto is not None:
        try:
            return aberto.conferir(url_entrada, familias, [], servidos=servidos)
        except navegador.ErroNavegador:
            pass  # este pedido sai pelo caminho frio; o aberto abre de novo no proximo (vapt.chromium.aberto)
    perfil = navegador.perfil_curto() / PERFIL
    try:
        return navegador.conferir(url_entrada, perfil, familias, [])
    finally:
        navegador.apagar_perfil(perfil)


def medir(pasta, laudo, briefing, estado):
    pedidos = mq.pedidos(briefing)
    if not pedidos:
        return {}
    camadas = mb.camadas_do_laudo(laudo)
    saida = {}
    faces, servidos, servidas = _servidos(pasta, estado)
    textos, ordem = [], []
    for lid, manter, inseridas in pedidos:
        c = camadas.get(lid)
        if c is None or c.get('tipo') != 'texto':
            saida[mq.chave(lid, manter, inseridas)] = {'erro': 'camada_sem_texto'}
            continue
        if mq.conferir_da_familia(c, manter, inseridas) is not None:
            continue
        no_cache = chave_da_medida(c, manter, inseridas, servidas)
        guardada = _guardada(no_cache)
        if guardada is not None:
            # a mesma medida de antes, sem abrir o Chromium (M7b, C3)
            saida[mq.chave(lid, manter, inseridas)] = guardada
            continue
        textos.extend([c, mq.com_juntadas(c, manter, inseridas)])
        ordem.append((lid, manter, inseridas, no_cache))
    if not ordem:
        return saida
    pares, plano, larguras, tintas, motivo = _na_pagina(textos, faces, servidos, estado)
    for k, (lid, manter, inseridas, no_cache) in enumerate(ordem):
        ch = mq.chave(lid, manter, inseridas)
        if motivo:
            saida[ch] = {'erro': motivo}
            continue
        mestre, juntado = plano['camadas'][2 * k], plano['camadas'][2 * k + 1]  # numero-neutro: duas camadas por pedido
        if any(pares.get(r.get('fonte_ps')) is None for r in camadas[lid]['texto'].get('runs') or [] if r.get('fonte_ps')):
            saida[ch] = {'erro': 'face_ausente'}
            continue
        _cm, sm = medicao.ler_larguras(mestre, larguras)
        _cj, sj = medicao.ler_larguras(juntado, larguras)
        if not sm or not sj:
            saida[ch] = {'erro': 'sem_medida_do_chromium'}
            continue
        saida[ch] = {'largura_texto_mestre': round(sm, 4), 'largura_texto': round(sj, 4),
                     'linhas': len(juntado['linhas'])}
        just = (camadas[lid].get('texto') or {}).get('justificacao')
        tm = medicao.tinta_do_bloco(mestre, larguras, tintas, just)
        tj = medicao.tinta_do_bloco(juntado, larguras, tintas, just)
        if tm is not None and tj is not None:
            # a tinta de cada linha, para a caixa seguir a do render (derivacao.quebras.caixa_medida)
            saida[ch]['tinta_mestre'] = {k: round(v, 4) for k, v in tm.items()}
            saida[ch]['tinta'] = {k: round(v, 4) for k, v in tj.items()}
        _guardar(no_cache, saida[ch])
    return saida


def _servidos(pasta, estado):
    """(faces, servidos, servidas): as faces do job, os bytes de cada face que o motor serve ao Chromium e os pares
    (id, sha256) delas (a parte das faces na chave do cache)."""
    faces, por_sha = _faces(pasta, estado)
    servidos = {}
    for f in faces:
        rel = por_sha.get(f['sha256'])
        dados = (Path(pasta) / rel).read_bytes() if rel else None
        if dados is None or arquivos.sha256_bytes(dados) != f['sha256']:
            continue
        servir = conferencia.bytes_para_servir(dados, f)
        if servir is not None:
            servidos[f['id']] = (servir, servidor.MIME_POR_FORMATO[f['formato']])
    return faces, servidos, [(f['id'], f['sha256']) for f in faces if f['id'] in servidos]


def _na_pagina(textos, faces, servidos, estado):
    """(pares, plano, larguras, tintas, motivo) da pagina de medida com as camadas textos, no Chromium."""
    pares = {}
    for c in textos:
        for r in c['texto'].get('runs') or []:
            ps = r.get('fonte_ps')
            if ps and ps not in pares:
                pares[ps] = casamento.casar(ps, faces)[0]
    prefixo = 'dsd-%s' % estado['job_id'][:8]  # numero-neutro: prefixo curto do job no nome da familia
    pagina, plano = medicao.montar(textos, pares, faces, prefixo)
    larguras, tintas, motivo = {}, {}, None
    if not servidos:
        motivo = 'sem_face_servivel'
    else:
        # com o aberto ligado, o servidor da pagina para sem a espera de meio segundo do serve_forever, que era quase
        # toda a remedicao no aberto; o caminho frio fica com o servidor de antes
        kw = {'intervalo_s': INTERVALO_SERVIDOR_ABERTO_S} if _aberto is not None else {}
        try:
            with servidor.ServidorFontes(pagina, servidos, **kw) as srv:
                resposta = _conferir(srv.url_entrada, [medicao.familia_css(prefixo, i) for i in servidos],
                                     [d for d, _mime in servidos.values()])
            larguras = resposta.get('larguras') or {}
            tintas = resposta.get('tintas') or {}
        except navegador.ErroNavegador:
            motivo = 'chromium_nao_mediu'
    return pares, plano, larguras, tintas, motivo


def medir_editados(pasta, laudo, estado, pedidos):
    """A caixa da tinta do texto editado pelo DA com as linhas dele (Linhas do DA, 0.9.4). pedidos: [(layer_id,
    linhas)], as linhas como o render as desenha (derivacao.quebras.linhas_editadas). Cada texto vai a pagina de medida
    num trecho so, com o estilo do primeiro trecho com tinta (derivacao.quebras.camada_do_editado), e a caixa sai da
    tinta medida pela ancora do render (derivacao.quebras.caixa_do_editado), no espaco do documento. O mesmo cache da
    medida das quebras: o mesmo texto nao abre o Chromium de novo.
    Devolve {chave_editado: {'caixa_doc': [x0, y0, x1, y1], 'linhas': n}} ou {chave_editado: {'erro': motivo}}."""
    camadas = mb.camadas_do_laudo(laudo)
    saida, ordem, textos = {}, [], []
    faces, servidos, servidas = _servidos(pasta, estado)
    for pedido in pedidos:
        lid, linhas = pedido[0], pedido[1]
        # 0.12.0: o pedido pode levar a justificacao do alinhamento do DA (LEFT, CENTER ou RIGHT)
        nova = pedido[2] if len(pedido) > 2 else None  # numero-neutro: o terceiro campo do pedido
        ch = mq.chave_editado(lid, linhas, nova)
        if ch in saida or any(o[0] == ch for o in ordem):
            continue
        c = camadas.get(lid)
        sint = mq.camada_do_editado(c, linhas) if c is not None and c.get('tipo') == 'texto' else None
        if sint is None:
            saida[ch] = {'erro': 'camada_sem_texto'}
            continue
        no_cache = chave_da_medida(sint, (), (), servidas, espaco='editado' if nova is None else 'editado:' + nova)
        guardada = _guardada(no_cache)
        if guardada is not None:
            saida[ch] = guardada
            continue
        textos.append(sint)
        ordem.append((ch, sint, no_cache, nova))
    if not ordem:
        return saida
    pares, plano, larguras, tintas, motivo = _na_pagina(textos, faces, servidos, estado)
    por_ps = {ps: f for ps, f in pares.items() if f is not None}
    for k, (ch, sint, no_cache, nova) in enumerate(ordem):
        if motivo:
            saida[ch] = {'erro': motivo}
            continue
        r0 = sint['texto']['runs'][0]
        if pares.get(r0.get('fonte_ps')) is None:
            saida[ch] = {'erro': 'face_ausente'}
            continue
        item = plano['camadas'][k]
        par = (sint['texto'].get('paragrafos') or [{}])[0]
        d = None
        if nova is None:
            tinta = medicao.tinta_do_bloco(item, larguras, tintas, par.get('justificacao'))
            caixa = mq.caixa_do_editado(sint, tinta, por_ps)
        else:
            # o alinhamento do DA (0.12.0): a mesma pagina (a medida nao depende da justificacao), a ancora anda o
            # desvio para a linha mais larga ficar no lugar, e a tinta sai pela justificacao nova
            bloco = medicao.bloco_das_linhas(item, larguras, par.get('justificacao'))
            d = mq.desvio(bloco, nova) if bloco is not None else None
            tinta = medicao.tinta_do_bloco(item, larguras, tintas, nova) if d is not None else None
            caixa = mq.caixa_do_editado(mq.camada_alinhada(sint, nova, d), tinta, por_ps) if d is not None else None
        if caixa is None:
            saida[ch] = {'erro': 'sem_medida_do_chromium'}
            continue
        saida[ch] = {'caixa_doc': [round(v, 4) for v in caixa],  # numero-neutro: casas do px
                     'linhas': len(item['linhas'])}
        if nova is not None:
            saida[ch].update(justificacao=nova, desvio=round(d, 4))  # numero-neutro: casas do px
        _guardar(no_cache, saida[ch])
    return saida


def medir_alinhados(pasta, laudo, estado, pedidos):
    """O texto do KV com o alinhamento das linhas escolhido pelo DA (0.12.0). pedidos: [(layer_id, manter, inseridas,
    justificacao)], com as quebras que o render aplica no formato (as da familia ou as da mestre propria; todas as
    gravadas e nenhuma inserida no texto sem quebra). A mesma pagina e o mesmo cache de medir: o texto com as linhas
    como o render as desenha. O desvio (no espaco de texto) e o quanto a ancora anda para a linha mais larga ficar no
    lugar (derivacao.quebras.desvio), e caixa_doc e a tinta com a justificacao nova, como a caixa da quebra
    (derivacao.quebras.caixa_medida).
    Devolve {chave_alinhado: {'justificacao', 'desvio', 'caixa_doc'}} ou {chave_alinhado: {'erro': motivo}}."""
    camadas = mb.camadas_do_laudo(laudo)
    saida, ordem, textos = {}, [], []
    faces, servidos, servidas = _servidos(pasta, estado)
    for lid, manter, inseridas, nova in pedidos:
        ch = mq.chave_alinhado(lid, manter, inseridas, nova)
        if ch in saida or any(o[0] == ch for o in ordem):
            continue
        c = camadas.get(lid)
        if c is None or c.get('tipo') != 'texto' or not (c.get('geometria') or {}).get('caixa_tinta'):
            saida[ch] = {'erro': 'camada_sem_texto'}
            continue
        if mq.conferir_da_familia(c, manter, inseridas) is not None:
            saida[ch] = {'erro': 'quebra_aprovada_invalida'}
            continue
        no_cache = chave_da_medida(c, manter, inseridas, servidas, espaco='alinhado:' + nova)
        guardada = _guardada(no_cache)
        if guardada is not None:
            saida[ch] = guardada
            continue
        cam = mq.com_juntadas(c, manter, inseridas)
        textos.extend([c, cam])
        ordem.append((ch, lid, manter, inseridas, nova, cam, no_cache))
    if not ordem:
        return saida
    pares, plano, larguras, tintas, motivo = _na_pagina(textos, faces, servidos, estado)
    for k, (ch, lid, manter, inseridas, nova, cam, no_cache) in enumerate(ordem):
        if motivo:
            saida[ch] = {'erro': motivo}
            continue
        c = camadas[lid]
        if any(pares.get(r.get('fonte_ps')) is None for r in c['texto'].get('runs') or [] if r.get('fonte_ps')):
            saida[ch] = {'erro': 'face_ausente'}
            continue
        mestre, juntado = plano['camadas'][2 * k], plano['camadas'][2 * k + 1]  # numero-neutro: duas camadas por pedido
        _cm, sm = medicao.ler_larguras(mestre, larguras)
        _cj, sj = medicao.ler_larguras(juntado, larguras)
        tm = medicao.tinta_do_bloco(mestre, larguras, tintas, mq.justificacoes_das_linhas(c, mestre))
        bloco = medicao.bloco_das_linhas(juntado, larguras, mq.justificacoes_das_linhas(cam, juntado))
        tj = medicao.tinta_do_bloco(juntado, larguras, tintas, nova)
        if not sm or not sj or tm is None or tj is None or bloco is None:
            saida[ch] = {'erro': 'sem_medida_do_chromium'}
            continue
        d = mq.desvio(bloco, nova)
        # a tinta nova a partir da ancora de antes: a ancora andou o desvio
        tj = dict(tj, esq=tj['esq'] + d, dir=tj['dir'] + d)
        caixa = mq.caixa_medida(c, c['geometria']['caixa_tinta'], manter,
                                {'tinta_mestre': tm, 'tinta': tj, 'largura_texto': sj, 'largura_texto_mestre': sm},
                                inseridas)
        saida[ch] = {'justificacao': nova, 'desvio': round(d, 4),  # numero-neutro: casas do px
                     'caixa_doc': [round(float(v), 4) for v in caixa]}  # numero-neutro: casas do px
        _guardar(no_cache, saida[ch])
    return saida
