# -*- coding: utf-8 -*-
"""A proposta confirmada pelo DA na tela, por familia (M7a, fatia 5; decisoes-v1.md, 164, 166, 167, 168, 169 e 171).

O briefing confirmado por "Salvar e seguir" (vapt.briefing.salvar) traz em composicoes cada familia da tela: os
formatos dela, a versao da galeria escolhida e as edicoes do DA no palco. A derivacao parte delas.
Desde a decisao 199 (18/11; etapa E4), cada familia tem um arquivo de edicao (arquivo_de_edicao: o de maior area na
composicao, em pe). So ele parte da galeria ou da proposta, com as edicoes do DA, pelas regras abaixo. Os outros
arquivos copiam o layout aprovado nele (layout_da_familia: vapt.derivacao.familia.transferir e ajustar_minimo),
com ou sem edicao, nunca da galeria propria nem da proposta propria; o caminho e 'familia', e o registro
transferencia diz o arquivo de edicao, a escala, o crescimento das bases, as ancoras, os ajustes e as relacoes
quebradas. A previa da tela chama a mesma conta. Onde as regras abaixo falam de "cada membro", vale o arquivo de
edicao:
  - o formato que o motor devolve por troca de orientacao, proporcao fora da faixa ou validacao obrigatoria que
    reprova (MOTIVOS_DA_GALERIA; usa_galeria, a regra unica que a tela tambem chama) sai da versao da galeria
    escolhida para a familia (sem escolha, a primeira sem falha, como a tela mostra), com as edicoes do DA; o caminho
    e 'galeria' e o formato deixa de ser devolvido quando a versao passa nas validacoes obrigatorias;
  - o formato que o motor deriva sozinho (transform ou solver) recebe as edicoes do DA por cima da proposta dele;
  - as edicoes vao a cada membro em proporcao ao formato dele, com a intencao de alinhamento (168, revista pela 185):
    a mesma conta da previa da tela (vapt.tela.edicao.Editor), pelas mesmas funcoes daqui, para a derivacao
    gravada ser o que o DA viu. O que o DA nao mexeu fica parado (0.9.5): o motor nao refaz o encaixe depois das
    edicoes, e cada elemento fora delas fica com a caixa da versao de partida;
  - cada elemento leva a origem da geometria (origem_geometria): 'da' (mexido, alinhado pela intencao ou com texto
    editado pelo DA), 'galeria' (a versao sem edicao), 'transformacao' (escala pura), 'regra' (solver, quando o
    motor derivou o formato pelo solver);
  - o elemento apagado sai do formato e fica em apagados_pelo_da, com a origem de quem confirmou a familia; ele deixa
    de contar no inventario igual entre formatos;
  - o texto editado vale so na familia onde o DA mexeu (171; a copia do layout de outra familia, 215, o grava como
    edicao desta familia, com as caixas, o alinhamento, os apagados e as quebras) e vai em texto_editado, com as
    quebras dele (as linhas
    do DA, M7b, A7, sem quebra na largura da caixa: Linhas do DA, 0.9.4) e a caixa medida da tinta delas
    (caixa_texto_editado, com o mesmo corpo): nunca as quebras da proposta (quebras
    'do_texto_editado');
  - a quebra de linha da familia (quebras_por_familia com familia, M7b, C2; decisoes-v1.md, 167 e 171) vale em todo
    membro: a mestre de onde o membro parte tem a caixa medida do texto com a quebra (mestre_do_membro; na galeria, a
    mesma mestre para todos os membros, mestre_da_galeria), e a escala do texto sai dela. O elemento leva
    quebras_origem ('da', ou 'proposta' na quebra que o motor propos) e origem_geometria 'da' quando a quebra e do DA
    ou foi aprovada por ele. No texto editado, a quebra vale sobre o texto novo, e a caixa e a da tinta medida;
  - a aprovacao do DA e soberana (0.9.6; proposta da decisao 198): o layout da familia confirmada que a validacao
    obrigatoria do motor reprova, ou que a conferencia marca (sobreposicao, fora do formato, area segura, distancia,
    texto na borda), fica derivado, com o registro aprovado_pelo_da_com_aviso e os valores. So a composicao que nao
    foi confirmada volta ao DA com o nome da validacao, como na derivacao sem tela;
  - o texto editado tem duas caixas (0.9.6; decisao 196): a de geometria, que da a escala e a transformacao, e a das
    linhas do DA (caixa_visivel, a tinta medida em volta da ancora), que vale para alinhar, para o Tamanho, para a
    conferencia, para as validacoes e para a caixa gravada;
  - o piso de escala (133) ou de distancia (135) que o elemento mexido pelo DA fura e decisao dele (M7b, D5): o
    formato leva o registro decisao_do_da, com os valores, no lugar de proposta_com_falha.
A galeria e a mesma da tela (galeria_da_familia, com os formatos devolvidos da familia na ordem da tela). So le
arquivos do job pelo contexto da derivacao: nao abre PSD, fonte nem imagem.
"""
import copy

# os motivos da devolucao que a galeria resolve (decisoes-v1.md, 164 e 166): a troca de orientacao, a proporcao fora
# da faixa e o layout do motor que reprova numa validacao obrigatoria (o formato que precisa de ajuste; previa igual
# ao Salvar, M7b). Os outros (folha, dimensao, indeterminado, bloco partido, medida por confirmar) sao guardas do motor
# que a escolha do DA nao pula
MOTIVOS_DA_GALERIA = ('troca_forte_de_orientacao', 'troca_de_orientacao_quadrado', 'fora_da_faixa_de_familia',
                      'validacao_obrigatoria_reprovou')
ORIGEM_POR_CAMINHO = {'galeria': 'galeria', 'transform': 'transformacao', 'solver': 'regra', 'mestre_propria': 'da',
                      'familia': 'familia'}
ORIGEM_DA = 'da'
# decisao 199 (etapa E4): o arquivo que sai da copia do layout aprovado no arquivo de edicao da familia
CAMINHO_FAMILIA = 'familia'
CODIGO_TRANSFERENCIA = 'transferencia'
CASAS_REGISTRO = 6  # numero-neutro: casas das medidas do registro da copia (o arredondamento, nao uma regra)
# 0.9.6: a familia confirmada pelo DA com aviso da conferencia (aprovacao soberana): o registro leva os valores
CODIGO_APROVADO_COM_AVISO = 'aprovado_pelo_da_com_aviso'
ORIGENS_DO_APAGADO = ('da', 'fixture_de_teste')
QUEBRAS_DO_TEXTO_EDITADO = 'do_texto_editado'


def usa_galeria(derivado):
    """True quando o formato (derivacao/1 em memoria) parte da galeria: devolvido por um motivo de MOTIVOS_DA_GALERIA.
    A regra unica da previa igual ao Salvar (M7b): a tela monta a galeria so destes formatos
    (vapt.tela.estado.galerias e vapt.tela.edicao.Editor._viva), e a derivacao da familia confirmada so os tira
    da galeria (aplicar). O formato devolvido por outro motivo fica devolvido nas duas, sem versao."""
    d = derivado or {}
    return d.get('situacao') == 'devolvido' and (d.get('devolucao') or {}).get('motivo') in MOTIVOS_DA_GALERIA


def mestre_da_galeria(ctx, kv, formatos):
    """(mestre, camadas sem medida) da galeria de uma familia: a mestre do KV com a caixa medida de cada texto que tem
    quebra da familia da tela (M7b, C2). A quebra da familia vale igual em todos os membros, entao a mestre e uma so
    para a familia; a quebra da faixa (M5) nunca entrou na galeria. Sem quebra da familia, a propria kv."""
    from vapt.derivacao import formatos as mod_formatos
    from vapt.derivacao import nucleo as nd
    if not formatos:
        return kv, []
    W, H = mod_formatos.composicao(formatos[0])
    return nd._com_quebras(ctx, kv, formatos[0], W, H, so_familia=True)


def mestre_do_membro(ctx, kv, formato, derivado):
    """A mestre de onde o membro da familia parte, com as quebras dele (M7b, C2): a do formato que o motor derivou
    (transformacao ou solver, com a quebra da faixa e a da familia, como vapt.derivacao.nucleo.derivar_formato) ou
    a da galeria (o formato devolvido). A edicao no palco (vapt.tela.edicao) e a derivacao da familia confirmada
    partem da mesma, para a escala do texto sair da caixa com a quebra. Sem a medida, a kv."""
    from vapt.derivacao import formatos as mod_formatos
    from vapt.derivacao import nucleo as nd
    if (derivado or {}).get('situacao') == 'derivado':
        if (derivado.get('mestre') or {}).get('tipo', 'kv') != 'kv':
            return kv
        W, H = mod_formatos.composicao(formato)
        m, _sem = nd._com_quebras(ctx, kv, formato, W, H)
    else:
        m, _sem = mestre_da_galeria(ctx, kv, [formato])
    return m


def galeria_da_familia(ctx, kv, formatos, *, specs, arquivo_specs, params, mestre=None):
    """{id do formato: [(ordem, variante do motor)]} dos formatos devolvidos de uma familia (formatos: os do briefing,
    na ordem da tela). As variantes vem da galeria no primeiro formato; com mais de um, cada variante vai a todos pela
    estrutura que deixa o pior membro melhor (vapt.derivacao.galeria.variante_para_grupo). Quando nenhuma estrutura
    serve a todos, cada membro fica com a variante de mesmo id dele. O membro sem nenhuma variante ganha a galeria dele
    sozinho. A galeria parte da mestre da familia, com a quebra de linha dela (mestre_da_galeria; mestre: a ja
    montada). So previa, em memoria."""
    from vapt.derivacao import galeria as mg
    kw = {'specs': specs, 'arquivo_specs': arquivo_specs, 'params': params}
    if not formatos:
        return {}
    kv = mestre if mestre is not None else mestre_da_galeria(ctx, kv, formatos)[0]
    por_id = {f['id']: f for f in formatos}
    fids = [f['id'] for f in formatos]
    por_formato = {fid: [] for fid in fids}
    proprias = {}

    def propria(fid, vid):
        if fid not in proprias:
            proprias[fid] = {x['id']: x for x in mg.variantes(ctx, kv, por_id[fid], **kw)}
        return proprias[fid].get(vid)
    for n, v in enumerate(mg.variantes(ctx, kv, por_id[fids[0]], **kw), 1):
        membros = {fids[0]: v}
        if len(fids) > 1:
            try:
                membros = mg.variante_para_grupo(ctx, kv, formatos, v['id'], **kw)['membros']
            except ValueError:  # nenhuma estrutura da variante serve a todos: cada um com a dele, de mesmo id
                for fid in fids[1:]:
                    mv = propria(fid, v['id'])
                    if mv is not None:
                        membros[fid] = mv
        for fid, mv in membros.items():
            por_formato[fid].append((n, mv))
    return {fid: por_formato[fid] or list(enumerate(mg.variantes(ctx, kv, por_id[fid], **kw), 1)) for fid in fids}


def membros_na_composicao(formatos):
    """[{'id', 'W', 'H', 'giro'}] dos formatos (os do briefing, ou o formato de uma derivacao/1), W x H na composicao,
    em pe como o publico ve (o giro fica na entrega, 139 e 180)."""
    from vapt.derivacao import formatos as mod_formatos
    saida = []
    for f in formatos:
        W, H = mod_formatos.composicao(f)
        saida.append({'id': f['id'], 'W': float(W), 'H': float(H),
                      'giro': int(((f.get('rotacao') or {}).get('graus')) or 0)})
    return saida


