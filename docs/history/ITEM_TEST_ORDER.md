# Roteiro manual — itens da loja PVP

Este roteiro acompanha efeitos e registros `cfgId` encontrados na cópia
laboratorial. Alguns registros compartilham nome localizado, mas têm parâmetros
diferentes; “variante” é um rótulo interno nosso, não um nome exibido no jogo.
A loja do laboratório pode sortear esses registros, mas isso não comprova que
sejam ofertas separadas na loja original do modo de três participantes. A loja
tem quatro posições; **Atualizar** troca as ofertas e cobra 300 R Coins.

Comece uma partida nova em `local-pvp:1:6`. Teste uma carta por vez e espere a
animação e a jogada terminarem antes da próxima. Se uma carta não aparecer,
use Atualizar e anote o cfgId e o resultado. Em cada teste, observe alvo/setas,
ícone, HP/Frenzy, munição, dinheiro, animação, turno e slot da carta.

## Confirmados pelo jogador

- **2001 Ejector** — funciona 100%.
- **2003 Real Bullet+1** — funciona 100%.
- **2004 Blank Bullet+1** — funciona 100%.
- **2007 Spare Magazine** — funciona em você e no bot; animação suave. A
  composição das munições varia e fica para a futura etapa de armas.
- **2008 Hallucinogen** — jogador confirmou funcionamento. O log registra uso
  em si (`target=0`) e em bot; tiro real em si reduziu HP de 4 para 3.
- **2025 Hallucinogen (cfg de nome repetido)** — jogador confirmou que funcionou. O trace
  registra tiro real no Bot 1, recarga imediata para 1 real + 3 falsas e HP
  4→3. O seletor local agora também permite mirar em si, apesar do cfg original
  ser oponente-only.
- **2009 Arms Voucher** — converte uma bala do carregador em bala melhorada;
  o pente não cresce e o disparo causa 2 de dano.
- **2011 Wet Cigarettes** — dado/cura funcionam; com HP em 0 não deve curar.
- **2016 Burst Mode** — jogador marcou como certo após reteste. O log confirma
  consumo em tiro próprio (`double_shot=False`) e rajada ao mirar no bot
  (`double_shot=True`).
- **2015 Maintenance Kit** — efeito, ícone e dano funcionam. A trava local de
  reaplicação foi coberta por trace/teste; resta, se conveniente, confirmar o
  aviso visual ao tentar comprar de novo enquanto ativo.
- **2018 Violation Ticket** — dado 2: bot 10.000→9.800; jogador paga 400 e
  recebe 200, terminando também em 9.800; animações ocorreram.
- **2020 Surprise Box** — duas aberturas confirmadas. Os itens recebidos são
  testes separados; a caixa em si abriu e entregou cartas.
- **2031 Energy Pump** — jogador confirmou funcionamento. O trace registra
  uso em si e em bot; a habilidade recebeu uma carga sem alterar HP ou munição.
- **2032 Rocket Launcher** — jogador confirmou que funcionou na partida após a
  correção de sorteio, consumo de munição e dano proporcional.
- **2033 Bucket** — jogador confirma que o item funciona; a animação e a
  aparição parecem corretas. O log mais recente não contém uma partida, então
  essa aprovação visual vem da observação do jogador, não do trace.
- **2029 Tranquilizer** — jogador confirmou que o efeito funcionou. No log de
  29/09, no turno 6, o Bot 2 escolheu cfg 2029 contra o Bot 1; isso confirma a
  decisão/alvo da IA, enquanto a confirmação do efeito vem do teste visual do
  jogador. Uso próprio, valores ímpares e animação/HUD ainda não foram isolados.
- **2030 Permission Ban** — jogador confirmou que funcionou bem. O log de
  29/09 registra compra/uso em alvo (`skill=10009`, `target=1`); a confirmação
  do bloqueio vem do reteste do jogador.
- **2022 Purchase Ban** — jogador confirmou três aplicações no Bot 1, sem
  compra dele nos turnos afetados. O log mostra duas compras/uso da loja e um
  uso de carta guardada; a política dos bots omite ofertas compráveis enquanto
  o bloqueio está ativo.
- **2021 Wanted** — funcionamento, contagem individual por participante e mira
  aprovados pelo jogador. A duração segue N turnos por aplicação (N = vivos
  quando aplicado); observar apenas possíveis regressões.

## Loja atual — efeito dos itens únicos testado

Não há outro efeito de item comprável único pendente para o modo local 1/6.
Ainda ficam para etapas específicas a composição do Spare Magazine/animação de
recarga (armas) e a confirmação visual do aviso ao tentar reaplicar o
Maintenance Kit. Os cfgs repetidos abaixo não contam como produtos separados
até confirmar que aparecem assim no jogo.

## Registros de nome repetido — disponibilidade da loja não confirmada

- **Wet Cigarettes:** cfg 2011, 2024 e 2027 compartilham nome localizado e
  família de efeito/dado; 2024/2027 são self-only, enquanto 2011 tem alvo amplo.
  São linhas de configuração diferentes, não prova de três itens separados na
  loja clássica 1/6.
- **Ejector:** cfg 2001 e 2026 têm nome/efeito-base iguais no catálogo extraído;
  não há evidência de ambos como ofertas da loja testada.
- **Hallucinogen:** cfg 2008 e 2025 compartilham nome, mas diferem na
  configuração de alvo. 2025 já foi exercitado na cópia; “variante” não é nome
  visível no jogo.
- **Surprise Box:** cfg 2020, 2028, 2036 e 2037 têm nome localizado semelhante,
  mas cfg/skill distintos. Diferenças de prêmio e disponibilidade no modo ainda
  não foram estabelecidas.

## Etapa seguinte de itens — equipamentos antes da partida (adiada)

- **2034 Piggy Bank** — o jogador confirmou que é equipado antes de iniciar a
  partida, não comprado na loja. Agora que os efeitos compráveis únicos foram
  testados, um próximo bloco será começar uma partida com ele equipado. O
  protocolo local já cobre acumular e coletar moedas; validar no
  cliente a seleção pré-partida, o contador e a coleta. A bolsa dourada
  congelada vista em todos os participantes permanece uma questão visual
  separada, sem vínculo comprovado com esse item.

## Planejado depois de fechar os itens — etapa de armas

- **Ativo por escolha do jogador em 29/09:** pesquisa dos traits automáticos
  de armas e das habilidades básicas/melhoradas dos personagens. Ver
  `WEAPON_SKILL_RESEARCH.md`. Pesquisa concluída nesta etapa; implementação
  dos traits e upgrades ainda pendente. Piggy Bank pré-partida fica adiado.

- Investigar a capacidade e as combinações de munição de cada arma, inclusive
  as opções aleatórias ao recarregar e o comportamento do Spare Magazine. A
  composição atual do carregador é observação do laboratório, não regra
  original confirmada.
- Revisar a animação da arma ao recarregar: o jogador confirmou que o efeito
  funciona, mas percebeu a animação um pouco errada. Manter como melhoria
  pendente da etapa de armas.
- Ajustar economia por modo: quando os modos 10×, 100× e 1000× forem
  implementados, multiplicar de forma consistente preços da loja e recompensa
  do Wanted (4 R-Chips no modo 1×). É ajuste de balanceamento/escala, não bug
  do efeito básico; por enquanto manter o modo atual em 1×.

Para cada teste, responda `ok`, `falhou` ou `parcial`, seguido de uma frase
curta. Se surgir “Erro de banco de dados”, anote cfgId e pare sem repetir a
compra/uso, para preservar a primeira falha no log.
