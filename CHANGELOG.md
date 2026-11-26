# Novidades do Vapt

O que muda em cada versão, em palavras simples. O detalhe técnico de cada mudança está em `docs/m1-interfaces.md` e no histórico do git.

## 0.19.3 (26/11/2026): o clique espera a sua última escolha ser salva

Conserto combinado com o Duda depois da 0.19.2: um clique feito enquanto o Vapt salvava sozinho podia chegar antes da escolha que estava sendo salva.

- Os botões da tela (modo de dados, Confirmar família, copiar layout, trocar arquivo, separar e juntar família e os outros) e os do painel (render e aprovação) agora esperam a gravação que já saiu. O pedido só vai depois dela, e depois da mudança que você fez enquanto ela estava a caminho.
- Se a gravação não deu certo por falha passageira (rede, erro do servidor), o clique tenta salvar mais uma vez antes de seguir. Se de novo não salvar, ou se o Vapt recusou a escolha com um motivo, o clique não vai. Na janela, o selo diz "O clique não foi registrado porque a sua última escolha não foi salva.". No painel, a frase é "O trabalho não foi pedido porque a sua última escolha não foi salva.".
- O render e a aprovação também passam a salvar de novo a escolha que tinha falhado antes de pedir o trabalho. Antes eles seguiam sem ela.

## 0.19.2 (26/11/2026): copiar o layout de outra família

Pedido do Duda em 26/11, antes do item 11: acertar o layout num arquivo e levar para outra família da mesma orientação, sem refazer à mão.

- No cabeçalho da família, ao lado de "Trocar arquivo de edição", entra "Copiar layout de outra família", com um botão por família de onde dá para copiar ("Copiar do 1080x1920"). A janela diz, antes do clique, o que vem junto, quanto o conteúdo muda de tamanho, o que o Vapt ajustou para caber e o que pede ajuste seu. Cancelar não grava nada.
- Vem junto o layout que o arquivo de edição da outra família tem agora: posição e tamanho de cada elemento, os apagados, o texto editado, as quebras de linha e o alinhamento das linhas. Tudo vira edição da família que recebe, e você ajusta no palco como qualquer edição. As edições que ela tinha antes saem, e a família pede a confirmação de novo.
- O conteúdo nunca cresce. Do arquivo maior para o menor, ele diminui o quanto precisa para caber. Do menor para o maior, ele fica do tamanho que tinha, e a cópia sai sempre como "Pede ajuste": a janela sugere aumentar no palco ou fazer o layout no arquivo maior e copiar dele.
- A cópia é uma foto: mexer depois na família de onde veio não muda nada. O cabeçalho, o selo do palco e o resumo embaixo dele dizem de onde veio o layout. Enquanto a cópia vale, a galeria de versões fica travada nessa família.
- Um Desfazer tira a cópia inteira e devolve a família como estava antes, com a versão, as edições, as quebras e os avisos. Se você mexeu depois da cópia, o Desfazer tira primeiro o que você fez, um clique por edição.
- O arquivo de edição com mestre própria (o artboard que você desenhou) fica de fora da cópia, como origem e como destino.
- Na família que o Vapt separa pelo tamanho, o "Briefing salvo" volta a aparecer depois do Salvar e seguir.

## 0.19.1 (25/11/2026): o texto editado guarda as cores do KV

Terceira leva dos pedidos de 25/11.

- O texto que você edita continua com as cores e os estilos do KV. Cada palavra fica com a cor que tinha; a palavra trocada fica com a cor da que estava no lugar; a palavra nova pega a cor da vizinha da esquerda na mesma linha, ou a da direita no começo da linha. Mexer só na quebra de linha de um texto igual ao do KV não muda cor nenhuma.
- A prévia, a medida e a arte final usam a mesma regra, então o que você vê no palco é o que sai no PNG. Isso vale também para a entrelinha de cada linha, o respiro entre parágrafos e o lugar da primeira linha.
- O espaço numa fonte que não está no job não some mais do PNG: ele sai na fonte da palavra ao lado, na mesma linha. Na caixa de parágrafo, esse espaço não para mais o render com "O layout do texto não fechou".
- Texto de um estilo só (mesma fonte, corpo, cor e tracking em tudo) fica igual. Pode pedir um "Salvar e seguir" a mais na família confirmada: o texto com mais de uma cor, fonte ou corpo que você já editou, o texto com um espaço ou uma quebra invisível de outro estilo, e a família cuja quebra junta ou parte a primeira linha do KV. A arte já feita muda no próximo render.
- Como a fonte agora é conferida na palavra de cada fonte, um texto já confirmado com uma letra que só a primeira fonte tinha pode ser recusado. Nesse caso, troque a letra e confirme a família de novo.

## 0.19.0 (25/11/2026): a biblioteca de marca sai

Segunda leva dos pedidos de 25/11: o Vapt fica mais simples.

- A biblioteca de marca sai do Vapt. Somem a pasta da biblioteca da agência na configuração do plugin, a escolha da marca no passo 1, o "Usar o padrão" no Design system e o botão "Guardar o padrão desta marca" no fim do job. A âncora continua sugerida pelo KV.
- Job aberto continua de onde parou. O que veio do padrão da marca fica como escolha sua. Um job que usou "Usar o padrão" pode pedir um "Salvar e seguir" a mais; a aprovação não cai.
- A pasta antiga da biblioteca fica no seu computador, sem uso. O Vapt não a lê nem a apaga; pode apagá-la quando quiser.
- O doctor deixa de conferir a pasta da biblioteca.

## 0.18.0 (25/11/2026): o job começa sem parar

Primeira leva dos pedidos de 25/11: menos perguntas no começo do job.

- As folhas de spec entram como vierem: um ou mais PDF, CSV, HTML salvo, texto ou e-mail soltos, ou pastas, com ou sem subpasta por veiculador. A folha solta vira um veiculador com o nome do arquivo. Duas folhas com o mesmo nome não param o job: a segunda entra com o nome da pasta de onde veio. O Claude não pergunta mais o nome do veiculador, e acrescentar uma folha depois nunca apaga outra.
- Sem caminho dado, o job nasce na pasta `output-vapt`, dentro da pasta de trabalho da sessão, sem pergunta. Continuar, ler a spec e sugerir funções usam a mesma pasta.
- Numa pasta de fontes como a baixada do Google Fonts, o Vapt usa as estáticas e deixa de fora a variable font, a licença e o leia-me, sem perguntar. A variable font sem estática ao lado continua recusada.
- Depois de salvar o briefing, o "Salvar e seguir" fica apagado até você mudar alguma coisa. Antes, qualquer gravação do rascunho, mesmo sem mudança, religava o botão.
- O desenvolvedor do plugin passa a ser Eduardo Grandelle.
- O gancho do plugin deixa de negar alguns comandos que só gravam fora do job (variável do shell com valor fixo e curinga que não alcança arquivo do Vapt).

