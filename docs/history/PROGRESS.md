# Progress

## 2026-09-30 — Venom Stinger: primeira integração no trio com loja, v48

- cfg35 skill10037, Toxin visual10066 (cadeia pai10061/10067). Acerto
  normal danoso aplica uma instância no alvo, inclusive self; falso/bloqueio
  completo não aplica. Hook de jogador/bots no trio, envelope addBuffs do tiro.
- Próxima cura positiva reduzida1 e remove buff via evento nativo typ10.
  Cigarro comprado/guardado, skill da coelha, conversão Frenzy→HP do urso
  e cura de bots integrados. Dado falho/cura0 não consome. Segunda cura normal.
- Duração por dono reutiliza relógio de início de turno: mantém no primeiro
  turno seguinte, expira no segundo; reapplication renova sem empilhar.
  Baseado no esclarecimento do jogador; fonte nativa diz removido ao ativar/1round.
- 231 testes passaram, oito novos de condição, isolamento, limites de cura,
  consumo, duração/reaplicação e envelopes HUD. Teste manual ainda pendente.
- Escopo atual de aplicação/expiração: trio com loja que está sendo testado.
  Duelo sem loja, ataques especiais e skills de cura ainda não implementadas
  devem passar pelo mesmo hook em etapa posterior; não declarar cobertura total.

## 2026-09-30 — Lady J validada; Venom Stinger em análise

- Jogador confirmou Lady J após preparar condição. Log235727 às00:07:28
  registra falsa em si deixando1 real/0 falsas; às00:07:34 Collect Bounty
  amount800, balance10100. Compatível com1/1 antes do tiro:400 dobrado800.
- Próxima arma cfg35 skill10037→buff10061. Texto nativo Toxin reduz próxima
  recuperaçãoHP em1, removido após ativar ou1 round. Cadeia10061→10067→10066
  possui ícone spidergun e limite1; efeitos filhos10062/10063 removem/modificam
  cura. Não confundir pai persistente da arma com debuff temporário do alvo.
- Implementação ainda pendente: aplicar no alvo, HUD, consumo por cura,
  cigarro/skills/bots, expiração individual. Antes de codificar duração, confirmar
  se termina no início do turno seguinte do alvo ou após ciclo completo.

## 2026-09-29 — Carnivore validada; Lady J implementada, v47

- Jogador confirmou Carnivore100%. Log234611 mostra duas recompensas2,
  saldo10300→10302→10304. Warning de card0/hero15 separado do combate,
  sem relação aparente com reward; não declarar sessão inteiramente sem aviso.
- Lady J IDs6/17/30/32 skill10006→buff10015 trigger34/lógica89,args[2].
  Texto nativo: reais≥falsas dobra recompensa de tiro em si. Condição avaliada
  antes de consumir falsa; inclui reais aprimoradas. Não ganha dinheiro na
  abertura, nem bônus em tiro contra outro. Apenas recompensa já existente
  de falsa em si; regra de real em si/Collect Bounty preservada.
- Multiplicador aplicado ao valor de shot reward incluindo combo, interpretação
  do texto sujeita a reteste; pool/nextShootCoin jogador e bots usam mesmo hook.
  Aviso isGunBuff no falso em si qualificado. Multiplicadores de modos futuros.
- Cinco testes novos cobrem IDs, condição/igualdade, base/combo, isolamento,
  aviso por alvo/tipo. Teste manual de valor/Collect Bounty ainda pendente.
- Validação local:223 testes passaram.

## 2026-09-29 — RedSiren validada; Carnivore implementada, v46

- Jogador confirmou RedSiren. Log232442 registra longa partida sem
  ERROR/WARNING/Traceback, inclusive fase sem falsas e dano no Bot1.
  Associação corrigida pelo jogador: RedSiren da Annie; Carnivore do Shelby.
- Carnivore cfg12 skill10015→buff10025 trigger13/lógica46,args[2,2].
  Recompensa2 por tiro normal real/aprimorado em outro que cause dano.
  Não multiplica pelo dano; conta HP ou Frenzy. Não premia falso, self,
  bloqueio completo, skill/Alucinógeno/Rocket. Burst premia cada acerto.
- Hook atualiza saldo autoritativo do shooter jogador/bots em modos2/3;
  publica delta de moeda na fonte do tiro e isGunBuff para aviso. Coexiste
  com Wanted sem substituir sua recompensa. Multiplicadores de modo futuros.
- 218 testes passaram, sete novos de recompensa, bloqueio, isolamento,
  cadeia, saldo/owner e envelope nativo de moeda/aviso. Visual pendente.

## 2026-09-29 — Ghosts validada; RedSiren implementada, v45

- Jogador confirmou Ghosts100%; log231901 mostra ganho2/4→3/3 e
  1/5→2/4, além de novo par2/3→3/2. Sem ERROR/WARNING/Traceback.
  V44 campo ghostGun resolveu o reteste; versões genéricas anteriores não.
- RedSiren cfg13 skill10019→buff10024 trigger7/17,lógica43,args[1,2].
  Metadados restringem tiro normal contra outro quando só há reais.
  Um tiro extra, não dano agregado; jogador e bots, modos2/3 participantes.
  Não aplica a tiro em si, Alucinógeno ou Rocket. Aprimoradas contam como reais.
- Usa cadeia nativa de tiros separados e aviso isGunBuff no primeiro tiro.
  Para se falta munição ou alvo/shooter eliminado; recarrega após cadeia.
  Não cria munição/bônus de entrada. Burst+trait atualmente soma1 disparo
  (até3), interpretação do argumento adicional ainda sem confirmação manual.
- 211 testes passaram, seis novos: condição, falsas, isolamento, self,
  composição com Burst e envelopes2 tiros/dano/munição/aviso. Visual pendente.

## 2026-09-29 — Ghosts: sinal nativo ghostGun recuperado, v44

- Reteste ainda sem efeito visual. Log231350 mostra ganhos1/5→2/4 e2/4→3/3
  no segundo falso de cada par: contador e estado autoritativo funcionaram.
- Encontrado PvpEventOutline.ghostGun campo69 boolean; ClientAnimExpression
  passa source.ghostGun diretamente a PlayerObject.ShootAmmo. V44 ativa o
  sinal apenas no tiro que concede real, publica rAmmo final nesse tiro e
  aviso isGunBuff. Removido evento genérico typ21 adicional de tiros normais
  e forçados para não duplicar apresentação. Rocket mantém caminho próprio.
- Revisão anterior de timestamp não resolveu o teste manual; não concluída.
  Testes exigem campo69 no segundo tiro apenas. Apresentação aguarda reteste.

## 2026-09-29 — Ghosts: evento de adição rejeitado por timestamp, v43

- Jogador não viu efeito. Log230951 às23:11:47 mostra falsa com1/3;
  às23:11:49 segunda falsa com2/2: ganho ocorreu no estado autoritativo.
- Lua OnFire aplica Finally_Source antes de OnShootOver/OtherEvent. A adição
  typ21 estava em uTime anterior, rejeitada pelo guard de UpdatePlayerInfo.
  Agora usa mesmo timestamp do evento final, inclusive cadeias e recarga.
- Testes de tiro forçado e rajada exigem essa igualdade. Não mudou contador,
  reset, probabilidades ou quantidades. HUD/animação aguardam reteste.

## 2026-09-29 — Ghosts implementada, v42

- Jogador acredita que recarga zera contagem; regra implementada assim,
  marcada como lembrança provisória, não prova da configuração nativa.
- cfg38 skill10040→buff10070, trigger35/lógica91,args[2,1,2]. Cada2 falsas
  disparadas adicionam1 real imediatamente. Contador por dono preservado
  no campo nativo Buff.args2; buff sem imagem, duração até recarregar/ativar.
  Tiros reais não limpam parcial, passar turno não limpa, Ejector não conta.
- Hook de tiro normal jogador/bots, rajada, Alucinógeno e Rocket. Recarga
  inicial não dá munição extra; qualquer recarga efetiva limpa parcial.
- Apresentação: tiro publica munição antes do ganho e evento AddFixed_Ammo
  typ21 com ammo1,num1/rAmmo final/isGunBuff, após tiro e antes do final.
  Isso instrui pop/add de slots na HUD em vez de apenas trocar quantidade.
- Testes cobrem isolamento, reset, tiro real intercalado, turnos, chain de
  duas falsas, tiro forçado e evento animado, Rocket. Manual visual pendente.
- Validação local: 205 testes passaram.

## 2026-09-29 — Grazier validada; próxima arma Ghosts em análise

- Jogador confirmou Grazier100%. Log222651 às22:33:04 registra Voucher
  com1 real comum+1 aprimorada; às22:33:10 tiro ammoCfg2 deixa1 real comum
  e2 falsas. Nenhum ERROR/WARNING/Traceback encontrado na sessão.
- Ghosts cfg38 skill10040→buff10070: trigger35/lógica91,args[2,1,2].
  Texto nativo: a cada2 falsas consumidas por tiro, carregar1 real.
  Não contar Ejector. Configuração disponível não esclarece reset do
  contador parcial ao recarregar: perguntar ao jogador antes de fechar regra.
  Ainda não implementada, nenhuma mudança de runtime nesta análise.

## 2026-09-29 — Artemis confirmada; Grazier implementada, v41

- Jogador confirmou apresentação da Artemis. Log222232 às22:23:24 mostra
  recarga3/3→4/2 e compra/uso Spare Magazine; sem ERROR/WARNING/Traceback.
- Grazier IDs7/18/31 skill10007 → buff10040, trigger16/lógica52,
  argumentos[1,2,2]: prioriza aprimorada quando resultado sorteado é real.
  Não gera vermelha, não aumenta chance de real e não impede falsa antes.
- Regra pura compartilha sorteio normal jogador/bots, rajada e Alucinógeno.
  Ejector mantém remoção aleatória (não é tiro). Rocket consome todas as
  reais no acerto, portanto não usa prioridade individual nem altera dano.
- Aviso isGunBuff no tiro aprimorado. Abertura sem bala criada; Arms Voucher
  é caminho de teste para obter vermelha durante a partida.
- 196 testes passaram; seis novos verificam famílias, probabilidade exata,
  isolamento, consumo, tiro forçado/dano2/aviso e preservação após falsa.
  Validação manual pendente; nenhuma outra arma foi implementada nesta etapa.

## 2026-09-29 — Artemis: recarga seguida de conversão visível, v40

- Trace/log da sessão220556: três Spare Magazine às22:17:28,22:17:48,
  22:18:51. Todos sortearam1 real+5 falsas, converteram para2 reais+4 falsas.
  Conversão funcional confirmada no servidor; não prova animação visual.
- V39 publicava apenas a munição final, omitindo a apresentação da troca.
  Lua nativa contém AfterReloadEvent e timer para typ12; CAmmo descreve os
  slots removidos/adicionados. V40 publica recarga typ1 com composição base,
  seguida de typ12 final com CAmmo300→1, quantidade1, e aviso da arma.
- Segunda etapa não tem isReload (evita repetir recarga). Timestamp acompanha
  o evento final do tiro para callback diferido não ser rejeitado como antigo.
  Mesma lógica nas quatro rotas, sem mudar sorteio nem dano/capacidade.
- 190 testes passaram; teste de envelopes agora exige base→conversão e
  CAmmo correto. Reteste visual pendente; misturas oficiais continuam futuras.

## 2026-09-29 — LoveSong validada; Artemis implementada, v39

- Jogador confirmou LoveSong em dois testes. Próxima etapa isolada: Artemis.
- Configuração nativa gun34 skill10034 → buff10053, trigger12/lógica66,
  argumentos [300,1,1]: converter1 falsa em1 real ao recarregar.
- Conversão ocorre após sortear o carregador, preserva capacidade6 e pode
  exceder reload_max_real3 no resultado final (por exemplo3+3 vira4+2).
  Não ativa na abertura, não gera aprimorada, não acumula entre carregadores
  e não converte se não houver falsa. Vale para jogador/bots pelo hook comum.
- HUD recebe munição já convertida e aviso isGunBuff nas recargas natural,
  Spare Magazine, Ejector, Alucinógeno e Rocket. Misturas oficiais continuam
  pendentes para futura etapa das armas; não foram alteradas aqui.
- Seis novos testes cobrem abertura, capacidade/limites, repetição, sorteio,
  isolamento de atualizações comuns, quatro envelopes e Alucinógeno real.
  Apresentação visual aguarda o jogador.
- Validação local desta etapa: 190 testes passaram.

## 2026-09-29 — Little Maniac confirmada; LoveSong implementada, v38

- Jogador confirmou abertura sem bônus e efeitos posteriores. Little Maniac
  concluída nesta etapa; apresentação da recarga das armas segue pendente.
- LoveSong cfg14, skill10016 → buff10026: trigger12, lógica38, argumento1
  na configuração nativa. A cada recarga efetiva reduz Hero.SkillCd em1,
  limitado a0 (pronta); não concede carga inicial nem crédito além de pronta.
- Hook comum aplicado no dono da arma, inclusive bot, independente do
  personagem. Não altera o ganho normal no início do turno. Recargas por
  tiro/Alucinógeno, Spare Magazine, Ejector e Rocket publicam evento nativo
  de SkillCd typ9 campo21 e aviso isGunBuff, no timestamp da recarga.
- 184 testes passaram; cinco novos verificam abertura sem ganho, limite,
  isolamento das armas, hook de estado e publicação das quatro rotas.
  HUD/animação e percepção do ganho aguardam teste manual da LoveSong.

## 2026-09-29 — carga inicial sem efeito automático de arma, v37

- Jogador confirmou a HUD pós-recarga da Little Maniac. Nova correção de
  regra: entrar na partida não conta como recarga para ativar traits.
- `_local_pvp_gamer` mantém a definição da skill, mas não converte munição
  amarela em vermelha nem concede Lucky Streak na carga inicial. Aplica-se
  ao jogador e a todos os bots/variantes. Capacidade inicial foi preservada.
- Recargas efetivas durante a partida continuam ativando os efeitos:
  natural, Spare Magazine e recargas provocadas pelos demais itens.
- Testes de famílias e integrações TCP distinguem abertura de recarga real.
  Regra registrada como base para próximas armas; não confundir trait da
  arma com cargas/cooldown da skill ativa do personagem.
- Validação: 179 testes locais passaram, incluindo abertura sem bônus e
  ativação subsequente por recarga em conexão TCP real.

## 2026-09-29 — Little Maniac: atualização da HUD após recarga, v36

- Jogador confirmou o bônus com cigarro e skill, mas o ícone da segunda
  recarga só apareceu na troca de turno. Trace `20260929-213348` confirma
  duas recargas por Spare Magazine enviando cfg600 dentro do evento typ12.
- Causa nativa: `RouletteGamePlayer:ShowUIChange` só chama UpdateBuffs nos
  tipos Buff_Update/Shoot/Pvp_Arcade_Shoot, não nos eventos de recarga.
  Agora cada recarga da Little Maniac inclui também um evento typ10 com
  cfg600. Mesmo timestamp da recarga evita invalidar seu callback diferido;
  origem e alvo são o dono da arma, sem redirecionar a câmera.
- Cobertura: Spare Magazine, Ejector, tiro/Alucinógeno e Rocket Launcher.
  Regra do dado e animação de bônus não foram alteradas. Dois novos testes
  cobrem as rotas e a segunda recarga após consumir o efeito; HUD requer
  confirmação manual antes de fechar esta etapa e avançar para LoveSong.
- Validação local: 177 testes passaram, incluindo conexão TCP real.

## 2026-09-29 — Screwdriver validada; Little Maniac implementada, v35

- Jogador confirmou que a Screwdriver parece funcionar bem. Auditoria do
  trace `packet-trace-20260929-211320.jsonl`, somente mensagens enviadas:
  21:15:17 falsa preservou a aprimorada; 21:15:23 real comum preservou cfg2;
  21:16:46 cfg2 retirou 2 HP e foi seguida por recarga com 2 falsas, 1 real,
  1 aprimorada. Não houve ERROR/WARNING/Traceback no log dessa sessão.
  O trace não contém Spare Magazine manual; essa integração passou em teste.
- Little Maniac IDs 0/8/10/15/19/33 recebe skillId 3 e Lucky Streak cfg600
  em cada recarga inicial/natural/forçada, incluindo bots. Não acumula buffs
  nas recargas, não expira pelo simples passar do turno e não volta só por
  adicionar uma bala. Versões de tutorial continuam sem trait.
- Próximo dado do dono, seja skill da coelha, cigarro ou Multa, consome cfg600
  e usa `min(6, dado_original+2)` no efeito. As outras armas/personagens não
  recebem bônus por causa da ação do jogador. Ejector/Alucinógeno sem dado
  não consomem Lucky; recarga provocada por eles pode renová-lo.
- Protocolo nativo recuperado: LuckEvent.randLuck (1), addLuck (2), buffs (4).
  `RouletteBattleWindow:PlayAddLuckAnim` aplica a apresentação do bônus após
  1,5s e limita visualmente a 6; campos são enviados separados, não um dado
  final disfarçado de resultado sorteado. Remoção do buff no dono é um evento
  separado, sem mover câmera de mira. Recargas incluem buff e isGunBuff.
- 175 testes passaram: 14 novos de Little Maniac, com casos 1..6, consumo
  único, recarga sem empilhar, isolamento por dono, bots e conexão TCP real
  de compra direta/uso guardado de itens e skill ativa. HUD/som/animação ainda
  não foram validados manualmente. Roteiro em `WEAPON_TEST_ORDER.md`.
- Próxima arma planejada: LoveSong, depois da confirmação da Little Maniac.
  Skills melhoradas dos personagens e outras pendências não avançaram.

## 2026-09-29 — primeira habilidade automática de arma: Screwdriver, v34

- Implementação limitada à Screwdriver; demais traits e upgrades de personagem
  continuam pendentes. Original intocado, somente servidor/arquivos de pesquisa
  na cópia foram alterados; nenhum bundle ou inventário foi editado.
- `weapon_skills.py` concentra o mapa de IDs 1/5/9/16/20/29 e o hook pós-recarga:
  uma real comum vira aprimorada, conservando a capacidade. IDs de tutorial
  3/11 não ganham a habilidade por parecerem a mesma arma.
- Recarga inicial, natural, Spare Magazine, Ejector, Alucinógeno e Rocket
  aplicam a conversão na arma correta. Snapshots/outlines incluem cfg2;
  recargas usam `isGunBuff` para o aviso nativo da HUD.
- Disparo sorteia falsas/reais/aprimoradas proporcionalmente. cfg2 causa 2
  de dano e consome uma munição, não toda a pilha. Não antecipar o trait de
  Grazier (prioridade da aprimorada). Probabilidade dos bots também corrigida.
- Compatibilidade: adicionar munição não apaga cfg2 na HUD; Arms Voucher
  preserva a contagem acumulada e não converte bala já aprimorada em
  munição negativa. Bounty inclui aprimoradas no total de balas reais.
- Verificação: 161 testes locais passaram, incluindo 15 testes de arma e
  conexão TCP real com inventário temporário: login, Spare Magazine,
  Arms Voucher, adicionar real, Alucinógeno e tiro normal aprimorado;
  compra/uso direto e item guardado. Testes antigos ajustados onde assumiam
  que Screwdriver não possuía trait; mocks de Wanted fixam o sorteio de tiro.
- Estado: funcionalidade automatizada verificada; HUD, som e animação ainda
  aguardam confirmação manual do jogador. Roteiro em `WEAPON_TEST_ORDER.md`.
- Misturas oficiais das recargas, câmera de morte e multiplicadores por modo
  seguem pendentes separados, sem declarar corrigidos nesta etapa.

## 2026-09-29 — pesquisa de armas e skills, antes da implementação

- Nova prioridade do jogador: armas/efeitos/animações/nível melhorado;
  Piggy Bank pré-partida adiado.
- Adicionado `WEAPON_SKILL_RESEARCH.md` com dez traits automáticos, dez
  pares de skills básicas/melhoradas dos personagens e referências de
  câmeras/cutscenes. Upgrade ativo pertence ao personagem nos campos
  examinados; nenhum upgrade individual de arma foi comprovado.
- Extrator reproduzível `tools/audit_weapon_skills.py`, restrito à cópia,
  lê os descritores protobuf do bundle atual e registra hashes. Saída:
  `private-server/config-extract/weapon-skill-audit.json` e Lua de auditoria.
- Validação: 42 IDs de arma 0–41; os dez traits visíveis apontam para skills
  e buffs válidos; `py_compile` passou. Diferenças gun_cfg/Steam são apenas
  `getWay_Common` nas 12 linhas divergentes; skill_cfg/Steam iguais.
