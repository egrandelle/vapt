# -*- coding: utf-8 -*-
"""Edicao da composicao no palco, por familia (M7a, fatia 4; decisoes-v1.md, 164, 166, 167, 168, 169, 171 e 185).

A familia (as composicoes de proporcao parecida de uma orientacao, vapt.tela.estado.agrupar_por_proporcao) recebe
as decisoes do DA de uma vez so, nunca peca a peca. Desde a decisao 199 (etapa E4), o DA edita so o arquivo de edicao
da familia (Editor.arquivo_de_edicao: o de maior area, em pe); o pedido que diz outro arquivo e recusado (conferir).
As regras abaixo valem nele, e os outros arquivos copiam o layout aprovado nele pela mesma conta do "Salvar e seguir"
(vapt.derivacao.proposta.layout_da_familia), cada um com a situacao (igual, ajustado ou pede_ajuste) e as frases:
  - o ponto de partida de cada membro e a versao da galeria que o DA escolheu (o formato devolvido) ou a proposta da
    derivacao (o formato derivado); sem escolha, a primeira versao sem falha, como a tela mostra;
  - cada edicao (mover, escalar, texto, apagar) e gravada em fracao do lado da peca e vai a cada membro em proporcao
    ao formato dele (aplicar);
  - o grupo (M7b, D1): mover e escalar podem levar a lista dos elementos escolhidos juntos no palco (elementos, o
    elemento da edicao e o primeiro dela). O grupo anda junto, e o escalar usa o ponto fixo em fracao da caixa que
    junta o grupo no formato: cada membro da familia escala o grupo em volta do mesmo ponto dele, e as distancias
    entre os elementos do grupo mudam na razao do tamanho. O grupo que fica (grupos) e o dos elementos que andaram
    juntos na ultima edicao de cada um; a intencao de alinhamento nunca o separa;
  - alinhar no quadro (M7b, D2): o elemento, ou o grupo, encosta na margem esquerda, na direita, no topo ou na base,
    ou fica no centro da largura ou da altura do quadro de cada membro (a margem dele ou a area segura dele). A
    intencao fica ate o DA mexer naquele eixo (intencoes): o alinhamento entre elementos nao a desfaz, e ela e firmada
    de novo no layout de cada membro (firmar);
  - a escala por numero (M7b, D3): o tamanho de cada elemento e a conta dos fatores das edicoes de escalar que o
    levam, sozinho ou no grupo (escalas); 100% e o tamanho antes das edicoes do DA, a versao de onde o membro parte. O
    campo Tamanho da pagina grava o escalar que leva do tamanho de agora ao digitado. O tamanho fica entre
    tela.escala_min e tela.escala_max (limites_da_escala): a previa e o rascunho recusam a edicao que passa disso
    (escala_fora). O tamanho que o rascunho gravado ja tinha fora dos limites (a tela de antes do D3) passa enquanto
    nao for para mais longe deles: o job nunca trava (revisao 1 da fase D). Em nenhum passo o tamanho sai do teto
    numerico, nem com o rascunho gravado (revisao 2 da fase D);
  - a sangria do DA (M7b, D4; pergunta 5 do plano, "So o DA ajusta"): o elemento, ou o grupo, que o DA mexeu ou
    escalou pode passar da borda do quadro em qualquer lado; o quadro corta o que fica fora (sangria_do_da). O lado
    vira sangria do elemento naquele membro: nada o puxa de volta e a conferencia nao o marca como defeito. O texto e a marca nunca sangram. O elemento que o DA tira da borda em que o asset dele acaba no KV fica
    onde o DA o pos, com o tamanho dele, e a conferencia pede ajuste porque o corte aparece (corte_a_mostra, revisao 1
    da fase D). No alinhamento no quadro, o elemento preso a borda daquele lado fica fora da linha do grupo e anda
    junto (caixa_da_linha). O elemento levado inteiro para fora da peca nao sangra: pede ajuste (fora_da_peca,
    revisao 2 da fase D);
  - o piso diante da intencao do DA (M7b, D5; pergunta 10 do plano): a escala abaixo do piso da 133 ou a distancia
    menor que a da 135 com um elemento que o DA mexeu ou escalou e decisao dele. A previa a leva em decisoes_do_da, com
    o valor no texto, e nao em falhas; a tela a mostra como "Decisão do DA", nunca como "Pede ajuste". A validacao
    do motor continua devolvendo o formato. O piso que
    a versao de partida ja furava, e a distancia de caixas que se sobrepoem, continuam falha (revisao 1 da fase D);
  - depois de cada edicao, a intencao de alinhamento (168, revista pela 185): so o elemento que o DA acabou de mexer
    (ou o grupo dele) anda. A borda ou o centro dele que fica a menos de derivacao.alinhamento_intencao_tolerancia do
    lado maior da peca da linha de um vizinho encaixa nela (normalizar); com o vizinho com quem ja se alinhava no KV,
    volta para a linha do KV. Nenhum outro elemento sai do lugar, nem o que o DA mexeu antes: o produto alinhado com o
    bloco de texto no KV nao acompanha o bloco. O mexido preso a uma linha do quadro nao anda naquele eixo. Acima da
    tolerancia, a diferenca e intencao do DA. A previa e o "Salvar e seguir" refazem as edicoes uma a uma, cada uma
    com o alinhamento na hora dela (editar), cada uma a partir do que a tela mostrou. O vizinho de cuja linha a edicao
    tirou o mexido nao o puxa de volta, e o eixo em que ele nao andou nao encaixa (o alinhar na largura nao muda a
    altura). O mexido que divide agora uma linha que ja dividia no KV com um terceiro fica nela, e a linha mais perto
    vem primeiro, sem depender da ordem dos cliques (revisao 2 da fase D);
  - o que o DA nao mexeu fica parado (decisao do Duda em 17/11, 0.9.5; revisa a 185 e o encaixe refeito do M7b):
    depois de qualquer edicao (mover, escalar, alinhar, texto, apagar), cada elemento fora dela fica com a caixa e o
    tamanho que a versao de partida, ou a edicao de antes, lhe deu. O motor nao reposiciona nada por conta propria. O
    layout de cada membro e conferido contra a mestre verdadeira (vapt.derivacao.galeria): quando o resultado
    sobrepoe elementos, sai do formato, passa da area segura ou fica mais perto do que o KV pede, a previa avisa (falhas
    ou decisoes_do_da), e o DA decide;
  - o texto editado precisa de todos os caracteres na face do job que o desenha (a cobertura do cmap lida pelo filho
    das fontes; o processo principal nunca abre a fonte); a previa leva o texto novo com a face real, e as linhas
    sao as do DA (Linhas do DA, 0.9.4): nada quebra na largura da caixa, e o texto cresce em volta da ancora com o
    mesmo corpo. A pagina mede a tinta e avisa quando ela passa da borda do formato. O texto vale so na familia
    editada (171), menos quando o DA copia o layout de outra familia (215): o texto copiado vira edicao desta
    familia. Cada caractere do texto editado fica com o estilo (face, cor, corpo, tracking) de um trecho do KV,
    pela regra por palavra (decisao 214; vapt.derivacao.quebras.runs_do_editado), e e conferido na face do trecho
    dele;
  - o elemento apagado sai de todos os membros, fica registrado com a origem do rascunho ('da', ou fixture_de_teste no
    modo de teste da tela) e deixa de reprovar o inventario (vapt.derivacao.validacao, apagados);
  - a quebra de linha da familia (M7b, C3; decisoes-v1.md, 167 e 171): o pedido pode levar as quebras do rascunho da
    familia (quebras, o mesmo formato do rascunho); sem o campo, a familia nao tem quebra no rascunho, como a lista
    vazia (revisao do C). Quando elas diferem das do briefing, a previa mede o texto com a
    quebra nova (vapt.derivacao.medida_quebras.medir, com o cache: so o texto que mudou vai ao Chromium) e deriva
    de novo os membros da familia com ela, como a derivacao vai fazer depois de "Salvar e seguir"; a previa e a
    derivacao gravada usam a mesma medida. A quebra fora de um espaco do texto de agora e recusada (como o rascunho).
    A previa leva os textos que o DA pode quebrar, com as posicoes (textos_da_quebra, o controle da quebra no palco,
    M7b, C4), e o texto editado sai no palco nas linhas da quebra da familia;
  - o alinhamento das linhas do texto (0.12.0, pedido do Duda): alinhar_texto leva o alinhamento (esquerda, centro ou
    direita) a todas as linhas de um texto, no texto do KV e no editado. A caixa do bloco fica onde estava: a linha
    mais larga nao anda, e as outras vao a borda esquerda, ao meio ou a borda direita dela. Nenhuma caixa anda (nada
    vai a mexidos), e o alinhamento vale em toda a familia, como o texto. O alinhamento do KV de novo volta ao KV
    (derivacao.quebras.alinhamento_efetivo). So no elemento com um texto de ponto so, com a fonte no job; o texto como
    imagem e o da caixa de texto do Photoshop sao recusados com a frase (Editor._alinhamento).
So previa, em memoria: nada aqui grava arquivo. As edicoes ficam no rascunho que a pagina grava (vapt.tela.rascunho),
e "Confirmar familia" e um ato da janela (vapt.tela.atos).
"""
import math
import threading
import time

from vapt import limites

# 0.15.0 (decisoes-v1.md, 204): devolver traz de volta o grafismo que a versao da galeria tirou. Ela so vale no
# layout da familia (vapt.derivacao.proposta.edicoes_efetivas), que a troca pelos apagar dos tirados que ficam fora
# decisao 215: caixa e a posicao e o tamanho copiados do layout de outra familia (caixa_copiada). So o servidor a
# grava (vapt.derivacao.proposta.edicoes_da_copia)
ACOES = ('mover', 'escalar', 'texto', 'apagar', 'alinhar', 'alinhar_texto', 'devolver', 'caixa')
ACOES_DO_GRUPO = ('mover', 'escalar', 'alinhar')  # M7b, D1 e D2: as acoes que levam a lista do grupo
# M7b, D2: o alinhamento no quadro do membro. alvo: (eixo, linha da caixa que encosta na mesma linha do quadro)
ALVOS = {'margem_esquerda': ('x', 'esquerda'), 'centro_horizontal': ('x', 'centro'), 'margem_direita': ('x', 'direita'),
         'topo': ('y', 'topo'), 'centro_vertical': ('y', 'meio'), 'base': ('y', 'base')}
REFERENCIAS = ('margem', 'area_segura')  # o quadro de cada membro: a margem dele ou a area segura dele
CAMPOS =('familia', 'versao', 'edicoes')
# M7b, C3: as quebras de linha do rascunho da familia. Decisao 199 (etapa E4): o arquivo em cujo palco o DA editou,
# que tem de ser o arquivo de edicao da familia
CAMPOS_OPCIONAIS = ('quebras', 'arquivo')
# decisao 199: o arquivo que nao tem o que copiar, ou cuja copia quebrou, fica como o motor o deixou, com a frase
TEXTO_SEM_ARQUIVO_DE_EDICAO = ('O arquivo de edição desta família está sem layout. Este arquivo fica com a proposta do '
                               'Vapt até o arquivo de edição ter uma versão.')
TEXTO_ERRO_NA_COPIA = ('O Vapt não conseguiu copiar o seu layout para este arquivo. Ele fica como o Vapt o '
                       'deixou. Fale com a Trezion.')
VIVAS_MAX = 8  # numero-neutro: familias com quebra nova guardadas na previa (a ultima mexida fica)
# as linhas de alinhamento de uma caixa [x0, y0, x1, y1]: (nome para o DA, indice, indice do outro lado para o centro)
LINHAS = {'x': (('esquerda', 0, None), ('centro', 0, 2), ('direita', 2, None)),  # numero-neutro: indices da caixa
          'y': (('topo', 1, None), ('meio', 1, 3), ('base', 3, None))}  # numero-neutro: indices da caixa
METADE = 0.5  # numero-neutro: o meio da caixa
IGUAL = 1e-6  # numero-neutro: folga numerica de duas linhas que ja estao no mesmo valor
# a folga relativa do tamanho nos limites: a pagina grava o fator em 6 casas (fracao), e a conta de varios fatores
# arredondados pode passar do limite por menos que isto
FOLGA_ESCALA = 1e-4  # numero-neutro: arredondamento das 6 casas da fracao do fator
POR_MS = 1000.0  # numero-neutro: segundos para milissegundos
CASAS_MS = 1  # numero-neutro: casas do tempo gasto
# o membro devolvido porque a quebra de linha da familia ficou sem medida (previa igual ao Salvar, M7b): o DA pode
# tirar a quebra no palco
# 0.9.1: a camada de texto que vai como imagem, por decisao do DA, nao se edita nem quebra no palco
TEXTO_COMO_IMAGEM = 'Este texto vai como imagem, por decisão sua. O texto não se edita aqui.'
# 0.12.0: as recusas do alinhamento das linhas do texto
TEXTO_EM_CAIXA = ('Este texto está numa caixa de texto do Photoshop. Por enquanto, o alinhamento muda aqui só no texto '
                  'de ponto.')
TEXTO_SEM_UM_TEXTO_PARA_ALINHAR = 'Este elemento não tem um texto só para alinhar.'
TEXTO_ALINHAR_SEM_FONTE = 'A fonte deste texto não está no job, e sem ela a tela não mostra o alinhamento novo.'
TEXTO_QUEBRA_SEM_MEDIDA = ('A quebra de linha desta família ficou sem medida. Sem a medida, o Vapt não monta as '
                           'versões deste arquivo. Tire a quebra ou fale com a Trezion.')
# decisao 215: a copia do layout de outra familia
TOL_COPIA = 1e-3  # numero-neutro: px, a conferencia da copia (as 10 casas da fracao, ampliadas pela ida a mestre)
S_IGUAL = 0.995  # numero-neutro: abaixo disto a escala da copia aparece ao DA (o arredondamento da porcentagem)
FRASES_MAX = 50  # numero-neutro: as frases guardadas da hora da copia (o tamanho do rascunho)
FRASE_MAX = 500  # numero-neutro: caracteres de cada frase guardada


def tolerancia(W, H):
    """A tolerancia da intencao de alinhamento, em px da peca W x H (proporcional ao lado maior)."""
    return float(limites.valor('derivacao.alinhamento_intencao_tolerancia')) * max(float(W), float(H))


