# -*- coding: utf-8 -*-
"""Preferencias da tela do DA (0.13.0): o ultimo tema que o DA escolheu, claro ou escuro, lembrado entre sessoes.

O arquivo fica na pasta de dados do plugin (vapt.chromium.pasta_dados_do_plugin), fora de todo job: a janela da
tela usa um perfil novo a cada abertura e o apaga ao fechar, por isso o localStorage nao guarda nada. O arquivo so
tem o esquema e o tema (preferencias-tela/1): nada do job, do cliente, do usuario nem da maquina.

  - arquivo(): o caminho do arquivo, ou None fora do ambiente do plugin (testes e desenvolvimento). Sem ele, a tela
    segue o tema do Windows e o clique no tema vale so enquanto a janela esta aberta;
  - ler(caminho): 'claro', 'escuro' ou None. Arquivo que falta, ilegivel ou fora do esquema da None, sem erro para o
    DA: a tela segue o tema do Windows;
  - gravar(caminho, tema): grava atomico, conferido pelo esquema (contratos.gravar).

O servidor da tela (vapt.tela.servidor) le o arquivo na abertura e escreve data-theme no <html> da pagina servida
(ATRIBUTO, nunca o texto do arquivo); o POST /preferencias da pagina grava a escolha nova.
"""
from vapt import contratos

ARQUIVO = 'preferencias-tela.json'
ESQUEMA = 'preferencias-tela/1'
TEMAS = ('claro', 'escuro')
# o valor do atributo data-theme da pagina (e do corpo do POST /preferencias) para cada tema guardado
ATRIBUTO = {'claro': 'light', 'escuro': 'dark'}
TEMA_DO_ATRIBUTO = {v: k for k, v in ATRIBUTO.items()}


def arquivo():
    """O caminho do arquivo de preferencias na pasta de dados do plugin, ou None fora do ambiente do plugin."""
    from vapt.chromium import pasta_dados_do_plugin
    pasta = pasta_dados_do_plugin()
    return None if pasta is None else pasta / ARQUIVO


def ler(caminho):
    """O tema guardado ('claro' ou 'escuro'), ou None (sem caminho, sem arquivo, ilegivel ou fora do esquema)."""
    if caminho is None:
        return None
    try:
        dados = contratos.ler(caminho, ESQUEMA)
    except (contratos.ErroContrato, OSError, ValueError):
        return None
    tema = dados.get('tema')
    return tema if tema in TEMAS else None


def gravar(caminho, tema):
    """Grava o tema (atomico, conferido pelo esquema). ValueError para tema fora de TEMAS; OSError do disco sobe."""
    if tema not in TEMAS:
        raise ValueError('tema fora do padrao')
    contratos.gravar(caminho, {'esquema': ESQUEMA, 'tema': tema}, ESQUEMA)