- Achados: textos históricos divergentes Lady J; textos curtos trocados em
  variantes internas; escala Carnivore 2/20/200 não é nível 2; servidor
  ainda não inicializa `Gun.skillId` nem executa traits específicos, e o
  handler ativo do jogador só aceita Yu/No.13 básicos.
- Nenhuma alteração de gameplay/assets/inventário nesta pesquisa; nenhuma
  animação foi declarada visualmente validada. Plano de implementação e
  casos de teste no documento de pesquisa.

## Rocket Launcher (2032) — regra e dano corrigidos, v33, 2026-09-28

- O log antigo registrava `hpDelta=-2`, mas era só o valor fixo da
  implementação anterior; não demonstrava a regra correta. A descrição do
  bundle e o jogador confirmam o contrato: o Rocket sorteia uma munição. Se
  falsa, consome uma falsa e não causa dano. Se real, consome todas as reais
  restantes e causa dano igual à quantidade real antes do disparo.
- O Lua do cliente confirma o formato: `Enum_Rpg=39`, `source.uAmmo` é consumido
  por `ShootAmmoMul`, e `source.isRpgHit` escolhe a animação de acerto/falha.
  O Rocket agora usa esse evento; HP/Frenzy do alvo e Frenzy do atirador são
  deltas corretos. Quando acaba a munição real e o confronto continua, um
  `Enum_Reload` separado vem depois da animação RPG, evitando dupla subtração.
- Implementado tanto em compra-uso quanto no item guardado. A IA também pode
  avaliar e usar Rocket; cfg2 melhorada conta como um espaço real neste efeito.
  Compatibilidade visual do cfg2 ainda deve ser conferida manualmente.
- `py_compile` passou e os 143 testes passaram. Há cobertura unitária para
  resultado falso/real, dano atravessando HP/Frenzy, consumo e recarga; teste
  TCP cobre compra-uso e item guardado. A animação/renderização real do Rocket
  ainda precisa de confirmação do jogador.
- Bucket (2033): o jogador relata que funciona e que sua aparição/animação
  parecem corretas. A sessão de log mais recente não continha uma partida, então
  esse ponto fica registrado como observação do jogador, não como evidência do
  trace. Original continua intocado; alterações apenas na cópia.
- Próxima validação no cliente: Rocket no Bot 1/2; anotar bala sorteada,
  munição consumida, dano, Frenzy, animação e recarga. Ver roteiro em
  `ITEM_TEST_ORDER.md`.

## Auditoria de Permission Ban e Rocket Launcher — v32, 21:14–21:22, 2026-09-28

- No segundo teste local, o usuário guardou Permission Ban (cfg2030) e o usou
  no Bot 1. O servidor registrou `skill=10009`, sem erro de uso. No próximo
  turno do alvo, a recarga da skill chegou de 1 a 0; o bot então usou outros
  itens e atirou, sem evento de ativação de skill. Isso é compatível com o
  bloqueio esperado, mas a expiração do efeito não apareceu antes do fim da
  sessão; o usuário relatou que parece funcionar.
- Na mesma sessão, Rocket Launcher (cfg2032) foi usado no Bot 1; o servidor
  registrou consumo do uso e `hpDelta=-2`. A parte de efeito/dano está
  confirmada no protocolo; animação e apresentação não foram avaliadas
  separadamente pelo usuário.
- O servidor terminou sem `ERROR`/exceção. Houve um `WARNING` esperado ao
  tentar atualizar a loja por 300 R Coins com saldo de apenas 100. O cliente
  traduziu essa recusa como “Database error” às 21:12:35; é uma mensagem
  genérica de saldo insuficiente, fora do teste de Permission Ban. Também há
  um erro de interface `[LID:133]` no encerramento da primeira partida, antes
  do segundo teste; causa ainda não identificada.
- O cliente da cópia foi fechado normalmente após a captura dos logs; o
  servidor de teste encerrou junto. Próximo teste manual: Bucket (cfg2033),
  usando em si e recebendo um tiro real normal para conferir bloqueio de um
  dano, ícone e consumo do slot.

## Persistência dos bans no snapshot — v32, 2026-09-28

- No trace 17:30:35, Purchase Ban (cfg2022 → buff1021) foi usado no bot 1.
  O outline do evento trazia o buff, mas o gamer serializado em `PvpInfo` não;
  a atualização completa seguinte podia removê-lo da HUD/observação da IA.
- Às 17:30:53 o urso usou corretamente sua skill 10001 para converter Frenzy
  em HP. Purchase Ban impede compras da loja, não skill nem item já guardado;
  o mesmo turno usou Surprise Box que já estava no slot e então atirou. O trace
  não indica reset de partida nem compra na loja neste trecho.
- `TurnRestrictions.apply_to_gamer` agora agenda a expiração individual e grava
  o buff nativo no gamer persistente. Aplicado tanto no uso comprado quanto no
  item guardado; o snapshot completo e as atualizações da HUD preservam o ban.
- Regressão cobre persistência após sync, bloqueio de oferta, skill permitida e
  remoção na expiração. `py_compile` e os 139 testes passam. Servidor/launcher
  avançados para v32 e cópia reaberta. Ícone/fluxo ainda pendentes de validação
  visual; original preservado.

## Auditoria da partida v32 — 17:50–17:58, 2026-09-28

- A partida completou cinco rodadas e encerrou com vencedor; sem ERROR/WARNING
  no log do servidor. O jogador reportou gameplay normal. Rocket Launcher
  (2032) gerou dano de 2 HP no alvo 2; 11 atualizações de loja cobraram 300
  cada e retornaram quatro ofertas novas por atualização.
- Compra/uso do Purchase Ban (2022) às 17:57:26 agora deixou buff nativo 1021
  no gamer 1 tanto no evento como nos snapshots seguintes. O bot não comprou
  durante o turno observado, mas escolheu atirar; não houve tentativa de compra
  bloqueada que comprovasse visualmente a trava. No snapshot de encerramento,
  turno 14, 1021 ainda estava presente e não apareceu evento passivo de remoção.
  Possível duração um turno maior; validar expiração em nova partida antes de
  dar o relógio comum de Purchase/Permission Ban como fechado.
- O Player.log registrou `skill_cfg id: -1`/`cfg=nil` durante seleção; logo
  depois o dado do jogador rolou 6 e a skill 10000 curou 1 HP. Não interrompeu
  a partida, mas fica como ruído de interface a observar. Após o resultado,
  também faltou o sprite `UI_Result_rank_0` (cosmético). Desconexões ocorreram
  após o fim da partida.

## Purchase Ban HUD e sequência de ações dos bots — v31, 2026-09-28

- Relato: Purchase Ban sem ícone; urso usa skill/Energy Pump ainda na animação,
  HP/Frenzy aparecem corretamente somente depois do tiro. Mantido como problema
  de apresentação, não mudança na regra da skill/cooldown de jogo.
- Evidência do cliente: `Player.log` em 17:03:51 registra
  `can not find buff_cfg , id: 2022`. `skill_cfg[1021].buff_id=1021` e
  `buff_cfg[1021].imgName=UI_Fight_bufficon_tradingrestrictions`. Era enviado
  cfg do item (2022), não do buff (1021). Corrigido na compra/uso guardado do
  humano, bot, regras de decisão e remoção por prazo. Mesmo mapeamento corrigido
  para Permission Ban: item2030 → skill10009 → buff10018. Bucket usa buff1026;
  seu comportamento/duração completos ainda não estão aprovados.
- Trace v30: urso skill10001 enviado às 17:03:29.536; Energy Pump às
  17:03:35.547, apenas 6s depois. `UseSkill` inicia cutscene; depois
  `OnCutSceneFinish` chama `StartUseSkill`, abre UI e dispara timer de 4,75s.
  Portanto esses 4,75s não são toda a ação. Confirmado em
  `fight_cutsceneprefab.ab`: `TV_Bear_Skill_NEW` tem `_length=4`, playbackSpeed1;
  `OnCutSceneFinish` em3,9s. Coelho tem cutscene3,4s/callback3,3s.
- `bot_presentation.py` separa espera de animação do cooldown de habilidade.
  Skill do urso reserva9,75s (4+4,75+1 de recuperação), dado10,4s
  (3,4+6+1), mais pausa decisória0,6s antes da próxima preparação. Cutscene,
  skillShowTime e alvo de carta (2s, expressão1s) são dados nativos; recuperação
  de1s e margens das cartas são estimativas do laboratório para teste visual.
  Energy Pump/ban/cigarro/multa têm barreira própria.
- Sem timer/pacote extra de atraso na HUD e sem reaplicar delta de HP/Frenzy.
  Efeitos permanecem no próprio pacote e nos callbacks nativos. Só a próxima
  ação recebe espera maior, para não interromper a anterior.
- 138 testes passam; `py_compile` passa. Novas regressões verificam IDs nativos
  no addBuff, efeitos HP/Frenzy no pacote da skill, bloqueio/expiração e barreira
  de animação. TCP anterior preservado; não prova ausência visual de sobreposição.
- Auditoria somente leitura em `tools/audit_bot_presentation.py`. Backup antes
  desta etapa: `private-server/rollback/2026-09-28-pre-bot-presentation/`.
- Reteste: marcar Purchase Ban, observar ícone e expiração; acompanhar urso
  usando skill e outro item: HP/Frenzy devem refletir a skill antes da próxima
  ação. Ajuste ainda não aprovado visualmente pelo jogador.

## Bots de utilidade v30 — 2026-09-28

- Mesa de três participantes integrada à IA modular por probabilidades e
  utilidade. Bots avaliam humano/outros bots/si, itens conforme descrição e
  condições, saldo e habilidade suportada. Sem conhecimento da próxima bala.
- 24 cfgs com executor; Rocket Launcher/Piggy Bank e habilidades além de
  10000/10001 seguem pendentes. Outros modos mantêm o comportamento anterior.
  Alucinógeno/Ejector com alvo de bala reforçada excluídos até validar combinação.
- Perfis fácil/médio/difícil preparados; launcher padrão médio. Pagamento,
  estoque, slot e origem/alvo individualizados. Compra/habilidade bloqueadas
  por bans individuais. Intervalos de ações e limites evitam sequências sem fim.
- 135 testes passam; compilação Python passa. TCP comprova compra/uso e
  tiros falsos consecutivos/coleta por bots, não qualidade visual/equilíbrio.
  Detalhes, fontes e teste manual em `BOT_RESEARCH.md`.
- Wanted: jogador aprovou correção de mira antes desta etapa. Próxima validação
  de item: Purchase Ban com bots que agora podem efetivamente comprar.
- Original preservado; rollback em `private-server/rollback/2026-09-28-pre-bot-ai/`.

## Milestones

| Milestone | Status | Evidence |
|---|---|---|
| M0 Client starts | CONFIRMED historically / not rerun this turn | original historical logs and prior lab launch |
| M1 Bootstrap/handshake | CONFIRMED on prior localhost wire | local HTTP and TCP sequence logged |
| M2 Login | CONFIRMED on prior localhost wire | logic `1/1`, profile requests, and sustained heartbeat |
| M3 Player snapshot | CONFIRMED on prior localhost wire / visual unknown | client advanced to local match creation |
| M4 Lobby | CONFIRMED on prior localhost wire / visual unknown | client initiated local match from the loaded profile |
| M5 Create match vs bot | CONFIRMED on prior localhost wire | local match, PVP fd/login, and scene-ready completed |
| M6 Initial state | `255/7` confirmed in TCP integration test; not in older live trace | test covers `3/14` -> `255/7` -> `255/1`; older live trace had `255/1` but no `255/7` |
| M7 One action end to end | CONFIRMED wire / VISUALLY REJECTED on v8 | client completed `3/3`, but self target was rewritten to opponent |
| M8 Bot turn | Bot sequence confirmed on older live wire / visual unresolved | older trace includes staged turns, `255/4` raise/aim, both bot shots, and return to player; earlier v8 visual rejection remains unresolved |
| M9 Complete match | CONFIRMED wire only / NOT PLAYABLE | v8 emitted final `255/2` + `255/5` and returned to lobby, but targeting, synchronization, and animation were wrong |

## Lote de itens PVP — 2026-09-24

- O estoque de laboratório passou a incluir os cards do recorte de 26 itens,
  com quatro ofertas distintas por geração e log de `cfgId`/id da oferta.
- Os contratos já confirmados (munição, ejetor, alucinógeno, cigarro e
  carregador) continuam usando seus builders específicos.
- Os demais cards agora usam um builder comum baseado no envelope real de
  `PvpEventResult`: compra/uso, alvo, consumo do slot, evento de efeito e
  atualização da sala. Isso elimina o antigo `Erro de banco de dados` causado
  por uma ramificação sem handler.
- Efeitos locais verificáveis foram adicionados para voucher de munição,
  manutenção, rajada, caixas-surpresa, foguete e balde; os itens cuja fórmula
  original não apareceu em captura ficam explicitamente marcados na matriz.
- `py_compile` e os 65 testes de protocolo/loopback passaram. Dois fluxos
  genéricos foram exercitados em loopback: compra-e-uso (2009) e compra,
  armazenamento e uso (2015). A validação visual de todos os cards ainda
  precisa ser feita na cópia aberta pelo jogador.

### Correção após o último teste manual — 2026-09-24

- O log confirmou o congelamento: com real=0 e falsa=0, `3/3` recebia ACK,
  mas não havia transição de turno. A cópia agora publica uma recarga de
  segurança 4+2 e mantém o turno jogável; isso é uma proteção local, não uma
  regra original declarada.
- A leitura direta de `fight_dbconfig.ab` identificou cfg 2 como a munição
  melhorada (“强化弹”), além de cfg 1 real, cfg 300 falsa e cfg 301 de cura.
- Arms Voucher (2009) agora envia `Enum_Ammo_Replace`, converte uma cfg 1
  existente em cfg 2 via `rAmmo`/`cAmmo` sem aumentar o pente, e o próximo
  tiro consome somente a cfg 2 para aplicar dano 2. O antigo +1 real foi
  removido.
- Burst Mode (2016) agora é um buff de disparo contínuo: no próximo tiro contra
  outro jogador o servidor sorteia/consome duas munições e envia dois eventos
  `Enum_Shoot` consecutivos, com `rAmmo` pós-cada-disparo. A tentativa de usar
  `ContinueShoot` como indicador visual foi uma hipótese errada; a investigação
  posterior identificou o sistema de buffs da placa como a UI correta.
- A suíte passou de 65 para 67 testes; `py_compile` continua limpo.

### Validação manual do Arms Voucher — 2026-09-24 01:38

- O log da sessão `server-session-20260924-013704.err.log` registra o uso de
  cfg 2009 com `targetAmmo=2/1 enhanced=1`: a bala melhorada substituiu uma
  bala real sem aumentar a quantidade total.
- O tiro seguinte foi registrado como `ammoCfg=2`, deixando `playerAmmo=2/1`;
  portanto consumiu apenas a cfg 2. O alvo terminou com 2 HP, confirmando os
  dois danos no disparo.
- A correção foi observada no modo de três participantes com o bot, e o
  servidor continuou a sequência de turnos normalmente.

## Work completed on 2026-09-16

- Captured baseline without modifying original game files.
- Verified the lab copy's critical hashes match the original.
- Inventoried historical logs and identified the richest gameplay session.
- Confirmed Unity/IL2CPP/xLua/UnityFS/protobuf/AntNet architecture.
- Corrected the `(255,3)` direction/name clue using the shipped Lua command table.
- Mapped login, dual TCP, PVP fd/login/load, heartbeat, action, notification, and end paths.
- Classified original bots as a client/server combination strongly weighted toward server-authoritative decisions.
- Preserved privacy by excluding tokens, user/device IDs, friend lists, original IP addresses, and SDK secrets.
- Re-read the preserved localhost session and promoted M1-M7 from generic partials to wire-level evidence: two real client shoot requests were received and processed.
- Identified the first current completion target as visual/state validation plus the final `255/5` and evaluation path, not the first shoot request.
- Captured a full v8 localhost run: 309 frames, zero length errors, four real client shot requests, final `255/5`, and return to the lobby.
- Rejected that run as gameplay validation after direct user observation: self-shot selected index `0`, while the server forced it to opponent index `1`; bot turns and animations were also out of sequence.
- Recovered the client-side animation contract from shipped Lua/protobuf: self shot is `source.Idx == target.Idx`; event death state is field 63; hit animation/type are fields 49/73; room round/turn/current gamer are fields 4/8/10.
- Implemented local server v9 with preserved target index, unique event ids/times, self-shot ammo/count, correct animation/death fields, authoritative PvpInfo state, and explicit bot/player turn notifications.
- Expanded the static protocol suite from 9 to 11 passing tests, including separate self-shot and opponent-shot assertions.
- Inspected the shipped update metadata: no human server manual was present, but `PkgVersion.json` enables normal and pre-update flows, and MD5 manifests version individual resource bundles.
- Recovered the ordinary-shot contract from bundled developer annotations and Lua: `cAmmo` means ammo-type change, `ShootAmmo` performs consumption, and every shot uses a separate `Enum_Finally_Source` event.
- Implemented server v12 with ordinary shot ammo semantics, final-source events, explicit `Pvp_Prepare -> PvpIng` transitions, the built-in local AI's 3-second think delay, and synchronized embedded gamer rounds.
- Expanded the protocol suite to 12 passing tests.
- Completed a real localhost v12 integration cycle. Decoded order: player shoot (two events, no `cAmmo`, two-entry `rAmmo`) -> bot prepare -> bot active -> bot shoot -> player prepare round 2 -> player active round 2. Both final global and embedded gamer rounds were 2.
- Added the reported persistence failures as a separate reconstruction track. Confirmed that only hero selection, fashion equip, and hero-gun equip currently save; shop refresh is empty and shop/lootbox/armory state is absent rather than intermittently failing to write.
- Verified the Steam configuration rows for every hero currently present in the lab inventory. Their skill ids, gun ids, and base-fashion ids exist in the shipped Steam tables; the observed `skill_info_cfg` Lua exception is therefore not explained by invented or missing hero skill ids.
- Implemented fashion-info refresh `23/2` from the same persisted ownership/wear lists used at login and by notification `253/18`, preventing a page refresh from replacing valid equipment state with an empty response.
- Started server v13 persistence reconstruction. `GamerHome` now serializes all three explicit supply-box slots from `inventory.json`; the level-50 lab profile defines them as unlocked and empty (`status=1`, `boxId=-1`) instead of accidentally locked by omission.
- Added targeted evidence logging for market purchase `22/1`, character/card selection `12/2`, and supply-box start/open/sell `13/1`-`13/3`. These paths intentionally remain non-mutating until a real client request identifies the selected ids and counts.
- Completed the inventory-first foundation in the writable copy. The known bag
  operations (`8/1`–`8/3`), exploration cells (`32/1`–`32/6`), and all five
  home-box commands (`13/1`–`13/5`) now validate, mutate, save atomically, and
  return absolute quantities. Home-box durations, currency/key costs, sell
  rewards, temporary boxes, and first-stage configured awards come from the
  shipped Steam tables; only the newer selector variants remain gated.
- Completed the first inventory chain pass from the shipped Steam tables:
  reward wrappers now expose `show`/`chgNumber` (the client ignores `get` when
  deciding whether to show a reward), home packages `701048..701076` resolve
  their decoded drop rows, and the historical character packages
  `701000..701047` persist hero badges and `specialShow` rewards. The newer
  `701077+` random selector remains intentionally gated pending evidence.
- Fechada também a lacuna de reutilização da grade de caixas: células
  concluídas (`chest=0`) voltam a ser usadas, e `wayToSave=3` não descarta uma
  caixa em andamento enquanto o prêmio desse caminho não estiver reconstruído.
- Corrigida a resposta parcial de `OpenAll`: o cliente calcula a animação com
  `5 * quantidade_de_células` e só envia `32/6` depois da última animação. O
  servidor resolve e devolve todas as células ativas (até onze) no `32/5`, e o
  `32/6` resgata exatamente esse conjunto; repetições pendentes continuam sem
  cobrar munição.
- Corrigida a lacuna descoberta no teste de compras: `22/1` agora atende os
  três produtos reais `14500000`/`14500001`/`14500002`, com preços 35k/50k/100k
  de `102000`, itens `701264`/`701265` e packs azuis/roxos persistidos.
- Aplicada a tabela `ExploreBoxUpCfgSteam`: a abertura de uma caixa resolve a
  chance real de raridade (incluindo `2 -> 3` e `2 -> 4`), envia evento `2`
  para cada tiro de upgrade e grava o `box_award` correto por qualidade/nível.
  Uma única abertura pendente também pode ser repetida sem nova cobrança.
