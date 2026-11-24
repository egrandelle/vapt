# -*- coding: utf-8 -*-
"""0.15.0: o tipo de arquivo que o DA escolhe na tela quando a folha de spec nao diz (o teste do Duda de 23/11, uma
planilha so com a coluna do formato: os sete formatos chegaram ao Aprovar e o portao recusou todos com
sem_tipos_aceitos_confirmados, com a mensagem "Um dos formatos" e sem o motivo).

Criterios cobertos aqui:
  - a folha que so traz a medida deixa os formatos confirmados na lista "Tipo de arquivo" do passo 1;
  - o ato spec_tipos grava uma acao escolher_tipos por formato, com um Disparo so, e o valor nasce confirmado no
    rascunho e chega a folha confirmada do formato (o que o encoder le);
  - o pedido fora da regra e recusado sem gravar; a escolha seguinte troca a anterior;
  - o formato cuja folha diz o tipo nunca entra na lista;
  - a mensagem do aprovar que parou no portao fica no plural quando sao varios, com o motivo de cada grupo.
"""
import pytest

import test_specs as tsp
import test_tela_lido as tl
from vapt import contratos
from vapt.tela import estado as te
from vapt.tela import tarefas as tt

SO_MEDIDA = 'Formato\n1080x1920\n300x600\n'
COM_TIPO = 'Formato;Tipos de arquivo\n1080x1920;JPG\n'


def _job(tmp_path, texto):
    from vapt.specs import importar
    job = tsp._job(tmp_path, {'portal/folha.csv': texto})
    importar.importar(job)
    tl._laudo_de_mentira(job)
    tl._sem_escolha_do_da(job)
    return job


def _confirmar_tudo(job):
    """Confirma pela tela, em lote, os valores simples da folha (as medidas)."""
    ids = [x['valor_id'] for x in te.specs_pendentes(job) if x['em_lote']]
    if not ids:
        return
    s = tl._servidor(job)
    try:
        assert tl._ato(s, 'spec_valores', {'valor_ids': ids})[:2] == (200, 200)
    finally:
        s.parar()


@pytest.fixture
def job_so_medida(tmp_path):
    job = _job(tmp_path, SO_MEDIDA)
    _confirmar_tudo(job)
    return job


def test_folha_so_com_a_medida_pede_o_tipo_de_cada_formato(job_so_medida):
    lista = te.formatos_sem_tipo(job_so_medida)
    assert sorted(x['nome'] for x in lista) == ['1080x1920', '300x600'], lista
    assert all(x['tipos'] == [] and x['texto'] == '' for x in lista)


def test_escolha_na_tela_grava_e_chega_a_folha_confirmada(job_so_medida):
    from vapt.specs import importar
    lista = te.formatos_sem_tipo(job_so_medida)
    chaves = [x['chave'] for x in lista]
    s = tl._servidor(job_so_medida)
    try:
        c1, c2, p = tl._ato(s, 'spec_tipos', {'formatos': chaves, 'tipos': ['jpg']})
        assert (c1, c2) == (200, 200)
        assert 'podem sair em JPEG' in p['texto'] and '1080x1920' in p['texto'], p
        assert not any(x in p['texto'] + p['titulo'] for x in tl.PROIBIDOS), p
    finally:
        s.parar()
    acoes = [a for a in importar.ler_confirmacoes(job_so_medida)['acoes'] if a['acao'] == 'escolher_tipos']
    assert [a['formato'] for a in acoes] == chaves and all(a['tipos'] == ['jpg'] for a in acoes)
    assert len({a['em'] for a in acoes}) == 1 and all(a['meio'] == 'medicao' for a in acoes)
    depois = te.formatos_sem_tipo(job_so_medida)
    assert all(x['tipos'] == ['jpg'] and x['texto'] == 'JPEG' for x in depois), depois
    doc = contratos.ler(job_so_medida / 'specs' / 'rascunho.json', 'spec/1')
    for f in doc['formatos']:
        if f.get('chave') in chaves:
            v = f['campos']['tipos_aceitos']
            assert v['valor'] == ['image/jpeg'] and v['situacao'] == 'confirmado', v
    from vapt.entrega import codificar
    for c in chaves:
        spec = codificar.spec_confirmada(job_so_medida, c)
        assert spec is not None and spec['campos']['tipos_aceitos']['valor'] == ['image/jpeg'], spec