def arquivo_de_edicao(formatos, gravado=None, conhecidos=None):
    """O id do arquivo de edicao da familia (decisao 199, 1; vapt.derivacao.familia.arquivo_de_edicao): o de maior
    area na composicao; no empate, o sem giro, depois o primeiro da lista. formatos: os da familia, na ordem da tela.
    gravado: a escolha gravada, que fica enquanto o arquivo esta na familia. A tela, a previa e a derivacao chamam
    esta, para as tres verem o mesmo arquivo.
    conhecidos (revisao da 0.10.0, a migracao): os formatos que a familia ja tinha antes, sem escolha gravada (o job da
    0.9.6). A regra vale so entre eles quando algum continua na familia: o irmao maior que entra depois nunca vira o
    arquivo de edicao da familia ja aprovada, e o formato aprovado nunca e derivado de novo como copia."""
    from vapt.derivacao import familia as mod_familia
    ids = [f['id'] for f in formatos]
    if conhecidos and gravado not in ids:
        velhos = [f for f in formatos if f['id'] in set(conhecidos)]
        if velhos:
            return mod_familia.arquivo_de_edicao(membros_na_composicao(velhos))
    return mod_familia.arquivo_de_edicao(membros_na_composicao(formatos), gravado)


def galeria_dos_devolvidos(ctx, kv, derivados, formatos, *, specs, arquivo_specs, params, arquivo=None):
    """(galeria, mestre, sem_medida) de uma familia: a regra unica de onde parte cada formato devolvido (previa igual
    ao Salvar, M7b). A tela (vapt.tela.estado.galerias e vapt.tela.edicao.Editor._viva) e a derivacao da
    familia confirmada (aplicar) chamam esta. A galeria e montada so no arquivo de edicao (decisao 199, 5; arquivo:
    o gravado, senao a regra de arquivo_de_edicao): os outros arquivos copiam o layout aprovado nele e nunca partem
    da galeria propria. Parte da galeria o arquivo de edicao devolvido por um motivo de usa_galeria, e a galeria parte
    da mestre com a quebra de linha da familia (mestre_da_galeria). Sem a medida da quebra (sem_medida: as camadas
    sem medida), a galeria nao sai, e o arquivo fica como o motor o deixou, na tela e no "Salvar e seguir".
    derivados: {id do formato: derivacao/1 em memoria}; formatos: os da familia no briefing, na ordem da tela.
    galeria: {id do formato: [(ordem, variante do motor)]}, so do arquivo de edicao, quando ele tem versao."""
    ref = arquivo_de_edicao(formatos, arquivo) if formatos else None
    devolvidos = [f for f in formatos if f['id'] == ref and usa_galeria(derivados.get(f['id']))]
    mestre, sem_medida = mestre_da_galeria(ctx, kv, devolvidos)
    if not devolvidos or sem_medida:
        return {}, mestre, sem_medida
    por = galeria_da_familia(ctx, kv, devolvidos, mestre=mestre, specs=specs, arquivo_specs=arquivo_specs,
                             params=params)
    return {fid: pares for fid, pares in por.items() if pares}, mestre, sem_medida


def partida(derivado, versoes, versao):
    """Os elementos de onde o membro parte: a proposta derivada (formato derivado), a versao escolhida, a primeira sem
    falha ou a primeira da galeria. versoes: {id da versao: variante do motor}. None sem nenhuma."""
    if (derivado or {}).get('situacao') == 'derivado':
        return derivado['elementos']
    vid = versao_de_partida(derivado, versoes, versao)
    return None if vid is None else versoes[vid]['elementos']


def versao_de_partida(derivado, versoes, versao):
    """O id da versao da galeria de onde o membro parte (partida): a escolhida, a primeira sem falha ou a primeira da
    galeria. None no formato derivado e sem versao. O id efetivo diz se a figura fica de fundo (galeria.fundo_da_versao;
    decisoes-v1.md, n 202), tambem quando o DA ainda nao escolheu versao."""
    if (derivado or {}).get('situacao') == 'derivado':
        return None
    versoes = versoes or {}
    if versao in versoes:
        return versao
    return next((k for k, x in versoes.items() if not x['falhas_obrigatorias']), next(iter(versoes), None))


def quadros_do_membro(cf):
    """Os quadros do membro para alinhar (M7b, D2): a margem (o quadro da galeria do formato: a area segura, ou a util,
    com a margem da mestre no lado curto) e a area segura da folha. Sem area segura na folha, a area segura do membro
    e a margem dele, como a pagina diz (revisao 2 da fase D): na familia em que so um membro tem area segura, o clique
    em "Área segura" nunca leva o outro ate a borda da peca. cf: o contexto da galeria do formato
    (galeria.contexto_do_formato)."""
    margem = [float(v) for v in cf['quadro']]
    seg = ((cf.get('areas') or {}).get('area_segura') or {}).get('caixa')
    return {'margem': margem, 'area_segura': [float(v) for v in seg] if seg else list(margem)}


def caixa_visivel(el_cf, geo, tinta_doc):
    """A caixa do texto editado no formato como o DA a ve (0.9.6; decisao 196): a tinta medida das linhas do DA
    (tinta_doc, no espaco do documento) levada ao formato pela mesma transformacao do elemento (a escala tirada da
    caixa de geometria geo, como galeria._escalas e galeria._elementos, e o destino no canto dela). Encolhe e cresce
    com as linhas do DA, em volta da ancora; a escala do texto nao muda. el_cf: o elemento na mestre do membro."""
    m, doc = el_cf['caixa'], el_cf['caixa_doc']
    if m[2] > m[0]:
        s = (float(geo[2]) - float(geo[0])) / (float(m[2]) - float(m[0]))
    else:
        s = (float(geo[3]) - float(geo[1])) / (float(m[3]) - float(m[1])) if m[3] > m[1] else 1.0
    s *= float(el_cf.get('escala_na_mestre') or 1.0)
    return _no_formato({'s': s, 'origem_doc': [float(doc[0]), float(doc[1])],
                        'destino': [float(geo[0]), float(geo[1])]}, tinta_doc)


def alinhamentos_do_da(ctx, kv, edicoes):
    """{id do elemento: alinhamento das linhas (esquerda, centro ou direita)} que o DA escolheu e que muda o texto
    (0.12.0; derivacao.quebras.alinhamento_efetivo: o do KV escolhido de novo volta ao KV e fica de fora). So o
    elemento com um texto de ponto so, que nao vai como imagem (a regra da tela, vapt.tela.edicao.Editor.
    _alinhamento): a edicao em outro elemento a tela recusa, e o "Salvar e seguir" para antes (pendencias)."""
    from vapt.briefing import modelo as mb
    from vapt.derivacao import quebras as mq
    if not any(e.get('acao') == 'alinhar_texto' for e in edicoes or ()):
        return {}
    cam = mb.camadas_do_laudo(ctx['laudo'])
    saida = {}
    for e in kv['elementos']:
        textos = [cam.get(lid) for lid in e['layer_ids'] if (cam.get(lid) or {}).get('tipo') == 'texto']
        if len(textos) != 1 or any((cam.get(lid) or {}).get('texto_como_imagem') for lid in e['layer_ids']) or \
                (textos[0].get('texto') or {}).get('tipo_caixa') == 'paragrafo':
            continue
        valor = mq.alinhamento_efetivo(edicoes, e['id'], textos[0])
        if valor is not None:
            saida[e['id']] = valor
    return saida


def tintas_editadas(ctx, kv, edicoes, fid):
    """{id do elemento: tinta das linhas do DA no documento} de cada elemento so de texto com texto editado nas
    edicoes (0.9.6; decisao 196), com a quebra da familia do formato fid sobre o texto novo. A medida e a mesma da
    derivacao gravada (_caixas_editadas, com o cache). O elemento sem a medida fica de fora: vale a caixa de antes."""
    from vapt.briefing import modelo as mb
    from vapt.derivacao import quebras as mq
    cam = mb.camadas_do_laudo(ctx['laudo'])
    alin = alinhamentos_do_da(ctx, kv, edicoes)
    els = []
    for e in kv['elementos']:
        texto = mq.texto_editado(edicoes, e['id'])
        if texto is None or not e['layer_ids'] or \
                any((cam.get(lid) or {}).get('tipo') != 'texto' for lid in e['layer_ids']):
            continue
        x = {'id': e['id'], 'layer_ids': list(e['layer_ids']), 'texto_editado': texto}
        if e['id'] in alin:
            # 0.12.0: a tinta das linhas do DA com o alinhamento novo (a caixa do bloco fica no lugar)
            x['alinhamento_do_da'] = {'alinhamento': alin[e['id']]}
        _quebras_do_editado(ctx, x, fid)
        els.append(x)
    if not els:
        return {}
    try:
        medidas = _caixas_editadas(ctx, els)
    except Exception:  # noqa: BLE001 - sem a medida, o texto fica com a caixa de antes, e o render confere a tinta
        return {}
    return {eid: c for eid, (c, _falta) in medidas.items() if c is not None}


def _figura_de_fundo(fundo, apagados):
    """O id da figura de fundo do layout (decisoes-v1.md, n 202), ou None: a figura que o DA apagou no palco nao esta
    no layout, e nada diz que ela fica de fundo."""
    return fundo[0] if fundo and fundo[0] not in apagados else None


