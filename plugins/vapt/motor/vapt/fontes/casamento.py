# -*- coding: utf-8 -*-
"""Funcoes puras da conferencia de fontes: faces do job, par com o nome PostScript do PSD e cobertura de glifos.

Casar so pelo nome PostScript falha nos dois sentidos (pesquisa/corpus-testes.md, 4, item 8): um arquivo pode
ter mais de um registro do name ID 6 (Mac e Windows diferentes), e outro grava no name ID 6 uma abreviacao, com
o nome do PSD so no id unico (name ID 3) ou na familia e estilo tipograficos (16 e 17). Por isso o par e
procurado em ordem: todos os registros do name ID 6, o id unico, e a familia com o estilo. O par que nao vem do
name ID 6 sai com aviso; o Chromium e a largura por linha confirmam a face depois.

Nada aqui le arquivo: recebe as leituras do filho (leitura-fonte/1) e o laudo/1.
"""
import re
import unicodedata

# metodos de casamento, do mais forte ao mais fraco
METODOS = ('nome_ps', 'id_unico', 'familia_estilo')
# peso CSS e usWeightClass pelos nomes de estilo da especificacao OpenType (tabela OS/2, usWeightClass)
PESOS_POR_ESTILO = (  # numero-neutro: valores de usWeightClass e font-weight da especificacao OpenType e CSS
    ('extralight', 200), ('ultralight', 200), ('semibold', 600), ('demibold', 600),  # numero-neutro: idem
    ('extrabold', 800), ('ultrabold', 800), ('xbold', 800), ('xbd', 800), ('hairline', 100),  # numero-neutro: idem
    ('thin', 100), ('light', 300), ('regular', 400), ('normal', 400), ('book', 400), ('roman', 400),  # numero-neutro: idem
    ('medium', 500), ('bold', 700), ('heavy', 900), ('black', 900),  # numero-neutro: idem
)
CONTROLES_DE_QUEBRA = ('\r', '\n', '\x03')


def normalizar(nome):
    """Minusculas, sem acento e so letras e digitos: compara nomes gravados de jeitos diferentes."""
    t = ''.join(c for c in unicodedata.normalize('NFKD', str(nome or '')) if not unicodedata.combining(c))
    return re.sub(r'[^0-9a-z]', '', t.casefold())


PESO_POR_CHAVE = dict(PESOS_POR_ESTILO)


def _tokens(texto):
    """Palavras do nome, separadas por hifen, espaco, sublinhado e troca de caixa (ExtraBold = extra, bold)."""
    t = ''.join(c for c in unicodedata.normalize('NFKD', str(texto or '')) if not unicodedata.combining(c))
    return [p.casefold() for p in re.findall(r'[A-Z]+(?![a-z])|[A-Z]?[a-z]+|[0-9]+', t)]


def _peso_dos_tokens(tokens):
    """Peso do maior casamento entre palavras vizinhas e a tabela (extra + bold = extrabold, 800)."""
    melhor = None
    for i in range(len(tokens)):
        for j in range(i + 1, len(tokens) + 1):
            chave = ''.join(tokens[i:j])
            if chave in PESO_POR_CHAVE and (melhor is None or len(chave) > len(melhor)):
                melhor = chave
    return PESO_POR_CHAVE[melhor] if melhor else None


def peso_do_estilo(*nomes):
    """Peso pelo nome do estilo (ExtraBold = 800); None se nenhum nome traz peso conhecido.

    Compara palavras inteiras, nunca pedaco de palavra (Thinker-Bold e 700, nao 100). Num nome com hifen, como o
    nome PostScript, vale so o sufixo de estilo depois do ultimo hifen; sem hifen, o nome todo (nome de estilo)."""
    for nome in nomes:
        texto = str(nome or '')
        parte = texto.rsplit('-', 1)[1] if '-' in texto else texto
        peso = _peso_dos_tokens(_tokens(parte))
        if peso is not None:
            return peso
    return None