- Fechado o caso de `OpenAll` parar visualmente em seis caixas: o corte
  temporário de seis foi removido do servidor e a Lua `TreasureBoxOpenAllWindow`
  recebeu proteção por tiro, coleta idempotente e watchdog para que uma falha
  de efeito não interrompa a fila antes do `32/6`. O teste laboratorial real
  registrou `32/5` com 11 células e `32/6` com 11 recompensas; o trace também
  decodificou 11 campos de célula na resposta. O bundle Lua original está
  preservado em `private-server/rollback/2026-09-17-pre-lua-resilience`.
- A suíte de protocolo passou a 41 testes. A nova integração cobre replay de
  resposta perdida sem recobrar munição, resgate de 11 recompensas e upgrade
  forçado de qualidade 1 para 4, sempre em uma cópia isolada do inventário.


## Next action

### Reavaliação em 2026-09-22

- O pedido real do cliente no laboratório foi `mode=1, subMode=6`. A sala
  fabricada tinha 2 combatentes e nenhuma loja, apesar de a tabela do modo 1
  prever 3 combatentes. A captura online 2v2 de referência tem 4 jogadores e
  itens; ver `MODE_RECONSTRUCTION.md`.
- Separado estado PVP planejado do último snapshot publicado: consultas
  `3/11` e `3/19` não recebem mais o tiro futuro do bot. Um teste TCP consulta
  a sala no intervalo entre os dois tiros.
- O heartbeat repetia o mesmo horário histórico e podia impedir `32/3` para
  sempre por causa do cooldown de dois segundos no Lua. O relógio de temporada
  agora avança com tempo monotônico e é enviado no login, heartbeat e dados da
  exploração. Testes locais cobrem o avanço em respostas reais TCP.
- A suíte local passou a 44 testes. O servidor já em execução antes dessas
  alterações precisa ser reiniciado para carregá-las; nenhuma validação visual
  do novo código foi feita.

O experimento do snapshot/turnos do modo 1/submodo 6 foi concluído em loopback
na retomada de 2026-09-23 (detalhes abaixo). A sequência renderizada ainda
precisa de uma partida manual curta do usuário.

Continue the evidence-gated tracks in the writable copy:

1. Let the user test the inventory screens and capture a fresh wire trace for
   any remaining error. Classify each failure as a missing config path,
   incorrect absolute quantity, or a UI-only animation issue before changing
   state code.
2. Test the current mode 1/submode 6 build manually. Validate all three
  participants, both bot poses/shots, correct target/HP/ammo HUD, return of the
  player's controls on the next round, and the piggybank prop/use animation.
  Capture a fresh trace if the display differs from the wire events.
3. Let the user test the complete box chain (shop product -> pack -> five-shot
   opening -> reward item -> direct use), including an `OpenAll` with more than
   six active cells, and capture a wire trace for any remaining UI mismatch.
   The shipped purple/orange/red reward rows are fixed coin drops; the blue row
   yields its configured character package. Decode the newer `701077+` selector
   only after that test; do not grant unsupported rewards.

Do not promote the build to playable until rendered HP/ammo, animation target, turn owner, owned-item counts, and equipped appearance all agree after reconnect.

### Retomada em 2026-09-23

- O snapshot `mode=1, subMode=6` foi avançado para três combatentes, com
  moeda inicial, quatro ofertas e flags da loja. Os handlers de armazenar uma
  carta (`Typ_Buy`) e atualizar a loja (`Typ_Refresh_Card`) agora emitem os
  eventos de moeda, slot e estoque descritos pelos Lua/protobuf do cliente.
- Teste TCP local cobre comprar/guardar `cfgId=2001`, débito de 100, estado
  de slot/estoque e refresh por 300; a segunda rotação da oferta também foi
  verificada como diferente da lista inicial.
- Verificação de retomada: `py_compile` e suíte completa passaram com 48
  testes. Isso é evidência de protocolo, não de animação ou jogabilidade
  renderizada.
- O uso genérico de carta guardada (`Typ_Use`) exige efeito por `skill_typ`;
  ejetar/trocar munição continua pendente porque o laboratório não modela a
  ordem das balas nem `ammoBank`. A exceção agora implementada e testada é o
  Cofrinho (`cfgId=34/1034/2034`, skill 1028): só esse efeito credita o saldo
  acumulado e limpa seu slot. Não generalizar esse handler para outras cartas.
- A lacuna de turno do modo 1/submodo 6 foi fechada no protocolo: um tiro local
  agora pode atingir o gamer 0, 1 ou 2; os dois bots vivos recebem poses/turnos
  em sequência e HP/munição de todos é sincronizado nos snapshots emitidos.
  A rodada seguinte devolve controle ao jogador e atualiza o Cofrinho. Se o
  jogador morre, os bots continuam até restar um vencedor e o encerramento
  atribui ranks conforme a ordem de eliminações. Testes TCP determinísticos
  cobrem ambas as rotas; a política de alvo (priorizar o jogador e, após sua
  morte, atacar o outro bot) é heurística, não IA oficial recuperada.
- Mapeamento da pendência da “bolsinha”: entre as 359 entradas de `CardCfgSteam`,
  apenas seis têm `is_only_outside_carried=1`: `33/1033/2033` (Balde de Ferro)
  e `34/1034/2034` (Cofrinho). A base `34` habilita a biblioteca, aponta para
  `UI_Fight_Itemicon_PiggyBank` e `Model_PropN_GoldPig`; a descrição diz que
  guarda 2 R Coins por turno e entrega o saldo ao ser usado. A própria tabela
  liga as variantes de dificuldade 2 e 3 aos IDs `1034` e `2034` (descrições
  com 20 e 200 R Coins por turno). É o encaixe mais forte para “bolsinha de
  dinheiro”, mas falta o usuário confirmar a aparência/nome que lembra. A base
  `34` não é desbloqueio padrão: a config/lógica de inventário aponta gate de
  herói 2 estrelas + base nível 30, com custo externo configurado de 100 R
  Coins ou token `201014`.
- Os `Treasure Bag` (`112191`, `122191`, `132191`) da hipótese anterior não são
  itens de pré-carga: `is_only_outside_carried=0`, biblioteca desabilitada e
  campos de ícone/modelo vazios. Corrigido o candidato nos registros.
- O Lua da seleção pega o cardId escolhido e o envia em `GamerReqPvpC2S`
  (campo 8); por outro caminho, a seleção persistida do herói vem de
  `GamerHero.readyCard`. Já dentro da partida, `PvpGamer.CardSlot` é outra
  estrutura: a carta tem `id` de instância, `cfgId` de configuração e
  `arg_one` para o dinheiro acumulado. O emulador agora lê o `cardId` do
  marcador local e serializa o slot carregado; teste de protocolo cobre o
  Cofrinho `cardId=34`. O trace antigo com `cardId=3` não é evidência sobre o
  Cofrinho nem sobre o sintoma relatado.
- O último trace salvo (22/09) enviou `mode=1`, `subMode=6`, `heroId=0`,
  `cardId=3`. O `inventory.json` atual da cópia também tem `readyCard=3` para
  esse herói, e o `cfgId=3` é `Bala Real +1`, não o Cofrinho. Isso explica o
  valor daquele trace como carta equipada/preselecionada, mas o trace antecede
  o relato do item “travado” e não identifica o objeto visto pelo usuário.
- No laboratório, a carta `34/1034/2034` agora inicia no slot visível com o
  valor do primeiro turno, acumula de 2 para 4 no início do turno seguinte e,
  ao ser usada, credita 4 e limpa o slot em eventos separados. Um teste TCP
  cobre evento 51, coleta `Typ_Use`/evento 8 e saldo final. Um teste adicional
  percorre a requisição de partida `GamerReqPvpC2S` (`cardId=34`) no serviço
  logic, verifica que o marcador local preserva o ID e confirma que o login
  PVP entrega o Cofrinho (`cfgId=34`, saldo 2) no `CardSlot` do jogador; o
  mesmo caminho com `cardId=0` não cria slot nem item carregado.
  `py_compile` e 53 testes locais passam. Ainda falta confirmar no cliente a
  aparência/animação do ícone e do modelo, e a correspondência do ID de
  instância fora do caso laboratorial.
- Para o ciclo dos três combatentes, novos testes cobrem os tiros dos índices
  `0 -> 2`, `1 -> 0`, `2 -> 0`, os estados de munição/HP e o retorno ao jogador
  na rodada 2; outra sequência elimina o jogador e verifica que a luta entre os
  bots termina com ranks `3/2/1`. A suíte completa agora passa com 55 testes e
  `py_compile` também passou. São resultados de loopback, não validação visual;
  política de alvo e término ao esgotar munição/`ammoBank` continuam pendentes.
- Nova inspeção somente-leitura dos TextAssets em `fight_dbconfig.ab` e
  `fight_languagedb.ab` resolveu os modos: 1 = Classic, três combatentes;
  11 = Classic 2v2, quatro combatentes. O trace preservado é modo 1/submodo 6;
  o print histórico é modo 11. A rotação de três participantes do submodo 6
  agora tem cobertura TCP, mas o snapshot continua forçando `mode=1`; o modo
  11/2v2 e os submodos 4/5 ainda não estão reproduzidos nem testados. O próximo
  teste manual deve confirmar poses/turnos no submodo 6, após o que a próxima
  frente técnica é completar o snapshot/loop do modo 11 com quatro combatentes.

### Erro de banco / Alucinógeno — 2026-09-23

- O trace `packet-trace-20260923-145105.jsonl` e o log correspondente mostram
  que a compra inicial do Alucinógeno (`cfgId=2008`, oferta 4) foi aceita:
  10.000 -> 9.800 moedas, carta de instância 4 no slot. As duas tentativas
  posteriores foram `Typ_Buy` (`typ=3`) para a oferta 2, enquanto o slot 4
  estava ocupado; o handler antigo respondeu com `error=1`. Isso coincide com
  o aviso genérico “Erro de banco de dados”, mas não é evidência de arquivo de
  inventário/banco corrompido.
- O mesmo trace não contém requisição `Typ_Use` (`typ=2`). Portanto, ele prova
  a rejeição das compras seguintes, mas não revela se o clique de uso foi
  recusado pela interface ou se a requisição não chegou a ser emitida.
- O servidor local agora permite comprar outra carta de loja substituindo uma
  carta normal já guardada, sem permitir que essa compra descarte uma carta de
  pré-carga como o Cofrinho. O evento de compra também carrega
  `Card_Reason_Buy=1`. Um teste TCP verifica a substituição e o débito.
- O `cfgId=2008` está confirmado nas tabelas empacotadas como Alucinógeno
  (`skill_id=1007`): seleciona um inimigo vivo e o força a disparar contra si.
  O handler `Typ_Use` do laboratório consome o slot e inclui no mesmo
  `Type_Use_Card` os subeventos de tiro contra si; munição falsa não causa
  dano, real reduz HP. Um teste TCP cobre o ramo de munição real e a limpeza
  do slot.
- A suíte completa passa com 56 testes e `py_compile` passou. O servidor que já
  estava ativo durante a inspeção não foi reiniciado por mim; se ainda estiver
  rodando, mantém o código antigo carregado. A mudança só pode ser validada no
  cliente depois de reiniciar o servidor local. O teste atual comprova o
  protocolo em loopback, não a interface,
  animação ou chegada do clique `Typ_Use`.
- A nova inspeção do Lua `RouletteBattleWindow.OnPlayerSelect` encontrou um
  terceiro caminho de compra: ao escolher e mirar numa carta da loja, o cliente
  envia `Typ_Buy_And_Use=1`; `Typ_Buy=3` é especificamente guardar a carta. O
  `Typ_Use=2` é usado para um item que já está no slot. Isso explica uma causa
  concreta para “Erro de banco de dados” se o jogador tentava usar diretamente
  o Alucinógeno da loja: o handler anterior não atendia `typ=1`. É uma explicação
  compatível com o print, ainda não confirmada por um trace desse clique.
- Implementado `Typ_Buy_And_Use` para a oferta Alucinógeno `cfgId=2008`:
  valida estoque, saldo e alvo; cobra 200 moedas; marca a oferta vendida;
  executa o tiro forçado e preserva qualquer carta que já estivesse guardada.
  Tanto esse caminho quanto `Typ_Use` agora colocam os subeventos do tiro
  (`Enum_Shoot` e `Enum_Finally_Source`) dentro do mesmo resultado da carta,
  sequência exigida pelo Lua `UseCard -> StartShootOnce`; removida a notificação
  `Type_Shoot` separada que podia desencontrar a animação e o estado.
- Dois testes TCP verificam os caminhos de uso guardado e compra-e-uso: ACK sem
  erro, alvo atirando em si, HP/munição atualizados, slot/loja e moedas corretos,
  além da ausência de segundo tiro top-level. `py_compile` e a suíte completa
  passaram com **57 testes**. Continua pendente a validação visual no cliente;
  o erro da captura não contém pacote e não prova, por si só, que esta era a
  única causa.

### Número “0” indevido no item — 2026-09-23

- A captura do usuário mostra “0” amarelo sobre cartas/itens; ele esclareceu que
  o jogo original não exibia contador em nenhum desses itens. Tratar isso como
  defeito visual do emulador, não como quantidade legítima.
- A origem foi confirmada no Lua do bundle original:
  `RouletteGamePlayerNameBoard:SetCardSlot` exibe `_text_card_arg` quando
  `Card.arg_one >= 0` e o oculta quando negativo. O comentário do descritor
  protobuf define `arg_one` como “valor acumulado de moedas”; não é contagem
  genérica. Omitir esse escalar opcional faz o cliente decodificar `0`, logo
  cartas comuns exibiam o zero. `_Obj_SelectPropsItem` e `_RouletteCardItem`
  também desativam `_Txt_ItemCount` na lista genérica de cartas.
- Corrigido `pvp_card_slot_body`: agora codifica `arg_one=-1` por padrão para
  cartas comuns, para o cliente ocultar o campo; valores explícitos não-negativos
  continuam disponíveis para mecanismos que realmente exibem saldo, como o
  Cofrinho. O slot vazio já usava `-1`. Testes TCP foram ampliados para conferir
  o sentinela tanto no evento de compra quanto no `PvpGamer.CardSlot` e durante
  o uso.
- Na sessão manual `packet-trace-20260923-155310.jsonl`, o servidor antigo
  aceitou a compra/armazenamento do Alucinógeno e depois duas substituições de
  carta. Até 16:08:25 local, o log não contém `Typ_Use`; portanto, a animação e
  o efeito de uso ainda não foram validados nessa partida. Até 16:11:35 local
  também não há requisição identificável de uso (`Typ_Use=2`) nem compra-e-uso
  (`Typ_Buy_And_Use=1`). A compra inicial de `cfgId=2008` e as substituições
  sucessivas por `cfgId=2003` e `cfgId=2001` foram aceitas, com débitos de 200,
  200 e 100 moedas; evidência live de que o caminho de guardar/substituir está
  funcionando no cliente.
- Ao retomar em 2026-09-23, não havia processo do jogo nem servidor escutando;
  `py_compile` passou e os 57 testes da suíte passaram novamente. Subi a versão
  atualizada do servidor (v14, `length-mode=body`) somente em loopback; o health
  respondeu `ok=true` e as portas 38000/38001/38002 estão vinculadas a
  `127.0.0.1`. O trace desta sessão é
  `private-server/packet-trace-resume-20260923.jsonl`. Não abri nem controlei o
  cliente. A correção `arg_one=-1` ainda precisa de confirmação visual manual;
  uso/animação do Alucinógeno também continuam sem validação na tela.

### Inicialização de munição e ciclo visual do tiro — 2026-09-23

- Extraí, de forma somente-leitura do bundle da cópia, 15 TextAssets relevantes
  para uma pasta de contrato de batalha. O script reproduzível é
  `tools/extract_battle_lua.py`; não altera o `lua.ab`.
- No cliente, o callback PVP `255/7` é `NotifyPvpGamerAmmo`: `OnGameInit`
  define `gameInitInfo`, e `RouletteBattleWindow:OnGameStart` usa
  `gameInitInfo.pvpInfo.gamers` para chamar `SetAmmo` nas armas dos jogadores.
  O servidor local anterior ao ajuste enviava somente o turno `255/1` após
  `3/14`; isso deixava sem execução o caminho explícito de inicialização da HUD
  e do carregamento visual de munição.
- Corrigi a sequência de `3/14`: agora ela responde o gamer-load, notifica
  `255/7` com o `PvpInfo` já conhecido e só então envia `255/1`. O campo
  opcional `ammoBank` foi deliberadamente omitido: o descritor o chama de
  reservatório anterior ao carregamento, mas o conteúdo inicial específico do
  modo ainda não foi comprovado.
- Teste TCP confirma a ordem, os três combatentes e as pilhas iniciais extraídas
  do próprio snapshot (2 falsas cfg 300 + 4 reais cfg 1); nenhuma munição de
  reserva é inventada. `py_compile` e os 57 testes passaram. Isso prova o fio,
  não a animação na tela.
- Após os testes, a instância foi reiniciada já com esse ajuste e com o contrato
  `arg_one=-1` para cartas comuns. Em 2026-09-23 18:18 local, a health check
  respondeu `ok=true`, v14; as três portas seguem somente em `127.0.0.1`.
  O trace novo, `private-server/packet-trace-resume-20260923-initammo.jsonl`,
  contém apenas `trace-start` até esta atualização: nenhum cliente conectou,
  então não há evidência de renderização no jogo.
- A leitura do fluxo de tiro confirmou que `OnFire` consome localmente o cfg de
  munição do evento, aplica `rAmmo` completo e depois o efeito/HP do alvo; o
  nameboard usa animação temporizada para remover balas. Isso estreita a análise
  da HUD que pisca/inverte, mas a causa final depende de comparar um trace real
  da sessão com o que a animação mostrou.
- O Lua também confirma o contrato visual dos bots: notificação `255/4`, ação 1
  levanta a arma (`PortGun`), ação 4 escolhe/alinha o alvo (`Chose`, `tIdx`) e
  ação 2 abaixa a arma. O escalonador local envia levantar + mirar antes do
  resultado do disparo; isso está coberto pelo caminho de código/testes, porém
  continua sem confirmação visual até haver uma sessão conectada.

### Reconciliação com trace de gameplay anterior — 2026-09-23

- Reanalisei `private-server/packet-trace-20260923-155310.jsonl` (trace do
  servidor antigo, antes do envio de `255/7`). O cliente pediu um único tiro
  (`3/3`, alvo 0). O resultado `255/2` também marca fonte/alvo 0, cfg 1 (real),
  `rAmmo` de 4 para 3 reais e HP de 4 para 3; o `PvpInfo` no mesmo pacote tem
  exatamente esses novos valores. Nesse evento, direção, dano e estado de
  munição são coerentes no fio.
- A sequência continuou: bot índice 1 recebeu turno em duas fases, enviou
  `255/4` ação 1 e ação 4 mirando o jogador 0, e disparou cfg 300 (falsa),
  reduzindo sua pilha de 2 para 1 sem dano. O bot índice 2 repetiu as poses,
  disparou cfg 1, reduziu a própria pilha real de 4 para 3 e o HP do jogador de
  3 para 2. Por fim, `255/1` devolveu o turno ativo ao índice 0 na rodada 2.
- Há somente um pedido de tiro do cliente após o início da partida; portanto o
  trace comprova a sequência escrita pelo servidor e o retorno de turno, mas
  não registra uma tentativa posterior do jogador. Não comprova que o cliente
  recebeu/renderizou cada pose, nem explica sozinho o relato de controles
  travados. O pacote inicial continha `255/1`, mas não `255/7`; o ajuste novo
  para inicializar munição ainda precisa de validação visual/live.
- O cliente descarta outlines cujo `uTime` seja anterior ao último estado
  aplicado. Neste trace, os horários dos eventos de tiro e das fases de turno
  avançam ou empatam, sem retroceder; não há evidência de descarte por tempo.
- `ammoBank` é separado do pente (`rAmmo`): o cliente substitui a reserva e
  atualiza sua UI quando o campo chega em um evento de tiro. Como o emulador o
  omite sem conhecer a reserva original, essa parte da HUD ainda não é fiel;
  isso não contradiz os valores corretos do pente vistos no trace.
- Importante: `2` falsas + `4` reais é a composição que o laboratório enviou,
  não uma regra oficial descoberta no cliente. `ammo_cfg` identifica tipo e
  ordenação; `PvpModeCfg` não declara a quantidade inicial. Sem uma partida
  original capturada, essa composição continua uma escolha de emulação.

