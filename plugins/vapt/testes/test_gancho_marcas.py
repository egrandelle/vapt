# -*- coding: utf-8 -*-
"""Compat da 0.19.x (nº213): o gancho continua negando ao Claude a escrita e a leitura na pasta marcas.

A pasta marcas e a biblioteca antiga da agencia (perfis de marca, <biblioteca>/marcas/<id>/perfil-marca.json). Desde a
0.19.0 o motor nao a usa mais, mas ela fica no disco do DA, com nome de marca e nome de pasta de job. Por isso o gancho
mantem por uma versao a negativa de escrita (MOTIVO_MARCA) e a de leitura (MOTIVO_LEITURA). As duas saem na 0.20.0,
junto com este arquivo. Os casos vieram de test_marca_perfil.py (M7c, M2), menos os do codigo do perfil e do registro
(o pacote vapt.marca saiu).

Tudo sintetico: a biblioteca e uma pasta temporaria; nenhum arquivo real da agencia e lido.
"""
import importlib.util

import pytest

from conftest import RAIZ_PLUGIN

SCRIPT_GANCHO = RAIZ_PLUGIN / 'scripts' / 'gancho_confirmacoes.py'
ID = 'ab' * 16


def _gancho():
    spec = importlib.util.spec_from_file_location('gancho_confirmacoes_marcas', SCRIPT_GANCHO)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def g():
    return _gancho()


def _decidir(g, ferramenta, entrada, cwd):
    return g.decidir_com_motivo({'tool_name': ferramenta, 'tool_input': entrada, 'cwd': str(cwd)})


# ------------------------------------------------------------------ escrita (compat, sai na 0.20.0)
@pytest.mark.parametrize('ferramenta', ['Write', 'Edit', 'MultiEdit', 'NotebookEdit'])
@pytest.mark.parametrize('rel', ['marcas/%s/perfil-marca.json' % ID, 'marcas/%s/outro.json' % ID,
                                 'marcas/novo.json', 'marcas\\%s\\perfil-marca.json' % ID])
def test_gancho_nega_ao_claude_a_escrita_na_biblioteca_de_marcas(g, tmp_path, ferramenta, rel):
    caminho = str(tmp_path / 'biblioteca') + '/' + rel
    campo = 'notebook_path' if ferramenta == 'NotebookEdit' else 'file_path'
    decisao, motivo = _decidir(g, ferramenta, {campo: caminho, 'content': '{}'}, tmp_path)
    assert decisao == 'deny'
    assert motivo == g.MOTIVO_MARCA


def test_gancho_nega_caminho_relativo_dentro_de_marcas(g, tmp_path):
    cwd = tmp_path / 'biblioteca' / 'marcas' / ID
    cwd.mkdir(parents=True)
    for caminho in ('perfil-marca.json', 'x.json', './y.json'):
        assert _decidir(g, 'Write', {'file_path': caminho, 'content': '{}'}, cwd)[0] == 'deny'


