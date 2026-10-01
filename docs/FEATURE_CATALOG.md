# Catálogo técnico de recursos — snapshot 30/09/2026

[Checklist principal](FEATURE_CHECKLIST.md) · [Estado atual](CURRENT_STATUS.md)

Este apêndice evita perder referências encontradas na auditoria. **Não é uma segunda lista de “pronto”.** As marcações de trabalho ficam na checklist principal; para um detalhe novo, abrir uma linha lá e citar a referência daqui.

## Procedência e como interpretar

- Leitura de `UIWindowList`/registro Lua e tabelas `hero_cfg`, `gun_cfg`, `card_cfg`, `pvp_mode_cfg`, `sub_pvp_mode_cfg` e linguagem inglesa da cópia isolada. Preferência por tabela Steam quando presente.
- São **nomes/IDs e metadados resumidos**, não código do cliente, assets nem dumps completos. O inspector da auditoria permanece no laboratório, fora do pacote compartilhado.
- Registro UI: 265 nomes únicos candidatos extraídos por padrão de texto. Referências comentadas/legadas podem entrar; **não provam janela habilitada nem rota acessível**. Agrupamento abaixo é uma hipótese pelo nome, não um mapa de chamadas certificado.
- Configuração: 590 TextAssets, 321 nomes após agrupar pares com sufixo `_steam`. Podem ser enums, constantes e tabelas auxiliares, não funções de jogador.
- Catálogo: 68 registros de herói (inclui variantes/tutorial), 42 registros de arma (13 com flag de exibição), 359 registros de carta/prop (27 com flag de biblioteca). Não contar cada variante como item novo.
- Prints do jogador confirmam lobby/Other/Season/Main Mode; abrir e testar todas as outras rotas é trabalho futuro.
- Dados desta build podem divergir de outras versões. Um ID vale dentro de sua tabela: `card_cfg.id=2` não é automaticamente `ammo_cfg.id=2`.

## Modos: 35 registros

A coluna participantes é quantidade total configurada, não tamanho de cada equipe. Submodo `-1` é sentinela/entrada indisponível na configuração, não um modo adicional. Interpretar `is_team_mode`/camp com o cliente antes de habilitar regras.

**Status de cada cfgId: AUDITAR.** A partida trio local já foi aprovada, mas isso não prova que todos os cfgIds Classic/Ranked/Hunter Game rodem suas regras originais: o backend pode usar o mesmo fluxo local. Não marcar esta tabela por aparência.

| cfgId | Nome de modo / rótulo localizado | Participantes | Submodos |
| --- | --- | --- | --- |
| 1 | Classic — Hunter Game / 3 Players | 3 | 4, 5, 6 |
| 2 | Single | 2 | — |
| 3 | 新手引导 | 2 | — |
| 4 | 切片 | 2 | — |
| 5 | Ranked — Hunter Game / 3 Players | 3 | -1, -1, 3 |
| 6 | Classic | 3 | — |
| 7 | Trek | 2, 3 | 7, 8, 9 |
| 8 | Custom: Classic | 3 | 10 |
| 9 | Custom: Solo | 2 | 13 |
| 10 | 新手引导 | 2 | — |
| 11 | Classic: 2v2 — Hunter Game / 2v2 | 4 | 20, 21, 22 |
| 12 | Ranked: 2v2 — Hunter Game / 2v2 | 4 | -1, -1, 19 |
| 13 | Custom: 2v2 | 4 | 23 |
| 14 | 生存教学 | 2, 3 | 16 |
| 15 | Ranked: Fate Split — Fate Split / 3 Players | 3 | -1, -1, 26 |
| 16 | Classic: Fate Split — Fate Split / 3 Players | 3 | 27, 28, 29 |
| 17 | Custom: Fate Split | 3 | 30 |
| 18 | Arcade Mode — Fatal Moment | 2 | 31 |
| 19 | Hunter Game / 3 Players | 3 | 32 |
| 20 | Classic: Codex Brawl (3 Players) — Codex Brawl: 3 Players | 3 | 33, 34, 35 |
| 21 | Ranked: Codex Brawl (3 Players) — Codex Brawl: 3 Players | 3 | -1, -1, 41 |
| 22 | Classic: Codex Brawl (2v2) — Codex Brawl: 2v2 | 4 | 36, 37, 38 |
| 23 | Ranked: Codex Brawl (2v2) — Codex Brawl: 2v2 | 4 | -1, -1, 44 |
| 24 | Custom: Codex Brawl (3 Players) | 3 | 45 |
| 25 | Custom: Codex Brawl (2v2) | 4 | 46 |
| 26 | Trial | 2 | 47 |
| 27 | Hunter Game / 2 Players | 2 | 48 |
| 28 | Gamble of Fate | 2 | 49 |
| 29 | Heat Match: Hunter Game (2v2) | 4 | 50 |
| 30 | Heat Match: Codex Brawl (2v2) | 4 | 51 |
| 31 | Classic: Gunfire Hold'em (3 Players) — Gunfire Hold'em: 3 Players | 3 | 52, -1, -1 |
| 32 | Classic: Gunfire Hold'em (2v2) — Gunfire Hold'em: 2v2 | 4 | 55, -1, -1 |
| 33 | Custom: Gunfire Hold'em (3 Players) | 3 | 58 |
| 34 | Custom: Gunfire Hold'em (2v2) | 4 | 59 |
| 35 | Heat Match: Gunfire Hold'em (2v2) | 4 | 60 |

Registros 3/10 são referências de tutorial; 4 é “slice” interno; 14 é ensino de sobrevivência. Traduções de nomes internos não comprovam opções visíveis.

Não há quantidade 6 nesta tabela. “3×3” como seis jogadores continua **não identificado**, diferente de Hunter Game (3 Players). Multiplicadores/preços dependem de submodo/economia; não assumir pelo nome principal.

## Personagens principais e melhorias

Armas não têm um “nível 2” equivalente; as melhorias abaixo pertencem ao herói. Variantes econômicas da skill não devem ser confundidas com outro personagem.

| hero cfgId | Nome | Skill básica | Melhoria |
| --- | --- | --- | --- |
| 0 | Mad Bunny - Yu | 10000 | 10003 |
| 1 | Escaped Bear - No.13 | 10001 | 10004 |
| 13 | Jester Monkey - Mr.R | 10002 | 10013 |
| 14 | Cowboy - Arthur | 10005 | 10014 |
| 15 | Gentle Deer - Shelby | 10020 | 10021 |
| 16 | Pirate Octopus - Annie | 10017 | 10018 |
| 17 | Sweety Cat - Katie | 10022 | 10023 |
| 35 | Tribal Lioness - Diana | 10032 | 10033 |
| 36 | Merc Spider - Vera | 10035 | 10036 |
| 38 | War Eagle - Hawke | 10038 | 10039 |