## 0.17.3 (24/11/2026): marcar todos no tipo e na aprovação

- Em O que eu li, a barra de lote dos Formatos do job ganha três botões com o nome inteiro: "Todos em JPEG", "Todos em PNG" e "Todos em JPEG e PNG". Um clique abre uma janela só para todos os formatos, em vez de um por um. O lote também troca o tipo dos formatos que já tinham um: a janela diz o tipo de antes de cada um e avisa que o formato já renderizado ou aprovado pede render e aprovação de novo. Só vão os formatos que mudam; o botão do tipo que todos já têm fica apagado.
- Em Render e aprovação, "Marcar todos" marca de uma vez os formatos que podem ser aprovados e vira "Desmarcar todos". Ele só marca: o Aprovar continua abrindo a janela com o arquivo final de cada formato.
- "Renderizar os afetados" passa a se chamar "Renderizar todos". O botão continua renderizando só os formatos que pedem render; os já renderizados e os aprovados ficam como estão, e o texto do botão diz isso.

## 0.17.2 (24/11/2026): o cartão do Design system respira

- No Design system, cada função mostra Tamanho no alto, numa grade de duas colunas com as regras em pares (largura e altura, lado menor e maior, área e fixo, cabe e cobre), e Âncora embaixo, com a grade de pontos à esquerda e o texto e o Usar à direita. Antes o texto da Âncora espremia os botões de Tamanho e o nome deles quebrava por cima um do outro. Nada muda no que cada clique grava.

## 0.17.1 (24/11/2026): o desenvolvedor aparece como Trezion.io

- A tela de plugins do Claude passa a mostrar Trezion.io como desenvolvedor do Vapt, com o endereço trezion.io. Nada muda no uso.

## 0.17.0 (24/11/2026): quatro melhorias na tela antes do M8

Pedidos do Duda antes dos testes finais: menos cliques no passo 1, um lugar só para a spec, o tipo e o giro, famílias que não encolhem o texto e uma barra de edição alinhada.

- Em O que eu li, quando a agência ainda não tem biblioteca de marcas, ou a biblioteca ainda não tem marca, a linha "Sem marca" já vem marcada, porque é a única escolha possível. A tela diz isso na própria linha. Nada fica gravado sem o seu clique, e com marcas na biblioteca nada vem marcado, como antes.
- A spec, o tipo de arquivo e o giro de cada formato ficam numa tabela só, "Formatos do job", uma linha por formato, com a coluna Estado dizendo o que falta ("Pronto" ou "Falta: spec, tipo, giro"). A barra de lote fica presa no alto: "Marcar todos" e "Confirmar os marcados", "Todos em JPEG, PNG ou os dois", "Sem giro nos N que faltam". A spec e o tipo continuam pedindo a confirmação na janela; o giro continua salvo no rascunho e vai ao briefing no Salvar e seguir. Os três blocos antigos (cartões de spec, Tipo de arquivo, Formatos e giro) saem.
- "Faltam" passa a avisar do tipo de arquivo que falta, e o Salvar diz quantos formatos ainda precisam dele para aprovar no passo 5.
- Nas Famílias, o formato de mesma proporção mas muito menor que o maior do grupo (menos da metade do lado) ganha família própria, com o próprio layout proposto. Antes ele copiava o layout do maior e o texto ficava minúsculo. O cabeçalho diz o motivo ("O Vapt separou este grupo do 1280x720: copiado, o conteúdo ficaria com 21% do tamanho") e "Juntar de volta" desfaz a separação; o que você junta não é separado de novo.
- A barra abaixo do palco virou uma grade: Desfazer, Escolher vários, Tamanho, Texto e Apagar na primeira linha; "Alinhar pela" com os alinhamentos na segunda, sempre no mesmo eixo; o escolhido e "Como editar" na terceira. A altura é fixa, com e sem escolha, e cabe a 1024 px.

## 0.16.0 (24/11/2026): a âncora vem sugerida pelo KV

No Design system, a âncora ficou mais clara e mais rápida de escolher.

- A âncora é o ponto do elemento que fica preso quando o formato muda. O lugar dele já vem do KV. A tela agora diz isso, e o ponto no KV "mostra onde o elemento fica preso".
- A função sem âncora escolhida mostra uma sugestão tracejada na grade, tirada do lugar do elemento no KV: fica presa a borda mais perto da borda do KV, ou o centro quando as duas margens empatam. É a mesma regra que o Vapt usa ao copiar o layout da família. "Usar" grava a sugestão, e "Usar as N âncoras sugeridas" grava todas de uma vez. Nada fica gravado sem o seu clique, e o padrão da marca vem antes da sugestão.
- A grade continua com 3 por 3. Uma grade 4 por 4 perderia o centro e não deixaria a posição mais precisa, porque a posição já vem do KV.

## 0.15.0 (23/11/2026): as versões deixam a arte do KV livre

Correção do teste com o banner do próprio Vapt. Na troca grande de proporção, a galeria espalhava o conteúdo sobre a arte e tratava as etiquetas soltas como conteúdo. O DA tinha de mover quase tudo. Tudo foi conferido num KV sintético com a geometria do banner e com o layout que o DA deixou em cada formato.

