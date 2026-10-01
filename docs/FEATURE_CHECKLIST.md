# Checklist do jogo — Feature checklist

Última auditoria: **30/09/2026**. Esta é a lista principal de trabalho, não uma promessa de que o jogo inteiro foi restaurado.

[Voltar ao README](../README.md) · [Catálogo técnico completo](FEATURE_CATALOG.md) · [Estado do backend](CURRENT_STATUS.md) · [Modelo de teste/descoberta](templates/FEATURE_TEST.md)

## Como usar sem conhecer Git

1. Procure a área pelo índice ou pelo nome em inglês que aparece no jogo.
2. Uma função ainda incompleta fica com `- [ ]`; só troque para `- [x]` quando a função **descrita naquela linha** estiver validada.
3. Para algo funcionando só em parte, mantenha `[ ]`, escreva `[PARCIAL]` e explique o que falta. GitHub Markdown não tem uma terceira marcação nativa de checkbox.
4. Para adicionar algo, copie o [modelo](templates/FEATURE_TEST.md), dê um ID novo e coloque na área correspondente. Não reutilize IDs antigos.
5. No GitHub, abra este arquivo e use o lápis **Edit**. Edite o texto, proponha a mudança em uma branch e peça revisão. Pelo GitHub Desktop, siga o README. **Estas caixas no arquivo não são um painel que salva sozinho ao clicar.**
6. Antes de fechar, registre personagem, arma, modo, sequência, resultado e evidência. Um ícone ou uma resposta de sucesso do servidor não bastam para provar o efeito.
7. Bugs ativos podem ganhar uma Issue, ligada ao ID da linha. Esta página continua sendo o mapa principal; não manter duas listas completas divergentes.

Para quem altera o código: [CONTRIBUTING](../CONTRIBUTING.md).
Para IAs: [AGENTS.md](../AGENTS.md). O modelo de pull request pede os IDs afetados,
estado anterior/novo, evidência e testes pendentes. Estas orientações não
marcam nada automaticamente e não substituem aprovação manual.

O GitHub gera as abas de apresentação para arquivos especiais; não há opção
documentada para uma aba personalizada de Checklist naquele quadro. Por isso,
o README tem uma barra de acesso no topo. Não usar SECURITY ou CONTRIBUTING
como disfarce para mudar a função dessas abas.

GitHub oferece [listas de tarefas Markdown](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/about-tasklists) e [sub-issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues). Escolhemos Markdown para começar: fica no Git, é fácil de revisar, baixar e editar. Não usamos os antigos blocos especiais de tasklist, descontinuados.

### Legenda e critérios

| Marcação | Significado |
| --- | --- |
| `[x] [CONFIRMADO]` | Comportamento específico aprovado manualmente pelo jogador no contexto indicado. |
| `[ ] [PARCIAL]` | Algumas partes existem/funcionam; a linha diz o que falta. |
| `[ ] [TESTAR]` | Há implementação ou cobertura automática, mas falta confirmação manual desse fluxo. |
| `[ ] [FAZER]` | Falta conhecida; precisa implementação/ajuste. |
| `[ ] [AUDITAR]` | Tela/configuração encontrada, mas contrato, acesso ou suporte ainda não determinados. |
| `[ ] [FUTURO]` | Planejamento; não é confirmação de recurso original. |

**Escopo das confirmações atuais:** cópia isolada do laboratório, conta GM preservada, partida local de três participantes com loja, salvo indicação diferente. Abrir um menu não prova persistência, economia, multiplayer ou todos os modos. Testes automáticos não são testes de câmera/som. Uma área só termina quando suas pendências terminarem; não há percentual global artificial.

Nomes em inglês ajudam a equipe internacional. Traduções aqui são rótulos de navegação, não alterações no cliente. Nas tarefas de auditoria, a lista é um roteiro do que verificar, não uma afirmação de que todos os subrecursos estão disponíveis nesta versão.

## Índice — árvore do jogador

