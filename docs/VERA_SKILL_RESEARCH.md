# Vera — preparação da próxima skill

IDs: `HERO-VERA-01`, `HERO-VERA-02`. Melhoria com roubo de reforçada: CONFIRMADO;
básica e demais casos: PARCIAL. Data: 2026-10-05. Hero 36, aranha.

## Evidência nativa

Descrições portuguesas 104068–104071: **Fio Sombrio da aranha / +**.
A básica rouba uma Bala Real/Reforçada/de execução da arma do alvo e a carrega
na própria arma. A melhoria dá prioridade à bala de execução e à reforçada.

Metadados: básica 10035, melhoria 10036; carga 2, skill type 13;
buffs 10055/10058, lógica 83/84, argumentos `[2]` / `[3,2,1]`.
Animação de origem 46 e do alvo 206; câmeras `Camera01_SpiderSkill` /
`Camera02_SpiderSkill`, apresentação 4000 ms, sem cutscene separado.
Cliente exige atualizar a munição de origem **e** alvo; remover só do alvo ou
atualizar uma HUD não representa a skill completa.

## Próxima implementação / validação

- Recuperar formato nativo do evento type 13 e critério de escolha da básica;
  não assumir que a básica já tem a prioridade da melhoria.
- Conferir capacidade da arma de origem, alvo sem munição elegível e seleção
  de alvo. Confirmar regra nativa de recarga quando a última real é roubada.
- Transferir exatamente uma munição sem duplicar, preservar seu tipo e manter
  estados e HUDs sincronizados com a animação.
- Integrar bots e desbloqueio da melhoria sem alterar progresso GM.
- Testes automáticos para os dois níveis, limites e estado antes/depois;
  só depois abrir roteiro de teste manual da Vera.

## Implementação candidata e decisões locais

- Básica escolhe aleatoriamente entre todas as reais/reforçadas disponíveis,
  ponderando pela quantidade. O enum recuperado confirma aleatoriedade, mas não
  prova o peso da distribuição original; esta distribuição é uma decisão do lab.
- Melhoria prioriza reforçada (cfg2), depois real (cfg1), preservando o tipo roubado.
  O estado atual não emite munição de execução (cfg3): esta parte permanece pendente.
- O executor rejeita alvo próprio, morto, sem real/reforçada, skill sem carga ou
  proibida, e arma da Vera sem espaço. Bloquear arma cheia protege a capacidade;
  precisa de confirmação manual/nativa, não foi recuperado como regra original.
- Retirada usa Enum_Pop_Ammo 13 no alvo; entrada usa Enum_Spider_Skill_Add_Ammo 77
  na Vera, separados para os callbacks próprios do cliente. Só depois é publicada
  a recarga do alvo se perdeu sua última munição real, seguindo a regra atual do lab.
- Recarga mantém a skill da arma, sem duplicar munição transferida. Atualiza os
  dois estados; não apenas a HUD do alvo. A skill volta a exigir duas cargas.
- Ativação só habilitada em mode1/sub6, sem alterar save/progresso/equipamentos GM.

## Roteiro de teste manual

1. Selecionar Vera (aranha), trio com loja. Esperar duas cargas ou usar Energy Pump.
2. Deixar pelo menos um espaço na própria arma (atirar ou usar Ejector).
3. Anotar munições da Vera e de um bot com real/reforçada; ativar nele.
4. Esperado: bot perde exatamente uma, Vera ganha a mesma munição. Na melhoria,
   se o bot tem vermelha, ela deve ser roubada antes da amarela. Nenhum HP perdido.
5. Conferir animação da teia, retirada/entrada, câmera e ambas as HUDs.
6. Se era a última real do alvo, esperar a recarga automática dele após a retirada;
   a munição roubada permanece na Vera. Testar novamente com o outro bot.
7. Arma própria cheia deve rejeitar sem consumir carga nem retirar munição do alvo.

Testes em `server/tests/test_vera.py`: escolha básica/prioridade, desbloqueio sem
mutação, conservação de munição e tipo, índices e tipos de callbacks, recarga,
rejeições sem mutação e fluxo TCP nos dois níveis. Testes não provam qualidade visual.

Verificação desta etapa: 307 testes passaram no repositório e na cópia isolada
(na cópia, 2 testes exclusivos de ferramentas do repositório são ignorados).
Auditoria de compartilhamento e testes de sincronização aprovados. Nenhuma
alteração em inventário/progresso do jogador. Validação manual ainda pendente.

## Aprovação manual — 2026-10-05

Jogador: “funcinou! proxima etapa, confere no log, e nao esquece da mandar la po git”.
Registro da última ativação: `skill=10036`, alvo Bot 1, `stolen_cfg=2`, sem recarga.
Snapshot anterior: Vera 3 falsas/1 real; Bot 1 2 falsas/1 real/1 reforçada.
Posterior: Vera 3 falsas/1 real/1 reforçada; Bot 1 2 falsas/1 real.
Eventos nativos recebidos: `9` (carga), `13` (retirada), `77` (entrada).
Confirmação limitada a este cenário da melhoria. Os demais casos permanecem
pendentes; descrições e testes não encerram suporte a munição de execução.