# ------------------------------------------------------------------ faces
def montar_faces(leituras):
    """Faces do job a partir de [(sha256, leitura-fonte/1)], com id estavel f01, f02... na ordem de (sha256, indice).

    Cada face leva os nomes, as metricas, a cobertura em faixas e os dados para servir ao Chromium."""
    itens = []
    for sha, leitura in leituras:
        for face in leitura.get('faces') or []:
            itens.append((sha, face['indice'], leitura, face))
    itens.sort(key=lambda x: (x[0], x[1]))
    faces = []
    for k, (sha, indice, leitura, face) in enumerate(itens, 1):
        nomes = face['nomes']
        os2 = face.get('os2') or {}
        familia = nomes.get('familia_tipografica') or nomes.get('familia')
        estilo = nomes.get('estilo_tipografico') or nomes.get('estilo')
        peso_estilo = peso_do_estilo(estilo, *(nomes.get('ps') or []))
        upm = face['head']['unidades_por_em']
        asc, desc, gap = os2.get('s_typo_ascender'), os2.get('s_typo_descender'), os2.get('s_typo_line_gap')
        if asc is None:
            asc, desc, gap = face['hhea']['ascender'], face['hhea']['descender'], face['hhea']['line_gap']
        faces.append({
            'id': 'f%02d' % k,
            'sha256': sha,
            'indice': indice,
            'formato': leitura['formato'],
            'nome_ps': (nomes.get('ps') or [None])[-1] if len(nomes.get('ps') or []) else None,
            'nomes_ps': list(nomes.get('ps') or []),
            'id_unico': list(nomes.get('id_unico') or []),
            'familia': familia,
            'estilo': estilo,
            'versao_name': nomes.get('versao'),
            'us_weight_class': os2.get('us_weight_class'),
            'peso_estilo': peso_estilo,
            'peso_declarado': peso_estilo or os2.get('us_weight_class') or None,
            'metricas': {'unidades_por_em': upm, 'ascender': asc, 'descender': desc,
                         'cap_height': os2.get('s_cap_height'), 'x_height': os2.get('s_x_height'),
                         'entrelinha_tipo': (asc - desc + (gap or 0)) if asc is not None and desc is not None else None},
            'cmap': face['cmap'],
            'colecao': face.get('colecao'),
        })
    return faces


def chaves_da_face(face):
    """{metodo: conjunto de nomes normalizados} pelos quais a face casa com um nome PostScript do PSD."""
    ps = {normalizar(n) for n in face['nomes_ps']}
    # id unico: o ultimo pedaco depois do ';' costuma ser o nome PostScript (1.005;Fundicao;Familia-Estilo)
    ids = set()
    for t in face['id_unico']:
        for pedaco in t.split(';'):
            n = normalizar(pedaco)
            if n:
                ids.add(n)
    fam = {normalizar('%s%s' % (face['familia'] or '', face['estilo'] or ''))} if face['familia'] else set()
    return {'nome_ps': ps, 'id_unico': ids - ps, 'familia_estilo': fam - ps}


def casar(fonte_ps, faces):
    """Par de um nome PostScript do PSD: (face ou None, metodo ou None, n_candidatos_do_mesmo_metodo)."""
    alvo = normalizar(fonte_ps)
    if not alvo:
        return None, None, 0
    for metodo in METODOS:
        achadas = [f for f in faces if alvo in chaves_da_face(f)[metodo]]
        if achadas:
            return achadas[0], metodo, len(achadas)
    return None, None, 0


def familia_do_ps(fonte_ps):
    """Familia que o nome PostScript sugere: o pedaco antes do primeiro hifen, normalizado."""
    return normalizar(str(fonte_ps or '').split('-')[0])


def faces_da_mesma_familia(fonte_ps, faces):
    fam = familia_do_ps(fonte_ps)
    if not fam:
        return []
    out = []
    for f in faces:
        nomes = {normalizar(f['familia'])} | {familia_do_ps(p) for p in f['nomes_ps']}
        if fam in nomes:
            out.append(f)
    return out