def test_gancho_nega_escrita_por_ligacao_para_marcas(g, tmp_path):
    marcas = tmp_path / 'biblioteca' / 'marcas'
    marcas.mkdir(parents=True)
    atalho = tmp_path / 'atalho'
    try:
        atalho.symlink_to(marcas, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip('sem permissao para criar ligacao simbolica nesta maquina')
    assert _decidir(g, 'Write', {'file_path': str(atalho / 'x.json'), 'content': '{}'}, tmp_path)[0] == 'deny'


COMANDOS_NEGADOS = [
    ('Bash', 'echo {} > biblioteca/marcas/%s/perfil-marca.json' % ID),
    ('Bash', 'echo {} > /c/agencia/biblioteca/marcas/%s/novo.json' % ID),
    ('Bash', 'cp /tmp/x.json "biblioteca/marcas/%s/perfil-marca.json"' % ID),
    ('Bash', 'mv x.json biblioteca/marcas/%s/' % ID),
    ('Bash', 'rm -rf biblioteca/marcas/%s' % ID),
    ('Bash', 'rm biblioteca/marcas/%s/perfil-marca.json' % ID),
    ('Bash', 'mkdir -p biblioteca/marcas/%s' % ID),
    ('Bash', 'touch biblioteca/marcas/novo.json'),
    ('Bash', "python -c \"open('biblioteca/marcas/%s/perfil-marca.json','w').write('{}')\"" % ID),
    ('Bash', "python -c \"import shutil; shutil.rmtree('biblioteca/marcas')\""),
    ('Bash', 'sed -i s/a/b/ biblioteca/marcas/%s/perfil-marca.json' % ID),
    ('Bash', 'echo {} > perfil-marca.json'),
    ('PowerShell', 'Set-Content -Path biblioteca\\marcas\\%s\\perfil-marca.json -Value "{}"' % ID),
    ('PowerShell', 'Remove-Item -Recurse -Force biblioteca\\marcas\\%s' % ID),
    ('PowerShell', 'New-Item -ItemType Directory biblioteca\\marcas\\%s' % ID),
    ('PowerShell', 'del biblioteca\\marcas\\%s\\perfil-marca.json' % ID),
    ('PowerShell', 'Clear-Content biblioteca\\marcas\\%s\\perfil-marca.json' % ID),
    # revisao do M2: o nome marcas sozinho, num argumento de codigo ou depois de um cd
    ('Bash', "python -c \"import os, shutil; shutil.rmtree(os.path.join('C:/agencia/bib', 'marcas'))\""),
    ('Bash', "python -c \"from pathlib import Path; (Path('C:/agencia/bib') / 'marcas' / 'x.json').write_text('1')\""),
    ('Bash', 'cd /c/agencia/bib && rm -rf marcas'),
    ('PowerShell', 'Set-Location C:\\agencia\\bib; Remove-Item -Recurse marcas'),
    # revisao do M2: marcas. (o Windows tira o ponto e o espaco do fim do segmento)
    ('Bash', 'echo x > C:/agencia/bib/marcas./%s/notas.json' % ID),
    ('PowerShell', 'Set-Content -Path C:/agencia/bib/marcas./%s/notas.json -Value x' % ID),
    ('PowerShell', 'Set-Content -Path "C:\\agencia\\bib\\marcas. .\\%s\\notas.json" -Value x' % ID),
    ('Bash', 'rm -rf C:/agencia/bib/marcas..'),
]


@pytest.mark.parametrize('ferramenta,comando', COMANDOS_NEGADOS)
def test_gancho_nega_escrita_em_marcas_pelo_terminal(g, tmp_path, ferramenta, comando):
    decisao, motivo = _decidir(g, ferramenta, {'command': comando}, tmp_path)
    assert decisao == 'deny', comando
    assert motivo == g.MOTIVO_MARCA


COMANDOS_LIVRES = [
    ('Bash', 'git diff -- plugins/vapt/motor/vapt/marca/perfil.py'),
    ('Bash', 'cd plugins/vapt && python -m pytest -p no:cacheprovider testes/test_gancho_marcas.py'),
    ('Bash', 'echo marcas da agencia > notas.txt'),
    ('Bash', 'echo x > docs/marcas.md'),
    ('Bash', 'ls plugins/vapt/motor/vapt/marca'),
    ('PowerShell', 'Get-ChildItem plugins\\vapt\\motor\\schemas\\perfil-marca-1.json'),
    ('Bash', 'python -m pytest -p no:cacheprovider testes/test_gancho_marcas.py -k marcas 2>&1 | tail -5'),
    ('Bash', 'git diff -- docs/marcas.md > /tmp/marcas.diff'),
    ('Bash', 'echo as marcas > notas.txt'),
    # nº213: o codigo do perfil e do registro saiu do motor, e o gancho nao nega mais o nome do pacote antigo
    ('Bash', 'python -c "import vapt.marca.perfil"'),
]


@pytest.mark.parametrize('padrao', ['marc*', 'm?rcas', '*', 'marcas*'])
def test_gancho_nega_apagar_marcas_por_curinga(g, tmp_path, padrao):
    """Revisao do M2: o curinga que cai na biblioteca de marcas (rm -rf <bib>/marc*) e conferido pelo que existe."""
    bib = tmp_path / 'bib'
    (bib / 'marcas' / ID).mkdir(parents=True)
    for comando in ('rm -rf %s/%s' % (bib.as_posix(), padrao), 'rm -rf %s' % padrao):
        decisao, motivo = _decidir(g, 'Bash', {'command': comando}, bib)
        assert decisao == 'deny', comando
        assert motivo == g.MOTIVO_MARCA


def test_gancho_nega_escrita_por_ligacao_para_marcas_pelo_terminal(g, tmp_path):
    marcas = tmp_path / 'biblioteca' / 'marcas'
    marcas.mkdir(parents=True)
    atalho = tmp_path / 'atalho'
    try:
        atalho.symlink_to(marcas, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip('sem permissao para criar ligacao simbolica nesta maquina')
    assert _decidir(g, 'Bash', {'command': 'rm -rf %s' % atalho.as_posix()}, tmp_path)[0] == 'deny'
    assert _decidir(g, 'Bash', {'command': 'echo x > atalho/x.json'}, tmp_path)[0] == 'deny'


@pytest.mark.parametrize('rel', ['marcas./%s/x.json' % ID, 'marcas. /x.json', 'MARCAS../x.json'])
def test_gancho_nega_ferramenta_de_arquivo_em_marcas_com_ponto_no_fim(g, tmp_path, rel):
    """Revisao do M2: marcas. sem a pasta existir ainda (o alvo real nao ajuda)."""
    caminho = (tmp_path / 'nova-biblioteca').as_posix() + '/' + rel
    assert _decidir(g, 'Write', {'file_path': caminho, 'content': '{}'}, tmp_path)[0] == 'deny'


@pytest.mark.parametrize('ferramenta,comando', COMANDOS_LIVRES)
def test_gancho_deixa_o_que_nao_grava_na_pasta_marcas(g, tmp_path, ferramenta, comando):
    assert _decidir(g, ferramenta, {'command': comando}, tmp_path) == (None, None)


@pytest.mark.parametrize('rel', ['plugins/vapt/motor/vapt/marca/perfil.py',
                                 'plugins/vapt/motor/vapt/marca/__init__.py',
                                 'plugins/vapt/motor/schemas/perfil-marca-1.json',
                                 'plugins/vapt/testes/test_gancho_marcas.py', 'docs/marcas.md'])
def test_gancho_deixa_editar_arquivo_fora_da_pasta_marcas(g, tmp_path, rel):
    assert _decidir(g, 'Write', {'file_path': str(tmp_path / rel), 'content': 'x'}, tmp_path) == (None, None)


def test_arquivos_do_da_tem_o_perfil_de_marca(g):
    assert g.ARQUIVOS_DO_DA.search('biblioteca/marcas/%s/perfil-marca.json' % ID)
    assert not g.ARQUIVOS_DO_DA.search('motor/schemas/perfil-marca-1.json')


def test_motivo_da_marca_diz_que_a_biblioteca_e_antiga_e_que_o_da_decide(g):
    texto = g.MOTIVO_MARCA
    assert 'biblioteca antiga' in texto and 'não a usa mais' in texto and 'o DA' in texto
    # nada do registro do padrao da marca, que saiu na 0.19.0
    assert 'padrão da marca' not in texto and 'registra' not in texto
    assert 'terminal' not in texto.lower()
    assert '\u2014' not in texto and '\u2013' not in texto


def test_codigo_do_perfil_saiu_do_gancho(g):
    """nº213: o pacote vapt.marca saiu do motor, e a regra do codigo dele saiu do gancho."""
    assert not hasattr(g, 'CODIGO_DA_MARCA')


# ------------------------------------------------------------------ leitura (compat, sai na 0.20.0)
@pytest.mark.parametrize('ferramenta', ['Read', 'Grep', 'Glob'])
def test_gancho_continua_negando_ao_claude_a_leitura_do_perfil_com_o_nome_do_job(g, tmp_path, ferramenta):
    """O perfil antigo guarda o nome do job, em marcas/**, que o gancho nega ao Claude em toda ferramenta de leitura."""
    alvo = (tmp_path / 'biblioteca' / 'marcas' / ID / 'perfil-marca.json').as_posix()
    entrada = {'Read': {'file_path': alvo}, 'Grep': {'pattern': 'job_nome', 'path': alvo},
               'Glob': {'pattern': '**/*.json', 'path': (tmp_path / 'biblioteca' / 'marcas').as_posix()}}[ferramenta]
    assert _decidir(g, ferramenta, entrada, tmp_path)[0] == 'deny'
    for comando in ('cat %s' % alvo, 'grep job_nome %s' % alvo):
        assert _decidir(g, 'Bash', {'command': comando}, tmp_path)[0] == 'deny', comando
