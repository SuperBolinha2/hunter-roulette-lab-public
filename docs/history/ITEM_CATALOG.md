# Hunter Roulette — mapa de itens utilizáveis (laboratório)

Fonte: `fight_dbconfig.ab` (`card_cfg` e `skill_cfg`) e
`fight_languagedb.ab` (`LanguageEnglish`) da **cópia laboratorial**. Os nomes,
descrições, `cfgId` e `skillId` foram extraídos dos arquivos; os efeitos
reconstituídos no servidor precisam de teste real no cliente. O jogador
consultou o menu `ITEM` e relatou esses registros, mas isso não prova que cada
`cfgId` seja uma oferta separada na loja do modo 1/6. Alguns têm o mesmo nome
localizado e parâmetros distintos; “variante” era apenas um rótulo interno
nosso, não um nome/categoria do jogo. A cópia laboratorial oferece esses
registros em quatro posições; isso é uma seleção de teste, não uma reconstrução
confirmada da disponibilidade ou ponderação originais. Bolsa de
Sangue (2035) e cartas de pôquer (2038–2044) ficam fora deste recorte até
existir evidência do contrato de equipe/pôquer.

| cfgId | Item (nome do cliente) | skillId | Preço cfg | Alvo cfg | Efeito descrito pelo cliente | Estado local |
|---:|---|---:|---:|---:|---|---|
| 2001 | Ejector | 1000 | 100 | 3 | Retira uma bala aleatória da arma escolhida | Confirmado pelo jogador; uso também aparece no trace local |
| 2003 | Real Bullet+1 | 1002 | 200 | 3 | Acrescenta uma bala real ao alvo | Confirmado pelo jogador |
| 2004 | Blank Bullet+1 | 1003 | 100 | 3 | Acrescenta uma bala falsa ao alvo | Confirmado pelo jogador |
| 2007 | Spare Magazine | 1006 | 300 | 3 | Força troca de carregador e recarga | Confirmado pelo jogador: efeito funcional em si e no bot, animação suave; composição de munição varia e fica para a etapa futura de armas |
| 2008 | Hallucinogen | 1007 | 200 | 3 | Força o alvo a atirar em si | Confirmado pelo jogador; trace registra uso em si e em bot; recarga local após zerar munição real |
| 2009 | Arms Voucher | 1008 | 200 | 3 | Converte uma bala real existente em cfg 2 (bala melhorada); o próximo tiro causa 2 danos sem aumentar o total do carregador | Confirmado pelo jogador: substitui uma bala sem aumentar o pente e causa 2 de dano |
| 2011 | Wet Cigarettes | 1010 | 200 | 3 | Dado 4+ recupera uma vida | Confirmado pelo jogador; não deve curar quando HP está em 0 |
| 2015 | Maintenance Kit | 1014 | 300 | 4 | Próximo tiro normal contra outro jogador causa +1 dano | Efeito, ícone e dano confirmados; erro 352 impede reaplicação local enquanto ativo; aviso visual da trava não fechado |
| 2016 | Burst Mode | 1015 | 300 | 4 | Próximo tiro normal contra outro jogador dá dois acertos consecutivos | Confirmado no reteste: tiro próprio consumiu sem rajada (`double_shot=False`); tiro contra bot gerou a sequência de rajada (`double_shot=True`) |
| 2018 | Violation Ticket | 1017 | 400 | 2 | Descrição literal da cópia: “Lance um dado para roubar um valor em recompensas igual ao resultado do dado ×100.” | Confirmado manualmente: dado 2, bot 10.000→9.800, jogador 10.000−400+200=9.800; animações de dado, moedas e personagem ocorreram. Erro 380 se alvo sem valor ainda não testado visualmente |
| 2020 | Surprise Box | 1019 | 200 | 1 | Gera item aleatório no armazenamento temporário | Abertura confirmada duas vezes; testar separadamente os itens recebidos |
| 2021 | Wanted | 1020 | 200 | 3 | Cada aplicação dura N trocas de turno, com N = participantes vivos no uso; o primeiro dano de tiro paga 4 R-Chips ao atacante; sem dano, o marcado vivo recebe 4 ao expirar | Jogador aprovou contagem individual, duração e mira após ajustes; 110 testes TCP. Observar regressões |
| 2022 | Purchase Ban | 1021 | 300 | 2 | Bloqueia compras do alvo no próximo turno | Jogador confirmou 3 aplicações no Bot 1 sem compras dele nos turnos afetados (2 da loja + 1 guardado); a IA omite ofertas compráveis sob buff 1021. Não há pacote de tentativa/rejeição explícita |
| 2024 | Wet Cigarettes | 1022 | 200 | 1 | Mesmo nome localizado da cfg 2011; configuração self-only da família Lucky | Registro de banco; oferta separada no modo 1/6 não confirmada |
| 2025 | Hallucinogen | 1023 | 200 | 2 | Mesmo nome localizado da cfg 2008, com configuração original de alvo diferente | Jogador confirmou uso no bot; a cópia também habilitou mirar em si por correção local |
| 2026 | Ejector | 1024 | 100 | 3 | Mesmo nome localizado/efeito-base da cfg 2001 | Registro de banco; oferta separada no modo 1/6 não confirmada |
| 2027 | Wet Cigarettes | 1025 | 200 | 1 | Mesmo nome localizado da cfg 2011; configuração self-only da família Lucky | Registro de banco; oferta separada no modo 1/6 não confirmada |
| 2028 | Surprise Box | 1019 | 200 | 1 | Mesmo nome localizado da família Surprise Box, cfg diferente | Registro de banco; disponibilidade e diferença de prêmio não confirmadas |
| 2029 | Tranquilizer | 10008 | 300 | 3 | Reduz o Frenzy do alvo em metade do HP atual, arredondada para cima (limitada ao Frenzy restante) | Jogador confirmou o efeito; log de 29/09 confirma Bot 2 escolhendo cfg 2029 no Bot 1. Uso próprio e detalhe de HUD/animação não isolados |
| 2030 | Permission Ban | 10009 | 200 | 2 | Bloqueia habilidade do inimigo no próximo turno | Jogador confirmou funcionamento; log de 29/09 registra compra/uso no alvo 1. Próxima pendência comprável: provar a rejeição de compra do cfg 2022 |
| 2031 | Energy Pump | 10010 | 200 | 3 | Carrega habilidade +1 | Confirmado pelo jogador em si e em bot; trace confirma carga da habilidade sem alteração de HP ou munição |
| 2032 | Rocket Launcher | 10011 | 600 | 2 | Sorteia uma munição: falsa consome uma falsa sem dano; real consome todas as reais e causa dano igual à quantidade consumida | Jogador confirmou que funcionou na partida; implementação em compra-uso e item guardado tem cobertura de pacote/TCP |
| 2033 | Bucket | 1026 | 200 | 1 | Bloqueia o primeiro dano de tiro normal neste turno | Jogador confirma que funciona e que aparição/animação parecem corretas; log recente não contém partida para validação visual independente |
| 2034 | Piggy Bank | 1028 | 0 | 4 | Acumula moedas por turno e concede o total ao usar | Item equipado antes da partida; sequência reservada para a etapa pós-itens compráveis. Protocolo local cobre acumular/coletar; validar seleção e visual no cliente. A bolsa dourada congelada não foi vinculada a ele |
| 2036 | Surprise Box | 1038 | 200 | 1 | Mesmo nome localizado da família Surprise Box, cfg/skill diferente | Registro de banco; disponibilidade e diferença de prêmio não confirmadas |
| 2037 | Surprise Box | 1039 | 200 | 1 | Mesmo nome localizado da família Surprise Box, cfg/skill diferente | Registro de banco; disponibilidade e diferença de prêmio não confirmadas |