# ------------------------------------------------------------------ cobertura
def cobre(face, codigo):
    for ini, fim in face['cmap']:
        if ini <= codigo <= fim:
            return True
        if ini > codigo:
            return False
    return False


def tem_tinta(ch):
    return not (ch.isspace() or unicodedata.category(ch) in ('Cc', 'Cf', 'Zs', 'Zl', 'Zp'))


def vizinho_com_face(runs, i, tem_face):
    """Decisao 214: o run em que se desenha o run i sem tinta cuja fonte nao tem face no job (o espaco de outra fonte),
    para o espaco nao sumir do PNG nem da medida. Como na regra R3, o estilo de um run sem tinta nao vale fora do seu
    papel: o vizinho e o run com face e tinta na mesma linha, o da esquerda ou, no comeco da linha, o da direita.
    Sem nenhum na linha, o run com face e tinta mais perto antes, sem nenhum o depois; sem nenhum com tinta, o run com
    texto e face mais perto. O palco, a medida e o render usam o mesmo. None quando o run i tem face ou tinta, ou
    quando nenhum outro tem face."""
    r = runs[i]
    if tem_face(r) or any(tem_tinta(ch) for ch in r.get('texto') or ''):
        return None

    def com_tinta(s):
        return any(tem_tinta(ch) for ch in s)

    def quebra(s, ultima):
        ks = [k for k, ch in enumerate(s) if ch in CONTROLES_DE_QUEBRA]
        return (ks[-1] if ultima else ks[0]) if ks else None

    # a quebra dentro do proprio run i conta: '\r ' abre a linha de baixo (so a direita), ' \r' fecha a de cima (so a
    # esquerda); o run so de quebra fecha a linha de cima
    si = r.get('texto') or ''
    qi, qf = quebra(si, False), quebra(si, True)
    pela_esquerda = qi is None or bool(si[:qi]) or not si[qf + 1:]
    pela_direita = qi is None or bool(si[qf + 1:])
    for k in range(i - 1, -1, -1) if pela_esquerda else ():  # a esquerda na mesma linha: o trecho depois da ultima quebra do run
        s = runs[k].get('texto') or ''
        q = quebra(s, True)
        if tem_face(runs[k]) and com_tinta(s if q is None else s[q + 1:]):
            return runs[k]
        if q is not None:
            break
    for k in range(i + 1, len(runs)) if pela_direita else ():  # a direita na mesma linha: o trecho antes da primeira quebra do run
        s = runs[k].get('texto') or ''
        q = quebra(s, False)
        if tem_face(runs[k]) and com_tinta(s if q is None else s[:q]):
            return runs[k]
        if q is not None:
            break
    antes, depois = runs[i - 1::-1] if i else [], runs[i + 1:]
    for serve in (lambda x: tem_face(x) and com_tinta(x.get('texto') or ''),
                  lambda x: bool(x.get('texto')) and tem_face(x)):
        v = next((x for x in antes if serve(x)), None) or next((x for x in depois if serve(x)), None)
        if v is not None:
            return v
    return None


def texto_do_trecho(run):
    """O texto como o Chromium vai desenhar: caixa alta aplicada quando o trecho pede."""
    t = run.get('texto') or ''
    if run.get('font_caps') in ('ALL_CAPS', 'SMALL_CAPS'):
        t = t.upper()
    return t


def glifos_faltando(face, textos):
    """Quantos caracteres diferentes com tinta dos textos a face nao cobre (so a contagem, nunca quais)."""
    faltam = set()
    for t in textos:
        for ch in t:
            if tem_tinta(ch) and not cobre(face, ord(ch)):
                faltam.add(ch)
    return len(faltam)


def amostra_da_face(face, maximo):
    """Alguns caracteres com tinta que a face cobre (do proprio cmap), para a sonda da face no Chromium."""
    out = []
    for ini, fim in face['cmap']:
        for c in range(ini, fim + 1):
            ch = chr(c)
            if tem_tinta(ch) and unicodedata.category(ch)[0] in 'LNP':
                out.append(ch)
                if len(out) >= maximo:
                    return ''.join(out)
    return ''.join(out)