def test_escolha_seguinte_troca_a_anterior(job_so_medida):
    lista = te.formatos_sem_tipo(job_so_medida)
    um = lista[0]['chave']
    s = tl._servidor(job_so_medida)
    try:
        assert tl._ato(s, 'spec_tipos', {'formatos': [um], 'tipos': ['jpg']})[:2] == (200, 200)
        c1, c2, p = tl._ato(s, 'spec_tipos', {'formatos': [um], 'tipos': ['png', 'jpg']})
        assert (c1, c2) == (200, 200)
        assert 'pode sair em JPEG e PNG' in p['texto'] and 'passa a JPEG' in p['texto'], p
    finally:
        s.parar()
    x = next(x for x in te.formatos_sem_tipo(job_so_medida) if x['chave'] == um)
    assert x['tipos'] == ['jpg', 'png'] and x['texto'] == 'JPEG e PNG'


def test_pedido_fora_da_regra_e_recusado_sem_gravar(job_so_medida):
    from vapt.specs import importar
    um = te.formatos_sem_tipo(job_so_medida)[0]['chave']
    s = tl._servidor(job_so_medida)
    try:
        for dados in ({'formatos': [], 'tipos': ['jpg']}, {'formatos': [um], 'tipos': []},
                      {'formatos': [um], 'tipos': ['gif']}, {'formatos': [um, um], 'tipos': ['jpg']},
                      {'formatos': ['nao-existe'], 'tipos': ['jpg']}, {'formatos': [um], 'tipos': ['jpg', 'jpg']},
                      {'formatos': um, 'tipos': ['jpg']}, {'formatos': [um]}):
            assert tl._ato(s, 'spec_tipos', dados)[0] == 403, dados
    finally:
        s.parar()
    assert not [a for a in importar.ler_confirmacoes(job_so_medida)['acoes'] if a['acao'] == 'escolher_tipos']


def test_folha_que_diz_o_tipo_nao_pede_escolha(tmp_path):
    job = _job(tmp_path, COM_TIPO)
    _confirmar_tudo(job)
    assert te.formatos_sem_tipo(job) == []


def test_mensagem_do_aprovar_no_plural_com_o_motivo():
    um = tt.texto_do_motivo('formato_com_falha', {'com_falha': [
        {'id': 'a', 'nome': '300x250', 'codigos': ['sem_master']}]})
    assert um.startswith('O formato 300x250 ainda não pode ser aprovado.') and um.endswith('Nada mudou no job.'), um
    varios = tt.texto_do_motivo('formato_com_falha', {'com_falha': [
        {'id': x, 'nome': x, 'codigos': ['sem_tipos_aceitos_confirmados']} for x in ('1080x1920', '300x600', '970x250')]})
    assert varios.startswith('A folha de spec não diz o tipo de arquivo dos formatos 1080x1920, 300x600 e 970x250.')
    assert 'Escolha JPEG ou PNG' in varios and 'Um dos' not in varios, varios
    misto = tt.texto_do_motivo('formato_com_falha', {'com_falha': [
        {'id': 'a', 'nome': '300x250', 'codigos': ['sem_tipos_aceitos_confirmados']},
        {'id': 'b', 'nome': '300x150', 'codigos': ['contrato_desatualizado']}]})
    assert 'tipo de arquivo do formato 300x250' in misto and 'O formato 300x150 mudou' in misto, misto
    for texto in [um, varios, misto] + [p for par in tt.TEXTOS_DA_FALHA_DO_APROVAR.values() for p in par]:
        assert not any(x in texto for x in tl.PROIBIDOS), texto
