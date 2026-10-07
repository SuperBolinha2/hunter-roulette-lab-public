# Clan — pesquisa, fundação e teste

Data: 2026-10-05; branch `work/clan-foundation`. IDs `CLAN-01` a `CLAN-05`.
Bucket e Piggy Bank adiados a pedido do jogador, sem alterar suas regras.
Estado: fundação TESTAR; membros/eventos/recompensas ainda incompletos.

## Fontes e o que existia

As [notas oficiais v616.603.0](https://steamcommunity.com/app/3591550/announcements/)
anunciaram criação/entrada em clãs e atividades exclusivas; Heat Match semanal
com molduras de avatar míticas, diamantes e outras recompensas. Isso não prova
os requisitos de cada prêmio. A apresentação de facções na página da loja não
deve ser confundida com este sistema de clãs de jogadores.

Pesquisa local read-only: ClanData, ClanCreateWindow, ClanMainWindow, schemas
client/gamer e tabelas Steam do cliente. Não compartilhar Lua nem assets.
`guildInfo` é o tutorial legado, não o Clan; dados de clã pertencem ao login
campos32/33 (`ClanTeam`/`GamerClanTeam`). Comando lógico47, notificações253/70–74.

## Requisitos recuperados

| Regra | Configuração nativa |
| --- | --- |
| Desbloqueio | Base nível7 |
| Criação | 500.000 R-Chips (item102000) |
| Edição de nome/ícone/descrição | 50.000 R-Chips |
| Membros | máximo6 |
| Nome / descrição | máximo16 / 30 caracteres |
| Edição | intervalo86.400s (24h) |
| Após saída/dissolução | espera7.200s (2h) |
| Transferência automática de líder inativo |604.800s (7dias) |
| Pedidos pendentes / validade | máximo50 / 7dias |
| Histórico | máximo50 operações |
| Intervalo de pedido de entrada |5s |
| Atualização de membros |10s |

Ícones de clã básicos desbloqueados: 1,2,3,4,5,8,9; 6 e7 têm requisitos próprios.
Não exigir diamantes nem dar gratuidade GM: custo recuperado é R-Chips.
Validação do lab usa Unicode normalizado, proíbe markup/controles, conta pontos
de código (peso exato de todos os idiomas no original ainda não comprovado).
Primeira edição é permitida; espera24h aplica entre edições. LastEdit inicial
zero é uma escolha local ainda não confirmada contra o backend original.

## Funções recuperadas e situação

| Área | Comando47/ação | Nesta etapa |
| --- | --- | --- |
| Lista, buscaID |1,2 | Implementados, lista paginada até100 |
| Criar |4 | Implementado, custa uma vez, nome único |
| Básico/detalhe, membros |5,6,8 | Dados reais do clã, sem bots/membros fictícios |
| Nome sugerido |7 | Sugestão local simples, não algoritmo original |
| Configuração, editar |14,15 | Só líder, saldo atualizado e persistência |
| Pedir entrada / rápido |3,16 | Próxima etapa; explicitamente indisponíveis |
| Transferir / remover / sair / dissolver |9–12 | Próxima etapa, não executados |
| Aprovar/recusar |13 | Próxima etapa |
| Resgatar caixa |17 | Rejeitado: sem ciclo/recompensa ganha implementada |
| Chat, equipe de partidas, Heat Match | contratos próprios | Não implementados |

Papéis recuperados nesta estrutura: líder e membro. Não inventar cargos adicionais.
Quando criar, o dono é o primeiro membro e o líder. Nome, descrição e ícone
constam do clã, do perfil de clã do jogador e das notificações de atualização.

## Recompensas: pesquisa, não concessão

- Caixas de clã combinam nível coletivo e nível pessoal de contribuição.
- `clan_box_level_steam`: 5 linhas, valores `up_score`15000,25000,35000,50000,50000.
- `clan_box_level_person_steam`: 11 linhas, `up_score`200,600,1200,2000,3000,4200,
  5600,7200,9000,11000,11000. Valores repetidos terminais não são prêmios extras.
- `clan_box_reward_steam`: 55 combinações (5×11); IDs0 e séries19100001–19500010.
  ID0 corresponde a nenhuma recompensa. Quantidades/conteúdo dos pacotes ainda
  precisam de resolução; não inventar loot a partir apenas desses IDs.
- Item701448 é **apenas exibição**, explicitamente marcado no cliente como
  proibido de conceder. Não deve entrar no inventário como prêmio real.
- Há16 períodos históricos de caixas/ranking e16 eventos Heat Match. Fases:
  prévia, jogo, divulgação, apuração de rank e fim. Datas não devem ser trocadas
  por eventos ativos fictícios sem um calendário coerente e regras de pontuação.
- Configuração prevê1000 pontos de calor por jogador, consumo100 por partida,
  duração máxima600s. Essas constantes não significam que o modo já funciona.
- Ranking de Heat Match e de caixa são estruturas diferentes; exigem apuração
  coletiva, contribuições pessoais, elegibilidade e registro de resgate único.

Nesta fundação a contribuição é zero, não há ciclo premiado anterior e não se
concede loot. A estrutura de ciclo atual serve apenas ao painel de progresso,
com janela local de7dias desde a criação; calendário/recompensas oficiais vêm depois.

## Persistência e segurança

Dados privados em `inventory.json → clanLab`, jamais no Git. Mudanças são feitas
sob lock e gravadas junto com o saldo; falha de gravação restaura estado em memória.
Campos de heróis, equipamentos e progresso GM são preservados.
Membros usam chave de nome de conta estável; gids transitórios são recalculados
para exibição em cada sessão, evitando pertencimento a conta errada após reiniciar.

O backend existente continua **localhost, sem autenticação pública**. Permissões
de domínio não tornam seguros os gids fornecidos pelo cliente. Não expor na internet.
Inventário/economia são compartilhados no protótipo; isolamento por conta e
broadcast de mudanças a todos os membros conectados ainda precisam de projeto.

## Roteiro manual — primeira etapa

1. Abrir Clan no lobby e verificar lista/criação. Anotar o saldo de R-Chips.
2. Criar **um** clã com nome até16 caracteres e descrição até30; escolher ícone
   básico. A ação custa **500.000 R-Chips**; não repetir criação como teste de UI.
3. Verificar nome/ícone/descrição, ID, você como líder e um membro no total.
   Conferir saldo reduzido exatamente500.000 e atualização imediata do painel.
4. Fechar e reabrir a janela. Depois sair/reabrir o jogo: clã deve continuar e
   não deve cobrar novamente. Persistência após reiniciar servidor é teste separado.
5. Lista e busca por ID devem devolver o mesmo clã. Se editar, há custo extra
   de50.000 e intervalo24h: testar só se desejar essa alteração.
6. Não testar resgate como recompensa pronta. Entrada/saída/dissolução estão
   indisponíveis nesta primeira etapa, sem sucesso falso.

Testes: criação/custo, duplicidade, nome/ícone/base, persistência com IDs alterados,
lista/detalhes/membros, permissões, edição/cooldown, falha de disco/rollback,
recusa de recompensas não ganhas e fluxo TCP de criação/notificação/login.
Automação não comprova layout, nome renderizado ou botões no cliente.

Validação em 2026-10-05: suíte completa com330 testes aprovados, auditoria de
compartilhamento sem problemas e sincronização na cópia isolada. Teste visual
de criação/nome/saldo ainda pendente de confirmação pelo usuário.
