# Matriz de implementação local — itens PVP

Escopo: somente `Hunter Roulette - Copia`. A instalação original não é lida
para escrita e continua intacta.

## Contratos já confirmados no cliente

| cfgId | skillId | Envelope | Estado que o servidor atualiza |
|---:|---:|---|---|
| 2001/2026 | 1000/1024 | PopAmmo (`13`) | remove uma munição existente |
| 2003 | 1002 | ChangeAmmo/AddFixed (`21`) | soma munição real |
| 2004 | 1003 | ChangeAmmo/AddFixed (`21`) | soma munição falsa |
| 2007 | 1006 | Reload+ChangeAmmo (`12`) | recarga local 4 reais + 2 falsas |
| 2008/2025 | 1007/1023 | Shoot (`2`) | força tiro do alvo em si mesmo |
| 2011/2024/2027 | 1010/1022/1025 | Lucky/Heal (`7`,`20`) | rolagem 1–6; 4–6 cura até 4 |

## Lote genérico reconstruído a partir de `card_cfg`/`skill_cfg`

Os itens abaixo agora percorrem o mesmo envelope protobuf oficial de compra,
uso, alvo, consumo e atualização visual. Quando o cálculo original não foi
encontrado em uma captura, o servidor usa um efeito local determinístico e o
log identifica isso explicitamente; isso evita fingir que a regra original foi
recuperada.

| cfgId | skillId | Efeito local verificável |
|---:|---:|---|
| 2009 | 1008 | `Enum_Ammo_Replace` com cfg 2 (munição melhorada oficial); converte uma cfg 1 existente, mantém o total e o próximo tiro consome somente a cfg 2 para causar 2 de dano |
| 2015 | 1014 | buff `1014` no evento e snapshot; +1 dano somente no tiro real normal (`cfg 1`) contra outro jogador, consumindo uma munição real e removendo o buff ao fim do turno; erro oficial 352 bloqueia reaplicação no mesmo alvo enquanto ativo |
| 2016 | 1015 | buff visível; próximo tiro contra outro jogador emite dois `Enum_Shoot` consecutivos, consumindo duas munições |
| 2018 | 1017 | evento Lucky com dado 1–6; o mesmo evento carrega `Coin_By_Steal` na origem (+) e no alvo (−), pois o cliente ignora eventos `Enum_Coin` extras na conclusão da carta. Saldo do alvo limita a transferência a dado ×100; erro 380 sem saldo. Jogador confirmou dado 2, transferência 200 e saldo líquido 9800 para ambos |
| 2020/2028/2036/2037 | 1019/1038/1039 | concede uma carta aleatória do pool ao slot |
| 2021 | 1020 | adiciona buffs 1020 e 5002 com IDs distintos; prazo próprio = relógio da aplicação + N participantes vivos; contador cai em cada troca de personagem; primeiro dano paga +4 ao atacante; expiração sem dano paga +4 ao marcado vivo |
| 2022 | 1021 | envia buff de bloqueio de compra ao alvo; duas aplicações no Bot 1 registradas em partida; sem tentativa de compra do bot para confirmar a rejeição diretamente |
| 2029 | 10008 | `Enum_Hp_Vir=14`; remove `min(Frenzy, ceil(HP atual / 2))`, atualiza o snapshot do alvo e não cria buff persistente; loja, item guardado e bots cobertos |
| 2030 | 10009 | envia buff de bloqueio de habilidade |
| 2031 | 10010 | envia evento de carga de habilidade |
| 2032 | 10011 | `Enum_Rpg=39`; sorteia uma munição; cfg300 consome uma falsa sem dano, cfg1/2 consome todas as reais restantes e causa dano por espaço real; deltas HP/Frenzy, `uAmmo` na origem e recarga posterior à animação |
| 2033 | 1026 | guarda consumível que absorve o primeiro dano normal; jogador confirma efeito e aparição/animação aparentemente corretas |

### Rocket Launcher (2032) — aprovado no teste manual do jogador

- A implementação anterior sempre subtraía 2 HP do alvo, marcava o tiro como
  real e não consumia munição. Isso não correspondia à descrição do item.
- Regra atual: sorteia uma bala dentre as reais (incluindo cfg2 melhorada) e
  falsas. Falsa: consome uma cfg300 e não causa dano. Real: consome todas as
  cfg1/cfg2, causa dano igual à quantidade de espaços reais antes do disparo,
  envia HP/Frenzy em deltas separados e aciona recarga automática após o evento
  RPG se ainda houver pelo menos dois participantes vivos.
