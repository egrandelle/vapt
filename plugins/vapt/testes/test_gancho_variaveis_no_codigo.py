# -*- coding: utf-8 -*-
"""Revisao de 25/11/2026 do gancho PreToolUse: os falsos positivos do codigo que grava arquivo, sem abrir a regra.

Quando o comando tem codigo que grava arquivo (open(..., 'w'), write_text, mkdir...), o gancho confere toda palavra
do comando como caminho, pelo nome. Antes, qualquer palavra com um caractere de nome montado ($ ` % * ? [) era
negada, em qualquer pasta. Isso pegava:
  - a variavel do shell atribuida com valor literal no inicio do mesmo comando (D="/pasta"; mkdir -p "$D" ...);
  - o colchete e o asterisco do proprio codigo (sys.argv[1], r'([^"]+)', a * b), que nao sao curinga do shell.

Agora:
  - a variavel atribuida uma vez so, com valor literal, no comeco do comando, e trocada pelo valor e conferida como
    caminho de verdade; qualquer outra variavel continua negada;
  - no codigo, o curinga so conta quando pode alcancar um escrito do motor (pacote-m*.json, miniatura?) ou quando a
    pasta e a sugestoes.

Tudo sintetico: o job e os arquivos sao criados na hora, com bytes quaisquer.
"""
import importlib.util

import pytest

from conftest import RAIZ_PLUGIN

SCRIPT = RAIZ_PLUGIN / 'scripts' / 'gancho_confirmacoes.py'


@pytest.fixture
def g():
    spec = importlib.util.spec_from_file_location('gancho_confirmacoes_variaveis', SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def area(tmp_path):
    job = tmp_path / 'trabalho' / 'testes' / 'j1'
    (job / 'sugestoes' / 'miniaturas').mkdir(parents=True)
    (job / 'estado.json').write_text('{}', encoding='utf-8')
    (job / 'sugestoes' / 'pacote-modelo.json').write_bytes(b'sintetico')
    fora = tmp_path / 'fora'
    fora.mkdir()
    return {'j': job.as_posix(), 'f': fora.as_posix(), 'cwd': fora}


def _decisao(g, ferramenta, comando, cwd):
    return g.decidir_com_motivo({'tool_name': ferramenta, 'tool_input': {'command': comando}, 'cwd': str(cwd)})[0]


GRAVA = "python -c \"import sys; open(sys.argv[1], 'w')\""


@pytest.mark.parametrize('comando', [
    # variavel com valor literal no inicio do comando, fora de qualquer job
    'D="{f}/saida"; mkdir -p "$D" && python - "$D" <<\'EOF\'\nimport sys\nopen(sys.argv[1] + "/a.txt", "w")\nEOF',
    'export D={f}/saida && ' + GRAVA + ' "${{D}}/a.txt"',
    'A={f}/a; B=\'{f}/b\'; ' + GRAVA + ' "$A/x.txt" "$B/y.txt"',
    '$D = "{f}/saida"; ' + GRAVA + ' "$D/a.txt"',
    # colchete, asterisco e interrogacao do codigo, sem variavel
    'python - "{f}/rastro.svg" <<\'EOF\'\nimport re, sys\nm = re.search(r\'d="([^"]+)"\', "x")\n'
    'open(sys.argv[1], "w").write(str(3 * 2))\nEOF',
    "python -c \"import sys; p = sys.argv[1]; open(p + '/b.txt', 'w')\" {f}",
])
def test_codigo_que_grava_fora_do_job_passa(g, area, comando):
    cmd = comando.format(**area)
    for ferramenta in ('Bash', 'PowerShell'):
        assert _decisao(g, ferramenta, cmd, area['cwd']) is None, (ferramenta, cmd)


@pytest.mark.parametrize('comando', [
    # variavel que o gancho nao resolve
    GRAVA + ' "$X"',
    GRAVA + ' "$_"',
    GRAVA + ' "$env:ALVO"',
    'read D; ' + GRAVA + ' "$D"',
    'true || D={f}; ' + GRAVA + ' "$D"',
    'D={f}; D=$(cat {f}/p.txt); ' + GRAVA + ' "$D"',
    'D={f}; D+=/x; ' + GRAVA + ' "$D"',
    'D={f}; ' + GRAVA + ' "$D$E"',
    'D="$HOME/x"; ' + GRAVA + ' "$D"',
    # variavel resolvida que cai num escrito do motor, sem o nome do motor no comando
    'D={j}/sugestoes; ' + GRAVA + ' "$D/miniaturas/13.png"',
    'D={j}; ' + GRAVA + ' "${{D}}/sugestoes/miniaturas/13.png"',
    '$D = "{j}/sugestoes"; ' + GRAVA + ' "$D/miniaturas/1.png"',
    # curinga do codigo que alcanca um escrito do motor
    "python -c \"import os, glob; os.chdir(os.environ['J']); p = glob.glob('pacote-m*.json')[0]; open(p, 'w')\"",
    "python -c \"import glob; p = glob.glob('*/miniatura?/1.png')[0]; open(p, 'wb')\"",
])
def test_codigo_que_grava_por_caminho_incerto_e_negado(g, area, comando):
    cmd = comando.format(**area)
    for ferramenta in ('Bash', 'PowerShell'):
        assert _decisao(g, ferramenta, cmd, area['cwd']) == 'deny', (ferramenta, cmd)


def test_colchete_do_codigo_na_pasta_sugestoes_continua_negado(g, area):
    cmd = "python -c \"import sys; open(sys.argv[1], 'w')\" x"
    cwd = area['j'] + '/sugestoes'
    for ferramenta in ('Bash', 'PowerShell'):
        assert _decisao(g, ferramenta, cmd, cwd) == 'deny', ferramenta
