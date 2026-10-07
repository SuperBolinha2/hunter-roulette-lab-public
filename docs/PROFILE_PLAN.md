# Perfil — pesquisa e plano de implementação

Data: 2026-10-05. Plano solicitado pelo jogador; nenhuma mudança de gameplay,
saldo, nome, cosméticos ou passe foi aplicada nesta etapa.
A checklist canônica continua em [FEATURE_CHECKLIST.md](FEATURE_CHECKLIST.md).

## Evidência e limites

Pesquisa direta na cópia isolada: HallPlayerInfoWindow, OtherPlayerInfoWindow,
HallPlayerInfoCom, Gamer, UManagerModel, RouletteFriendData, RoulettePassData,
descritores protobuf e configurações nativas. Somente conclusões derivadas aqui;
não publicar dumps, assets ou dados privados.

O backend atual tem identidade mínima de login com nome fixo `Local Hunter`,
ícone/moldura padrão, inventário GM compartilhado e respostas mínimas de login.
O login não fornece ainda acessórios, registros de renomeação e Battle Pass
completos. Listar opções ou receber ACK não prova que salvam, são possuídas ou
aparecem corretamente no perfil de outra conta. Não confundir handlers de skins
e seleção de arma existentes com edição da vitrine pessoal.

## Mapa funcional

| Área | Conteúdo e requisitos a implementar | Checklist |
| --- | --- | --- |
| Identidade | ID estável, nome exibido separado do login, rename, contador grátis e cooldown | PROFILE-01/02/05 |
| Avatar/moldura | Catálogo, posse, bloqueado/desbloqueado, seleção, prazo, fallback e efeitos visuais | PROFILE-02 |
| País | Bandeira opcional, seleção e cooldown; independente de idioma e servidor | PROFILE-06 |
| Vitrine | Herói, arma, skins de ambos, honor/adereço, toys/interação e cartões | PROFILE-03/07 |
| Coleções | Heróis, armas, skins, avatar, molduras, toys e poker realmente adquiridos | PROFILE-02/08 |
| Dados públicos | Perfil próprio/alheio, clã, nível, favoritos, estado, patentes e recordes | PROFILE-03/09 |
| Estatísticas | Temporada/carreira, vitórias, sequência, taxa e totais, por modo suportado | PROFILE-05/09 |
| Histórico | Resultado, participantes, loadout e detalhes; replay precisa compatibilidade própria | PROFILE-04 |
| Passe | Battle Pass e New Player Pass separados, XP, níveis, grátis/VIP, prazos e resgate | PASS-01/02/03/04 |
| Temporada ranked | Rank/cup/MMR, calendário, reset e prêmio; não é Battle Pass | SEASON-01 e demais SEASON |

## Regras recuperadas, não inventadas

- Renomear: configuração Steam indica 1 oportunidade grátis inicial, depois
  10 unidades do item103000 (diamantes), cooldown86400s/24h. A conta GM não deve
  ganhar nova oportunidade a cada login. Migrar contador existente quando houver;
  definir migração explícita se nunca houve esse registro.
- HallPlayerInfoWindow bloqueia comprimento calculado por `getStringLength` acima
  de12. Comentário antigo fala14: seguir código executado, mas investigar a
  contagem Unicode do helper antes de impor uma medida incompatível no servidor.
  Rejeitar vazio/controle/markup no servidor; auditar duplicidade e erros nativos.
- País:195 entradas em country_cfg_steam; change_nation_cd604800s/7dias.
  País ausente é representado por0. Não inferir localização por IP nem coletar
  telefone para escolher a bandeira.
- player_head_pic contém117 entradas:51 tipo1/avatar e66 tipo2/moldura. Inclui
  ocultos e efeitos; não significa117 opções desbloqueadas. ACCESSORY contém
  id/typ/limitTime; prazo0 e prazo limitado precisam de semântica confirmada.
- business_card_cfg_steam contém51 registros, com condições/conquistas. Não são
  todos títulos equipáveis nem automaticamente possuídos. Auditar também
  visiting_card, cartões de poker e limite real de slots antes de implementação.
- Battle Pass Steam contém9 configurações históricas e558 linhas de recompensa.
  Configurações recuperadas de passe tipo1 usam Base2 e battle_exp[250,150,50].
  Resolver qual resultado corresponde a cada índice antes de conceder XP.
  New Player Pass usa fluxo de atividades separado; não reutilizar cegamente as
  regras do Battle Pass. Os preços/entitlements VIP precisam de decisão local;
  não simular pagamento Steam nem conceder acesso pago por ACK.
- Estado BattlePassInfo inclui id, curLevel, curFreeGetLevel, curPayGetLevel,
  isPay, exp, starTime, endTime, passType e vipStatus. Trilha e posse VIP são
  distintas. Datas históricas precisam acompanhar o relógio coerente do lab,
  sem criar eventos fictícios pela data real do computador.

