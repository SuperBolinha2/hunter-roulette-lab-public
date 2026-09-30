# Reconstrução dos modos de partida — 2026-09-23

## Referência visual e pedido real

- Uma captura anterior do usuário mostra 2 combatentes: jogador local e
  `Local Bot`.
- A captura histórica fornecida pelo usuário mostra 4 combatentes, loja lateral,
  moedas, bônus central e objetos da partida. O usuário esclareceu que é uma
  partida **online 2v2 de outra pessoa**, usada como referência para os itens;
  não é a partida que ele tentou iniciar no laboratório.
- O trace local mais recente disponível registra `GamerReqPvpC2S` com
  `mode=1`, `subMode=6`. Leitura direta do bundle `fight_dbconfig.ab` confirma
  que o modo 1 se chama **Classic** e declara três combatentes; as submodalidades
  são 4/5/6, com `pvp_init_coin` de 100/1.000/10.000. O modo 11 é
  **Classic: 2v2**, declara quatro combatentes e tem submodalidades 20/21/22.
  O nome foi resolvido em `fight_languagedb.ab` (`LID:997` = “Classic”,
  `LID:2062` = “Classic: 2v2”). A captura histórica do usuário é, portanto,
  referência do modo 11, não evidência do modo 1 testado no laboratório.
- O modo 1 marca `is_team_mode=1` e `camp_gamers_num=0`; o modo 11 declara
  `camp_gamers_num=1`. Esses flags indicam estruturas de equipe distintas, mas
  ainda não provam a ordem dos turnos nem a política de bot. O modo 1/submodo 6
  declara 10.000 moedas iniciais; o snapshot atual do laboratório mostra
  refresh de loja por 300.

## Estado atual do emulador

- Para `mode=1/subMode=6`, `protocol.py:pvp_login_snapshot` já serializa três
  gamers, 10.000 moedas por jogador, quatro cartas de loja e as flags de HUD;
  compra e refresh têm handlers locais. TCP tests verificam esses payloads.
- O Lua da cópia confirma uma notificação de inicialização separada:
  `255/7` (`NotifyPvpGamerAmmo`) define `gameInitInfo`, e
  `RouletteBattleWindow:OnGameStart` carrega as revistas a partir de
  `pvpInfo.gamers`; `255/1` é a notificação subsequente de turno. O laboratório
  agora envia `255/7` entre o `3/14` e o `255/1`. Teste TCP confirma o conteúdo
  de `PvpInfo`; a renderização continua aguardando validação manual. A pilha
  enviada pelo laboratório (2 falsas, 4 reais) é uma escolha local, não uma
  quantidade inicial comprovada pela configuração oficial. O `ammoBank`
  opcional foi omitido para não presumir uma reserva que ainda não foi
  decodificada.
- Ainda há uma divergência importante: `pvp_login_snapshot` força `mode=1`
  mesmo quando o cliente pede outro modo. O modo 11/2v2 não é emulado: quatro
  combatentes, times, loja, rotação, morte e resultado precisam ser coerentes
  antes de se alegar suporte.
- No modo 1/submodo 6, o handler local agora resolve tiros contra os índices
  0/1/2, sincroniza HP e as duas pilhas de munição dos três gamers, agenda os
  turnos dos bots 1 e 2 e devolve o controle no início da rodada seguinte.
  Testes TCP confirmam a ordem dos eventos, o alvo do tiro, a munição, a volta
  ao índice 0 e a acumulação do Cofrinho. Se o jogador morrer, os bots restantes
  continuam a partida até um deles vencer; um teste confirma morte, término e
  ranks 1/2/3. Isso é evidência do protocolo local, não da animação renderizada.
- O trace manual mais recente confirma a compra do Alucinógeno `cfgId=2008` e
  registra duas compras posteriores recusadas (`Typ_Buy`, cabeçalho `error=1`)
  com o slot ainda ocupado. Esse trace explica recusas ao tentar guardar outra
  carta, mas não tem o pacote que gerou o print “Erro de banco de dados”.
  Inspeção do callback `RouletteBattleWindow.OnPlayerSelect` confirmou três
  caminhos: `Typ_Buy_And_Use=1` ao comprar/mirar uma carta de loja, `Typ_Use=2`
  para carta já guardada e `Typ_Buy=3` para guardar. O cliente usa por padrão
  compra-e-uso na loja, exceto se a oferta selecionada já corresponder ao slot.
  O handler antigo atendia 2 e 3, mas não 1; isso é uma causa provável, não
  comprovada sem trace do clique, para o erro genérico do print.
- O servidor local agora atende `Typ_Buy_And_Use=1` do Alucinógeno: valida
  oferta/saldo/alvo, cobra 200, marca a oferta vendida e preserva carta já
  guardada. Tanto ele quanto `Typ_Use=2` embutem `Enum_Shoot` e
  `Enum_Finally_Source` no resultado da carta, conforme a rota Lua
  `UseCard -> StartShootOnce`; o antigo tiro top-level separado foi removido.
  Dois testes TCP validam o estado de protocolo, mas não a animação renderizada.
- A política de IA ainda é uma heurística explícita, não recuperada do servidor
  original: bots priorizam o jogador enquanto ele está vivo e, depois, atacam o
  outro bot. Ordem exata, seleção real de alvo e pose/animação precisam ser
  comparadas com uma partida observada. O modelo de `ammoBank`/recarga também
  permanece incompleto; a cópia não deve ser chamada de jogável por causa dos
  testes de protocolo.
- O cliente usa `PvpInfo.gamers` para criar os personagens e `PvpInfo.cards`
  para construir a loja. As flags `isShowCardSlot` (46),
  `isShowPlayerCoin` (47) e `isShowPvpCoin` (48) controlam partes da HUD.