### Resultado, identidade local e auditoria dos eventos de tiro — 2026-09-23

- Decodifiquei os eventos `255/2` das três capturas históricas de gameplay,
  incluindo os campos aninhados da bala e do pente. Em todas elas, cfg `1`
  (real) aparece com `hp=-1` no alvo e reduz a pilha real em `rAmmo`; cfg `300`
  (falsa) aparece com `hp=0` e reduz a pilha falsa. Os índices de origem/alvo
  também correspondem aos tiros pedidos/turnos registrados. Isso confirma
  coerência dos pacotes antigos, não a animação/HUD que o cliente renderizou.
- No Lua, o cliente acha o jogador local comparando `PvpGamer.base.gid` com
  `GL.Data.Gamer.id`; a instância principal recebe o `serverIndex` desse
  `PvpGamer`, e seu `teamID` começa em `base.campIdx`. A tela de resultado marca
  vitória quando um gamer de rank 1 pertence ao mesmo `campIdx` da instância
  principal.
- O `255/5` da captura `packet-trace-20260922-233656.jsonl` foi decodificado:
  `pvpMode=1`, dois participantes (formato do servidor antigo), local `gid=1000002`
  no índice 0/camp 0/HP 0/morto/rank 2 e bot no índice 1/camp 1/HP 4/rank 1.
  Esses dados devem produzir derrota no código de resultado do cliente. Portanto,
  este trace não prova a vitória incorreta relatada em outra sessão; falta o
  trace que corresponda exatamente à tela em que isso ocorreu.
- O handler normal de `255/2` não aplica o `pvpInfo` completo recebido no mesmo
  pacote (a aplicação ocorre em fluxos especiais, como Arcade). Para tiro
  comum, o cliente processa `events` e animação; no callback `OnFire`, consome
  localmente `source.ammo.cfgId`, aplica o `source.rAmmo` pós-tiro e depois o
  delta de HP do alvo. Assim, não há evidência de que um snapshot completo
  anterior à animação esteja causando a inversão temporária da HUD.
- A falha visual continua aberta: os registros históricos são de builds antes
  do envio `255/7` e todos os tiros neles têm cfg, lista pós-tiro e delta de HP
  coerentes. O trace v14 `packet-trace-resume-20260923-initammo.jsonl` ainda tem
  somente `trace-start`; não houve cliente conectado desde a inicialização de
  munição. A próxima reprodução precisa casar, no mesmo tiro, cfg exibido,
  pilhas `rAmmo` antes/depois, estado de HP e imagem observada.

### Validação manual conectada — tiro falso no próprio jogador — 2026-09-23

- Atualização: a afirmação acima de que o trace v14 ainda continha apenas
  `trace-start` ficou obsoleta assim que o cliente foi aberto. O arquivo agora
  registra a sessão iniciada pelo launcher da cópia.
- No primeiro tiro relatado pelo usuário, o cliente enviou `cmd=3/act=3`,
  `idx=0` (autoalvo). O servidor respondeu com evento de tiro `255/2`,
  `event_id=1`, origem/alvo 0, `ammo_cfg=300` (falsa) e lista posterior do
  pente `[cfg 300: 1, cfg 1: 4]`. O usuário confirmou visualmente que foi falsa
  e que a munição foi contabilizada. O evento não traz delta de HP no alvo;
  portanto, o pacote do tiro local é coerente com um auto-tiro falso.
- O mesmo ciclo de turno contém os eventos seguintes: bot índice 1 disparou
  `cfg=1` no jogador 0 (`hp=-1`, reais 4→3), e depois bot índice 2 também
  disparou `cfg=1` no jogador 0 (`hp=-1`, reais 4→3). Isso explica a queda
  observada pelo estado interno de HP 4→2: são dois acertos dos bots, não dano
  da bala falsa do auto-tiro.
- O trace registra notificações `255/4` para preparar/apontar os bots antes
  dos eventos de tiro; isso prova que os pacotes de pose foram enviados, mas
  ainda não prova como as animações foram renderizadas na tela.
- Intervalos observados entre tiros: jogador→bot 1 ≈8,05 s e bot 1→bot 2
  ≈8,05 s. O próximo pedido de tiro do cliente chegou depois, mirando índice
  2, e foi registrado como falsa (`cfg 300`, pilha falsa 1→0, sem delta de HP).
  Isso mostra que a sessão continuou recebendo uma nova ação do cliente, mas
  a espera entre turnos ainda merece avaliação de jogabilidade.
- Evidência principal: `private-server/packet-trace-resume-20260923-initammo.jsonl`.
  O relato visual confirma tipo de munição e contagem do primeiro tiro; falta
  confirmar se a HUD permaneceu estável, se as duas animações dos bots foram
  vistas e se a espera de ~8 s por bot parece correta no jogo.

### Abertura da partida: cadência das animações — 2026-09-23

- Nova observação manual do usuário: as animações agora parecem sincronizadas,
  porém rápidas demais; a munição surge na mesa e a recarga parece começar sem
  o intervalo/cooldown esperado.
- No Lua extraído, a sequência de `OnGameStart_New` é explícita: `SetAllPlayerStartAmmo`
  no instante inicial; `StartShowAmmoUI` após 1 s; `StartSetPlayerAmmo` após mais
  3 s (chama `SetAmmo(..., true)` e, portanto, a animação de recarga); `playerInit`
  após mais 2 s; e fechamento da abertura após mais 5 s. Valores derivados do
  código do cliente: ~4 s da munição na mesa à recarga e ~11 s até liberar o fim
  da abertura. Não encontrei ainda um parâmetro de servidor que altere os timers
  internos dessas etapas.
- No trace v14 anterior, `255/7` (inicialização de munição) e `255/1` (primeiro
  turno ativo) foram enviados no mesmo instante. O handler do cliente para
  `255/1` troca jogador ativo e abre UI de tiro/mira imediatamente; não aguarda
  `IsGameIniting`. Isso é uma sobreposição de eventos comprovável e pode expor
  os controles enquanto a abertura ainda toca, mas não prova que o temporizador
  interno de recarga tenha sido encurtado.
- Correção preparada em `private-server/server.py` (build local v15): manter `255/7` imediato e
  enviar `255/1` após 11 s, alinhado à soma dos temporizadores da abertura; o
  estado do servidor também rejeita ação do jogador antes desse prazo. O intervalo
  interno mesa→recarga continua o do cliente (~4 s); não aumentei esse tempo sem
  referência observável do jogo original.
- O teste de protocolo agora verifica que `255/1` chega depois de `255/7` com o
  atraso configurado. Sintaxe e os 57 testes passaram após a mudança. Após o
  usuário confirmar que o jogo estava aberto sem partida e autorizar o fechamento,
  reiniciei somente a cópia: o endpoint de saúde respondeu versão 15, e o launcher
  e `Client.exe` da cópia foram reabertos. Trace novo:
  `private-server/packet-trace-20260923-192555.jsonl`. A validação visual da nova
  abertura ainda aguarda o teste manual; a instalação original não foi tocada.

### Objeto dourado congelado em todos os participantes — 2026-09-23

- Observação do usuário: o jogador local e todos os NPCs exibem o mesmo objeto
  dourado semelhante a uma bolsa/cofrinho; ele parece parado e não responde ao
  clique. O recorte enviado não permite identificar o asset com certeza.
- No trace ativo da cópia, a partida requisitada é `mode=1/subMode=6`, com
  `hero=0` e `carriedCard=3`. A configuração local de `pvp_login_snapshot`
  dá 10.000 moedas aos três participantes nesse modo e ativa as flags globais
  `isShowCardSlot` e `isShowPlayerCoin`. `card=3` não é o Cofrinho; o helper só
  cria `CardSlot` para os cfg IDs `34/1034/2034`. O snapshot capturado não tem
  `CardSlot` em nenhum dos três jogadores.
- O caminho confirmado no cliente separa os conceitos: `SetCoin` chama
  `UpdatePlayerCoin` (gated por `isShowPlayerCoin`), enquanto `SetCardSlot`
  encaminha um item para `PlayerCardShow`. No teste visual de diagnóstico em que
  `isShowPlayerCoin=0`, a bolsa dourada permaneceu. Portanto, a hipótese de que
  ela seja somente o visual do saldo inicial está descartada: essa flag, sozinha,
  não controla o objeto observado. O snapshot sem `CardSlot` também não prova que
  seja o Cofrinho. A ligação visual exata continua desconhecida porque o corpo
  nativo de `SceneController:UpdatePlayerCoin` não está no dump IL2CPP; comparar
  slot vazio com um Cofrinho real e inspecionar o prefab/efeito ainda são passos
  necessários.
- Sobre o ritmo: o cliente inicia a recarga aproximadamente 4 s após a munição
  aparecer na mesa; o v15 apenas segura o primeiro turno ativo até 11 s. O
  usuário relata que a recarga ficou melhor, mas ainda começa um pouco cedo.
  Falta medir o intervalo que ele considera correto; não há alteração cliente
  de cadência feita nesta etapa.

### Seletor de alvo compartilhado para itens — 2026-09-23

- Confirmação do usuário: alucinógeno, injetor de munição e munições real/falsa
  usam o mesmo padrão de setas por jogador; a diferença esperada está no efeito
  depois da escolha do alvo.
- O Lua embarcado confirma o fluxo comum: `OnClickCardSlot` ou `OnShopItemClick`
  chama `ShowCurSelectCardInfo`; quando `IsCanUseItem` aceita o item, a rotina
  chama `OnUseBtnClick(true)`, que prepara os botões via `ShowCurSelectBtn` e
  abre `_obj_PlayerSelect`. O seletor lê `target_typ/target_num`; a animação e
  aplicação do efeito são uma etapa posterior roteada por `skill_typ` em
  `ClientAnimExpression.UseCard`.
- No trace v2 `private-server/packet-trace-20260923-201910.jsonl`, foram
  capturados 14 pedidos `3/4` alternando escolha do item de loja `id=4` e
  cancelamento `-1`, sem pedido `3/5` de uso. O estado publicado nesses pedidos
  indica `player_card_cfg=0`; portanto, a captura prova cancelamento no fluxo da
  loja, mas não uma tentativa de uso de item já guardado.
- Patch Lua experimental v3: esconde o painel de detalhes sempre que o fluxo
  comum entrou em seleção de alvo, não apenas ao clicar em item guardado. A
  hipótese é que o painel sobreposto impedia o clique nos alvos. A cópia foi
  instalada com SHA-256 `DBD4B0ECC026F271849DAF96F33C377AE0C406ED809777E2A3C6DB0FFA7DD284`;
  rollback v2 permanece em `private-server/rollback/2026-09-23-pre-item-target-ui/lua-item-target-ui-v2.ab`.
  O hash da instalação original continua `C534E0DFE86910F4F0E41D5F24F52EBCD7CD4C5CA93E56F325CE9205D870BB54`.
- Validação local: `py_compile` e 58 testes passaram, incluindo compra/uso do
  alucinógeno no contrato do servidor. Isso não valida renderização/clique: a
  sessão aberta após instalar v3 ainda não conectou ao PVP (trace novo só contém
  a inicialização). Próximo passo: entrar manualmente em uma partida local e
  verificar se as setas aparecem; depois confirmar no trace se o alvo gera
  `Typ_Use`/`Typ_Buy_And_Use`. O servidor ainda precisa de handlers específicos
  para itens além dos efeitos já reconstruídos.

### Erro de banco ao substituir item após renovar a loja — 2026-09-23

- No trace `private-server/packet-trace-20260923-203739.jsonl`, o cliente
  armazenou a oferta `id=4/cfg=2008` com sucesso; depois renovou a loja e pagou
  300 moedas. A renovação publicou quatro novas ofertas com IDs `5..8`. Na
  tentativa seguinte de substituir o item, o cliente enviou `id=3`; o servidor
  não encontrou essa oferta no estoque atual (`status=0`, `price=0`) e devolveu
  `header.error=1`, que aparece no jogo como “Erro de banco de dados”.
- Causa concreta no protocolo gerado pelo laboratório: `_pvp_card_small_event`
  serializava a lista `cards` no campo protobuf `32`. O schema `pvp_pb.lua`
  embarcado no cliente declara `PvpEventOutline.cards` no campo `42`; portanto,
  a lista renovada não era entregue no campo que o cliente reconhece e a seleção
  podia continuar usando IDs antigos. Corrigido em `private-server/protocol.py`.
- Regressão ampliada em `private-server/tests/test_protocol.py`: verifica que o
  evento de renovação contém as quatro cartas em `target.cards` (campo `42`),
  não no campo `32`, e que uma compra pós-renovação substitui o item guardado
  sem rejeição. `py_compile` e os 58 testes passaram.
- A sessão da captura estava usando o servidor anterior, já carregado em
  memória. Reiniciei somente o laboratório copiado após o patch: health v15 OK,
  jogo reaberto e novo trace `private-server/packet-trace-20260923-205631.jsonl`.
- No novo trace, a compra `id=4/cfg=2008` foi aceita e, em seguida, a troca pela
  oferta `id=3/cfg=2004` também foi aceita; saldo `9800→9700` e log
  `replacedSlot=4/2008`, sem erro de banco. Isso valida a troca normal no cliente
  real, mas ainda não a renovação: nesta sessão não há evento `shop refreshed`.
  Falta renovar a loja, escolher uma oferta nova e repetir a substituição; a
  instalação original não foi alterada.

### Setas de alvo ausentes no modo offline com bots — 2026-09-23

- O print do usuário mostra a seleção do item `Bala Falsa +1` e o aviso para
  escolher um jogador, mas nenhuma seta/alvo sobre os participantes. O trace
  anterior não contém requisição de uso `cmd=3/act=5`; portanto, o clique de
  escolha de alvo não chegou ao servidor.
- A causa encontrada foi uma diferença entre janelas de jogo: o modo local com
  bots usa `RouletteBattleWindow_Single` (confirmado em `Lua%UIGroup`), não
  `RouletteBattleWindow`. O patch experimental v3 tratava a segunda janela e,
  por isso, não corrigia essa partida offline.
- No prefab `RouletteBattleWindow_Single`, `_Btn_PlayerSelect1..4` e
  `_obj_PlayerSelect` são descendentes de `_obj_GuideWindow02`, que começa
  inativo. O método `RouletteBattleWindow_Single:ShowPlayerSelect` ativa apenas
  `_obj_PlayerSelect`; não ativa o ancestral. Assim, o prompt/máscara de seleção
  pode aparecer sem que os botões de alvo sejam renderizados. A função de alvo
  (`ShowCurSelectBtn`) já calcula os alvos por `target_typ` e ativa os botões;
  para cfg `2004` / skill `1003`, a configuração indica `target_typ=3`,
  `target_num=1`, que inclui os participantes elegíveis, inclusive o jogador.
- Criado `private-server/patch_single_item_target_ui.py`. Ele altera apenas o
  TextAsset `Lua%RouletteBattleWindow_Single` na cópia: ao abrir o seletor,
  habilita temporariamente `_obj_GuideWindow02`, registra o estado anterior e
  o restaura ao fechar. Bundle de saída passou pela reextração/validação do
  UnityPy e `py_compile`.
- Patch instalado na cópia com SHA-256
  `688B965184F5F1562F99EA38002FCA654B1641AE3FFAD8C35A57C3B07AF460B8`.
  Rollback do bundle anterior: `private-server/rollback/2026-09-23-pre-item-target-ui/lua-item-target-ui-v3-before-single-parent.ab`.
  A instalação Steam original continua com SHA-256
  `C534E0DFE86910F4F0E41D5F24F52EBCD7CD4C5CA93E56F325CE9205D870BB54`.
- Fechei graciosamente o `Client.exe` da cópia para instalar o bundle e reiniciei
  somente o laboratório. Health responde servidor v15; novo trace:
  `private-server/packet-trace-20260923-211556.jsonl`. O novo cliente conectou
  e recebeu snapshot de três participantes, mas a confirmação visual da seta e
  a requisição `cmd=3/act=5` após clique ainda dependem do teste manual. Não
  considerar o uso de itens resolvido até essa validação e a confirmação do
  efeito no servidor.

### Reavaliação do caminho de uso, ícone de compra e bolsa visual — 2026-09-24

- Corrijo a conclusão anterior sobre a janela ativa: o mapeamento em
  `Lua%UIGroup` prova que existe uma janela Single para o tutorial/local, mas
  não prova que ela foi usada neste teste. O log da sessão real registra
  `mode=1/subMode=6`, snapshot PVP de três jogadores e pedidos PVP de compra;
  portanto, o caminho desta partida é o `RouletteBattleWindow` de rede local.
  O defeito de ID descoberto no caminho Single continua documentado, mas não
  deve ser tratado como causa desta partida sem evidência de que essa janela
  estava aberta.
- Causa de UI reproduzível por leitura do código: ao clicar em **Usar**,
  `RouletteBattleWindow:OnUseBtnClick` chamava `ShowCurSelectBtn()` mas deixava
  ativo o painel `_obj_UseCard` (a chamada que o esconderia estava comentada).
  O painel de detalhes pode ficar à frente dos botões de alvo e interceptar o
  clique. O patch anterior cobria somente a seleção automática, não o clique
  explícito no botão **Usar**.
- Corrigido somente na cópia em
  `private-server/patch_live_item_target_ui.py`: agora o callback explícito
  oculta o painel depois de ativar os alvos. Saída de pesquisa serializada e
  reextraída com UnityPy; `py_compile` passou. Instalado com backup
  `private-server/rollback/2026-09-23-live-item-target-ui/lua-before-live-item-target-fix.ab`.
  Bundle da cópia: SHA-256
  `EAB3556E487907FE6CE5537461F2067BC89EBAC918FCE69C780FA63E9FA1A6B6`.
  Resultado visual/clique ainda requer teste manual em partida.
- Reanalisei o evento de guardar item na captura. O pedido `cmd=3/act=5` tinha
  `action_type=3` (guardar), oferta `id=4`; o evento do servidor informa
  `Type_Buy_Card`, `uniqueId=4`, e `card.cfgId=2008`. O evento aninhado
  `Enum_Card_Slot` carrega `id=4`, `cfgId=2008` e `arg_one=-1`; os campos batem
  com o schema extraído do cliente. Assim, o ícone vazio não é explicado por
  ID/config ausente no pacote; resta localizar a etapa de renderização/asset
  no cliente e validar se a notificação citada é a animação de compra ou o slot.
- O bug de identificadores do caminho Single é específico e confirmado no
  código embarcado: `OnPlayerSelect` passa `curSelectShopItem.id` para um
  método que pesquisa `card_cfg` e compara a loja por `cfgId`. No modo Single
  nativo, a lista criada por `UpdateShopItems_ID` usa `id=cfgId`, mas uma oferta
  PVP de servidor pode usar `id` de oferta diferente de `cfgId` (ex.: `4/2008`).
  Não alterar a rota PVP padrão: nela o cliente deve enviar o ID de oferta, que
  o servidor associa ao `cfgId`.
- A bolsa dourada congelada continua sem causa comprovada. Ela é uma trilha
  separada; nem o evento correto do cartão guardado nem o snapshot de três
  jogadores identificam sua origem. Não atribuir ao cofrinho/carried card até
  comparar o primeiro snapshot de jogador, estado do card slot e efeito visual.
- Instalação original preservada e revalidada: `lua.ab` SHA-256
  `C534E0DFE86910F4F0E41D5F24F52EBCD7CD4C5CA93E56F325CE9205D870BB54`.

### Causa confirmada para as setas de itens ausentes — 2026-09-23

- A instrumentação temporária do cliente na partida real registrou seleção de
  `cfgId=2004` / skill `1003`, `target_typ=3`, `target_num=1`, painel seletor
  visível, mas todos os botões de alvo inativos. Os três participantes tinham
  `hp=4` e `state=1`; `IsCanSelect(true, ...)` devolveu `false` para cada um.
  A hipótese de painel ancestral invisível ou de sobreposição **não explica**
  esta sessão e o patch experimental de visibilidade foi retirado da cópia.
- O contrato extraído do cliente identifica `PvpGamer.pvpGamerState` como campo
  protobuf 27; `State_Normal=0` e `State_Grave_Mound=1`. Em
  `RouletteGamePlayer:IsCanSelect`, `State_Grave_Mound` é sempre rejeitado para
  alvo de item. Já o campo 10 é outro enum (`PvpGamerStatus`) e valor 2 indica
  participante em partida. O servidor local emitia incorretamente campo 27 = 1
  para **todos** os jogadores no snapshot inicial, apesar de vida positiva.
