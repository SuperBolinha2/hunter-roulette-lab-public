# Hawke — Julgamento Aéreo / +

IDs: `HERO-HAWKE-01`, `HERO-HAWKE-02`. Melhoria no cenário registrado:
CONFIRMADO; básica e demais casos: PARCIAL.
Data: 2026-10-05; branch `work/hawke-skill`. Hero 38; mode1/sub6, trio com loja.

## Contrato recuperado

Skills 10038/10039, carga 3, skill type14, target type2/quantidade -1 (múltiplos
alvos inimigos). Buffs 10068/10069, lógica 90, argumentos `[500,0,1,2,3]` /
`[500,999,1,2,3]`: descrições confirmam metade das reais, arredondada para baixo
na básica e para cima na melhoria. Câmera `Camera01_EagleSkill`, cutscene29,
prefab `TV_EagleH_skill` (Cutscene2: 3,6667 s), apresentação 4000 ms.

Cliente aplica a retirada via Enum_Eagle_Skill_Reduce_Ammo 86/uAmmo e agrupa
impactos por alvo via Enum_Eagle_Skill_Hit_Enemy 87. O parent contém todos os
alvos para tocar as animações de impacto do drone, não só o primeiro selecionado.
Ao fim da apresentação há uma etapa de 0,5 s para animação dos alvos.

## Execução candidata e limites

- Conta reais amarelas e reforçadas vermelhas; não conta/consome falsas.
- Carrega floor(N/2) ou ceil(N/2). Com 3 reais: básica usa 1, melhoria usa 2.
- Cada munição carregada gera um impacto de 1 dano, em inimigo vivo aleatório.
  Escolha uniforme e retirada ponderada pelas quantidades são decisões do lab;
  não se afirma que a distribuição original foi recuperada.
- Reinicia a carga da skill em 3. Respeita proibição, personagem morto, ausência
  de inimigos e quantidade insuficiente (básica com uma real não pode executar).
- Um alvo derrotado não recebe os próximos impactos. Se todos forem derrotados,
  termina a sequência e a partida, preservando o consumo já carregado no drone.
- Dano consome HP e depois Frenzy excedente como as outras skills. Não concede
  Frenzy ao atirador e não dispara bônus de tiro normal (Diana, Burst, Maintenance).
- Integra interceptação do robô Katie: primeiro impacto é bloqueado/consome o robô,
  próximos podem causar dano. Bucket continua sendo proteção de tiro normal;
  verificar essas interações manualmente antes de declará-las originais.
- Se a melhoria carrega a última real, recarrega a arma automaticamente após o
  drone, mantendo a skill da arma. Essa regra segue a recarga atual do laboratório.
- Execução/cfg3 não existe no estado do trio suportado e não foi implementada aqui.
- Dano das reforçadas no drone segue 1 por impacto da descrição, não o bônus de
  dano do disparo normal; reteste manual necessário para confirmar essa interpretação.

## Roteiro manual

1. Selecionar Hawke (águia), trio com loja. Conferir nível da skill e esperar
   três cargas, ou usar Energy Pump. Não rebaixar o save GM para testar básica.
2. Preferir uma quantidade ímpar, por exemplo 3 reais, com bots vivos e saudáveis.
   Anotar munições, HP e Frenzy de todos antes de ativar a skill.
3. Na melhoria: 3 reais devem virar 1 real; drone aplica 2 impactos no total,
   em um bot ou distribuídos entre ambos. Falsas permanecem iguais.
4. Na básica, os mesmos 3 reais viram 2 e há 1 impacto. Não testar assumindo que
   toda conta tem acesso aos dois níveis sem mudar a progressão.
5. Verificar cutscene do drone, câmera, som, retirada das balas e acertos, com
   HP/Frenzy na HUD acompanhando os impactos. A skill não encerra a vez sozinha.
6. Testar melhoria com 1 real: usa 1 impacto e depois recarrega. Se o drone
   elimina o último oponente, deve finalizar a partida sem travar.

## Testes e pendências

`server/tests/test_hawke.py` cobre quantidades, arredondamento, reforçadas,
alvos aleatórios/vivos, HP/Frenzy, eliminação, eventos nativos, recarga,
desbloqueio sem mutação, bots, bloqueios e preservação de itens de tiro normal.
TCP usa o handler real nos dois níveis; cenário sintético letal verifica fim de
partida. Isso não comprova qualidade visual/audio nem multiplayer/outros modos.

Nenhuma modificação em saves, equipamento ou progresso GM. Publicação final
e checkbox CONFIRMADO ficam para depois da aprovação manual deste escopo.

Verificação: 319 testes passaram no repositório e na cópia isolada (2 testes
exclusivos de ferramentas do repositório são ignorados na cópia). Auditoria de
compartilhamento, fixtures de sincronização e verificação de whitespace passaram.

## Validação manual — 2026-10-05

Jogador aprovou a apresentação (“Ficou bom!”), questionou a seleção e depois
aceitou manter os alvos aleatórios (“aaa ok ok, deixe assim”). O fluxo nativo
`RouletteBattleWindow:IsUseSkillIm` ativa imediatamente quando target type2 e
target_num=-1: não mostra seleção individual. Não foi alterado para uma regra
personalizada de alvo fixo.

Última ativação: skill10039, antes Hawke tinha 4 reais/3 falsas; depois 2 reais/3
falsas. Foram 2 impactos de -1 HP no Bot 1 (4 → 2), sem alterar sua munição ou
Frenzy. Eventos: 9 (carga), 86 (retirada), 87/87 (acertos). O estado publicado
confirma o consumo e dano. Este cenário não valida sozinho arredondamento ímpar,
básica, robô, última real/recarregamento, munição de execução ou outros modos.