Separados deste recorte: 2035 Blood Bag (alvo companheiro de equipe) e
2038–2044 (mecânicas de cartas de pôquer). Não apresentar essas linhas como
itens disponíveis no modo de três participantes antes de evidência adicional.

`Alvo cfg` vem de `skill_cfg.target_typ`: 1=si, 2=oponentes, 3=todos,
4=mesma equipe (incluindo si), 5=só companheiro, 6=todos menos si.
São regras de seleção do cliente, não prova de que o efeito do servidor
já esteja implementado. `Preço cfg` é `card_cfg` campo 13.

## Contrato de efeito já identificado

- 2003/2004: `skill_typ=3` (ChangeAmmo); pequeno evento
  `Enum_AddFixed_Ammo=21`, `ammo` com uma bala e `rAmmo` com a lista completa
  após o uso.
- 2007: `skill_typ=3` (ChangeAmmo); o cliente espera
  `Enum_Reload_And_Change_Ammo=12`, `isReload=true`, `rAmmo` completo e pares
  `cAmmo` para substituir os dois tipos de munição. O construtor local passou
  em teste de pacote; o jogador agora confirmou efeito e animação suave em si
  e no bot. As composições que apareceram variaram. A regra original de
  capacidade/combinação por arma ainda não foi recuperada; não tratar a
  composição atual como original. Deixar a investigação de `ammoBank` para a
  etapa de armas, depois de fechar os testes dos itens.