- O módulo local `_single` do cliente é o prólogo guiado (modo 10); a mesa
  atual é uma sala de rede incompleta, não a execução desse módulo.
- Nenhum trace de pacote de uma partida oficial bem-sucedida foi preservado.
  As tabelas, descritores e handlers Lua são a fonte verificável dos campos;
  valores exatos não documentados continuam hipóteses até teste no cliente.

## Critério para declarar um modo jogável

1. Pedido do menu mantém `mode`, `subMode` e carga de personagem.
2. Snapshot inicial contém a quantidade de combatentes da configuração,
   modelos e posições válidos, moeda, loja e flags correspondentes ao modo.
3. Compra/uso de carta altera moeda, estoque, efeito e HUD pela sequência
   de eventos que o cliente espera.
4. Tiros reais e falsos em cada alvo válido atualizam HP e munição sem
   correções visuais posteriores; os bots animam e o turno volta ao jogador.
5. Vitória/derrota e recompensa conferem com o estado após reconexão.

Os testes de protocolo validam serialização e ordem de mensagens; a renderização
e os controles exigem um teste manual curto do usuário, pois ele pediu que a
interface do computador não seja controlada pelo agente.

## Pendências de reprodução

- **Carta de pré-carga / “bolsinha de dinheiro” (relato do usuário):** a tabela
  marca `33/1033/2033` (Balde de Ferro) e `34/1034/2034` (Cofrinho) como
  `is_only_outside_carried=1`. A base `34` tem biblioteca habilitada, ícone
  `UI_Fight_Itemicon_PiggyBank`, modelo de porco dourado e descrição de acumular
  2 R Coins por turno; as variantes de dificuldade 2/3 são `1034`/`2034` e
  descrevem 20/200 R Coins. `Treasure Bag` `112191/122191/132191` não encaixa:
  não tem a marca de pré-carga nem ícone/modelo nesta tabela. O cliente envia
  a escolha por `GamerReqPvpC2S.cardId` (campo protobuf 8), separado do
  `GamerHero.readyCard` (carta equipada no herói). `PvpGamer.CardSlot` é um
  terceiro objeto, da partida: contém `id` de instância, `cfgId` da configuração
  e `arg_one` para o saldo acumulado do Cofrinho. A base `34` não é desbloqueio
  padrão; a lógica/configuração local aponta herói 2 estrelas, base nível 30 e
  custo externo de 100 R Coins ou token `201014`. A cadeia do cliente é:
  `GamerReqPvpC2S.cardId` (seleção pré-partida) -> `PvpGamer.CardSlot` ->
  `arg_one` (saldo acumulado) -> `Typ_Use` -> evento `Type_Use_Card=8`, com
  crédito de moeda e evento de limpeza do slot. O laboratório agora serializa
  o slot e implementa essa sequência para o Cofrinho, além do efeito específico
  do Alucinógeno `cfgId=2008`; teste local confirma cfg 34 com saldo 2, 4 após
  outro turno, crédito do saldo e slot vazio após uso. Para construir o slot,
  o protótipo usa o `cardId` selecionado tanto
  como `Card.id` quanto como `cfgId`; a equivalência com um ID de instância real
  continua sem confirmação fora do caso de teste. A requisição de partida
  capturada na sessão do erro enviou `mode=1/subMode=6/heroId=0/cardId=3`; a cópia de
  inventário associa `readyCard=3` ao herói 0, e o cfg 3 é `Bala Real +1`, não
  dinheiro. A lógica está validada em loopback, mas ícone/modelo, animação,
  carteira e remoção visuais ainda precisam de teste manual no cliente.
- **Contrato visual de `Card.arg_one`:** o comentário protobuf do cliente o
  define como valor acumulado de moedas; o Lua
  `RouletteGamePlayerNameBoard:SetCardSlot` mostra `_text_card_arg` quando o
  valor é `>= 0` e o oculta quando negativo. Como protobuf entrega `0` para um
  escalar opcional omitido, o servidor estava fazendo cartas comuns aparecerem
  com um “0” amarelo — não era quantidade do item. As imagens/relato do usuário
  confirmam que o zero é espúrio; os componentes gerais de seleção também
  desativam `_Txt_ItemCount`. O servidor envia `arg_one=-1` em cartas comuns e
  mantém o valor real não-negativo somente em itens que o usam, como o saldo do
  Cofrinho. O caso fica coberto por regressão TCP. A instância v14 reiniciada em
  2026-09-23 inclui essa correção, mas o trace da sessão ainda não tem conexão
  de cliente; remoção visual permanece sem confirmação.
- **Turnos dos três combatentes:** a sequência local para o modo 1/submodo 6
  agora agenda os dois bots, sincroniza os três estados, devolve a vez ao
  jogador e permite que os bots terminem a partida após a morte do jogador.
  Testes TCP cobrem esses fluxos, mas ordem e seleção real de alvo ainda são
  hipóteses até um teste visual. A cópia atual atribui `campIdx` distinto a
  cada gamer sintético; isso também é escolha do emulador, não regra confirmada
  do cliente/servidor original. Os submodos 4/5 ainda não foram elevados ao
  mesmo nível de teste.
- **Uso das demais cartas guardadas:** ainda pendente e deve ser reconstruído
  por `skill_typ`. O Cofrinho e o Alucinógeno `cfgId=2008` têm handlers
  específicos testados em protocolo local; isso não generaliza os demais
  efeitos. Ejetar/trocar munição lê `target.uAmmo`, `ammoBank`, `cAmmo` e a
  lista pós-efeito `rAmmo`; o laboratório ainda não modela essa ordem nem o
  banco de munição. Falta confirmar manualmente os dois caminhos do Alucinógeno:
  usar uma carta guardada e comprar/mirar uma carta diretamente da loja.