def layout_do_membro(cf, elementos, edicoes, *, kv_por_id, conteudo, kv_caixas, kv_tamanho, tintas=None, fundo=(),
                     alinhamentos=None):
    """O layout de um membro da familia com as edicoes do DA: as edicoes em proporcao ao formato (o alinhamento no
    quadro com os quadros do membro, M7b, D2), a intencao de alinhamento entre os elementos de conteudo depois de cada
    edicao, so no que ela mexeu (edicao.editar, decisao 185), o alinhamento no quadro firmado de novo e a conferencia
    contra a mestre verdadeira. O que o DA nao mexeu fica parado (decisao do Duda em 17/11, 0.9.5): cada elemento fora
    das edicoes fica com a caixa da versao de partida, e o motor nao reposiciona nada por conta propria (o encaixe
    refeito pelo solver do M7b saiu). Quando o resultado sobrepoe elementos, sai do formato, passa da area segura ou
    fica mais perto do que o KV pede, a conferencia avisa, e o DA decide. O lado em que o elemento mexido pelo DA
    passa da borda do formato vira sangria dele (sangria_do_da {id: [lados]}, M7b, D4), sem o lado que ja sangrava no
    KV. O piso de escala ou de distancia que o elemento mexido pelo DA fura sai das falhas e vai a decisoes_do_da, com
    o valor a vista (M7b, D5); o piso que a versao de partida ja furava continua falha. O lado em que o asset acaba na
    borda do KV e que o DA tirou da borda e um corte a vista: o elemento fica onde o DA o pos, e a falha corte_a_mostra
    pede ajuste (revisao 1 da fase D); o lado que so a versao da galeria sangrava deixa de sangrar, sem falha, e o
    elemento que o DA levou inteiro para fora da peca fica onde ele o pos e pede ajuste (revisao 2 da fase D). cf: o
    contexto da galeria do formato (galeria.contexto_do_formato).
    tintas (0.9.6; decisao 196): {id: tinta das linhas do DA no documento} do texto editado (tintas_editadas). O
    elemento com texto editado tem duas caixas: a de geometria (caixas, a que da a escala e a transformacao) e a
    visivel (caixas_visiveis, a tinta das linhas do DA em volta da ancora). Alinhar, o Tamanho, o encaixe, a
    conferencia e as validacoes usam a visivel: o texto que passou de 4 para 2 linhas nunca sobrepoe nem sai do
    formato pela caixa de antes.
    fundo (decisoes-v1.md, n 202): os ids da figura de fundo da versao de partida neste formato
    (galeria.fundo_da_versao): o conteudo sobre ela nao e falha, e o conteudo mexido pelo DA nao encaixa nas bordas
    dela.
    Devolve {'caixas', 'caixas_visiveis', 'sangra', 'apagados', 'textos', 'mexidos', 'alinhados', 'no_quadro',
    'quadros', 'sangria_do_da', 'falhas', 'decisoes_do_da', 'avisos', 'reprovadas', 'elementos',
    'figura_de_fundo', 'alinhamentos', 'copiados', 'copiados_do_da'}.
    A caixa copiada de outra familia (decisao 215; edicao 'caixa') vai a mestre deste membro pela mesma transformacao
    (edicao.caixa_copiada) e e a partida do elemento, com a sangra dela; a sangria do DA da origem volta, e o
    copiado que era decisao do DA na origem (do_da) continua decisao dele (corte a vista e sangria) enquanto o DA nao o
    mexe; o piso que ja era decisao do DA na origem (piso_do_da) continua decisao mesmo depois que o DA o mexe aqui
    (revisao 2 da 215). copiados: os elementos com a caixa copiada que vale; copiados_do_da: os que eram decisao do DA.
    alinhamentos (0.12.0): {id: alinhamento das linhas do texto} que o DA escolheu (alinhamentos_do_da). Nao mexe em
    caixa nenhuma; o layout so o leva, sem o elemento apagado."""
    from vapt import limites
    from vapt.derivacao import elementos as mod_elementos
    from vapt.derivacao import galeria as mg
    from vapt.tela import edicao
    W, H = cf['W'], cf['H']
    quadros = quadros_do_membro(cf)
    caixas = {e['id']: e['caixa'] for e in elementos}
    sangra = {e['id']: dict(e['transformacao']['sangra']) for e in elementos
              if e['transformacao'].get('sangra') != kv_por_id[e['id']]['sangra']}
    partida = {k: [float(x) for x in v] for k, v in caixas.items()}
    sangra_partida = {k: dict(v) for k, v in sangra.items()}
    do_cf = {e['id']: e for e in cf['kv']['elementos']}
    # o lado em que o asset acaba na borda do KV (o que sangra no KV, nunca so na versao da galeria): no alinhamento no
    # quadro, o elemento fica preso a essa borda e anda com o grupo, fora da linha dele (revisoes 1 e 2 da fase D)
    borda = {(k, lado) for k in caixas if k in do_cf for lado, v in do_cf[k]['sangra'].items() if v}
    # as edicoes uma a uma, cada uma com a intencao de alinhamento na hora dela: so o que ela mexeu encaixa no
    # vizinho, com o grupo inteiro, e o alinhado no quadro fica na linha do quadro (decisao 185; M7b, D1 e D2)
    tintas = dict(tintas or {})

    def visivel(k, geo):
        # a caixa das linhas do DA (0.9.6): so do elemento com a medida da tinta
        return caixa_visivel(do_cf[k], geo, tintas[k]) if k in tintas and k in do_cf else None
    caixas, apagados, textos, mexidos, alinhados = edicao.editar(
        caixas, edicoes, W, H, quadros, borda, conteudo=set(conteudo) - set(fundo), kv_caixas=kv_caixas,
        kv_tamanho=kv_tamanho,
        visivel=visivel if tintas else None, mestre_caixas={k: e['caixa'] for k, e in do_cf.items()})
    # decisao 215: o elemento com a caixa copiada de outra familia parte dela, com a sangra dela (revisao 1 da fase D
    # sobre a copia: o piso que a copia ja furava continua falha). O copiado que era decisao do DA na origem (do_da)
    # continua decisao aqui enquanto o DA nao o mexe (o piso de piso_do_da, mesmo mexido)
    cop = edicao.copiados(edicoes)
    vig = [k for k in caixas if k in cop]
    for k in vig:
        sangra[k] = dict(cop[k]['sangra'])
        partida[k] = edicao.caixa_copiada(cop[k], W, H, (do_cf.get(k) or {}).get('caixa'))
        sangra_partida[k] = dict(cop[k]['sangra'])
    cop_da = {k for k in vig if cop[k].get('do_da') and k not in mexidos}
    # o piso que ja era decisao do DA na origem continua decisao mesmo depois que o DA mexe o copiado aqui (revisao 2
    # da 215): a partida dele e a caixa copiada, que ja furava o piso pela escolha de tamanho do DA na origem
    cop_piso = {k for k in vig if cop[k].get('piso_do_da')}
    intencoes = edicao.intencoes(edicoes)
    # o lado que o DA deixou passar da borda vira sangria do elemento neste membro (M7b, D4): a validacao e a
    # conferencia nao o marcam como defeito; o texto e a marca nunca sangram. A conta e sem a tolerancia do
    # enquadramento (revisao 2 da fase D)
    sem =[k for k, e in kv_por_id.items() if e['classe'] in mod_elementos.CLASSES_SEM_SANGRIA]
    tol = limites.valor('derivacao.enquadramento_tolerancia_px')
    do_da = [k for k in mexidos if k in do_cf]
    sangria_do_da = edicao.sangria_do_da(caixas, do_da, W, H, edicao.IGUAL, sem)
    # o elemento que o DA levou inteiro para fora da peca nao sangra: pede ajuste (revisao 2 da fase D)
    editados = [k for k in textos if k in tintas]
    fora_da_peca = [k for k in edicao.fora_da_peca(edicao.vistas(caixas, visivel, editados), do_da, W, H, tol)
                    if k not in sem]
    for k, lados in list(sangria_do_da.items()):
        s = dict(sangra.get(k) or do_cf[k]['sangra'])
        # o lado que ja sangrava fica como era (o corte do asset na borda do KV), fora da sangria do DA
        sangria_do_da[k] = [lado for lado in lados if not s[lado]]
        if not sangria_do_da[k]:
            del sangria_do_da[k]
            continue
        s.update({lado: True for lado in lados})
        sangra[k] = s
    # decisao 215: os lados que o DA deixou passar da borda na familia de origem, no copiado que ele nao mexeu aqui
    for k in vig:
        if k not in mexidos and cop[k].get('sangria_do_da'):
            sangria_do_da[k] = list(cop[k]['sangria_do_da'])
    for k in apagados:
        sangra.pop(k, None)
    # o lado que sangrava no membro de partida e que o DA tirou da borda: o elemento fica onde o DA o pos, com o
    # tamanho dele (o grupo nao se separa, e o tamanho vale igual em todo membro). Quando o asset acaba ali no KV, o
    # corte fica a vista (revisao 1 da fase D): a conferencia pede ajuste com a frase do corte, e a validacao
    # obrigatoria devolve o formato. Quando so a versao da galeria sangrava ali (a arte da faixa), a borda do asset e
    # inteira: o lado deixa de sangrar, sem falha (revisao 2 da fase D)
    cortes, soltos = {}, {}
    for k in do_da + sorted(cop_da):
        s, c = sangra.get(k) or do_cf[k]['sangra'], caixas[k]
        lados = [lado for lado, dentro in (('esq', c[0] > tol), ('topo', c[1] > tol), ('dir', c[2] < W - tol),
                                           ('base', c[3] < H - tol)) if s[lado] and dentro]
        if [lado for lado in lados if do_cf[k]['sangra'][lado]]:
            cortes[k] = [lado for lado in lados if do_cf[k]['sangra'][lado]]
        if [lado for lado in lados if not do_cf[k]['sangra'][lado]]:
            soltos[k] = [lado for lado in lados if not do_cf[k]['sangra'][lado]]
    for k, lados in soltos.items():
        sangra[k] = dict(sangra.get(k) or do_cf[k]['sangra'], **{lado: False for lado in lados})
    # o que o DA nao mexeu fica parado (0.9.5): nada reposiciona os elementos depois das edicoes. O que esta inteiro
    # fora da peca tambem fica onde o DA o pos (a previa mostra o que ele fez), e a conferencia pede ajuste
    caixas, no_quadro = edicao.firmar(caixas, intencoes, quadros, W, H, borda, visivel=visivel, editados=editados)
    vis = edicao.vistas(caixas, visivel, editados)
    falhas, avisos, reprovadas = mg.conferir_edicao(cf, vis, sangra, apagados, geometria=caixas, fundo=fundo)
    falhas = mg.corte_a_mostra(cf, falhas, cortes)
    falhas = mg.fora_da_peca(cf, falhas, fora_da_peca)
    # o piso que a versao de partida ja furava continua pedindo ajuste (revisao 1 da fase D): o DA so andou ou alinhou o
    # elemento, e o piso nao e decisao dele. A conta da partida so roda quando ha piso furado com elemento do DA
    da_partida = ()
    # decisao 215: o copiado que era decisao do DA na origem conta como mexido. So o piso que ja era decisao do DA na
    # origem (piso_do_da na caixa) fica fora da conta da partida; o piso que so a copia fura continua falha
    mexidos_d = list(mexidos) + sorted(cop_da)
    if any(f['codigo'] in mg.PISOS_DO_DA and set(f['elementos']) & set(mexidos_d) for f in falhas):
        f_partida = mg.conferir_edicao(cf, partida, sangra_partida, apagados, fundo=fundo)[0]
        da_partida = {(f['codigo'], tuple(sorted(f['elementos']))) for f in f_partida
                      if f['codigo'] in mg.PISOS_DO_DA and not set(f['elementos']) & cop_piso}
    falhas, decisoes = mg.decisoes_do_da(cf, falhas, mexidos_d, da_partida)
    return {'caixas': caixas, 'caixas_visiveis': vis, 'sangra': sangra, 'apagados': apagados, 'textos': textos,
            'mexidos': mexidos,
            'alinhados': alinhados, 'no_quadro': no_quadro, 'quadros': quadros,
            'sangria_do_da': sangria_do_da,
            'falhas': falhas, 'decisoes_do_da': decisoes, 'avisos': avisos, 'reprovadas': reprovadas,
            'elementos': mg.elementos_do_layout(cf, caixas, sangra, apagados),
            'figura_de_fundo': _figura_de_fundo(fundo, apagados),
            'alinhamentos': {k: v for k, v in sorted((alinhamentos or {}).items()) if k in caixas},
            'copiados': sorted(vig), 'copiados_do_da': sorted(k for k in vig if cop[k].get('do_da'))}