- O evento `Enum_Rpg` leva `source.uAmmo` e `source.isRpgHit`, conforme o Lua do
  cliente; a recarga vem num `Enum_Reload` subsequente para não atualizar o
  carregador antes de `ShootAmmoMul` consumir o pente antigo.
- Compra-uso e item guardado passaram por teste TCP; falso e real, consumo,
  dano, Frenzy, morte e recarga têm cobertura automatizada. O jogador confirmou
  que o Rocket funcionou na partida; fica encerrado no roteiro atual.

### Wanted (2021) — contratos recuperados dos arquivos do jogo

- `card_cfg` 2021 aponta para `skill_cfg` 1020. O skill adiciona o buff de
  controle 1020; esse buff de um round referencia o buff visível 5002, cujo
  ícone é `UI_Fight_bufficon_reward` e cuja lógica `Offer_Reward` configura
  4 R-Chips.
- A descrição inglesa no bundle define a resolução: o primeiro jogador a
  causar dano de tiro no alvo ganha 4 R-Chips; se o round acabar sem esse dano,
  o alvo marcado ganha os 4. A enumeração do protocolo associa esse pagamento
  a `Coin_By_Offer_Award` (reason 7).
- A cópia usa um prazo por aplicação: relógio atual + quantidade de vivos no
  uso. Cada troca real de personagem avança o relógio; uso de itens, recargas,
  rajadas e tiros falsos em si na mesma vez não o avançam. Em três participantes,
  o contador é 3→2→1→expiração. As marcas criadas na mesma vez expiram juntas;
  marcas posteriores preservam seus próprios prazos. O orçamento é fixado no
  uso, não recalculado quando outro participante morre.
- `Enum_Gamer_Buff_Calc` (25), com `PvpEventOutline.buffs` (campo 3), atualiza
  `Buff.showNum` sem remover/recriar o efeito. O efeito de mesa 107 tem versões
  oficiais de números 1–4 (136–139). O cliente troca a versão pelo contador.
  Isso confirma o mecanismo visual; o algoritmo do servidor original para o
  prazo não foi recuperado. A duração local segue a regra proposta pelo jogador.
- Os 110 testes cobrem as duas marcas do relato, contagem no TCP, pagamento uma
  vez só, prazos distintos de aplicações posteriores e tiros falsos repetidos
  mantendo o prazo. Acerto já confirmado manualmente; contador/expiração ainda
  aguardam reteste visual. Modos com mais participantes precisam validar também
  os recursos visuais disponíveis, além da economia 10×/100×/1000× planejada.

## Testes automatizados desta etapa

- `py_compile` de `protocol.py` e `server.py`.
- 73 testes de protocolo/loopback existentes (incluem quatro novos testes do
  Kit de Manutenção: buff/snapshot, regra de dano, pacote de tiro e fluxo TCP
  de compra/uso/disparo).
- Compra-e-uso genérico de cfg 2009 em loopback: ack sem erro, `skillId=1008`,
  `rAmmo` inclui cfg 2 e `cAmmo` liga a troca para a bala melhorada; o
  próximo tiro real consome o bônus e aplica dano 2.
- Compra, armazenamento e uso de cfg 2015 em loopback: ack sem erro,
  `skillId=1014`, evento de consumo e evento de efeito.
- Fluxo TCP do Kit: compra-e-uso mostra buff cfg 1014 no evento e na placa;
  disparo em bot envia cfg 1, atualiza a munição real de 4 para 3, aplica
  `hpDelta=-2`, emite os marcadores de animação normal e remove o buff.
- O jogador confirmou em 2026-09-24 que ícone, disparo e dano do Kit passaram a
  funcionar. No mesmo teste encontrou compra duplicada enquanto o buff ainda
  estava ativo. O fluxo TCP agora verifica erro 352 (texto oficial do bundle:
  “O alvo já possui este efeito, não pode ser empilhado”), sem debitar moedas ou
  marcar oferta como vendida. Uma carta guardada rejeitada permanece no slot.

O trace manual de 2026-09-24 mostrou a falha anterior do cfg 2015: o evento
usava o id da carta como buff e o disparo saía como cfg 2 sem reduzir o pente.
Isso foi corrigido localmente; a próxima sessão deve confirmar o ícone do
Kit, a munição cfg 1 consumida, +1 dano, a animação/som normais e a remoção do
ícone. A lista manual abaixo separa o que já foi confirmado, o que deve ser
repetido após esta correção e o que continua pendente.
