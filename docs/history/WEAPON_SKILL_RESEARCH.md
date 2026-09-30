# Armas, habilidades e melhorias — auditoria de 29/09/2026

## Escopo e conclusão

Pesquisa somente-leitura dos bundles da **cópia**, sem alterar assets, servidor,
inventário ou instalação original. Artefatos derivados ficam em `research`.

O cliente separa três sistemas:

1. **Trait da arma:** `gun_cfg.skill_id`, efeito automático condicionado a
   recarga/tiro/dano; não é o botão da habilidade do personagem.
2. **Habilidade ativa do personagem:** `hero_cfg.skill_id`, com carga,
   animação, alvo e efeito.
3. **Melhoria da habilidade ativa:** `hero_cfg.skill_up_id`, outro skillId,
   descrição e ícone. Não foi encontrado um `skill_up_id` equivalente para
   cada arma. Não inventar um nível 2 da arma a partir de skins.

A linguagem contém referências históricas a desbloquear trait em 2 estrelas
e habilidade melhorada em 5 estrelas (LID 1118/1121), além de consumíveis de
upgrade atuais (LID 3256–3275). A disponibilidade efetiva dessas duas vias no
modo/versão atual precisa de auditoria de progressão, não apenas do texto.

## Fontes reproduzíveis

- `tools/audit_weapon_skills.py`: lê TextAssets Unity e descritores protobuf
  **do Lua bundle atual da cópia**, inclusive campos signed. Gera
  `private-server/config-extract/weapon-skill-audit.json`.
- `fight_dbconfig.ab`: 42 armas, 348 skills, 755 buffs, 714 apresentações de
  buff, 127 remapeamentos de animação por personagem/arma e 54 remapeamentos
  de efeitos de arma. As 42 IDs de arma cobrem exatamente 0–41.
- `fight_languagedb.ab`: LanguageEnglish e LanguagePortugal, preservadas no JSON.
- `private-server/lua-extract/weapon-audit`: descritores e UI de upgrade,
  reextraídos da cópia atual, não dependem da extração histórica.
- SHA256 dos três bundles usados estão no JSON (`provenance.sha256`).
- `skill_cfg` e `skill_cfg_steam` são byte-a-byte iguais. `gun_cfg` e
  `gun_cfg_steam` diferem; a comparação inicial encontrou diferenças de
  `getWay_Common` (aquisição). Não tratar igualdade parcial como igualdade
  completa das tabelas.
- A tabela auxiliar `skill_cfg_level` foi lida com o layout `SkillCfg`;
  não estabelece upgrades de armas e não é fonte de regras atuais.