def _linha(c, eixo, nome):
    for n, i, j in LINHAS[eixo]:
        if n == nome:
            return c[i] if j is None else (c[i] + c[j]) * METADE
    raise KeyError(nome)


def _deslocar(c, eixo, d):
    if eixo == 'x':
        return [c[0] + d, c[1], c[2] + d, c[3]]
    return [c[0], c[1] + d, c[2], c[3] + d]


# ------------------------------------------------------------------ as edicoes em proporcao
def membros(ed):
    """Os elementos que a edicao mexe: a lista do grupo (elementos, M7b, D1) ou o elemento so."""
    if ed['acao'] in ACOES_DO_GRUPO and ed.get('elementos'):
        return list(ed['elementos'])
    return [ed['elemento']]


def grupos(edicoes):
    """Os grupos que ficam depois das edicoes (M7b, D1): os elementos que andaram juntos na ultima edicao de mover ou
    escalar de cada um, na ordem da lista dela. O elemento mexido sozinho depois sai do grupo, o apagado tambem, e o
    grupo de um elemento so deixa de ser grupo. Vale igual em todo formato (so le as edicoes)."""
    ultima, apagados = {}, set()
    for n, ed in enumerate(edicoes):
        if ed['acao'] == 'apagar':
            apagados.add(ed['elemento'])
            ultima.pop(ed['elemento'], None)
        elif ed['acao'] in ACOES_DO_GRUPO:
            for eid in membros(ed):
                if eid not in apagados:
                    ultima[eid] = (n, membros(ed).index(eid))
    por_edicao = {}
    for eid, (n, i) in ultima.items():
        por_edicao.setdefault(n, []).append((i, eid))
    return [[eid for _i, eid in sorted(v)] for _n, v in sorted(por_edicao.items()) if len(v) > 1]


def limites_da_escala():
    """(menor, maior) tamanho que o DA da a um elemento (M7b, D3), em fator sobre o tamanho antes das edicoes."""
    return float(limites.valor('tela.escala_min')), float(limites.valor('tela.escala_max'))


def escalas(edicoes):
    """O tamanho de cada elemento escalado pelo DA (M7b, D3): {id: produto dos fatores das edicoes de escalar que o
    levam, sozinho ou no grupo}, sobre o tamanho antes das edicoes. O elemento sem escalar fica de fora (1, 100%), e o
    apagado sai. A caixa copiada de outra familia (215) volta o elemento a 1: o 100% passa a ser o tamanho copiado.
    Vale igual em todo formato (so le as edicoes)."""
    tamanho = {}
    for ed in edicoes:
        if ed['acao'] in ('apagar', 'caixa'):
            tamanho.pop(ed['elemento'], None)
        elif ed['acao'] == 'escalar':
            for eid in membros(ed):
                tamanho[eid] = tamanho.get(eid, 1.0) * float(ed['fator'])
    return tamanho


def _passos(edicoes):
    """{id: [tamanho depois de cada edicao de escalar que o leva]} (escalas, passo a passo); o apagado e o da caixa
    copiada (215) recomecam."""
    passos, tamanho = {}, {}
    for ed in edicoes:
        if ed['acao'] in ('apagar', 'caixa'):
            tamanho.pop(ed['elemento'], None)
        elif ed['acao'] == 'escalar':
            for eid in membros(ed):
                tamanho[eid] = tamanho.get(eid, 1.0) * float(ed['fator'])
                passos.setdefault(eid, []).append(tamanho[eid])
    return passos


def escala_fora(edicoes, antes=None):
    """Os elementos, ordenados pelo id, cujo tamanho depois das edicoes passa dos limites da escala (M7b, D3), com a
    folga do arredondamento (FOLGA_ESCALA). antes: as edicoes gravadas da mesma familia (revisao 1 da fase D). O
    tamanho que elas ja tinham fora dos limites (o rascunho da tela de antes do D3, sem o limite acumulado) passa,
    enquanto o novo nao for para mais longe do mesmo limite: o job nunca trava, e o DA conserta pela tela. Conta o
    tamanho final, para o conserto que sai de fora dos limites passar. Revisao 2 da fase D: em nenhum passo o tamanho
    sai do teto, os limites esticados pela razao entre eles (de escala_min ao quadrado sobre escala_max a escala_max ao
    quadrado sobre escala_min), nem com o rascunho gravado: o par forjado que se cancela no fim (1e308 e 1e-308) levaria
    a caixa a infinito ou a um ponto, e a previa e a derivacao quebrariam."""
    menor, maior = limites_da_escala()
    baixo, alto = menor * (1 - FOLGA_ESCALA), maior * (1 + FOLGA_ESCALA)
    piso, teto = baixo * menor / maior, alto * maior / menor
    velho = escalas(antes or [])
    passos = _passos(edicoes)
    fora = []
    for eid, s in escalas(edicoes).items():
        if not all(math.isfinite(p) and piso <= p <= teto for p in passos.get(eid, ())):
            fora.append(eid)
            continue
        if baixo <= s <= alto:
            continue
        v = velho.get(eid)
        if v is not None and ((s < baixo and v < baixo and s >= v * (1 - FOLGA_ESCALA)) or
                              (s > alto and v > alto and s <= v * (1 + FOLGA_ESCALA))):
            continue  # ja estava gravado fora do limite, e nao foi para mais longe
        fora.append(eid)
    return sorted(fora)


def ids_conferem(edicoes, ids):
    """As edicoes citam so elementos que existem (ids, os do KV que a tela mostra), e o grupo (M7b, D1) comeca pelo
    elemento da edicao. A previa e o rascunho conferem igual (revisao 1 da fase D): o rascunho nunca guarda a edicao
    que a previa recusa. ids None: so a ordem do grupo."""
    for e in edicoes:
        lista = e.get('elementos')
        if lista is not None and lista[0] != e['elemento']:
            return False
        if ids is not None and not ({e['elemento']} | set(lista or ())) <= set(ids):
            return False
    return True


def intencoes(edicoes):
    """Os alinhamentos no quadro que ficam valendo depois das edicoes (M7b, D2), na ordem delas: [{'elementos',
    'eixo', 'alvo', 'referencia'}]. A ultima edicao vence: o elemento movido naquele eixo, escalado ou apagado depois
    sai da intencao (a caixa copiada de outra familia, 215, tambem), e o alinhamento novo no mesmo eixo vale sobre o
    de antes. Vale igual em todo formato (so le as
    edicoes); a derivacao a segura contra a intencao de alinhamento (168) e a firma de novo no layout (firmar).
    Revisao 0.9.5 (o que o DA nao mexeu fica parado): quando um membro sai do alinhamento de um grupo, o grupo inteiro
    sai daquele eixo. Senao o firmar recalcularia a linha so com quem sobrou e levaria um elemento que o DA nao tocou."""
    vale = {}

    def tirar(eid, eixo):
        n = vale.pop((eid, eixo), None)
        if n is None:
            return
        for chave in [c for c, m in vale.items() if m == n and c[1] == eixo]:
            vale.pop(chave)

    for n, ed in enumerate(edicoes):
        acao = ed['acao']
        if acao == 'alinhar':
            eixo = ALVOS[ed['alvo']][0]
            for eid in membros(ed):
                tirar(eid, eixo)
                vale[(eid, eixo)] = n
        elif acao == 'mover':
            for eid in membros(ed):
                for eixo, d in (('x', ed['dx']), ('y', ed['dy'])):
                    if float(d):
                        tirar(eid, eixo)
        elif acao in ('escalar', 'apagar', 'caixa'):
            for eid in membros(ed):
                for eixo in ('x', 'y'):
                    tirar(eid, eixo)
    por_edicao = {}
    for (eid, _eixo), n in vale.items():
        por_edicao.setdefault(n, set()).add(eid)
    saida = []
    for n in sorted(por_edicao):
        ed = edicoes[n]
        saida.append({'elementos': [k for k in membros(ed) if k in por_edicao[n]], 'eixo': ALVOS[ed['alvo']][0],
                      'alvo': ed['alvo'], 'referencia': ed['referencia']})
    return saida


def vistas(caixas, visivel=None, editados=()):
    """As caixas como o DA as ve (0.9.6; decisao 196): o elemento com texto editado (editados) fica com a caixa das
    linhas dele, a tinta medida em volta da ancora (visivel(id, caixa) -> caixa visivel, ou None sem a medida). A
    caixa de geometria (a que da a escala) continua nas caixas; alinhar, o ponto fixo do Tamanho, o encaixe e a
    conferencia usam esta. Sem visivel, as proprias caixas."""
    if visivel is None or not editados:
        return caixas
    saida = dict(caixas)
    for k in editados:
        if k in caixas:
            v = visivel(k, caixas[k])
            if v is not None:
                saida[k] = [float(x) for x in v]
    return saida


def firmar(caixas, intencoes_, quadros, W, H, borda=(), visivel=None, editados=()):
    """Os alinhamentos no quadro (intencoes) de novo, no layout de cada membro depois das edicoes (M7b, D2): cada
    intencao leva os elementos dela que o formato tem, juntos, ate a linha do quadro do membro; nada tira o bloco do
    lugar que o DA pediu. A linha do grupo e a de caixa_da_linha (borda: {(id, lado)} do asset cortado na borda do
    KV), sobre a caixa que o DA ve (vistas, 0.9.6). Devolve (caixas, no_quadro [{'elementos', 'eixo', 'alvo',
    'referencia', 'valor'}])."""
    caixas = {k: list(v) for k, v in caixas.items()}
    feitos = []
    for i in intencoes_:
        ids = [k for k in i['elementos'] if k in caixas]
        if not ids:
            continue
        q = quadro_da_referencia(quadros, i['referencia'], W, H)
        eixo, d, valor = no_quadro(caixa_da_linha(vistas(caixas, visivel, editados), ids, i['alvo'], W, H, borda),
                                   i['alvo'], q)
        if abs(d) > IGUAL:
            for k in ids:
                caixas[k] = _deslocar(caixas[k], eixo, d)
        feitos.append({'elementos': ids, 'eixo': eixo, 'alvo': i['alvo'], 'referencia': i['referencia'],
                       'valor': round(valor, 4)})  # numero-neutro: casas do px
    return caixas, feitos


def _uniao(cs):
    return [min(c[0] for c in cs), min(c[1] for c in cs), max(c[2] for c in cs), max(c[3] for c in cs)]


LADO_DO_ALVO = {'esquerda': 'esq', 'topo': 'topo', 'direita': 'dir', 'base': 'base'}


def caixa_da_linha(caixas, ids, alvo, W, H, borda=()):
    """A caixa que da a linha do grupo no alinhamento no quadro (revisao 1 da fase D do M7b). No alvo de borda (as
    margens, o topo e a base), o elemento preso a borda da peca daquele lado fica fora da conta e anda junto: o que
    passa da borda agora (o que sangra) e o que tem o asset cortado naquela borda do KV (borda: {(id, lado)}). Assim o
    packshot vai para a base pela linha dos produtos, e o circulo de tras continua passando da borda. Com todos presos
    a borda, e no centro, conta o grupo inteiro. Revisao 2 da fase D: o elemento que so encosta na borda (o que o
    alinhamento acabou de levar ate ela, quando a linha do quadro e a propria borda da peca) continua na conta; senao
    o segundo clique, ou o alinhamento firmado no layout do membro, levaria o grupo para fora da peca."""
    _eixo, nome = ALVOS[alvo]
    lado = LADO_DO_ALVO.get(nome)
    cs = [caixas[k] for k in ids]
    if lado is None:
        return _uniao(cs)
    passa = {'esq': lambda c: c[0] < -IGUAL, 'topo': lambda c: c[1] < -IGUAL, 'dir': lambda c: c[2] > float(W) + IGUAL,
             'base': lambda c: c[3] > float(H) + IGUAL}[lado]
    dentro = [caixas[k] for k in ids if not passa(caixas[k]) and (k, lado) not in borda]
    return _uniao(dentro or cs)


def quadro_da_referencia(quadros, referencia, W, H):
    """O quadro do membro para o alinhamento (M7b, D2): a margem ou a area segura dele; sem quadros, a peca inteira."""
    q = (quadros or {}).get(referencia)
    return [float(v) for v in q] if q else [0.0, 0.0, float(W), float(H)]


def no_quadro(u, alvo, quadro):
    """(eixo, deslocamento, valor) que leva a linha do alvo da caixa u a mesma linha do quadro (M7b, D2)."""
    eixo, nome = ALVOS[alvo]
    valor = _linha(quadro, eixo, nome)
    return eixo, valor - _linha(u, eixo, nome), valor


def caixa_copiada(ed, W, H, mestre_caixa=None):
    """A caixa de geometria [x0, y0, x1, y1] em px do formato W x H de uma edicao 'caixa' (decisao 215). A edicao
    guarda a caixa em fracao (caixa) e a caixa do elemento na mestre de onde ela saiu (doc): as duas dao a
    transformacao do elemento (a escala s pela regra de galeria._escalas e o ponto do documento no canto). Com a
    mestre de agora (mestre_caixa) diferente da doc (a quebra de linha mudou a caixa do texto), a caixa vai a ela pela
    mesma transformacao: o mesmo s e o mesmo ponto do documento, entao o texto fica do mesmo corpo e no mesmo lugar, e
    a caixa cresce ou encolhe com as linhas. Sem mestre_caixa, ou com a mesma, a propria caixa."""
    W, H = float(W), float(H)
    f = [float(v) for v in ed['caixa']]
    c = [f[0] * W, f[1] * H, f[2] * W, f[3] * H]
    if mestre_caixa is None:
        return c
    d, m = [float(v) for v in ed['doc']], [float(v) for v in mestre_caixa]
    if all(abs(a - b) <= IGUAL for a, b in zip(m, d)):
        return c
    if d[2] > d[0]:
        s = (c[2] - c[0]) / (d[2] - d[0])
    else:
        s = (c[3] - c[1]) / (d[3] - d[1]) if d[3] > d[1] else 1.0
    return [c[0] + s * (m[0] - d[0]), c[1] + s * (m[1] - d[1]), c[0] + s * (m[2] - d[0]), c[1] + s * (m[3] - d[1])]


