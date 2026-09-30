# Inventário offline — mapa confirmado e plano de implementação

Este documento separa o que foi observado no cliente comprado, o que já é
persistido pelo laboratório e o que ainda não pode ser afirmado. Os bots ficam
fora desta etapa; o objetivo é tornar a bolsa, os baús e os equipamentos
jogáveis offline com bots somente depois.

## Invariante mais importante: quantidade é absoluta

`GamerBag.UpdateItem` não soma o número recebido. Para um item existente, o
cliente calcula `chg = item.number - v.number` e substitui `v.number` pelo valor
recebido. Para um item novo, insere o número recebido; número zero remove o
item. Isso vale também para moedas (`money`, `rCoin`, `diamond` e `hunterCoin`).

Consequência: qualquer resposta de prêmio, custo ou notificação precisa enviar
a quantidade total depois da operação. Enviar apenas o delta faz a HUD parecer
correta por um instante e depois voltar, ou deixa a bolsa sem descontar.

## Domínios e contratos confirmados

| Domínio | Comandos | Estado que precisa sobreviver |
|---|---:|---|
| Bolsa | `8/1`, `8/2`, `8/3`, `8/6`, `8/7` | itens, moedas e quantidades absolutas |
| Cartas | `12/1`, `12/2` | `unlockCards` e `readyCard` por herói |
| Roupas | `23/1`, `23/2`, `23/3` | roupas possuídas, lidas e usadas |
| Armas | `24/1`, `25/1`, `25/2` | arma por herói e armorial |
| Loja | `22/1`, `22/2`, `22/3` | catálogo, limites, custo e prêmio |
| Baú da base | `13/1`–`13/5` | slots, cronômetros, baú temporário e prêmio |
| Caixa de exploração | `32/1`–`32/6` | células, armazém, eventos e prêmio |

O cliente aplica `award.get` e `cost` nos comandos de uso/venda, e aplica
`item.get` nos comandos de prêmio da exploração. As notificações correspondentes
são `253/6` (bolsa), `253/9` (carta), `253/18` (roupa), `253/21` (arma do
herói), `253/33` (armorial), `253/10` (base) e `253/46` (exploração).

## Caixas de exploração — fluxo real

O cliente não abre uma caixa de exploração pela bolsa. Ele mantém dois estados:

1. `exploreBoxPack`: armazém de caixas (`id=1` azul, `12` roxa, `23` laranja,
   `34` vermelha no nível 0);
2. `exploreCells`: onze posições, cada uma com `id` e `chest`.

O fluxo é:

1. `32/4` move uma caixa do armazém para uma célula;
2. `32/2` resolve a célula e retorna `event[]`, `oldChest` e `chest`;
3. o cliente exibe cinco tiros localmente;
4. `32/3` (ou `32/6`) recolhe o resultado e retorna `item.get` em quantidade
   absoluta, além de limpar a célula.

A configuração embarcada confirma que a recompensa final é o `box_award` da
linha `ExploreBoxCfgSteam`: `701219 + box_id` para os ids regulares 1–44 (por
exemplo, `12 -> 701231`, `23 -> 701242` e `34 -> 701253`). Esses itens são de
uso direto (`use_result_type=20`) e seus `use_result_value` apontam para os
drops 116, 127, 138 e 149. Os itens `201004`–`201014` e `203000`–`203002` são
somente prévia visual.

O `ExploreBoxUpCfgSteam` também foi aplicado: partindo da qualidade 2, o
resultado final é 2/3/4 com pesos 300/40/25. O evento `2` é
`Up_Qua_Ammo` (upgrade de raridade) e o evento `1` é tiro sem upgrade; a lista
de cinco eventos enviada ao cliente agora sempre coincide com o `chest` final.

As três linhas de loja estavam no bundle, mas duas não eram atendidas pelo
protótipo: `14500000` e `14500001` vendem `701264`/pack 1 por 35.000/50.000 de
`102000`, e `14500002` vende `701265`/pack 12 por 100.000. Todas agora deixam o
item e o armazém persistidos.

## Equipamentos

- `23/1` envia `gid`, `typ`, `fid` e `tid`; o cliente espera resposta de sucesso
  e a notificação `253/18`. O servidor deve rejeitar roupa não possuída ou
  incompatível com o alvo.
