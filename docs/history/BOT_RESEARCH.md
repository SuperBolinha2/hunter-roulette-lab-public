# Bot research

## Correção de apresentação v31

Purchase Ban usava cfgId2022 (carta) como buff; cliente registra catálogo
inexistente e omite ícone. Agora usa1021, Permission Ban10018 e Bucket1026,
incluindo seleção/bloqueio/expiração; dados conferidos no bundle da cópia.
Separado `bot_presentation.py`: espera antes da próxima ação, sem atraso novo
da HUD. Skill10001 tem UI nativa4,75s APÓS cutscene nativa4s (callback3,9s);
a antiga barreira6s interrompia essa sequência. Nova reserva9,75s e dado10,4s
(cutscene3,4+UI6+recuperação1), mais pausa decisória0,6s. Cartas consideram
alvo nativo2s e etapas de abertura/efeito; margens ainda exigem teste manual.
138 testes passam;
efeitos HP/Frenzy continuam no pacote da skill, não no tiro posterior. Consulte
`PROGRESS.md` para evidência, ressalvas e reteste; qualidade visual pendente.

## Implementação local v30 — 2026-09-28

- Nova IA integrada à mesa de três participantes. `private-server/bot_ai.py`
  seleciona ações; `bot_actions.py` executa usando pacotes nativos. Dois
  participantes mantêm o caminho antigo; equipes e outros modos são pendentes.
  Original intocado. Backup: `private-server/rollback/2026-09-28-pre-bot-ai/`.
- Utilidade esperada sobre dados públicos: HP/Frenzy, quantidades de balas,
  saldo, buffs, habilidade, estoque e alvo. Não recebe ordem das balas ou
  resultado futuro do dado. Pode mirar outro bot, atirar em si, comprar/usar
  item e usar habilidade suportada. Pesos são projeto local, não IA original.
- Comparamos expectiminimax de Buckshot Roulette, mas adotamos pontuação
  curta para três atores com carregadores próprios, sem IA externa ou busca
  profunda. Referência: https://github.com/CameronScarpati/buckshot-roulette-bot
- As 26 entradas `ITEM_RULES` possuem descrição, efeito e regra de alvo,
  derivados do catálogo/configurações da cópia e correções do jogador.
  Exemplos: curar somente HP recuperável, reforçar bala existente, evitar
  buffs duplicados, bloquear adversário e manipular munição conforme benefício.
- 25 entradas habilitadas possuem executor e teste de protocolo; isso NÃO
  equivale a aprovação visual. Rocket Launcher (2032) agora está habilitado:
  a IA compara chance/dano esperado e executa resultados falso/real, incluindo
  consumo de munição, Frenzy e recarga. Piggy Bank (2034) continua excluído.
  Alucinógeno/Ejector contra munição reforçada ficam fora
  das escolhas até validar esse resolvedor combinado. Outros itens/variantes
  ainda pendentes no catálogo precisam do teste manual, especialmente
  Tranquilizer/Bucket. Habilidades suportadas: 10000 (dado) e 10001 (urso);
  demais habilidades continuam pendentes.
- Compra desconta do bot correto e consome estoque; uso guardado consome seu
  slot. Revalidação impede ação ilegal. Origem/alvo são índices do ator real.
  Ações preparatórias e tiros repetidos têm limites. A mira fica fixa durante
  o disparo; compra/uso tem intervalo de animação antes da próxima ação.
  Bala falsa em si mantém turno; recompensa é coletada pelo próprio bot ao
  encerrar a sequência. Não é prova de qualidade visual: testar no cliente.
- Purchase Ban/Permission Ban têm relógio individual: cobrem o próximo turno
  completo do alvo e expiram no início do seguinte. Compra bloqueada não cobra
  nem consome estoque; item guardado ainda pode ser usado. Mensagem visual ao
  jogador e duração original exata precisam de confirmação.
- Perfis `easy`, `medium`, `hard`: variam risco, alternativas/erros legais e
  orçamento de ações. `scripted` mantém caminho legado para regressão.
  Launcher: `research/start_local_test.ps1 -BotDifficulty medium` (padrão).
  Servidor: `--bot-difficulty hard --bot-seed 7` para escolhas reproduzíveis;
  a semente não fornece conhecimento de balas futuras ao bot.
- Validação: 135 testes passaram (110 antigos + 25 novos), incluindo TCP de
  compra/uso por bots e sequência de tiros falsos em si/coleta. Cobrem escolha
  de outro bot com humano vivo, condições de itens, saldo, bloqueios e limites.
  `py_compile` passou. 10.000 escolhas mediram cerca de 0,027 ms/escolha neste
  PC; isso não mede FPS, rede ou animações. Campanha longa/equilíbrio pendentes.