def caixas_de(edicoes):
    """As edicoes 'caixa' (decisao 215), na ordem."""
    return [e for e in edicoes or () if e.get('acao') == 'caixa']


def copiados(edicoes):
    """{id: a ultima edicao 'caixa' do elemento} (decisao 215), sem o elemento apagado depois dela."""
    saida = {}
    for e in edicoes or ():
        if e['acao'] == 'caixa':
            saida[e['elemento']] = e
        elif e['acao'] == 'apagar':
            saida.pop(e['elemento'], None)
    return saida


def copiados_do_da(edicoes):
    """Os ids, em ordem, dos elementos copiados (copiados) que eram decisao do DA na familia de origem (do_da)."""
    return sorted(k for k, e in copiados(edicoes).items() if e.get('do_da'))


def fundo_copiado(edicoes):
    """A figura de fundo (n 202) do layout copiado de outra familia (decisao 215): None sem edicao 'caixa' (vale a
    regra da versao); senao a tupla dos ids copiados marcados fundo, que pode ser vazia."""
    if not caixas_de(edicoes):
        return None
    return tuple(sorted(k for k, e in copiados(edicoes).items() if e.get('fundo')))


def aplicar(caixas, edicoes, W, H, quadros=None, borda=(), visivel=None, editados=(), mestre_caixas=None):
    """As edicoes do DA no formato W x H. caixas: {id: [x0, y0, x1, y1]}. Mover anda dx x W e dy x H; escalar multiplica
    a caixa pelo fator em volta do ponto fixo (fx, fy, fracoes da caixa; o meio sem eles). No grupo (elementos, M7b,
    D1), todos andam igual, e o ponto fixo e a fracao da caixa que junta o grupo no formato (sem o elemento apagado nem
    o que o formato nao tem). Alinhar (M7b, D2) desloca o elemento, ou o grupo inteiro, no eixo do alvo, ate a linha da
    caixa que junta o grupo encostar na mesma linha do quadro do membro (quadros: {'margem', 'area_segura'}: caixas do
    formato; sem ele, a peca inteira); o tamanho nao muda. No alvo de borda, o elemento preso a borda da peca daquele
    lado fica fora da linha e anda junto (caixa_da_linha; borda: {(id, lado)} do asset cortado na borda do KV, revisao
    1 da fase D). Devolve (caixas, apagados, textos {id: texto}, mexidos na
    ordem, o ultimo por ultimo). visivel, editados (0.9.6): a linha do alinhar e o ponto fixo do escalar saem da caixa
    que o DA ve (vistas: o texto editado nas linhas dele); o deslocamento e o fator vao a caixa de geometria.
    A caixa copiada de outra familia (decisao 215) poe o elemento na caixa dela (caixa_copiada, com a caixa dele na
    mestre de agora: mestre_caixas {id: caixa}); nao e mexido, entao nada encaixa depois dela."""
    caixas = {k: [float(x) for x in v] for k, v in caixas.items()}
    apagados, textos, mexidos = [], {}, []
    editados = set(editados)
    for ed in edicoes:
        eid, acao = ed['elemento'], ed['acao']
        if acao == 'caixa':
            if eid in caixas and eid not in apagados:
                caixas[eid] = caixa_copiada(ed, W, H, (mestre_caixas or {}).get(eid))
            continue
        if acao in ('apagar', 'texto', 'alinhar_texto'):
            # 0.12.0: o alinhamento das linhas do texto nao mexe em caixa nenhuma (derivacao.quebras.alinhamento_
            # editado o le das edicoes)
            if eid not in caixas or eid in apagados:
                continue
            if acao == 'apagar':
                apagados.append(eid)
            elif acao == 'texto':
                textos[eid] = ed['texto']
                editados.add(eid)
            continue
        ids = [k for k in membros(ed) if k in caixas and k not in apagados]
        if not ids:
            continue
        if acao == 'mover':
            dx, dy = float(ed['dx']) * W, float(ed['dy']) * H
            for k in ids:
                c = caixas[k]
                caixas[k] = [c[0] + dx, c[1] + dy, c[2] + dx, c[3] + dy]
        elif acao == 'alinhar':
            q = quadro_da_referencia(quadros, ed['referencia'], W, H)
            vis = vistas(caixas, visivel, editados)
            eixo, d, _v = no_quadro(caixa_da_linha(vis, ids, ed['alvo'], W, H, borda), ed['alvo'], q)
            for k in ids:
                caixas[k] = _deslocar(caixas[k], eixo, d)
        else:
            f = float(ed['fator'])
            vis = vistas(caixas, visivel, editados)
            u = _uniao([vis[k] for k in ids])
            px = u[0] + float(ed.get('fx', METADE)) * (u[2] - u[0])
            py = u[1] + float(ed.get('fy', METADE)) * (u[3] - u[1])
            for k in ids:
                c = caixas[k]
                caixas[k] = [px + (c[0] - px) * f, py + (c[1] - py) * f, px + (c[2] - px) * f, py + (c[3] - py) * f]
        for k in ids:
            if k in mexidos:
                mexidos.remove(k)
            mexidos.append(k)
    for eid in apagados:
        caixas.pop(eid, None)
        textos.pop(eid, None)
        if eid in mexidos:
            mexidos.remove(eid)
    return caixas, apagados, textos, mexidos


def sangria_do_da(caixas, mexidos, W, H, tol, sem_sangria=()):
    """Os lados em que o DA deixou o elemento passar da borda da peca W x H (M7b, D4): {id: [lados, na ordem esq,
    topo, dir, base]} de cada elemento mexido (mover, escalar ou alinhar, sozinho ou no grupo) cuja caixa passa da
    borda por mais que tol. O quadro corta o que fica fora, e o lado vira sangria por decisao do DA. O texto e a marca
    (sem_sangria: os ids deles) nunca sangram: continuam dentro do quadro, como no KV. Revisao 2 da fase D: o elemento
    que fica inteiro fora da peca nao sangra (fora_da_peca): sangrar e passar uma parte pela borda, e o que some da
    peca pede ajuste. A derivacao passa tol pequeno (a folga numerica): o elemento que passa da borda por menos que a
    tolerancia do enquadramento tambem fica onde o DA o pos, com o lado marcado como sangria."""
    saida = {}
    fora = set(fora_da_peca(caixas, mexidos, W, H, tol))
    for k in mexidos:
        if k not in caixas or k in sem_sangria or k in fora:
            continue
        c = caixas[k]
        lados = [lado for lado, fora in (('esq', c[0] < -tol), ('topo', c[1] < -tol), ('dir', c[2] > W + tol),
                                         ('base', c[3] > H + tol)) if fora]
        if lados:
            saida[k] = lados
    return saida


def fora_da_peca(caixas, mexidos, W, H, tol):
    """Os elementos mexidos pelo DA, na ordem, que ficam inteiros fora da peca W x H (revisao 2 da fase D): nada da
    caixa aparece no quadro, a menos de tol. Nao e sangria: a conferencia pede ajuste e diz que, para tirar o elemento,
    o caminho e Apagar."""
    return [k for k in mexidos if k in caixas and (
        caixas[k][2] <= tol or caixas[k][3] <= tol or caixas[k][0] >= W - tol or caixas[k][1] >= H - tol)]


def normalizar(caixas, mexidos, W, H, kv_caixas=None, kv_tamanho=None, grupos=(), acompanham=None, presos=(),
               antes=None):
    """A intencao de alinhamento (decisoes-v1.md, 168, revista pela 185) depois de uma edicao: so o elemento que o DA
    acabou de mexer anda (mexidos: os elementos daquela edicao, o elemento so ou o grupo dele). Em cada eixo, o par
    que ja divide uma linha fica; senao, o mexido encaixa na linha mais perto de um vizinho abaixo da tolerancia, so
    com deslocamento (o tamanho nao muda), um encaixe por elemento e eixo. Nenhum outro elemento sai do lugar: nem o
    que o DA nao mexeu, nem o que ele mexeu antes. Duas passadas: primeiro os vizinhos com quem o mexido ja estava
    alinhado no KV (o mexido volta para a linha do outro), depois os outros, ja com as posicoes da primeira; assim um
    encaixe do KV nunca e desfeito por outro e nao fica linha quase igual (revisao do M7a). O grupo (M7b, D1; grupos,
    as listas de ids) nunca se separa: os elementos do mesmo grupo nao se alinham entre si, e o elemento do grupo que
    encosta na linha de outro leva o grupo inteiro com ele, tambem os membros fora da conta do alinhamento
    (acompanham: {id: caixa}, os que nao sao de conteudo), num encaixe so por eixo. O mexido alinhado no quadro pelo
    DA (M7b, D2; presos: {(id, eixo)}, de intencoes) nunca sai da linha do quadro: naquele eixo nada anda. O mexido
    que divide agora, naquele eixo, uma linha que ja dividia no KV com um terceiro fica nela (revisao 2 da fase D),
    e os pares vao da linha mais perto para a mais longe, com o empate pelos ids, para o resultado nao depender da
    ordem dos cliques no grupo. antes ({id: caixa antes da edicao}, de editar): a linha do mexido so encaixa na do
    vizinho que fica a frente de onde a edicao o tirou, no sentido em que ela o levou; a linha que ele deixou para
    tras nao o puxa de volta (o toque da seta sai da linha) e o eixo em que ele nao andou nao encaixa (o arraste so na
    vertical nao muda o x, o alinhar na largura nao muda a altura). Sem antes, qualquer sentido. Devolve (caixas, com
    as de acompanham; alinhados [{'elementos': [o que andou, o que ficou], 'eixo', 'linha', 'valor'}])."""
    tol = tolerancia(W, H)
    presos = set(presos)
    tol_kv = tolerancia(*kv_tamanho) if kv_tamanho else None
    caixas = {k: list(v) for k, v in caixas.items()}
    junto = {k: list(v) for k, v in (acompanham or {}).items() if k not in caixas}
    grupo_de = {eid: tuple(g) for g in grupos for eid in g}
    # o que anda nesta edicao: o mexido e o grupo dele; o resto fica (decisao 185)
    andam = {x for m in mexidos for x in (grupo_de.get(m) or (m,))} | set(mexidos)
    feitos, alinhados = set(), []

    def a_frente(m, o, eixo, n):
        # a linha do vizinho fica a frente de onde a edicao tirou o mexido (antes): a linha que ele deixou para tras
        # nao o puxa de volta, e o eixo em que ele nao andou nao encaixa (decisao 185)
        if antes is None or m not in antes:
            return True
        v0 = _linha(antes[m], eixo, n)
        andou, falta = _linha(caixas[m], eixo, n) - v0, _linha(caixas[o], eixo, n) - v0
        return abs(andou) > IGUAL and abs(falta) > IGUAL and (andou > 0) == (falta > 0)

    def perto_de(m, o, eixo):
        nomes = [n for n, _i, _j in LINHAS[eixo]]
        difs = [(abs(_linha(caixas[m], eixo, n) - _linha(caixas[o], eixo, n)), n) for n in nomes]
        if any(d <= IGUAL for d, _n in difs):
            return []
        return [(d, n) for d, n in difs if d <= tol and a_frente(m, o, eixo, n)]

    def preso(k, eixo):
        return any((x, eixo) in presos for x in grupo_de.get(k) or (k,))

    def encaixar(anda, fica, eixo, nome):
        # o mexido alinhado no quadro fica na linha do quadro (M7b, D2): naquele eixo nada anda (decisao 185)
        if preso(anda, eixo) or (anda, eixo) in feitos:
            return
        valor = _linha(caixas[fica], eixo, nome)
        d = valor - _linha(caixas[anda], eixo, nome)
        # o grupo do elemento anda inteiro com ele (M7b, D1)
        for k in grupo_de.get(anda) or (anda,):
            for onde in (caixas, junto):
                if k in onde:
                    onde[k] = _deslocar(onde[k], eixo, d)
            feitos.add((k, eixo))
        alinhados.append({'elementos': [anda, fica], 'eixo': eixo, 'linha': nome, 'valor': round(valor, 4)})  # numero-neutro: casas do px

    def do_kv(m, o, eixo, perto):
        if not (kv_caixas and tol_kv is not None and m in kv_caixas and o in kv_caixas):
            return []
        return [(d, n) for d, n in perto
                if abs(_linha(kv_caixas[m], eixo, n) - _linha(kv_caixas[o], eixo, n)) <= tol_kv]

    def linha_do_kv(k, eixo, fica):
        # o mexido (ou o grupo dele) divide agora, naquele eixo, uma linha que ja dividia no KV com outro elemento
        # (revisao 2 da fase D): encaixar no vizinho o tiraria do alinhamento do KV, que vale (168)
        if not (kv_caixas and tol_kv is not None):
            return False
        meus = grupo_de.get(k) or (k,)
        for g in meus:
            if g not in caixas or g not in kv_caixas:
                continue
            for x in caixas:
                if x == fica or x in meus or x not in kv_caixas:
                    continue
                for n, _i, _j in LINHAS[eixo]:
                    if abs(_linha(caixas[g], eixo, n) - _linha(caixas[x], eixo, n)) <= IGUAL and \
                            abs(_linha(kv_caixas[g], eixo, n) - _linha(kv_caixas[x], eixo, n)) <= tol_kv:
                        return True
        return False

    def mais_perto_primeiro(lista):
        # a linha mais perto primeiro, e o empate pelos ids: o resultado nunca depende da ordem dos cliques no grupo
        # (revisao 2 da fase D)
        cands = []
        for m, o, eixo in pares:
            perto = lista(m, o, eixo)
            if perto:
                d, nome = min(perto)
                cands.append((d, eixo, nome, sorted((m, o)), m, o))
        return [(m, o, eixo) for _d, eixo, _n, _ids, m, o in sorted(cands)]

    # o mexido com cada vizinho que nao anda com ele; os do mesmo grupo ficam como o DA os deixou (M7b, D1)
    pares = [(m, o, eixo) for m in sorted(set(mexidos)) if m in caixas for o in sorted(caixas)
             if o not in andam for eixo in ('x', 'y')]
    # 1a passada: o alinhamento do KV vence, o mexido volta para a linha do outro
    for m, o, eixo in mais_perto_primeiro(lambda m, o, eixo: do_kv(m, o, eixo, perto_de(m, o, eixo))):
        no_kv = do_kv(m, o, eixo, perto_de(m, o, eixo))
        if no_kv:
            encaixar(m, o, eixo, min(no_kv)[1])
    # 2a passada: o resto, com as posicoes da primeira; o mexido encaixa na linha do vizinho. O mexido que dividia uma
    # linha do KV com um terceiro e continua nela nao anda
    for m, o, eixo in mais_perto_primeiro(
            lambda m, o, eixo: [] if do_kv(m, o, eixo, perto_de(m, o, eixo)) else perto_de(m, o, eixo)):
        perto = perto_de(m, o, eixo)
        if not perto or do_kv(m, o, eixo, perto) or linha_do_kv(m, eixo, o):
            continue
        encaixar(m, o, eixo, min(perto)[1])
    caixas.update(junto)
    return caixas, alinhados