- Corrigido em `private-server/protocol.py`: `_local_pvp_gamer` agora emite
  campo 27 = 0, mantendo campo 10 = 2. Adicionada regressão em
  `private-server/tests/test_protocol.py`; 58 testes passaram. Servidor e
  cliente da cópia reiniciados; trace da nova sessão:
  `private-server/packet-trace-20260923-220939.jsonl`. A confirmação visual
  das setas e o efeito do item ainda aguardam teste manual nesta sessão.
- A instrumentação `[HR_TARGET_DIAG]` permanece **temporariamente** no bundle
  da cópia para confirmar o estado e os cliques. Não declarar o uso de itens
  resolvido até verificar `cmd=3/act=5`, atualização de estado e efeito visual;
  retirar a instrumentação depois de obter a evidência necessária.

### Setas confirmadas; uso de Alucinógeno corrigido no laboratório — 2026-09-23

- Na primeira partida após corrigir `PvpGamerState`, o diagnóstico real mostrou
  os três participantes com `state=0`, `hp=4`, `IsCanSelect=true`; os botões de
  alvo foram habilitados e `OnPlayerSelect` recebeu cliques para índices 1 e 2.
  O usuário confirmou visualmente que as setas apareceram pela primeira vez.
- Trace `packet-trace-20260923-220939.jsonl`: uso comprado do Alucinógeno em
  si mesmo (`id=4`, `target=0`, `action_type=1`) retornou erro 1; o mesmo item
  no bot (`target=1`) retornou sucesso. O servidor restringia erradamente o
  alvo a `(1,2)`, embora o cliente envie `0` ao escolher o próprio jogador.
- No uso aceito no bot, o servidor sorteou munição falsa (`cfg=300`), portanto
  a vida permaneceu 4. Porém o cliente também registrou exceção Lua em
  `ClientAnimExpression.AddOtherEvent`: tentativa de concatenar
  `event.source.typ` ausente. O evento de moeda emitido pelo servidor tinha
  `target.typ=Enum_Coin` mas omitira `source.typ`; isso interrompia a animação.
- Corrigidos `server.py` e `protocol.py`: ambos os caminhos de Alucinógeno
  (comprar+usar e usar do slot) aceitam alvo 0; o snapshot de si mesmo conserva
  vida/munição após o tiro; `_pvp_card_small_event` preenche `source.typ`.
  Ampliados testes para validar o tipo de origem e uso em si mesmo. **59 testes
  passaram**. Nova sessão da cópia:
  `private-server/packet-trace-20260923-221930.jsonl`. Efeito visual real e
  uso de outros itens continuam pendentes da próxima verificação manual.

### Ponto de pausa: Bala Real +1 — 2026-09-23

- O usuário confirmou **em jogo** que o Alucinógeno usado em si mesmo funcionou
  e manteve corretamente o turno. Trace `packet-trace-20260923-221930.jsonl`:
  oferta 4 / cfg 2008 / alvo 0 / action 1 aceita; tiro real reduziu vida 4→3,
  consumiu uma bala real e descontou 200 moedas. A tentativa seguinte de Bala
  Real +1 (oferta 2 / cfg 2003 / alvo 0) foi rejeitada pela antiga rota que
  suportava apenas Alucinógeno; isso produziu o aviso “Erro de banco de dados”.
- Extraído **sem modificar** `fight_dbconfig.ab` da cópia: `card_cfg` liga
  cfg 2003 à skill 1002, ícone `UI_Fight_Itemicon_real bullet`; `skill_cfg`
  declara `target_typ=3`, `target_num=1`, `skill_typ=3` (ChangeAmmo). O cliente
  chama `ClientAnimExpression.ChangeAmmo` e aplica eventos pequenos em
  `ShowUIChange`. O tipo `Enum_AddFixed_Ammo=21` adiciona o projétil e exige
  `ammo` + lista completa `rAmmo` para atualizar contagem/posição na HUD.
- Implementado **somente para Bala Real +1** (`cfg 2003`): comprar+usar no
  alvo e usar do slot guardado aceitam participante vivo, inclusive você;
  acrescentam uma bala real, atualizam snapshot do alvo, saldo/oferta ou slot,
  e emitem `Type_Buy_Use_Card` ou `Type_Use_Card` com evento 21. O item de
  descartar munição e a Bala Falsa +1 **não foram implementados nesta etapa**.
- Teste integrado de protocolo percorre ambos os fluxos (imediato em você,
  guardado em bot) e verifica resposta, eventos, saldo, slot e munição final.
  `python -m unittest discover -s tests -p test_protocol.py`: **60 testes OK**.
  Isso comprova o servidor/protocolo local, **não** a animação visual no jogo.
- Servidor e cópia reiniciados com essa versão, portas 38000–38002 ativas;
  trace da nova sessão: `private-server/packet-trace-20260923-223140.jsonl`.
  Bundle Lua da cópia ainda contém diagnóstico temporário de alvos (SHA-256
  `76A629BC1A65FAEF7B41D01650386E8AFA5BDCC9C5D14BECBED4321DFF4E5511`);
  instalação original preservada (SHA-256
  `C534E0DFE86910F4F0E41D5F24F52EBCD7CD4C5CA93E56F325CE9205D870BB54`).
- **Retomar daqui:** pedir teste manual de comprar e usar Bala Real +1 em si
  mesmo após consumir pelo menos uma bala. Conferir animação, HUD e log/trace
  desta sessão; se falhar, investigar a sequência `ChangeAmmo`/evento 21.
  Depois validar o uso do slot, retirar a instrumentação Lua temporária e só
  então reconstruir Bala Falsa +1 e o item de descartar munição.

### Continuação dos itens: Bala Falsa, Extrator e Cigarro Molhado — 2026-09-23

- O jogador confirmou visualmente que Bala Real +1 e Bala Falsa +1 funcionam.
  O último trace confirmou Bala Falsa `cfg 2004` comprada e usada no próprio
  jogador: cartucho falso 2→3, moeda 9800→9700. A rota de Bala Falsa usa o
  mesmo contrato `Enum_AddFixed_Ammo=21` da Bala Real, mas munição cfg 300.
- Extrator `cfg 2001` implementado nas rotas comprar+usar e usar do slot.
  O servidor sorteia um cartucho presente, decrementa o tipo sorteado e
  emite `Enum_Pop_Ammo=13` com `uAmmo`; a origem do pequeno evento aponta para
  o alvo porque o Lua indexa a animação de descarte por `source.Idx`.
  Testes de protocolo passaram, mas **a animação ainda não foi confirmada**
  pelo jogador. Não marcar como finalizado até essa verificação.
- Extraído catálogo de 34 `card_cfg` do cliente: 26 itens comuns no recorte
  relatado pelo jogador, excluindo Bolsa de Sangue e cartas de pôquer.
  Ver `ITEM_CATALOG.md`. A loja inicial oferece apenas quatro itens; a
  expansão da loja deve acompanhar a implementação real dos efeitos.
- Cigarro Molhado `cfg 2011` implementado no laboratório. O cliente usa
  `skill_typ=6`/Lucky; o servidor emite `Enum_Update_Luck=7` com resultado de
  dado 1–6 e `isSuccess`, seguido por `Enum_Heal=20` quando resultado ≥4 e
  HP<4. O snapshot de HP, oferta e slot é atualizado. As variantes 2024 e
  2027 têm o mesmo construtor de pacote, mas ainda não são ofertadas. A
  primeira atualização da loja pode mostrar 2011. Foram validados uso
  imediato e uso guardado em teste de rede, além do pacote de cura:
  **62 testes passaram**. Animação/dado/cura reais ainda pendem de teste
  manual. O preço de 100 moedas é experimental, não comprovado como original.
- Teste manual de 23:06 mostrou o Extrator aceito pelo servidor: cfg 2001,
  alvo 0, bala real retirada, contagem real 4→3. O jogador ainda não confirmou
  se animação e HUD acompanharam. Ao atualizar a loja, o servidor devolveu
  quatro ofertas, mas o botão Atirar ficou oculto; `Player.log` registrou
  `skill_cfg id: -1` duas vezes. A rota de `Type_Gamer_Refresh_Shop=36`
  do cliente entra em animação de card sem `itemId`, busca skill inexistente e
  não aplica `Enum_Gamer_Refresh_Shop` nem reabre o tiro. Como correção
  **somente no servidor do laboratório**, a atualização agora usa
  `Type_System=11` com os mesmos pequenos eventos de moeda e estoque; o Lua
  chama `ShowUIChange` diretamente sem esconder o tiro. 62 testes passaram.
  Cópia/servidor reiniciados no trace `packet-trace-20260923-231046.jsonl`;
  falta validação manual do botão de atualizar e do Cigarro Molhado.
- No trace novo, atualizar a loja permitiu comprar o Cigarro Molhado
  (`cfg 2011`), portanto o estoque novo chegou ao cliente. O uso sorteou 2,
  falhou e não curou, coerente com HP cheio. O usuário mostrou em captura que
  uma oferta consumida permanecia “Vendido” após o turno mudar. A causa no
  laboratório era ausência de reposição: o snapshot da rodada seguinte
  preservava os mesmos `cards` com `status=2`.
- O cliente lê `NotifyGamerPvpNextRound.info.cards` e chama
  `RouletteGameModule.UpdateShopItems` em cada troca de jogador. O servidor
  agora substitui somente ofertas vendidas antes de construir essa
  notificação; preserva as não vendidas, IDs de oferta passam a ser
  monotônicos e não colidem com atualizações manuais. Teste integrado compra
  e usa o cigarro, atira, verifica na primeira rodada do bot a nova oferta
  no lugar da vendida e todas as ofertas com status 1. **63 testes passaram**.
- `card_cfg` da cópia mostrou que o preço do Cigarro Molhado é 200 (campo
  13), não 100; corrigido. O executável em teste ainda carrega a versão
  anterior até reiniciar cópia/servidor. Falta confirmação visual da reposição
  e da cura num uso com HP abaixo do máximo.
- Sessão `packet-trace-20260923-231745.jsonl`: Cigarro Molhado 2011 foi
  comprado e usado em si com dado 4; servidor registrou cura 3→4 e custo
  200, sem exceção Lua no trecho recente. **Jogador confirmou em jogo** a
  animação do dado e o HP recuperado. Outro item vendido também foi usado
  antes do tiro; na primeira troca para o bot o servidor registrou reposição
  de duas ofertas (`stock=[2003,2008,2011,2001]`). A confirmação visual da
  loja após essa troca ainda não chegou.

### Ponto de pausa: seleção aleatória da loja — 2026-09-23

- O jogador observou que a loja inicial parecia sempre igual. Confirmado no
  servidor local: a lista inicial era fixa e Atualizar usava rotação
  determinística. Os arquivos do cliente mostram os itens e preços, mas não
  as probabilidades do servidor original.
- Implementada seleção uniforme sem repetição de quatro dentre os cinco
  itens cujos efeitos já estão no laboratório (2001, 2003, 2004, 2008,
  2011). A lista inicial é gravada no `PvpInfo` retornado no login; Atualizar
  também sorteia nova ordem/conjunto, evitando resposta idêntica. Reposição
  de ofertas vendidas sorteia entre itens ausentes, sem recolocar
  imediatamente o mesmo item consumido quando existe alternativa. Preços
  vêm de `card_cfg` da cópia, inclusive Cigarro Molhado=200.
- Seis sorteios locais exibiram sequências variadas. Testes de protocolo e
  integração: **64 OK**. Isso valida código/pacotes, não a visualização do
  primeiro conjunto sorteado dentro do jogo.
- **Pausado a pedido do jogador.** A cópia/servidor que permaneceram abertos
  na sessão `packet-trace-20260923-231745.jsonl` carregam a versão anterior
  à mudança aleatória. Ao retomar, reiniciar somente a cópia laboratorial e
  seu servidor, testar a loja inicial em duas partidas e confirmar a
  reposição visual após comprar/usar + passar a vez. Não alterar o original.
- Pergunta pendente ao jogador: o Cigarro Molhado original podia escolher
  qualquer participante ou apenas si? `skill_cfg.target_typ=3` na variante
  2011 indica todos, embora a descrição inglesa diga “yourself”. As
  variantes 2024/2027 usam target_typ=1 (si), e 2025 (Alucinógeno variante)
  usa target_typ=2 (oponentes). Resolver isso antes de ampliar os alvos/loja.

### Retomada: contrato do Spare Magazine — 2026-09-24

- A leitura do cliente confirmou `cfg 2007 -> skill 1006 -> skill_typ=3`
  (ChangeAmmo). `ClientAnimExpression.ChangeAmmo` inicia o efeito de mesa e
  `RouletteGamePlayer.UpdatePlayerInfo` adia o tipo 12 até o intervalo de
  recarga; depois aplica `isReload`, a lista completa `rAmmo` e os pares
  `cAmmo.source -> cAmmo.target`.
- Implementado no servidor/protocolo da cópia o pacote de recarga para os
  fluxos comprar+usar e usar do slot. O estado local do alvo é atualizado e o
  slot é consumido no caminho guardado. O teste de pacote verifica skill 1006,
  evento 12, `isReload`, duas pilhas finais e os dois pares CAmmo. **65 testes
  passaram**.
- A implementação ainda não foi colocada na loja aleatória: os dados
  `ammoBank` do modo original não foram encontrados, então a recarga
  experimental (4 reais + 2 falsas) não deve entrar no fluxo normal sem teste
  manual e sem decisão explícita de aceitar essa regra local.
- Próximo ponto seguro: confirmar no jogo a lista/Atualizar da loja aleatória;
  depois decidir se o Spare Magazine entra como item de laboratório. Os itens
  2009, 2015, 2016, 2018, 2020–2033, 2036 e 2037 continuam pendentes, cada um
  com efeito distinto; “todos funcionando” ainda não é uma afirmação válida.

### Correção da atualização visual da loja — 2026-09-24

- O trace do servidor confirmou que Atualizar já estava emitindo listas novas
  de `cfgId` e IDs de oferta monotônicos (19 gerações, incluindo 2011). Logo,
  o problema observado não era sorteio no servidor.
- O Lua do cliente mostra que o evento `RefreshShop` usava a animação que
  calcula posições a partir dos cards antigos e redesenha os dados só depois
  de 0,4 s. Na cópia laboratorial, o branch foi ajustado para chamar o
  renderizador completo imediatamente (`UpdateWindowUI_Shop(false)`).
- Patch aplicado somente em `Game/Client_Data/.../LuaBundles/lua.ab`; backup e
  saída validada estão em
  `research/private-server/rollback/2026-09-24-shop-refresh-ui/`. O hash do
  bundle instalado é `435697678614072B4D5B6CD7FAE281F1810ECC29A0A2DE353E232FD5B9B46B4A`.
- A próxima validação manual é simples: iniciar uma partida, anotar os quatro
  nomes/ícones, clicar Atualizar uma vez e confirmar se pelo menos uma posição
  mostra um item diferente; depois comprar esse item. O servidor ainda deve
  registrar uma geração, quatro IDs novos e saldo menos 300.
- O log da rotação foi ampliado no servidor da cópia para registrar, além da
  geração/preço/saldo, a lista exata de `cfgId` e de IDs de oferta enviados.
  Assim, uma próxima divergência poderá ser classificada sem adivinhar: se o
  `cfg` mudar no log e não na tela, é renderização/cache do cliente; se não
  mudar no log, é seleção/estado do servidor.

### Variantes de cartas com contrato já reconstruído — 2026-09-24

- `cfgId=2024/2027` (Cigarro Molhado), `2025` (Alucinógeno) e `2026`
  (Ejector) já tinham construtores de pacote e handlers de uso guardado/compra
  direta no servidor, mas estavam deliberadamente fora da rotação.
- A cópia laboratorial agora inclui essas quatro variantes na seleção aleatória
  e na reposição de ofertas vendidas. Os preços usados são os campos `price`
  extraídos de `card_cfg` (200, 200, 100 e 200 respectivamente); isso não
  afirma que a ponderação original foi recuperada.
- `py_compile` e os testes TCP devem ser repetidos antes da próxima sessão. A
  validação que falta é visual: cada variante precisa mostrar seu ícone, abrir
  as setas corretas, consumir a carta e atualizar o estado sem erro.

### Correção do indicador visual do Burst Mode — 2026-09-24

- O print da comunidade Steam mostra outro modo de jogo, mas confirma a
  convenção visual: ícones de efeitos ativos ficam na placa junto ao nome,
  vida e munição, e o mouse mostra nome/descrição. No Lua do cliente, a placa
  lê `PvpGamer.buffs` (campo 8), busca cada `cfgId` em `buff_cfg` e usa
  `imgName`, `name`, `descripe` e `state` para compor ícone e tooltip.
- A leitura somente-leitura dos dados oficiais da cópia confirma a cadeia
  `card_cfg_steam 2016 -> skill_cfg_steam 1015 -> buff_cfg_steam 1015`.
  Esse buff usa `UI_Fight_bufficon_burstmode`, estado visível 1 e os textos
  portugueses LID 77 (`Modo Rajada`) e LID 78 (`Neste turno, ao atirar em
  outro jogador, dispare duas vezes consecutivas`).
- O servidor estava enviando `cfgId=2016` como se fosse buff; 2016 identifica
  a carta, não existe como buff nessa configuração e portanto não tinha ícone,
  nome ou descrição para a placa. Os campos `ContinueShoot` enviados antes
  pertencem a outro estado e não substituem a lista de buffs.
- Corrigido somente no servidor da cópia: compra/uso guardado adicionam buff
  1015 tanto ao evento quanto ao snapshot do jogador; o disparo duplo remove
  esse mesmo buff no evento-final e no estado autoritativo. O disparo duplo
  mantém sua implementação confirmada pelo jogador. A instalação original e
  os bundles do jogo não foram alterados nesta etapa.
- `py_compile` passou e a suíte local passou com 69 testes. Falta o teste
  visual no cliente: confirmar o ícone e tooltip ao ativar, e que ele some só
  depois dos dois tiros. O print fornecido é de outro modo, então ele serve
  como referência da UI, não como captura de validação deste modo local.

### Kit de Manutenção: buff e tiro normal — 2026-09-24

- O jogador usou cfg 2015 duas vezes. No trace, as notificações de uso
  reportavam `skillId=1014`, mas anexavam `buff cfgId=2015`; o cliente não tem
  buff com esse ID, então a placa não podia mostrar o ícone. A cadeia extraída
  do bundle confirma `card 2015 -> skill 1014 -> buff 1014`.
- O disparo seguinte estava sendo representado como munição especial `cfg=2`,
  o caminho do Arms Voucher. O trace mostra dano `-2`, mas o pente continuou
  com quatro balas reais e o pacote não usou a animação de acerto normal. Isso
  explica o dano correto acompanhado de efeitos/animação estranhos.
- Corrigido somente no servidor da cópia: cfg 2015 agora envia/manuseia buff
  1014 em `PvpGamer.buffs`, tem estado separado do Arms Voucher, dispara uma
  bala real `cfg=1`, debita o pente uma vez, soma +1 dano contra outro jogador
  e remove o buff no evento final. Tiros falsos e tiros em si mesmo não ganham
  esse bônus; o Arms Voucher continua no caminho independente de cfg 2.
- Backup anterior à alteração em
  `private-server/rollback/2026-09-24-pre-maintenance-kit-fix/`.
  `py_compile` passou; a suíte local passou com 73 testes, incluindo quatro
  testes novos do Kit, um deles percorrendo o fluxo TCP de compra, uso, disparo
  e remoção do buff.
- Próxima confirmação manual: verificar o ícone do Kit ao usar, um disparo
  normal com som/efeitos e uma bala a menos, −2 HP no alvo, e o ícone sumindo
  após o disparo. A aparência/áudio ainda não foi observada após a correção.

### Kit de Manutenção: impedir reaplicação enquanto ativo — 2026-09-24

- O jogador confirmou que o Kit agora funciona no cliente, mas conseguiu
  comprá-lo duas vezes consecutivas. O log da sessão `161032` mostra compras
  de cfg 2015 às 16:25:01 e 16:25:09, ambas no alvo 0 e sem disparo entre
  elas. O servidor cobrava 300 R Coins por um segundo efeito que apenas
  repetia o estado já ativo.
- A tabela `error` de `fight_dbconfig.ab` da cópia associa o código 352 a
  “O alvo já possui este efeito, não pode ser empilhado”; `fight_error` inclui
  esse código para combate. O servidor agora rejeita compra-e-uso e uso de
  carta guardada quando o mesmo alvo já tem o buff 1014. A recusa ocorre antes
  de alterar moedas, oferta, slot ou evento.
- Backup em `private-server/rollback/2026-09-24-pre-maintenance-stack-guard/`.
  Teste TCP cobre segunda compra, erro 352, oferta preservada e carta
  guardada não consumida. `py_compile` e 73 testes completos passaram.