- Quando o KV tem o conteúdo de um lado e a arte do outro, a versão que deixa a arte livre desse lado vem primeiro. O conteúdo fica numa coluna do tamanho da coluna do KV.
- O número, o símbolo e o texto do destaque andam juntos, como a chamada e a linha dela.
- No formato em pé, a chamada para ação fica na base, abaixo da arte.
- As etiquetas soltas sobre a arte e o brilho atrás do texto saem das versões. A frase "O Vapt tirou desta versão" diz o que saiu, com um botão "Devolver" para cada um. O que você devolve volta preso à arte do fundo, e Desfazer o tira de novo.
- A galeria nunca tira texto, imagem, foto nem fundo. O texto que você tira num formato e mantém em outro continua sendo decisão sua.
- Na medida contra o layout do DA, a versão mais parecida ficou mais perto na posição (8% de distância, antes 13%). No tamanho, ficou um pouco mais longe (20%, antes 17%), porque o título do 1080x1920 cresce mais que o do DA. O cartaz de 19/11 não mudou.

Também do mesmo teste: a folha de spec que só traz a medida (uma planilha com a coluna do formato) não diz se o arquivo final sai em JPEG ou PNG. Sem isso, o Aprovar recusava todos os formatos com "Um dos formatos ainda não pode ser aprovado", sem dizer o motivo.

- Em O que eu li, nos valores de spec, o bloco "Tipo de arquivo" lista os formatos cuja folha não diz o tipo. Você escolhe JPEG, PNG ou os dois, para todos de uma vez ou para cada formato. Com os dois, o Vapt entrega PNG e só passa a JPEG quando o PNG fica acima do peso máximo.
- No passo 5, o formato sem tipo de arquivo mostra "Falta o tipo de arquivo" no lugar de "Pode aprovar", e diz onde escolher.
- Quando o Aprovar para, a mensagem diz cada formato, no singular ou no plural, e o motivo de cada um.

## 0.14.1 (23/11/2026): a trava do Claude erra menos

A trava que impede o Claude de fazer o que só o DA faz recusava, por engano, alguns comandos comuns. Ela continua recusando tudo o que recusava de verdade.

- Uma palavra que é também nome de pasta, num texto do Claude, não é mais tratada como pedido de abrir a pasta.
- Uma busca feita depois de entrar em outra pasta é conferida na pasta certa.
- Rodar os testes com a saída de erro junto da saída normal não conta mais como gravar arquivo.

## 0.14.0 (23/11/2026): o desdobra passa a se chamar Vapt

Pedido do Duda: já existe uma solução parecida com o nome antigo, então o produto passa a se chamar Vapt.

- O plugin, o marketplace, as skills e a tela passam a usar o nome Vapt. As skills agora são `/vapt:doctor`, `/vapt:continuar`, `/vapt:novo-job`, `/vapt:ler-spec` e `/vapt:sugerir-funcoes`.
- O topo da tela mostra o logo novo: a palavra "vapt", com o "v" azul e um rastro de velocidade. O "v" fica azul nos dois temas, e o resto da palavra acompanha a cor do texto. Os arquivos do logo ficam em `docs/marca`.
- O endereço do plugin no GitHub muda para `egrandelle/vapt`.
- Quem já tinha o plugin instalado precisa instalar o Vapt de novo. O ambiente do motor é refeito na primeira sessão, e o tema escolhido na tela volta a seguir o Windows até o próximo clique.
- Os jobs feitos com o nome antigo continuam abrindo no Vapt: os arquivos do job não levam o nome do produto.

## 0.13.0 (23/11/2026): a tela ganha o visual novo, com tema claro e escuro

Pedido do Duda: levar para a tela o visual que ele desenhou (pasta design-telas), com superfície clara e escura e um botão para escolher. Tudo foi conferido em arquivos sintéticos.

- A tela inteira segue o visual novo: topo com as abas dos passos, rodapé com a barra de progresso e o "Salvar e seguir" em azul, cartões, chips de função com a cor do grupo e a mesa pontilhada atrás da peça. Os passos 3 e 5, os diálogos e a barra de edição seguem as mesmas cores e formas.
- No canto direito do topo, o sol e a lua trocam entre o tema claro e o escuro.
- Na primeira vez, a tela segue o tema do Windows. Depois do seu clique, ela lembra a escolha nas próximas aberturas, em qualquer job. A escolha fica guardada na pasta do plugin, fora do job, e continua depois de uma atualização.
- A peça não muda com o tema: o papel continua branco e o texto sem cor própria continua escuro nos dois temas.
- A parte da peça que passa do formato aparece numa sangria lilás, com um tracejado só nos lados em que ela passa. No "Ver limpo" a sangria some.
- A tecla Enter aparece ao lado do "Salvar e seguir" e faz o mesmo que o clique. Ela só vale quando o botão está ligado e nada mais está usando o Enter: um campo de escrever, o texto aberto no palco, o editor de texto ou de quebra, uma janela aberta ou a lista do que falta. Quando não vale, a tecla some.
- A frase "Suas escolhas ficam salvas no rascunho" foi do topo para o rodapé, ao lado do passo. Em janelas estreitas ela vira um ponto colorido, e o erro do rascunho continua com a frase inteira.
- A busca de camadas ganhou a lupa. No passo 1, cada modo de dados mostra em barras quanto vai ao Claude.
- No palco, cada etiqueta tem um ponto com a cor do grupo da função. A etiqueta que não cabe no palco fica escondida em vez de sair da vista.
- O palco do passo 4 ganhou um quadro de cantos arredondados. O "Ajustar" calcula a escala pelo tamanho novo.
- As medidas da barra de edição e da galeria continuam as mesmas.

## 0.12.0 (21/11/2026): você escolhe o alinhamento do texto

Pedido do Duda: passar um texto que veio centralizado no KV para alinhado à esquerda ou à direita. Tudo foi conferido em arquivos sintéticos.