def editar(caixas, edicoes, W, H, quadros=None, borda=(), conteudo=None, kv_caixas=None, kv_tamanho=None,
           visivel=None, mestre_caixas=None):
    """As edicoes do DA no formato W x H, uma a uma, cada uma com a intencao de alinhamento na hora dela (decisao
    185): aplicar a edicao e normalizar so o que ela mexeu (o elemento ou o grupo dele), com os grupos e os
    alinhamentos no quadro que valem ate ela. Cada edicao parte das caixas que a tela mostra depois da edicao de
    antes, ja com o encaixe dela, como tela.js mede o arraste, o Tamanho e o alinhar: o elemento solta onde o DA o
    soltou, o grupo anda inteiro como o DA o via e o canto fixo do Tamanho fica no lugar. A edicao depois nunca tira
    do lugar o que o DA mexeu antes nem o que ele nao mexeu, e o rascunho refeito inteiro (a previa e o "Salvar e
    seguir") da o mesmo layout que a tela mostrou edicao a edicao. O mexido so encaixa na linha que fica a frente de
    onde a edicao o tirou (normalizar, antes): o toque de 1 px da seta anda 1 px nos dois sentidos, e o eixo em que
    ele nao andou nao muda. A edicao de texto e a de apagar nao alinham nada. conteudo: os ids que entram na conta do
    alinhamento (os de conteudo; None: todos); o elemento do grupo fora dela anda junto com o grupo. Devolve (caixas,
    apagados, textos {id: texto}, mexidos na ordem, o ultimo por ultimo, alinhados da ultima edicao: vazio quando
    ela nao mexeu em caixa). visivel (0.9.6; decisao 196): visivel(id, caixa) da a caixa das linhas do DA do texto
    editado (vistas). Depois da edicao de texto, o alinhar, o Tamanho e o encaixe medem essa caixa, como a tela, e o
    deslocamento vai a caixa de geometria; antes dela, vale a caixa do KV. mestre_caixas (decisao 215): {id: caixa na
    mestre de agora}, para a caixa copiada de outra familia (aplicar)."""
    atual = {k: [float(x) for x in v] for k, v in caixas.items()}
    apagados, textos, mexidos, alinhados = [], {}, [], []
    for n, uma in enumerate(edicoes):
        antes = atual
        atual, ap, tx, mx = aplicar(atual, [uma], W, H, quadros, borda, visivel=visivel, editados=set(textos),
                                    mestre_caixas=mestre_caixas)
        textos.update(tx)
        for k in ap:
            apagados.append(k)
            textos.pop(k, None)
            if k in mexidos:
                mexidos.remove(k)
        for k in mx:
            if k in mexidos:
                mexidos.remove(k)
            mexidos.append(k)
        alinhados = []
        if not mx:
            continue
        ate_aqui = edicoes[:n + 1]
        gs = grupos(ate_aqui)
        so = {k: v for k, v in atual.items() if conteudo is None or k in conteudo}
        junto = {k: atual[k] for g in gs for k in g if k in atual and k not in so}
        presos = {(k, i['eixo']) for i in intencoes(ate_aqui) for k in i['elementos']}
        if visivel is None or not textos:
            norm, alinhados = normalizar(so, mx, W, H, kv_caixas, kv_tamanho, grupos=gs, acompanham=junto,
                                         presos=presos, antes={k: antes[k] for k in mx if k in antes})
            atual.update(norm)
            continue
        # 0.9.6: o encaixe mede a caixa que o DA ve (o texto editado nas linhas dele); o deslocamento de cada um vai a
        # caixa de geometria dele (normalizar so desloca)
        so_v, junto_v = vistas(so, visivel, textos), vistas(junto, visivel, textos)
        antes_v = vistas({k: antes[k] for k in mx if k in antes}, visivel, textos)
        norm, alinhados = normalizar(so_v, mx, W, H, kv_caixas, kv_tamanho, grupos=gs, acompanham=junto_v,
                                     presos=presos, antes=antes_v)
        for k, c in norm.items():
            ref = so_v.get(k) or junto_v.get(k)
            if ref is None or k not in atual:
                continue
            dx, dy = c[0] - ref[0], c[1] - ref[1]
            g = atual[k]
            atual[k] = [g[0] + dx, g[1] + dy, g[2] + dx, g[3] + dy]
    return atual, apagados, textos, mexidos, alinhados


# ------------------------------------------------------------------ texto
def caracteres_que_faltam(texto, face, caixa_alta=False):
    """Os caracteres com tinta do texto que a face nao cobre, em ordem e sem repetir."""
    from vapt.fontes import casamento
    alvo = texto.upper() if caixa_alta else texto
    vistos = []
    for ch in alvo:
        if casamento.tem_tinta(ch) and not casamento.cobre(face, ord(ch)) and ch not in vistos:
            vistos.append(ch)
    return vistos


def _texto_da_recusa(faltam):
    lista = ', '.join(faltam)
    if len(faltam) == 1:
        return 'A fonte deste texto não tem o caractere %s. Troque o caractere ou envie a fonte que o tenha.' % lista
    return 'A fonte deste texto não tem os caracteres %s. Troque esses caracteres ou envie a fonte que os tenha.' % lista


def _trechos_do_editado(texto_kv, faces, s, linhas):
    """[{'trechos', 'entrelinha'}] de cada linha do texto editado no palco: os trechos da regra por palavra (decisao 214;
    vapt.derivacao.quebras.runs_do_editado) sobre os runs do KV (texto_kv: o _texto da peca base, nunca as linhas do
    palco, que podem ja ter a quebra da familia com posicoes do texto editado), cada um como estado._linhas o monta
    (texto, fonte_ps, face, cor, corpo, tracking) e com o corpo na escala s do formato, como estado._peca_no_formato.
    Os vizinhos com o mesmo estilo no palco viram um trecho; a linha vazia leva o estilo do trecho com tinta antes dela
    (no comeco do texto, o do primeiro com tinta) e a entrelinha da quebra dela. None sem run com tinta no KV."""
    from vapt.derivacao import quebras as mq
    from vapt.tela import estado
    from vapt.render import texto as rt
    from vapt.fontes import casamento
    runs = mq.runs_do_editado((texto_kv or {}).get('runs') or [], linhas, '\n')
    if runs is None:
        return None
    _r0, par = mq._trecho_e_paragrafo({'texto': texto_kv})
    m = (texto_kv or {}).get('matriz') or [1.0, 0.0, 0.0, 1.0]
    sy = math.hypot(float(m[2]), float(m[3]))

    def entrelinha(rs):
        # a do render e da medida (render.texto.linhas_da_camada): a maior dos runs da linha, no paragrafo de r0, com
        # o arredondamento duplo de estado._linhas e estado._peca_no_formato (o KV de um estilo so da a de antes)
        lead = max((rt._entrelinha(r, par or {}) for r in rs), default=0.0)
        return estado._arred(estado._arred(lead * sy) * s) if lead else None

    def trecho(r, parte):
        cor = r.get('cor_hex') if isinstance(r.get('cor_hex'), str) and estado.COR.match(r['cor_hex']) else None
        corpo = r.get('corpo_efetivo')
        return {'texto': parte, 'fonte_ps': r.get('fonte_ps'), 'face': faces.get(r.get('fonte_ps')), 'cor': cor,
                'corpo': None if corpo is None else estado._arred(corpo * s), 'tracking': r.get('tracking') or 0}

    def estilo(t):
        return {k: v for k, v in t.items() if k != 'texto'}
    # decisao 214: o espaco sem tinta de uma fonte sem face vai no estilo do vizinho com face, como na medida e no render
    no_vizinho = {}
    for i, r in enumerate(runs):
        v = casamento.vizinho_com_face(runs, i, lambda x: faces.get(x.get('fonte_ps')) is not None)
        if v is not None:
            no_vizinho[id(r)] = v
    saida, a = [], 0
    for n, ln in enumerate(linhas):
        b = a + len(ln)
        # os runs da linha no render: os dos caracteres dela e o da quebra que a termina (a ultima linha nao tem)
        e = b + 1 if n + 1 < len(linhas) else b
        da_linha = [r for r in runs if r['inicio'] < e and r['fim'] > a]
        trechos = []
        for r in runs:
            i, f = max(r['inicio'], a), min(r['fim'], b)
            if i >= f:
                continue
            t = trecho(no_vizinho.get(id(r), r), ln[i - a:f - a])
            if trechos and estilo(trechos[-1]) == estilo(t):
                trechos[-1]['texto'] += t['texto']
            else:
                trechos.append(t)
        if not trechos:
            # o estilo do trecho com tinta antes dela (a quebra da linha vazia pode ser de um run sem tinta, que guarda
            # so a entrelinha); no comeco do texto, o primeiro com tinta
            vizinho = next((r for r in reversed(runs) if r['inicio'] < a and r['tem_tinta']),
                           next((r for r in runs if r['tem_tinta']), runs[0]))
            trechos = [trecho(vizinho, '')]
            da_linha = da_linha or [vizinho]
        saida.append({'trechos': trechos, 'entrelinha': entrelinha(da_linha)})
        a = b + 1
    return saida


def _linhas_do_psd(pb, escala):
    """As linhas do texto do KV como o PSD as grava (estado._linhas sem a quebra da familia), com o corpo e a
    entrelinha na escala do formato, como estado._peca_no_formato. None sem o texto ou sem a escala."""
    from vapt.tela import estado
    if not (pb or {}).get('_texto') or escala is None:
        return None
    s = float(escala)
    linhas = estado._linhas(pb['_texto'], (pb.get('_faces') or {}).get)
    if not linhas:
        return None
    return [{'trechos': [dict(t, corpo=None if t['corpo'] is None else estado._arred(t['corpo'] * s))
                         for t in ln['trechos']],
             'entrelinha': None if ln['entrelinha'] is None else estado._arred(ln['entrelinha'] * s)} for ln in linhas]


def _desvio_da_caixa(pb, linhas, faces, escala):
    """Na caixa de paragrafo, quanto a primeira linha de base do texto editado desce em relacao a do KV no palco (px do
    formato), pela regra do render (render.texto.origem_das_linhas: topo da caixa mais a ascendente da face da primeira
    linha cheia): a diferenca entre a do texto editado (trechos da regra R3) e a do KV. 0 no texto de ponto, sem as
    faces ou sem a escala."""
    from vapt.derivacao import quebras as mq
    from vapt.render import texto as rt
    from vapt.tela import estado
    t = (pb or {}).get('_texto')
    if not t or not faces or escala is None or not rt.eh_caixa_de_paragrafo(t):
        return 0.0
    fp = {ps: faces[fid] for ps, fid in (pb.get('_faces') or {}).items() if fid in faces}
    cam = mq.camada_do_editado({'texto': t}, linhas)
    if not (cam.get('texto') or {}).get('runs'):
        return 0.0
    linhas_kv = rt.linhas_da_camada(t)
    # a ascendente do KV tem de ser conhecida: sem a face ou as metricas de um trecho da primeira linha cheia, o render
    # conta 0 nele e o desvio sairia de uma ascendente que o palco nao tem (o palco fica como antes)
    primeira = next((ln for ln in linhas_kv if ln['pedacos']), None)
    for _s, r in (primeira or {}).get('pedacos') or ():
        m = (fp.get(r.get('fonte_ps')) or {}).get('metricas') or {}
        if not (m.get('ascender') and m.get('unidades_por_em')):
            return 0.0
    y_kv = rt.origem_das_linhas(t, linhas_kv, fp)[1]
    y_novo = rt.origem_das_linhas(cam['texto'], rt.linhas_da_camada(cam['texto']), fp)[1]
    m = t.get('matriz') or [1.0, 0.0, 0.0, 1.0]
    return estado._arred((y_novo - y_kv) * math.hypot(float(m[2]), float(m[3])) * float(escala))