- Próximo item: cfg 2018 Violation Ticket. A descrição em `LanguagePortugal`
  diz lançar dado e roubar da recompensa do alvo resultado ×100; `error`
  código 380 diz “Jogador alvo não tem recompensa”. A implementação genérica
  atual não faz esse roubo. O estado de recompensa e seu evento visual precisam
  de reconstrução antes de chamar o item de funcional.

### Multa: ausência de dado e transferência — 2026-09-24

- O teste manual chegou ao servidor às 19:18:05, compra-e-uso de cfg 2018 no
  bot índice 1. O pacote `255/2` do trace tinha apenas compra `Enum_Coin`
  seguida de um efeito genérico `typ=10` no alvo; não tinha
  `Enum_Update_Luck` nem deltas de moedas. Isso explica o zoom longo sem dado
  ou resultado. O cliente (`ClientAnimExpression.ShowLuckyUI`) espera um evento
  com `source.typ=Enum_Update_Luck`; o `skill_cfg` 1017 confirma tipo Lucky.
- A cópia agora envia dado 1–6, depois dois eventos `Coin_By_Steal`: perda no
  alvo e ganho igual no usuário, limitados ao saldo do alvo. O erro oficial 380
  rejeita alvo sem moedas antes de cobrar ou consumir a carta. O cálculo
  “dado ×100” é literal da descrição; tratar `PvpGamer.coin` como a recompensa
  disponível é uma inferência local, ainda sem captura do servidor original.
- Backup: `private-server/rollback/2026-09-24-pre-violation-ticket/`.
  O teste TCP percorre compra-e-uso e uso de carta guardada com rolagens
  controladas, verifica `Enum_Update_Luck`, dois deltas e os saldos finais.

### Multa: dado aparece, mas moedas não mudam na HUD — 2026-09-24

- O jogador confirmou dado, animação das moedas e do personagem, mas não viu
  transferência de saldo. No log, cfg 2018 rolou 3 e calculou `stolen=300`.
  O snapshot do servidor já continha o saldo líquido do jogador (8100 após
  várias atualizações da loja), porém os dois `Enum_Coin` adicionais não
  atualizavam a HUD.
- `ClientAnimExpression.UseNormalCard` descarta eventos cujo alvo tem
  `typ=Enum_Coin`; esses eventos eram exatamente os deltas de roubo. O cliente
  processa o evento `Enum_Update_Luck` ao concluir a UI do dado. A cópia agora
  embute `Coin_By_Steal` na origem (+300) e no alvo (−300) desse mesmo evento.
- Backup antes do ajuste em
  `private-server/rollback/2026-09-24-pre-violation-coin-ui/`.
  `py_compile` e 74 testes passaram; o teste TCP verifica que os dois deltas
  estão no evento Lucky e não em eventos `Enum_Coin` descartados. A atualização
  visual das moedas ainda requer reteste manual.

### Multa: validação manual concluída — 2026-09-24

- O jogador confirmou dado 2, animações de moeda/personagem e saldos finais:
  bot 10.000→9.800; jogador 10.000−400 do preço+200 do roubo=9.800.
  O log da sessão `192811` registra `cfg=2018`, `die=2`, `stolen=200` no alvo 1.
  Isso valida o fluxo atual do cliente para esse caso; não comprova ainda o
  erro 380 nem todos os resultados possíveis do dado.
- Próximo teste manual: cfg 2020 Surprise Box, inicialmente com slot vazio.

### Caixa Surpresa: fluxo local validado — 2026-09-24

- Teste TCP de compra/uso de cfg 2020 passou: custo debitado uma vez, carta
  aleatória colocada no slot temporário e evento de slot enviado ao cliente.
- No mesmo teste, a carta recebida (cfg 2003 controlado pelo teste) foi usada
  com sucesso, limpou o slot e alterou a munição. A suíte completa passou:
  75 testes. Isso verifica o protocolo e estado do servidor, não a renderização
  nem a animação da Caixa Surpresa no jogo.
- Próxima verificação manual: usar cfg 2020 com slot vazio, observar a carta
  recebida, usá-la e confirmar que o turno não fica preso.

### Caixa Surpresa: dois usos reais e defeitos revelados — 2026-09-24

- O jogador confirmou que a Caixa Surpresa funcionou duas vezes. A primeira
  recompensa foi Energy Pump (cfg 2031), **não usado** porque a habilidade do
  herói aparecia desabilitada. Portanto, não declarar o efeito +1 de skill
  testado. O snapshot PvP local constrói `Hero` com id/modelo, mas sem
  `Hero.SkillId` (campo 2); o inventário contém `skillId` por herói. Isso é
  uma hipótese concreta para a habilidade desabilitada, ainda sem correção.
- A segunda recompensa foi Alucinógeno cfg **2025**: o `Player.log` da cópia
  registra `selectReady cfg=2025 skill=1023 targetType=2` e botões
  `false,true,false,true`. A ausência de seta para si é **comportamento
  configurado** dessa variante (só oponentes), não o defeito. Ao usá-lo no
  Bot 1, houve tiro real e HP 4→3. O log do servidor às 19:41:34 registra
  `card=50 target=1 ammo=1` e munição real 4→3, mas a HUD continuou igual
  até a próxima jogada, segundo o jogador: dessintonia visual ainda aberta.
- Foi adicionada instrumentação para registrar cfg e id de cada recompensa
  da Caixa Surpresa na próxima execução do servidor. Não confundir esse log
  futuro com prova de que o cliente exibiu/aplicou a animação corretamente.
- Diagnóstico temporário `[HR_AMMO_DIAG]` instalado **só** no `lua.ab` da cópia,
  com backup em `private-server/rollback/2026-09-24-ammo-hud-diagnostics/`.
  Registra se o evento `Enum_Shoot` chegou ao objeto do bot, se foi recusado
  por `uTime` e qual `rAmmo` foi aplicado. O servidor e a cópia foram
  reiniciados; próximo teste é usar cfg 2025 em um bot e comparar HUD antes,
  após a animação e após a jogada seguinte.

### Capacidade das armas e mistura da recarga — 2026-09-24

- Os dois testes manuais seguintes de Alucinógeno (Bot 1 e Bot 2) chegaram ao
  cliente e chamaram `SetAmmo` com a lista pós-tiro. No Bot 1, a placa mostrava
  só quatro ícones apesar de o servidor antigo enviar seis balas. O Lua da
  cópia define a quantidade de slots pela propriedade `gun_cfg.ammo_num`;
  portanto, o recorte visual era consequência de dados incompatíveis, não
  evidência de que o personagem do urso pertença ao tutorial.
- `fight_dbconfig.ab` da **cópia** contém 42 linhas `gun_cfg` (ids 0–41).
  Campos protobuf 6/7 fornecem `ammo_num`/`reload_max_real`. Exemplos:
  gun 0 = capacidade 6, máximo 3 reais; gun 1 = capacidade 4, máximo 2
  reais; gun 6 = capacidade 7, máximo 3 reais. Inicialização, recarga de
  segurança e Spare Magazine agora respeitam a arma de cada participante.
- O jogador esclareceu que a recarga ocupa toda a capacidade, mas a proporção
  real/falsa varia. Não achamos no cliente uma tabela de **probabilidades**
  nem um mínimo de balas reais. Por isso, a cópia do servidor escolhe
  provisoriamente e uniformemente de 1 até `reload_max_real`, preenchendo as
  demais posições com falsas. Isso **não** é alegado como algoritmo original.
  Os testes de protocolo ficam determinísticos; o processo local iniciado
  pelo launcher ativa a variação. Testes automatizados: 77/77 antes do teste
  manual desta mudança.

### Tiro falso em si e carregador vazio — 2026-09-24

- O jogador confirmou a regra: tiro falso em si **mantém o mesmo turno**;
  tiro real em si ou qualquer tiro em outro participante passa a vez. O log
  local às 21:20 registrou `target=0 ammoCfg=300` seguido pelo fluxo de bots,
  comprovando a divergência do emulador. O fluxo do modo de três pessoas e o
  de duas pessoas agora reativam o mesmo jogador após a animação, sem somar
  turno nem disparar novamente o cofrinho. Regressões TCP cobrem tiros falsos
  consecutivos e a ausência de jogada de bot entre eles.
- Antes, a recarga de segurança só acontecia depois de **outro pedido de
  disparo** com 0/0, quando a interface já podia estar presa. Agora, quando
  a última bala falsa é disparada em si, o servidor envia automaticamente
  uma atualização de turno com o carregador completo. Se o último disparo
  passa a vez, o carregador é renovado antes do próximo turno desse jogador.
  Bots sem balas também recarregam no começo da próxima jogada deles.
- A composição da recarga continua sendo a aproximação laboratorial descrita
  acima; o pacote de recarga/animação original ainda não foi recuperado.
  A verificação local passou em 79 testes, mas **a animação e o controle em
  jogo ainda exigem confirmação manual** numa partida nova da cópia.

### Sequência de tiros falsos em si, prêmio e Frenzy — 2026-09-24/25

- O cliente tem estado próprio `PvpGamer.ContinueShoot` (campo 19): número de
  tiros, prêmio acumulado, valor do próximo tiro, estado e bônus. O evento
  final de tiro espelha esses valores em `PvpEventOutline` (15, 16, 53, 54).
  A mira em si só permanece após o disparo quando `nextShootCoin > 0`.
- `RouletteBattleWindow` mostra os controles de sequência quando o estado é
  `Continue_Shoot_State_Ing`; “Cancel/Take All” envia
  `GamerPvpShootMoneyC2S`, separado do pedido de atirar. O servidor local
  agora acumula o prêmio por tiro falso em si e o transfere ao saldo ao
  recolher, usando `PvpEventEnum.Type_GetShoot_Money` e motivo de moeda 2.
  O modo também precisa publicar `PvpInfo.isHasShootAward` (campo 44): sem
  isso o próprio cliente oculta o botão de recolha, ainda que haja prêmio.
  A associação numérica do comando de recolha a `3/6` ainda precisa de
  confirmação no trace do cliente; a tabela Lua só expõe seu nome simbólico.
- O valor base vem das linhas **dificuldade 3** de `ammo_reward_cfg` da cópia
  para a arena de três participantes; o bônus sequencial vem das dez linhas
  de `ammo_continue_shoot_self_cfg` (100, 200, ..., 1000). A sequência é
  cancelada por tiro real em si ou tiro em outro jogador. O estado e o
  próximo valor são enviados também nos snapshots posteriores.
- No cliente, `virtualHp`/`virtualHpCap` são os dois campos que desenham os
  ícones de Frenzy depois dos corações. O jogador esclareceu a regra observada:
  início em **0/2**; um item pode alterar esse contador. A mecânica dos tiros
  foi corrigida em 26/09: bala falsa contra outro jogador reduz 1 Frenzy; bala
  real que causa dano a outro jogador concede 1, limitado a `virtualHpCap`;
  tiro em si mesmo não altera Frenzy. A recompensa de moedas/combo por falso
  em si continua independente desse medidor.
- A configuração Lua extraída documenta `Shoot_Del_Vir_Hp` como “tiro básico
  subtrai Frenzy”, `Gamer_Add_Hp_Vir` como efeito que adiciona Frenzy e
  `By_Gun_Shoot_By_Other_Not_Hold_Real_Damage` como gatilho de tiro em outro
  jogador que só dispara quando dano real foi causado. Isso corrobora os dois
  lados da regra. A extração disponível contém descrições do schema, não as
  linhas ativas que fixariam a quantidade em cada situação; o delta de 1 segue
  a lembrança/correção do jogador e precisa de confirmação manual na partida.
- O trace anterior mostrou `Pvp_Prepare` em 0,1 s e liberação do próximo pedido
  após 4,9 s. Reduzir a espera para 2,5 s resolveu o bloqueio de tiros seguintes,
  mas manteve uma transição de operador desnecessária: o cliente a enfileira
  enquanto toca o tiro e, ao terminar, redefine a mira para `Default`. Por isso
  a HUD voltava a `Fire` em vez de manter `Shoot/Cancel`.
- A recarga quando todas as balas acabam tem dois caminhos: após o último
  tiro falso em si, recarrega imediatamente no mesmo turno; se o pente zera
  ao passar a vez, recarrega quando o jogador volta. Foi adicionada uma
  regressão TCP do modo de três participantes que esvazia o pente, confirma
  a recarga e dispara de novo sem pedido manual de recarga.
- Testes locais: 80/80 antes da próxima confirmação visual. A rodada manual
  deve validar o ciclo de tiros, Frenzy em 0/2 e a recarga em partida.

### Frenzy ao atirar em adversários — 2026-09-26

- Corrigida a antiga regra inferida incorretamente de tiro falso em si: ela
  concedia Frenzy, embora o combo mostrado pelo cliente seja recompensa em
  moedas. Tiro falso em adversário agora reduz o Frenzy do atirador; tiro real
  só concede Frenzy quando o alvo realmente perde HP/Frenzy (um bloqueio que
  absorve todo dano não concede ponto). O tiro em si mesmo não altera o medidor.
- Aplicado ao jogador e aos bots nos modos de três participantes e duelo. Cada
  subtiro do Burst emite o próprio delta do atirador, separado do delta de dano
  do alvo; o limite vem do `virtualHpCap` presente no snapshot do cliente.
- Confirmação estática do cliente: `RouletteGamePlayer.lua` soma
  `PvpEventOutline.virtualHp` ao medidor da entidade do evento, e
  `pvp_pb.lua` identifica esse delta como campo 14. Não foi tocada a instalação
  original. Ainda falta validar visualmente em uma partida da cópia.
- Regressão de bot: o valor randômico fixo `5` usado por um teste podia ficar
  fora do intervalo de munição restante e simular tiros reais impossíveis;
  troquei por escolhas determinísticas válidas que também permitem falsos.
  Suíte atual: **92/92 testes OK**; `py_compile` também passou. O processo
  já aberto, se ainda estiver em v23, precisa ser reiniciado para carregar v24.
- Tentativa de abrir v24 em 26/09: a cópia consultou `PkgVersion.json`, mas o
  cliente fechou antes de conectar ao serviço PVP; pelo launcher, o servidor
  foi encerrado normalmente quando `Client.exe` saiu. Nenhum teste visual da
  mecânica Frenzy ocorreu ainda.
- Segunda abertura em 26/09: `/health` confirmou `version=24`, e
  `Game\\Client.exe` está ativo dentro da cópia isolada; aguardando teste manual.

### Continuação visual do tiro falso em si — 2026-09-25

- O jogador confirmou que a HUD começa com **0/2 Frenzy**. O defeito relatado
  agora é outro: após atirar em si com bala falsa, a animação termina/cancela e
  os controles voltam a **Fire**, em vez de permanecer em **Shoot/Cancel**.
- A fonte Lua explica a transição: `OpPreNext` guarda `Pvp_Prepare` enquanto
  aguarda `Finally_Source`; `OnShootOver` então chama `StartOpPvpPrepare`, que
  redefine a mira para `Default` e atualiza o turno. O ramo do servidor local
  estava enviando `Pvp_Prepare` e `PvpIng` mesmo quando o tiro falso mantinha
  o mesmo jogador ativo, tanto no modo de três participantes quanto no duelo.
  Para tiros não finais, esses sinais foram removidos;
  o evento final mantém `Continue_Shoot_State_Ing` e o snapshot continua com
  o jogador ativo. A recarga automática do último cartucho permanece separada.
- A rotina ativa do cliente usa `ShootSelf_Aim` para tiro em si; uma rotina
  antiga com animações `ShootSelfN_NoHit` aparece comentada no Lua. Portanto,
  o servidor não inventa uma animação nova: a validação visual após reiniciar
  a cópia deve confirmar se o fluxo nativo agora completa a provocação e deixa
  os botões **Shoot/Cancel** disponíveis. Teste de regressão TCP também exige
  que um tiro falso não-final não gere notificação de novo turno.
- O launcher `RLGame.exe` pode retornar antes do processo `Game\\Client.exe`;
  por isso o `finally` antigo encerrava o servidor com o jogo ainda aberto.
  `start_local_test.ps1` agora espera e acompanha o cliente da cópia, mantendo
  o servidor v16 ativo até o usuário fechar o jogo.
- Verificação deste reinício: health respondeu `version=16`; o cliente da cópia
  conectou aos serviços locais e carregou o lobby. Trace desta sessão:
  `private-server/packet-trace-20260925-225611.jsonl`. Ainda falta o novo teste
  manual do tiro falso em si; o teste automatizado cobre a ausência de uma
  transição de operador, mas não consegue validar a animação visual.

### Coleta do prêmio do tiro em si — 2026-09-25

- Na sessão manual, o jogador clicou para coletar os chips após um tiro falso
  em si e o fluxo travou. O trace registrou exatamente `cmd=3 act=8`, com
  corpo protobuf de 2 bytes (`idx=1`), no pedido de coleta.
- O Lua embarcado nomeia essa ação
  `GAME_CMD_PVP_ING_SHOOT_MONEY`; o handler local, porém, estava associado a
  `(3, 6)`. O pedido real caiu no caminho genérico, recebeu resposta vazia e
  não pagou o prêmio nem emitiu o evento que atualiza/libera a interface.
- Corrigidos o handler e o teste TCP para `(3, 8)`. O servidor e o launcher
  avançaram para v17 para não reutilizar acidentalmente o processo v16.
- Falta validação manual: após reiniciar a cópia, atirar em si com bala falsa,
  clicar em coletar/cancelar e conferir pagamento, animação do evento e retorno
  aos controles. A instalação original permanece intocada.
- Na primeira validação manual da v17, a coleta destravou. O log registra
  `amount=100 balance=10100` e o trace da notificação PVP carrega `coin=10100`
  (saldo inicial da partida `10000`). Os novos prints confirmaram que o painel
  laranja permanece em `10000` depois de o prêmio aparecer como `+200`.
- Causa visual confirmada no Lua: `ShowUIChange_Small` não atualiza `source`
  quando `source.Idx == target.Idx`; só aplica o `target`. O pacote v17 colocava
  o delta de moeda e a limpeza do prêmio no `source`, deixando o saldo exibido
  inalterado embora o snapshot do servidor já estivesse em `10200`.
- Correção v18: mover delta de moeda e zeragem do bounty para o `target` do
  evento. A regressão TCP agora verifica mesmo índice, origem sem delta,
  destino com `+1100`/razão Shoot_Self e pool zerado. `py_compile` e 80 testes
  passaram. Falta confirmar visualmente no cliente após reinício da cópia.

### Habilidades dos personagens — v19, 2026-09-25

- O cliente lê `PvpGamer.hero.SkillId` (Hero campo 2) e `SkillCd` (campo 3)
  para mostrar o botão/ícone e bloquear o uso enquanto `SkillCd > 0`. O
  servidor v18 enviava só id/modelo, deixando a skill invisível/desabilitada.
- Extraídos **da cópia** de `fight_dbconfig.ab` os `skill_info_cfg` e
  `skill_cfg_steam` dos dez heróis presentes no inventário: ids
  10000/10001/10002/10005/10020/10017/10022/10032/10035/10038;
  recarga inicial 3 para todos; após uso, 10020 e 10035 voltam a CD 2,
  as demais a CD 3. Nomes/efeitos foram
  conferidos em `LanguagePortugal`, não inferidos pelos ícones.
- O snapshot PvP agora transporta ID/CD e a passagem para o próximo turno
  reduz o CD em 1, inclusive na primeira entrada do jogador. Energy Pump
  cfg 2031 reduz CD em 1 com `Enum_Skill_Cd=9`; antes criava somente buff
  genérico. São tratados os caminhos de compra+uso e item guardado.
- Primeiro efeito implementado para teste manual: Bomba de Cenoura (herói
  0, skill 10000) usa `GamerPvpGamerUseHeroSkillC2S` assumido em `(3,6)`,
  rola d6; em 3+ cura 1 HP em si ou causa 1 ao inimigo, e repõe CD 3.
  O envelope `type_Skill=3` contém o dado, delta de HP e reset de CD.
  **A associação `(3,6)` e a animação ainda não foram confirmadas por trace
  do cliente**. Outras nove habilidades ainda não têm handler de efeito;
  não chamá-las de funcionais. O próximo teste manual deve confirmar se o
  ícone aparece, se recarrega por turno e qual pedido chega ao clicar.