- Com um texto escolhido no palco, três botões depois de "Quebrar linha" alinham as linhas dele à esquerda, ao centro ou à direita. O botão do alinhamento de agora fica marcado.
- A caixa do texto fica onde estava. A linha mais longa não anda, e as outras vão para a borda esquerda dela, para o meio ou para a borda direita.
- Vale para o texto do KV e para o texto que você editou. O alinhamento vai para todos os arquivos da família, como as outras edições, e o render desenha o texto assim.
- Desfazer volta ao alinhamento de antes. Os cliques seguidos no alinhamento do mesmo texto contam como uma edição só.
- Escolher de novo o alinhamento do KV volta o texto ao KV, sem edição nenhuma.
- Quando os parágrafos do texto têm alinhamentos diferentes no PSD, nenhum botão fica marcado. Qualquer escolha leva todas as linhas ao mesmo alinhamento, e a linha mais longa continua no lugar.
- O texto numa caixa de texto do Photoshop, o texto que vai como imagem e o elemento com mais de um texto ficam com o alinhamento do KV por enquanto. O botão diz por quê.
- Os seis botões de "Alinhar pela" ficam só com o desenho numa faixa estreita de largura da barra de edição: quando eles cabiam com os nomes ao lado dos botões do elemento antes desta versão e agora não cabem mais. É o caso da tela de 2048 px com os arquivos da família ao lado. Assim a barra continua com duas linhas e o palco não perde altura. O nome de cada botão aparece ao parar o mouse sobre ele. Nas janelas comuns (1280, 1366, 1600 e 1920 px, por exemplo), os nomes ficam como antes.
- Na janela de 1024 px, os botões do elemento ficam um pouco mais juntos, e o Apagar continua na mesma linha deles.
- As famílias que você confirmou antes continuam confirmadas.

## 0.11.0 (19/11/2026): as versões chegam mais perto do que você faria

Correção do teste com o cartaz vertical de 19/11. As versões de cada formato saíam com os blocos do KV só escalados, pequenos demais, e a pessoa da foto cobria o texto. O DA tinha de montar cada formato do zero. Tudo foi conferido num KV sintético com a geometria do cartaz e com o layout que o DA deixou em cada formato.

- A galeria foi refeita. A foto da pessoa fica do lado em que estava no KV, presa à base e na altura toda. O conteúdo vai para o lado livre e cresce para ocupar o espaço. No KV deitado, os formatos em pé e quadrados também têm uma versão com a foto de fundo (veja abaixo).
- O título pode crescer mais que os outros textos, até 1,6 vez o crescimento deles.
- A lista de itens iguais vira uma fileira nos formatos largos e volta a ser coluna nos estreitos. Os itens de uma coluna começam no mesmo ponto.
- O contato fica no alto, e os logos e a marca ficam embaixo, como no KV.
- As versões sem falha vêm primeiro. A versão com falha só entra para completar três versões.
- Nenhum bloco fica abaixo do mínimo de 50% da escala prevista. Quando o conteúdo não cabe acima desse mínimo, a versão diz que não fecha, em vez de mostrar texto pequeno demais.
- O ajuste final que encolhe demais um bloco agora aparece como falha da versão.
- No cartaz de teste, a versão mais parecida com a do DA chega a 9% de distância na posição (antes 14%) e a 16% no tamanho (antes 44%). Ela vem em primeiro em 4 dos 5 formatos, sem nenhuma falha.
- O aviso de fundo pouco visível não aparece mais quando o fundo cobre o KV inteiro ou é só cor.
- Na frase das versões, a pessoa recortada passa a ser "a foto".
- No KV deitado com a foto de uma pessoa, nos formatos em pé e quadrados, a foto pode ficar de fundo. Nessa versão, o conteúdo fica por cima da foto, e isso não conta como falha. A frase diz "a foto fica de fundo, atrás do conteúdo". A versão com a foto ao lado do conteúdo continua em primeiro na galeria, e a versão com a foto de fundo entra como mais uma opção (no teste, em segundo). Se a foto estiver acima de um texto na ordem das camadas do PSD, a versão pede ajuste e diz isso. As versões com a foto numa faixa, os formatos deitados e o KV em pé continuam como antes. No 160x600 do teste, o título ainda não cabe na largura, e a versão mostra essa falha.
- A família confirmada continua confirmada quando você reabre o job depois de "Salvar e seguir". Antes, a quebra de linha aprovada trocava a lista das versões e a confirmação caía. Se o layout mudar de verdade, a confirmação ainda cai no "Salvar e seguir".

## 0.10.0 (18/11/2026): você edita um arquivo, e a família segue

Correção do job real com a família vertical de 1080x1920 e 300x600. Você editou só o 1080x1920, e o 300x600 saiu com a assinatura sobre o azul. Agora cada família tem um arquivo de edição, e os outros arquivos seguem o layout que você aprovou nele. Tudo foi conferido em arquivos sintéticos.

- Cada família tem um arquivo de edição: o maior dela, em pé, como o público vê. No palco, você edita só ele. O topo diz, por exemplo, "Você edita o 1080x1920. Os outros 3 arquivos seguem este layout."
- As fichas "Arquivo desta família" saíram. Os outros arquivos aparecem em "Como fica em cada arquivo", ao lado do palco, grandes o bastante para ler, cada um com um selo em palavras: "Igual ao seu", "Ajustado pelo Vapt", com o que mudou, ou "Pede ajuste", com o valor.
- O clique num arquivo da faixa abre "Ver grande", só para ver. Lá, "Mostrar o seu por cima" desenha o arquivo de edição por cima, e o contorno marca o que o Vapt ajustou.
- Os outros arquivos copiam o seu layout com uma escala só. Cada bloco fica preso à borda ou ao centro em que você o deixou, e o que estava no branco continua no branco. No caso do job real, a assinatura do 300x600 fica no branco, sem ajuste.
- Quando o layout não cabe igual num arquivo, o Vapt faz o menor ajuste que aparece menos e diz qual foi. O que ele ajusta nunca fica calado.
- A forma que sangra cresce nos outros arquivos só o necessário para continuar chegando à borda, até 1,5 vez o tamanho copiado. Quando precisa crescer mais, o arquivo fica com "Pede ajuste" e diz quanto ela cresceu e a que bordas ela chega. Isso vale também para a forma que você juntou a um texto num grupo. O fundo cresce o quanto precisar.
- "Confirmar família" abre "Conferir os N arquivos". Primeiro vêm os que pedem ajuste, depois os ajustados, e os iguais ficam recolhidos. Há um contador e um filtro.
- O arquivo girado aparece em pé, com a etiqueta "gira 90° na entrega". O giro acontece só na entrega.
- Na família sem edição, "Trocar arquivo de edição" escolhe outro arquivo para editar, com um clique e a confirmação na janela.
- Quando um arquivo pede ajuste e você prefere cuidar dele à parte, "Separar em família própria" o tira da família. Ele passa a ser editado nele mesmo. "Juntar de volta" o devolve.
- As famílias que você confirmou antes desta versão pedem a confirmação de novo, uma vez, também as sem edição. A tela diz por quê, acima do palco.
- A confirmação guarda o layout de cada arquivo como a janela mostrou. Se algum layout mudar antes do "Salvar e seguir", a tela pede que você confira e confirme de novo.