def trocar_texto(palco, elemento, texto, quebra=None, base=None, escala=None, faces=None):
    """As pecas de texto do elemento no palco levam o texto novo, linha a linha (as quebras do DA); a pagina desenha so
    as linhas do DA, sem quebra na largura da caixa (Linhas do DA, 0.9.4). quebra: a quebra de linha da familia no
    texto (o item do rascunho, M7b, C4): as linhas juntadas e as inseridas, como o render desenha
    (vapt.derivacao.quebras.linhas_do_editado). base e escala: as pecas base do palco ({layer_id: peca},
    vapt.tela.estado.pecas_base) e a escala do elemento no formato (transformacao['s']): cada caractere fica com o
    estilo de um trecho do KV (face, cor, corpo e tracking, o corpo na escala do formato), pela regra por palavra
    (decisao 214, _trechos_do_editado), como a medida e o render. Sem elas, ou sem trecho com tinta no KV, o estilo do
    primeiro trecho do palco e a entrelinha da primeira linha do KV que a tem, como antes. Cada linha leva a entrelinha
    do render e da medida (a maior dos runs dela); o KV de um estilo so da o mesmo palco de antes (o hash da familia
    confirmada nao muda), menos quando um espaco ou uma quebra sem tinta tinha outro estilo (corpo, fonte, cor,
    tracking ou outro campo): o palco e o render passam a seguir o KV nele (vapt.derivacao.quebras._no_mesmo_papel), e
    quando a quebra da familia toca a linha da tinta do KV (a ancora sai das linhas do PSD). faces: {id: face servida,
    com as metricas}, para a ancora da caixa de paragrafo (_desvio_da_caixa)."""
    from vapt.derivacao import quebras as mq
    if quebra is not None:
        linhas = mq.linhas_do_editado(texto, quebra['manter'], quebra['inseridas'])
    else:
        linhas = texto.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    for p in palco['pecas']:
        if p.get('elemento') != elemento or p.get('tipo') != 'texto' or not p.get('linhas'):
            continue
        # o primeiro trecho do palco (a primeira linha do KV pode ser vazia, quando o texto comeca com CR)
        t0 = next((t for ln in p['linhas'] for t in ln.get('trechos') or []), None)
        ent = next((ln['entrelinha'] for ln in p['linhas'] if ln.get('entrelinha')), None)
        pb = (base or {}).get(p.get('camada')) or {}
        novas = None
        if escala is not None and pb.get('_texto'):
            novas = _trechos_do_editado(pb['_texto'], pb.get('_faces') or {}, float(escala), linhas)
        if novas is None:
            if t0 is None:
                continue
            novas = [{'trechos': [dict(t0, texto=ln)], 'entrelinha': ent} for ln in linhas]
        if 'ancora_kv' not in p:
            # revisao 0.9.4: o render ancora o texto editado pela primeira linha de base do KV. A pagina so tem a caixa
            # de tinta do KV (caixa_tinta), cujo topo e o da primeira linha do KV com tinta: leva o texto dessa linha e
            # a distancia da primeira linha de base ate a dela (as entrelinhas acima), para medirTexto achar a linha
            # de base do KV e por nela a primeira linha do DA, vazia ou nao
            estilos = {(t.get('face'), t.get('corpo')) for ln in p['linhas'] for t in ln.get('trechos') or []
                       if str(t.get('texto') or '').strip()}
            # decisao 214: a ancora sai das linhas do PSD (sem a quebra da familia, que pode juntar a primeira linha a
            # outra, ou partir a linha da tinta do KV), na escala do formato
            lk = _linhas_do_psd(pb, escala) or p['linhas']
            kv = [''.join(str(t.get('texto') or '') for t in ln.get('trechos') or []) for ln in lk]
            j = next((i for i, s in enumerate(kv) if s.strip()), None)
            acima = [lk[i].get('entrelinha') for i in range(1, j + 1)] if j is not None else None
            if j is not None and all(isinstance(a, (int, float)) and a > 0 for a in acima):
                p['ancora_kv'] = {'texto': kv[j], 'acima': round(float(sum(acima)), 4)}
                # o primeiro trecho do texto editado pode nao ter a face e o corpo da linha do KV: a pagina mede a
                # subida dela nos trechos dela (o KV de um estilo so fica como antes)
                if len(estilos) > 1:
                    p['ancora_kv']['trechos'] = [{'texto': str(t['texto']), 'face': t.get('face'), 'corpo': t.get('corpo')}
                                                 for t in lk[j]['trechos'] if str(t.get('texto') or '').strip()]
        if p.get('ancora_kv') is not None:
            # na caixa de paragrafo o render poe a primeira linha de base no topo da caixa mais a ascendente da primeira
            # linha do texto editado, que pode ter outra face ou corpo que a do KV: o palco desce o mesmo tanto
            d = _desvio_da_caixa(pb, linhas, faces, escala)
            if d:
                p['ancora_kv']['caixa'] = d
            else:
                p['ancora_kv'].pop('caixa', None)
        p['linhas'] = novas
        p['texto_editado'] = True
        # Linhas do DA (0.9.4): o texto cresce ate a linha mais longa, entao o recorte dele vai alem do mundo do palco
        # (um formato para cada lado): a pagina mede a tinta inteira e mostra a que passa da borda (o membro fica
        # marcado)
        W, H = float(palco.get('largura') or 0), float(palco.get('altura') or 0)
        mundo = palco.get('mundo') or [0.0, 0.0, W, H]
        p['recorte'] = [float(mundo[0]) - W, float(mundo[1]) - H, float(mundo[2]) + W, float(mundo[3]) + H]
        p['modo'] = 'texto'
    return palco


def alinhar_texto(palco, elemento, alinhamento, justificacoes=None):
    """As pecas de texto do elemento no palco levam o alinhamento das linhas escolhido pelo DA (0.12.0). A pagina
    alinha as linhas pelo novo (alinhamento) e poe a linha mais larga onde o KV a poe, como o render: a ancora do bloco
    no KV pelo alinhamento de antes (alinhamento_kv) e o lugar de cada linha do KV pela justificacao dela
    (alinhamento_kv_linhas, uma por linha do palco, no texto do KV que nao foi editado; o texto de paragrafos com
    alinhamentos diferentes). justificacoes: {layer_id: [justificacao de cada linha]} (estado.justificacoes_no_formato).
    So o elemento alinhado ganha esses campos: o palco do resto fica o mesmo de antes (o hash da familia confirmada nao
    muda)."""
    from vapt.derivacao import quebras as mq
    for p in palco['pecas']:
        if p.get('elemento') != elemento or p.get('tipo') != 'texto' or not p.get('linhas'):
            continue
        p.setdefault('alinhamento_kv', p.get('alinhamento') or 'esquerda')
        p['alinhamento'] = alinhamento
        js = (justificacoes or {}).get(p.get('camada'))
        if not p.get('texto_editado') and js and len(js) == len(p['linhas']):
            p['alinhamento_kv_linhas'] = [mq.alinhamento_da_justificacao(j) for j in js]
    return palco