[Estado de cada herói e acesso à melhoria](FEATURE_CHECKLIST.md#hero--personagens); [pesquisa de estrelas/Enhance Hero](history/HERO_UPGRADE_PLAN.md). No catálogo existem aliases de skill por modo; preservar o contrato e a economia correspondente.

<details>
<summary>Todos os 68 registros de hero_cfg — nomes/skillId, incluindo internos</summary>

| cfgId | Nome recuperado | skillId |
| --- | --- | --- |
| 0 | Mad Bunny - Yu | 10000 |
| 1 | Escaped Bear - No.13 | 10001 |
| 2 | Mad Bunny - Yu | 0 |
| 3 | Escaped Bear - No.13 | 0 |
| 4 | Mad Bunny - Yu | 10000 |
| 5 | Escaped Bear - No.13 | 10001 |
| 7 | Mad Bunny - Yu | 10012 |
| 8 | Escaped Bear - No.13 | 10001 |
| 9 | Mad Bunny - Yu | 10012 |
| 10 | Escaped Bear - No.13 | 10001 |
| 11 | Mad Bunny - Yu | 10000 |
| 12 | Escaped Bear - No.13 | 10001 |
| 13 | Jester Monkey - Mr.R | 10002 |
| 14 | Cowboy - Arthur | 10005 |
| 15 | Gentle Deer - Shelby | 10020 |
| 16 | Pirate Octopus - Annie | 10017 |
| 17 | Sweety Cat - Katie | 10022 |
| 18 | Mad Bunny - Yu | 10000 |
| 19 | Escaped Bear - No.13 | 10001 |
| 20 | Jester Monkey - Mr.R | 10002 |
| 21 | Cowboy - Arthur | 10005 |
| 22 | Mad Bunny - Yu | 10012 |
| 23 | Escaped Bear - No.13 | 10001 |
| 24 | Mad Bunny - Yu | 0 |
| 25 | Escaped Bear - No.13 | 0 |
| 26 | Mad Bunny - Yu | 0 |
| 27 | Hunter - Arthur | 0 |
| 28 | Hunter - No.13 | 0 |
| 29 | Hunter - Mr.R | 0 |
| 30 | Hunter - No.13 | 0 |
| 31 | Hunter - Mr.R | 0 |
| 32 | Hunter - Arthur | 0 |
| 33 | Hunter - Mr.R | 0 |
| 34 | Mad Bunny - Yu | 0 |
| 35 | Tribal Lioness - Diana | 10032 |
| 36 | Merc Spider - Vera | 10035 |
| 37 | Hunter - No.13 | 0 |
| 38 | War Eagle - Hawke | 10038 |
| 39 | Mad Bunny - Yu | 0 |
| 40 | Escaped Bear - No.13 | 0 |
| 41 | Jester Monkey - Mr.R | 0 |
| 42 | Cowboy - Arthur | 0 |
| 43 | Gentle Deer - Shelby | 0 |
| 44 | Pirate Octopus - Annie | 0 |
| 45 | Sweety Cat - Katie | 0 |
| 46 | Tribal Lioness - Diana | 0 |
| 47 | Merc Spider - Vera | 0 |
| 48 | War Eagle - Hawke | 0 |
| 49 | Mad Bunny - Yu | 0 |
| 50 | Escaped Bear - No.13 | 0 |
| 51 | Jester Monkey - Mr.R | 0 |
| 52 | Cowboy - Arthur | 0 |
| 53 | Gentle Deer - Shelby | 0 |
| 54 | Pirate Octopus - Annie | 0 |
| 55 | Sweety Cat - Katie | 0 |
| 56 | Tribal Lioness - Diana | 0 |
| 57 | Merc Spider - Vera | 0 |
| 58 | War Eagle - Hawke | 0 |
| 59 | Mad Bunny - Yu | 10041 |
| 60 | Escaped Bear - No.13 | 10041 |
| 61 | Jester Monkey - Mr.R | 10041 |
| 62 | Cowboy - Arthur | 10041 |
| 63 | Gentle Deer - Shelby | 10041 |
| 64 | Pirate Octopus - Annie | 10041 |
| 65 | Sweety Cat - Katie | 10041 |
| 66 | Tribal Lioness - Diana | 10041 |
| 67 | Merc Spider - Vera | 10041 |
| 68 | War Eagle - Hawke | 10041 |

</details>

## Armas — 13 exibidas no catálogo

| gun cfgId | Nome | Skill/trait configurado |
| --- | --- | --- |
| 0 | Little Maniac | 3 |
| 1 | Screwdriver | 2 |
| 6 | Lady J | 10006 |
| 7 | Grazier | 10007 |
| 12 | Carnivore | 10015 |
| 13 | RedSiren | 10019 |
| 14 | LoveSong | 10016 |
| 21 | Lucky Revolver | 0 (sem trait) |
| 22 | Lucky Shotgun | 0 (sem trait) |
| 34 | Artemis | 10034 |
| 35 | Venom Stinger | 10037 |
| 38 | Ghosts | 10040 |
| 41 | Dealer | 0 (sem trait) |

Flag de exibição não prova posse/desbloqueio. [Validações e pendências de arma](FEATURE_CHECKLIST.md#weapon--armas).

<details>
<summary>Todos os 42 registros de gun_cfg, incluindo não exibidos</summary>

| cfgId | Nome | Skill | Exibição |
| --- | --- | --- | --- |
| 0 | Little Maniac | 3 | 1 |
| 1 | Screwdriver | 2 | 1 |
| 2 | Little Maniac | 0 | 0 |
| 3 | Screwdriver | 0 | 0 |
| 4 | Little Maniac | 0 | 0 |
| 5 | Screwdriver | 2 | 0 |
| 6 | Lady J | 10006 | 1 |
| 7 | Grazier | 10007 | 1 |
| 8 | Little Maniac | 3 | 0 |
| 9 | Screwdriver | 2 | 0 |
| 10 | Little Maniac | 3 | 0 |
| 11 | Screwdriver | 0 | 0 |
| 12 | Carnivore | 10015 | 1 |
| 13 | RedSiren | 10019 | 1 |
| 14 | LoveSong | 10016 | 1 |
| 15 | Little Maniac | 3 | 0 |
| 16 | Screwdriver | 2 | 0 |
| 17 | Lady J | 10006 | 0 |
| 18 | Grazier | 10007 | 0 |
| 19 | Little Maniac | 3 | 0 |
| 20 | Screwdriver | 2 | 0 |
| 21 | Lucky Revolver | 0 | 1 |
| 22 | Lucky Shotgun | 0 | 1 |
| 23 | Lucky Revolver | 0 | 0 |
| 24 | Lucky Shotgun | 0 | 0 |
| 25 | Lucky Revolver | 0 | 0 |
| 26 | Lucky Revolver | 0 | 0 |
| 27 | Lucky Shotgun | 0 | 0 |
| 28 | Lucky Revolver | 0 | 0 |
| 29 | Screwdriver | 2 | 0 |
| 30 | Lady J | 10006 | 0 |
| 31 | Grazier | 10007 | 0 |
| 32 | Lady J | 10006 | 0 |
| 33 | Little Maniac | 3 | 0 |
| 34 | Artemis | 10034 | 1 |
| 35 | Venom Stinger | 10037 | 1 |
| 36 | Lucky Revolver | 0 | 0 |
| 37 | Lucky Shotgun | 0 | 0 |
| 38 | Ghosts | 10040 | 1 |
| 39 | Lucky Revolver | 0 | 0 |
| 40 | Lucky Shotgun | 0 | 0 |
| 41 | Dealer | 0 | 1 |

</details>

## Prop — biblioteca e família 2000

`card_cfg` contém tanto biblioteca base quanto variantes de partida e cartas de outros sistemas. O flag de compra é **metadado desta configuração**, não certificado de execução do servidor. A loja de laboratório tem ajustes de teste: disponibilidade final ainda deve obedecer ao modo.

| cfgId base / biblioteca | Nome | Skill | Biblioteca habilitada | Só pré-partida |
| --- | --- | --- | --- | --- |
| 1 | Ejector | 1000 | Sim | Não |
| 2 | X-Ray Goggles | 1001 | Não | Não |
| 3 | Real Bullet+1 | 1002 | Sim | Não |
| 4 | Blank Bullet+1 | 1003 | Sim | Não |
| 5 | Box of Real Bullets | 1004 | Não | Não |
| 6 | Box of Blank Bullets | 1005 | Não | Não |
| 7 | Spare Magazine | 1006 | Sim | Não |
| 8 | Hallucinogen | 1007 | Sim | Não |
| 9 | Arms Voucher | 1008 | Sim | Não |
| 10 | Tranquilizer | 1009 | Não | Não |
| 11 | Wet Cigarettes | 1010 | Sim | Não |
| 12 | Pack of Cigarettes | 1011 | Não | Não |
| 13 | Stimulant | 1012 | Não | Não |
| 14 | Cigar | 1013 | Não | Não |
| 15 | Maintenance Kit | 1014 | Sim | Não |
| 16 | Burst Mode | 1015 | Sim | Não |
| 17 | Blockade | 1016 | Não | Não |
| 18 | Violation Ticket | 1017 | Sim | Não |
| 19 | Crack the Safe | 1018 | Não | Não |
| 20 | Surprise Box | 1019 | Sim | Não |
| 21 | Wanted | 1020 | Sim | Não |
| 22 | Purchase Ban | 1021 | Sim | Não |
| 23 | Surprise Box | 0 | Não | Não |
| 24 | Wet Cigarettes | 1022 | Não | Não |
| 25 | Hallucinogen | 1023 | Não | Não |
| 26 | Ejector | 1024 | Não | Não |
| 27 | Wet Cigarettes | 1025 | Não | Não |
| 28 | Surprise Box | 1019 | Não | Não |
| 29 | Tranquilizer | 10008 | Sim | Não |
| 30 | Permission Ban | 10009 | Sim | Não |
| 31 | Energy Pump | 10010 | Sim | Não |
| 32 | Rocket Launcher | 10011 | Sim | Não |
| 33 | Bucket | 1026 | Sim | Sim |
| 34 | Piggy Bank | 1028 | Sim | Sim |
| 35 | Blood Bag | 1037 | Sim | Não |
| 36 | Surprise Box | 1038 | Não | Não |
| 37 | Surprise Box | 1039 | Não | Não |
| 38 | Swap Card | 1040 | Sim | Não |
| 39 | Peeking Card | 1041 | Sim | Não |
| 40 | Shuffle Card | 1042 | Sim | Não |
| 41 | Draw Card | 1043 | Sim | Não |
| 42 | Plunder Card | 1044 | Sim | Não |
| 43 | Cut Card | 1045 | Sim | Não |
| 44 | Selection Card | 1046 | Sim | Não |

X-Ray Goggles, caixas de balas, Pack of Cigarettes, Stimulant, Cigar, Blockade e Crack the Safe aparecem em registros base **desabilitados na biblioteca auditada**. São candidatos internos/legados, não itens prometidos para a loja atual.

### Variantes 2000 — 34 registros

| cfgId | Nome | Skill | Só pré-partida | Compra flag |
| --- | --- | --- | --- | --- |
| 2001 | Ejector | 1000 | Não | 1 |
| 2003 | Real Bullet+1 | 1002 | Não | 1 |
| 2004 | Blank Bullet+1 | 1003 | Não | 1 |
| 2007 | Spare Magazine | 1006 | Não | 0 |
| 2008 | Hallucinogen | 1007 | Não | 1 |
| 2009 | Arms Voucher | 1008 | Não | 1 |
| 2011 | Wet Cigarettes | 1010 | Não | 1 |
| 2015 | Maintenance Kit | 1014 | Não | 0 |
| 2016 | Burst Mode | 1015 | Não | 0 |
| 2018 | Violation Ticket | 1017 | Não | 0 |
| 2020 | Surprise Box | 1019 | Não | 0 |
| 2021 | Wanted | 1020 | Não | 1 |
| 2022 | Purchase Ban | 1021 | Não | 1 |
| 2024 | Wet Cigarettes | 1022 | Não | 0 |
| 2025 | Hallucinogen | 1023 | Não | 0 |
| 2026 | Ejector | 1024 | Não | 0 |
| 2027 | Wet Cigarettes | 1025 | Não | 0 |
| 2028 | Surprise Box | 1019 | Não | 0 |
| 2029 | Tranquilizer | 10008 | Não | 1 |
| 2030 | Permission Ban | 10009 | Não | 1 |
| 2031 | Energy Pump | 10010 | Não | 1 |
| 2032 | Rocket Launcher | 10011 | Não | 0 |
| 2033 | Bucket | 1026 | Sim | 1 |
| 2034 | Piggy Bank | 1028 | Sim | 1 |
| 2035 | Blood Bag | 1037 | Não | 0 |
| 2036 | Surprise Box | 1038 | Não | 0 |
| 2037 | Surprise Box | 1039 | Não | 0 |
| 2038 | Swap Card | 1040 | Não | 0 |
| 2039 | Peeking Card | 1041 | Não | 0 |
| 2040 | Shuffle Card | 1042 | Não | 0 |
| 2041 | Draw Card | 1043 | Não | 0 |
| 2042 | Plunder Card | 1044 | Não | 0 |
| 2043 | Cut Card | 1045 | Não | 0 |
| 2044 | Selection Card | 1046 | Não | 0 |

Bucket/Piggy Bank possuem flag pré-partida; o flag de compra não autoriza colocá-los na loja da partida. Variantes com nome igual podem ter skill/pool distinto. [Efeitos confirmados e faltantes](FEATURE_CHECKLIST.md#prop--itens).

<details>
<summary>Todos os 359 registros de card_cfg — nomes e skillIds, incluindo cartas internas/de outros modos</summary>

Esta lista inclui passivas/cartas/modificadores e cópias por modo. Não é uma lista de 359 itens equipáveis diferentes. Antes de criar uma tarefa, conferir se já pertence à mesma família na checklist.

| cfgId | Nome recuperado | skillId |
| --- | --- | --- |
| 1 | Ejector | 1000 |
| 2 | X-Ray Goggles | 1001 |
| 3 | Real Bullet+1 | 1002 |
| 4 | Blank Bullet+1 | 1003 |
| 5 | Box of Real Bullets | 1004 |
| 6 | Box of Blank Bullets | 1005 |
| 7 | Spare Magazine | 1006 |
| 8 | Hallucinogen | 1007 |
| 9 | Arms Voucher | 1008 |
| 10 | Tranquilizer | 1009 |
| 11 | Wet Cigarettes | 1010 |
| 12 | Pack of Cigarettes | 1011 |
| 13 | Stimulant | 1012 |
| 14 | Cigar | 1013 |
| 15 | Maintenance Kit | 1014 |
| 16 | Burst Mode | 1015 |
| 17 | Blockade | 1016 |
| 18 | Violation Ticket | 1017 |
| 19 | Crack the Safe | 1018 |
| 20 | Surprise Box | 1019 |
| 21 | Wanted | 1020 |
| 22 | Purchase Ban | 1021 |
| 23 | Surprise Box | 0 |
| 24 | Wet Cigarettes | 1022 |
| 25 | Hallucinogen | 1023 |
| 26 | Ejector | 1024 |
| 27 | Wet Cigarettes | 1025 |
| 28 | Surprise Box | 1019 |
| 29 | Tranquilizer | 10008 |
| 30 | Permission Ban | 10009 |
| 31 | Energy Pump | 10010 |
| 32 | Rocket Launcher | 10011 |
| 33 | Bucket | 1026 |
| 34 | Piggy Bank | 1028 |
| 35 | Blood Bag | 1037 |
| 36 | Surprise Box | 1038 |
| 37 | Surprise Box | 1039 |
| 38 | Swap Card | 1040 |
| 39 | Peeking Card | 1041 |
| 40 | Shuffle Card | 1042 |
| 41 | Draw Card | 1043 |
| 42 | Plunder Card | 1044 |
| 43 | Cut Card | 1045 |
| 44 | Selection Card | 1046 |
| 1001 | Ejector | 1000 |
| 1003 | Real Bullet+1 | 1002 |
| 1004 | Blank Bullet+1 | 1003 |
| 1007 | Spare Magazine | 1006 |
| 1008 | Hallucinogen | 1007 |
| 1009 | Arms Voucher | 1008 |
| 1011 | Wet Cigarettes | 1010 |
| 1015 | Maintenance Kit | 1014 |
| 1016 | Burst Mode | 1015 |
| 1018 | Violation Ticket | 1017 |
| 1020 | Surprise Box | 1019 |
| 1021 | Wanted | 1020 |
| 1022 | Purchase Ban | 1021 |
| 1024 | Wet Cigarettes | 1022 |
| 1025 | Hallucinogen | 1023 |
| 1026 | Ejector | 1024 |
| 1027 | Wet Cigarettes | 1025 |
| 1028 | Surprise Box | 1019 |
| 1029 | Tranquilizer | 10008 |
| 1030 | Permission Ban | 10009 |
| 1031 | Energy Pump | 10010 |
| 1032 | Rocket Launcher | 10011 |
| 1033 | Bucket | 1026 |
| 1034 | Piggy Bank | 1028 |
| 1035 | Blood Bag | 1037 |
| 1036 | Surprise Box | 1038 |
| 1037 | Surprise Box | 1039 |
| 1038 | Swap Card | 1040 |
| 1039 | Peeking Card | 1041 |
| 1040 | Shuffle Card | 1042 |
| 1041 | Draw Card | 1043 |
| 1042 | Plunder Card | 1044 |
| 1043 | Cut Card | 1045 |
| 1044 | Selection Card | 1046 |
| 2001 | Ejector | 1000 |
| 2003 | Real Bullet+1 | 1002 |
| 2004 | Blank Bullet+1 | 1003 |
| 2007 | Spare Magazine | 1006 |
| 2008 | Hallucinogen | 1007 |
| 2009 | Arms Voucher | 1008 |
| 2011 | Wet Cigarettes | 1010 |
| 2015 | Maintenance Kit | 1014 |
| 2016 | Burst Mode | 1015 |
| 2018 | Violation Ticket | 1017 |
| 2020 | Surprise Box | 1019 |
| 2021 | Wanted | 1020 |
| 2022 | Purchase Ban | 1021 |
| 2024 | Wet Cigarettes | 1022 |
| 2025 | Hallucinogen | 1023 |
| 2026 | Ejector | 1024 |
| 2027 | Wet Cigarettes | 1025 |
| 2028 | Surprise Box | 1019 |
| 2029 | Tranquilizer | 10008 |
| 2030 | Permission Ban | 10009 |
| 2031 | Energy Pump | 10010 |
| 2032 | Rocket Launcher | 10011 |
| 2033 | Bucket | 1026 |
| 2034 | Piggy Bank | 1028 |
| 2035 | Blood Bag | 1037 |
| 2036 | Surprise Box | 1038 |
| 2037 | Surprise Box | 1039 |
| 2038 | Swap Card | 1040 |
| 2039 | Peeking Card | 1041 |
| 2040 | Shuffle Card | 1042 |
| 2041 | Draw Card | 1043 |
| 2042 | Plunder Card | 1044 |
| 2043 | Cut Card | 1045 |
| 2044 | Selection Card | 1046 |
| 10000 | Bucket | 30000 |
| 90010 | Death | 90010 |
| 90020 | The Magician | 90020 |
| 90021 | The Magician | 90021 |
| 90022 | The Magician | 90022 |
| 90030 | The Tower | 90030 |
| 90040 | The Hierophant | 90040 |
| 90050 | The Sun | 90050 |
| 90060 | The Devil | 90060 |
| 90070 | The Chariot | 90070 |
| 100001 | Bucket | 100001 |
| 110001 | Max. Health Points +1 | 110001 |
| 110002 | Max. Frenzy Points +1 | 110002 |
| 110003 | R-Chip +2 | 110003 |
| 110004 | R-Chip +20 | 110004 |
| 110005 | R-Chip +200 | 110005 |
| 110006 | Max. Health Points +2 | 110006 |
| 110007 | Max. Frenzy Points +2 | 110007 |
| 110008 | R-Chips +4 | 110008 |
| 110009 | R-Chips +40 | 110009 |
| 110010 | R-Chips +400 | 110010 |
| 111011 | Midas Touch | 111011 |
| 111012 | Midas Touch | 111012 |
| 111013 | Midas Touch | 111013 |
| 111021 | Glitch Out | 111021 |
| 111071 | Reasonable Income | 111071 |
| 111072 | Reasonable Income | 111072 |
| 111073 | Reasonable Income | 111073 |
| 111151 | Relief Fund | 111151 |
| 111152 | Relief Fund | 111152 |
| 111153 | Relief Fund | 111153 |
| 111271 | Accident Insurance | 111271 |
| 111291 | Side Effect | 111291 |
| 111292 | Side Effect | 111292 |
| 111293 | Side Effect | 111293 |
| 111301 | Prop Collector | 111301 |
| 111321 | Rebate | 111321 |
| 111331 | Last-Ditch Earnings | 111331 |
| 111332 | Last-Ditch Earnings | 111332 |
| 111333 | Last-Ditch Earnings | 111333 |
| 111351 | Life Conversion | 111351 |
| 111381 | Rebound | 111381 |
| 111382 | Rebound | 111382 |
| 111383 | Rebound | 111383 |
| 111391 | Redemption | 111391 |
| 111392 | Redemption | 111392 |
| 111393 | Redemption | 111393 |
| 111521 | Endless | 111521 |
| 112091 | Never-Ending | 112091 |
| 112101 | Hostile Takeover | 112101 |
| 112102 | Hostile Takeover | 112102 |
| 112103 | Hostile Takeover | 112103 |
| 112111 | Lucky Gun | 112111 |
| 112121 | Buttered Bread | 112121 |
| 112131 | Delayed Start | 112131 |
| 112132 | Delayed Start | 112132 |
| 112133 | Delayed Start | 112133 |
| 112141 | Maximum Utility | 112141 |
| 112142 | Maximum Utility | 112142 |
| 112143 | Maximum Utility | 112143 |
| 112161 | Investment Strategy | 112161 |
| 112162 | Investment Strategy | 112162 |
| 112163 | Investment Strategy | 112163 |
| 112181 | Fire Sale | 112181 |
| 112191 | Treasure Bag | 112191 |
| 112211 | Worth the Wait | 112211 |
| 112212 | Worth the Wait | 112212 |
| 112213 | Worth the Wait | 112213 |
| 112231 | Full-Charge Crit | 112231 |
| 112241 | Stress Loading | 112241 |
| 112251 | Power Bank | 112251 |
| 112281 | Useful Material | 112281 |
| 112411 | Lucky Break | 112411 |
| 112461 | Lightweight Boost | 112461 |
| 112471 | Charged Strike | 112471 |
| 112541 | Buy One, Get One | 112541 |
| 112551 | Soul Shepherd | 112551 |
| 112561 | High Stakes I | 112561 |
| 112571 | Singer | 112571 |
| 112581 | Hunting Time | 112581 |
| 112591 | Localized Necrosis | 112591 |
| 112601 | Overflow | 112601 |
| 112611 | Lucky Party | 112611 |
| 112621 | Big Smile | 112621 |
| 113031 | Damaged Backpack | 113031 |
| 113041 | No Exceptions | 113041 |
| 113051 | Fortune's Favor | 113051 |
| 113052 | Fortune's Favor | 113052 |
| 113053 | Fortune's Favor | 113053 |
| 113061 | Barrel Warm-Up | 113061 |
| 113081 | Enhanced Magazine | 113081 |
| 113201 | Declare Attack | 113201 |
| 113221 | Primed | 113221 |
| 113261 | Golden Scale Armor | 113261 |
| 113262 | Golden Scale Armor | 113262 |
| 113263 | Golden Scale Armor | 113263 |
| 113311 | Spendthrift | 113311 |
| 113312 | Spendthrift | 113312 |
| 113313 | Spendthrift | 113313 |
| 113341 | Dual Repair | 113341 |
| 113371 | Giant | 113371 |
| 113401 | Simple Math | 113401 |
| 113431 | Positive Cycle | 113431 |
| 113441 | Aftershock | 113441 |
| 113451 | Emergency Bucket | 113451 |
| 113481 | Real Bullet+2 | 113481 |
| 113491 | Golden Arms Voucher | 113491 |
| 113501 | Overclocked Energy Pump | 113501 |
| 113631 | Giant Slayer | 113631 |
| 113651 | Nomad | 113651 |
| 113661 | Cthulhu | 113661 |
| 113671 | Storm | 113671 |
| 113681 | Basic Training | 113681 |
| 113691 | Blank & Real Swap | 113691 |
| 113701 | High Stakes II | 113701 |
| 121011 | Midas Touch | 121011 |
| 121021 | Glitch Out | 121021 |
| 121071 | Reasonable Income | 121071 |
| 121151 | Relief Fund | 121151 |
| 121271 | Accident Insurance | 121271 |
| 121291 | Side Effect | 121291 |
| 121301 | Prop Collector | 121301 |
| 121321 | Rebate | 121321 |
| 121331 | Last-Ditch Earnings | 121331 |
| 121351 | Life Conversion | 121351 |
| 121361 | Heart Container I | 121361 |
| 121371 | Frenzy Container I | 121371 |
| 122091 | Never-Ending | 122091 |
| 122101 | Hostile Takeover | 122101 |
| 122111 | Lucky Gun | 122111 |
| 122121 | Buttered Bread | 122121 |
| 122131 | Delayed Start | 122131 |
| 122141 | Maximum Utility | 122141 |
| 122161 | Investment Strategy | 122161 |
| 122181 | Fire Sale | 122181 |
| 122191 | Treasure Bag | 122191 |
| 122211 | Worth the Wait | 122211 |
| 122231 | Full-Charge Crit | 122231 |
| 122241 | Stress Loading | 122241 |
| 122251 | Power Bank | 122251 |
| 122281 | Useful Material | 122281 |
| 122301 | Lucky Break | 122301 |
| 122311 | Aftershock | 122311 |
| 122321 | Charged Strike | 122321 |
| 122331 | Double Bounty | 122331 |
| 122341 | Weakening Strike | 122341 |
| 122351 | Suppression | 122351 |
| 122361 | Double Surprise | 122361 |
| 123031 | Damaged Backpack | 123031 |
| 123041 | No Exceptions | 123041 |
| 123051 | Fortune's Favor | 123051 |
| 123061 | Barrel Warm-Up | 123061 |
| 123081 | Enhanced Magazine | 123081 |
| 123201 | Declare Attack | 123201 |
| 123221 | Primed | 123221 |
| 123261 | Golden Scale Armor | 123261 |
| 123311 | Spendthrift | 123311 |
| 123341 | Dual Repair | 123341 |
| 123401 | Simple Math | 123401 |
| 123411 | Have It Both Ways | 123411 |
| 123421 | Frenzy Herald | 123421 |
| 123431 | Heart Container II | 123431 |
| 123441 | Frenzy Container II | 123441 |
| 123451 | Positive Cycle | 123451 |
| 123461 | Lightweight Boost | 123461 |
| 123471 | Emergency Bucket | 123471 |
| 123481 | Bounty Bonus | 123481 |
| 123491 | Violent Collection | 123491 |
| 123501 | Lady J's Counterattack | 123501 |
| 123511 | Firepower Accumulation | 123511 |
| 123521 | Taxation | 123521 |
| 123531 | Double Crit | 123531 |
| 123541 | Self-Healing | 123541 |
| 123551 | A Little More | 123551 |
| 123561 | Disarm | 123561 |
| 123571 | Critical Strike | 123571 |
| 123581 | Red-Eye Moment | 123581 |
| 123591 | Extreme Challenge | 123591 |
| 123601 | Stun | 123601 |
| 131011 | Midas Touch | 131011 |
| 131021 | Glitch Out | 131021 |
| 131071 | Reasonable Income | 131071 |
| 131151 | Relief Fund | 131151 |
| 131271 | Accident Insurance | 131271 |
| 131291 | Side Effect | 131291 |
| 131301 | Prop Collector | 131301 |
| 131331 | Last-Ditch Earnings | 131331 |
| 131351 | Life Conversion | 131351 |
| 132091 | Never-Ending | 132091 |
| 132111 | Lucky Gun | 132111 |
| 132121 | Buttered Bread | 132121 |
| 132141 | Maximum Utility | 132141 |
| 132181 | Fire Sale | 132181 |
| 132191 | Treasure Bag | 132191 |
| 132211 | Worth the Wait | 132211 |
| 132231 | Full-Charge Crit | 132231 |
| 132241 | Stress Loading | 132241 |
| 132251 | Power Bank | 132251 |
| 132281 | Useful Material | 132281 |
| 132301 | Lucky Break | 132301 |
| 132311 | Lightweight Boost | 132311 |
| 132321 | Charged Strike | 132321 |
| 133031 | Damaged Backpack | 133031 |
| 133041 | No Exceptions | 133041 |
| 133061 | Barrel Warm-Up | 133061 |
| 133081 | Enhanced Magazine | 133081 |
| 133201 | Declare Attack | 133201 |
| 133221 | Primed | 133221 |
| 133261 | Golden Scale Armor | 133261 |
| 133341 | Dual Repair | 133341 |
| 133411 | Have It Both Ways | 133411 |
| 133451 | Positive Cycle | 133451 |
| 133461 | Aftershock | 133461 |
| 133471 | Emergency Bucket | 133471 |
| 133481 | Super Lucky | 133481 |
| 133491 | Tactical Charge | 133491 |
| 133501 | Super Bear | 133501 |
| 133511 | Desperado | 133511 |
| 133521 | Damaged Backpack+ | 133521 |
| 133531 | Bullet Upgrade | 133531 |
| 133541 | Lucky Gun+ | 133541 |
| 133551 | Initial Boost | 133551 |
| 133561 | Gift | 133561 |
| 133571 | Real Bullet Awakening | 133571 |
| 133581 | Blessing in Disguise | 133581 |
| 133591 | Battle-Hardened | 133591 |
| 133601 | Firepower Cycle | 133601 |
| 133611 | Glitch Out+ | 133611 |
| 133621 | Blank-to-Real | 133621 |
| 133631 | Super Double | 133631 |
| 133641 | Pain Conversion | 133641 |
| 133651 | Second Wind | 133651 |
| 133661 | Ad Nauseam | 133661 |
| 133671 | Diamond Frenzy | 133671 |
| 133681 | Deadly Toxin | 133681 |
| 144011 | Cutoff | 144011 |
| 144021 | Bad Luck | 144021 |
| 144031 | Monopoly | 144031 |
| 144041 | Evaporation | 144041 |
| 144051 | Zero Out | 144051 |
| 144061 | No Healing | 144061 |
| 144071 | Eject | 144071 |
| 144081 | Bankruptcy | 144081 |
| 144091 | Barren | 144091 |
| 144101 | Corrosion | 144101 |
| 144111 | Poisoned | 144111 |
| 144121 | Blanking | 144121 |

</details>

## Janelas — 265 referências candidatas

Referências `UI-001...` são um índice deste snapshot. Manter IDs existentes ao acrescentar novos nomes; não renumerar pela ordenação. Para testar uma janela: identificar rota pai, abrir, verificar as ações/retornos e o estado persistido. **Não marcar “feito” só porque o nome aparece abaixo.**

Agrupamento é inferido por nome. Exemplo: uma janela com “Card” pode pertencer a equipamento de herói, não ao menu Prop. Nome sobreposto/comentado exige confirmar chamada real no cliente.

<details>
<summary>Login / conta / tutorial — 35 referências candidatas</summary>

| Ref. | Nome interno da janela |
| --- | --- |
| UI-007 | `ArcadeBaseGuideWindow` |
| UI-008 | `ArcadeBaseGuideWindow_Over` |
| UI-037 | `GuideBar` |
| UI-038 | `GuideWindow` |
| UI-052 | `LoginAccountCenterWindow` |
| UI-053 | `LoginBGWindow` |
| UI-054 | `LoginErrTipWindow` |
| UI-055 | `LoginLanguageWindow` |
| UI-056 | `LoginLineUpWindow` |
| UI-057 | `LoginNewBieWindow` |
| UI-058 | `LoginkoreaServeWindow` |
| UI-083 | `PrizeCode` |
| UI-106 | `RouletteGuideReviewWindow` |
| UI-130 | `SelectAudioLanguage` |
| UI-135 | `SelectRoleWindow` |
| UI-150 | `TexasGuideRuleWindow` |
| UI-151 | `TouristCreateRoleWindow` |
| UI-152 | `TouristMaskWindow` |
| UI-153 | `TouristTipWindow` |
| UI-180 | `UTouristTopMaskWindow` |
| UI-181 | `UnLockNewFunction` |
| UI-182 | `UnLockNewProps` |
| UI-209 | `_LoginAreaConfirmWindow` |
| UI-210 | `_LoginAreaSelectWindow` |
| UI-211 | `_LoginEnterWindow` |
| UI-212 | `_LoginGooglePgsBtnWindow` |
| UI-213 | `_LoginKoreaPolicy` |
| UI-214 | `_LoginNoticeCom` |
| UI-215 | `_LoginPrivacyPolicyWindow` |
| UI-216 | `_LoginRegWindow` |
| UI-217 | `_LoginServerWindow` |
| UI-218 | `_LoginWindow` |
| UI-219 | `_LoginWindowSelect` |
| UI-222 | `_PhoneRebindWindow` |
| UI-262 | `_UnderageLoginNotice` |

</details>

<details>
<summary>Hero / personagem — 13 referências candidatas</summary>

| Ref. | Nome interno da janela |
| --- | --- |
| UI-107 | `RouletteHeroCampSelectWindow` |
| UI-108 | `RouletteHeroEquipmentWindow` |
| UI-109 | `RouletteHeroListWindow` |
| UI-208 | `_HeroStoryWindow` |
| UI-237 | `_RouletteHeroBadgeWindow` |
| UI-238 | `_RouletteHeroCardWindow` |
| UI-239 | `_RouletteHeroFightRewardWindow` |
| UI-240 | `_RouletteHeroGunChooseWindow` |
| UI-241 | `_RouletteHeroShowWindow` |
| UI-242 | `_RouletteHeroSkillPreviewWindow` |
| UI-243 | `_RouletteHeroSkillUpdateWindow` |
| UI-244 | `_RouletteHeropreviewWindow` |
| UI-251 | `_RouletteStarPromotionWindow` |

</details>

<details>
<summary>Weapon / arma — 4 referências candidatas</summary>

| Ref. | Nome interno da janela |
| --- | --- |
| UI-040 | `GunMainWindow` |
| UI-041 | `GunShowEditorWindow` |
| UI-132 | `SelectGunListWindow` |
| UI-204 | `_GunInfoWindow` |

</details>

<details>
<summary>Prop / cartas / poker — 18 referências candidatas</summary>

| Ref. | Nome interno da janela |
| --- | --- |
| UI-003 | `ActivityPoker_AllCardWindow` |
| UI-004 | `ActivityPoker_CardGain` |
| UI-005 | `ActivityPoker_CardPreviewWindow` |
| UI-006 | `ActivityPoker_MainWindow` |
| UI-010 | `ArkClashGameRuseltWindow` |
| UI-023 | `ClickClashCardItemTipsWindow` |
| UI-075 | `Normal_AllCardWindow` |
| UI-089 | `RouletteArkClashShowWindow` |
| UI-090 | `RouletteArkClashWindow` |
| UI-104 | `RouletteCardLibraryWindow` |
| UI-124 | `RouletteTrialFailChooseCardWindow` |
| UI-125 | `RouletteTrialFirstFreeCardWindow` |
| UI-126 | `RouletteTrialFreeCardWindow` |
| UI-134 | `SelectPropsListWindow` |
| UI-162 | `TrekPropsSelectWindow` |
| UI-187 | `_ArkClashRuleWindow` |
| UI-199 | `_ClashDetailWindow` |
| UI-255 | `_TexasdDetailWindow` |

</details>

<details>
<summary>Supply Box — 10 referências candidatas</summary>

| Ref. | Nome interno da janela |
| --- | --- |
| UI-084 | `PrizedrawPreviewWindow` |
| UI-105 | `RouletteExploreBoxMainWindow` |
| UI-120 | `RouletteTempTreasureBoxOperationWindow` |
| UI-138 | `ShootingOpenBoxWindow` |
| UI-154 | `TreasureBoxOpenAllWindow` |
| UI-155 | `TreasureBoxOpenWindow` |
| UI-156 | `TreasureBoxRewardWindow` |
| UI-235 | `_RouletteExploreBoxGetNewBoxWindow` |
| UI-236 | `_RouletteExploreBoxTeamInfoWindow` |
| UI-259 | `_TreasurePreviewWindow` |

</details>

<details>
<summary>Base / caixas domésticas — 4 referências candidatas</summary>

| Ref. | Nome interno da janela |
| --- | --- |
| UI-091 | `RouletteBaseLevelUpWindow` |
| UI-110 | `RouletteHomeLevelWindow` |
| UI-205 | `_HallHomeDailyRewardWindow` |
| UI-206 | `_HallHomeTransToGold` |

</details>

<details>
<summary>Backpack — 9 referências candidatas</summary>

| Ref. | Nome interno da janela |
| --- | --- |
| UI-188 | `_BagPropChoice` |
| UI-189 | `_BagPropSaleCom` |
| UI-190 | `_BagPropSaleEnsure` |
| UI-191 | `_BagPropUseCom` |
| UI-192 | `_BagPropUseEnsure` |
| UI-193 | `_BagPropUseWithKeyCom` |
| UI-194 | `_BagSyntheticWindow` |
| UI-223 | `_PlayerGameBagWindow` |
| UI-252 | `_RouletteTrialPlayerBag` |

</details>

<details>
<summary>Shop / compras — 15 referências candidatas</summary>

| Ref. | Nome interno da janela |
| --- | --- |
| UI-034 | `FirstChargeWindow` |
| UI-065 | `MallGoodsBuyPanel` |
| UI-102 | `RouletteBuyConfirmWindow` |
| UI-103 | `RouletteBuyOutLookConfirmWindow` |
| UI-111 | `RouletteLimitPackWindow` |
| UI-117 | `RouletteRechargeConfirmWindow` |
| UI-128 | `RouletteTrialShopWindow` |
| UI-139 | `ShopBridgeSubWindow` |
| UI-140 | `ShopBridgeWindow` |
| UI-141 | `ShopConfirmationSingleWindow` |
| UI-142 | `ShopConfirmationWindow` |
| UI-143 | `ShopGiftPackageWindow` |
| UI-144 | `ShopTab` |
| UI-145 | `ShopWindow` |
| UI-253 | `_RouletteWishListWindow` |

</details>

<details>
<summary>Clan — 10 referências candidatas</summary>

| Ref. | Nome interno da janela |
| --- | --- |
| UI-018 | `ClanCreateWindow` |
| UI-019 | `ClanListWindow` |
| UI-020 | `ClanMainWindow` |
| UI-021 | `ClanMatchMainWindow` |
| UI-022 | `ClanMatchShowWindow` |
| UI-039 | `GuildApplicationWindow` |
| UI-195 | `_ClanInfoWindow` |
| UI-196 | `_ClanMatchInviteWindow` |
| UI-197 | `_ClanMatchRuleWindow` |
| UI-198 | `_ClanMatchViewRewardWindow` |

</details>

<details>
<summary>Friend / chat — 10 referências candidatas</summary>

| Ref. | Nome interno da janela |
| --- | --- |
| UI-035 | `FriendWindow` |
| UI-067 | `MatchFriendsCom` |
| UI-165 | `UChatConnectingWindow` |
| UI-202 | `_FriendContactBindWindow` |
| UI-231 | `_RouletteChatPopup` |
| UI-232 | `_RouletteChatReportWindow` |
| UI-233 | `_RouletteChatWindow` |
| UI-234 | `_RouletteChatWindowList` |
| UI-245 | `_RouletteInteractRewardWindow` |
| UI-246 | `_RouletteInteractTipsWindow` |

</details>

<details>
<summary>Temporada / tarefas / passes / ranking — 20 referências candidatas</summary>

| Ref. | Nome interno da janela |
| --- | --- |
| UI-001 | `AchievementLevelWindow` |
| UI-002 | `AchievementMainWindow` |
| UI-027 | `CommonTab_RankingList` |
| UI-030 | `DailyTaskWindow` |
| UI-072 | `NewSeasonInfoWindow` |
| UI-074 | `NewbieSignIn` |
| UI-085 | `RankAppealWindow` |
| UI-086 | `RankPreviewWindow` |
| UI-087 | `RankSeasonSettlementWindow` |
| UI-088 | `RookieTaskWindow` |
| UI-092 | `RouletteBattlePassWindow` |
| UI-113 | `RouletteNewPlayerPassWindow` |
| UI-116 | `RouletteRankingListWindow` |
| UI-146 | `SignInActivity` |
| UI-225 | `_RouletteBattlePassBuyLevelWindow` |
| UI-226 | `_RouletteBattlePassBuyVipWindow` |
| UI-227 | `_RouletteBattlePassRewardWindow` |
| UI-247 | `_RouletteNewPlayerPassBuyVipWindow` |
| UI-248 | `_RouletteNewPlayerPassRewardWindow` |
| UI-250 | `_RouletteRankingListRewardWindow` |

</details>

<details>
<summary>Adventure / eventos — 27 referências candidatas</summary>

| Ref. | Nome interno da janela |
| --- | --- |
| UI-009 | `ArcadeMatchWindow` |
| UI-015 | `BattleResultWindow_Arcade` |
| UI-059 | `LotteryActivityMainWindow` |
| UI-060 | `LotteryActivityTab` |
| UI-061 | `LotteryActivityWindow` |
| UI-062 | `LotteryRewardNewWindow` |
| UI-063 | `LotteryTipsWindow` |
| UI-100 | `RouletteBattleWindow_Arcade` |
| UI-121 | `RouletteTournamentShowWindow` |
| UI-122 | `RouletteTournamentWindow` |
| UI-123 | `RouletteTrialEnemynfoWindow` |
| UI-127 | `RouletteTrialResultWindow` |
| UI-147 | `SlotMachineWindow` |
| UI-148 | `SurvivalChallengeWindow` |
| UI-149 | `SurvivalChallenge_Confirm` |
| UI-157 | `TrekContinueTipsWindow` |
| UI-158 | `TrekDeadWindow` |
| UI-159 | `TrekExitTipsWindow` |
| UI-160 | `TrekModeBlankWindow` |
| UI-161 | `TrekModeWindow` |
| UI-163 | `TrekWinWindow` |
| UI-164 | `TrekrewardWindow` |
| UI-186 | `_ArcadeDetailWindow` |
| UI-256 | `_TournamentRankListBetWindow` |
| UI-257 | `_TournamentRuleWindow` |
| UI-258 | `_TournamentviewRewardWindow` |
| UI-260 | `_TrialSecondconfirm` |

</details>

<details>
<summary>Custom / salas / equipe — 10 referências candidatas</summary>

| Ref. | Nome interno da janela |
| --- | --- |
| UI-068 | `MatchTeammatesCom` |
| UI-093 | `RouletteBattleRoomApplyChangeSlotTipsWindow` |
| UI-094 | `RouletteBattleRoomHUDWindow` |
| UI-095 | `RouletteBattleRoomHallWindow` |
| UI-096 | `RouletteBattleRoomHallWindow_new` |
| UI-097 | `RouletteBattleRoomInviteTipsWindow` |
| UI-098 | `RouletteBattleRoomWindow` |
| UI-228 | `_RouletteBattleRoomPreparationDetailsInfoWindow` |
| UI-229 | `_RouletteBattleRoomPreparationWindow` |
| UI-230 | `_RouletteBattleRoomSettingWindow` |

</details>

<details>
<summary>Espectador / apostas / histórico — 12 referências candidatas</summary>

| Ref. | Nome interno da janela |
| --- | --- |
| UI-011 | `BattleRecordDetailWindow` |
| UI-012 | `BattleRecordSimWindow` |
| UI-013 | `BattleResultOB` |
| UI-076 | `ObBetWindow` |
| UI-080 | `PlayerBattleReportWindow` |
| UI-114 | `RouletteOBWindow` |
| UI-115 | `RouletteObBattlelistHallWindow` |
| UI-220 | `_Obj_BattleWindowTips` |
| UI-221 | `_Obj_Rob_DetailWindow` |
| UI-263 | `_obj_bethistory` |
| UI-264 | `gotoOBWindow` |
| UI-265 | `playerob_details` |

</details>

<details>
<summary>Setting / Other / debug — 12 referências candidatas</summary>

| Ref. | Nome interno da janela |
| --- | --- |
| UI-036 | `GameGMWindow` |
| UI-064 | `LuaDebugWindow` |
| UI-078 | `PWGWebViewWindow` |
| UI-079 | `PcQuitGameWindow` |
| UI-131 | `SelectContactUs` |
| UI-133 | `SelectLanguage` |
| UI-136 | `SettingWindow` |
| UI-137 | `SettingWindow_steam` |
| UI-183 | `UpdateVideoWindow` |
| UI-203 | `_GMDropWindow` |
| UI-254 | `_TestList` |
| UI-261 | `_UMailWindow` |

</details>

<details>
<summary>Lobby / partida / infraestrutura UI — 56 referências candidatas</summary>

| Ref. | Nome interno da janela |
| --- | --- |
| UI-014 | `BattleResultWindow` |
| UI-016 | `BgWindow` |
| UI-017 | `ChangeHeadIconWindow` |
| UI-024 | `ClickItemTipsWindow` |
| UI-025 | `CommonConfirmWindow` |
| UI-026 | `CommonTab` |
| UI-028 | `CommonTitleBar` |
| UI-029 | `ConfirmWindow` |
| UI-031 | `DialogWindow` |
| UI-032 | `DialogueWindow` |
| UI-033 | `ErrWindow` |
| UI-042 | `HallFaceWindow` |
| UI-043 | `HallMusicPlayWindow` |
| UI-044 | `HallNameBoardRoot` |
| UI-045 | `HallPlayerCollectorWindow` |
| UI-046 | `HallPlayerInfoCom` |
| UI-047 | `HallPlayerInfoWindow` |
| UI-048 | `HallPopupWindowBridge` |
| UI-049 | `HallRootWindow` |
| UI-050 | `HallTitleBar` |
| UI-051 | `IntroductionWindow` |
| UI-066 | `MatchBtnCom` |
| UI-069 | `MatchTitleCom` |
| UI-070 | `MatchWindow` |
| UI-071 | `MatchWindowBg` |
| UI-073 | `NewSelectModeWindow` |
| UI-077 | `OtherPlayerInfoWindow` |
| UI-081 | `PlayerInfoWindow` |
| UI-082 | `PlayerRenameWindow` |
| UI-099 | `RouletteBattleWindow` |
| UI-101 | `RouletteBattleWindow_Single` |
| UI-112 | `RouletteMatchingWindow` |
| UI-118 | `RouletteSelfAdWindow` |
| UI-119 | `RouletteSpecialRewardWindow` |
| UI-129 | `ScrolAnnouncement` |
| UI-166 | `UCommitLogWindow` |
| UI-167 | `UConnectingWindow` |
| UI-168 | `UErrorWindow` |
| UI-169 | `UGlobalPreviewWindow` |
| UI-170 | `UGlobalRewardWindow` |
| UI-171 | `UGlobalRewardWindowNew` |
| UI-172 | `ULoadingMaskWindow` |
| UI-173 | `ULoadingWindow` |
| UI-174 | `UNetWorkMaskWindow` |
| UI-175 | `UPVPConnectingWindow` |
| UI-176 | `UPopUpWindow` |
| UI-177 | `UPromptWindow` |
| UI-178 | `UTopMaskWindow` |
| UI-179 | `UTopMaskWindow_SyncUI` |
| UI-184 | `UserWindow` |
| UI-185 | `VsLoadingWindow` |
| UI-200 | `_CommonGetWindow` |
| UI-201 | `_CommonRenameWindow` |
| UI-207 | `_HallTreasureTimeUI` |
| UI-224 | `_PopupNoticeWindow` |
| UI-249 | `_RouletteOpenBoxWindow` |

</details>

## Famílias de configuração — inventário de cobertura

A árvore principal considera as famílias abaixo, mas seu suporte ainda exige auditoria funcional:

| Área | Exemplos de fontes encontradas | O que investigar |
| --- | --- | --- |
| Login/tutorial | server_list, region, guide, novice/new_guild | Rotas reais, conta inicial e progresso |
| Hero/arma/item | hero_star, hero_up, skill, gun, ammo, card | Condição de desbloqueio e efeito |
| Base/caixas | home, treasure_box, explore_box | Temporizador, custo, raridade e prêmio |
| Shop/economia | item_shop, recharge, gift_package, limit_time_pack | Transação, limites e entrega |
| Social | clan, chat, mail, business_card | Estado por conta e interação real |
| Season/progresso | season, top, day_task, achievement, battle_pass | Pontos, reset e resgate único |
| Modos | pvp_mode, sub_pvp_mode, journey, pve, arcade, championship | Regras próprias; não fallback |
| Cartas especiais | pvp_clash, pvp_texas, act_poker | Deck/mão, informação e efeitos |
| Apresentação | anim, cut_scene, effect, audio, scene_player_pos | Câmera, som, sequência e HUD |
| Plataformas/legado | admob, phone, tourist, Korea/Google UI | Separar mobile/Steam; não recriar sem confirmar necessidade |

<details>
<summary>321 famílias de nomes agrupados — cobertura técnica (590 TextAssets)</summary>

São somente identificadores de configuração. Sufixo Steam é agrupado, mas as versões **não devem ser fundidas como se fossem iguais**.

| Família | TextAssets encontrados |
| --- | --- |
| `act_ark_brawl_base` | `act_ark_brawl_base`, `act_ark_brawl_base_steam` |
| `act_ark_brawl_shop` | `act_ark_brawl_shop`, `act_ark_brawl_shop_steam` |
| `act_ark_brawl_topic` | `act_ark_brawl_topic`, `act_ark_brawl_topic_steam` |
| `act_poker_cfg` | `act_poker_cfg`, `act_poker_cfg_steam` |
| `act_poker_race_cfg` | `act_poker_race_cfg`, `act_poker_race_cfg_steam` |
| `act_poker_type_cfg` | `act_poker_type_cfg`, `act_poker_type_cfg_steam` |
| `activity_base_open` | `activity_base_open`, `activity_base_open_steam` |
| `activity_progress_invert` | `activity_progress_invert` |
| `activity_task_cfg` | `activity_task_cfg`, `activity_task_cfg_steam` |
| `activity_task_rookie_cfg` | `activity_task_rookie_cfg`, `activity_task_rookie_cfg_steam` |
| `admob_rewardad_cfg` | `admob_rewardad_cfg`, `admob_rewardad_cfg_steam` |
| `ammo_cfg` | `ammo_cfg`, `ammo_cfg_steam` |
| `ammo_continue_shoot_self_cfg` | `ammo_continue_shoot_self_cfg`, `ammo_continue_shoot_self_cfg_steam` |
| `ammo_fix_cfg` | `ammo_fix_cfg`, `ammo_fix_cfg_steam` |
| `ammo_init_reward_cfg` | `ammo_init_reward_cfg`, `ammo_init_reward_cfg_steam` |
| `ammo_reward_cfg` | `ammo_reward_cfg`, `ammo_reward_cfg_steam` |
| `ammo_weight_cfg` | `ammo_weight_cfg`, `ammo_weight_cfg_steam` |
| `anim_gun_cfg` | `anim_gun_cfg`, `anim_gun_cfg_steam` |
| `anim_player_cfg` | `anim_player_cfg`, `anim_player_cfg_steam` |
| `animation_base_cfg` | `animation_base_cfg`, `animation_base_cfg_steam` |
| `animator_all_cfg` | `animator_all_cfg` |
| `animator_cfg` | `animator_cfg`, `animator_cfg_steam` |
| `animator_event_time_cfg` | `animator_event_time_cfg`, `animator_event_time_cfg_steam` |
| `arcade_base_cfg` | `arcade_base_cfg`, `arcade_base_cfg_steam` |
| `arcade_guild_task_cfg` | `arcade_guild_task_cfg`, `arcade_guild_task_cfg_steam` |
| `arcade_hero_gun_cfg` | `arcade_hero_gun_cfg`, `arcade_hero_gun_cfg_steam` |
| `arcade_lottery_draw_cfg` | `arcade_lottery_draw_cfg`, `arcade_lottery_draw_cfg_steam` |
| `arcade_lottery_draw_group_cfg` | `arcade_lottery_draw_group_cfg`, `arcade_lottery_draw_group_cfg_steam` |
| `arcade_lottery_draw_pool_cfg` | `arcade_lottery_draw_pool_cfg`, `arcade_lottery_draw_pool_cfg_steam` |
| `audio_function` | `audio_function`, `audio_function_steam` |
| `auto_exchange_item_cfg` | `auto_exchange_item_cfg`, `auto_exchange_item_cfg_steam` |
| `battle_chat_all_cfg` | `battle_chat_all_cfg`, `battle_chat_all_cfg_steam` |
| `battle_chat_cfg` | `battle_chat_cfg`, `battle_chat_cfg_steam` |
| `battle_interact_cfg` | `battle_interact_cfg`, `battle_interact_cfg_steam` |
| `battle_pass_award_cfg` | `battle_pass_award_cfg`, `battle_pass_award_cfg_steam` |
| `battle_pass_cfg` | `battle_pass_cfg`, `battle_pass_cfg_steam` |
| `battle_shop_refresh` | `battle_shop_refresh`, `battle_shop_refresh_steam` |
| `bet_ammo_reward_cfg` | `bet_ammo_reward_cfg`, `bet_ammo_reward_cfg_steam` |
| `buff` | `buff` |
| `buff_cfg` | `buff_cfg`, `buff_cfg_steam` |
| `buff_effect_cfg` | `buff_effect_cfg`, `buff_effect_cfg_steam` |
| `buff_logic_type` | `buff_logic_type` |
| `buff_logic_type_cfg` | `buff_logic_type_cfg`, `buff_logic_type_cfg_steam` |
| `business_card_cfg` | `business_card_cfg`, `business_card_cfg_steam` |
| `camp_cfg` | `camp_cfg`, `camp_cfg_steam` |
| `card_cfg` | `card_cfg`, `card_cfg_steam` |
| `card_index_cfg` | `card_index_cfg` |
| `card_weight_cfg` | `card_weight_cfg`, `card_weight_cfg_steam` |
| `cbt_avatar` | `cbt_avatar`, `cbt_avatar_steam` |
| `chair_cfg` | `chair_cfg`, `chair_cfg_steam` |
| `championship_base` | `championship_base`, `championship_base_steam` |
| `championship_bet_cfg` | `championship_bet_cfg`, `championship_bet_cfg_steam` |
| `championship_hero_random` | `championship_hero_random`, `championship_hero_random_steam` |
| `chat_fast_cfg` | `chat_fast_cfg`, `chat_fast_cfg_steam` |
| `chat_message` | `chat_message`, `chat_message_steam` |
| `chat_system_cfg` | `chat_system_cfg`, `chat_system_cfg_steam` |
| `clan_avatar_cfg` | `clan_avatar_cfg`, `clan_avatar_cfg_steam` |
| `clan_avatar_item_cfg` | `clan_avatar_item_cfg`, `clan_avatar_item_cfg_steam` |
| `clan_base_cfg` | `clan_base_cfg`, `clan_base_cfg_steam` |
| `clan_box_level` | `clan_box_level`, `clan_box_level_steam` |
| `clan_box_level_person` | `clan_box_level_person`, `clan_box_level_person_steam` |
| `clan_box_rank` | `clan_box_rank`, `clan_box_rank_steam` |
| `clan_box_reward` | `clan_box_reward`, `clan_box_reward_steam` |
| `clan_heat_race` | `clan_heat_race`, `clan_heat_race_steam` |
| `clan_team_base_cfg` | `clan_team_base_cfg`, `clan_team_base_cfg_steam` |
| `clan_team_icon_cfg` | `clan_team_icon_cfg`, `clan_team_icon_cfg_steam` |
| `coe_continue_pvp` | `coe_continue_pvp`, `coe_continue_pvp_steam` |
| `coe_win_ratio` | `coe_win_ratio`, `coe_win_ratio_steam` |
| `country_cfg` | `country_cfg`, `country_cfg_steam` |
| `cup_extr_info_cfg` | `cup_extr_info_cfg`, `cup_extr_info_cfg_steam` |
| `cup_info_cfg` | `cup_info_cfg`, `cup_info_cfg_steam` |
| `cup_task_cfg` | `cup_task_cfg`, `cup_task_cfg_steam` |
| `cut_scene` | `cut_scene`, `cut_scene_steam` |
| `cut_scene_player_cfg` | `cut_scene_player_cfg`, `cut_scene_player_cfg_steam` |
| `day_task_cfg` | `day_task_cfg`, `day_task_cfg_steam` |
| `day_task_fixed_cfg` | `day_task_fixed_cfg`, `day_task_fixed_cfg_steam` |
| `device_setting_lv` | `device_setting_lv`, `device_setting_lv_steam` |
| `dialog_cfg` | `dialog_cfg`, `dialog_cfg_steam` |
| `drop_something` | `drop_something`, `drop_something_steam` |
| `effect_cfg` | `effect_cfg`, `effect_cfg_steam` |
| `effect_cfg_buff` | `effect_cfg_buff`, `effect_cfg_buff_steam` |
| `effect_cfg_move` | `effect_cfg_move`, `effect_cfg_move_steam` |
| `effect_gun_cfg` | `effect_gun_cfg`, `effect_gun_cfg_steam` |
| `effect_player_cfg` | `effect_player_cfg`, `effect_player_cfg_steam` |
| `effect_pos_cfg` | `effect_pos_cfg`, `effect_pos_cfg_steam` |
| `effect_table_postopos_cfg` | `effect_table_postopos_cfg`, `effect_table_postopos_cfg_steam` |
| `error` | `error`, `error_steam` |
| `event_consume_time` | `event_consume_time`, `event_consume_time_steam` |
| `event_time` | `event_time` |
| `event_time_cfg` | `event_time_cfg` |
| `exp_rank_coefficient` | `exp_rank_coefficient` |
| `exp_round_coefficient` | `exp_round_coefficient`, `exp_round_coefficient_steam` |
| `explore_box_cfg` | `explore_box_cfg`, `explore_box_cfg_steam` |
| `explore_box_extract` | `explore_box_extract`, `explore_box_extract_steam` |
| `explore_box_fix_item_cfg` | `explore_box_fix_item_cfg`, `explore_box_fix_item_cfg_steam` |
| `explore_box_no_ammo_cfg` | `explore_box_no_ammo_cfg`, `explore_box_no_ammo_cfg_steam` |
| `explore_box_preview_item` | `explore_box_preview_item`, `explore_box_preview_item_steam` |
| `explore_box_progress` | `explore_box_progress`, `explore_box_progress_steam` |
| `explore_box_quality_cfg` | `explore_box_quality_cfg`, `explore_box_quality_cfg_steam` |
| `explore_box_shooting_cfg` | `explore_box_shooting_cfg`, `explore_box_shooting_cfg_steam` |
| `explore_box_up_cfg` | `explore_box_up_cfg`, `explore_box_up_cfg_steam` |
| `explore_box_weight_cfg` | `explore_box_weight_cfg`, `explore_box_weight_cfg_steam` |
| `explore_cell` | `explore_cell`, `explore_cell_steam` |
| `explore_fake_box_cfg` | `explore_fake_box_cfg`, `explore_fake_box_cfg_steam` |
| `fake_ammo_weight_cfg` | `fake_ammo_weight_cfg`, `fake_ammo_weight_cfg_steam` |
| `fake_dropitem` | `fake_dropitem`, `fake_dropitem_steam` |
| `fake_dropitem_group` | `fake_dropitem_group`, `fake_dropitem_group_steam` |
| `fashion_cfg` | `fashion_cfg`, `fashion_cfg_steam` |
| `fight_error` | `fight_error`, `fight_error_steam` |
| `fight_task_cfg` | `fight_task_cfg`, `fight_task_cfg_steam` |
| `fix_rank_data` | `fix_rank_data`, `fix_rank_data_steam` |
| `func_unlock_cfg` | `func_unlock_cfg`, `func_unlock_cfg_steam` |
| `gift_package_reward` | `gift_package_reward`, `gift_package_reward_steam` |
| `gpu_animation_group_cfg` | `gpu_animation_group_cfg`, `gpu_animation_group_cfg_steam` |
| `guide_cfg` | `guide_cfg`, `guide_cfg_steam` |
| `guide_evaluate_base_cfg` | `guide_evaluate_base_cfg`, `guide_evaluate_base_cfg_steam` |
| `guide_evaluate_trigger_cfg` | `guide_evaluate_trigger_cfg`, `guide_evaluate_trigger_cfg_steam` |
| `guide_mask_cfg` | `guide_mask_cfg`, `guide_mask_cfg_steam` |
| `gun` | `gun` |
| `gun_cfg` | `gun_cfg`, `gun_cfg_steam` |
| `gun_model_cfg` | `gun_model_cfg`, `gun_model_cfg_steam` |
| `gun_page_cfg` | `gun_page_cfg`, `gun_page_cfg_steam` |
| `gun_recommend` | `gun_recommend`, `gun_recommend_steam` |
| `gun_shoot_fix_ammo_cfg` | `gun_shoot_fix_ammo_cfg`, `gun_shoot_fix_ammo_cfg_steam` |
| `hall_song_cfg` | `hall_song_cfg`, `hall_song_cfg_steam` |
| `hero_badge_cfg` | `hero_badge_cfg`, `hero_badge_cfg_steam` |
| `hero_badge_random_cfg` | `hero_badge_random_cfg`, `hero_badge_random_cfg_steam` |
| `hero_cfg` | `hero_cfg`, `hero_cfg_steam` |
| `hero_fight_exp_cfg` | `hero_fight_exp_cfg`, `hero_fight_exp_cfg_steam` |
| `hero_gun_cfg` | `hero_gun_cfg` |
| `hero_SelectRole_cfg` | `hero_SelectRole_cfg`, `hero_SelectRole_cfg_steam` |
| `hero_star_fun_cfg` | `hero_star_fun_cfg`, `hero_star_fun_cfg_steam` |
| `hero_star_level` | `hero_star_level` |
| `hero_star_nature_cfg` | `hero_star_nature_cfg`, `hero_star_nature_cfg_steam` |
| `hero_up_cfg` | `hero_up_cfg`, `hero_up_cfg_steam` |
| `home_exp_cfg` | `home_exp_cfg`, `home_exp_cfg_steam` |
| `home_exp_rank_coefficient` | `home_exp_rank_coefficient` |
| `home_exp_round_coefficient` | `home_exp_round_coefficient` |
| `home_task_cfg` | `home_task_cfg`, `home_task_cfg_steam` |
| `honor_cfg` | `honor_cfg`, `honor_cfg_steam` |
| `interact_move` | `interact_move`, `interact_move_steam` |
| `item_base` | `item_base`, `item_base_steam` |
| `item_model` | `item_model`, `item_model_steam` |
| `item_shop_base` | `item_shop_base`, `item_shop_base_steam` |
| `item_shop_main` | `item_shop_main`, `item_shop_main_steam` |
| `item_use_discount` | `item_use_discount`, `item_use_discount_steam` |
| `journey_layer_cfg` | `journey_layer_cfg`, `journey_layer_cfg_steam` |
| `journey_match_pool_cfg` | `journey_match_pool_cfg` |
| `journey_refresh_card_cfg` | `journey_refresh_card_cfg`, `journey_refresh_card_cfg_steam` |
| `language_name_perfix` | `language_name_perfix`, `language_name_perfix_steam` |
| `limit_time_pack_award_cfg` | `limit_time_pack_award_cfg`, `limit_time_pack_award_cfg_steam` |
| `limit_time_pack_cfg` | `limit_time_pack_cfg`, `limit_time_pack_cfg_steam` |
| `loading_cfg` | `loading_cfg`, `loading_cfg_steam` |
| `lottery_cam_cfg` | `lottery_cam_cfg`, `lottery_cam_cfg_steam` |
| `lottery_draw_ammo_reward` | `lottery_draw_ammo_reward`, `lottery_draw_ammo_reward_steam` |
| `lottery_draw_base` | `lottery_draw_base`, `lottery_draw_base_steam` |
| `lottery_draw_magazine` | `lottery_draw_magazine`, `lottery_draw_magazine_steam` |
| `LotteryCameraCfg` | `LotteryCameraCfg`, `LotteryCameraCfg_steam` |
| `mail_cfg` | `mail_cfg`, `mail_cfg_steam` |
| `match_pool_cfg` | `match_pool_cfg`, `match_pool_cfg_steam` |
| `message_cfg` | `message_cfg`, `message_cfg_steam` |
| `new_guide_behavior` | `new_guide_behavior`, `new_guide_behavior_steam` |
| `new_guide_step` | `new_guide_step`, `new_guide_step_steam` |
| `new_guild_card_pool_cfg` | `new_guild_card_pool_cfg` |
| `new_guild_cfg` | `new_guild_cfg`, `new_guild_cfg_steam` |
| `new_guild_dia_cfg` | `new_guild_dia_cfg`, `new_guild_dia_cfg_steam` |
| `newbieroute_award_cfg` | `newbieroute_award_cfg` |
| `newbieroute_cfg` | `newbieroute_cfg` |
| `normal_const_lua` | `normal_const_lua`, `normal_const_lua_steam` |
| `normal_const_lua_int` | `normal_const_lua_int` |
| `normal_const_lua_int_array` | `normal_const_lua_int_array` |
| `normal_const_lua_itemconfig` | `normal_const_lua_itemconfig` |
| `normal_const_lua_itemconfig_array` | `normal_const_lua_itemconfig_array` |
| `normal_const_lua_steam_int` | `normal_const_lua_steam_int` |
| `normal_const_lua_steam_string` | `normal_const_lua_steam_string` |
| `normal_const_lua_string` | `normal_const_lua_string` |
| `normal_const_parameter` | `normal_const_parameter`, `normal_const_parameter_steam` |
| `normal_const_parameter_bool` | `normal_const_parameter_bool` |
| `normal_const_parameter_int` | `normal_const_parameter_int` |
| `normal_const_parameter_int_array` | `normal_const_parameter_int_array` |
| `normal_const_parameter_itemconfig` | `normal_const_parameter_itemconfig` |
| `normal_const_parameter_itemconfig_array` | `normal_const_parameter_itemconfig_array` |
| `normal_const_parameter_sdvector3` | `normal_const_parameter_sdvector3` |
| `normal_const_parameter_sdvector3_array` | `normal_const_parameter_sdvector3_array` |
| `normal_const_parameter_steam_int` | `normal_const_parameter_steam_int` |
| `normal_const_parameter_steam_int_array` | `normal_const_parameter_steam_int_array` |
| `normal_const_parameter_steam_itemconfig` | `normal_const_parameter_steam_itemconfig` |
| `normal_const_parameter_steam_itemconfig_array` | `normal_const_parameter_steam_itemconfig_array` |
| `normal_const_parameter_steam_string` | `normal_const_parameter_steam_string` |
| `normal_const_parameter_steam_string_array` | `normal_const_parameter_steam_string_array` |
| `normal_const_parameter_string` | `normal_const_parameter_string` |
| `normal_const_parameter_string_array` | `normal_const_parameter_string_array` |
| `novice_guild_card` | `novice_guild_card`, `novice_guild_card_steam` |
| `novice_guild_cfg` | `novice_guild_cfg`, `novice_guild_cfg_steam` |
| `novice_guild_player_info_cfg` | `novice_guild_player_info_cfg`, `novice_guild_player_info_cfg_steam` |
| `novice_guild_pvp_info_cfg` | `novice_guild_pvp_info_cfg` |
| `novice_guild_slice_step_cfg` | `novice_guild_slice_step_cfg`, `novice_guild_slice_step_cfg_steam` |
| `novice_guild_step_cfg` | `novice_guild_step_cfg`, `novice_guild_step_cfg_steam` |
| `novice_guild_task_cfg` | `novice_guild_task_cfg`, `novice_guild_task_cfg_steam` |
| `novice_survive_teach_behavior` | `novice_survive_teach_behavior`, `novice_survive_teach_behavior_steam` |
| `novice_survive_teach_step` | `novice_survive_teach_step`, `novice_survive_teach_step_steam` |
| `novice_survive_teach_step_group_cfg` | `novice_survive_teach_step_group_cfg`, `novice_survive_teach_step_group_cfg_steam` |
| `novice_survive_teach_tips` | `novice_survive_teach_tips`, `novice_survive_teach_tips_steam` |
| `obj_fake` | `obj_fake`, `obj_fake_steam` |
| `phone_adaptation` | `phone_adaptation`, `phone_adaptation_steam` |
| `player_gun_cfg` | `player_gun_cfg`, `player_gun_cfg_steam` |
| `player_head_pic` | `player_head_pic`, `player_head_pic_steam` |
| `player_model` | `player_model`, `player_model_steam` |
| `popup_face` | `popup_face`, `popup_face_steam` |
| `push_system_content` | `push_system_content`, `push_system_content_steam` |
| `pve_ai_buff_group_cfg` | `pve_ai_buff_group_cfg`, `pve_ai_buff_group_cfg_steam` |
| `pve_ai_group_cfg` | `pve_ai_group_cfg`, `pve_ai_group_cfg_steam` |
| `pve_card_group_cfg` | `pve_card_group_cfg`, `pve_card_group_cfg_steam` |
| `pve_evn_group_cfg` | `pve_evn_group_cfg`, `pve_evn_group_cfg_steam` |
| `pve_hero_reward_cfg` | `pve_hero_reward_cfg`, `pve_hero_reward_cfg_steam` |
| `pve_level_cfg` | `pve_level_cfg`, `pve_level_cfg_steam` |
| `pve_random_hero_cfg` | `pve_random_hero_cfg`, `pve_random_hero_cfg_steam` |
| `pvp_battle_event` | `pvp_battle_event`, `pvp_battle_event_steam` |
| `pvp_battle_event_info` | `pvp_battle_event_info`, `pvp_battle_event_info_steam` |
| `pvp_battle_event_pool` | `pvp_battle_event_pool`, `pvp_battle_event_pool_steam` |
| `pvp_battle_event_task_cfg` | `pvp_battle_event_task_cfg`, `pvp_battle_event_task_cfg_steam` |
| `pvp_bgm_group` | `pvp_bgm_group`, `pvp_bgm_group_steam` |
| `pvp_bo_win_bet` | `pvp_bo_win_bet`, `pvp_bo_win_bet_steam` |
| `pvp_bonus` | `pvp_bonus`, `pvp_bonus_steam` |
| `pvp_card_plan` | `pvp_card_plan`, `pvp_card_plan_steam` |
| `pvp_clash_base_cfg` | `pvp_clash_base_cfg`, `pvp_clash_base_cfg_steam` |
| `pvp_clash_card_add_weight_cfg` | `pvp_clash_card_add_weight_cfg`, `pvp_clash_card_add_weight_cfg_steam` |
| `pvp_clash_card_base_cfg` | `pvp_clash_card_base_cfg`, `pvp_clash_card_base_cfg_steam` |
| `pvp_clash_card_cfg` | `pvp_clash_card_cfg`, `pvp_clash_card_cfg_steam` |
| `pvp_clash_card_condition_cfg` | `pvp_clash_card_condition_cfg`, `pvp_clash_card_condition_cfg_steam` |
| `pvp_clash_card_event_cfg` | `pvp_clash_card_event_cfg`, `pvp_clash_card_event_cfg_steam` |
| `pvp_clash_card_plan_cfg` | `pvp_clash_card_plan_cfg`, `pvp_clash_card_plan_cfg_steam` |
| `pvp_clash_card_refresh_consume_cfg` | `pvp_clash_card_refresh_consume_cfg`, `pvp_clash_card_refresh_consume_cfg_steam` |
| `Pvp_Eval_Award` | `Pvp_Eval_Award`, `Pvp_Eval_Award_steam` |
| `pvp_high_light_task_cfg` | `pvp_high_light_task_cfg`, `pvp_high_light_task_cfg_steam` |
| `pvp_main_mode_switch_btn` | `pvp_main_mode_switch_btn`, `pvp_main_mode_switch_btn_steam` |
| `pvp_mode_cfg` | `pvp_mode_cfg`, `pvp_mode_cfg_steam` |
| `pvp_mode_time_limit_cfg` | `pvp_mode_time_limit_cfg`, `pvp_mode_time_limit_cfg_steam` |
| `pvp_model_list_btn` | `pvp_model_list_btn`, `pvp_model_list_btn_steam` |
| `pvp_model_scene` | `pvp_model_scene`, `pvp_model_scene_steam` |
| `pvp_ob_num` | `pvp_ob_num`, `pvp_ob_num_steam` |
| `pvp_rob_role_base_cfg` | `pvp_rob_role_base_cfg`, `pvp_rob_role_base_cfg_steam` |
| `pvp_rob_role_cfg` | `pvp_rob_role_cfg`, `pvp_rob_role_cfg_steam` |
| `pvp_rob_role_pool_cfg` | `pvp_rob_role_pool_cfg`, `pvp_rob_role_pool_cfg_steam` |
| `pvp_task_cfg` | `pvp_task_cfg` |
| `pvp_texas_base_cfg` | `pvp_texas_base_cfg`, `pvp_texas_base_cfg_steam` |
| `pvp_texas_poker_cfg` | `pvp_texas_poker_cfg`, `pvp_texas_poker_cfg_steam` |
| `pvp_texas_poker_type` | `pvp_texas_poker_type`, `pvp_texas_poker_type_steam` |
| `quality_setting_open` | `quality_setting_open`, `quality_setting_open_steam` |
| `question_pwg_cfg` | `question_pwg_cfg`, `question_pwg_cfg_steam` |
| `rand_name_library` | `rand_name_library`, `rand_name_library_steam` |
| `random_audio_group` | `random_audio_group`, `random_audio_group_steam` |
| `recharge_cfg` | `recharge_cfg`, `recharge_cfg_steam` |
| `recharge_cost_show` | `recharge_cost_show`, `recharge_cost_show_steam` |
| `recharge_rebate` | `recharge_rebate`, `recharge_rebate_steam` |
| `region_area_code` | `region_area_code`, `region_area_code_steam` |
| `region_config` | `region_config`, `region_config_steam` |
| `region_fun_open_cfg` | `region_fun_open_cfg`, `region_fun_open_cfg_steam` |
| `region_language_config` | `region_language_config`, `region_language_config_steam` |
| `region_translate_config` | `region_translate_config`, `region_translate_config_steam` |
| `report_cfg` | `report_cfg`, `report_cfg_steam` |
| `res_audio` | `res_audio`, `res_audio_steam` |
| `res_video` | `res_video`, `res_video_steam` |
| `resources_img` | `resources_img`, `resources_img_steam` |
| `robot_fix_cfg` | `robot_fix_cfg`, `robot_fix_cfg_steam` |
| `robot_hero_pool_cfg` | `robot_hero_pool_cfg`, `robot_hero_pool_cfg_steam` |
| `robot_intact_cfg` | `robot_intact_cfg`, `robot_intact_cfg_steam` |
| `robot_pool_cfg` | `robot_pool_cfg`, `robot_pool_cfg_steam` |
| `roulette_machine_base_cfg` | `roulette_machine_base_cfg`, `roulette_machine_base_cfg_steam` |
| `scene_base` | `scene_base`, `scene_base_steam` |
| `scene_player_pos` | `scene_player_pos`, `scene_player_pos_steam` |
| `sd_name_library` | `sd_name_library`, `sd_name_library_steam` |
| `sd_quality_main` | `sd_quality_main`, `sd_quality_main_steam` |
| `season_award_cfg` | `season_award_cfg`, `season_award_cfg_steam` |
| `season_cfg` | `season_cfg`, `season_cfg_steam` |
| `season_quarter_task_cfg` | `season_quarter_task_cfg`, `season_quarter_task_cfg_steam` |
| `select_play_mode_cfg` | `select_play_mode_cfg`, `select_play_mode_cfg_steam` |
| `select_question_cfg` | `select_question_cfg`, `select_question_cfg_steam` |
| `sensitives` | `sensitives`, `sensitives_steam` |
| `sensitives_fullcompare` | `sensitives_fullcompare`, `sensitives_fullcompare_steam` |
| `server_const_parameter` | `server_const_parameter`, `server_const_parameter_steam` |
| `server_const_parameter_int` | `server_const_parameter_int` |
| `server_const_parameter_int_array` | `server_const_parameter_int_array` |
| `server_const_parameter_itemconfig` | `server_const_parameter_itemconfig` |
| `server_const_parameter_steam_int` | `server_const_parameter_steam_int` |
| `server_const_parameter_string` | `server_const_parameter_string` |
| `server_list_cfg` | `server_list_cfg`, `server_list_cfg_steam` |
| `server_name_idx_cfg` | `server_name_idx_cfg`, `server_name_idx_cfg_steam` |
| `share_img` | `share_img`, `share_img_steam` |
| `shot_pseudo_cfg` | `shot_pseudo_cfg`, `shot_pseudo_cfg_steam` |
| `shot_pseudo_luck_cfg` | `shot_pseudo_luck_cfg`, `shot_pseudo_luck_cfg_steam` |
| `skill_cfg` | `skill_cfg`, `skill_cfg_steam` |
| `skill_cfg_level` | `skill_cfg_level` |
| `skill_index_cfg` | `skill_index_cfg` |
| `skill_info_cfg` | `skill_info_cfg`, `skill_info_cfg_steam` |
| `slice_behavior` | `slice_behavior` |
| `slice_step` | `slice_step` |
| `slice_step_group_cfg` | `slice_step_group_cfg` |
| `steam_achievement_cfg` | `steam_achievement_cfg`, `steam_achievement_cfg_steam` |
| `steam_achievement_reward_cfg` | `steam_achievement_reward_cfg`, `steam_achievement_reward_cfg_steam` |
| `sub_pvp_mode_cfg` | `sub_pvp_mode_cfg`, `sub_pvp_mode_cfg_steam` |
| `system_language_config` | `system_language_config`, `system_language_config_steam` |
| `system_out_weburl` | `system_out_weburl`, `system_out_weburl_steam` |
| `task_cond_typ_cfg` | `task_cond_typ_cfg`, `task_cond_typ_cfg_steam` |
| `top` | `top`, `top_steam` |
| `top_reward` | `top_reward`, `top_reward_steam` |
| `tourist_mask` | `tourist_mask`, `tourist_mask_steam` |
| `treasure_box_award_cfg` | `treasure_box_award_cfg`, `treasure_box_award_cfg_steam` |
| `treasure_box_cfg` | `treasure_box_cfg`, `treasure_box_cfg_steam` |
| `treasure_box_fake_weight_cfg` | `treasure_box_fake_weight_cfg`, `treasure_box_fake_weight_cfg_steam` |
| `treasure_box_quality_cfg` | `treasure_box_quality_cfg`, `treasure_box_quality_cfg_steam` |
| `treasure_box_reclaim_dec` | `treasure_box_reclaim_dec`, `treasure_box_reclaim_dec_steam` |
| `treasure_box_weight_cfg` | `treasure_box_weight_cfg`, `treasure_box_weight_cfg_steam` |
| `true_ammo_cfg` | `true_ammo_cfg`, `true_ammo_cfg_steam` |
| `ui_jump` | `ui_jump`, `ui_jump_steam` |
| `ui_page_tab` | `ui_page_tab`, `ui_page_tab_steam` |
| `ui_top_title` | `ui_top_title`, `ui_top_title_steam` |
| `visiting_card` | `visiting_card`, `visiting_card_steam` |
| `wash_gamer_steam_id` | `wash_gamer_steam_id`, `wash_gamer_steam_id_steam` |
| `welfare_match_cfg` | `welfare_match_cfg`, `welfare_match_cfg_steam` |
| `zidan_cfg` | `zidan_cfg` |

</details>

## Como transformar referência em trabalho

1. Confirmar que a função é acessível nesta build e onde aparece.
2. Comparar descrição/configuração, chamada do cliente, handler e testes do servidor.
3. Separar “não implementado”, “resposta genérica”, “implementado mas sem teste visual” e “aprovado”.
4. Criar tarefa com ID estável na checklist e registrar esta referência como origem.
5. Validar modo, personagem/equipamento, limites, custo e persistência; encerrar só o escopo testado.

O inventário é amplo; a auditoria funcional de cada janela **não foi realizada nesta etapa documental**. Sistemas sociais, temporada e modos não testados permanecem abertos explicitamente.