## 0.9.6 (17/11/2026): a sua aprovação vale

Correção do teste da 0.9.5 num job real. A família confirmada com "Pede ajuste" deixava os formatos "Sem layout" no passo 5, a caixa do texto editado continuava com a altura antiga, e cada valor de spec pedia dois cliques. Tudo foi conferido em arquivos sintéticos.

- Quando você confirma uma família, o layout dela vale, mesmo com "Pede ajuste". O Vapt guarda o aviso e segue. Os formatos chegam ao passo 5 com "Layout pronto".
- No passo 5, o formato que você aprovou com aviso mostra uma linha discreta "Aviso aceito por você", com o que o Vapt achou.
- Antes de confirmar, a família continua mostrando "Pede ajuste" e os motivos. Depois de confirmar, a marca vira "Aprovado por você", sem a cor de erro.
- O texto que você editou e que passa da borda de um arquivo não trava mais "Confirmar família". A tela avisa, e o render corta o texto na borda, como o palco mostra.
- O Vapt só para quando não dá para fazer a peça: falta uma letra na fonte, falta um arquivo ou há um erro do motor. Nesses casos, a tela diz o motivo.
- Se o "Salvar e seguir" grava o briefing e não consegue montar os layouts, a tela diz isso, e o botão volta ligado. O aviso fica no rodapé até os layouts serem montados. No passo 5, o formato sem layout de uma família confirmada mostra o motivo real.
- O job salvo na 0.9.5 com formatos "Sem layout": abra a tela e clique em "Salvar e seguir". O Vapt monta os layouts de novo.
- A família com texto editado que você confirmou antes da 0.9.6 pede a confirmação de novo, uma vez, porque a caixa do texto mudou. As outras continuam confirmadas.
- O arquivo que o Vapt não consegue montar, como o da quebra de linha sem medida, continua com "Pede ajuste" na família. A tela diz que ele fica sem layout, mesmo com a família confirmada.
- Depois de confirmar, a frase do aviso no palco deixa o vermelho de erro. No passo 5, o aviso aceito diz o que acontece, por exemplo "Uma parte do fundo fica fora do formato, na base."
- Quando o texto editado perde linhas, a caixa tracejada diminui junto. Ela tem a altura das linhas que você escreveu. Assim o Vapt não acusa mais sobreposição que não existe.
- Alinhar e mudar o tamanho de um texto editado usam a caixa das linhas que você escreveu.
- No passo 1, os valores de spec de cada formato ficam num cartão com caixas de marcar. "Marcar todos" marca tudo, e "Confirmar os marcados" confirma de uma vez, com uma janela que lista cada valor. Nada vem marcado.
- O valor em que as folhas discordam e o formato com duas medidas continuam pedindo a sua escolha, um por um.
- O cartão de cada formato mostra a medida, sem o código interno da folha. A janela de confirmar diz quantos valores entram, e a lista mostra cada um.
- No giro, o botão "Sem giro nos formatos que faltam" escolhe o giro de todos de uma vez. O formato em que a folha fala de giro fica para você escolher. Nada vem marcado.
- Na entrega, a peça que você aprovou com aviso e que passa da área segura da folha vai para os aprovados, com o aviso no relatório. Peso, tamanho e tipo do arquivo continuam reprovando.

## 0.9.5 (17/11/2026): o que você não mexeu fica parado

Correção do teste do KV A na 0.9.4, no passo das Famílias. No 970x250, aumentar só o texto de apoio fazia o título e a barra do fundo subirem juntos, até o título sair do formato. Tudo foi conferido em arquivos sintéticos.

- Quando você mexe num elemento, só ele anda. Os outros ficam no mesmo lugar e com o mesmo tamanho, em todos os arquivos da família.
- Isso vale para mover, mudar o tamanho, alinhar, editar o texto e apagar.
- O Vapt não reorganiza mais a peça depois da sua edição. Antes, ele refazia o encaixe e mudava elementos que você não tinha tocado.
- Se a sua edição deixa um elemento sobre outro, fora do formato, fora da área segura ou mais perto do que o KV pede, a tela avisa. Você decide o que fazer.
- A prévia e o "Salvar e seguir" continuam dando o mesmo resultado.
- O Tamanho agora vai até 1000%. O limite de 400% chegava cedo no título do 970x250. O teto de 1000% fica só para proteger de um número digitado errado.
- Se você alinha dois elementos juntos e depois mexe em um deles, o outro fica onde o alinhamento o deixou.
- Ir a 1000% e voltar a 100% pelo Tamanho devolve o elemento ao lugar de antes, mesmo quando ele passou das bordas no caminho.
- O palco fica com o mesmo zoom enquanto você edita. Os avisos que aparecem em cima dele não encolhem mais o desenho. Ajustar, o zoom e a troca de formato refazem o enquadramento.
- Mudar o tamanho pelo canto do elemento mostra a porcentagem final, como o campo Tamanho.
- Cada aviso aparece uma vez só na faixa de avisos e nas marcas dos arquivos.

## 0.9.4 (17/11/2026): as linhas do texto editado são as do DA

Correção do teste do KV A na 0.9.3, no passo das Famílias. O texto editado quebrava sozinho na largura da caixa, o "Aprovar quebra" não mudava nada, e o render do 970x250 parava com a mensagem genérica. Também ficou mais rápido escrever no texto. Tudo foi conferido em arquivos sintéticos.

- Clique duas vezes num texto do palco para escrever nele ali mesmo. O campo aparece sobre o texto, com a mesma fonte, o mesmo tamanho e a mesma cor. Enter quebra a linha. Ctrl+Enter, Tab ou um clique fora aplica, e Esc desiste.
- Pelo teclado, F2 abre o texto do elemento. Enter também abre, quando o texto já está escolhido.
- O campo cresce com a linha mais longa e nunca quebra sozinho. Se a fonte do job não tem uma letra, o aviso aparece e o texto que você escreveu continua no campo.
- Abrir o texto e sair sem mudar nada não grava edição. O botão "Editar texto" da barra continua abrindo o editor embaixo do palco.
- Um tremor da mão no clique não move mais o elemento. O arraste começa depois de 3 pixels na tela.