# ------------------------------------------------------------------ a familia
class Editor:
    """A previa da edicao por familia, para a rota POST /api/familia/previa do servidor da tela.

    ctx, kv: o contexto e a mestre da derivacao; laudo e base: os do palco (vapt.tela.estado.pecas_base);
    derivados: {id do formato: derivacao/1 em memoria}; brutos: {id do formato: {id da versao: variante do motor}};
    familias: {id da familia: [ids dos formatos membros]}; faces: as faces servidas do job (com o cmap)."""
    # a trava de quem monta o Editor sem __init__ (os testes); __init__ da a cada Editor a dele (decisao 215)
    _trava = threading.RLock()

    def __init__(self, ctx, kv, laudo, base, derivados, brutos, familias, faces, *, specs, arquivo_specs, params,
                 arquivos=None):
        from vapt.derivacao import solver as mod_solver
        from vapt.tela import estado
        self.ctx, self.kv, self.laudo, self.base = ctx, kv, laudo, base
        self.derivados, self.brutos, self.familias = derivados, brutos, familias
        # decisao 199 (0.10.0): {id: arquivo de edicao} como a tela mostra (o gravado no rascunho ou a regra)
        self.arquivos = dict(arquivos or {})
        self.faces = {f['id']: f for f in faces}
        self.kw = {'specs': specs, 'arquivo_specs': arquivo_specs, 'params': params}
        self.por_formato = {f['id']: f for f in ctx['briefing']['formatos']}
        self.kv_por_id = {e['id']: e for e in kv['elementos']}
        self.conteudo = [e['id'] for e in kv['elementos'] if mod_solver.conteudo(e)]
        self.kv_caixas = {e['id']: [float(x) for x in e['caixa']] for e in kv['elementos']}
        self.kv_tamanho = (float(kv['largura']), float(kv['altura']))
        self.nomes = estado._nomes(laudo)
        self._cf = {}
        # a familia com a quebra de linha do rascunho diferente da do briefing (M7b, C3): {chave: {'chave', 'ctx',
        # 'derivados', 'brutos'}}, a mais nova no fim
        self._vivas = {}
        # decisao 215: o servidor da tela atende cada pedido num fio (ThreadingHTTPServer), e a previa e a copia
        # mexem nos guardados (_vivas, _cf): um fio de cada vez. A copia de outra familia guardada pela chave dos
        # dados dela (copia_entre_familias)
        self._trava = threading.RLock()
        self._copias = {}

    def __deepcopy__(self, memo):
        # a copia do conteudo da tela (os testes copiam o conteudo inteiro) ganha uma trava nova: a trava nao se copia
        import copy as mod_copy
        novo = self.__class__.__new__(self.__class__)
        memo[id(self)] = novo
        for k, v in self.__dict__.items():
            setattr(novo, k, threading.RLock() if k == '_trava' else mod_copy.deepcopy(v, memo))
        return novo

    def versoes(self, gid):
        return {vid for fid in self.familias.get(gid, ()) for vid in (self.brutos.get(fid) or {})}

    def arquivo_de_edicao(self, gid):
        """O arquivo de edicao da familia (decisao 199, 1): o que a tela mostra (o gravado no rascunho, enquanto
        estiver na familia), senao a mesma regra da derivacao (vapt.derivacao.proposta.arquivo_de_edicao). None sem
        formato."""
        from vapt.derivacao import proposta
        fs = [self.por_formato[f] for f in self.familias.get(gid, ()) if f in self.por_formato]
        return proposta.arquivo_de_edicao(fs, self.arquivos.get(gid)) if fs else None

    def _contexto(self, fid, viva=None):
        from vapt.derivacao import galeria as mg
        from vapt.derivacao import proposta
        ctx = viva['ctx'] if viva else self.ctx
        derivados = viva['derivados'] if viva else self.derivados
        chave = (fid, viva['chave'] if viva else None)
        if chave not in self._cf:
            # a mestre de onde o membro parte, com a quebra de linha da familia (a mesma da derivacao, M7b, C2)
            mestre = proposta.mestre_do_membro(ctx, self.kv, self.por_formato[fid], derivados.get(fid))
            self._cf[chave] = mg.contexto_do_formato(ctx, mestre, self.por_formato[fid], **self.kw)
        return self._cf[chave]

    def partida(self, fid, versao, viva=None):
        """Os elementos de onde o membro parte: a versao escolhida, a primeira sem falha ou a proposta derivada (a
        mesma regra da derivacao, vapt.derivacao.proposta.partida). viva: a familia com a quebra nova (_viva)."""
        from vapt.derivacao import proposta
        derivados, brutos = (viva['derivados'], viva['brutos']) if viva else (self.derivados, self.brutos)
        return proposta.partida(derivados.get(fid), brutos.get(fid), versao)

    def conferir(self, dados, antes=None):
        """True quando os dados da pagina seguem o formato da edicao (o mesmo esquema do rascunho), com o tamanho de
        cada elemento entre os limites da escala (escala_fora, M7b, D3; antes: as edicoes gravadas da familia no
        rascunho, revisao 1 da fase D). As quebras de linha, quando vem, seguem as regras do rascunho
        (vapt.tela.rascunho._conferir_quebras). Decisao 215: a caixa copiada de outra familia so o servidor grava; o
        pedido com caixas diferentes das gravadas (antes) e recusado."""
        from vapt import contratos
        from vapt.tela import rascunho
        if not isinstance(dados, dict) or not set(CAMPOS) <= set(dados) <= set(CAMPOS + CAMPOS_OPCIONAIS):
            return False
        gid, versao, edicoes = dados['familia'], dados['versao'], dados['edicoes']
        if not isinstance(gid, str) or gid not in self.familias:
            return False
        if isinstance(edicoes, list) and all(isinstance(e, dict) for e in edicoes) and caixas_de(edicoes) and \
                caixas_de(edicoes) != caixas_de(antes or []):
            return False
        # decisao 199 (1): so o arquivo de edicao aceita edicao no palco. O pedido que diz outro arquivo e recusado
        if 'arquivo' in dados and dados['arquivo'] != self.arquivo_de_edicao(gid):
            return False
        if versao is not None and (not isinstance(versao, str) or versao not in self.versoes(gid)):
            return False
        familia = {'versao': versao, 'confirmada': False, 'edicoes': edicoes}
        if 'quebras' in dados:
            familia['quebras'] = dados['quebras']
        prova = {'esquema': rascunho.ESQUEMA, 'job_id': '0' * 32, 'laudo_sha256': '0' * 64,  # numero-neutro: tamanhos dos ids
                 'origem': 'rascunho', 'atualizado_em': '2026-01-01T00:00:00', 'familias': {gid: familia}}
        try:
            contratos.validar(prova, rascunho.ESQUEMA)
        except contratos.ErroContrato:
            return False
        # todos os elementos no KV, e o grupo (M7b, D1) com o elemento da edicao primeiro
        if not ids_conferem(edicoes, self.kv_por_id):
            return False
        # o tamanho de cada elemento entre os limites da escala (M7b, D3); o que o rascunho gravado ja tinha fora
        # deles passa (antes, revisao 1 da fase D)
        if escala_fora(edicoes, antes):
            return False
        return self._quebras_conferem(edicoes, dados.get('quebras') or [])

    def _quebras_conferem(self, edicoes, quebras):
        """Cada quebra num texto do elemento que ela cita, uma por texto, com os indices e as posicoes no texto de
        agora (o do KV, ou o editado pelo DA nas edicoes da familia, decisoes-v1.md, 171)."""
        from vapt.briefing import modelo as mb
        from vapt.derivacao import quebras as mq
        camadas = mb.camadas_do_laudo(self.ctx['laudo'])
        vistos = set()
        for q in quebras:
            el, c = self.kv_por_id.get(q['elemento']), camadas.get(q['layer_id'])
            if el is None or q['layer_id'] not in el['layer_ids'] or q['layer_id'] in vistos or c is None or \
                    c.get('tipo') != 'texto':
                return False
            vistos.add(q['layer_id'])
            if mq.conferir_da_familia(c, q['manter'], q['inseridas'], mq.texto_editado(edicoes, q['elemento'])):
                return False
        return True

    def _viva(self, gid, quebras, edicoes, origem):
        """A familia com as quebras de linha do rascunho (M7b, C3), ou None quando elas sao as do briefing (quebras
        None: as do briefing, sem conferir; a previa manda a lista, vazia sem quebra). O briefing em memoria troca as
        quebras da familia pelas do rascunho e leva as edicoes dela (a derivacao so le delas qual texto foi editado: o
        texto editado nao tem medida); a medida vem de
        vapt.derivacao.medida_quebras.medir, com o cache, so dos textos do KV com quebra; os membros sao derivados
        de novo com ela, e os devolvidos que partem da galeria (vapt.derivacao.proposta.usa_galeria) ganham a
        galeria de novo, como a tela monta na abertura (vapt.tela.estado.galerias). Guardada pela chave das
        quebras: a proxima edicao na familia parte dela."""
        import json

        from vapt.briefing import modelo as mb
        from vapt.briefing import salvar
        from vapt.derivacao import medida_quebras
        from vapt.derivacao import nucleo as nd
        from vapt.derivacao import proposta
        from vapt.derivacao import quebras as mq
        from vapt.job import nucleo
        if quebras is None:
            return None
        b = self.ctx['briefing']
        fids = list(self.familias[gid])
        antes = [q for q in b.get('quebras_por_familia') or []
                 if q.get('familia') is not None and set(q.get('formatos') or ()) & set(fids)]
        tipo = origem if origem in (mb.ORIGEM_DA, mb.ORIGEM_FIXTURE) else mb.ORIGEM_DA
        novas = salvar.quebras_da_familia(gid, fids, {'quebras': quebras}, tipo)
        editados = sorted({q['elemento'] for q in quebras if mq.texto_editado(edicoes, q['elemento']) is not None})
        if _assinatura(novas) == _assinatura(antes) and not editados:
            return None
        chave = json.dumps([gid, _assinatura(novas), editados])
        if chave in self._vivas:
            viva = self._vivas.pop(chave)
            self._vivas[chave] = viva
            return viva
        novo = dict(b, quebras_por_familia=[q for q in b.get('quebras_por_familia') or [] if q not in antes] + novas)
        novo['composicoes'] = [c for c in b.get('composicoes') or [] if not set(c['formatos']) & set(fids)] + [
            {'familia': gid, 'formatos': fids, 'versao': None, 'edicoes': list(edicoes), 'confirmada': False,
             'confirmacao': None, 'arquivo_de_edicao': self.arquivo_de_edicao(gid)}]
        a_medir = [n for n, q in zip(novas, quebras) if q['elemento'] not in editados]
        medidas = dict(self.ctx.get('medidas_quebras') or {})
        if a_medir and self.ctx.get('pasta') is not None:
            pasta = self.ctx['pasta']
            medidas.update(medida_quebras.medir(pasta, self.ctx['laudo'], {'quebras_por_familia': a_medir},
                                                nucleo.ler_estado(pasta)))
        # so as quebras e as composicoes mudam: as funcoes resolvidas do contexto continuam valendo
        ctx = dict(self.ctx, briefing=novo, medidas_quebras=medidas)
        derivados = dict(self.derivados)
        derivados.update(nd.derivar_em_memoria(ctx, so=fids, composicoes=False, **self.kw)['formatos'])
        # a galeria so dos membros que a derivacao tira dela, pela mesma regra (proposta.galeria_dos_devolvidos): o
        # membro que a quebra nova deixa sem galeria (tambem pela quebra sem medida) nao parte da versao de antes
        brutos = {f: v for f, v in self.brutos.items() if f not in fids}
        por, _mestre, sem_medida = proposta.galeria_dos_devolvidos(
            ctx, self.kv, derivados, [self.por_formato[f] for f in fids], arquivo=self.arquivo_de_edicao(gid),
            **self.kw)
        brutos.update({f: {v['id']: v for _n, v in pares} for f, pares in por.items()})
        viva = {'chave': chave, 'ctx': ctx, 'derivados': derivados, 'brutos': brutos, 'sem_medida': sem_medida}
        self._vivas[chave] = viva
        while len(self._vivas) > VIVAS_MAX:
            velha = next(iter(self._vivas))
            del self._vivas[velha]
            self._cf = {k: v for k, v in self._cf.items() if k[1] != velha}
        return viva

    def _texto(self, eid, texto, quebra=None):
        """(texto aceito, recusa ou None) de uma edicao de texto no elemento. Cada caractere com tinta e conferido na
        face do trecho do KV de que ele herda o estilo (decisao 214; vapt.derivacao.quebras.runs_do_editado), com a
        caixa alta desse trecho, nas linhas que o palco desenha (quebra: o item da quebra da familia do elemento, como
        em trocar_texto): a palavra inserida na fronteira de linha herda pela linha em que fica."""
        from vapt.derivacao import quebras as mq
        el = self.kv_por_id[eid]
        if any((self.base.get(lid) or {}).get('como_imagem') for lid in el['layer_ids']):
            return None, TEXTO_COMO_IMAGEM
        textos = [lid for lid in el['layer_ids'] if (self.base.get(lid) or {}).get('linhas')]
        if len(textos) != 1:
            return None, 'Este elemento não tem um texto só para editar.'
        if not texto.strip():
            return None, 'O texto ficou vazio. Para tirar o elemento, use Apagar.'
        peca = self.base[textos[0]]
        sem_fonte = 'A fonte deste texto não está no job, e sem ela a tela não mostra o texto novo.'
        runs = (peca.get('_texto') or {}).get('runs') or [{}]
        if quebra is not None:
            linhas = mq.linhas_do_editado(texto, quebra['manter'], quebra['inseridas'])
        else:
            linhas = mq.linhas_editadas(texto)
        novos = mq.runs_do_editado(runs, linhas, '\n') if runs[0] else None
        if novos is None:
            face_id = next((t['face'] for ln in peca['linhas'] for t in ln['trechos'] if t['face']), None)
            face = self.faces.get(face_id)
            if face is None:
                return None, sem_fonte
            faltam = caracteres_que_faltam(texto, face, runs[0].get('font_caps') in ('ALL_CAPS', 'SMALL_CAPS'))
        else:
            faltam = []
            for r in novos:
                if not r['tem_tinta']:
                    continue
                face = self.faces.get((peca.get('_faces') or {}).get(r.get('fonte_ps')))
                if face is None:
                    return None, sem_fonte
                for ch in caracteres_que_faltam(r['texto'], face, r.get('font_caps') in ('ALL_CAPS', 'SMALL_CAPS')):
                    if ch not in faltam:
                        faltam.append(ch)
        if faltam:
            return None, _texto_da_recusa(faltam)
        return texto, None

    def _alinhamento(self, eid):
        """A recusa do alinhamento das linhas no elemento (0.12.0), ou None quando ele vale: o elemento com um texto de
        ponto so, que nao vai como imagem, com a fonte no job (a mesma regra da quebra de linha no palco,
        _textos_da_quebra). Na caixa de texto do Photoshop o render alinha nas bordas da caixa e quebra a linha
        sozinho, e a derivacao nao veria as linhas que ele desenha."""
        el = self.kv_por_id[eid]
        if any((self.base.get(lid) or {}).get('como_imagem') for lid in el['layer_ids']):
            return TEXTO_COMO_IMAGEM
        textos = [lid for lid in el['layer_ids'] if (self.base.get(lid) or {}).get('linhas')]
        if len(textos) != 1:
            return TEXTO_SEM_UM_TEXTO_PARA_ALINHAR
        peca = self.base[textos[0]]
        if (peca.get('_texto') or {}).get('tipo_caixa') == 'paragrafo':
            return TEXTO_EM_CAIXA
        face_id = next((t['face'] for ln in peca['linhas'] for t in ln['trechos'] if t['face']), None)
        if self.faces.get(face_id) is None or peca.get('modo') == 'imagem':
            return TEXTO_ALINHAR_SEM_FONTE
        return None

    def previa(self, dados, origem='da', antes=None):
        """{'familia', 'versao', 'membros': [{'formato', 'palco', 'falhas', 'decisoes_do_da', 'avisos',
        'validacoes_reprovadas', 'situacao', 'sangria_do_da': {id: [lados]}, 'quadro': {'margem', 'area_segura'}}],
        'apagados',
        'textos_editados', 'alinhamentos_do_da', 'recusas', 'alinhados', 'no_quadro', 'textos_da_quebra', 'tempo_ms'},
        ou None quando os
        dados nao seguem o formato. no_quadro: os alinhamentos no quadro que valem em cada membro, com o valor da linha
        (M7b, D2). sangria_do_da: os lados em que o DA deixou cada elemento passar da borda do membro (M7b, D4).
        decisoes_do_da: o piso de escala ou de distancia que o elemento mexido pelo DA fura, fora das falhas, com o
        valor no texto ({'codigo', 'texto', 'elementos', 'medidas'}; M7b, D5). antes: as edicoes gravadas da familia
        no rascunho (o servidor as le), para o tamanho que ja estava fora dos limites nunca travar a familia (revisao
        1 da fase D). O membro devolvido sem versao da galeria vem com situacao 'devolvido', o palco do formato
        devolvido e a falha que diz por que (_devolvido; previa igual ao Salvar, M7b). So previa: nada e gravado.
        Decisao 215: copia_sem_efeito ({'arquivo', 'medida'} das caixas copiadas de outra familia que deixaram de
        valer, ou None) e copiados (os elementos com a caixa copiada que vale)."""
        with self._trava:
            return self._previa(dados, origem, antes)

    def _previa(self, dados, origem, antes):
        from vapt.tela import estado
        inicio = time.perf_counter()
        r = self._layouts(dados, origem, antes)
        if r is None:
            return None
        gid, versao = dados['familia'], dados['versao']
        lays, viva, aceitas, recusas, quebras = r['lays'], r['viva'], r['aceitas'], r['recusas'], r['quebras']
        tintas, ref = r['tintas'], r['ref']
        # o texto editado no palco sai nas linhas da quebra da familia (M7b, C4)
        quebras_por_elemento = {q['elemento']: q for q in quebras}
        membros, apagados_fam, textos_fam, alinhados_fam, no_quadro_fam = [], [], {}, [], []
        alinhamentos_fam = {}
        sem_arquivo = lays.get(ref) is None
        for fid in self.familias[gid]:
            lay = lays.get(fid)
            if lay is None or 'erro' in lay:
                # o membro devolvido sem versao da galeria fica devolvido, como o "Salvar e seguir" o grava; o que nao
                # tem o que copiar fica com a proposta do motor, com a frase
                membros.append(dict(self._sem_copia(fid, viva, sem_arquivo and fid != ref, lay is not None),
                                    arquivo_de_edicao=fid == ref))
                continue
            cf = lay['cf']
            W, H = cf['W'], cf['H']
            apagados, textos, alinhados = lay['apagados'], lay['textos'], lay['alinhados']
            falhas, avisos, reprovadas = lay['falhas'], lay['avisos'], lay['reprovadas']
            els = lay['elementos']
            palco = estado.palco_da_variante(fid, W, H, {'elementos': els}, self.laudo, self.base)
            for eid, texto in textos.items():
                # decisao 214: o estilo de cada caractere sai dos trechos do KV (as pecas base), com o corpo na escala
                # do elemento no formato, a mesma do palco
                tr = next((x.get('transformacao') for x in els if x['id'] == eid), None) or {}
                trocar_texto(palco, eid, texto, quebras_por_elemento.get(eid), base=self.base, escala=tr.get('s'),
                             faces=self.faces)
            # 0.12.0: o alinhamento das linhas que o DA escolheu, em todo arquivo da familia
            for eid, valor in sorted((lay.get('alinhamentos') or {}).items()):
                el = next((x for x in els if x['id'] == eid), {'id': eid})
                alinhar_texto(palco, eid, valor, {
                    lid: estado.justificacoes_no_formato(self.base[lid], el)
                    for lid in self.kv_por_id[eid]['layer_ids'] if (self.base.get(lid) or {}).get('linhas')})
            # o rotulo do texto editado (moldura, alcas e etiqueta) fica na caixa das linhas do DA (0.9.6): encolhe
            # quando o texto perde linhas
            vis = lay.get('caixas_visiveis') or {}
            for e in palco.get('elementos') or []:
                if e.get('id') in textos and e['id'] in tintas and e['id'] in vis:
                    e['caixa'] = [round(float(v), 4) for v in vis[e['id']]]  # numero-neutro: casas do px
                    e['caixa_das_linhas'] = True
            # os quadros do membro para alinhar (M7b, D2): a margem dele e a area segura da folha, None sem ela
            seg = ((cf.get('areas') or {}).get('area_segura') or {}).get('caixa')
            copia = fid != ref
            membros.append({'formato': fid, 'palco': palco,
                            # decisao 199: o arquivo de edicao e o unico em que o DA edita; os outros dizem em
                            # palavras como ficaram ("Igual ao seu", "Ajustado pelo Vapt" com a frase de cada
                            # ajuste, ou "Pede ajuste" com o valor)
                            'arquivo_de_edicao': not copia,
                            'frases': list(lay.get('frases') or []),
                            # os elementos de cada ajuste e de cada relacao quebrada: o "Ver grande" da tela mostra o
                            # contorno deles (decisao 199, 6)
                            'ajustes': [{'tipo': a.get('tipo') or a.get('codigo'), 'frase': a['frase'],
                                         'elementos': list(a.get('elementos') or
                                                           ([a['elemento']] if a.get('elemento') else []))}
                                        for a in ((lay.get('transferencia') or {}).get('ajustes') or [])],
                            'falhas': [dict({'codigo': f['codigo'], 'texto': f['texto']},
                                            **({'elementos': list(f['elementos'])}
                                               if copia and f['codigo'] == 'relacao_quebrada' else {}))
                                       for f in falhas],
                            # o piso que o DA furou com a edicao dele (M7b, D5), com o valor no texto
                            'decisoes_do_da': [{'codigo': d['codigo'], 'texto': d['texto'],
                                                'elementos': list(d['elementos']),
                                                'medidas': dict(d.get('medidas') or {})}
                                               for d in lay['decisoes_do_da']],
                            'avisos': [{'codigo': a['codigo'], 'texto': a['texto']} for a in avisos],
                            'validacoes_reprovadas': reprovadas,
                            # nada refaz o encaixe depois da edicao (0.9.5): o arquivo de edicao e sempre a proposta
                            # com as edicoes do DA, e o que precisa do olhar dele vem nas falhas. Os outros: igual,
                            # ajustado ou pede_ajuste (199, 3)
                            'situacao': lay['situacao'] if copia else 'proposta',
                            # revisao da 0.10.0: o contorno do "Mostrar o seu por cima", pela mesma conta da copia
                            'seu_levado': [{'id': k, 'caixa': c} for k, c in (lay.get('levado') or {}).items()]
                            if copia else [],
                            'sangria_do_da': {k: list(v) for k, v in lay['sangria_do_da'].items()},
                            'quadro': {'margem': [round(v, 4) for v in lay['quadros']['margem']],  # numero-neutro: casas do px
                                       'area_segura': [round(float(v), 4) for v in seg] if seg else None}})  # numero-neutro: casas do px
            for k in apagados:
                if k not in apagados_fam:
                    apagados_fam.append(k)
            textos_fam.update(textos)
            alinhamentos_fam.update(lay.get('alinhamentos') or {})
            alinhados_fam.extend(dict(a, formato=fid) for a in alinhados)
            no_quadro_fam.extend(dict(a, formato=fid) for a in lay['no_quadro'])
        nome = self._nome
        # 0.15.0 (204): o grafismo que a versao tirou e o DA nao apagou sai com a origem 'vapt', e a tela oferece
        # "Devolver"
        do_vapt = set((lays.get(ref) or {}).get('tirados') or ()) - \
            {e['elemento'] for e in aceitas if e['acao'] == 'apagar'}
        return {'familia': gid, 'versao': versao, 'membros': membros, 'arquivo_de_edicao': ref,
                'apagados': [{'elemento': k, 'nome': nome(k), 'origem': 'vapt' if k in do_vapt else origem}
                             for k in apagados_fam],
                'textos_editados': [{'elemento': k, 'nome': nome(k)} for k in textos_fam],
                # 0.12.0: o alinhamento das linhas que muda o texto (o do KV escolhido de novo nao entra)
                'alinhamentos_do_da': [{'elemento': k, 'nome': nome(k), 'alinhamento': v}
                                       for k, v in sorted(alinhamentos_fam.items())],
                'recusas': recusas, 'alinhados': alinhados_fam, 'no_quadro': no_quadro_fam,
                'textos_da_quebra': self._textos_da_quebra(aceitas),
                # decisao 215: a caixa copiada de outra familia que deixou de valer, e os elementos copiados
                'copia_sem_efeito': (lays.get(ref) or {}).get('copia_sem_efeito'),
                'copiados': list((lays.get(ref) or {}).get('copiados') or []),
                'tempo_ms': round((time.perf_counter() - inicio) * POR_MS, CASAS_MS)}

    def _layouts(self, dados, origem='da', antes=None):
        """A conta da previa ate o layout da familia (proposta.layout_da_familia), sem o palco: {'lays', 'ctx',
        'viva', 'aceitas', 'recusas', 'quebras', 'tintas', 'ref', 'derivados', 'brutos'}, ou None quando os dados nao
        seguem o formato (conferir). A previa e a copia do layout de outra familia (decisao 215) partem desta."""
        from vapt.derivacao import proposta
        with self._trava:
            if not self.conferir(dados, antes):
                return None
            gid, versao = dados['familia'], dados['versao']
            recusas, aceitas = [], []
            # decisao 214: a fonte e conferida nas linhas que o palco desenha, com a quebra da familia; as posicoes dela
            # contam na ultima edicao de texto do elemento
            ultima = {e['elemento']: n for n, e in enumerate(dados['edicoes']) if e['acao'] == 'texto'}
            quebra_de = {q['elemento']: q for q in dados.get('quebras') or []}
            for n, e in enumerate(dados['edicoes']):
                if e['acao'] == 'texto':
                    item = quebra_de.get(e['elemento']) if ultima.get(e['elemento']) == n else None
                    texto, recusa = self._texto(e['elemento'], e['texto'], item)
                    if recusa is not None:
                        recusas.append({'elemento': e['elemento'], 'texto': recusa})
                        continue
                    e = dict(e, texto=texto)
                elif e['acao'] == 'alinhar_texto':
                    # 0.12.0: a recusa do alinhamento leva a acao (a do texto fica como era, sem ela)
                    recusa = self._alinhamento(e['elemento'])
                    if recusa is not None:
                        recusas.append({'elemento': e['elemento'], 'acao': 'alinhar_texto', 'texto': recusa})
                        continue
                aceitas.append(e)
            # a quebra de linha do rascunho diferente da do briefing: os membros partem da derivacao com ela (M7b,
            # C3). O pedido sem o campo e o rascunho sem quebra na familia: a previa nunca volta a quebra do briefing
            # de antes, que "Salvar e seguir" tira (revisao do C)
            quebras = dados.get('quebras') or []
            viva = self._viva(gid, quebras, aceitas, origem)
            # a tinta das linhas do DA do texto editado (0.9.6; decisao 196), a mesma medida do "Salvar e seguir": a
            # caixa do texto encolhe e cresce com as linhas dele no palco e na conferencia
            fids = list(self.familias[gid])
            # decisao 199: o arquivo de edicao parte da galeria ou da proposta com as edicoes do DA, e os outros
            # copiam o layout aprovado nele, pela mesma conta do "Salvar e seguir"
            # (vapt.derivacao.proposta.layout_da_familia). A tinta das linhas do DA e medida no arquivo de edicao, com
            # a quebra dele
            ref = self.arquivo_de_edicao(gid)
            ctx = viva['ctx'] if viva else self.ctx
            derivados, brutos = (viva['derivados'], viva['brutos']) if viva else (self.derivados, self.brutos)
            tintas = proposta.tintas_editadas(ctx, self.kv, aceitas, ref) \
                if ref and any(e['acao'] == 'texto' for e in aceitas) else {}
            cache = self._cf.setdefault(('familia', viva['chave'] if viva else None), {})
            lays = proposta.layout_da_familia(
                ctx, self.kv, {'familia': gid, 'formatos': fids, 'versao': versao, 'edicoes': aceitas,
                               'arquivo_de_edicao': ref},
                derivados=derivados, versoes={ref: brutos.get(ref) or {}}, tintas=tintas, cache=cache, **self.kw)
            return {'lays': lays, 'ctx': ctx, 'viva': viva, 'aceitas': aceitas, 'recusas': recusas,
                    'quebras': quebras, 'tintas': tintas, 'ref': ref, 'derivados': derivados, 'brutos': brutos}

    # -------------------------------------------------------------- a copia do layout de outra familia (215)
    def escala_da_copia(self, origem, destino):
        """A escala unica s da copia do layout da familia origem para a familia destino (decisao 215), pelos quadros
        dos dois arquivos de edicao (proposta.escala_da_copia, a conta da 199). So filtra as origens que a tela
        oferece: o numero da janela vem da copia (copia_entre_familias)."""
        from vapt.derivacao import proposta
        with self._trava:
            ref_o, ref_d = self.arquivo_de_edicao(origem), self.arquivo_de_edicao(destino)
            return proposta.escala_da_copia(proposta.quadros_do_membro(self._contexto(ref_o)),
                                            proposta.quadros_do_membro(self._contexto(ref_d)))

    def _fora_da_copia(self, gid):
        """True quando a familia nao entra na copia de outra familia (decisao 215), nem como origem nem como destino:
        sem arquivo de edicao; o arquivo de edicao com a mestre propria (o artboard do DA, resposta 4 do Duda) ou
        devolvido por uma guarda do motor (fora de proposta.usa_galeria); um formato com valor de spec a espera do DA
        (por_confirmar)."""
        from vapt.derivacao import nucleo as nd
        from vapt.derivacao import proposta
        ref = self.arquivo_de_edicao(gid)
        d = self.derivados.get(ref) if ref else None
        if d is None:
            return True
        if d.get('situacao') == 'derivado':
            if (d.get('mestre') or {}).get('tipo', 'kv') != 'kv':
                return True
        elif not proposta.usa_galeria(d):
            return True
        return any(((self.derivados.get(f) or {}).get('devolucao') or {}).get('motivo') in nd.MOTIVOS_POR_CONFIRMAR
                   for f in self.familias.get(gid, ()))

    def origens_da_copia(self, gid, irmas):
        """As familias de onde a familia gid pode copiar o layout (decisao 215): [{'familia', 'arquivo' (o arquivo de
        edicao dela)}], em ordem pelo arquivo. irmas: os ids das familias da mesma orientacao. Ficam de fora a propria
        familia, as que nao entram na copia (_fora_da_copia) e as com a escala da copia abaixo de
        derivacao.grupo_escala_min (a regra do tamanho da 208), e a de outra orientacao (a do arquivo de edicao, em pe
        como o publico ve). Vazio quando a familia gid nao entra na copia."""
        from vapt.derivacao import escala as mod_escala
        from vapt.derivacao import proposta
        with self._trava:
            if gid not in self.familias or self._fora_da_copia(gid):
                return []

            def orientacao(g):
                m = proposta.membros_na_composicao([self.por_formato[self.arquivo_de_edicao(g)]])[0]
                return mod_escala.orientacao(m['W'], m['H'])
            minimo = float(limites.valor('derivacao.grupo_escala_min'))
            saida = []
            for o in irmas:
                if o == gid or o not in self.familias or self._fora_da_copia(o) or orientacao(o) != orientacao(gid):
                    continue
                if self.escala_da_copia(o, gid) < minimo:
                    continue
                saida.append({'familia': o, 'arquivo': self.arquivo_de_edicao(o)})
            return sorted(saida, key=lambda x: (x['arquivo'], x['familia']))

    def copia_entre_familias(self, destino, origem, f_o, f_d):
        """A copia do layout de agora do arquivo de edicao da familia origem para o da familia destino (decisao 215),
        sem gravar nada. f_o, f_d: as familias no rascunho gravado ({'versao', 'edicoes', 'quebras', ...}). Devolve
        {'edicoes', 'quebras', 'versao', 'copiado_de', 's', 'situacao', 'frases', 'ajustes', 'avisos', 'n_piso',
        'falhas_d', 'origem_menor'}: as edicoes e as quebras que o destino grava (substituem as dele), a versao de
        partida dele, o copiado_de do rascunho (com a familia de antes, para o Desfazer de um clique), a escala, a
        situacao, as frases da escada (os ajustes para caber e os avisos do encaixe, tambem em separado), quantos
        elementos ficam abaixo do piso da 133, os textos das outras falhas do destino e se a origem e menor que o
        destino (resposta 1 do Duda: pede ajuste). Ou {'motivo': codigo, ...}: SEM_LAYOUT
        (o arquivo de edicao da origem sem layout), ESCALA_PEQUENA (com 's'), FONTE (com 'elemento' e 'texto') e
        ERRO_NA_COPIA (com 'detalhe'). Antes de devolver, o destino e derivado com as edicoes e as quebras novas e
        conferido contra a copia (a conferencia M4): o que nao bate e ERRO_NA_COPIA. Guardada pela chave dos dados."""
        import json
        with self._trava:
            chave = json.dumps([destino, origem, f_o, f_d, self.arquivos], sort_keys=True)
            if chave not in self._copias:
                self._copias[chave] = self._copiar(destino, origem, f_o or {}, f_d or {})
            return self._copias[chave]

    def _copiar(self, destino, origem, f_o, f_d):
        import copy as mod_copy

        from vapt.briefing import modelo as mb
        from vapt.derivacao import proposta
        from vapt.derivacao import quebras as mq
        from vapt.tela import rascunho
        if destino not in self.familias or origem not in self.familias or destino == origem:
            return {'motivo': 'ERRO_NA_COPIA', 'detalhe': ['familia']}
        ref_o, ref_d = self.arquivo_de_edicao(origem), self.arquivo_de_edicao(destino)
        # i) o layout de agora do arquivo de edicao da origem (L*), pela conta da previa
        edicoes_o = list(f_o.get('edicoes') or [])
        r_o = self._layouts({'familia': origem, 'versao': rascunho.versao_de_agora(f_o.get('versao'),
                                                                                  self.versoes(origem)),
                             'edicoes': edicoes_o, 'quebras': list(f_o.get('quebras') or [])}, antes=edicoes_o)
        lay_o = (r_o or {}).get('lays', {}).get(ref_o)
        if lay_o is None or 'erro' in lay_o:
            return {'motivo': 'SEM_LAYOUT'}
        # ii) a copia (a conta da 199, s <= 1)
        formato_d = self.por_formato[ref_d]
        try:
            lay_t = proposta.copia_entre_familias(r_o['ctx'], self.kv, lay_o, formato_d, **self.kw)
        except Exception as e:  # noqa: BLE001 - a copia que quebra nao grava nada
            return {'motivo': 'ERRO_NA_COPIA', 'detalhe': ['copia: %s' % type(e).__name__]}
        s = float(lay_t['transferencia']['s'])
        if s < float(limites.valor('derivacao.grupo_escala_min')):
            return {'motivo': 'ESCALA_PEQUENA', 's': s}
        # iii) e vi) as edicoes: o texto, o alinhamento, os apagados e as caixas
        eds = proposta.edicoes_da_copia(lay_t, lay_o, self.kv)
        eds_t = [e for e in eds if e['acao'] != 'caixa']
        # iv) as quebras da origem (passos 1 e 2) e v) as neutras do destino derivado (passo 3), sobre a derivacao do
        # destino ja com as quebras copiadas, refeita uma vez quando cresce
        qs = proposta.quebras_da_copia(r_o['ctx'], self.kv, lay_o, r_o['quebras'], self.por_formato[ref_o],
                                       r_o['derivados'][ref_o], r_o['aceitas'])
        viva = None
        for _vez in range(2):  # numero-neutro: a derivacao do destino e refeita uma vez
            viva = self._viva(destino, qs, eds_t, 'da')
            ctx_d = viva['ctx'] if viva else self.ctx
            derivados_d = viva['derivados'] if viva else self.derivados
            novas = proposta.quebras_neutras(ctx_d, self.kv, qs, eds_t, formato_d, derivados_d.get(ref_d))
            if not novas:
                break
            qs = qs + novas
        # vii) a versao de partida do destino: a gravada, quando a galeria a tem; senao a partida efetiva
        brutos = (viva['brutos'] if viva else self.brutos).get(ref_d) or {}
        versoes_d = self.versoes(destino)
        if f_d.get('versao') in versoes_d:
            versao_d = f_d['versao']
        else:
            versao_d = proposta.versao_de_partida(None, brutos, None) if brutos else None
            versao_d = versao_d if versao_d in versoes_d else None
        # viii) o destino com as edicoes e as quebras novas, pela conta da previa
        r_d = self._layouts({'familia': destino, 'versao': versao_d, 'edicoes': eds, 'quebras': qs}, antes=eds)
        if r_d is None:
            return {'motivo': 'ERRO_NA_COPIA', 'detalhe': ['conferir']}
        if r_d['recusas']:
            # decisao 214: o texto copiado que a face nao cobre nas linhas do destino
            x = r_d['recusas'][0]
            return {'motivo': 'FONTE', 'elemento': x['elemento'], 'nome': self._nome(x['elemento']),
                    'texto': x['texto']}
        lays = r_d['lays']
        lay_d = lays.get(ref_d)
        if lay_d is None or 'erro' in lay_d or any('erro' in (v or {}) for v in lays.values()):
            return {'motivo': 'ERRO_NA_COPIA', 'detalhe': ['destino sem layout']}
        # ix) a conferencia M4: o destino derivado e a copia
        detalhe = conferir_copia(lay_t, lay_d)
        if detalhe:
            return {'motivo': 'ERRO_NA_COPIA', 'detalhe': detalhe}
        # x) a situacao e as frases
        n_piso = sum(1 for f in lay_d['falhas'] if f['codigo'] == 'abaixo_do_piso_da_regra')
        falhas_d = [f['texto'] for f in lay_d['falhas'] if f['codigo'] != 'abaixo_do_piso_da_regra']
        textos_t = {f['texto'] for f in lay_t['falhas']}
        escada = [f for f in lay_t.get('frases') or [] if f not in textos_t]
        # os ajustes para caber (transferencia.ajustes) e os avisos do encaixe neste arquivo (as outras frases)
        ajustes = [a['frase'] for a in (lay_t['transferencia'] or {}).get('ajustes') or [] if a.get('frase')]
        avisos = [f for f in escada if f not in ajustes]
        # resposta 1 do Duda (26/11): a origem menor que o destino. A copia nunca aumenta (s = 1), e no sentido
        # contrario ela encolheria: a copia do menor para o maior pede ajuste, e a janela avisa
        origem_menor = s >= S_IGUAL and self.escala_da_copia(destino, origem) < S_IGUAL
        if falhas_d or n_piso or lay_t['situacao'] == 'pede_ajuste' or origem_menor:
            situacao = 'pede_ajuste'
        elif lay_t['situacao'] == 'ajustado' or (lay_t['transferencia'] or {}).get('ajustes') or s < S_IGUAL:
            situacao = 'ajustado'
        else:
            situacao = 'igual'
        # xi) o copiado_de, com a familia de antes (resposta 2 do Duda em 26/11: o Desfazer tira a copia inteira)
        antes = {'versao': f_d.get('versao'), 'edicoes': mod_copy.deepcopy(list(f_d.get('edicoes') or [])),
                 'quebras': mod_copy.deepcopy(list(f_d.get('quebras') or []))}
        if f_d.get('copiado_de'):
            antes['copiado_de'] = mod_copy.deepcopy(f_d['copiado_de'])
        # os avisos de arquivo trocado e de layout mudado, que a copia tira: o Desfazer os devolve (nada calado)
        for k in ('arquivo_trocado', 'layout_mudou'):
            if f_d.get(k):
                antes[k] = mod_copy.deepcopy(f_d[k])
        copiado_de = {'familia': origem, 'arquivo': ref_o, 'para': ref_d, 's': min(s, 1.0), 'situacao': situacao,
                      'frases': [f[:FRASE_MAX] for f in (escada + falhas_d)[:FRASES_MAX]], 'em': mb.agora(),
                      'quebras': sorted({q['layer_id'] for q in qs if mq.texto_editado(eds, q['elemento']) is None}),
                      'antes': antes}
        return {'edicoes': eds, 'quebras': qs, 'versao': versao_d, 'copiado_de': copiado_de, 's': s,
                'situacao': situacao, 'frases': escada, 'ajustes': ajustes, 'avisos': avisos, 'n_piso': n_piso,
                'falhas_d': falhas_d, 'origem_menor': origem_menor}

    def _sem_copia(self, fid, viva, sem_arquivo, erro):
        """O membro sem layout da familia, como o "Salvar e seguir" o grava (decisao 199; previa igual ao Salvar): o
        devolvido fica devolvido (_devolvido); o derivado que nao tem o que copiar (o arquivo de edicao sem layout) ou
        cuja copia quebrou (erro) fica com a proposta do motor, com a frase que diz por que."""
        from vapt.tela import estado
        d = (viva['derivados'] if viva else self.derivados)[fid]
        if d['situacao'] != 'derivado':
            m = self._devolvido(fid, viva)
            if erro:
                m['falhas'].append({'codigo': 'erro_na_copia', 'texto': TEXTO_ERRO_NA_COPIA})
            elif sem_arquivo and m['falhas'][0]['codigo'] == 'formato_devolvido':
                m['avisos'].append({'codigo': 'familia_sem_arquivo_de_edicao', 'texto': TEXTO_SEM_ARQUIVO_DE_EDICAO})
            return dict(m, arquivo_de_edicao=False, frases=[f['texto'] for f in m['falhas']], ajustes=[])
        W, H = d['formato']['composicao']
        falhas = [{'codigo': 'erro_na_copia', 'texto': TEXTO_ERRO_NA_COPIA}] if erro else []
        avisos = [{'codigo': 'familia_sem_arquivo_de_edicao', 'texto': TEXTO_SEM_ARQUIVO_DE_EDICAO}] \
            if sem_arquivo and not erro else []
        return {'formato': fid, 'palco': estado.palco(d, self.kv, self.laudo, self.base), 'falhas': falhas,
                'decisoes_do_da': [], 'avisos': avisos, 'validacoes_reprovadas': [], 'situacao': 'proposta',
                'arquivo_de_edicao': False, 'frases': [x['texto'] for x in falhas + avisos], 'ajustes': [],
                'sangria_do_da': {}, 'quadro': {'margem': [float(v) for v in (0, 0, W, H)], 'area_segura': None}}

    def _devolvido(self, fid, viva=None):
        """O membro devolvido sem versao da galeria, como a derivacao da familia confirmada o grava (previa igual ao
        Salvar, M7b): o palco do formato devolvido, sem layout do Vapt, e a falha que diz por que. A falha e a
        quebra de linha sem medida quando ela tirou a galeria do membro (vapt.derivacao.proposta.
        galeria_dos_devolvidos), e a frase da devolucao no resto."""
        from vapt.derivacao import proposta
        from vapt.tela import estado
        d = (viva['derivados'] if viva else self.derivados)[fid]
        W, H = d['formato']['composicao']
        if viva and viva.get('sem_medida') and proposta.usa_galeria(d):
            falha = {'codigo': 'quebra_sem_medida', 'texto': TEXTO_QUEBRA_SEM_MEDIDA}
        else:
            falha = {'codigo': 'formato_devolvido',
                     'texto': estado.texto_da_devolucao((d.get('devolucao') or {}).get('motivo'), 0)}
        return {'formato': fid, 'palco': estado.palco(d, self.kv, self.laudo, self.base), 'falhas': [falha],
                'decisoes_do_da': [], 'avisos': [], 'validacoes_reprovadas': [], 'situacao': 'devolvido',
                'sangria_do_da': {}, 'quadro': {'margem': [float(v) for v in (0, 0, W, H)], 'area_segura': None}}

    def _textos_da_quebra(self, edicoes):
        """Os textos que o DA pode quebrar na familia (M7b, C4), na ordem do KV: o elemento com um texto de ponto so
        (a caixa de paragrafo o render refaz na largura dela; o elemento apagado sai), com o texto de agora e as
        posicoes das quebras gravadas e dos espacos (vapt.derivacao.quebras.texto_para_quebrar). A pagina monta
        o controle da quebra com eles; o texto do cliente vai a ela so por textContent."""
        from vapt.briefing import modelo as mb
        from vapt.derivacao import quebras as mq
        camadas = mb.camadas_do_laudo(self.ctx['laudo'])
        apagados = {e['elemento'] for e in edicoes if e['acao'] == 'apagar'}
        saida = []
        for e in self.kv['elementos']:
            textos = [lid for lid in e['layer_ids'] if (camadas.get(lid) or {}).get('tipo') == 'texto']
            if e['id'] in apagados or len(textos) != 1 or \
                    (camadas[textos[0]].get('texto') or {}).get('tipo_caixa') == 'paragrafo':
                continue
            editado = mq.texto_editado(edicoes, e['id'])
            # 0.12.0: o alinhamento do texto no KV, para a pagina marcar o botao dele; None no texto de paragrafos com
            # alinhamentos diferentes (nenhum botao marcado, e toda escolha leva as linhas ao mesmo alinhamento)
            saida.append(dict(mq.texto_para_quebrar(camadas[textos[0]], editado), elemento=e['id'],
                              layer_id=textos[0], editado=editado is not None,
                              alinhamento_kv=mq.alinhamento_do_kv(camadas[textos[0]], editado is not None)))
        return saida

    def _nome(self, eid):
        e = self.kv_por_id[eid]
        return self.nomes.get(e.get('raiz')) or ''


