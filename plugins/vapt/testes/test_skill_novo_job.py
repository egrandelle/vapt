# -*- coding: utf-8 -*-
"""M7c, K1: o texto da skill novo-job e das referencias dela (revisao do K1).

1. O o_que_fazer do motor fala com quem roda o motor e cita comandos (job proxima, spec confirmar, render, aprovar,
   entregar, parametros-entrega). A skill nunca manda repetir esse texto ao DA ao pe da letra: o Claude traduz para o
   clique na tela e nunca passa comando ao DA (no 159).
2. A biblioteca da agencia saiu na 0.19.0 (nº213): a SKILL.md e as referencias nao citam o marcador
   ${user_config.biblioteca_agencia} nem --biblioteca.
3. A sinopse de job criar no README e na doc do M2 mostra --modo-dados como opcional.
"""
import re
from pathlib import Path

RAIZ_PLUGIN = Path(__file__).resolve().parents[1]
RAIZ_REPO = RAIZ_PLUGIN.parents[1]
SKILL = RAIZ_PLUGIN / 'skills' / 'novo-job'


def _textos():
    arquivos = [SKILL / 'SKILL.md'] + sorted((SKILL / 'references').glob('*.md'))
    return {a.name: a.read_text(encoding='utf-8') for a in arquivos}


def test_skill_nunca_manda_repetir_o_o_que_fazer_ao_da():
    proibidos = [re.compile(r'repit\w*[^.\n]{0,40}o_que_fazer', re.I),
                 re.compile(r'repita-o', re.I),
                 re.compile(r'diga ao DA o `o_que_fazer`', re.I)]
    achados = [(nome, m.group(0)) for nome, texto in _textos().items() for p in proibidos for m in p.finditer(texto)]
    assert achados == []


def test_skill_diz_que_o_comando_do_o_que_fazer_nunca_vai_ao_da():
    textos = _textos()
    regras = textos['regras-do-modelo.md']
    # a regra: o o_que_fazer fala com quem roda o motor; comando dele nunca chega ao DA; ato do DA vira clique na tela
    assert re.search(r'o_que_fazer[^\n]*nunca[^\n]*comando|comando[^\n]*o_que_fazer[^\n]*nunca', regras)
    assert 'clique' in regras
    # no concluido, o texto final do motor cita render, aprovacao e entrega: a skill manda abrir a tela, sem repetir
    fluxo = textos['fluxo.md']
    assert re.search(r'concluido[^\n]*', fluxo)
    assert 'entrega' in fluxo and 'próximo marco' in fluxo


def test_skill_e_referencias_sem_biblioteca_da_agencia():
    """0.19.0 (nº213): a biblioteca da agencia saiu. Nenhum texto cita o marcador nem --biblioteca, e o comando da
    tela segue sem a opcao."""
    for nome, texto in _textos().items():
        assert '${user_config.biblioteca_agencia}' not in texto, nome
        assert '--biblioteca' not in texto, nome
        assert 'BIBLIOTECA' not in texto, nome
    texto = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
    linhas_tela = [l for l in texto.splitlines() if 'tela abrir' in l and '-m vapt' in l]
    assert linhas_tela


def test_sinopse_de_job_criar_mostra_modo_dados_opcional():
    obrigatorio = re.compile(r'job criar[^\n]*(?<!\[)--modo-dados \{a,b,c\}')
    readme = (RAIZ_REPO / 'README.md').read_text(encoding='utf-8')
    assert not obrigatorio.search(readme)
    # a sinopse da entrada de fontes (M2) na doc de interfaces; a das linhas 200 a 208 e do K5
    doc = (RAIZ_REPO / 'docs' / 'm1-interfaces.md').read_text(encoding='utf-8')
    linhas = [l for l in doc.splitlines() if 'job criar' in l and '--fontes <arquivo ou pasta>' in l]
    assert linhas and not any(obrigatorio.search(l) for l in linhas)


def test_sem_folha_a_skill_diz_que_o_da_escreve_os_formatos_na_tela():
    """0.9.2: o job sem folha de spec fica sem formato ate o DA escrever a largura e a altura de cada formato na tela,
    no passo 1. A skill diz isso na criacao e na explicacao da tela, sem mandar o DA ao terminal."""
    texto = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
    linha = next(l for l in texto.splitlines() if 'Sem folhas agora' in l)
    assert 'na tela' in linha and 'Valores de spec' in linha and 'formatos' in linha
    passo_1 = next(l for l in texto.splitlines() if 'Passo 1, O que eu li no arquivo' in l)
    assert 'sem folha' in passo_1 and 'largura e a altura de cada formato' in passo_1