- 2001: `skill_typ=9` (PopAmmo); pequeno evento `Enum_Pop_Ammo=13` com
  `uAmmo` da bala removida. `ClientAnimExpression.PopAmmo` guarda o evento pelo
  índice da **origem** e `StartPopAmmo` o aplica no callback da animação do
  alvo; por isso, nesse pequeno evento origem e alvo devem ser o jogador que
  perdeu a bala. O código/config também declara `BuffLogic.Pop_Ammo_If_Reload_Show_Reload=127`
  (“ejetar uma bala e, se houver recarga, notificar imediatamente”) e
  `ReloadSource.By_Pop_Ammo=2`. Ainda não foi confirmado que cada variante de
  Ejetor referencia esse buff na tabela do item; no laboratório, quando a
  ejeção deixa o alvo sem balas reais, o resultado agora inclui `Enum_Reload`
  depois do `Enum_Pop_Ammo`, no mesmo `PvpEventResult`, para o cliente consumir
  ambos na sequência da animação. Isso também evita deixar o botão de tiro
  disponível com pente vazio.
- 2008: `skill_typ=2` (Shoot); o resultado de uso contém os subeventos de
  tiro e de fonte final. O cliente aceita escolher a si mesmo apesar da
  descrição inglesa mencionar inimigo; o jogador confirmou esse uso. O handler
  compartilhado agora acrescenta `Enum_Reload` logo após o tiro se o alvo ficar
  sem munição real e sobreviver. A mistura do novo pente ainda segue apenas a
  estimativa local por arma, não a regra original.
- 2025: skill 1023 compartilha o disparo forçado com 2008, mas o cfg original
  tem `target_typ=2`, que exclui o jogador principal do seletor. Na cópia, o
  Lua agora expõe uma seta para o jogador principal somente para skill 1023;
  o servidor já aceita o índice 0. Isso é uma alteração intencional do
  laboratório, não comportamento confirmado do cliente original. A mensagem
  ainda usa a palavra “enemy”. O trace de 2026-09-27 confirma que o uso no Bot
  1 gastou a última bala real (HP 4→3) e deixou balas falsas sem recarregar;
  agora o resultado manda o evento de tiro com contagens pós-tiro, seguido por
  `Enum_Reload` com o pente novo, e o snapshot final fica sincronizado.
- 2032: `skill_typ=11` (Rpg), `Enum_Rpg=39`. O evento deve pôr `uAmmo` e
  `isRpgHit` na origem: `RouletteGamePlayer:OpUAmmoData_Rpg` consome exatamente
  essa lista, e a animação do alvo consulta `source.isRpgHit`. Regra confirmada
  pela descrição do bundle e pelo jogador: sorteia uma bala; falsa consome uma
  cfg300 sem dano; real consome todas as cfg1 restantes e causa dano igual à
  quantidade real pré-disparo. Atualização de HP e Frenzy usa deltas separados;
  se a reserva real acaba e a partida continua, `Enum_Reload` ocorre depois da
  animação RPG. A bala melhorada cfg2 é tratada como real no sorteio/consumo e
  conta como um espaço para o dano do Rocket; combinação visual com Arms Voucher
  ainda requer reteste manual.
- Recarga automática local: todos os caminhos de tiro PVP recarregam assim que
  o contador de munição real chega a zero (incluindo um pente só de falsas),
  salvo eliminação/fim da partida. O evento de recarga vem depois do evento de
  disparo; o teste de integração confirma que a sequência permite continuar o
  tiro próprio falso sem uma notificação intermediária que resetaria a mira.
- 2011/2024/2027: `skill_typ=6` (Lucky); `Enum_Update_Luck=7` carrega
  `LuckEvent.randLuck` e `isSuccess` para a UI de dado. Em sucesso 4–6,
  `Enum_Heal=20` carrega o delta de vida, limitado ao máximo de 4 no modo
  local. `card_cfg` da cópia informa preço 200 para cfg 2011; o laboratório
  agora usa esse valor. Os preços dos itens suportados vêm do campo 13 da
  mesma tabela.