## Contratos nativos que orientam a implementação

- Rename: GamerSetNameC2S(gid,name,index), resposta com `cousume` (grafia nativa)
  e modifyNameTime; cliente atualiza nome, saldo e lastModifyNameTime.
- Avatar/moldura da tela atual: GamerSetAccessoryC2S(gid,id); tipo recuperado
  do catálogo determina icon ou iFrame. Há APIs legadas separadas no UManagerModel:
  não assumir que ambos os caminhos são usados pela tela de Hunter Roulette.
- Vitrine: GamerSetFavoriteHeroC2S(gid,heroId,gun,honor,toys,busCard[],heroSkinId,
  gunSkinId). Isso é apresentação do perfil, não autorização para trocar o
  equipamento de combate selecionado.
- País: GamerCountryChangeC2S(gid,country), resposta gid/country/changeTime.
- Perfil próprio/alheio: RouletteFriendData.ReqGetGamerDataInfo usa
  GamerDataInfoC2S(gid,fids), retorna GamerInfoData. Não confundir com o endpoint
  GamerGetGamerInfo que retorna GamerDetail: são estruturas diferentes.
- GamerInfoData inclui identidade, favoritos, estatísticas, país, vitrine,
  collection, busCardPoker e clanTeamInfo. Preencher apenas valores reais.
- Passes: login battlePass e NotifyGamerBattlePassUpdate, resgate
  GamerFinishBattlePass e compra de níveis GamerBattlePassBuyLevel. Resolver
  números cmd/act no enum nativo e registrar trace sanitizado antes de codificar.

## Ordem proposta — etapas pequenas e testáveis

1. **Fundação do perfil e leitura própria.** Criar modelo versionado por conta,
   ID estável separado de apelido; backup/migração não destrutiva preservando
   heróis/equipamentos GM. Mesma fonte de identidade em login/perfil/clã/lobby.
   Abrir/fechar/relogin/reiniciar servidor não deve mudar dados. Não é ainda
   autenticação pública; continuar localhost.
2. **Nome.** Aplicar oportunidade grátis, custo, Unicode e cooldown. Atualizar
   imediatamente lobby/perfil/clã; impedir cobrança dupla e rollback parcial.
3. **Avatar e moldura.** Catálogo e posse separados da seleção; equipar somente
   desbloqueado e válido, validar prazo e restaurar padrão ao expirar. Confirmar
   imagem/efeito em lobby, perfil próprio/alheio e interfaces de partida.
4. **País.** Seleção, confirmação e persistência do cooldown7dias; manter
   idioma/conexão inalterados. País não altera regras/economia da partida.
5. **Vitrine e coleções.** Validar posse e compatibilidade de skins, salvar
   favoritos/cartões, preview e cancelamento. Não trocar loadout de combate
   incidentalmente. Separar adquirido/descoberto/equipado/expirado.
6. **Perfil de outros e integrações.** Dois usuários locais com nomes/cosméticos
   distintos; clã, friend, ranking e equipe devem usar a mesma identidade.
   Não devolver o perfil GM para qualquer ID desconhecido; não expor inventário
   privado, credenciais, telefone ou sessão.
7. **Estatísticas e histórico.** Registrar resultados uma única vez, ID da partida,
   modo, vencedores, abandonos e economia. Projetar estatísticas reais separadas
   dos dados GM, não deduzir recordes a partir do saldo existente. Replay é etapa
   posterior, não requisito para listar resultados reais.
8. **Battle Pass/New Player Pass.** Primeiro leitura e calendário; depois XP de
   resultados elegíveis; depois resgate grátis idempotente e inventário; somente
   então definir VIP/compra de níveis local. Não misturar rank e XP do passe.

Proposta de módulos futuros: profile.py para identidade/posse/vitrine,
profile_protocol.py para projeções se necessário; progression/pass separados.
Extrair somente handlers envolvidos, sem refatoração ampla de server.py.

## Critérios antes de marcar cada etapa confirmada

- Testes unitários: IDs inexistentes, posse, prazo, duplicidade, limites Unicode,
  cooldown, custo insuficiente, repetição de requisição e falha de gravação.
- Integração: protobuf real, resposta/notify/login coerentes, reinício, duas
  contas diferentes e migração preservando inventário GM.
- Teste manual: antes/depois, saldo quando há custo, efeito visual, reabrir janela,
  relogin e leitura por outra conta. Aprovação só no escopo realmente observado.
- Não gastar diamantes, renomear a conta ou conceder VIP durante pesquisa.
  Nova conta zerada será criada em etapa própria, conforme decisão do jogador.

## Pontos ainda abertos para auditoria