def previa_gravada(editar, gid, f):
    """A previa da familia gid com o que o rascunho tem dela (f: a familia do rascunho), como a pagina a pede: a
    versao, as edicoes e as quebras de linha (decisao 199, 5: a confirmacao e o "Salvar e seguir" medem o mesmo).
    editar: Editor.previa. None quando os dados nao valem."""
    f = f or {}
    dados = {'familia': gid, 'versao': f.get('versao'), 'edicoes': list(f.get('edicoes') or []),
             'quebras': list(f.get('quebras') or [])}
    return editar(dados, antes=list(f.get('edicoes') or []))


def _transformacao(cf, caixas, k):
    """(s, origem no documento, destino) do elemento k no layout (a conta de galeria._elementos, sem arredondar)."""
    e = next(x for x in cf['kv']['elementos'] if x['id'] == k)
    c, m = [float(v) for v in caixas[k]], [float(v) for v in e['caixa']]
    if m[2] > m[0]:
        s = (c[2] - c[0]) / (m[2] - m[0])
    else:
        s = (c[3] - c[1]) / (m[3] - m[1]) if m[3] > m[1] else 1.0
    s *= float(e.get('escala_na_mestre') or 1.0)
    return s, [float(v) for v in e['caixa_doc'][:2]], c[:2], [float(v) for v in e['caixa_doc']]