- `py_compile` e 82 testes locais passaram. Instalação original intocada.
- Teste manual v19: o jogador confirmou Bomba de Cenoura visível e funcional.
  O trace registra `(3,6)` duas vezes: dado 2/`hpDelta=0`/Bot 2 com 4 HP;
  depois dado 4/`hpDelta=-1`/Bot 2 com 3 HP. Ambos retornaram `error=0`,
  e o cliente continuou enviando ações. Quatro Energy Pumps comprados/ usados
  entre os disparos fizeram o `SkillCd` no snapshot cair 3→2→1→0.
- Ao confrontar as duas tabelas, corrigimos a distinção: `hero_cfg_steam`
  campo `init_skill_cd` é 3 para os dez heróis; `skill_cfg_steam.cd` é a
  recarga **após uso** (2 somente nos ids 10020 e 10035). O teste inicial do
  herói 0 não era afetado; os outros seriam.
- Na v20, tiro falso em si concede +1 Desespero/Frenzy até o limite normal
  de 2, publicando tanto o delta do evento quanto o valor do snapshot. A
  habilidade do Urso 10001 converte esses pontos em HP e consome a carga.
  Isso passou por testes de protocolo/loopback, mas **Urso ainda não foi
  validado visualmente**. Total atual: `py_compile` e 83 testes locais OK.

### Urso validado e recarga da última bala real — v21, 2026-09-26

- O primeiro teste visual de “Saúde!” não produziu efeito porque o usuário
  havia saído da partida em que ganhou Frenzy e entrado em outra. O log da
  nova partida mostrou `hpDelta=0 virDelta=0`. Com duas caveiras preenchidas
  na **mesma** partida e vida faltando, o servidor registrou
  `hpDelta=2 virDelta=-2`; o usuário confirmou que ambas viraram HP na HUD.
  A habilidade do Urso está confirmada nesse cenário. Ativá-la com zero
  Frenzy ainda gasta o cooldown sem efeito; não há evidência suficiente para
  afirmar se o original bloqueava isso.
- Observação manual: quando a última bala real é disparada, o usuário espera
  recarga automática mesmo que restem falsas. A implementação anterior só
  recarregava com 0/0 e deixava HUD 0 real/N falsas. Em v21, os quatro
  caminhos de disparo (jogador/bot, trio/duelo) calculam a nova composição
  conforme a arma e anexam `Enum_Reload` ao próprio resultado do tiro. O Lua
  embarcado armazena esse evento e o aplica em `OnShootOver`, após a animação.
  O snapshot do servidor já reflete o pente novo; um fallback na abertura de
  turno também recarrega quem ainda estiver com zero balas reais.
- Validação local: `py_compile` e 85 testes, inclusive loopback TCP do trio
  forçando 1 real + 3 falsas e verificando tiro 0/3, evento de recarga 2/2 e
  snapshot 2/2. **Animação e HUD da recarga ainda precisam de teste manual no
  cliente copiado.** Instalação original intocada.
- Teste manual v21: o usuário confirmou que o Urso recarregou quando as
  amarelas acabaram. Às 01:44:43, o log registrou a última bala real e a
  recarga 2 reais/2 falsas no mesmo disparo; o trace saiu de 1/2 no pedido
  para 2/2 na resposta/evento. Outro tiro às 01:45:09 reduziu o pente para
  1/2, confirmando continuidade do estado. A ocorrência da recarga na HUD
  está confirmada pelo usuário; o tempo/qualidade da animação não foi
  avaliado separadamente.
- Ao testar visualmente, o usuário relatou que o pente só aparecia, sem
  animação. Causa encontrada no `Lua%ClientAnimExpression` da cópia:
  `OnShootOver` recebia `Enum_Reload`, mas as chamadas nativas
  `PlayTableAnimator(...Reload_Table)` e
  `PlayTableAnimator(...Reload_And_ChangeAmmoTable)` estavam comentadas.
  Criei `patch_reload_table_animation.py`, com hash de entrada estrito,
  backup, round-trip UnityPy e instalação apenas na cópia. O bundle da cópia
  agora tem SHA256 `B3BE67948EDE33E405338CBDDF9FDF45D14B67AF6684E3B52EDADDA741D0E417`;
  o backup anterior está em `rollback/2026-09-26-reload-table-animation/`.
  Cliente e servidor v21 foram reabertos. A animação ainda aguarda validação
  manual do usuário; os eventos da HUD continuam processados por
  `StartReload`/`isReload`.

### Ejetor sem munição após a última bala real — v22, 2026-09-26

- Reconstrução do relato nos arquivos `private-server/server-session-20260926-015544.err.log`
  e `private-server/packet-trace-20260926-015544.jsonl`: às 01:57:11.227,
  `(cmd=3, act=5)` ejetou a última bala real (`real=1/fake=0` antes,
  `real=0/fake=0` depois). Nenhum evento de recarga foi enviado naquele uso.
  Às 01:57:23.678, o cliente ainda pediu para atirar; só então o fallback do
  servidor recarregou (`1 real/3 falsas`, turno 2) e recusou esse disparo.
  Isso explica a mira/tiro aparentemente disponível e a recarga tardia.
- Evidência do jogo: `Lua_Config_Description` define
  `Pop_Ammo_If_Reload_Show_Reload=127` como “ejetar uma bala e, se houver
  recarga, notificar imediatamente”, além de `ReloadSource.By_Pop_Ammo=2`.
  O `ClientAnimExpression.PopAmmo` processa tanto `Enum_Pop_Ammo` quanto
  `Enum_Reload` no mesmo resultado e usa `OnShootOver` para aplicar a recarga.
  Não localizei ainda prova de que todos os cfgs/variantes de Ejetor ativam
  esse BuffLogic específico.
- Corrigidos os caminhos de Ejetor comprado/uso imediato e item guardado: se
  a ejeção deixa o alvo sem balas reais, o servidor recalcula o pente pela arma,
  atualiza o snapshot e anexa `Enum_Reload` depois do evento de ejeção. A recarga
  não avança o turno. Caso haja só balas falsas, também recarrega, consistente
  com o fluxo já reconstruído do tiro quando as balas reais acabam.
- Adicionado teste de integração TCP para ambos os caminhos, começando com
  exatamente 1 bala real; confirma sequência PopAmmo→Reload, pente atualizado
  e consumo do item guardado. `py_compile` passou e a suíte completa passou:
  86 testes. O servidor v22 responde `/health` com versão 22. Reiniciei só a
  cópia para o teste manual; a sessão atual grava em
  `private-server/packet-trace-20260926-021115.jsonl` e
  `private-server/server-session-20260926-021115.err.log`. Falta confirmar no
  cliente a animação/HUD da recarga após o Ejetor; instalação original
  permanece intocada.

### Derrota com Frenzy acumulado — análise de log v22, 2026-09-26

- Na sessão `private-server/server-session-20260926-021115.err.log`, o jogador
  estava com 1 HP após o Alucinógeno em si (`02:14:02`, HP 2→1). Em
  `02:14:13`, atirou em si com bala falsa e manteve o turno; em `02:14:16`,
  atirou em si com bala real. O evento registrou `hpDelta=-1`, `targetDead=1`,
  HP 1→0, e encerrou a partida em derrota (`winner=2`, jogador rank 3, round
  12), embora o snapshot ainda tivesse `virtualHp=2`.
- A interpretação anterior de que Frenzy só poderia virar HP pela skill do
  Urso estava errada. A inspeção do cliente embarcado corrigiu isso: o método
  `TrySetPlayerDieStatus()` só marca derrota quando HP **e** `m_VirtualHp`
  estão zerados; os caminhos de dano também reconhecem ambos os pools.
- Correção aplicada apenas na cópia de pesquisa: dano consome HP primeiro e,
  após zerá-lo, Frenzy; tiros, recargas, alvos de itens e resolução de
  Alucinógeno usam a condição combinada. Incluídos testes para HP 0/Frenzy 1
  continuar vivo e HP 0/Frenzy 0 ser eliminado. `py_compile` passou e os 90
  testes da suíte passaram; o servidor foi marcado como v23 para distinguir a
  correção do v22. A validação visual em partida continua pendente.

### Bullet Time em eliminação por bala real — reconstrução estática, 2026-09-26

- A câmera lenta não é a animação de morte do alvo. São dois fluxos distintos:
  o cliente escolhe `beKilledAnim` para o alvo; o Bullet Time é iniciado no
  controlador da cena durante o evento de disparo do atacante.
- Caminho reconstruído no cliente: o servidor codifica
  `EventGamerStatus` (campo protobuf 63); `RouletteGameModule.GetPlayerState`
  devolve esse estado do atirador; `ClientAnimExpression.StartShootAmmo` o
  passa em `AnimConditions.playerState`; `AnimatorLogic.Play` guarda o estado,
  IDs de munição e alvo. No callback `AnimatorLogic.OnFire`, quando o estado é
  `2` (atirador eliminou outro jogador), termina a contagem de disparos da
  animação e verifica o cfg da última bala. Se `AmmoCfg.ammo_typ == 2` (bala
  real), encaminha o ID dessa bala como `ammoTimeFlag` para
  `RouletteGameSceneController.OnFire`. Esse controlador só prossegue quando
  o flag é positivo e chama `StartAmmoTime`.
- `StartAmmoTime` escolhe o controlador Bullet Time normal/perto e inicia
  `BulletTimeCtrl`; o método nativo `DoSlowmotion` define `Time.timeScale` pelo
  fator serializado do prefab (`0,2`) e ajusta `fixedDeltaTime`. Os clips
  `CameraBulletTime*` e os objetos `BulletTimeCtrl*` estão presentes nos bundles
  da cópia do jogo.
- A análise inicial concluiu incorretamente que o campo 63 bastava. O trace
  bruto do disparo final de 2026-09-26 às 16:54:32 mostra status 2 no
  `PvpEventOutline`, mas nenhum status no `PvpEventResult.source` (PvpGamer),
  exatamente onde `GetPlayerState` procura o estado do atirador. A correção e
  os testes estão registrados na seção de correção logo abaixo.
- Evidências para repetir a análise: Lua extraído em
  `private-server/lua-extract/battle-contract/{RouletteGameModule.lua,ClientAnimExpression.lua,RouletteGameScene.lua}`;
  contratos em `0004_Lua_Config_Description_1.lua` (`AmmoCfg.ammo_typ`:
  1=falsa, 2=real); binário da cópia `Game/GameAssembly.dll`, métodos
  `AnimatorLogic.Play` RVA `0xC0F430`, `AnimatorLogic.OnFire` RVA `0xC0E580`,
  `RouletteGameSceneController.OnFire` RVA `0xC323E0`, `StartAmmoTime` RVA
  `0xC3BBB0` e `BulletTimeCtrl.DoSlowmotion` RVA `0xBD3770`.
- Limite da evidência: os traces não registram `Time.timeScale` nem o estado
  efetivo da câmera; a confirmação visual do Bullet Time após corrigir o campo
  ainda depende de nova eliminação com bala real.

### Correção do estado de animação de morte e verificação do cigarro — 2026-09-26

- Revisão do contrato Lua/protobuf corrigiu a conclusão acima: embora o
  `PvpEventOutline` tenha `eventGamerStatus` no campo 63, o Lua consulta
  `gamerPvpEvent.source/targets` da mensagem externa `PvpEventResult`; esses
  campos são `PvpGamer`, cujo estado transitório está no campo 26. Antes, o
  servidor enviava 2/4 apenas no outline, então `GetPlayerState` recebia 0 e
  `AnimatorLogic.OnFire` nunca iniciava o Bullet Time de uma eliminação.
- Correção aplicada só à cópia de pesquisa: o resultado de tiro agora também
  marca os snapshots externos com status de atirador/alvo, preservando os
  outlines internos. Testes cobrem status 2/4 e remoção do status transitório
  em tiro normal.
- O trace antigo do abate final confirma a discrepância em runtime: status 2
  no field 63 do outline e field 26 ausente no PvpGamer externo. O log da nova
  execução também registrará `eventStatus=2/4` no disparo letal, inclusive se
  a partida terminar nesse tiro.
- Sobre cigarro com HP zerado: o log de 2026-09-26 às 16:52:26 registra o
  jogador com HP 0 ainda na partida; às 16:53:06, um Cigarros Molhados tirou
  5 no dado e registrou `heal=1 hp=1`. Isso confirma que 0 HP com Frenzy ainda
  positivo pode ser curado. A regra é probabilística: 4–6 cura 1 HP, 1–3 não;
  HP/Frenzy ambos zerados significa eliminado. A regra agora está centralizada
  e tem teste de regressão para esse cenário.
- Validação visual do Bullet Time ainda depende de uma eliminação por bala real
  em nova partida. A partida mais recente no log carregou às 16:56:37, mas até
  17:02:23 só registrou consultas periódicas, sem ações de tiro. Versão do
  laboratório atualizada para v25.

### Morte por bala falsa e cigarro com HP zerado — v26, 2026-09-26

- A primeira interpretação concluiu incorretamente que o alvo perdia a última
  caveira. A análise corrigida está em v27: atirar uma bala falsa em oponente
  reduz o Frenzy de quem atirou.
- Correção do cigarro: a interpretação antiga (HP 0 com Frenzy ainda curável)
  estava errada para o comportamento original lembrado pelo jogador. Como os
  corações somem com HP 0, o cigarro pode resolver sua ação, mas sua cura agora
  é sempre zero nesse estado. Com HP entre 1 e 3, a chance normal permanece;
  HP máximo também não cura além do limite.
- `py_compile` passou e os 95 testes locais passaram, incluindo o cigarro sem
  cura a 0 HP. A animação por bala falsa ainda não estava validada em partida.
- Health version do servidor e script de inicialização atualizados para v26.

### Correções de tiro, morte por Frenzy e ritmo de espectador — v27, 2026-09-26

- Corrigida a regra de bala falsa: se o disparo contra um oponente remove a
  última caveira de quem atirou (com HP já zerado), o evento 76 agora aponta
  para o atirador. A rajada para nesse tiro letal sem consumir a bala seguinte.
- Corrigido o Kit de Manutenção: cfg 1 com bônus +1 causa dois pontos de dano
  também em tiro próprio; cfg 300 continua sem dano e cfg 2 mantém o bônus
  próprio do Arms Voucher.
- Trace anterior: o resultado da partida chegou cerca de 2m44s após a
  eliminação local, após 102 quadros da luta entre bots. Para espectador, todos
  os tiros e animações permanecem, mas os intervalos mudam de 5s/3s para
  3s/1,5s; `PVP_END` também não espera mais 2,5s extras nesse caso.
- Verificação: `py_compile` e 97 testes locais; teste TCP em modo trio confirma
  que a última bala falsa marca como morto o índice do atirador. Ainda falta
  validação visual da animação cadeira/choque, HUD de -2 HP e tempo percebido
  até a tela Loser.
- O Lua embarcado na cópia foi ajustado para chamar também `PlayChairAnimator`
  no evento 76; o bundle anterior foi guardado em
  `research/private-server/rollback/2026-09-26-pre-death-chair-animation/`.
- Health version do servidor e inicializador atualizados para v27.

### Câmera de morte local por Frenzy — 2026-09-26

- O jogador esclareceu que o Kit de Manutenção funciona; o defeito pendente é
  a câmera/animação ao morrer por ficar sem Frenzy. Nenhuma mudança no Kit foi
  feita nesta etapa.
- No handler Lua do evento 76 (`Enum_Update_Gamer_Dead_Status`), a cópia já
  tocava as animações do jogador e da cadeira, mas não chamava o controlador
  de câmera. Os assets originais do bundle incluem as trilhas
  `CameraSelfDie_Position` e `CameraSelfDie_PushRotation` (4 s), e as trilhas
  de retorno `Camera_BackToDefault_Pos` / `Camera_BackToDefault` (1 s).
- Aplicada somente na cópia local a chamada das duas trilhas de morte quando
  o evento é recebido pelo jogador principal, com retorno ao enquadramento
  padrão após 4 s. Bundle anterior guardado em
  `private-server/rollback/2026-09-26-pre-frenzy-death-camera/`.
- A serialização do bundle foi reaberta e verificada antes da instalação; a
  primeira tentativa falhou na verificação e não substituiu o bundle ativo.
  A gravação corrigida passou. O teste visual posterior mostrou que a câmera
  ainda ficou em primeira pessoa; a causa e a correção estão abaixo.

### Estado correto da câmera de morte — 2026-09-26

- O teste do jogador mostrou animação/efeitos de morte em primeira pessoa.
  Inspeção dos `AnimatorController` `CameraControl` e `CameraControlchild` no
  bundle original mostrou que `CameraSelfDie` é o estado aceito por
  `SinglePlayCameraAnim`. As trilhas `CameraSelfDie_PushRotation` e
  `CameraSelfDie_Position` são os clipes ligados a esse estado nos dois
  controladores, não nomes de estados. A tentativa anterior chamava os clipes
  diretamente e, portanto, não ativava a câmera de terceira pessoa.
- O handler local do evento 76 agora chama o estado `CameraSelfDie` uma vez
  para o jogador principal. Removido o temporizador anterior que acionava
  retorno após 4 s. O bundle foi reaberto após serialização: uma chamada do
  estado correto, nenhum nome de clipe antigo e nenhum timer anterior.
- Backup antes desta correção em
  `private-server/rollback/2026-09-26-pre-camera-state-fix/`. A confirmação
  visual em nova partida ainda é necessária. O jogador também lembrou que o
  choque na cadeira interrompia a animação do tiro falso; o servidor emite o
  evento de tiro seguido do evento 76, e falta validar o ritmo em tela.

### Câmera de morte — melhoria ainda não finalizada — 2026-09-27

- O jogador informou que a câmera melhorou, mas ainda faltam elementos. Manter
  como **não finalizado / melhoria futura**; não declarar essa etapa concluída.
- Em uma próxima sessão, identificar com o jogador quais detalhes visuais ainda
  divergem e conferir terceira pessoa, enquadramento, choque na cadeira e se o
  choque interrompe a animação de tiro falso. Nenhuma nova mudança de câmera foi
  feita nesta atualização.
- A lista de teste de itens foi reconciliada com os relatos do jogador e com o
  catálogo de cfgIds: agora são 9 confirmados, 4 parciais, 12 ainda sem teste
  manual e o Piggy Bank (2034) bloqueado até corrigir o ícone/interação
  congelados. Ver
  `ITEM_TEST_ORDER.md` e `ITEM_CATALOG.md`.

### Item 2007 — Spare Magazine confirmado — 2026-09-27

- O jogador testou o item em si e no bot: efeito funcional e animação da troca
  suave. Encerrar o teste funcional do cfg 2007.
- As combinações de munição observadas variam. A capacidade e a distribuição
  por arma ficam deliberadamente para a etapa de armas, depois de concluir os
  testes de itens; a configuração atual não é evidência da regra original.
- Próximo item da fila: 2008 Hallucinogen, com foco na divergência de munição
  já relatada para o Bot 1.

### Alucinógeno e recarga sem balas reais — 2026-09-27

- O trace da partida identificou cfg 2025/skill 1023, offer 40, usado no Bot
  1: a munição real foi de 1 para 0, o HP de 4 para 3 e sobraram falsas, mas
  não houve evento de recarga. Isso explica a HUD do segundo print.
- Corrigido o disparo forçado compartilhado pelos cfg 2008/2025: quando o alvo
  sobrevive e fica com zero balas reais, o resultado envia o evento do tiro e
  depois `Enum_Reload`; o estado autoritativo e a HUD recebem o pente novo.
  Também ajustados os tiros normais para recarregar imediatamente quando não
  restam balas reais, mesmo se o tiro que acabou de ocorrer foi falso.
- A cfg original do skill 1023 traz `target_typ=2` (oponentes) e por isso a
  seta em si não aparecia. Como solicitado, a cópia local agora habilita a seta
  do jogador principal apenas para essa variante. A mensagem ainda descreve
  “enemy”; confirmar visualmente no teste e revisar o texto se causar confusão.
- Verificação: `python -m unittest discover -s tests -p test_protocol.py` — 99
  testes passaram, incluindo bala falsa contínua, recarga de pente só falso e
  recarga após o tiro forçado. O bundle Lua passou extração/serialização e foi
  instalado somente em `Hunter Roulette - Copia`, com backup em
  `private-server/rollback/2026-09-27-hallucinogen-self-target/`. Hash da cópia:
  `4A7AB241...755DB672`; instalação original mantida em hash distinto.
- O jogador testou e informou que tudo funcionou. O log confirma o cfg 2008
  usado em si (`target=0`, tiro real, HP 4→3) e o cfg 2025 usado no Bot 1:
  oferta 94, tiro real, HP 4→3 e auto-recarga registrada para 1 bala real + 3
  falsas. O snapshot enviado após a ação mantém o Bot 1 com esse pente.
