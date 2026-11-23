# -*- coding: utf-8 -*-
"""Revisao de 23/11/2026 do gancho PreToolUse: os falsos positivos vistos no uso, sem abrir a regra.

  - a palavra solta de um texto livre numa ferramenta mcp__ (a lista de tarefas do app, por exemplo) nao vira caminho so
    por existir uma pasta com esse nome no cwd; o valor inteiro de um campo continua conferido;
  - a leitura pelo terminal acompanha o cd literal feito antes no mesmo comando; o cd que o gancho nao acompanha volta a
    conferencia pelo cwd do evento;
  - as redirecoes que nao gravam arquivo (2>&1, > $null, > /dev/null, > NUL) nao contam como escrita; a redirecao para
    arquivo continua contando.

Tudo sintetico: os jobs e os arquivos sao criados na hora, com bytes quaisquer.
"""
import importlib.util

import pytest

from conftest import RAIZ_PLUGIN

SCRIPT = RAIZ_PLUGIN / 'scripts' / 'gancho_confirmacoes.py'


@pytest.fixture
def g():
    spec = importlib.util.spec_from_file_location('gancho_confirmacoes_falsos_positivos', SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def area(tmp_path):
    """Uma pasta de trabalho com testes/<job> (como a pasta do projeto) e um repositorio sem job ao lado."""
    trabalho = tmp_path / 'trabalho'
    job = trabalho / 'testes' / 'j1'
    (job / 'laudo').mkdir(parents=True)
    (job / 'estado.json').write_text('{}', encoding='utf-8')
    (job / 'laudo' / 'laudo.json').write_bytes(b'sintetico')
    repo = tmp_path / 'repo'
    (repo / 'motor').mkdir(parents=True)
    (repo / 'motor' / 'modulo.py').write_text('x = 1\n', encoding='utf-8')
    return {'trabalho': trabalho, 'job': job, 'repo': repo}


def _comando(g, ferramenta, comando, cwd):
    return g.decidir_com_motivo({'tool_name': ferramenta, 'tool_input': {'command': comando}, 'cwd': str(cwd)})[0]


# ------------------------------------------------------------------ texto livre nas ferramentas mcp__

def test_texto_livre_com_palavra_que_e_pasta_passa(g, area):
    plano = {'items': [{'content': 'Rodar testes das três áreas', 'status': 'pending'},
                       {'content': 'Mostrar o diff', 'status': 'pending'}], 'scope': 'first_task'}
    for ferramenta in ('mcp__ccd_turn__update_plan', 'mcp__ccd_turn__wrap_up', 'mcp__drive__upload_file'):
        assert g.decidir({'tool_name': ferramenta, 'tool_input': plano, 'cwd': str(area['trabalho'])}) is None


@pytest.mark.parametrize('entrada', [
    {'folder': 'testes'},
    {'paths': ['testes']},
    {'text': 'anexo testes/j1'},
    {'text': 'anexo testes/j1/laudo/laudo.json'},
])
def test_valor_inteiro_ou_caminho_com_barra_continua_negado(g, area, entrada):
    assert g.decidir({'tool_name': 'mcp__drive__upload_folder', 'tool_input': entrada,
                      'cwd': str(area['trabalho'])}) == 'deny', entrada


# ------------------------------------------------------------------ cd literal no mesmo comando

@pytest.mark.parametrize('ferramenta', ['Bash', 'PowerShell'])
def test_busca_recursiva_depois_de_cd_para_pasta_sem_job_passa(g, area, ferramenta):
    repo = area['repo'].as_posix()
    for comando in ('cd "%s" && grep -rn "x" .' % repo,
                    'cd "%s"; grep -rn "x" --include=*.py .' % repo,
                    'Set-Location "%s"; Get-ChildItem -Recurse -Filter *.py' % repo,
                    'cd /d "%s" && findstr /s x *.py' % repo):
        assert _comando(g, ferramenta, comando, area['trabalho']) is None, comando


@pytest.mark.parametrize('ferramenta', ['Bash', 'PowerShell'])
def test_cd_para_job_ou_saida_dele_continua_negado(g, area, ferramenta):
    job, repo = area['job'].as_posix(), area['repo'].as_posix()
    for comando in ('cd "%s" && cat laudo/laudo.json' % job,
                    'cd "%s" && cat ../trabalho/testes/j1/laudo/laudo.json' % repo,
                    'cd "%s" && grep -rn x ../trabalho' % repo,
                    'cd "%s" && cd "%s" && grep -rn x .' % (repo, area['trabalho'].as_posix())):
        assert _comando(g, ferramenta, comando, area['repo']) == 'deny', comando


def test_cd_que_o_gancho_nao_acompanha_volta_ao_cwd_do_evento(g, area):
    repo = area['repo'].as_posix()
    for comando in ('cd "%s" && cd $X && grep -rn x .' % repo,
                    'cd "%s" && cd - && grep -rn x .' % repo,
                    'pushd "%s" && popd && grep -rn x .' % repo):
        assert _comando(g, 'Bash', comando, area['trabalho']) == 'deny', comando


def test_busca_recursiva_sem_cd_no_cwd_com_job_continua_negada(g, area):
    assert _comando(g, 'Bash', 'grep -rn x .', area['trabalho']) == 'deny'
    assert _comando(g, 'Bash', 'grep -rn x', area['trabalho']) == 'deny'


# ------------------------------------------------------------------ redirecao que nao grava arquivo

@pytest.mark.parametrize('redirecao', ['2>&1', '2>&1 | Select-Object -Last 25', '>$null', '2> /dev/null', '> NUL',
                                       '*>&1'])
def test_redirecao_sem_arquivo_nao_e_escrita(g, area, redirecao):
    repo = area['repo'].as_posix()
    comando = ('Set-Location "%s"; & python -m pytest testes -q -k "briefing or derivacao or entrega or aprovar" %s'
               % (repo, redirecao))
    assert _comando(g, 'PowerShell', comando, area['trabalho']) is None, comando


@pytest.mark.parametrize('comando', [
    'Set-Location "{job}/briefing"; echo x 2>&1 > novo.json',
    'cd "{job}" && echo x > briefing/novo.json 2>&1',
    'echo x 2>/dev/null > "{job}/briefing/novo.json"',
    'cd "{job}" && echo x >nul.json',
])
def test_redirecao_para_arquivo_continua_escrita(g, area, comando):
    comando = comando.format(job=area['job'].as_posix())
    assert _comando(g, 'Bash', comando, area['trabalho']) == 'deny', comando


def test_escreve_tira_so_a_redirecao_sem_arquivo(g):
    assert g._escreve('pytest -q 2>&1') is None
    assert g._escreve('pytest -q > $null') is None
    assert g._escreve('pytest -q >/dev/null 2>&1') is None
    assert g._escreve('pytest -q > saida.txt 2>&1')
    assert g._escreve('pytest -q >& saida.txt')
    assert g._escreve('pytest -q > nul.txt')