- O texto que você edita nunca quebra sozinho. As linhas são as que você escreve, com Enter no texto ou com o controle de quebra de linha.
- O texto fica com o mesmo corpo de letra. A caixa cresce até a linha mais longa, em volta do ponto de alinhamento do texto do KV.
- A proposta de quebra do Vapt e o botão "Aprovar quebra" saíram do texto editado. Um rascunho antigo com essa proposta numa família ainda não confirmada volta às linhas do texto e não trava a confirmação. A família já confirmada fica como você a confirmou.
- Quando o texto editado passa da borda de um arquivo da família, a miniatura dele fica marcada, uma faixa diz qual é o arquivo e leva até ele, e "Confirmar família" espera o ajuste.
- Antes do render, o Vapt confere o texto editado de novo. Se ele passa da borda de um formato, o render não começa, e a tela diz o formato e o que fazer. Nada muda no job.
- Se o render parar porque um texto passou da borda, a tela diz isso com o nome do formato. A mensagem genérica de problema fica só para o que o Vapt não sabe explicar.
- Uma família confirmada na 0.9.3 com texto editado pede "Salvar e seguir" de novo antes do render, para o Vapt medir o texto com as linhas novas. A tela diz isso com o nome do formato.
- O texto editado que encosta na borda do formato, dentro da folga que a tela aceita, também passa no render.
- A moldura do texto editado cresce com ele. O duplo clique na parte nova do texto abre a escrita.
- Na escrita no palco, a prévia fica na mesma altura do render, também com uma primeira linha vazia.
- No formato exibido pequeno, o palco aproxima antes de abrir a escrita, para as letras ficarem legíveis. A etiqueta de outro elemento não impede o duplo clique no texto.
- A faixa da borda diz "Ver o arquivo", como o resto do passo Famílias.

## 0.9.3 (16/11/2026): as famílias aparecem depois do Design system

Correção do teste do KV A na 0.9.2: com as funções e o Design system feitos, as famílias não apareciam, o "Salvar e seguir" não dava retorno e o passo das Famílias mandava de volta para Funções. Tudo foi conferido em arquivos sintéticos.

- A tela agora pergunta ao Vapt pelas famílias também depois de cada escolha do Design system. Antes, ela só perguntava depois de uma escolha de função, e quem fazia o Design system por último via a espera velha.
- Quando o Vapt ainda não consegue montar as famílias, o passo das Famílias diz o motivo concreto, com o nome das camadas, marca na lista o item que falta e leva ao lugar certo. A lista nunca fica toda verde junto com a espera.
- Todo motivo que o Vapt pode dar ganhou uma frase para o DA, com o passo onde ele se resolve.
- No KV A, o motivo mais provável é o retângulo de fundo e o grafismo, que se sobrepõem e andam juntos num bloco: as funções deles precisam da mesma regra de escala. O Design system mostra esse aviso no alto, e a contagem "Faltam" conta esse item.
- O "Salvar e seguir" fica desligado enquanto as famílias não aparecem, com o motivo ao lado. A frase "Tudo confirmado. Pode salvar." só aparece com todas as famílias confirmadas.
- Quando o Vapt recusa um clique ou uma escolha não é salva, o aviso aparece no rodapé, ao lado do "Salvar e seguir", com o motivo que o Vapt deu. O botão mostra "Conferindo" enquanto espera a resposta. A frase "Tente de novo" saiu dos casos em que tentar de novo não resolve.
- Quando uma escolha não é salva, o rodapé e o passo das Famílias dizem isso, com o motivo. Antes, a tela podia ficar dizendo "Salvando" sem salvar nada.
- O aviso de um clique recusado sai quando você muda alguma coisa ou troca de passo. O motivo aparece uma vez só, no rodapé, e o foco do teclado volta ao botão.
- A frase curta ao lado do "Salvar e seguir" diz o que fazer, como "Dê a mesma regra de tamanho às funções do bloco". As listas de camadas usam "e" no fim, e uma camada sem nome aparece como "sem nome".
- O botão "Ir para o Design system" mostra o aviso do motivo junto do cartão que resolve, também nas telas menores.
- A regra de bloco que veio de um briefing salvo fora da tela não se muda na tela. Quando ela trava as famílias, a tela diz para pedir ajuda ao Claude, em vez de mandar a um passo sem esse controle.

## 0.9.2 (16/11/2026): formatos digitados na tela

Para o job que chega sem folha de spec. Sem folha, o job não tinha formato nenhum, e as famílias nunca apareciam. Tudo foi conferido em arquivos sintéticos.

- No passo 1 da tela, em "Valores de spec", o bloco "Formatos sem folha de spec" recebe a largura e a altura de cada formato em pixels. Dá para colar vários de uma vez, separados por vírgula, como 1080x1920, 300x600.
- A tela avisa na hora o que não entendeu, o formato repetido e o tamanho fora do que o Vapt aceita.
- Uma janela de confirmação mostra os formatos, e eles entram já confirmados, com quem escreveu e quando. O Claude não escreve formatos.
- Os formatos aparecem em "Formatos e giro" e, com as funções e o Design system completos, nas famílias.

A tela também ficou mais clara para quem desenha:

- O Design system passou a ser o passo 3 e as Famílias o passo 4, porque as famílias dependem dele.
- Sem família para mostrar, o passo das Famílias explica por quê, mostra o que falta (formatos, funções, tamanho e âncora) e tem o botão para o lugar certo.
- No topo do passo 1, uma faixa diz o que trava o job e o que falta para as famílias, com o botão "Resolver aqui" ou "Escrever os formatos". Cada bloqueio também ganhou o botão que leva ao lugar onde ele se resolve.
- O motivo do "Salvar e seguir" desligado fica em destaque ao lado do botão, com "Ir até lá".
- As abas dos passos mostram o que já está feito e o que falta. A lista do que falta vem separada por passo.
- Na lista de camadas do passo 2 há busca pelo nome e o filtro "Só as sem função".
- Os nomes no palco ficaram curtos (função e camada); a regra aparece ao parar o mouse em cima e na linha do elemento escolhido. Sem elemento escolhido, a barra de edição mostra só Desfazer e Escolher vários.
- Texto maior nos passos de leitura, cinza mais escuro para ler melhor e botões desligados sem a transparência.
- Cada formato digitado tem o botão "Remover".
- Se a folha de spec trouxer o mesmo formato, vale a folha depois que a medida dela for confirmada, e a tela avisa. Antes disso, o formato que você escreveu continua no job. Se a folha sair, o formato digitado volta.
- Dá para escrever o milhar com ponto, como 1.080 x 1.920.
- Quando as funções e o Design system estão completos e as famílias ainda não aparecem, o passo das Famílias diz o motivo, com o nome das camadas, e o botão leva ao lugar certo.
- O aviso de que uma escolha não foi salva aparece em frase também nas telas menores.
- Na janela de confirmação, o botão que confirma fica em destaque, e o de remover fica na cor de aviso.
- Os botões desligados do passo 5 dizem por que estão desligados quando o mouse para em cima.
- No palco, o nome que ficaria em cima de outro sai da vista. O nome do elemento escolhido sempre aparece.
- A camada com transparência aparece sem o quadrado preto em volta.
- O formato que você escreveu aparece pela medida em "Formatos e giro", sem o código interno.
- Um formato escrito no modo de teste nunca chega ao render, à entrega nem ao padrão da marca.
- Um formato digitado só tem a medida: peso, área segura e faixas ficam sem regra do veículo.

## 0.9.1 (16/11/2026): texto como imagem

Para o KV que tem texto vivo no PSD, mas cuja fonte a agência nunca recebeu em arquivo. Tudo foi conferido em arquivos sintéticos.

- No passo 1 da tela, em "Fontes do job", cada fonte que falta ganha o botão "Não tenho esta fonte: usar o texto como imagem". A janela de confirmação mostra as camadas atingidas e o efeito, e a decisão fica gravada com quem decidiu e quando. O Claude não faz essa declaração.
- Com a decisão, o job deixa de parar nessa fonte. As camadas dela vão pelos pixels do próprio PSD e escalam como imagem, pela regra da função que o DA escolheu. Ampliar acima do tamanho do KV avisa, como em qualquer imagem.
- No palco, essas camadas aparecem com o selo "Texto como imagem": o texto não se edita e a linha não quebra ali.
- O botão também aparece quando o arquivo da fonte chegou, mas não confere com o PSD (outra versão da fonte, por exemplo).
- Se chegar depois o arquivo da fonte que confere, o texto volta a ser texto vivo, e a tela avisa. Um arquivo que não confere deixa a decisão valendo. O botão "Desfazer" (ou "Tirar a declaração") desfaz a decisão com um clique.
- Para o que vai ao Claude nada muda: a camada continua sendo texto e nunca vira miniatura no modo (a).
- O manifesto e o relatório da entrega registram a camada como texto como imagem por decisão do DA, sem recusar a entrega.

## 0.9.0 (13/11/2026): marca, sugestão de função e skills (M7c)

Com esta versão, o Claude pode sugerir a função de cada camada quando o diretor de arte pede, o Vapt guarda o padrão de cada marca da agência e as skills levam o DA da criação do job até a tela sem nenhum comando. Tudo foi conferido em arquivos sintéticos; a rodada com os KVs reais fica para quando o Duda decidir. Antes de usar, veja também "O que ainda não funciona nesta versão", no fim desta entrada.

### Sugestão de função, só quando o DA pede

- O job nasce sem modo de dados. O DA escolhe o modo no passo 1 da tela, e até a escolha nada do conteúdo do job vai ao Claude.
- Depois de gravar o modo (a) ou (b), a tela mostra a frase para escrever ao Claude: "quero sugestões". O Claude prepara as sugestões, o Vapt confere cada uma e a tela as mostra ao lado de cada função, com a alternativa e a fonte.
- A sugestão nunca vira função sozinha: só o clique do DA em "Usar" põe a função no briefing. Com a tela aberta, as sugestões novas aparecem com o aviso "Chegaram as sugestões do Claude", e o que o DA já fez não muda.
- No modo (a), vão ao Claude só as imagens de camadas sem texto. Ficam de fora o grupo, o objeto inteligente com texto dentro ou linkado, a camada escondida e a camada recortada sobre um texto; na dúvida, a camada fica de fora. A tela avisa que letra desenhada em pixel pode ir na imagem.
- Quando o modo muda, ou quando a agência baixa o teto, o Vapt refaz o que o Claude pode ler, e as sugestões do modo antigo saem da tela.
- O Vapt mede quantas sugestões batem com a função que o DA confirmou e o tempo do passo "Funções", com e sem sugestão na tela. Esses números ficam no job, fora do briefing, e o DA não vê.

### O padrão da marca

- No passo 1, o DA pode dizer de que marca é o job: uma das marcas da agência, "Marca nova" ou "Sem marca". Nenhuma vem marcada, e a escolha é opcional.
- Quando todos os formatos do job estão aprovados, a tela mostra o botão "Guardar o padrão desta marca". A janela mostra o que vai entrar no padrão (as regras de escala e as âncoras de cada função e o nome das faces) e pede a confirmação na própria janela.
- Cada registro vira uma versão nova do padrão. As versões anteriores ficam guardadas e nunca são apagadas, e registrar de novo o mesmo job sem mudança não cria versão.
- No job seguinte da mesma marca, o Design system mostra o padrão ao lado de cada função, com a versão e o job de origem. Nada fica preenchido: o DA usa o padrão com um clique em "Usar o padrão" ou escolhe outro valor.
- O padrão guarda só o nome das faces. Arquivo de fonte, edições de palco, versão da galeria e lockup de governo ficam no job.

### Biblioteca da agência

- A pasta onde o Vapt guarda o padrão de cada marca é escolhida pelo DA em `/plugin`, no plugin vapt, opção Configure, com cliques. Ela é opcional: sem ela, o job roda normal, sem marca, e a tela diz onde configurar.
- A pasta fica fora do plugin, por isso desinstalar ou atualizar o Vapt não apaga o padrão das marcas. A conferência da instalação diz se a pasta existe, se dá para gravar nela e se ela está num lugar que o Vapt apagaria.

### O Claude lê menos do job

- Dentro da pasta de um job, o Claude lê só o que o modo de dados permite: os pacotes preparados pelo Vapt, as imagens permitidas do modo (a) e as sugestões. O PSD, as fontes, o laudo, o briefing, as imagens geradas e a biblioteca da agência ficam fechados para ele, por qualquer ferramenta.
- O Claude nunca grava o padrão de uma marca nem o que o Vapt preparou para ele.