- `BOT decision` registra ator, dificuldade, ação, alvo, cfgId, pontuação e
  motivo. Correlacionar com o relato visual, não apenas o pacote enviado.

### Teste manual desta etapa

1. Partida nova de três participantes: observar vários turnos e quais bots
   compram/usam itens, atacam entre si e tentam tiros em si.
2. Conferir compra/uso antes de mirar/disparar e mira preservada no alvo.
   Informar nome do bot/item se houver sobreposição ou ação sem efeito.
3. Purchase Ban em um bot: não deve comprar no próximo turno; pode comprar
   depois de expirar. Não comprar posteriormente pode ser decisão estratégica:
   conferir log/saldo/estoque antes de concluir que o bloqueio ficou preso.

## Investigação histórica

## Current classification

`[HIGH CONFIDENCE]` Scenario C, strongly weighted toward server-authoritative bot decisions.

The client contains substantial bot support, but the evidence does not show a complete local decision engine for the original roulette bots.

## Client-side bot material confirmed

- Robot identity/configuration: `robotHeroPoolId`, `robot_hero_pool_cfg`.
- Robot/PVE presentation and mode UI.
- Protocol types: `NotifyRobotPvp`, `NotifyPvpStartRobot`.
- Robot lifecycle/status enums.
- Behavior enum values for shoot, skill, card, login, TCP, next round, event, end, and error.
- General battle state/animation/UI handlers that work for any indexed gamer, including a bot.

## Why the server side is still required

- The player sends only a target index for a shot.
- HP delta, ammunition result, death, round transition, and match end arrive from the server.
- `PvpRobotBehavior` includes network/login/heartbeat and authoritative game-event categories, suggesting original bots participated through server-side orchestration rather than a self-contained client AI.
- `GAME_CMD_INNER_ROBOT_START` exists in the internal server command table.
- The client handler for `255/21` is described as AI recovery/start timing, not as an AI decision tree.

## Practical reuse boundary

Reuse the original client's bot avatar/configuration, animations, UI, mode definitions, and all notification handlers. Reconstruct only the minimal server decision loop needed to select legal behavior and emit the same authoritative notifications.

The initial v9 policy always had the bot target the local player. The current
v29 trio loop still prioritizes index 0 while that player is alive and selects
the other surviving bot only afterwards. This is an explicit emulator heuristic,
not a recovered original decision rule. Target selection, self-shot probability,
shopping, card use and skills remain open implementation work.

## Next proof

Trace every reference to `NotifyPvpStartRobot` and `NotifyRobotPvp` in native code/string metadata, then run a local match where the emulator sends one bot aim/shot sequence. If the client spontaneously chooses the bot action without a server instruction, downgrade the server-authoritative conclusion. If it waits for server notifications, promote it to confirmed.

## Decision-policy investigation — 2026-09-28

Research only: no bot code, live processes or gameplay behavior changed here.
The player asked whether to address bots before Purchase Ban testing.

### Verified local findings

- `server.py`, trio shot handler (3/3): the `bot_target` expression picks the
  human while alive, otherwise another surviving bot. No voluntary self-shot
  candidate is generated. The two-player fallback also uses target 0.
- The bot loop resolves ammunition, Frenzy, death and animated notifications,
  but has no shopping/card/hero-skill decision stage. Existing buffs can affect
  a bot shot; that is not evidence that the bot bought or used them itself.
- Purchase/use handler (3/5) requires `current_pvp_turn == 0`, reads the human's
  coin/card slot and emits human-source item results. Hero-skill handler (3/6)
  similarly reads the human's skill and applies human-source results. Bot use
  needs actor-neutral validation/resolution; calling these branches as if a
  bot were the human would debit the wrong wallet or animate the wrong actor.
- The trio handler builds a sequence of future bot actions and queues their
  frames with animation delays. Any added item/skill action needs ordered
  resolution, fresh state and its own animation settlement; do not insert
  notifications that reset an active shot's selected target.
- Extracted Config_Description_1 declares `RobotFixCfg.tree_id`, `round_num`
  and `robot_id`, plus `RobotIntactCfg.robot_id/sub_tree_type/tree_id`.
  `RobotHeroPoolCfg` exposes heroes, initial cards, guns and skip-TV timing.
  Current copied lua.ab lists robot_hero_pool_cfg, but no RobotIntact/RobotFix
  behavior-tree implementation was recovered in this inspection. Tree IDs are
  references, not a complete AI algorithm or a proven client-enable switch.