- `12/1` desbloqueia carta e `12/2` equipa carta. O cliente exige a carta na
  lista `unlockCard` antes de aceitar `readyCard`; equipar não deve desbloquear
  automaticamente.
- `24/1` associa uma arma possuída ao herói e requer `253/21` para atualizar a
  tela.

## O que estava errado no laboratório

- o prêmio da exploração era fabricado a partir da prévia `201004 x300`;
- a resposta não respeitava sempre a quantidade absoluta esperada pela bolsa;
- duas compras reais (`14500000` e `14500001`) eram descartadas como produto
  desconhecido, e a terceira usava preço fixo incorreto;
- `8/*` ainda não tinha a fundação de leitura/uso/venda da bolsa;
- roupa e carta tinham respostas parciais e validação insuficiente;
- os fluxos de baú da base (`13/*`) ainda eram apenas registrados.

### Fundação aplicada nesta etapa

- `8/1` agora devolve a lista persistida da bolsa;
- compra (`22/1`) devolve custo e prêmio absolutos e persiste os dois;
- abertura de exploração (`32/2`/`32/5`) desconta `106000 x5` e devolve
  `cost` no contrato correto;
- coleta (`32/3`/`32/6`) grava o `box_award` da linha final (por exemplo,
  `701231` para a roxa nível 0), sem usar os itens de prévia, e a quantidade
  devolvida é absoluta;
- `32/2` repete com segurança uma abertura pendente de uma única célula, sem
  cobrar munição novamente;
- a abertura escolhe a raridade pelos pesos reais e envia eventos `1`/`2`
  coerentes com a animação de cinco tiros;
- `22/1` atende os três `shop_item_id` reais, usando o preço e o pack
  correspondentes (`1` azul ou `12` roxo);
- `32/5` resolve e devolve todas as células ativas da grade (até as onze
  posições desbloqueadas) em uma única resposta; `TreasureBoxOpenAllWindow`
  calcula `5 * quantidade_de_células` e só então envia `32/6`. `32/6` recolhe
  exatamente o conjunto completo; uma repetição pendente não cobra munição
  novamente;
- `8/2` e `8/3` já têm a base transacional para os itens Steam conhecidos e
  retornam erro para operações ainda não decodificadas;
- respostas inválidas agora carregam códigos de erro do próprio catálogo Lua,
  em vez de parecerem sucesso vazio.
- `13/1` move o baú temporário para um slot desbloqueado, preservando o
  cronômetro e consumindo somente um custo explicitamente enviado pelo cliente;
- `13/2` abre um slot terminado (ou faz abertura imediata por moeda/chave),
  grava o prêmio configurado e limpa o slot;
- `13/3` vende o baú temporário pelo `sell_reward` da tabela embarcada;
- `13/4` coleta apenas entradas de renda passiva que estejam explicitamente
  persistidas em `currentIncome`; a fórmula observada no cliente é
  `floor(duracao_segundos * income / 1000 / 60)`, em que `income` é a taxa por
  minuto multiplicada por 1000, e somente Fight Coin `101000` e RCoin `102000`
  são elegíveis;
- `13/5` abre o baú temporário usando o custo completo configurado;
- todos os fluxos de base salvam atomicamente e enviam `GamerHome`/`ItemData`
  com quantidades absolutas.

## Ordem de trabalho

### Fase A — fundação da bolsa (concluída para os itens decodificados)

Leitura (`8/1`), uso seguro dos itens conhecidos (`8/2`), venda com preço da
configuração (`8/3`), recentes (`8/6`) e notificações/persistência já estão
implementados. Itens cujo `use_result_type` ainda não foi reconstruído são
recusados explicitamente.
Cada operação deve validar saldo, aplicar uma transação única, salvar
atomicamente e devolver quantidades absolutas.

### Fase B — exploração e baús recebidos (encadeamento histórico implementado)