- [Login / entrada](#login--entrada)
- [Lobby / tela principal](#lobby--tela-principal)
  - [Perfil / Local Hunter](#perfil--local-hunter)
  - [Hero / personagens](#hero--personagens)
  - [Weapon / armas](#weapon--armas)
  - [Prop / itens](#prop--itens)
  - [Base](#base)
  - [Backpack / mochila](#backpack--mochila)
  - [Supply Box](#supply-box)
  - [Shop / loja do lobby](#shop--loja-do-lobby)
  - [Challenge / progressão / temporada](#challenge--progressão--temporada)
  - [Clan / Friend / social](#clan--friend--social)
  - [Other / outras opções](#other--outras-opções)
  - [Lobby / escolha de modos](#lobby--escolha-de-modos)
- [Dentro da partida](#dentro-da-partida)
- [Infraestrutura / distribuição](#infraestrutura--distribuição)
- [Novas descobertas e prioridades](#novas-descobertas-e-prioridades)

## Fontes e limites da auditoria

- Configurações e registro de janelas da **cópia**, lidos sem modificar a instalação original. Foram identificados **265 nomes candidatos de janelas**, **35 registros de modos**, **13 armas com flag de exibição no catálogo** e **10 personagens principais**. Há tutoriais, variantes e referências internas; os números não equivalem a recursos jogáveis completos.
- Foram lidos 590 TextAssets de configuração, incluindo pares Steam/não-Steam e dados auxiliares. Não são 590 funções.
- Evidência histórica: [itens](history/ITEM_IMPLEMENTATION_MATRIX.md), [armas](history/WEAPON_TEST_ORDER.md), [melhorias de herói](history/HERO_UPGRADE_PLAN.md), [progresso](history/PROGRESS.md) e código/testes atuais do servidor.
- Prints enviados nesta sessão confirmam a navegação visível do lobby, Other, anúncio Season 18 e Main Mode. Não publicamos esses prints nem dumps proprietários no repositório.
- O print mostra temporada de maio/2026, embora esta auditoria seja de setembro. Datas antigas e uma tela de anúncio não comprovam calendário/progressão reais.

## Login / entrada

- [ ] [PARCIAL] `AUTH-01` Entrar no laboratório e chegar ao lobby: funcional com identidade local/GM; não equivale à autenticação original Steam ou serviço público.
- [ ] [FAZER] `AUTH-02` Conta nova realmente zerada: criação, nome, herói inicial, inventário, moedas e tutorial naturais.
- [ ] [AUDITAR] `AUTH-03` Seleção de conta/servidor/região, idiomas iniciais e fluxo de visitante; distinguir telas legadas mobile/Steam.
- [ ] [AUDITAR] `AUTH-04` Avisos, políticas, código de prêmio e validações de nome.
- [ ] [TESTAR] `AUTH-05` Falha de conexão, mensagem útil, tentar novamente e retorno sem travar.
- [ ] [FAZER] `AUTH-06` Identidades separadas, sessão/reconexão e progresso de vários usuários sem misturar saves.
- [ ] [AUDITAR] `AUTH-07` Tutorial inicial, revisão do tutorial, desbloqueio de funções e término persistente.

## Lobby / tela principal

A árvore abaixo segue os prints atuais: perfil e Base no alto; Clan/Friend/Backpack/Other; Shop e Supply Box à esquerda; Challenge/Prop/Weapon/Lobby/Hero à direita; escolha de modo e START.

- [x] [CONFIRMADO] `LOBBY-01` Tela principal e esses botões existem visualmente nos prints atuais; esta linha confirma **navegação visível**, não seus sistemas.
- [ ] [PARCIAL] `LOBBY-02` Nome, avatar, herói, Base e moedas aparecem; saldo real, progressão e troca de perfil precisam testes próprios.
- [ ] [AUDITAR] `LOBBY-03` Animações/falas do herói, gramofone, cena sazonal e objetos clicáveis.
- [ ] [TESTAR] `LOBBY-04` Voltar de cada submenu sem perder seleção, duplicar janela ou deixar máscara bloqueando clique.
- [ ] [AUDITAR] `LOBBY-05` Avisos/popups automáticos, recompensas diárias e indicadores New/notificação.
- [ ] [TESTAR] `LOBBY-06` Modo selecionado, entrada/prêmio exibidos e START coerentes com a partida criada.

## Perfil / Local Hunter

- [ ] [PARCIAL] `PROFILE-01` Dados locais retornados pelo backend; conta GM sintética, sem provar estatísticas naturais.
- [ ] [AUDITAR] `PROFILE-02` Avatar, apelido, renomear, título/cartão de visita, moldura e coleções.
- [ ] [AUDITAR] `PROFILE-03` Ver perfil próprio e de outro jogador, herói/equipamento e estatísticas.
- [ ] [AUDITAR] `PROFILE-04` Histórico de partidas, relatório, detalhes e simulação/replay; respeitar versões do protocolo.
- [ ] [FAZER] `PROFILE-05` Persistência isolada por usuário e estatísticas calculadas de partidas reais, não privilégios GM.

## Hero / personagens

- [ ] [PARCIAL] `HERO-01` Lista, seleção e equipamento: handlers locais existem; confirmar posse, salvar e restaurar ao reiniciar com conta normal.
- [ ] [AUDITAR] `HERO-02` Cada página: nome, descrição, história, preview, aparência, badge e recompensas de uso.
- [ ] [FAZER] `HERO-03` Enhance Hero: melhorar por nível/estrelas **ou** compra permanente, o que vier primeiro; regra final e custos naturais a validar.
- [ ] [FAZER] `HERO-04` Compra/uso do item de melhoria (referência `1135`), persistência e impedir recompra indevida.
- [ ] [TESTAR] `HERO-05` Cargas de skill: início sem carga indevida, +1 na nova vez, consumo, HUD e limites/itens modificadores.
- [ ] [TESTAR] `HERO-06` Bloqueio, alvo inválido, custo, animação e HUD sem atrasar estado; modos em equipe exigem matriz própria.

### Coelha — Yu / Mad Bunny - Yu

- [x] [CONFIRMADO] `HERO-YU-01` Skill básica `10000` e melhorada `10003` no contexto local: Básica e melhoria exercitadas; melhoria com dado 6 recuperou 2 HP em si.
- [ ] [TESTAR] `HERO-YU-02` Alvo aliado/oponente na melhoria, limites de cura e combinações.
- [ ] [AUDITAR] `HERO-YU-03` Aparência, história, emblemas, recompensas e seleção/equipamento específicos deste personagem.
- [ ] [FAZER] `HERO-YU-04` Aquisição natural e desbloqueio da melhoria sem privilégios GM, conforme regra de progressão validada.

### Urso — No.13 / Escaped Bear - No.13

- [x] [CONFIRMADO] `HERO-BEAR-01` Skill básica `10001` e melhorada `10004` no contexto local: Conversão de Frenzy em HP e melhoria confirmadas.
- [ ] [TESTAR] `HERO-BEAR-02` HP/Frenzy nos limites, interação com bloqueios e outros modos.
- [ ] [AUDITAR] `HERO-BEAR-03` Aparência, história, emblemas, recompensas e seleção/equipamento específicos deste personagem.
- [ ] [FAZER] `HERO-BEAR-04` Aquisição natural e desbloqueio da melhoria sem privilégios GM, conforme regra de progressão validada.

### Macaco — Mr.R / Jester Monkey - Mr.R

- [x] [CONFIRMADO] `HERO-MONKEY-01` Skill básica `10002` e melhorada `10013` no contexto local: Básica/melhoria de ofertas grátis confirmadas no laboratório.
- [ ] [TESTAR] `HERO-MONKEY-02` Distribuição original das ofertas e esgotamento da loja.
- [ ] [AUDITAR] `HERO-MONKEY-03` Aparência, história, emblemas, recompensas e seleção/equipamento específicos deste personagem.
- [ ] [FAZER] `HERO-MONKEY-04` Aquisição natural e desbloqueio da melhoria sem privilégios GM, conforme regra de progressão validada.

### Cowboy — Arthur / Cowboy - Arthur

- [x] [CONFIRMADO] `HERO-ARTHUR-01` Skill básica `10005` e melhorada `10014` no contexto local: Fair Duel exercitado; Grazier prioriza a vermelha quando o disparo é real, sem eliminar chance de falsa.
- [ ] [TESTAR] `HERO-ARTHUR-02` Robô contra duelo: regressão visual dirigida; espectador após duelo.
- [ ] [AUDITAR] `HERO-ARTHUR-03` Aparência, história, emblemas, recompensas e seleção/equipamento específicos deste personagem.
- [ ] [FAZER] `HERO-ARTHUR-04` Aquisição natural e desbloqueio da melhoria sem privilégios GM, conforme regra de progressão validada.

### Cervo — Shelby / Gentle Deer - Shelby

- [x] [CONFIRMADO] `HERO-SHELBY-01` Skill básica `10020` e melhorada `10021` no contexto local: Trocas HP/chips nas duas direções confirmadas.
- [ ] [TESTAR] `HERO-SHELBY-02` Escalas monetárias e limites fora do trio.
- [ ] [AUDITAR] `HERO-SHELBY-03` Aparência, história, emblemas, recompensas e seleção/equipamento específicos deste personagem.
- [ ] [FAZER] `HERO-SHELBY-04` Aquisição natural e desbloqueio da melhoria sem privilégios GM, conforme regra de progressão validada.

### Polvo — Annie / Pirate Octopus - Annie

- [x] [CONFIRMADO] `HERO-ANNIE-01` Skill básica `10017` e melhorada `10018` no contexto local: Conversão própria falsa→vermelha e inimiga falsa→real confirmadas.
- [ ] [TESTAR] `HERO-ANNIE-02` Arma cheia, proteção e alvos em equipes.
- [ ] [AUDITAR] `HERO-ANNIE-03` Aparência, história, emblemas, recompensas e seleção/equipamento específicos deste personagem.
- [ ] [FAZER] `HERO-ANNIE-04` Aquisição natural e desbloqueio da melhoria sem privilégios GM, conforme regra de progressão validada.

### Gata — Katie / Sweety Cat - Katie

- [ ] [PARCIAL] `HERO-KATIE-01` Skill básica `10022` / melhorada `10023`: robô/proteção aprovados no contexto local; falsa conserva proteção até expirar. Não fechar separadamente o bônus monetário da melhoria sem teste dirigido.
- [ ] [TESTAR] `HERO-KATIE-02` Rocket e Grazier/duelo têm testes automáticos; falta confirmar visualmente essas combinações.
- [ ] [AUDITAR] `HERO-KATIE-03` Aparência, história, emblemas, recompensas e seleção/equipamento específicos deste personagem.
- [ ] [FAZER] `HERO-KATIE-04` Aquisição natural e desbloqueio da melhoria sem privilégios GM, conforme regra de progressão validada.

### Leoa — Diana / Tribal Lioness - Diana

- [ ] [AUDITAR] `HERO-DIANA-01` Skill básica `10032` e melhorada `10033` no contexto local: Não fechar executor básico/melhorado apenas por catálogo ou animação.
- [ ] [TESTAR] `HERO-DIANA-02` Reconstruir contrato, efeito, duração, animação e testar os dois níveis.
- [ ] [AUDITAR] `HERO-DIANA-03` Aparência, história, emblemas, recompensas e seleção/equipamento específicos deste personagem.
- [ ] [FAZER] `HERO-DIANA-04` Aquisição natural e desbloqueio da melhoria sem privilégios GM, conforme regra de progressão validada.

### Aranha — Vera / Merc Spider - Vera

- [ ] [AUDITAR] `HERO-VERA-01` Skill básica `10035` e melhorada `10036` no contexto local: Não fechar executor básico/melhorado apenas por catálogo ou animação.
- [ ] [TESTAR] `HERO-VERA-02` Reconstruir contrato, efeito, duração, animação e testar os dois níveis.
- [ ] [AUDITAR] `HERO-VERA-03` Aparência, história, emblemas, recompensas e seleção/equipamento específicos deste personagem.
- [ ] [FAZER] `HERO-VERA-04` Aquisição natural e desbloqueio da melhoria sem privilégios GM, conforme regra de progressão validada.

### Águia — Hawke / War Eagle - Hawke

- [ ] [AUDITAR] `HERO-HAWKE-01` Skill básica `10038` e melhorada `10039` no contexto local: Não fechar executor básico/melhorado apenas por catálogo ou animação.
- [ ] [TESTAR] `HERO-HAWKE-02` Reconstruir contrato, efeito, duração, animação e testar os dois níveis.
- [ ] [AUDITAR] `HERO-HAWKE-03` Aparência, história, emblemas, recompensas e seleção/equipamento específicos deste personagem.
- [ ] [FAZER] `HERO-HAWKE-04` Aquisição natural e desbloqueio da melhoria sem privilégios GM, conforme regra de progressão validada.

## Weapon / armas

Armas têm traits/passivas próprios. **Não atribuir melhoria de skill de personagem às armas.** O catálogo técnico registra todas as 13 armas exibidas; há mais registros internos.

- [x] [CONFIRMADO] `GUN-00` Little Maniac: trait `3` aprovado no trio; não fecha misturas/combinações em todos os modos.
- [x] [CONFIRMADO] `GUN-01` Screwdriver: trait `2` aprovado no trio; não fecha misturas/combinações em todos os modos.
- [x] [CONFIRMADO] `GUN-06` Lady J: trait `10006` aprovado no trio; não fecha misturas/combinações em todos os modos.
- [x] [CONFIRMADO] `GUN-07` Grazier: trait `10007` aprovado no trio; não fecha misturas/combinações em todos os modos.
- [x] [CONFIRMADO] `GUN-12` Carnivore: trait `10015` aprovado no trio; não fecha misturas/combinações em todos os modos.
- [x] [CONFIRMADO] `GUN-13` RedSiren: trait `10019` aprovado no trio; não fecha misturas/combinações em todos os modos.
- [x] [CONFIRMADO] `GUN-14` LoveSong: trait `10016` aprovado no trio; não fecha misturas/combinações em todos os modos.
- [ ] [TESTAR] `GUN-21` Lucky Revolver: sem trait nesta configuração; validar comportamento básico no modo correspondente.
- [ ] [TESTAR] `GUN-22` Lucky Shotgun: sem trait nesta configuração; validar comportamento básico no modo correspondente.
- [x] [CONFIRMADO] `GUN-34` Artemis: trait `10034` aprovado no trio; não fecha misturas/combinações em todos os modos.
- [x] [CONFIRMADO] `GUN-35` Venom Stinger: trait `10037` aprovado no trio; não fecha misturas/combinações em todos os modos.
- [x] [CONFIRMADO] `GUN-38` Ghosts: trait `10040` aprovado no trio; não fecha misturas/combinações em todos os modos.
- [ ] [TESTAR] `GUN-41` Dealer: sem trait nesta configuração; validar comportamento básico no modo correspondente.

- [ ] [FAZER] `GUN-SYSTEM-01` Reconstruir capacidade e as combinações/pesos originais de recarga **por arma**; não fixar uma mistura universal.
- [ ] [TESTAR] `GUN-SYSTEM-02` Limite de capacidade em toda adição/troca; HUD genérica com slots extras não aumenta a arma.
- [ ] [PARCIAL] `GUN-SYSTEM-03` Traits não devem começar ativados indevidamente; condições corrigidas, testar a matriz completa de início e recargas.
- [ ] [PARCIAL] `GUN-SYSTEM-04` Recarga e transformação de munição com animação/áudio corretos; detalhes de timing ainda abertos.
- [ ] [TESTAR] `GUN-SYSTEM-05` Combinações com Rocket/Burst/Kit/Wanted/robô/veneno e dano aumentado.
- [ ] [AUDITAR] `GUN-SYSTEM-06` Posse, obtenção, arma padrão, equipar, preview e salvar com conta sem GM.

## Prop / itens

### Efeitos utilizáveis já confirmados

Confirmações abaixo são por **família de efeito no trio local**, não por todas as variantes internas, sorteios, preços e modos.

- [x] [CONFIRMADO] `PROP-2001` Ejector: Ejeta uma munição; recarrega se não sobra real.
- [x] [CONFIRMADO] `PROP-2003` Real Bullet +1: Adiciona uma real respeitando capacidade.
- [x] [CONFIRMADO] `PROP-2004` Blank Bullet +1: Adiciona uma falsa respeitando capacidade.
- [x] [CONFIRMADO] `PROP-2007` Spare Magazine: Recarga em si/bot confirmada; mistura exata e apresentação da recarga continuam pendentes.
- [x] [CONFIRMADO] `PROP-2008` Hallucinogen / Alucinógeno: Permite alvo próprio e bots; força tiro próprio e atualiza munição/recarga.
- [x] [CONFIRMADO] `PROP-2009` Arms Voucher: Transforma real existente em vermelha; não fabrica slot extra.
- [x] [CONFIRMADO] `PROP-2011` Wet Cigarettes: Cura com dado; não ressuscita HP zerado.
- [x] [CONFIRMADO] `PROP-2015` Maintenance Kit: Melhoria de dano e apresentação aprovadas; não confundir com câmera da morte.
- [x] [CONFIRMADO] `PROP-2016` Burst Mode: Dois tiros no outro; tiro em si é único e consome o efeito.
- [x] [CONFIRMADO] `PROP-2018` Violation Ticket: Dado, transferência de chips e animação aprovados.
- [x] [CONFIRMADO] `PROP-2020` Surprise Box: Entrega um item utilizável; aquisição não significa ativação automática.
- [x] [CONFIRMADO] `PROP-2021` Wanted: Marcadores individuais, duração por turnos/ciclo e mira corrigidos; escala por modo fica aberta.
- [x] [CONFIRMADO] `PROP-2022` Purchase Ban: Bloqueio de compra e uso dos bots confirmados; negativa de compra direta também coberta em teste automático.
- [x] [CONFIRMADO] `PROP-2029` Tranquilizer: Uso por bot confirmado pelo jogador.
- [x] [CONFIRMADO] `PROP-2030` Permission Ban: Restrição confirmada pelo jogador.
- [x] [CONFIRMADO] `PROP-2031` Energy Pump: Uso para carga de skill exercitado; não confundir possuir item com já tê-lo usado.
- [x] [CONFIRMADO] `PROP-2032` Rocket Launcher: Falsa consome uma falsa; real consome todas as reais, causa dano igual à quantidade e recarrega.

### Pré-partida, variantes e efeitos ainda abertos

- [ ] [PARCIAL] `PROP-2033` Bucket: proteção exercitada; retirado da compra em partida a pedido do jogador. Fechar seleção pré-partida, consumo, duração individual e consistência efeito/visual.
- [ ] [PARCIAL] `PROP-2034` Piggy Bank: contrato local de acumular/coletar coberto; falta validar equipar antes, bônus inicial, consumo e desaparecer corretamente. Não declarar que toda bolsa congelada era este item.
- [ ] [FAZER] `PROP-2035` Blood Bag: fora da rodada atual de testes do trio; reconstruir disponibilidade e executor no modo correspondente.
- [ ] [AUDITAR] `PROP-VARIANTS-01` IDs 2024–2028 e 2036–2037: variantes internas por configuração/modo, não novos nomes que o jogador tenha de procurar; validar diferenças e executor fora do trio.
- [ ] [FAZER] `PROP-CARDS-01` Swap/Peeking/Shuffle/Draw/Plunder/Cut/Selection Card (2038–2044): regras, alvos e integração com Gunfire Hold'em.
- [ ] [FAZER] `PROP-2038` Swap Card: executor e teste no modo de cartas correspondente.
- [ ] [FAZER] `PROP-2039` Peeking Card: executor, informação visível só a quem tem direito e teste no modo correspondente.
- [ ] [FAZER] `PROP-2040` Shuffle Card: executor e teste no modo correspondente.
- [ ] [FAZER] `PROP-2041` Draw Card: executor e teste no modo correspondente.
- [ ] [FAZER] `PROP-2042` Plunder Card: executor e teste no modo correspondente.
- [ ] [FAZER] `PROP-2043` Cut Card: executor e teste no modo correspondente.
- [ ] [FAZER] `PROP-2044` Selection Card: executor e teste no modo correspondente.
- [ ] [AUDITAR] `PROP-LEGACY-01` X-Ray Goggles, Box of Real/Blank Bullets, Pack of Cigarettes, Stimulant, Cigar, Blockade e Crack the Safe: registros base existem, mas estão desabilitados na biblioteca auditada; confirmar legado/modo antes de implementar.
- [ ] [AUDITAR] `PROP-SPECIAL-01` Demais cartas/passivas de Arcade/Codex/Trial: inventariadas entre os 359 registros do catálogo, não confundir com itens compráveis do trio.
- [ ] [PARCIAL] `PROP-LIBRARY-01` Menu Prop/Card Library e descrições acessíveis; completar posse, desbloqueio, requisitos, custos e persistência de cada família.
- [ ] [TESTAR] `PROP-PREMATCH-01` Selecionar/deselecionar item pré-partida, limite, gasto real, inventário depois e equipamento na intro.
- [ ] [TESTAR] `PROP-PREMATCH-02` Começar sem item pré-partida não deve criar bolsa/cofrinho para todos.
- [ ] [TESTAR] `PROP-HUD-01` Cada buff: nome/descrição no hover, ícone HUD, objeto na mesa, número/ampulheta e remoção sincronizados.
- [ ] [TESTAR] `PROP-RULES-01` Reuso/duplicação, arma cheia, HP0, alvo morto, bloqueios e substituição de inventário; rejeitar antes de debitar.
- [ ] [FAZER] `PROP-ECONOMY-01` Preços/recompensas/limites e pools originais por modo (incluindo escalas 10×/100×/1000×), separados dos ajustes de teste.

## Base

- [ ] [PARCIAL] `BASE-01` Base Lv.50 visível na conta GM; não comprova evolução natural.
- [ ] [AUDITAR] `BASE-02` XP, nível, custos, requisitos e funções/itens desbloqueados por nível.
- [ ] [TESTAR] `BASE-03` Caixa doméstica: obter, iniciar temporizador, abrir, vender, refresh e recompensa temporária; handlers locais existem.
- [ ] [AUDITAR] `BASE-04` Recompensa diária, conversão em chips, limite/intervalo e retorno no próximo dia.
- [ ] [FAZER] `BASE-05` Persistência e relógio do servidor; reabrir/reiniciar não deve duplicar prêmio ou avançar nível indevido.

## Backpack / mochila

- [ ] [PARCIAL] `BAG-01` Lista/posse no inventário local; separar dados GM dos obtidos naturalmente.
- [ ] [TESTAR] `BAG-02` Usar, vender, quantidade, confirmar/cancelar e atualizar saldo imediatamente.
- [ ] [TESTAR] `BAG-03` Caixas e chaves, falta de chave e receber recompensa uma única vez.
- [ ] [AUDITAR] `BAG-04` Síntese/conversão, seleção de materiais, preço e resultado.
- [ ] [TESTAR] `BAG-05` Novos itens, ordenação, filtros, descrição e atualização sem precisar mudar de tela.
- [ ] [FAZER] `BAG-06` Conta nova/reconexão/reinício: nenhum item perdido, fabricado ou duplicado.

## Supply Box

- [ ] [PARCIAL] `BOX-01` Fluxo local implementado; histórico de abertura exercitado. Fechar o conjunto visual completo, não só pacote retornado.
- [ ] [TESTAR] `BOX-02` Lista/equipe/células, novas caixas, extrair para bancada e capacidade.
- [ ] [TESTAR] `BOX-03` Abrir uma: sequência de tiros, qualidade, resultado e coleta; cobertura automática existe.
- [ ] [TESTAR] `BOX-04` Open All e Collect All: resultado completo, animação e impossibilidade de receber/cobrar duas vezes.
- [ ] [TESTAR] `BOX-05` Repetir/reconectar durante abertura; retomar sem trocar resultado ou perder prêmio.
- [ ] [AUDITAR] `BOX-06` Preview e pool/peso/raridade originais, melhorias de caixa e custo por tipo.
- [ ] [TESTAR] `BOX-07` Prêmios de herói/arma/skin/moeda entram na posse e ficam após reiniciar; incluir item já possuído.

## Shop / loja do lobby

Não confundir com a loja de itens **dentro** da partida.

- [ ] [PARCIAL] `SHOP-01` Backend trata produtos conhecidos de Supply Box; outras compras não são fechadas. ACK genérico não prova entrega.
- [ ] [AUDITAR] `SHOP-02` Todas as abas e produtos visíveis: moedas, caixas, heróis, armas, aparências e pacotes conforme versão.
- [ ] [TESTAR] `SHOP-03` Confirmar/cancelar compra, saldo insuficiente, posse, entrega, saldo HUD e limite/recompra.
- [ ] [AUDITAR] `SHOP-04` Gift package, pacote limitado, primeira compra, wishlist e itens temporários.
- [ ] [FAZER] `SHOP-05` Enhance Hero permanente e regra nível OU aquisição; integrar a HERO-03/04.
- [ ] [AUDITAR] `SHOP-06` Botão + de moedas e recharge: decidir simulação local sem cobrança real; não conectar pagamentos por engano.
- [ ] [FAZER] `SHOP-07` Rejeitar produto não suportado explicitamente; nenhuma resposta de sucesso sem transação/entrega.
- [ ] [TESTAR] `SHOP-08` Refresh/compra/prêmio atualizam dinheiro sem exigir próxima compra; versão corrigida precisa regressão fora da partida.

## Challenge / progressão / temporada

### Season / Ranked

- [ ] [PARCIAL] `SEASON-01` Anúncio Season 18, período e Start Season visíveis no print; dados locais de abertura/info existem.
- [ ] [FAZER] `SEASON-02` Calendário coerente, temporada atual, começar/encerrar e transição persistente; não eternizar período histórico.
- [ ] [AUDITAR] `SEASON-03` Bronze I e demais ranks: pontos, limites, vitória/derrota, progresso e requisitos.
- [ ] [FAZER] `SEASON-04` Recompensas dos marcos (print 200/400/600), resgate único e integração com inventário.
- [ ] [FAZER] `SEASON-05` Ranking calculado, recompensa final, settlement e reset/continuidade entre temporadas.
- [ ] [AUDITAR] `SEASON-06` Ranked 100× e outros níveis de entrada; prêmio, saldo, requisitos e matchmaking corretos.

### Challenge / tarefas / passes

- [ ] [AUDITAR] `TASK-01` Challenge: descobrir abas e condições reais; não confundir com Survival Challenge.
- [ ] [AUDITAR] `TASK-02` Tarefas diárias, Rookie/Newbie e atividades: progresso, reset, resgate e notificações.
- [ ] [AUDITAR] `TASK-03` Conquistas, níveis/marcos e integração Steam; catálogo não prova envio/resgate.
- [ ] [AUDITAR] `TASK-04` Sign In/Newbie Sign In, dias consecutivos/perdidos e recompensas.
- [ ] [AUDITAR] `PASS-01` New Player Pass e Battle Pass: XP, nível, trilha grátis/VIP, compra de níveis, recompensa e duração.
- [ ] [AUDITAR] `EVENT-01` Loteria/Slot Machine, atividades e recompensas especiais; confirmar quais estão acessíveis nesta build.
- [ ] [AUDITAR] `EVENT-02` Eventos sazonais e cronograma; separar decoração estática de sistema ativo.

## Clan / Friend / social

### Clan

- [ ] [AUDITAR] `CLAN-01` Lista, busca, criar, nome/avatar/descrição e requisitos/custos.
- [ ] [AUDITAR] `CLAN-02` Pedir entrada, aprovar/recusar, convite e lista de membros.
- [ ] [AUDITAR] `CLAN-03` Cargos/permissões, remover, sair e transferência/dissolução.
- [ ] [AUDITAR] `CLAN-04` Partidas de clã, equipe, regras, recompensa, caixa/rank e Heat Match.
- [ ] [FAZER] `CLAN-05` Estado compartilhado real entre contas, persistência e autorização; não só janelas vazias.

### Friend / chat

- [ ] [AUDITAR] `FRIEND-01` Lista, pesquisar usuário, pedido, aceitar/recusar e remover.
- [ ] [AUDITAR] `FRIEND-02` Online/offline, perfil, convite para equipe/sala e indisponibilidade.
- [ ] [AUDITAR] `FRIEND-03` Chat privado/lista, mensagens rápidas, relatório/bloqueio e contato/vinculação (pode ser legado).
- [ ] [FAZER] `FRIEND-04` Dois usuários reais: pedidos, convites, mensagens e reconexão sem confundir identidades.
- [ ] [AUDITAR] `SOCIAL-01` Interações/presentes/emotes na partida, custo, áudio e recompensas.

## Other / outras opções

Estas quatro opções são **visíveis no print do submenu Other**, não inferidas apenas dos nomes internos.

### Rankinglist

- [ ] [AUDITAR] `OTHER-RANK-01` Abrir, categorias/temporada, posição própria, perfis e prêmio.
- [ ] [FAZER] `OTHER-RANK-02` Dados reais, ordenação/empates, atualização e persistência; depende de SEASON.

### Mail

- [ ] [AUDITAR] `OTHER-MAIL-01` Inbox, abrir/ler, anexo, resgatar, apagar e validade.
- [ ] [FAZER] `OTHER-MAIL-02` Correio por usuário, entrega/resgate único e notificação.

### Gramophone

- [ ] [AUDITAR] `OTHER-MUSIC-01` Lista de músicas, desbloqueio, selecionar, tocar/parar e salvar escolha.
- [ ] [TESTAR] `OTHER-MUSIC-02` Música do lobby não deve vazar/desincronizar na intro e na partida.

### Setting

- [ ] [AUDITAR] `OTHER-SET-01` Idioma de texto e áudio; aplicar, voltar e manter ao reabrir.
- [ ] [AUDITAR] `OTHER-SET-02` Volumes, vídeo/qualidade/resolução e controles presentes nesta build.
- [ ] [AUDITAR] `OTHER-SET-03` Contact Us, links externos, avisos/privacidade; distinguir botão sem serviço original.
- [ ] [TESTAR] `OTHER-SET-04` Sair do jogo, confirmar/cancelar e salvar; não confundir com Exit da partida.

## Lobby / escolha de modos

O print mostra quatro abas: **Main Mode, Casual, Adventure, Custom**. Ainda falta mapear visualmente cada registro para a aba exata. [Todos os 35 registros e seus cfgIds](FEATURE_CATALOG.md#modos-35-registros) estão no catálogo.

**Nomes/tamanhos:** Hunter Game (3 Players) é trio, não prova equipes 3×3. 1×1 tem dois participantes; 2×2 tem quatro. Não apareceu modo de seis participantes na tabela auditada. Se “3×3” significar seis jogadores, acrescentar descoberta e evidência, sem inventar suporte.

### Main Mode

- [ ] [PARCIAL] `MODE-MAIN-01` Ranked/Matchmaking, Switch Mode, Bronze I, recompensas e 100× visíveis; backend local não equivale ao matchmaking/rank original.
- [x] [CONFIRMADO] `MODE-MAIN-02` Partida local de três participantes com loja jogável; confirmação restrita às regras testadas neste laboratório.
- [ ] [FAZER] `MODE-MAIN-03` Hunter Game 2 Players / 1×1 completo: criação, economia, final e efeitos.
- [ ] [FAZER] `MODE-MAIN-04` Hunter Game 2×2: equipes, alvos aliados/inimigos, ordem, vitória da equipe e economia.
- [ ] [AUDITAR] `MODE-MAIN-05` Classic/Ranked e variantes Fate Split: contratos originais, requisitos e comparação com trio local.
- [ ] [AUDITAR] `MODE-MAIN-06` Codex Brawl (3 Players/2×2): cartas, aquisição, efeitos, regras e progressão.
- [ ] [AUDITAR] `MODE-MAIN-07` Gunfire Hold'em (3 Players/2×2): cartas, mãos, informação escondida e interação com tiros.

### Casual / Adventure

- [ ] [AUDITAR] `MODE-CASUAL-01` Solo/Single, Arcade/Fatal Moment, Gamble of Fate e entradas liberadas por nível.
- [ ] [AUDITAR] `MODE-ADV-01` Trek: fases, continuar, loja/props, derrota, vitória e recompensa.
- [ ] [AUDITAR] `MODE-ADV-02` Trial: escolha de cartas, inimigos, loja, bolsas e resultado.
- [ ] [AUDITAR] `MODE-ADV-03` Survival Challenge e guias: confirmar rota acessível e regras separadas do trio.
- [ ] [AUDITAR] `MODE-EVENT-01` Tournament/Heat Match: participação, clã, espectador, apostas e prêmios.

### Custom

- [ ] [AUDITAR] `ROOM-01` Listar/criar/entrar em sala, nome, senha/privacidade e convite.
- [ ] [AUDITAR] `ROOM-02` Configurações, modo, equipe, slots, troca de posição, ready e iniciar.
- [ ] [FAZER] `ROOM-03` Dois ou mais clientes reais, sair/desconectar/reentrar e dono da sala.
- [ ] [AUDITAR] `ROOM-04` Custom Classic/Solo/2×2/Fate Split/Codex/Hold'em; nenhuma opção deve iniciar outro modo silenciosamente.

### Espectador e encerramento

- [ ] [AUDITAR] `OB-01` Lista de partidas, observar, HUD própria, histórico de aposta e resultado.
- [ ] [TESTAR] `OB-02` Morrer e assistir bots até terminar sem congelar; câmera e duração até Loser.
- [ ] [FAZER] `MODE-ECONOMY-01` Escalas 10×/100×/1000× coerentes em custo, Wanted, skills, recompensa e settlement.
- [ ] [FAZER] `MODE-ROUTING-01` Seleção não suportada deve avisar; não marcar modo como pronto se backend o substituiu pelo trio local.

## Dentro da partida

### Entrada e HUD

- [x] [CONFIRMADO] `MATCH-INTRO-01` Duas cenas de introdução em sequência, sem mostrar mesa no meio; aprovadas com dois personagens. [Contrato e instalação](MATCH_INTRO.md).
- [ ] [TESTAR] `MATCH-INTRO-02` Intro dos demais heróis, armas/itens pré-partida e modos/equipes.
- [ ] [TESTAR] `MATCH-EXIT-01` Exit restaurado pelo status nativo; cobertura automática existe, falta confirmar clique/retorno após intro na versão publicada.
- [ ] [PARCIAL] `MATCH-HUD-01` HP, Frenzy, moedas, munição e buffs funcionais no trio; revisar todos os efeitos simultâneos e atualização imediata.
- [ ] [TESTAR] `MATCH-HUD-02` Dados atualizados no evento correto, sem “cooldown de HUD” esperando a próxima jogada.

### Tiro, recompensa, recarga e morte

- [x] [CONFIRMADO] `MATCH-SHOT-01` Real em alvo/si e falsa em alvo; consumo/dano e turno aprovados no trio.
- [x] [CONFIRMADO] `MATCH-SELF-01` Falsa em si permite repetir Shoot/Cancel, com recompensa e Collect Bounty funcionando após ajustes.
- [ ] [TESTAR] `MATCH-BOUNTY-01` Tabela/combo/penalidades nos outros modos, combinações, cancelamento e nenhuma coleta duplicada.
- [x] [CONFIRMADO] `MATCH-FRENZY-01` Regra revisada com acerto real/falsa em inimigo e derrota por HP/Frenzy; partida longa aprovada pelo jogador.
- [ ] [TESTAR] `MATCH-FRENZY-02` Limite inicial 2 e modificadores, HP0 com Frenzy restante, falsa fatal e todos os heróis.
- [x] [CONFIRMADO] `MATCH-RELOAD-01` Recarga automática quando acaba real ou toda munição, inclusive após Ejector/Alucinógeno, aprovada no trio.
- [ ] [PARCIAL] `MATCH-RELOAD-02` Movimento da arma/câmera e ordem de munição→recarga; timing ainda precisa refinamento.
- [ ] [PARCIAL] `MATCH-DEATH-01` Slow motion e morte/choque têm implementação; câmera de terceira pessoa, interrupção da falsa e transição final **não finalizadas**.
- [ ] [TESTAR] `MATCH-TURN-01` Timer, item/skill sem perder vez indevidamente, morte durante sequência, recarga antes da próxima ação e resultado.
- [ ] [TESTAR] `MATCH-FINAL-01` Vitória/derrota, recompensa, XP, histórico e retorno ao lobby persistentes.

### Loja da partida

- [x] [CONFIRMADO] `MATCH-SHOP-01` Comprar/substituir/usar e renovar ofertas no trio; saldo imediato corrigido e confirmado.
- [ ] [TESTAR] `MATCH-SHOP-02` Pool original, renovação após uso/turno, preço e oferta por modo; não só trocar a ordem das mesmas cartas.
- [ ] [TESTAR] `MATCH-SHOP-03` Compra bloqueada, item duplicado não acumulável, saldo insuficiente e limite do inventário sem cobrar na falha.
- [ ] [TESTAR] `MATCH-SHOP-04` Todos os avisos/ícones/modelos corretos, sem imagem branca ou contador artificial.

### Bots

- [x] [CONFIRMADO] `BOT-01` Não só atiram no jogador: usam itens/skills e outras escolhas, exercitados pelo jogador no trio.
- [ ] [TESTAR] `BOT-02` Decisão legal com bloqueios, munição cheia, HP0, proteção, veneno, orçamento e alvos mortos.
- [ ] [PARCIAL] `BOT-03` Sequenciamento das animações separado do estado HUD; revisar combinações skill→Energy Pump→tiro.
- [ ] [FUTURO] `BOT-04` Fácil/médio/difícil configuráveis; decisões leves, probabilidade e testes reprodutíveis.
- [ ] [TESTAR] `BOT-05` IA não pode conhecer ordem oculta das balas sem regra que conceda informação.
- [ ] [FAZER] `BOT-06` Estratégia e suporte a equipes/modos diferentes sem reaproveitar cegamente regras do trio.

## Infraestrutura / distribuição

- [ ] [PARCIAL] `INFRA-01` Backend local e 286 testes no snapshot v63; protocolo reconstruído, não servidor original completo.
- [ ] [TESTAR] `INFRA-02` Persistência/transações por conta, migração e recuperação de arquivo incompleto, sem duplicação.
- [ ] [FAZER] `INFRA-03` Instalador limpo auditado para cliente compatível; clonar Git não instala patches do cliente.
- [ ] [FAZER] `INFRA-04` Multiplayer remoto: autenticação, isolamento, autorização, validação e limites. Manter escopo local até auditoria.
- [ ] [TESTAR] `INFRA-05` Testes de fluxo completo além da unidade: login→menu→partida→resultado→reinício.
- [ ] [TESTAR] `INFRA-06` Validar em outra máquina limpa, com cópia legítima e sem depender de caminhos locais.
- [ ] [TESTAR] `INFRA-07` Auditoria de compartilhamento/CI em cada publicação; sem jogo, saves, credenciais ou dumps de código proprietário.
- [ ] [AUDITAR] `INFRA-08` Telas GM/debug/dev: manter separadas do jogador normal e não dar privilégios públicos.

## Novas descobertas e prioridades

### Ordem sugerida, sem iniciar implementação automaticamente

1. Usar os prints para conferir navegação de todos os menus e listar opções ainda não abertas.
2. Concluir skills Diana/Vera/Hawke e regressões dirigidas do robô; não encerrar heróis por preview.
3. Pré-partida: Bucket/Piggy Bank, seleção real e bolsa fantasma.
4. Armas: misturas originais de recarga e refinamento visual; morte/choque continuam explicitamente pendentes.
5. Conta nova, progressão/Enhance Hero e economia.
6. Expandir modos/contas/sistemas sociais com contratos próprios, sem tratar fallback como suporte.

### Espaços livres para você preencher

Estas linhas são reservas, não tarefas reais e não entram em contagens.

- [ ] `NEW-01` Área/menu: ____ · Função: ____ · Esperado: ____ · Observado: ____ · Evidência: ____
- [ ] `NEW-02` Área/menu: ____ · Função: ____ · Esperado: ____ · Observado: ____ · Evidência: ____
- [ ] `NEW-03` Área/menu: ____ · Função: ____ · Esperado: ____ · Observado: ____ · Evidência: ____
- [ ] `NEW-04` Área/menu: ____ · Função: ____ · Esperado: ____ · Observado: ____ · Evidência: ____
- [ ] `NEW-05` Área/menu: ____ · Função: ____ · Esperado: ____ · Observado: ____ · Evidência: ____
- [ ] `NEW-06` Área/menu: ____ · Função: ____ · Esperado: ____ · Observado: ____ · Evidência: ____

Para uma tarefa maior, copiar [o modelo](templates/FEATURE_TEST.md). Se o jogo mostrar outra arma, herói, aba ou modo, incluir primeiro como **AUDITAR**, com nome/print e cfgId quando identificado.