### Skills

- `novo-job` foi reescrita para quem não usa terminal: pede os caminhos completos do PSD e das fontes, com a dica de "Copiar como caminho", roda a preparação e abre a tela.
- Skills novas: `continuar` (retoma um job do ponto em que parou), `sugerir-funcoes` (as sugestões de função, só quando o DA pede, só nos modos a e b) e `ler-spec` (ajuda a ler uma folha de especificação nova; a confirmação de cada valor continua na tela).
- Nenhuma skill pede ao DA o modo, o teto, um valor ou uma regra no chat, e nenhuma manda o DA a um terminal. As recusas dos atos do DA e os textos das fases do job, que mandavam rodar comando, passaram a mandar o DA à tela.

### Para quem já usava a 0.8.0

- Configure a biblioteca da agência em `/plugin` se quiser guardar o padrão das marcas. Sem ela, nada muda no job.
- A versão do Vapt entra na impressão de cada formato. Um formato aprovado na 0.8.0 pode pedir render e aprovação de novo, uma vez, quando o job for salvo nesta versão.
- Ao abrir um job que já existia, o Vapt lê de novo as specs dele, uma vez, porque a biblioteca de specs passou a levar a versão nova. As confirmações de spec que o DA já fez entram nessa leitura.
- O pacote que o Claude lê é refeito no formato novo na primeira vez que o job é aberto.

### O que ainda não funciona nesta versão

- Entregar e trocar os parâmetros de entrega ainda não têm botão na tela. A entrega chega no próximo marco.
- Restaurar uma versão antiga do briefing ainda não existe; o histórico aparece só para leitura.
- O padrão de uma marca só aparece depois que a primeira campanha dela é registrada.
- Nos modos (a) e (b), os textos das camadas e, no (a), as imagens permitidas ficam na transcrição local da conversa até o DA apagar. A skill lembra disso ao fim de cada sugestão e ao fechar o job.

## 0.8.0 (12/11/2026): a tela corrige, renderiza e aprova (M7b)

Com esta versão, o diretor de arte corrige o briefing depois da aprovação, gera as imagens e aprova cada formato pela tela, sem comando. A entrega continua fora da tela: o botão de entregar fica para uma versão seguinte. Antes de usar, veja também "O que ainda não funciona nesta versão", no fim desta entrada.

### Corrigir sem perder o que já estava pronto

- Quando o DA muda alguma coisa depois de aprovar, o Vapt refaz só os formatos que a mudança atinge. Os outros continuam com a mesma imagem e com a aprovação que já tinham.
- Cada formato mostra, em frase simples, o que mudou desde a última versão. As versões do briefing ficam guardadas em ordem e aparecem para consulta.
- O texto que o DA editou no palco sai na imagem final com as mesmas linhas da prévia. Uma letra que a fonte do job não tem trava o render com uma mensagem clara.
- A família guarda o mesmo nome quando o DA muda os formatos dela, e a tela avisa quando uma família ganhou ou perdeu formatos e precisa ser confirmada de novo.

### Gerar as imagens e aprovar na própria tela

- O botão "Renderizar os afetados" gera as imagens de todos os formatos que pedem render, com uma confirmação só. O render nunca começa sozinho.
- A tela continua respondendo enquanto o render roda, mostra o andamento de cada formato e deixa cancelar entre uma etapa e outra.
- A aprovação é por formato: o DA marca os formatos, vê o arquivo final de cada um na janela e aprova. Quando o formato vai girado na entrega, a janela pergunta para que lado, com um desenho.
- Um painel mostra a situação de cada formato, o motivo e o histórico de versões.

### Editar a mestre da família

- O DA quebra a linha de um texto direto no palco, com as miniaturas dos outros formatos da família ao lado. A quebra vale para a família inteira.
- A quebra que o próprio DA faz já vale como aprovada. A quebra que o Vapt propõe pede um clique em "Aprovar quebra" antes de confirmar a família.
- O tempo para desenhar a mestre de cada família é medido e guardado junto do job, fora do briefing.

### Mais jeitos de mexer no palco

- Escolher vários elementos de uma vez (Shift e clique, o botão "Escolher vários" ou um retângulo) e mover ou mudar o tamanho do grupo inteiro.
- Alinhar pela margem ou pela área segura da folha, nas bordas e no centro.
- Dar o tamanho em porcentagem, de 25% a 400%.
- Passar da borda deixou de ser erro: o DA pode deixar um elemento sangrar. Um elemento que sai inteiro da peça ganha um aviso próprio.
- Quando o DA fura de propósito a distância mínima ou o tamanho mínimo, a peça mostra "Decisão do DA" e não cobra ajuste.
- O botão "Nomes" esconde as etiquetas dos elementos para facilitar o clique num palco cheio. O elemento escolhido continua com o nome.
- A ajuda "Como editar" lista todos os gestos do palco.

### A prévia mostra o que vai ser gravado

- A prévia da tela e o "Salvar e seguir" seguem a mesma regra. Um formato que o "Salvar e seguir" devolveria aparece na prévia com "Pede ajuste" antes da confirmação.
- O alinhamento automático move só o elemento que o DA acabou de mexer. Nenhum outro sai do lugar, e o elemento só encaixa numa linha que fica à frente do movimento: a seta anda 1 px nos dois sentidos.
- Por causa dessas duas correções, a família confirmada numa versão anterior pede uma nova confirmação, uma vez.

### Mais rápido

- O navegador que mede as quebras de linha fica aberto enquanto a tela estiver aberta. A prévia de uma quebra nova caiu de cerca de 1,1 s para cerca de 0,1 s.

### Para quem já usava a 0.7.0

- A aprovação feita na versão anterior pede uma nova aprovação do formato, uma vez.
- Toda família confirmada na 0.7.0 pede uma nova confirmação, uma vez, com ou sem edição.
- Ao abrir um job que já existia, o Vapt lê de novo as specs dele, uma vez, porque a biblioteca de specs passou a levar a versão nova. As confirmações de spec que o DA já fez entram nessa leitura.

### O que ainda não funciona nesta versão

- Trocar os parâmetros de entrega e entregar ainda pedem comando.