- Pesquisa pública: [anúncios oficiais Steam](https://steamcommunity.com/app/3591550/allnews/)
  confirmam skins com efeitos próprios, incluindo RedSiren – Dominator. Não
  oferecem um catálogo completo de traits e upgrades; bundles locais são a
  fonte principal para este mapa.

## Traits das armas

IDs abaixo são as linhas visíveis no catálogo (`IsShowInGunCom=1`). Os nomes
ingleses são os efetivamente resolvidos na linguagem do cliente.

| Arma / cfg | Capacidade / máximo real de recarga | skill → buff | Efeito e condição |
|---|---|---|---|
| Little Maniac / 0 | 6 / 3 | 3 → 599 → 600 | Ao recarregar, Lucky Streak: +2 ao próximo dado, limitado a 6. |
| Screwdriver / 1 | 4 / 2 | 2 → 602 | Ao recarregar, converte aleatoriamente 1 bala real comum em aprimorada. `buf_args=[1,2,1]`; não adiciona uma bala extra. |
| Lady J / 6 | 7 / 3 | 10006 → 10015 | Quando reais ≥ falsas, dobra a recompensa de tiros em si. Buff lógico 89, multiplicador 2. |
| Grazier / 7 | 5 / 2 | 10007 → 10040 | Havendo bala aprimorada, o primeiro resultado real será aprimorado. Não significa que o próximo disparo não possa ser falso. |
| Carnivore / 12 | 5 / 2 | 10015 → 10025 | Recompensa 2 R-Chips por ocorrência de dano. Metadados da lógica 46 restringem a tiros normais reais/aprimorados contra outros; não presumir recompensa por skill ou tiro em si. |
| RedSiren / 13 | 6 / 3 | 10019 → 10024 | Se só restam reais, dispara um tiro adicional. A lógica 43 indica ataque normal contra outro personagem; não reutilizar cegamente Burst Mode em tiros em si. |
| LoveSong / 14 | 4 / 2 | 10016 → 10026 | +1 carga da habilidade do personagem por recarga, independente da carga normal de início de turno. |
| Artemis / 34 | 6 / 3 | 10034 → 10053 | Na recarga, troca 1 falsa por 1 real. O máximo real da composição anterior ao trait não é necessariamente o total final. |
| Venom Stinger / 35 | 5 / 2 | 10037 → 10061 | Ao acertar, aplica Toxin: próxima recuperação de HP reduzida em 1, removido ao disparar o efeito ou após um round. Auditar a cadeia 10061 → 10067 → 10066 antes de implementar duração/remoção. |
| Ghosts / 38 | 7 / 3 | 10040 → 10070 | A cada 2 falsas consumidas **por tiro**, carrega imediatamente 1 real. Ejector não deve contar como tiro. Contador/reset em recarga ainda precisa de confirmação. |
| Lucky Revolver / 21 | 6 / 3 | 0 | Sem trait. |
| Lucky Shotgun / 22 | 4 / 2 | 0 | Sem trait. |
| Dealer / 41 | 4 / 2 | 0 | Sem trait ligado nesta linha; arma associada a outro modo, não inventar habilidade. |

As capacidades são configuradas, mas os pesos de sorteio da mistura original
não foram recuperados. O servidor hoje sorteia uniformemente 1..max_real:
é aproximação do laboratório, não prova de duas combinações oficiais.

### Variação não é necessariamente nível 2

- Carnivore tem `skill_diffict`: índice 2 → skill 10028 → buff 10045,
  recompensa 20; índice 3 → skill 10029 → buff 10046, recompensa 200.
  São escalas monetárias do contexto, não melhoria de dano da arma.
- `gunskilldescdiffct` / `gunshortskilldescdiffct` selecionam descrições pelo
  índice de moeda do modo, como prova `GetGunSkillDescByDiffict`.
- IDs 2/3/4, por exemplo, incluem versões de tutorial sem skill ativa;
  outras IDs são variantes internas da mesma família. Não são 42 armas
  com 42 habilidades diferentes.
- Skin visual não comprova alteração de trait. Os remapeamentos de arma e
  personagem podem trocar animação/VFX mantendo a mesma habilidade.

## Habilidades ativas e nível melhorado

Os pares abaixo vêm de `hero_cfg.skill_id/skill_up_id` e `skill_info_cfg.desc`,
não de dedução pelo nome da arma recomendada.

| Personagem / arma recomendada | Básica → melhorada | Efeito básico | Diferença da melhoria | Carga após uso |
|---|---|---|---|---|
| Yu / Little Maniac | 10000 → 10003 | Carrot Bomb: dado ≥3 cura 1 em si ou causa 1 ao inimigo. | Dado 6 cura/causa 2. | 3 |
| No.13 / Screwdriver | 10001 → 10004 | Cheers!: converte todos os Frenzy em HP, inclusive com HP=0. | Preserva Frenzy excedente à cura possível. | 3 |
| Mr.R / Lady J | 10002 → 10013 | Frightful Laughter: troca 2 ofertas aleatórias por Caixas Surpresa grátis. | Troca 3 ofertas. | 3 |
| Arthur / Grazier | 10005 → 10014 | Fair Duel: adiciona uma real ao Cowboy, ele começa; ambos alternam tiros de skill até sair real. | Bala adicionada é aprimorada. | 3 |
| Shelby / Carnivore | 10020 → 10021 | Even Trade: 1 HP/Frenzy por 5 chips, ou 3 chips por 1 HP. | Pode ser usada em Frenzied State. | 2 |
| Annie / RedSiren | 10017 → 10018 | Forced Reloading: transforma 1 falsa do alvo em real. | Em unidade amiga, transforma em aprimorada. | 3 |
| Katie / LoveSong | 10022 → 10023 | Musical Barrier: robô por 1 round bloqueia o primeiro tiro inimigo. | Se não for atingida durante a duração, saída do robô rende 2 chips. | 3 |
| Diana / Artemis | 10032 → 10033 | Hunting Art: dano de tiro normal neste turno retira mais 1 Frenzy do alvo. | Retira também 1 da capacidade máxima de Frenzy. | 3 |
| Vera / Venom Stinger | 10035 → 10036 | Shadow Thread: rouba 1 real/aprimorada/execução e coloca na própria arma. | Prioriza execução/aprimorada. | 2 |
| Hawke / Ghosts | 10038 → 10039 | Aerial Judgment: drone consome metade das reais, arredondando para baixo; faz tantos ataques aleatórios contra inimigos quanto balas carregadas. | Arredonda para cima. | 3 |

`hero.init_skill_cd` pode diferir da carga após uso (Shelby e Vera começam
com valor 3 nas linhas examinadas, embora a skill tenha `cd=2`). Não usar
um único número fixo para todas as etapas de carga.

## Animações e HUD

### Traits automáticos

As dez skills das armas têm os campos de animação/cutscene/câmera zerados ou
vazios na configuração examinada. Logo, **não existe prova de uma cutscene
exclusiva por trait**. A apresentação é ligada ao evento:

- `RouletteGamePlayer:UpdatePlayerInfo`, linha 669: outline `isGunBuff=true`
  chama `NameBoard:ShowGunSkill(gunID)`.
- `RouletteGamePlayerNameBoard:ShowGunSkill`, linha 1225: mostra ícone da arma
  e descrição curta; fecha após 2 segundos. Isso é uma apresentação local,
  não atraso obrigatório para o estado autoritativo.
- `isReload=true` chama `PlayGunEffect(..., Reload)` e `SetAmmo`.
- Mudanças de munição, buffs e chips precisam acompanhar o evento; somente
  mostrar o aviso não executa o efeito.
- `anim_gun_cfg` remapeia `defaultID → finalID` por `heroType/gunType`;
  `effect_gun_cfg` remapeia efeito por arma/modelo; `player_gun_cfg` escolhe
  controller/pose de personagem + família de arma.

### Skills ativas — IDs nativos configurados

| Personagem | Câmeras | Cutscene self/target | Animações relevantes / diferença de upgrade |
|---|---|---|---|
| Yu | Camera01 | 4 / 5 | fonte self 47/other 46; alvo inimigo 48, amigo 156; mesmos IDs na melhoria. |
| No.13 | Camera01_BearSkill | 1 / 1 | fonte self 47; mesmos IDs na melhoria. |
| Mr.R | Camera01_MonkeySkill | 6 / 6 | fonte self 47; mesmos IDs na melhoria. |
| Arthur | Camera02_Right / Camera02_Left | 7 / 7 | skill_typ=10, fluxo de duelo; mesmos IDs na melhoria. |
| Shelby | Camera01_DeerSkill | -1 / -1 | alvo 157; fonte 47/46; isTargetAnimLater=1; mesmos IDs na melhoria. |
| Annie | Camera01 | -1 / -1 | alvo básico 86; melhoria muda alvo self para 87, outros continuam 86. |
| Katie | Camera01_CatSkill | 8 / 8 | fonte 47/46; mesmos IDs na melhoria; robô é apresentação do buff. |
| Diana | Camera01 | -1 / -1 | fonte self 47; mesmos IDs na melhoria. |
| Vera | Camera01_SpiderSkill / Camera02_SpiderSkill | -1 / -1 | alvo 206; fonte other 46; mesmos IDs na melhoria. |
| Hawke | Camera01_EagleSkill | 29 / 29 | fonte other 46; skill_typ=14; mesmos IDs na melhoria. |

IDs acima são referências da configuração, **não teste visual** dos clips,
som ou sincronização. Cutscene -1 não significa ausência de animação.
As animações podem ser remapeadas pelo personagem/arma e por skins.

## Inconsistências recuperadas

- LID 1268 descreve Lady J dando Caixa Surpresa após tiro real em si;
  `gun_cfg` atual descreve recompensa dobrada com reais ≥ falsas. Não unir
  essas duas regras automaticamente; tratar o texto de desbloqueio como
  possivelmente obsoleto. Buff 10015/logic 89 sustenta multiplicador 2.
- Algumas variantes internas Little Maniac/Screwdriver têm textos curtos
  trocados. Referenciar `skill_id`, buff e descrição longa antes de decidir.
- `gunskillInfo` diz Reload inclusive para traits de dano/tiro. Esse rótulo
  genérico não é evidência de que todos os traits só ativem em recarga.
- Carnivore: descrição ampla de dano versus metadados mais restritos de
  ataque normal contra outros. Teste original/manual necessário para bordas.
- RedSiren versus recarga automática ao zerar reais: verificar a ordem de
  resolução da habilidade adicional antes da recarga, sem perder seu tiro.

## Comparação com o servidor local — estado antes da implementação

- `protocol.py:GUN_AMMO_SPECS` cobre capacidade/máximo real, não traits.
- O `Gun` inicial em `pvp_gamer_message` contém id, stacks e modelId, mas
  não preenche `Gun.skillId` (campo 4). Não assume que preencher o campo
  sozinho bastará: o servidor precisa executar os efeitos.
- Não foram encontrados mapeamentos/execução dos dez buffs de traits no
  servidor/protocolo atual. Itens parecidos (Burst Mode, Arms Voucher,
  Energy Pump) não equivalem à habilidade automática da arma.
- O handler de skill ativa do jogador em `server.py` restringe explicitamente
  `skill_id in (10000,10001)`. Assim, Yu e No.13 básicos têm suporte nesse
  caminho, mas os outros personagens e todos os upgrades não devem ser
  anunciados como prontos apenas porque o cliente tem os assets.

## Ordem proposta de implementação e teste

1. Mapa arma → trait e um único hook pós-recarga: Screwdriver, Little Maniac,
   LoveSong, Artemis. Publicar alterações autoritativas junto da apresentação.
2. Hook de escolha/resolução de munição: Grazier, Ghosts, RedSiren. Proteger
   ordem do segundo tiro, contadores e recarga automática.
3. Hook de dinheiro/dano/cura: Lady J, Carnivore e Venom Stinger; respeitar
   escala do modo e duração individual.
4. Registry de skills ativas básicas/melhoradas com charge, alvo e events;
   tirar a lógica do jogador/bot da lista fixa de dois IDs.
5. Testes locais determinísticos para todas as transições, depois testes
   manuais arma por arma e personagem básico/melhorado. Não testar tudo numa
   partida aleatória e declarar completo por ausência de exception.

### Primeira etapa implementada — Screwdriver (v34)

Em 29/09, o mapa e o hook de recarga foram implementados somente para
Screwdriver em `private-server/weapon_skills.py`. A bala aprimorada conta como
real para impedir recarga prematura; seu disparo causa 2 de dano e consome
uma bala. A capacidade continua 4 antes de itens que adicionam munição.
Recarga natural e forçada publicam cfg2 e `isGunBuff`, sem aplicar uma
habilidade nova de personagem nem inventar uma cutscene exclusiva.

161 testes locais passaram, incluindo integração TCP real com o trait ativo,
fluxos de compra direta/uso guardado e interação com itens. Testes não
substituem a validação visual: HUD, animação e som estão pendentes do jogador.
Little Maniac foi implementada após retorno positivo do jogador sobre Screwdriver.
Roteiro manual separado em `WEAPON_TEST_ORDER.md`.

### Segunda etapa implementada — Little Maniac (v35; HUD corrigida em v36)

Auditoria pós-teste: `RouletteGamePlayer.lua` só processa addBuffs em
Buff_Update/Shoot/Pvp_Arcade_Shoot. Typ12 de Spare Magazine ignora esse
campo; NextRound restaura a HUD depois. V36 acrescenta Buff_Update typ10
separado em cada recarga, no próprio dono, com uTime igual ao da recarga.
Isso evita que o callback diferido seja descartado por timestamp antigo.
O bônus com cigarro e skill foi confirmado pelo jogador; a correção visual
da segunda recarga ainda precisa de reteste manual.

IDs 0/8/10/15/19/33 usam skill 3 → trigger 599 → Lucky Streak 600;
configuração de cfg600: lógica 19, argumento 2, uma instância, duração até uso.
V37: carga inicial não ativa traits (confirmação do jogador). Apenas recarga
natural/forçada durante a partida publica uma única instância. Próximo dado do
dono recebe +2 limitado a 6; não apenas o dado da skill ativa.

O descritor atual `pvp_pb.lua` comprova LuckEvent.randLuck (campo 1),
addLuck (2) e buffs (4). `RouletteBattleWindow.lua`, linhas 4240–4260,
mostra a animação original → bônus depois de 1,5s e o limite visual 6.
O servidor publica esses campos e calcula o efeito com o dado ajustado,
remove o ícone do dono e conserva o estado dos outros participantes.

175 testes locais passaram. As integrações TCP cobrem comprado/guardado,
cigarro, Multa, skill ativa e recarga; bots também têm teste. Apresentação
visual permanece pendente do jogador. LoveSong é a próxima etapa planejada.

Casos obrigatórios: recarga inicial/natural/Spare Magazine; capacidade antes
e depois de conversão; dado 1/2/3/6 e consumo de Lucky Streak; enhanced sem
adicionar slot; disparo normal versus Hallucinogen/duelo; falso em si versus
outro; buffs no alvo certo; cura em HP=0 e estado Frenzied; upgrades com
capacidade cheia; morte/recarga durante cadeia de ataques; apresentação HUD
sem congelar ou atrasar estado. Misturas originais e câmera de morte seguem
pendentes separados.

### Terceira etapa — LoveSong (v38)

Configuração local verificada: gun_cfg/steam cfg14 skill10016; skill_cfg
aponta para buff10026, cujo trigger12/lógica38/argumento1 concede uma carga
por recarga. Não confundir buff10026 com skill10026 do cervo: tabelas distintas.
No protocolo atual cargas são representadas por Hero.SkillCd restante:
reduzir1, limitado a0. Abertura não ativa trait. Hook compartilhado com as
recargas efetivas já existentes, sem modificar o carregador de capacidade4.
Lua SetSkillCD aceita Enum_Skill_Cd/Reset_Cd, não reload: publicamos typ9
com campo21 no dono, timestamp igual à recarga e isGunBuff para apresentação.
184 testes locais passaram; apresentação visual aguarda retorno do jogador.

### Quarta etapa — Artemis (v39)

Gun cfg34 nas duas tabelas usa skill10034 → buff10053: trigger12, lógica66,
args [300,1,1]. A composição é sorteada antes de converter1 falsa em1 real,
preservando capacidade6. reload_max_real3 limita a composição base, não o
resultado pós-trait. Abertura sem conversão; recargas efetivas usam o hook
comum do servidor e bots. Envelopes publicam munição convertida/isGunBuff.
Não precisa de buff persistente na HUD: efeito instantâneo de recarga.
Seis testes novos; apresentação visual aguarda validação manual.

V40: log confirmou conversão1/5→2/4 em três recargas, mas V39 omitira CAmmo.
Sequência nativa recuperada: Enum_Reload base, Enum_Reload_And_Change_Ammo
final; ClientAnimExpression.AfterReload e RouletteGamePlayer.AddAfterReloadTimer
aplicam a segunda etapa com atraso nativo. CAmmo.source300,num1 → target1,num1
orienta popIndex/addIndex da HUD; só a segunda etapa mostra isGunBuff.
190 testes passaram; aguardando confirmação visual, sem alterar misturas.

### Quinta etapa — Grazier (v41)

IDs7/18/31 com skill10007 na configuração Steam; buff10040 trigger16,
lógica52,args[1,2,2]. Sorteio conserva probabilidade total live/blank e,
se sair real comum com aprimorada disponível, substitui o resultado porcfg2.
Tiros normais de jogador/bot/rajada e forçados compartilham regra. Não se
aplica a Ejector (remoção aleatória), nem cria balas na abertura/recarga.
Rocket já consome todas as reais no acerto. isGunBuff no tiro aprimorado;
196 testes passaram. Teste manual requer Arms Voucher e ao menos uma
amarela comum restante para distinguir prioridade de sorteio ordinário.

### Sexta etapa — Ghosts (v42)

cfg38 skill10040/buff10070: trigger35/lógica91,args[2,1,2]. Cada2 falsas por
tiro carrega1 real. Reset em recarga adotado conforme lembrança provisória
do jogador (configuração não explicita). Native Buff.args campo2 armazena
parcial por dono; não confundir args com contagem global. Real intercalada
e turno mantêm parcial; recarga limpa; Ejector não dispara hook.
AddFixed_Ammo typ21 publica ammo1,num1/rAmmo final após tiro, isGunBuff para
aviso e indices de adição nativos da HUD. Integração normal/rajada/forçado/RPG;
efeitos e apresentação manual ainda aguardam teste.

### Sétima etapa — RedSiren (v45)

cfg13 skill10019/buff10024 trigger7/17,lógica43,args[1,2]. Texto da lógica
restringe tiro normal contra outro com apenas reais; adiciona1 disparo.
Hook compartilhado por jogador/bots e modos2/3 participantes; cadeia real
com dano/consumo individuais, respeitando interrupção por morte/sem munição.
Sem efeito em self/Alucinógeno/Rocket. Burst+trait soma1 adicional atualmente,
interpretação provisória até teste manual. isGunBuff avisa no primeiro tiro.
211 testes passaram. Ghosts foi confirmada manualmente após campo69 nativo.

### Oitava etapa — Carnivore (v46)

cfg12 skill10015/buff10025 trigger13,lógica46,args[2,2]. Lógica restringe
reais/aprimoradas de tiro normal em outro; descrições citam causar dano.
Implementado2 por acerto danoso, não por quantidade de dano, incluindo
Frenzy; bloqueio completo não rende. Tiros separados de Burst somam; self,
skill/forçado/RPG não aplicam hook. Saldo persistido no shooter e delta nativo
de moeda no tiro, isGunBuff para aviso. Multiplicadores futuros não alterados.
218 testes passaram; aguardando teste visual. Associação corrigida: RedSiren
pertence à Annie; Carnivore ao Shelby (confirmação do jogador).

### Nona etapa — Lady J (v47)

IDs6/17/30/32 skill10006/buff10015 trigger34,lógica89,args[2]. Condição
localizada reais≥falsas antes do tiro em si; dobra shot reward. Implementação
aplica2 ao cálculo inteiro (base+combo), interpretação a confirmar manualmente.
Pool e próximo valor de jogador/bots usam mesmo hook, aviso no disparo
qualificado. Não altera tiros em outros nem ganha moeda ao entrar.
Carnivore confirmada; aviso card inválido do menu foi registrado separado.

### Décima etapa — Venom Stinger (v48, trio com loja)

Dados cfg35 skill10037, chain10061→10067→10066, ícone spidergun. Primeiro
hook em tiro normal danoso de jogador/bots no trio. Próxima cura positiva
reduz1/remove, segunda normal; falha/zero não dispara. Cigarro direto/guardado,
coelha, urso e bots integrados. Relógio individual de turnos, start+2 conforme
explicação do jogador; refresh sem empilhar. Eventos addBuffs/delBuffs nativos.
231 testes passaram. Aplicação/expiração no duelo e ataques especiais ainda
pendentes; cobertura de futuras skills de cura depende de integração no hook.