Contagem Unicode nativa; exclusividade/moderação de nomes; slots de cartões;
origem de desbloqueio e expiração de cada cosmético; coleção versus posse;
campos legados desativados; números de comandos; status de passe no perfil e
eventual outro passe exibido; fórmulas de estatísticas; mapeamento de XP por
resultado; VIP/loja local e datas; projeções para amigo/ranking/partida.
Screenshots de todas as subabas ajudam a verificar acessibilidade nesta build;
catálogo e Lua não provam que todas estão disponíveis na interface atual.

## Primeira implementação —2026-10-05

A pedido explícito do jogador, os51 avatares e66 molduras são liberados de forma
permanente apenas para sua conta GM local. `profileLab.accounts` armazena nome,
seleção e posse por chave de conta. `tools/grant_gm_accessories.py` faz a liberação
offline com backup privado, sem gastar saldo ou alterar heróis/equipamentos.
Não é padrão para contas novas. Todos os IDs catalogados foram incluídos;
moldura1019 é `isHide=1` no cliente e pode continuar ausente da tela sem alteração
dos assets, que não foi solicitada.

Login1/1 e1/2 usam identidade/seleção persistidas; login2/3 envia acessórios no
campo24 com prazo0 permanente. Equipar2/5 valida ID e posse, salva atomicamente,
sincroniza o avatar do membro do clã e envia NotifyGamerAccessory253/29. Detalhe
próprio2/9 inclui a coleção de avatares/molduras e os modelos atualmente equipados.
Campos de vitrine própria ainda não são independentes do loadout. Perfil de
outros usuários conhecidos retorna indisponibilidade nesta etapa; ID desconhecido
retorna erro544, não a conta GM. A implementação existente de login continua
localhost sem autenticação pública; chave de perfil não é uma credencial segura.

ID público ainda transitório, estatísticas naturais, cosméticos de partida,
broadcast de clã/friend/ranking, rename/country/showcase e passes ficam pendentes.
Renomear2/2, vitrine2/6 e país2/12 agora recusam explicitamente, evitando ACK falso.
Um perfil novo normal recebe avatar1/moldura1001; auditar defaults naturais antes
de fechar o onboarding. Contador de rename inicial é armazenado, não gasto ainda.

Roteiro manual: abrir perfil, escolher um avatar e uma moldura (preferencialmente
também uma com efeito), confirmar, voltar ao lobby, reabrir perfil e depois relogar.
Seleção deve persistir; nome, saldo, personagens, equipamentos e clã devem permanecer.
Testes automatizados cobrem tipos/IDs/posse, concessão isolada, preservação do save,
rollback, versão inválida e fluxo TCP login→seleção→notify→detalhe.

Validação:336 testes aprovados, auditoria108 arquivos sem problemas, fixtures de
sincronização aprovadas. Liberação GM aplicada offline com backup privado; apenas
código aprovado sincronizado na cópia do jogo. Interface/efeitos/relogin continuam
em TESTAR até retorno do jogador.

Reteste2026-10-05: jogador encontrou todos bloqueados. Trace real2/3 solicitou
gid1000002 e recebeu apenas2 acessórios; conta ativa do caminho SDK é `nil`,
enquanto a concessão anterior estava no placeholder `local`. Correção: mover
concessão explícita para a chave realmente observada, restaurando nome exibido
Local Hunter, sem normalizar/renomear chave de login e sem alterar vínculo do clã.
Teste TCP passa a reproduzir placeholder local + conta ativa nil. liberação visual
continua pendente; login de teste deve transmitir117 acessórios para conta ativa.

## Renomear —2026-10-05

Aviso “Clan feature not available yet” no screenshot era erro757 da trava temporária
do rename, não falha do clã. Comando2/2 agora executa a troca real: primeira grátis,
depois10 diamantes103000, cooldown24h. Resposta contém saldo absoluto em `cousume`
e modifyNameTime; notify253/28 atualiza contador grátis;253/70 atualiza membro do
clã. Chave interna nil e vínculo do clã não mudam. Nenhum nome real foi escolhido
automaticamente pelo assistente.

Contagem nativa confirmada em GlobalFunc.getStringLength: UTF8 com1/2bytes vale1,
com3/4bytes vale2, limite12. Validar vazio, espaços nas extremidades, controle,
markup, Unicode inválido e duplicidade casefold/NFKC com erros nativos531/283/518/256.
Nome inalterado retorna511 sem cobrança; cooldown513 e diamantes insuficientes410.
Não há filtro de palavras do serviço original; política de moderação pendente.

Prazo usa marca privada de tempo real, projetada ao relógio histórico do lab no
login, para não reiniciar24h cada vez que o servidor reinicia. Falha de gravação
restaura nome, saldo, contador e clã juntos. Fonte de identidade em friend/ranking/
partida e isolamento completo da economia permanecem pendentes.
Testar “SuperBolinha”, primeira grátis; confirmar lobby/perfil/clã e relogin,
contador agora pago e nova alteração bloqueada por24h. Cobrança após24h testada
com relógio sintético, não gastar/resetar cooldown GM para conseguir reteste.