# ------------------------------------------------------------------ a familia segue o arquivo de edicao (199)
def _arredondar(v):
    """O registro da copia em numeros arredondados (CASAS_REGISTRO): o mesmo texto em todo processo."""
    if isinstance(v, float):
        return round(v, CASAS_REGISTRO)
    if isinstance(v, dict):
        return {k: _arredondar(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_arredondar(x) for x in v]
    return v


def _modelo(ctx, cf, lay, edicoes, fid):
    """O modelo da familia (vapt.derivacao.familia.extrair_modelo) tirado do layout aprovado L* no arquivo de
    edicao (lay, de layout_do_membro; cf: o contexto dele). Cada elemento leva a caixa que o DA ve, a de geometria do
    texto editado (196), os lados em que sangra e a ancora da funcao no Design system. A base leva o recorte (a caixa
    em que o render corta a pilha) e, quando o elemento tem uma camada so com a silhueta que o preparo gravou, a caixa
    do asset levada ao arquivo pela transformacao do elemento e a grade (vapt.derivacao.silhueta). Sem ela, a
    forma e conferida pela caixa, com o aviso. A figura de fundo de L* (lay['figura_de_fundo']; decisoes-v1.md, n 202)
    vai como fundo (de_fundo): o conteudo sobre ela ja foi aprovado, e ela cresce para continuar sangrando, sem relacao
    de tinta com o conteudo."""
    from vapt import limites
    from vapt.derivacao import familia as mod_familia
    from vapt.derivacao import silhueta as mod_silhueta
    from vapt.derivacao import solver as mod_solver
    from vapt.tela import edicao
    kvm = cf['kv']
    canvas = [float(v) for v in (kvm.get('canvas_doc') or [0.0, 0.0, kvm['largura'], kvm['altura']])]
    por = {e['id']: e for e in lay['elementos']}
    vis = lay.get('caixas_visiveis') or lay['caixas']
    tol = float(limites.valor('derivacao.enquadramento_tolerancia_px'))
    W, H = cf['W'], cf['H']
    elementos, silhuetas = [], {}
    for e in kvm['elementos']:
        x = por.get(e['id'])
        if x is None:
            continue
        tr = x['transformacao']
        caixa = [float(v) for v in vis[e['id']]]
        geo = [float(v) for v in lay['caixas'][e['id']]]
        # o lado que sangra no aprovado: o que sangrava e ainda chega a borda (o elemento que o DA tirou da borda em
        # que acabava no KV fica com o corte a vista e nao volta a sangrar na copia)
        chega = {'esq': caixa[0] <= tol, 'topo': caixa[1] <= tol, 'dir': caixa[2] >= W - tol, 'base': caixa[3] >= H - tol}
        sangra = {lado: bool(v) and chega[lado] for lado, v in tr['sangra'].items()}
        item = {'id': e['id'], 'classe': e['classe'], 'funcao': e['funcao'], 'caixa': caixa, 'sangra': sangra,
                'ancora': tuple(e.get('ancora') or (None, None)), 'opaco': bool(e.get('opaco'))}
        de_fundo = e['id'] == lay.get('figura_de_fundo') and any(sangra.values())
        if de_fundo:
            item['de_fundo'] = True
        if geo != caixa:
            item['geometria'] = geo
        if (de_fundo or not mod_solver.conteudo(e)) and any(sangra.values()):
            item['recorte'] = list(caixa)
            partes = mod_silhueta.partes_do_elemento(ctx, e, canvas)
            if len(partes) == 1 and partes[0][1] is not None:
                s, o, d = float(tr['s']), tr['origem_doc'], tr['destino']
                a = partes[0][0]
                item['caixa_asset'] = [s * (a[0] + canvas[0] - o[0]) + d[0], s * (a[1] + canvas[1] - o[1]) + d[1],
                                       s * (a[2] + canvas[0] - o[0]) + d[0], s * (a[3] + canvas[1] - o[1]) + d[1]]
                silhuetas[e['id']] = partes[0][1]
        elementos.append(item)
    referencia = {'id': fid, 'W': cf['W'], 'H': cf['H'], 'quadros': lay['quadros']}
    return mod_familia.extrair_modelo(referencia, elementos, intencoes=edicao.intencoes(edicoes),
                                      grupos=edicao.grupos(edicoes), silhuetas=silhuetas)


def _pisos(cf, col, fundo=()):
    """{id: fator} do piso da 133 de cada conteudo no layout copiado (col, de transferir): o fator abaixo do qual a
    escala dele fica abaixo de derivacao.escala_conteudo_min_da_regra x a regra do arquivo. A escada (F3) nunca
    diminui o bloco abaixo disso (199, 3). A figura de fundo (fundo, n 202) vai como fundo na copia e fica de fora."""
    from vapt import limites
    from vapt.derivacao import solver as mod_solver
    piso = float(limites.valor('derivacao.escala_conteudo_min_da_regra'))
    saida = {}
    for e in cf['kv']['elementos']:
        k, r = e['id'], cf['regras'].get(e['id'])
        if k not in col['caixas'] or not r or not mod_solver.conteudo(e) or k in fundo:
            continue
        g, m = col['geometrias'].get(k) or col['caixas'][k], e['caixa']
        if m[2] > m[0]:
            esc = (g[2] - g[0]) / (m[2] - m[0])
        else:
            esc = (g[3] - g[1]) / (m[3] - m[1]) if m[3] > m[1] else 1.0
        if esc > 0:
            saida[k] = piso * r / esc
    return saida


def _aviso_do_modelo(modelo, a):
    from vapt.derivacao import familia as mod_familia
    k = a['elemento']
    rotulo = mod_familia._rotulo(modelo, k)
    if a['codigo'] == 'forma_conferida_pela_caixa':
        texto = 'O Vapt conferiu %s pela caixa, porque não tem o desenho %s.' % (rotulo, mod_familia._dela(rotulo))
    else:
        texto = '%s cresceu em volta do centro, porque a borda %s não deixava continuar sangrando.' % (
            mod_familia._maiuscula(rotulo), mod_familia._dela(rotulo))
    return {'codigo': a['codigo'], 'texto': texto, 'elementos': [k]}


def _copia(ctx, cf, modelo, lay_ref, membro, fundo=()):
    """O layout de um arquivo da familia que nao e o de edicao (199, 2 e 3): a copia do modelo (transferir), a escada
    do menor ajuste (ajustar_minimo, com o piso da 133) e a conferencia de hoje (conferir_edicao). A relacao do KV que
    a conferencia acha (relacao_quebrada) sai: no arquivo copiado, quem diz o que vale sao as relacoes do layout
    aprovado, e a que se perdeu entra como falha com a frase e o valor. O piso que o elemento mexido pelo DA fura e
    decisao dele, como no arquivo de edicao. fundo: os ids da figura de fundo neste arquivo (n 202), pela regra no
    contexto dele (galeria.fundo_da_versao): o arquivo deitado da familia confere a figura como conteudo. Devolve o
    layout na forma de layout_do_membro, mais 'situacao' (igual, ajustado ou pede_ajuste), 'frases' e
    'transferencia' (o registro da copia). O elemento copiado de outra familia que era decisao do DA la (decisao 215,
    lay_ref['copiados_do_da']) continua decisao dele aqui."""
    from vapt.derivacao import familia as mod_familia
    from vapt.derivacao import galeria as mg
    col = mod_familia.transferir(modelo, membro)
    de_fundo = [k for k in modelo['ordem'] if k == lay_ref.get('figura_de_fundo')]
    est = mod_familia.ajustar_minimo(modelo, col, pisos=_pisos(cf, col, de_fundo))
    caixas = {k: list(est['geometrias'].get(k) or est['caixas'][k]) for k in est['caixas']}
    vis = {k: list(v) for k, v in est['caixas'].items()}
    sangra = {x['id']: dict(x['transformacao']['sangra']) for x in lay_ref['elementos']}
    # a base que cresceu em volta do ponto fixo (199, 2) pode passar da borda num lado em que nao sangrava: o render
    # corta ali, e o lado passa a sangrar neste arquivo, com a frase (nada calado)
    passa = _base_passa_da_borda(modelo, est, sangra)
    apagados = list(lay_ref['apagados'])
    falhas, avisos, reprovadas = mg.conferir_edicao(cf, vis, sangra, apagados, geometria=caixas, fundo=fundo)
    falhas = [f for f in falhas if f['codigo'] != 'relacao_quebrada']
    # decisao 215: o copiado de outra familia que era decisao do DA la continua decisao dele na copia
    do_da = set(lay_ref['mexidos']) | {a['elementos'][0] for a in lay_ref['alinhados']} | set(lay_ref['textos']) | \
        set(lay_ref.get('copiados_do_da') or ())
    # o corte do KV que o DA deixou a vista no arquivo de edicao (revisao 1 da fase D) fica a vista na copia, com a
    # mesma frase
    from vapt import limites
    tol = float(limites.valor('derivacao.enquadramento_tolerancia_px'))
    W, H = cf['W'], cf['H']
    cortes = {}
    for e in cf['kv']['elementos']:
        k = e['id']
        if k not in do_da or k not in vis:
            continue
        c = vis[k]
        lados = [lado for lado, dentro in (('esq', c[0] > tol), ('topo', c[1] > tol), ('dir', c[2] < W - tol),
                                           ('base', c[3] < H - tol)) if e['sangra'][lado] and dentro]
        if lados:
            cortes[k] = lados
    falhas = mg.corte_a_mostra(cf, falhas, cortes)
    falhas, decisoes = mg.decisoes_do_da(cf, falhas, do_da)
    for q in est['relacoes_quebradas']:
        falhas.append({'codigo': 'relacao_quebrada', 'texto': q['frase'], 'elementos': list(q['elementos']),
                       'medidas': {'relacao': q['tipo'], 'id': q['relacao'], 'valor_px': round(q['valor_px'], 1)}})  # numero-neutro: casas do px
    avisos += passa
    ja = {(a['codigo'], tuple(a['elementos'])) for a in avisos}
    for a in est['avisos']:
        x = _aviso_do_modelo(modelo, a)
        if (x['codigo'], tuple(x['elementos'])) not in ja:
            avisos.append(x)
    situacao = 'pede_ajuste' if falhas else est['situacao']
    registro = {'arquivo_de_edicao': modelo['referencia'], 's': est['s'],
                'crescimento': dict(sorted(dict({k: b['crescimento'] for k, b in est['bases'].items()},
                                                **est.get('crescimento_movel', {})).items())),
                'ancoras': {bid: {'lado': b['lado'], 'quadro': b['quadro'], 'origem': b['origem']}
                            for eixo in mod_familia.EIXOS for bid, b in sorted(est['blocos'][eixo].items())},
                'ajustes': [{k: v for k, v in a.items() if k != 'estado'} for a in est['ajustes']],
                'relacoes_quebradas': [dict(q) for q in est['relacoes_quebradas']]}
    return {'caixas': caixas, 'caixas_visiveis': vis, 'sangra': sangra, 'apagados': apagados,
            'textos': dict(lay_ref['textos']), 'alinhamentos': dict(lay_ref.get('alinhamentos') or {}),
            'mexidos': [], 'alinhados': [], 'no_quadro': [], 'copiados': [], 'copiados_do_da': [],
            'quadros': quadros_do_membro(cf), 'sangria_do_da': {k: list(v) for k, v in lay_ref['sangria_do_da'].items()},
            'falhas': falhas, 'decisoes_do_da': decisoes, 'avisos': avisos, 'reprovadas': reprovadas,
            'elementos': mg.elementos_do_layout(cf, caixas, sangra, apagados), 'situacao': situacao,
            'figura_de_fundo': _figura_de_fundo(fundo, apagados),
            'frases': [a['frase'] for a in est['ajustes']] + [a['texto'] for a in passa] + [f['texto'] for f in falhas],
            'transferencia': _arredondar(registro),
            # a caixa de cada conteudo do arquivo de edicao levada a este pela copia, antes da escada (revisao da
            # 0.10.0): o "Mostrar o seu por cima" da tela desenha o contorno dela; no arquivo igual, cai no elemento
            'levado': {k: [round(float(v), 4) for v in col['caixas'][k]] for k in modelo['ordem']  # numero-neutro: casas do px
                       if modelo['elementos'][k]['conteudo'] and k in col['caixas']}}


BORDAS = {'esq': 'a borda esquerda', 'topo': 'a borda de cima', 'dir': 'a borda direita', 'base': 'a borda de baixo'}


def _base_passa_da_borda(modelo, est, sangra):
    """Os avisos das bases que a copia levou alem da borda num lado em que elas nao sangravam (o crescimento em volta
    do ponto fixo, 199, 2), alem de derivacao.enquadramento_tolerancia_px. O lado passa a sangrar em sangra (no
    lugar): o render corta ali, como corta o que sangra. A frase diz qual borda a forma passa a tocar e o motivo, sem o
    valor em px (revisao da 0.10.0): o que passa da borda nunca aparece, e um valor como "2209,2 px da base" nao
    ajuda o DA a decidir nada. O valor fica nas medidas."""
    from vapt import limites
    from vapt.derivacao import familia as mod_familia
    tol = float(limites.valor('derivacao.enquadramento_tolerancia_px'))
    W, H = est['W'], est['H']
    saida = []
    for k in modelo['ordem']:
        if modelo['elementos'][k]['papel'] == 'movel' or k not in sangra:
            continue
        c = est['caixas'][k]
        fora = [(lado, px) for lado, px in (('esq', -c[0]), ('topo', -c[1]), ('dir', c[2] - W), ('base', c[3] - H))
                if not sangra[k][lado] and px > tol]
        if not fora:
            continue
        for lado, _px in fora:
            sangra[k][lado] = True
        rotulo = mod_familia._rotulo(modelo, k)
        hospede = modelo['bases'][k].get('hospede')
        motivo = 'para o desenho ficar no mesmo lugar em relação %s' % mod_familia._contrair(
            'a', mod_familia._rotulo(modelo, hospede)) if hospede else 'para continuar cobrindo o arquivo'
        bordas = [BORDAS[lado] for lado, _px in fora]
        feminino = rotulo.partition(' ')[0] == 'a'
        saida.append({'codigo': 'base_passa_da_borda',
                      'texto': '%s chega até %s neste arquivo e fica %s ali, %s. No seu arquivo, %s não chegava %s.' % (
                          mod_familia._maiuscula(rotulo), ' e '.join(bordas), 'cortada' if feminino else 'cortado',
                          motivo, 'ela' if feminino else 'ele',
                          'a essa borda' if len(bordas) == 1 else 'a essas bordas'),
                      'elementos': [k], 'medidas': {'lados': {lado: round(px, 1) for lado, px in fora}}})  # numero-neutro: casas do px
    return saida


def edicoes_efetivas(tirados, edicoes):
    """As edicoes que o layout aplica (0.15.0; decisoes-v1.md, 204): um apagar para cada grafismo que a versao da
    galeria tirou e o DA nao devolveu, antes das edicoes do DA, e as edicoes do DA sem os devolver (o devolver so
    cancela o apagar do tirado; o elemento volta para a caixa da versao, presa a arte). A caixa copiada de outra
    familia (decisao 215) tambem devolve: a copia que mostra um grafismo que a versao tirou o mantem."""
    devolvidos = {e['elemento'] for e in edicoes if e['acao'] in ('devolver', 'caixa')}
    return [{'elemento': k, 'acao': 'apagar'} for k in tirados if k not in devolvidos] + \
        [e for e in edicoes if e['acao'] != 'devolver']


MEDIDA_IGUAL = 0.5  # numero-neutro: px, a folga da medida do arquivo de edicao na caixa copiada (o arredondamento)


def caixas_que_valem(edicoes, ref, medida):
    """(edicoes, sem_efeito) da familia (decisao 215): a caixa copiada de outra familia so vale no arquivo de edicao em
    que foi copiada (arquivo == ref) e com a mesma composicao (medida, W x H, com MEDIDA_IGUAL). As outras saem: o
    arquivo de edicao trocou ou a medida mudou, e as caixas ficam sem efeito; o texto, o alinhamento e os apagados
    copiados continuam. sem_efeito: {'arquivo', 'medida'} da primeira caixa tirada, ou None."""
    ficam, sem_efeito = [], None
    for e in edicoes:
        if e['acao'] == 'caixa' and (e.get('arquivo') != ref or len(e.get('medida') or ()) != 2 or any(  # numero-neutro: o par W x H
                abs(float(a) - float(b)) > MEDIDA_IGUAL for a, b in zip(e['medida'], medida))):
            if sem_efeito is None:
                sem_efeito = {'arquivo': e.get('arquivo'), 'medida': [float(v) for v in e.get('medida') or ()]}
            continue
        ficam.append(e)
    return ficam, sem_efeito


def layout_da_familia(ctx, kv, familia, *, derivados, versoes=None, tintas=None, cache=None, specs, arquivo_specs,
                      params):
    """{id do formato: layout} da familia inteira (decisao 199; etapa E4): a conta unica que a previa da tela
    (vapt.tela.edicao.Editor.previa) e o "Salvar e seguir" (aplicar) chamam, para a previa ser o Salvar.
      - o arquivo de edicao (arquivo_de_edicao, com o gravado em familia['arquivo_de_edicao']) sai como hoje: da
        proposta derivada ou da versao da galeria (versoes[ref], a de galeria_dos_devolvidos), com as edicoes do DA
        (layout_do_membro). E o layout aprovado L*;
      - cada outro arquivo sai da copia de L* (_copia: transferir, ajustar_minimo e conferir_edicao), com a mestre do
        arquivo de edicao (as mesmas quebras de linha e a mesma tinta do texto editado), nunca da partida propria. Vale
        tambem sem edicao (resposta 3 do Duda em 18/11);
      - o arquivo devolvido por uma guarda do motor (fora de usa_galeria) fica devolvido: None.
    familia: {'familia', 'formatos' (na ordem da tela), 'versao', 'edicoes', 'arquivo_de_edicao' (opcional)};
    derivados: {id: derivacao/1 em memoria}; versoes: {id: {id da versao: variante do motor}}; tintas: as das linhas
    do DA, medidas no arquivo de edicao (tintas_editadas); cache: um dict para guardar a mestre e os contextos.
    Cada layout leva 'cf', 'caminho', 'mestre', 'arquivo_de_edicao', 'situacao' ('arquivo_de_edicao' no de edicao;
    igual, ajustado ou pede_ajuste nos outros), 'frases', 'transferencia' (None no de edicao), 'versao' (o id efetivo
    da versao de partida no arquivo de edicao, None na proposta derivada) e 'figura_de_fundo' (o id da figura que fica
    de fundo neste arquivo, decisoes-v1.md, n 202, ou None). O arquivo cuja copia quebra fica {'erro': nome do erro}.
    Sem layout no arquivo de edicao (devolvido sem versao), todos ficam None.
    Decisao 215: a caixa copiada de outra familia que nao vale mais (caixas_que_valem) sai, e o arquivo de edicao
    leva 'copia_sem_efeito' ({'arquivo', 'medida'} ou None); com a copia, a figura de fundo e a do layout copiado
    (edicao.fundo_copiado), e o arquivo de edicao leva tambem 'edicoes_efetivas' e 'copiado_de' (o da familia, quando
    alguma caixa copiada vale)."""
    from vapt.derivacao import galeria as mg
    from vapt.derivacao import solver as mod_solver
    from vapt.tela import edicao
    kw = {'specs': specs, 'arquivo_specs': arquivo_specs, 'params': params}
    cache = {} if cache is None else cache
    por_id = {f['id']: f for f in ctx['briefing']['formatos']}
    fids = [f for f in familia['formatos'] if f in por_id and f in derivados]
    saida = {f: None for f in fids}
    if not fids:
        return saida
    ref = arquivo_de_edicao([por_id[f] for f in fids], familia.get('arquivo_de_edicao'))
    edicoes = list(familia.get('edicoes') or [])
    # decisao 215: a caixa copiada de outra familia so vale no arquivo de edicao e na medida em que foi copiada
    edicoes, sem_efeito = caixas_que_valem(edicoes, ref, [membros_na_composicao([por_id[ref]])[0][k]
                                                          for k in ('W', 'H')])
    d_ref = derivados[ref]
    vid = None
    if (d_ref or {}).get('situacao') == 'derivado':
        elementos, caminho = d_ref['elementos'], d_ref['caminho']
    elif usa_galeria(d_ref) and (versoes or {}).get(ref):
        elementos, caminho = partida(None, versoes[ref], familia.get('versao')), 'galeria'
        # o id efetivo da versao de partida (tambem sem escolha do DA): diz se a figura fica de fundo (n 202)
        vid = versao_de_partida(None, versoes[ref], familia.get('versao'))
    else:
        return saida
    if elementos is None:
        return saida
    # 0.15.0 (decisoes-v1.md, 204): os grafismos que a versao tirou saem como apagados, menos os que o DA devolveu
    tir = list((versoes[ref][vid].get('tirados') or ()) if vid is not None else ())
    edicoes = edicoes_efetivas(tir, edicoes)
    # decisao 215: com a copia de outra familia, a figura de fundo e a do layout copiado, nunca a do id da versao
    fundo_cop = edicao.fundo_copiado(edicoes)
    if ('mestre', ref) not in cache:
        # a mesma mestre da tela (Editor._contexto) e da derivacao: a da proposta, ou a da galeria
        cache[('mestre', ref)] = mestre_do_membro(ctx, kv, por_id[ref], d_ref)
    mestre = cache[('mestre', ref)]

    def contexto(fid):
        if ('cf', fid, ref) not in cache:
            cache[('cf', fid, ref)] = mg.contexto_do_formato(ctx, mestre, por_id[fid], **kw)
        return cache[('cf', fid, ref)]
    extra = {'kv_por_id': {e['id']: e for e in kv['elementos']},
             'conteudo': [e['id'] for e in kv['elementos'] if mod_solver.conteudo(e)],
             'kv_caixas': {e['id']: [float(x) for x in e['caixa']] for e in kv['elementos']},
             'kv_tamanho': (float(kv['largura']), float(kv['altura']))}
    cf_ref = contexto(ref)
    # a figura de fundo da versao de partida no arquivo de edicao (decisoes-v1.md, n 202): a mesma regra da galeria,
    # para a previa, a copia e o "Salvar e seguir" verem o mesmo
    fundo_ref = fundo_cop if fundo_cop is not None else mg.fundo_da_versao(cf_ref, vid)
    lay_ref = layout_do_membro(cf_ref, elementos, edicoes, tintas=tintas, fundo=fundo_ref,
                               alinhamentos=alinhamentos_do_da(ctx, kv, edicoes), **extra)
    lay_ref.update(cf=cf_ref, caminho=caminho, mestre=mestre, arquivo_de_edicao=ref, situacao='arquivo_de_edicao',
                   frases=[], transferencia=None, versao=vid, tirados=[k for k in tir if k in lay_ref['apagados']],
                   copia_sem_efeito=sem_efeito, edicoes_efetivas=edicoes,
                   copiado_de=familia.get('copiado_de') if lay_ref['copiados'] else None)
    saida[ref] = lay_ref
    outros = [f for f in fids if f != ref and (derivados[f]['situacao'] == 'derivado' or usa_galeria(derivados[f]))]
    if not outros:
        return saida
    modelo = _modelo(ctx, cf_ref, lay_ref, edicoes, ref)
    membros = {m['id']: m for m in membros_na_composicao([por_id[f] for f in outros])}
    for fid in outros:
        try:
            cf = contexto(fid)
            # a regra da figura de fundo pela orientacao deste arquivo, so quando ela ja e fundo no arquivo de edicao
            # (decisao 215: com a copia, a figura copiada, pela mesma regra de orientacao)
            if fundo_cop is not None:
                fundo = fundo_cop if fundo_cop and mg.fundo_elegivel(cf) else ()
            else:
                fundo = mg.fundo_da_versao(cf, vid) if fundo_ref else ()
            lay = _copia(ctx, cf, modelo, lay_ref, dict(membros[fid], quadros=quadros_do_membro(cf)), fundo=fundo)
        except Exception as e:  # noqa: BLE001 - o arquivo fica como o motor o deixou, com o registro
            saida[fid] = {'erro': type(e).__name__}
            continue
        lay.update(cf=cf, caminho=CAMINHO_FAMILIA, mestre=mestre, arquivo_de_edicao=ref, versao=vid)
        saida[fid] = lay
    return saida


# ------------------------------------------------------------------ a copia do layout de outra familia (215)
# Casas da fracao da caixa copiada. A ida a mestre (_levar) amplia o arredondamento pela razao entre a
# caixa na mestre (doc) e a caixa copiada: com 7 casas, a copia do 300x600 para o 1080x1920 do KV da diagonal passava
# de TOL_COPIA (revisao 2 da 215); com 10, o desvio fica abaixo de 1e-6 px
CASAS_FRACAO = 10  # numero-neutro: casas da fracao da caixa copiada (o arredondamento, nao uma regra)
CASAS_DOC = 4  # numero-neutro: casas da caixa da mestre na caixa copiada, as da caixa em px


def escala_da_copia(quadros_o, quadros_d):
    """A escala unica s da copia do layout de outra familia (decisao 215): a mesma conta da 199
    (vapt.derivacao.familia.escala_unica), com os quadros do arquivo de edicao da origem (quadros_o) e do destino
    (quadros_d), na forma de quadros_do_membro. Nunca passa de 1."""
    from vapt.derivacao import familia as mod_familia
    return mod_familia.escala_unica(quadros_d, quadros_o)


def copia_entre_familias(ctx_o, kv, lay_o, formato_d, *, specs, arquivo_specs, params):
    """O layout do arquivo de edicao de outra familia (lay_o: o layout do arquivo de edicao da origem, de
    layout_da_familia, com 'cf', 'mestre', 'edicoes_efetivas' e 'arquivo_de_edicao') levado ao arquivo formato_d
    (decisao 215): a conta da 199 (_modelo, transferir, ajustar_minimo e conferir_edicao, com s <= 1), com a mestre da
    origem, as quebras e o texto dela. ctx_o: o contexto da derivacao em que lay_o saiu (com as quebras da origem).
    A figura de fundo da origem continua de fundo (as duas familias tem a mesma orientacao). Devolve o layout na forma
    de _copia, com 'cf' (o contexto do destino com a mestre da origem). Puro: nada e gravado."""
    from vapt.derivacao import galeria as mg
    kw = {'specs': specs, 'arquivo_specs': arquivo_specs, 'params': params}
    cf_t = mg.contexto_do_formato(ctx_o, lay_o['mestre'], formato_d, **kw)
    modelo = _modelo(ctx_o, lay_o['cf'], lay_o, lay_o['edicoes_efetivas'], lay_o['arquivo_de_edicao'])
    membro = dict(membros_na_composicao([formato_d])[0], quadros=quadros_do_membro(cf_t))
    fundo_t = (lay_o['figura_de_fundo'],) if lay_o.get('figura_de_fundo') else ()
    lay_t = _copia(ctx_o, cf_t, modelo, lay_o, membro, fundo=fundo_t)
    lay_t['cf'] = cf_t
    return lay_t


def _do_da_da_origem(lay_o):
    return set(lay_o['mexidos']) | {a['elementos'][0] for a in lay_o['alinhados']} | set(lay_o['textos']) | \
        set(lay_o.get('copiados_do_da') or ())


def edicoes_da_copia(lay_t, lay_o, kv):
    """As edicoes que a copia do layout de outra familia grava no destino (decisao 215), nesta ordem, que substitui
    todas as edicoes dele: o texto editado (lay_o['textos']), o alinhamento das linhas (lay_o['alinhamentos']), os
    apagados (lay_o['apagados'], com os tirados da versao da origem que o DA nao devolveu) e a 'caixa' de cada
    elemento de lay_t (a copia, de copia_entre_familias), na ordem do KV. A caixa e a de geometria em fracao do
    arquivo de edicao do destino (CASAS_FRACAO), com a caixa do elemento na mestre da copia (doc), a sangra, a
    sangria do DA, do_da (o elemento era decisao do DA na origem), piso_do_da (o piso furado do elemento ja era decisao
    do DA na origem: so esse piso continua decisao no destino; o que so a copia fura e falha) e fundo (a figura de
    fundo do layout copiado)."""
    from vapt.derivacao import galeria as mg
    ordem = [e['id'] for e in kv['elementos']]
    saida = [{'elemento': k, 'acao': 'texto', 'texto': lay_o['textos'][k]} for k in ordem if k in lay_o['textos']]
    alin = lay_o.get('alinhamentos') or {}
    saida += [{'elemento': k, 'acao': 'alinhar_texto', 'alinhamento': alin[k]} for k in ordem if k in alin]
    saida += [{'elemento': k, 'acao': 'apagar'} for k in lay_o['apagados']]
    cf_t = lay_t['cf']
    W, H = float(cf_t['W']), float(cf_t['H'])
    da_mestre = {e['id']: e for e in cf_t['kv']['elementos']}
    do_da = _do_da_da_origem(lay_o)
    piso_da = {k for f in lay_o['decisoes_do_da'] if f['codigo'] in mg.PISOS_DO_DA
               for k in f['elementos'] if k in do_da}
    for k in ordem:
        c = lay_t['caixas'].get(k)
        if c is None or k not in da_mestre:
            continue
        ed = {'elemento': k, 'acao': 'caixa', 'arquivo': cf_t['formato']['id'], 'medida': [W, H],
              'caixa': [round(float(c[0]) / W, CASAS_FRACAO), round(float(c[1]) / H, CASAS_FRACAO),
                        round(float(c[2]) / W, CASAS_FRACAO), round(float(c[3]) / H, CASAS_FRACAO)],
              'doc': [round(float(v), CASAS_DOC) for v in da_mestre[k]['caixa']],
              'sangra': {lado: bool(v) for lado, v in
                         (lay_t['sangra'].get(k) or da_mestre[k]['sangra']).items()}}
        if lay_t['sangria_do_da'].get(k):
            ed['sangria_do_da'] = list(lay_t['sangria_do_da'][k])
        if k in do_da:
            ed['do_da'] = True
        if k in piso_da:
            ed['piso_do_da'] = True
        if k == lay_t.get('figura_de_fundo'):
            ed['fundo'] = True
        saida.append(ed)
    return saida


def _camadas_de_texto(ctx, e):
    from vapt.briefing import modelo as mb
    cam = mb.camadas_do_laudo(ctx['laudo'])
    return [(lid, cam[lid]) for lid in e['layer_ids'] if (cam.get(lid) or {}).get('tipo') == 'texto']


def _com_faixa(derivado):
    # a mesma condicao de mestre_do_membro: a quebra da faixa (M5) so vale no formato derivado com a mestre do KV
    d = derivado or {}
    return d.get('situacao') == 'derivado' and (d.get('mestre') or {}).get('tipo', 'kv') == 'kv'


def _faixa(ctx, lid, camada, formato):
    """Os indices que a quebra da faixa (M5) deixa no texto do KV neste formato, ou None quando ela nao muda nada."""
    from vapt.derivacao import formatos as mod_formatos
    from vapt.derivacao import quebras as mq
    n = len(mq.posicoes_de_quebra(camada))
    if not n:
        return None
    W, H = mod_formatos.composicao(formato)
    manter = mq.aprovadas_para(ctx['briefing'], lid, formato, W, H)
    if manter is None or sorted(manter) == list(range(n)):
        return None
    return sorted(manter)


def quebras_da_copia(ctx_o, kv, lay_o, quebras_o, formato_o, derivado_o, edicoes_o):
    """As quebras de linha que a copia do layout de outra familia grava no destino (decisao 215), no formato do
    rascunho, para o destino ter as mesmas linhas da origem: (1) as entradas do rascunho da origem (quebras_o), menos
    as dos elementos apagados; as posicoes contam no texto de agora, que e o mesmo porque o texto editado vai junto;
    (2) so quando o arquivo de edicao da origem e derivado com a mestre do KV (derivado_o; a condicao de
    mestre_do_membro), a quebra da faixa (M5) que mudava o texto do KV vira entrada explicita (origem 'da', aprovada).
    O texto editado nunca ganha entrada de faixa: a faixa nao vale nele. formato_o: o arquivo de edicao da origem;
    edicoes_o: as edicoes dela. Pura."""
    from vapt.derivacao import quebras as mq
    apagados = set(lay_o['apagados'])
    qs = [copy.deepcopy(q) for q in quebras_o or () if q['elemento'] not in apagados]
    if not _com_faixa(derivado_o):
        return qs
    tem = {q['layer_id'] for q in qs}
    for e in kv['elementos']:
        if e['id'] in apagados or e['id'] not in lay_o['caixas'] or \
                mq.texto_editado(edicoes_o, e['id']) is not None:
            continue
        for lid, c in _camadas_de_texto(ctx_o, e):
            manter = None if lid in tem else _faixa(ctx_o, lid, c, formato_o)
            if manter is not None:
                qs.append({'elemento': e['id'], 'layer_id': lid, 'manter': manter, 'inseridas': [], 'origem': 'da',
                           'aprovada': True})
    return qs


def quebras_neutras(ctx_d, kv, qs, edicoes, formato_d, derivado_d):
    """As entradas a mais para o destino derivado (decisao 215, passo 3): no arquivo de edicao do destino derivado com
    a mestre do KV, a quebra da faixa (M5) que a origem nao tinha mudaria as linhas do texto do KV; a entrada neutra
    (todos os indices, nada inserido) a desfaz. So no texto do KV sem entrada em qs, do elemento que fica (edicoes:
    as do destino). Devolve so as entradas novas. Pura."""
    from vapt.derivacao import quebras as mq
    if not _com_faixa(derivado_d):
        return []
    tem = {q['layer_id'] for q in qs}
    apagados = {e['elemento'] for e in edicoes if e['acao'] == 'apagar'}
    novas = []
    for e in kv['elementos']:
        if e['id'] in apagados or mq.texto_editado(edicoes, e['id']) is not None:
            continue
        for lid, c in _camadas_de_texto(ctx_d, e):
            if lid not in tem and _faixa(ctx_d, lid, c, formato_d) is not None:
                novas.append({'elemento': e['id'], 'layer_id': lid,
                              'manter': list(range(len(mq.posicoes_de_quebra(c)))), 'inseridas': [],
                              'origem': 'da', 'aprovada': True})
    return novas


def _origem_do_apagado(ctx, comp):
    conf = comp.get('confirmacao') or {}
    if conf.get('origem') in ORIGENS_DO_APAGADO:
        return conf['origem']
    o = ctx['briefing']['cabecalho']['origem']
    return o if o in ORIGENS_DO_APAGADO else ORIGEM_DA


def _quebras_do_editado(ctx, x, fid):
    """As quebras do elemento com texto editado pelo DA: as do texto dele (QUEBRAS_DO_TEXTO_EDITADO), ou a quebra da
    familia da tela sobre o texto novo (M7b, C2), sem caixa medida."""
    from vapt.derivacao import quebras as mq
    x.pop('quebras_camada', None)
    fams = mq.da_familia_no_formato(ctx['briefing'], x['layer_ids'], fid)
    if not fams:
        x['quebras'] = QUEBRAS_DO_TEXTO_EDITADO
        return
    x['quebras'] = {'familia': [mq.item_da_familia(lid, f) for lid, f in fams]}
    x['quebras_origem'] = mq.origem_das([f for _lid, f in fams])


def _caixas_editadas(ctx, elementos):
    """A caixa medida do texto editado de cada elemento (Linhas do DA, 0.9.4), no espaco do documento: {id do elemento:
    (caixa_doc ou None, motivo da falta ou None)}. As linhas sao as do DA (derivacao.quebras.linhas_editadas, com a
    quebra da familia do elemento), com o mesmo corpo; a tinta e medida no Chromium com o cache
    (derivacao.medida_quebras.medir_editados). O elemento com mais de um texto fica com a caixa que junta todos. Com o
    alinhamento do DA (0.12.0, x['alinhamento_do_da']), a tinta sai pela justificacao nova, com a linha mais larga no
    lugar."""
    por_el, medidas, motivo = _medidas_editadas(ctx, elementos)
    return _caixas_das_medidas(por_el, medidas, motivo)


def _medidas_editadas(ctx, elementos):
    """(por_el {id do elemento: [(layer_id, chave)]}, medidas {chave: medida}, motivo da falta de todas ou None) do
    texto editado de cada elemento (_caixas_editadas)."""
    from pathlib import Path

    from vapt import contratos
    from vapt.briefing import modelo as mb
    from vapt.derivacao import medida_quebras
    from vapt.derivacao import quebras as mq
    cam = mb.camadas_do_laudo(ctx['laudo'])
    pedidos, por_el = [], {}
    for x in elementos:
        if x.get('texto_editado') is None:
            continue
        fam = {i['layer_id']: i for i in ((x.get('quebras') or {}).get('familia') or [])} \
            if isinstance(x.get('quebras'), dict) else {}
        j = mq.ALINHAMENTO_PARA_JUSTIFICACAO.get((x.get('alinhamento_do_da') or {}).get('alinhamento'))
        por_el[x['id']] = []
        for lid in x['layer_ids']:
            if (cam.get(lid) or {}).get('tipo') != 'texto':
                continue
            linhas = mq.linhas_editadas(x['texto_editado'], fam.get(lid))
            pedidos.append((lid, linhas) if j is None else (lid, linhas, j))
            por_el[x['id']].append((lid, mq.chave_editado(lid, linhas, j)))
    if not pedidos:
        return {}, {}, None
    medidas, motivo = {}, None
    pasta = ctx.get('pasta')
    try:
        estado = contratos.ler(Path(pasta) / 'estado.json', 'estado/1') if pasta else None
        if estado is None:
            motivo = 'sem_job'
        else:
            medidas = medida_quebras.medir_editados(pasta, ctx['laudo'], estado, pedidos)
    except (contratos.ErroContrato, OSError, ValueError, KeyError):
        motivo = 'sem_medida'
    return por_el, medidas, motivo


def _caixas_das_medidas(por_el, medidas, motivo):
    saida = {}
    for eid, pares in por_el.items():
        caixa, falta = None, motivo
        for _lid, ch in pares:
            m = medidas.get(ch) or {}
            if 'caixa_doc' not in m:
                falta = falta or m.get('erro') or 'sem_medida'
                continue
            c = m['caixa_doc']
            caixa = list(c) if caixa is None else [min(caixa[0], c[0]), min(caixa[1], c[1]), max(caixa[2], c[2]),
                                                  max(caixa[3], c[3])]
        saida[eid] = (None, falta or 'sem_medida') if caixa is None or falta else (caixa, None)
    return saida


def _quebras_do_render(x, camada, lid):
    """(manter, inseridas) das quebras que o render aplica no texto do KV layer_id do elemento x
    (render.derivado.quebras_da_entrada): as da familia, as da mestre propria, ou todas as gravadas e nenhuma
    inserida."""
    from vapt.derivacao import quebras as mq
    q = x.get('quebras')
    if isinstance(q, dict):
        item = next((i for i in q.get('familia') or [] if i['layer_id'] == lid), None)
        if item is not None:
            return list(item['aprovadas']), list(item.get('inseridas') or ())
    todas = list(range(len(mq.posicoes_de_quebra(camada))))
    if isinstance(q, list) and x.get('quebras_camada') == lid:
        return todas, list(q)
    return todas, []


def _alinhamentos_medidos(ctx, elementos, por_el, medidas_ed):
    """As camadas do alinhamento do DA (0.12.0) de cada elemento com x['alinhamento_do_da'], no lugar, e os registros
    da medida que falta. O texto editado ja foi medido com a justificacao nova (_medidas_editadas: o desvio vem de la);
    o texto do KV e medido aqui (derivacao.medida_quebras.medir_alinhados), com as quebras que o render aplica, e a
    caixa medida (caixa_doc, no documento) e a caixa validada do render. Sem medida, a camada fica so com a
    justificacao: o render desenha o texto como o KV e registra (texto_alinhado_sem_medida)."""
    from pathlib import Path

    from vapt import contratos
    from vapt.briefing import modelo as mb
    from vapt.derivacao import medida_quebras
    from vapt.derivacao import quebras as mq
    alinhados = [x for x in elementos if x.get('alinhamento_do_da')]
    if not alinhados:
        return []
    cam = mb.camadas_do_laudo(ctx['laudo'])
    pedidos, chaves = [], {}
    for x in alinhados:
        j = mq.ALINHAMENTO_PARA_JUSTIFICACAO[x['alinhamento_do_da']['alinhamento']]
        if x.get('texto_editado') is not None:
            continue
        for lid in x['layer_ids']:
            c = cam.get(lid) or {}
            if c.get('tipo') != 'texto':
                continue
            manter, inseridas = _quebras_do_render(x, c, lid)
            pedidos.append((lid, manter, inseridas, j))
            chaves[(x['id'], lid)] = mq.chave_alinhado(lid, manter, inseridas, j)
    medidas, motivo = {}, None
    if pedidos:
        pasta = ctx.get('pasta')
        try:
            estado = contratos.ler(Path(pasta) / 'estado.json', 'estado/1') if pasta else None
            if estado is None:
                motivo = 'sem_job'
            else:
                medidas = medida_quebras.medir_alinhados(pasta, ctx['laudo'], estado, pedidos)
        except (contratos.ErroContrato, OSError, ValueError, KeyError):
            motivo = 'sem_medida'
    registros = []
    for x in alinhados:
        j = mq.ALINHAMENTO_PARA_JUSTIFICACAO[x['alinhamento_do_da']['alinhamento']]
        if x.get('texto_editado') is not None:
            pares = por_el.get(x['id']) or []
            achadas = [(lid, medidas_ed.get(ch) or {}) for lid, ch in pares]
        else:
            achadas = [(lid, medidas.get(ch) or {}) for (eid, lid), ch in sorted(chaves.items()) if eid == x['id']]
        camadas, falta = [], None
        for lid, m in achadas:
            item = {'layer_id': lid, 'justificacao': j}
            if 'desvio' in m:
                item['desvio'] = m['desvio']
                if x.get('texto_editado') is None and 'caixa_doc' in m:
                    item['caixa_doc'] = list(m['caixa_doc'])
            else:
                falta = falta or motivo or m.get('erro') or 'sem_medida'
            camadas.append(item)
        x['alinhamento_do_da']['camadas'] = camadas
        if falta or not camadas:
            registros.append({'codigo': 'texto_alinhado_sem_medida',
                              'medidas': {'elemento': x['id'], 'motivo': falta or motivo or 'sem_medida'}})
    return registros


def _no_formato(tr, c):
    s = float(tr['s'])
    o, d = tr['origem_doc'], tr['destino']
    return [s * (float(c[0]) - o[0]) + d[0], s * (float(c[1]) - o[1]) + d[1],
            s * (float(c[2]) - o[0]) + d[0], s * (float(c[3]) - o[1]) + d[1]]


def lados_fora(caixa, W, H, tol):
    """Os lados em que a caixa passa da borda do formato W x H alem de tol."""
    return [lado for lado, fora in (('esq', caixa[0] < -tol), ('topo', caixa[1] < -tol), ('dir', caixa[2] > W + tol),
                                    ('base', caixa[3] > H + tol)) if fora]


def aviso_aprovado_pelo_da(lay, ruins, registros):
    """As medidas do registro aprovado_pelo_da_com_aviso (0.9.6): as falhas da conferencia que o DA viu na previa
    ({'codigo', 'texto', 'elementos', 'medidas'}), as validacoes do motor que reprovam (nome, elementos, fonte e
    medidas) e os lados em que o texto editado passa da borda (o render corta ali, como o palco mostra). {} sem
    nada."""
    falhas = [{'codigo': f['codigo'], 'texto': f.get('texto') or '', 'elementos': list(f.get('elementos') or []),
               'medidas': dict(f.get('medidas') or {})} for f in lay.get('falhas') or []]
    validacoes = [{'nome': v['nome'], 'elementos': list(v.get('elementos') or []), 'fonte': v.get('fonte'),
                   'medidas': v.get('medidas')} for v in ruins]
    borda = [dict(r['medidas']) for r in registros if r.get('codigo') == 'texto_editado_passa_da_borda']
    if not (falhas or validacoes or borda):
        return {}
    return {'falhas': falhas, 'validacoes': validacoes, 'texto_na_borda': borda}


def _derivacao(ctx, kv, cf, d, lay, caminho, proposta, origem_apagado, d_ref=None):
    """A derivacao/1 do membro a partir do layout com as edicoes (layout_do_membro). cf: o contexto do formato, com a
    mestre de onde o membro partiu (mestre_do_membro). Na copia do arquivo de edicao (caminho 'familia', decisao 199;
    d_ref: a derivacao/1 em memoria do arquivo de edicao), as quebras de linha sao as dele, cada elemento leva a
    origem 'familia', e o registro transferencia leva o arquivo de edicao, a escala, o crescimento das bases, as
    ancoras, os ajustes e as relacoes quebradas. Decisao 215: o elemento com a caixa copiada de outra familia leva a
    origem 'da'; o registro layout_de_outra_familia diz de onde veio a copia, e layout_de_outra_familia_sem_efeito diz
    que as caixas copiadas deixaram de valer. O caminho nao muda."""
    from vapt.derivacao import galeria as mg
    from vapt.derivacao import nucleo as nd
    from vapt.derivacao import validacao as mv
    novo = copy.deepcopy(d)
    kv_por_id = {e['id']: e for e in kv['elementos']}
    copia = caminho == CAMINHO_FAMILIA
    # a mestre do membro: a quebra da familia da tela que ela traz (quebras_origem e quebra_do_da, nucleo._com_quebras)
    da_mestre = {e['id']: e for e in cf['kv']['elementos']}
    # decisao 215: a caixa copiada de outra familia e escolha do DA (o ato da copia)
    do_da = set(lay['mexidos']) | {a['elementos'][0] for a in lay['alinhados']} | set(lay['textos']) | \
        set(lay.get('copiados') or ())
    # de onde vem a quebra de linha aprovada: a proposta do proprio membro, ou a do arquivo de edicao na copia
    fonte = d_ref if copia else d
    antes = {e['id']: e for e in fonte['elementos']} if (fonte or {}).get('situacao') == 'derivado' else {}
    fid_quebras = fonte['formato']['id'] if copia else d['formato']['id']
    base = ORIGEM_POR_CAMINHO[caminho]
    elementos = []
    for e in lay['elementos']:
        x = dict(e)
        o = antes.get(e['id'])
        m = da_mestre.get(e['id']) or {}
        if e['id'] in lay['textos']:
            # o texto editado leva so as quebras do DA, nunca as da proposta junto com as linhas dele (M7b, A7); a
            # quebra da familia vale sobre o texto novo (C2)
            _quebras_do_editado(ctx, x, fid_quebras)
        elif o is not None:
            # as quebras aprovadas da familia ficam as da proposta derivada (o render as aplica)
            for k in ('quebras', 'quebras_camada', 'quebras_origem'):
                if k in o:
                    x[k] = o[k]
        elif m.get('quebras_origem') is not None:
            # a versao da galeria: a quebra da familia veio da mestre da galeria
            x['quebras_origem'] = m['quebras_origem']
        x['regra_aplicada'] = {'funcao': e['funcao'], 'regra': e['regra'], 'caminho': caminho, 'classe': e['classe']}
        if copia:
            # a caixa veio da copia do layout aprovado no arquivo de edicao (199, 2)
            x['origem_geometria'] = base
        elif e['id'] in do_da or (e['id'] not in lay['textos'] and m.get('quebra_do_da')):
            # mexido, alinhado, com texto editado, ou com a quebra de linha que o DA fez ou aprovou na familia
            x['origem_geometria'] = ORIGEM_DA
        else:
            # o que o DA nao mexeu fica com a caixa e a origem da versao de partida (0.9.5: nada refaz o encaixe)
            x['origem_geometria'] = base
        if e['id'] in lay['textos']:
            x['texto_editado'] = lay['textos'][e['id']]
            vis = (lay.get('caixas_visiveis') or {}).get(e['id'])
            if vis is not None and vis is not (lay.get('caixas') or {}).get(e['id']):
                # 0.9.6 (decisao 196): a caixa gravada do texto editado e a das linhas do DA, a mesma do palco; a
                # escala e o destino da transformacao continuam os da geometria
                x['caixa'] = [nd._q(v, nd.CASAS_PX) for v in vis]
        if e['id'] in lay['sangria_do_da']:
            # os lados que o DA deixou passar da borda (M7b, D4): o render corta no quadro
            x['sangria_do_da'] = list(lay['sangria_do_da'][e['id']])
        if e['id'] in (lay.get('alinhamentos') or {}):
            # 0.12.0: o alinhamento das linhas que o DA escolheu; as camadas (a justificacao, o desvio da ancora e a
            # caixa medida) saem da medida abaixo. A geometria nao muda: a origem fica a de antes
            x['alinhamento_do_da'] = {'alinhamento': lay['alinhamentos'][e['id']], 'camadas': []}
        elementos.append(x)
    registros = list(d['registros'])
    cop = lay.get('copiado_de')
    if lay.get('copiados') and cop:
        # decisao 215: o layout do arquivo de edicao veio do de outra familia
        registros.append({'codigo': 'layout_de_outra_familia', 'medidas': dict(
            {k: cop[k] for k in ('familia', 'arquivo', 'para', 's', 'situacao') if k in cop},
            elementos=sorted(lay['copiados']))})
    if lay.get('copia_sem_efeito'):
        registros.append({'codigo': 'layout_de_outra_familia_sem_efeito',
                          'medidas': {'arquivo': lay['copia_sem_efeito']['arquivo'],
                                      'medida': list(lay['copia_sem_efeito']['medida'])}})
    # Linhas do DA (0.9.4): a caixa do texto editado e a tinta medida das linhas dele, com o mesmo corpo. O render a
    # usa como caixa validada; o texto que passa da borda do formato fica registrado aqui e sai cortado nessa borda,
    # com registro (0.9.6; vapt.render.derivado.montar)
    from vapt import limites
    tol = float(limites.valor('derivacao.enquadramento_tolerancia_px'))
    por_el, medidas_ed, motivo_ed = _medidas_editadas(ctx, elementos)
    registros.extend(_alinhamentos_medidos(ctx, elementos, por_el, medidas_ed))
    for eid, (caixa, falta) in sorted(_caixas_das_medidas(por_el, medidas_ed, motivo_ed).items()):
        x = next(e for e in elementos if e['id'] == eid)
        if caixa is None:
            registros.append({'codigo': 'texto_editado_sem_medida', 'medidas': {'elemento': eid, 'motivo': falta}})
            continue
        c = [round(v, 2) for v in _no_formato(x['transformacao'], caixa)]  # numero-neutro: casas do px
        x['caixa_texto_editado'] = c
        lados = lados_fora(c, cf['W'], cf['H'], tol)
        if lados:
            registros.append({'codigo': 'texto_editado_passa_da_borda', 'medidas': {'elemento': eid, 'lados': lados}})
    if copia:
        # a copia do arquivo de edicao (199, 2 e 3): o registro e a frase de cada ajuste e de cada relacao quebrada
        medidas = dict(lay['transferencia'], situacao=lay['situacao'])
        if d['situacao'] == 'devolvido':
            medidas['motivo_da_devolucao'] = d['devolucao']['motivo']
        registros.append({'codigo': CODIGO_TRANSFERENCIA, 'medidas': medidas})
        novo['mestre'] = {'id': kv['id'], 'tipo': 'kv', 'largura': kv['largura'], 'altura': kv['altura']}
        novo['restricoes'] = []
    elif d['situacao'] == 'devolvido':
        registros.append({'codigo': 'proposta_da_galeria', 'medidas': {'motivo_da_devolucao': d['devolucao']['motivo']}})
        novo['mestre'] = {'id': kv['id'], 'tipo': 'kv', 'largura': kv['largura'], 'altura': kv['altura']}
        novo['restricoes'] = []
    else:
        registros.append({'codigo': 'editado_pelo_da', 'medidas': {'edicoes': proposta['edicoes']}})
    if lay['falhas']:
        registros.append({'codigo': 'proposta_com_falha',
                          'medidas': {'falhas': sorted({f['codigo'] for f in lay['falhas']})}})
    if lay['decisoes_do_da']:
        # o piso que o DA furou com a edicao dele (M7b, D5): fica registrado com o valor, sem virar falha
        registros.append({'codigo': 'decisao_do_da',
                          'medidas': {'decisoes': [{'codigo': x['codigo'], 'elementos': list(x['elementos']),
                                                    'medidas': dict(x.get('medidas') or {})}
                                                   for x in lay['decisoes_do_da']]}})
    fx = lay.get('figura_de_fundo')
    if fx in lay['apagados']:
        # a figura que o DA apagou nao fica de fundo: nao esta nos elementos
        fx = None
    if fx is not None:
        # decisoes-v1.md, n 202: a foto fica de fundo neste arquivo, e o conteudo sobre ela foi aprovado. O registro e
        # o campo do elemento dizem isso ao render, a entrega e o painel sem refazer a galeria
        registros.append({'codigo': 'figura_de_fundo', 'medidas': {'elemento': fx, 'versao': lay.get('versao')}})
        for x in elementos:
            if x['id'] == fx:
                x['figura_de_fundo'] = True
    # a conferencia ve a caixa que o DA ve (0.9.6): o texto editado nas linhas dele; a escala sai da geometria
    # sem a figura de fundo, a chamada de antes (quem troca validacoes_do_layout, como os testes, continua valendo)
    validacoes = mg.validacoes_do_layout(cf, lay.get('caixas_visiveis') or lay['caixas'], lay['sangra'],
                                         lay['apagados'], geometria=lay['caixas'],
                                         **({} if fx is None else {'fundo': (fx,)}))
    novo.update(elementos=elementos, validacoes=validacoes, caminho=caminho, situacao='derivado', devolucao=None,
                registros=registros, proposta=dict(proposta),
                apagados_pelo_da=[{'elemento': k, 'layer_ids': list(kv_por_id[k]['layer_ids']), 'origem': origem_apagado}
                                  for k in lay['apagados']])
    ruins = mv.reprovadas(validacoes)
    if proposta.get('confirmada'):
        # a aprovacao do DA e soberana (0.9.6): a familia que ele confirmou olhando a previa nunca volta devolvida por
        # julgamento de composicao. O que a conferencia e as validacoes acham fica registrado com o valor, e o passo 5
        # mostra como aviso aceito por ele
        avisos = aviso_aprovado_pelo_da(lay, ruins, registros)
        if avisos:
            registros.append({'codigo': CODIGO_APROVADO_COM_AVISO, 'medidas': avisos})
        return novo
    if ruins:
        v = ruins[0]
        return nd._devolver(novo, nd._devolucao('validacao_obrigatoria_reprovou',
                                                restricao={'nome': v['nome'], 'forca': 'obrigatoria',
                                                           'fonte': v['fonte'], 'elementos': v['elementos'],
                                                           'medidas': v.get('medidas')},
                                                elementos=v['elementos'], validacoes=[x['nome'] for x in ruins]))
    return novo


def _conhecidos_gravados(ctx, comp):
    """Os formatos da composicao sem arquivo de edicao gravado (o briefing da 0.9.6) que ja tinham a derivacao gravada
    nesta familia (revisao da 0.10.0, a migracao): o arquivo de edicao sai deles, e o irmao novo copia o layout. Le so
    o JSON das derivacoes do job; sem pasta (a derivacao so em memoria) ou sem derivacao gravada, None."""
    from pathlib import Path

    from vapt import contratos
    from vapt.derivacao import nucleo as nd
    pasta = ctx.get('pasta')
    if not pasta:
        return None
    saida = []
    for fid in comp['formatos']:
        arq = Path(pasta) / nd.PASTA / ('%s.json' % fid)
        try:
            d = contratos.ler(arq, nd.ESQUEMA) if arq.is_file() else None
        except (contratos.ErroContrato, OSError, ValueError):
            d = None
        # o que ja saiu como copia (caminho familia) nunca conta: a escolha fica a mesma derivacao apos derivacao
        if d is not None and (d.get('proposta') or {}).get('familia') == comp['familia'] and \
                d.get('caminho') != CAMINHO_FAMILIA:
            saida.append(fid)
    return saida or None


def aplicar(ctx, kv, resultados, derivar_um, *, specs, arquivo_specs, params):
    """Aplica as composicoes do briefing (as familias confirmadas na tela) aos formatos de resultados ({id:
    derivacao/1}), no lugar. derivar_um(formato) deriva um membro da familia que nao esta em resultados (a derivacao
    de um formato so precisa dos outros devolvidos da familia para montar a galeria como a tela)."""
    comps = ctx['briefing'].get('composicoes') or []
    if not comps:
        return resultados
    kw = {'specs': specs, 'arquivo_specs': arquivo_specs, 'params': params}
    por_id = {f['id']: f for f in ctx['briefing']['formatos']}
    for comp in comps:
        alvo = [f for f in comp['formatos'] if f in resultados]
        if not alvo:
            continue
        dos = {}
        for f in comp['formatos']:
            if f in resultados:
                dos[f] = resultados[f]
            elif f in por_id:
                dos[f] = derivar_um(por_id[f])
        proposta = {'familia': comp['familia'], 'versao': comp['versao'], 'edicoes': len(comp['edicoes']),
                    'confirmada': bool(comp['confirmada']), 'confirmacao': comp.get('confirmacao')}
        formatos = [por_id[f] for f in comp['formatos'] if f in dos and f in por_id]
        if not formatos:
            continue
        # decisao 199: o arquivo de edicao da familia (o mesmo da tela) e o unico que parte da galeria ou da proposta;
        # os outros copiam o layout aprovado nele (layout_da_familia), com ou sem edicao (resposta 3 do Duda)
        ref = arquivo_de_edicao(formatos, comp.get('arquivo_de_edicao'),
                                None if comp.get('arquivo_de_edicao') else _conhecidos_gravados(ctx, comp))
        # a mesma galeria da tela, pela mesma regra (galeria_dos_devolvidos; vapt.tela.estado.galerias): a mestre
        # da galeria leva a quebra de linha da familia (M7b, C2); sem a medida dela, a galeria nao sai e o arquivo de
        # edicao fica como o motor o deixou, com o registro
        try:
            galeria, _kv_galeria, sem_medida = galeria_dos_devolvidos(ctx, kv, dos, formatos, arquivo=ref, **kw)
        except Exception as e:  # noqa: BLE001 - a galeria que quebra deixa os formatos como o motor os deixou
            galeria, sem_medida = None, []
            erro_galeria = type(e).__name__
        else:
            erro_galeria = None
        d_ref = dos[ref]
        # por que o arquivo de edicao fica sem layout (os outros arquivos da familia gravam o mesmo motivo)
        motivo_ref = None if d_ref['situacao'] == 'derivado' else (d_ref.get('devolucao') or {}).get('motivo')
        if d_ref['situacao'] == 'devolvido' and usa_galeria(d_ref):
            if galeria is None:
                # 0.9.6: o motivo fica gravado, e o passo 5 o diz (nunca "espera uma decisao sua em Familias")
                d_ref['registros'].append({'codigo': 'erro_na_galeria', 'medidas': {'erro': erro_galeria}})
                motivo_ref = 'erro_na_galeria'
            elif sem_medida:
                d_ref['registros'].append({'codigo': 'quebra_sem_medida', 'medidas': {'camadas': sem_medida}})
                galeria = None
                motivo_ref = 'quebra_sem_medida'
        # a medida das linhas do DA do texto editado (0.9.6; decisao 196), no arquivo de edicao, com a quebra dele:
        # a mesma tinta vale, escalada, em todo arquivo da familia
        tintas = tintas_editadas(ctx, kv, comp['edicoes'], ref) if comp['edicoes'] else {}
        try:
            lays = layout_da_familia(
                ctx, kv, dict(comp, arquivo_de_edicao=ref), derivados=dos, tintas=tintas,
                versoes={fid: {v['id']: v for _n, v in pares} for fid, pares in (galeria or {}).items()}, **kw)
        except Exception as e:  # noqa: BLE001 - os formatos ficam como o motor os deixou, com o registro
            for fid in alvo:
                dos[fid]['registros'].append({'codigo': 'erro_na_proposta', 'medidas': {'erro': type(e).__name__}})
            continue
        sem_arquivo = lays.get(ref) is None
        for fid in alvo:
            d, lay = dos[fid], lays.get(fid)
            if lay is None:
                if fid != ref and sem_arquivo and (d['situacao'] == 'derivado' or usa_galeria(d)):
                    # sem layout no arquivo de edicao, nao ha o que copiar: o arquivo fica como o motor o deixou
                    d['registros'].append({'codigo': 'familia_sem_arquivo_de_edicao',
                                           'medidas': {'arquivo_de_edicao': ref, 'motivo': motivo_ref}})
                if d['situacao'] == 'derivado':
                    d['proposta'] = dict(proposta)
                continue
            if 'erro' in lay:
                d['registros'].append({'codigo': 'erro_na_proposta', 'medidas': {'erro': lay['erro']}})
                continue
            if fid == ref and d['situacao'] == 'derivado' and not comp['edicoes']:
                # o arquivo de edicao sem edicao fica com a proposta do motor, como antes
                d['proposta'] = dict(proposta)
                continue
            try:
                resultados[fid] = _derivacao(ctx, kv, lay['cf'], d, lay, lay['caminho'], proposta,
                                             _origem_do_apagado(ctx, comp), d_ref=d_ref)
            except Exception as e:  # noqa: BLE001 - o formato fica como o motor o deixou, com o registro
                d['registros'].append({'codigo': 'erro_na_proposta', 'medidas': {'erro': type(e).__name__}})
    return resultados