Os prêmios da exploração são itens `701220`/`701231`/`701242`/`701253` (e seus
níveis), que seguem os drops 116/127/138/149 do `drop_something_steam`. Os
itens de baú roxo `701176`/`701177` continuam sendo um fluxo separado: o uso
pela bolsa consome a caixa e a chave `10001000` conforme as linhas 20/21 de
`treasure_box_cfg_steam`, e o resultado persistido é `701067`/`701068`. Esses
pacotes agora seguem o encadeamento confirmado em
`item_base_steam` + `drop_something_steam`: `701048..701071` fazem um sorteio
entre o próximo pacote de personagem e quatro valores de Fight Coin, e
`701072..701076` usam os drops 49/45..48 (pacotes, materiais e moeda).

Os pacotes históricos `701000..701047` também são consumidos por `8/2` (isso
inclui o prêmio `701000` da linha especial 25). O
intervalo de quantidade vem dos dois primeiros `use_result_value`; para essa
família antiga, o único seletor Steam não-zero em
`hero_badge_random_cfg_steam` é `random` para os sete heróis de nível 0.
Cada insígnia é persistida em `inventory.json.badges`, enviada no campo
`GamerLoginGetDataS2C.badge` e marcada em `specialShow`, para o cliente abrir
a janela de recompensa especial. A interpretação de quantidade inclusiva e
o sorteio de uma insígnia por unidade são a reconstrução operacional mais
consistente com as tabelas; as variantes novas `701077+` (que usam
`hero_random`) continuam recusadas até haver evidência do servidor para essa
regra diferente.

O wrapper de recompensa agora inclui `get` (quantidade absoluta) e `show`
(`chgNumber` positivo). Isso é necessário porque
`GlobalFunc.IsAwardNotEmptyToShow` ignora `get` e só abre a janela quando há
`show`, `change` ou `specialShow`.

### Fase C — equipamentos

Validar posse e compatibilidade de roupas, separar desbloqueio/equipamento de
cartas e manter armas, roupas e cartas consistentes entre login, refresh,
notificação e partida.

### Fase D — loja e base (base implementada; loja parcial)

Os cinco comandos de baú da base já têm transações e respostas reais. O
refresh/catalogação completa da loja e o cálculo de renda sem uma entrada
`currentIncome` explícita continuam pendentes.

## Mapa confirmado dos baús da base

As linhas 1–24 de `treasure_box_cfg_steam` formam quatro grupos de seis:

| Grupo | Duração | Abertura por moeda | Chave | Prêmio de primeira etapa |
|---|---:|---:|---:|---:|
| 1–6 | 3.600 s | 101000 x3.500 | 10001000 x1 | 701048–701053 |
| 7–12 | 18.000 s | 101000 x17.000 | 10001000 x5 | 701054–701059 |
| 13–18 | 43.200 s | 101000 x45.600 | 10001000 x12 | 701060–701065 |
| 19–24 | 86.400 s | 101000 x100.000 | 10001000 x24 | 701066–701071 |

A linha 25 é o tipo especial da base: 21.600 s, moeda 101000 x21.600,
chave 10001000 x6 e prêmio 701000. O cliente trata `status=0` ou slot ausente
como bloqueado; `status=1` com `boxId=-1` é slot desbloqueado vazio.

Ao trocar uma caixa já em andamento, `wayToSave=2` é o descarte explícito.
`wayToSave=3` significa abrir a antiga, mas a resposta de prêmio/notificação
desse caminho ainda não foi recuperada; o servidor o rejeita para não apagar
uma caixa sem entregar seu resultado.

O perfil de laboratório não recebe chaves ou caixas artificiais. Para testar a
abertura por chave, o item `10001000` precisa ser obtido por um fluxo que o
cliente realmente ofereça ou ser colocado conscientemente no arquivo de teste.

## Limites atuais

Ainda não foi encontrado no cliente o RNG histórico da conta nem um servidor
original. A tabela de prévia não autoriza inventar uma recompensa. Onde a
configuração não identifica completamente uma transformação, o servidor deve
recusar a operação e registrar o motivo, em vez de conceder um item arbitrário.

Todas as mudanças desta etapa são feitas apenas em `Hunter Roulette - Copia`.
O estado anterior foi copiado para
`research/private-server/rollback/2026-09-17-pre-inventory-foundation` antes da
alteração; antes desta correção específica também foi salvo em
`research/private-server/rollback/2026-09-17-pre-box-quality-purchase-fix`.