- Pendência visual adicionada: a função está correta, mas a animação da arma
  recarregando ainda parece errada. Revisar junto com capacidades e composição
  de munição por arma, na futura etapa de armas.
- Próximo item para fechar: **2016 Burst Mode** — conferir os dois tiros, o
  consumo correspondente de munição e a duração/remoção do ícone na HUD. O
  servidor v28 e o jogo da cópia continuam abertos para esse teste.

### Burst Mode consumido no primeiro tiro próprio — 2026-09-27

- No log da sessão `server-session-20260927-010605.err.log`, o uso do cfg 2016
  / skill 1015 foi registrado às 01:23:08 com `target=0`. Às 01:23:22 houve um
  tiro falso próprio (`ammo=1/2`) que manteve o jogador no turno. Isso é
  compatível com a regra de tiro falso em si; não é, por si só, evidência de
  rajada dupla.
- A inspeção do código confirmou o defeito: o servidor só marcava Burst como
  ativo se o alvo fosse outro jogador. Para um tiro próprio, isso evitava a
  bala extra, mas também deixava o buff/ícone ativo para a ação seguinte.
- Corrigido no servidor v29: o próximo disparo sempre consome Burst, mas só
  dispara a segunda bala quando o alvo é outro personagem. O tiro próprio
  continua sendo uma bala; um tiro falso ainda pode manter o turno por sua
  regra independente. Adicionado log explícito de consumo para facilitar a
  próxima verificação.
- Testes: 101 testes passaram (`python -m unittest discover -s tests -p
  test_protocol.py -v`), incluindo teste TCP de compra/uso do Burst, tiro
  próprio único, remoção do buff cfg 1015 e snapshot sem ícone. O teste de
  lógica também confirma que um alvo adversário continua habilitando duas
  balas.
- Estado do item continua **parcial** até o teste visual: em partida nova,
  ative Burst em si e atire uma vez; confirme que o ícone some imediatamente.
  Se a bala for falsa, o turno pode continuar, mas a próxima ação não pode
  herdar Burst. Depois teste em um bot: devem ocorrer dois disparos e o ícone
  desaparecer. O próximo item manual continua sendo 2031 Energy Pump.

### Burst Mode retestado e fechado — 2026-09-27

- O jogador informou que o resultado ficou correto e pediu o próximo item.
- O log v29 confirma dois casos distintos: às 01:40:34, Burst aplicado em si
  foi consumido com `double_shot=False`, e o tiro falso próprio continuou o
  turno como esperado; às 01:41:54, um tiro contra o bot consumiu o buff com
  `double_shot=True`. O item 2016 sai da lista parcial e fica confirmado.
- Próximo teste manual: **2031 Energy Pump**. Usar quando uma habilidade
  estiver em recarga e conferir se o indicador avança uma carga/reduz o
  cooldown em 1, sem alterar HP ou munição; testar a disponibilidade quando o
  cooldown chegar a zero.

### Energy Pump fechado; Wanted preparado para teste — 2026-09-27

- O jogador confirmou que Energy Pump (cfg 2031) funcionou. Os traces locais
  registram o uso no jogador e em bot e a carga da habilidade; a fila manual
  foi atualizada.
- Próximo item: Wanted (cfg 2021). A engenharia reversa dos bundles encontrou
  o marcador de 1 round, buff visível 5002 e recompensa de 4 R-Chips. O
  servidor local agora paga ao primeiro atacante que causar dano de tiro e
  remove o marcador; se ninguém acertar antes da expiração, paga ao alvo vivo.
- Validação local: `py_compile` aprovado e 106 testes de protocolo/loopback
  passaram, incluindo compra/uso TCP, recompensa e remoção dos buffs. A
  confirmação de HUD e saldo real no cliente ainda depende do teste manual.
- Próximo teste: em partida nova, compre/use Wanted no Bot 1 e confira o ícone;
  em seguida acerte-o com um tiro que cause dano. Esperado: +4 R-Chips para o
  jogador e ícone removido. Purchase Ban (cfg 2022) passa a ser o item seguinte.

### Wanted: ids de buff e escala econômica planejada — 2026-09-27

- O jogador aplicou Wanted em si e no Bot 1. O log da partida registra as duas
  reivindicações: o tiro real do jogador no Bot 1 pagou +4; o contra-ataque do
  Bot 1 ao jogador também pagou +4. Os pagamentos ocorreram, mas o marcador
  visual continuou.
- A inspeção do Lua extraído mostrou que `AddBuff` e `RemoveBuff` identificam
  instâncias por `Buff.id`, enquanto o servidor local emitia `id=1` para todos
  os cfgIds. Corrigido `_pvp_buff`: cada cfg recebe agora ID sintético estável
  `1.000.000 + cfgId`, igual nos eventos de adição e remoção. Testes agora
  cobrem IDs distintos para 1020/5002, além do caminho TCP de Wanted.
- Economia futura (não bug atual): suportar modos 10×/100×/1000× multiplicando
  preços dos itens e a recompensa base de Wanted (4 R-Chips no modo 1×). Não
  implementar nesta etapa.
- Próximo teste: iniciar partida nova; aplicar Wanted em você e no Bot 1; após
  cada alvo receber dano real, confirmar pagamento de +4 ao atirador e remoção
  do ícone daquele alvo. O item permanece parcial até confirmar a HUD.

### Wanted: primeiro teste TCP (regra global antiga, supersedido) — 2026-09-27

- O jogador confirmou que acertar com tiro remove Wanted; a pendência agora é
  exclusivamente o tempo de duração. A sessão anterior registra acerto nos
  dois alvos, então não continha uma expiração sem reivindicação.
- O primeiro teste de três participantes verificava a implementação então
  existente: marcava Bot 1, fazia o jogador atirar em Bot 2 e esperava o prêmio
  só no retorno ao turno do jogador. Esse relógio global foi posteriormente
  identificado como incorreto e substituído pela regra individual abaixo.
- `py_compile` e os testes TCP passaram para aquela implementação, mas essa
  expectativa de ordem foi supersedida. A validação atual e o estado pendente
  de teste manual estão na seção de 2026-09-28 abaixo.

### Wanted: bug de expiração global observado — 2026-09-28 (corrigido abaixo)

  (Registro histórico antes da correção: o servidor expirava todas as marcas
  pelo relógio global. A regra correta, esclarecida depois pelo jogador, está
  documentada e implementada na seção seguinte.)

### Wanted: tentativa no próximo turno do alvo (superada no reteste) — 2026-09-28

- Correção do jogador: cada Wanted é individual e dura até chegar o próximo
  turno do personagem marcado. O marcador do Bot 1 não deve sumir no turno de
  quem o aplicou; expira quando começa o turno do próprio Bot 1. Isso vale por
  alvo em todos os modos.
- Causa: o servidor guardava prêmio por alvo, mas comparava a expiração com o
  relógio global da rodada. Agora mantém um contador de turnos por personagem.
  Ao começar o turno do alvo, se a marca não foi reivindicada por dano, paga 4
  R-Chips ao alvo sobrevivente e remove os buffs visível/oculto antes da ação.
- A regressão TCP de três participantes confirma a ordem: jogador age, Wanted
  de Bot 1 expira/paga, então Bot 1 age. `py_compile` e os 107 testes passaram.
  O reteste seguinte rejeitou esse prazo: a marca do Bot 1 acabou na primeira
  vez dele, antes de completar a duração desejada. A regra atual está abaixo.

### Wanted: orçamento individual de trocas de turno — 2026-09-28

- Trace da versão anterior: aplicado no Bot 1 às 14:15:10 e no jogador às
  14:15:20; a marca do bot expirou na primeira vez dele. O jogador propôs uma
  contagem explícita: com três participantes, cada aplicação recebe 3 turnos,
  começa a contar no uso e perde 1 a cada troca de personagem ativo.
- Implementado prazo próprio por aplicação (`relógio atual + N vivos no uso`).
  Tiros repetidos em si com bala falsa, uso de cartas e recarga na mesma vez não
  gastam esse orçamento. Duas marcas aplicadas na mesma vez têm o mesmo prazo;
  marcas aplicadas em turnos diferentes têm prazos diferentes. O prazo já
  criado não encolhe quando outro jogador é eliminado.
- Descoberta no cliente: `Enum_Gamer_Buff_Calc=25` atualiza buffs existentes;
  o campo `buffs` do outline é 3. `UpdateBuffsInfo` troca o efeito da mesa pelo
  `showNum`. A tabela oficial liga efeito 107/número 1→136, 2→137, 3→138 e
  4→139. Contador inicial/corrente agora é enviado no evento e no snapshot,
  mantendo IDs e origem. O algoritmo do servidor original não foi recuperado;
  esta duração local segue a regra proposta pelo jogador.
- `py_compile` e 110 testes passaram. O TCP reproduz Wanted em você e Bot 1:
  ambos ficam em 2 no turno de Bot 1, em 1 no de Bot 2 e expiram só na terceira
  troca, pagando uma vez cada. Outro teste confirma duas balas falsas em si sem
  gastar turnos. Marcas aplicadas em instantes diferentes são testadas separadas.
- Wanted permanece parcial até validar visualmente 3→2→1→expiração e o crédito.
  Depois, Purchase Ban (2022). O teste usa somente a cópia local.

### Wanted: atualização passiva sem desviar a mira — 2026-09-28

- Jogador aprovou a duração, mas relatou arma mirando corretamente e virando
  para outro lado antes do tiro quando há Wanted. HP/dano permanecem corretos.
- Verificado no `lua.ab` atual da cópia: `Type_System=11` passa pelo caminho
  que substitui `gamerPvpEvent`, limpa a fila de animação e chama
  `ClearCurSelectInfo` → `PlayerLookForward`. Contador/expiração não devem
  executar esse caminho durante uma ação de tiro.
- Ambos passam a `Type_Behavior=17`, atualização UI passiva nativa que retorna
  antes dessas limpezas. O pagamento de expiração acompanha a remoção de buffs
  no mesmo outline (Enum_Buff_Update), pois a UI ignora Enum_Coin isolado.
  Confirmado que `UpdatePlayerInfo` aplica moedas independentemente desse enum.
- 110 testes passam, incluindo TCP: contagem individual, remoção, +4 uma vez,
  alvos de tiros preservados e nenhum Type_System no fluxo do contador. Não há
  alteração no cliente original, dano ou regra de duração. Reteste visual da
  mira do jogador/bots e crédito no cliente permanece pendente.
### Rocket Launcher aprovado; próximo item Purchase Ban — 2026-09-28

- O jogador confirmou que o Rocket Launcher funcionou após a correção de
  sorteio, consumo das munições reais/falsas, dano proporcional e recarga.
  Marcado como concluído no roteiro de validação manual.
- Próximo item: Purchase Ban (cfg 2022). Validar HUD/ícone no alvo, bloqueio
  das compras durante o próximo turno completo daquele personagem e expiração.
  Se o bot não tentar comprar, consultar o trace para separar decisão da IA de
  bloqueio efetivo.
### Purchase Ban observado; próximo item Wet Cigarettes variante — 2026-09-28

- O trace/sessão registra Purchase Ban (cfg 2022, skill 1021) usado no Bot 1
  às 22:33:19 e às 22:34:34. O Bot 1 chegou aos turnos seguintes e escolheu
  atirar; não houve tentativa de compra observável nesses turnos nem registro
  de compra rejeitada. O jogador relatou que parece funcionar, então fica como
  aprovação provisória, com a limitação da evidência anotada para regressão.
- Sessão terminou com desconexão normal às 22:41:43, sem exceção no log.
- Próximo teste: Wet Cigarettes variante (cfg 2024). Conferir dado, cura,
  consumo e o caso HP 0 com Frenzy restante.
### Correção de terminologia: registros cfg com nome repetido — 2026-09-28

- O jogador questionou “Wet Cigarettes variante” porque esse nome/categoria não
  existe na experiência dele. Confirmado: “variante” foi um rótulo interno nosso
  para distinguir linhas `card_cfg` com mesmo nome localizado e `cfgId`/alvo/skill
  distintos; não é texto de interface.
- A lista `PVP_LAB_SHOP_SPECS` inclui esses registros para testes, embora o
  comentário do servidor já diga que disponibilidade e pesos originais não
  foram recuperados. A aparição no menu `ITEM` ou na loja da cópia não prova que
  sejam ofertas separadas no modo clássico 1/6. Não pedir teste independente de
  cfg 2024/2026/2027/2028/2036/2037 até verificar a disponibilidade por modo.
- O catálogo e o roteiro foram corrigidos para separar nome de interface de
  configuração interna. Próximo item não duplicado no roteiro: Tranquilizer
  (cfg 2029). Nenhuma alteração foi feita ao pool de jogo nesta correção.
### Tranquilizer (cfg 2029): descrição e regra implementadas — 2026-09-28

- A descrição original foi lida dos dados PT/EN do cliente: “Reduza o ponto de
  Desespero do alvo pela metade de seus pontos de vida atuais (arredondado para
  cima)” / “Reduces the target's Frenzy Point(s) by half of their current
  Health Points (rounded up).”
- Implementação: remove `min(Frenzy atual, ceil(HP atual / 2))` como efeito
  instantâneo `Enum_Hp_Vir=14`, atualiza o estado de partida e não adiciona buff
  persistente. Corrigidos usos de loja, item guardado e resolução dos bots.
- Cobertura adicionada para HP 0–4, Frenzy menor que a redução, compra direta e
  item guardado. A conferir manualmente na cópia: HUD/animação, arredondamento
  com HP ímpar, alvo com menos Frenzy que a quantidade calculada e uso em si.

### Tranquilizer: confirmação em partida e próximo teste — 2026-09-29

- O jogador relatou que o efeito funcionou, mas o Bot 2 usou o item no Bot 1
  antes do teste manual planejado. O log de 00:23:00:627 registra a decisão da
  IA: actor=2, target=1, cfg=2029; em seguida, o Bot 2 também usou cfg 2008 no
  jogador e atirou. Assim, o trace confirma ator/alvo/ordem da escolha, e a
  confirmação do efeito do Tranquilizer vem da observação do jogador (não há
  linha separada no log com o delta de Frenzy).
- Marcado como funcional no roteiro, sem alegar validação isolada de uso
  próprio, arredondamento ímpar, item guardado ou animação/HUD.
- Próximo teste naquela ocasião: **Permission Ban (cfg 2030)**; aprovado pelo
  jogador no registro abaixo. O teste seguinte da loja passa a ser Purchase Ban.

### Permission Ban aprovado; Purchase Ban é o próximo item comprável — 2026-09-29

- O jogador confirmou que Permission Ban (cfg 2030) funcionou bem. O log da
  sessão registra compra/uso com `skill=10009`, `target=1`; o resultado do
  bloqueio foi confirmado pelo jogador.
- O próximo reteste da loja é Purchase Ban (cfg 2022): a aplicação no Bot 1 já
  ocorreu em sessões anteriores, mas ainda falta uma tentativa de compra
  durante o turno bloqueado para validar a rejeição diretamente.
- O jogador esclareceu que Piggy Bank (cfg 2034) é equipado antes da partida,
  não comprado na loja. Movido para uma etapa posterior. A implementação local
  já cobre acúmulo/coleta via protocolo; a seleção, HUD e animação ainda exigem
  teste no cliente. A bolsa dourada congelada permanece sem vínculo comprovado
  com o Piggy Bank.

### Laboratório local reiniciado — 2026-09-29 16:35

- Após reinício da máquina, `research/start_local_test.ps1` iniciou o servidor
  local v32 (dificuldade média) e abriu somente o cliente da cópia laboratorial.
  HTTP/Logic/PVP estão vinculados a `127.0.0.1:38000–38002`; `/health` retornou
  `ok=true`, e o log registrou o login do cliente. Sessão: `163513`.
- Na abertura desta sessão, o próximo reteste era Purchase Ban (cfg 2022);
  esse teste foi concluído mais tarde na mesma sessão. Piggy Bank (cfg 2034)
  segue reservado à etapa posterior de itens equipados pré-partida.

### Purchase Ban confirmado pelo jogador; loja pronta para a fase pré-partida — 2026-09-29

- O jogador relata três usos de Purchase Ban no Bot 1 e nenhuma compra dele
  durante os turnos afetados. O log registra dois usos diretos (19:50:56.783 e
  19:52:51.109) e um uso de carta guardada (19:51:42.724), todos com
  `skill=1021`, `target=1`.
- Nos turnos seguintes, o Bot 1 escolheu `kind=shoot`; antes da primeira
  aplicação, a IA tinha escolhido `kind=item` para cfg 2018. O código da IA
  exclui ofertas compráveis quando o buff 1021 está no próprio bot. Assim, o
  padrão observado é consistente com o bloqueio; não há uma tentativa de
  compra rejeitada em pacote separado. Sem erros/exceções no log da sessão.
- No último round, o log confirma Permission Ban (`cfg=2030`, `skill=10009`,
  `target=1`) às 19:52:57; na vez seguinte o Bot 1 atirou e não ativou skill,
  em linha com a confirmação funcional do jogador.
- O jogador aprovou ambos os itens. A etapa comprável única do modo 1/6 está
  fechada; próxima sequência é Piggy Bank (cfg 2034), equipado antes de iniciar
  a partida, conforme o plano do jogador.
# 2026-09-30 — v49: capacidade dos itens de munição

- Usuário confirmou: Bala Real/Falsa +1 não substitui munição; arma cheia bloqueia uso.
- IA corrigida: limite fixo 8 substituído pela capacidade individual do gun_cfg.
- Servidor rejeita uso comprado/guardado antes de cobrar, consumir item ou alterar munição; balas vermelhas também ocupam capacidade.
- Aviso específico de arma cheia / ocultação da seta ainda pendente: a rejeição usa o erro genérico já existente, sem inventar um código nativo.
- Venom: usuário informou que o tiro parece correto; validação completa de cura e duração permanece pendente.
# 2026-09-30 — v50: saldo do refresh e fumaça do veneno

- Trace v49: saldo 6100 antes/depois do tiro real em si às 00:47:27; refreshes anteriores cobraram 300 cada. Usuário identificou HUD atrasada.
- Causa nativa: ClientAnimExpression.ShowUIChange ignora Enum_Coin (4). Refresh Type_System enviava cobrança nesse evento ignorado; alterado apenas o refresh para atualização genérica typ10, mantendo desconto incremental e stock typ83.
- Venom delBuffs agora informa existTyp: 3 quando consumido por cura, 2 quando expira. RemoveBuff usa esses campos para eff_Spider_buff_end; sem eles removia ícone mas não encerrava fumaça.
- Testes de protocolo cobrem tipo processável do refresh e os dois motivos de remoção. Visual e múltiplos refreshes consecutivos aguardam teste manual v50.
# 2026-09-30 — v51: No.13 skill melhorada, primeira etapa

- Conta GM preservada: nenhum saldo, nível, equipamento ou unlock alterado.
- Resolver do urso ativa10004 em starLevel>=5 OU skillUpgradeUnlocked/skillId
  melhorada já persistido. Demais melhorias continuam básicas até executor.
- Lobby GamerHero.skillId e login PvP usam mesma resolução; não depende de
  migração destrutiva do inventário. Bots gerados mantêm básica por padrão,
  executor/IA suportam10004 quando o perfil do bot explicitamente a recebe.
- Básica gasta todos Frenzy; melhorada gasta min(Frenzy, espaço de HP), guarda
  excedente. Toxin reduz recuperação em1 depois do custo, sem devolver custo;
  essa interação é hipótese de execução e requer confirmação manual.
- Animação nativa10004: camera Camera01_BearSkill, sourceAnim47, cutScene1,
  skillShowTime4750ms; mesmos tempos de barreira da básica. CD após uso3.
- Compra/use1135 e normalização UI de compra abaixo5 estrelas ainda pendentes.
- Testes incluem limites HP/Frenzy, ambas condições de desbloqueio, IA/Toxin,
  e integração TCP: login mostra10004, usar com HP3/Frenzy2 resulta HP4/Frenzy1.
# 2026-09-30 — v52: Bucket retirado da loja

- Usuário lembrou que Bucket não era comprável; removido2033 do catálogo de
  abertura/refresh/reposição. Preservado item e pool de recompensas humano.
- Bug de expiração da proteção Bucket confirmado no v51: HUD pode sair e
  booleano servidor permanece até bloquear real. Ainda pendente, não resolvido
  apenas pela retirada da loja; caixa/itens pré-partida podem expor o problema.
- Urso melhorado confirmado manualmente: log15:22:57 skill10004 hpDelta1,
  virDelta-1 preserva excedente. Próxima melhoria: Yu10003, dado6 cura/dano2;
  ainda não implementada, não solicitar teste como pronta.