- Purchase Ban cfg 2022/skill 1021 currently has generic buff presentation in
  the item implementation matrix. A visual buff alone does not establish a
  server-enforced purchase restriction, correct duration or bot compliance.

### Proposed local approach (not original AI recovered)

Recommend a bounded bot milestone now, before closing Purchase Ban/Permission
Ban. Start with actor-neutral action resolution and a small utility policy,
not a trained model or a large search engine.

1. Shared legal-action validator/resolver for human and bot actors: own wallet,
   slot, skill charge, target rules, restrictions, buffs and round transitions.
   Preserve existing regression scenarios before adding probabilistic choices.
2. Separate observed state from authoritative state. Scoring sees public HP,
   Frenzy, counts of ammo, visible effects, own inventory/coins and explicitly
   revealed next-round information. It must not peek at a hidden bullet result
   or future random dice. Actual results are drawn only after choosing an action.
3. Score action/target pairs: enemy shots for expected damage, elimination and
   Wanted bounty; self-shots for bounty/continuation versus death risk; collect
   for banking the current reward; healing/protection for survivability;
   reload/eject/inject for ammunition advantage. Zero HP disables cigarettes.
   Frenzy changes must enter the evaluation, not just normal hearts.
4. Shopping evaluates affordability, slot replacement, actionable value and
   restrictions. Bot skills initially cover only implemented hero skills;
   unsupported skills/items are not silently treated as working.
5. Weighted choice among near-best legal actions adds variation without a
   fixed human bias. Profiles can adjust aggression, risk and saving. These
   weights are local design choices requiring gameplay tuning, not canon.
6. Commit to one target through the action/animation. Reevaluate only after it
   finishes; cap preparatory actions/turn and repeated self-shots to avoid
   infinite buying, refresh loops, stalls or instant animation overlap.
7. Keep two separate modes: seeded scripted bots for item regression/manual
   diagnosis, and fair utility bots for play. Scripted testing must not become
   a live policy that buys the item under test every turn.

### Acceptance before returning to Purchase Ban

- Tests prove bots can target each other while the human lives; self-shots can
  be selected under a favorable controlled scenario and blanks can continue.
- Purchases charge only the acting bot and consume real shop stock. Card use
  consumes its own slot and emits correct source/target animation indices.
- Purchase Ban refuses a genuinely attempted purchase, without charging or
  consuming stock; expiry reenables buying. Skill bans obey the same contract.
- No cheating: identical observations with different hidden outcomes generate
  identical decisions with the same seed. The selector cannot receive hidden
  outcomes. Unknown future shot results are not pre-drawn for planning.
- Retain all 110 existing tests with controlled bot policy/seed; add protocol
  exchanges for bot purchases, use, self-shots and actor-specific restrictions.
- Run bounded seeded simulations for termination, legality and balance, then
  request manual validation of animation order, aim and pacing. Simulations
  do not prove visual gameplay correctness.

### Primary references used

- Intrinsic Algorithm, IAUS manual: scoring each action-target context from
  world inputs, separate from behavior execution:
  https://www.gameai.com/manuals/index.php/IAUS
- David Graham, Game AI Pro chapter 9: expected utility, weighted selection
  among near-best actions and commitment until action completion:
  https://www.gameaipro.com/GameAIPro/GameAIPro_Chapter09_An_Introduction_to_Utility_Theory.pdf
- Game Creator Utility AI documentation: score curves and legal-action
  conditions; used as architectural reference only, no plugin installation:
  https://docs.gamecreator.io/behavior/utility-ai/nodes/
- Official Steam game description confirms self-blank continuation, offensive
  Frenzy, tactical props and hero-specific skills; it does not publish original
  bot selection rules:
  https://store.steampowered.com/app/3591550/Hunter_Roulette/

### Live trace follow-up — 2026-09-28

- A live Purchase Ban on bot 1 emitted native buff 1021 in the immediate event
  outline but omitted it from the target gamer in the persisted PVP snapshot.
  v32 writes the buff into that snapshot when the ban is applied, for both a
  newly bought item and a stored item, and removes it at the existing deadline.
- Purchase Ban blocks shop purchases only. It does not block a hero skill or
  using a card already in the bot's slot; the observed Bear skill and stored
  Surprise Box were valid. Verification should check that the ban icon persists
  and a shop offer cannot be bought, while the Bear skill remains available.
- In the v32 live retest, the 1021 icon persisted through later snapshots, but
  it was still in the match-end snapshot at turn 14 and no passive removal
  event was traced. The bot chose to shoot rather than attempt a shop purchase,
  so refusal of an attempted purchase and exact expiry timing remain distinct
  checks. Recheck both before marking the shared ban timer complete.