def _levar(t, b):
    s, o, d = t[0], t[1], t[2]
    return [s * (b[0] - o[0]) + d[0], s * (b[1] - o[1]) + d[1], s * (b[2] - o[0]) + d[0], s * (b[3] - o[1]) + d[1]]


def conferir_copia(lay_t, lay_d, tol=TOL_COPIA):
    """A conferencia final da copia do layout de outra familia (decisao 215, M4): o arquivo de edicao do destino
    derivado com as edicoes e as quebras da copia (lay_d, de layout_da_familia) contra a copia (lay_t, de
    proposta.copia_entre_familias). Cada elemento com a mesma transformacao (a mesma escala e o mesmo ponto do
    documento: as caixas das duas mestres levadas pelas duas transformacoes ficam a menos de tol px), a mesma caixa
    visivel, os mesmos apagados, a mesma sangra, a mesma figura de fundo, os mesmos textos e alinhamentos, e todas as
    caixas copiadas valendo. Devolve a lista do que nao bate (vazia quando bate)."""
    detalhe = []
    cf_t, cf_d = lay_t['cf'], lay_d['cf']
    kv_d = {e['id']: e for e in cf_d['kv']['elementos']}
    if sorted(lay_t['caixas']) != sorted(lay_d['caixas']):
        detalhe.append('elementos: %s != %s' % (sorted(lay_t['caixas']), sorted(lay_d['caixas'])))
        return detalhe
    for k in sorted(lay_t['caixas']):
        tt, td = _transformacao(cf_t, lay_t['caixas'], k), _transformacao(cf_d, lay_d['caixas'], k)
        for b in (tt[3], td[3]):
            a, c = _levar(tt, b), _levar(td, b)
            if any(abs(x - y) > tol for x, y in zip(a, c)):
                detalhe.append('transformacao %s: %s != %s' % (k, a, c))
                break
        vt, vd = lay_t['caixas_visiveis'].get(k), lay_d['caixas_visiveis'].get(k)
        if vt is None or vd is None or any(abs(float(x) - float(y)) > tol for x, y in zip(vt, vd)):
            detalhe.append('caixa visivel %s: %s != %s' % (k, vt, vd))
        st = dict(lay_t['sangra'].get(k) or {})
        sd = dict(lay_d['sangra'].get(k) or kv_d[k]['sangra'])
        if {x: bool(v) for x, v in st.items()} != {x: bool(v) for x, v in sd.items()}:
            detalhe.append('sangra %s: %s != %s' % (k, st, sd))
    for campo in ('textos', 'alinhamentos'):
        if dict(lay_t.get(campo) or {}) != dict(lay_d.get(campo) or {}):
            detalhe.append('%s: %s != %s' % (campo, lay_t.get(campo), lay_d.get(campo)))
    if sorted(lay_t['apagados']) != sorted(lay_d['apagados']):
        detalhe.append('apagados: %s != %s' % (lay_t['apagados'], lay_d['apagados']))
    if lay_t.get('figura_de_fundo') != lay_d.get('figura_de_fundo'):
        detalhe.append('figura_de_fundo: %s != %s' % (lay_t.get('figura_de_fundo'), lay_d.get('figura_de_fundo')))
    if sorted(lay_d.get('copiados') or ()) != sorted(lay_t['caixas']) or lay_d.get('copia_sem_efeito'):
        detalhe.append('copiados: %s' % (lay_d.get('copiados'),))
    return detalhe


def hash_dos_layouts(previa):
    """{id do formato: sha256 do palco} de cada arquivo da previa da familia (decisao 199, 5; 0.10.0): o layout de
    cada arquivo como a janela mostrou, para a impressao da confirmacao (175). O palco vai em JSON com as chaves em
    ordem; a previa e deterministica, e a mesma familia da o mesmo hash."""
    import hashlib
    import json
    return {m['formato']: hashlib.sha256(json.dumps(m['palco'], sort_keys=True, ensure_ascii=True,
                                                    separators=(',', ':')).encode('utf-8')).hexdigest()
            for m in (previa or {}).get('membros') or []}


def _assinatura(entradas):
    """As quebras de linha de familia (entradas de quebras_por_familia) sem a origem da decisao, em ordem: o texto, os
    indices que ficam, as posicoes inseridas, quem fez e a aprovacao."""
    return sorted([int(q['layer_id']), sorted(q['quebras']['valor']), sorted(q.get('inseridas') or ()),
                   q.get('origem'), bool(q.get('aprovada'))] for q in entradas)
