# Diana — Hunting Art: contrato e teste

IDs: `HERO-DIANA-01`, `HERO-DIANA-02`. Melhoria com tiro real: **CONFIRMADO**;
básica e casos visuais específicos: **PARCIAL**, sem aprovação manual completa.
Nome em português: **Técnica de Caça / Técnica de Caça+**; efeito: **Foco de Caça**.
Data: 2026-10-04. Branch local: `work/diana-skill`.
Escopo implementado: partida local de três participantes com loja, `mode=1/sub=6`.

## Evidência nativa e execução

Metadados de `skill_cfg_steam` e `buff_cfg_steam`, enums do cliente e descrições
recuperadas: Diana/hero 35, básica 10032, melhoria 10033, buffs 10051/10052.
Lógica 65 (`Shoot_Del_Vir_Hp`), argumentos `[1,0]` / `[1,1]`; gatilho 29
(`By_Gun_Shoot_Other_Not_Hold`): tiro normal em outro jogador após dano calculado.
O ícone é `UI_Fight_bufficon_lionskill`; animação própria 47, câmera `Camera01`,
sem cutscene separado, apresentação de 4,5 s e margem local de recuperação de 1 s.

- Ativa em si e permanece durante a vez atual. Falsa em si que mantém a vez
  não remove o buff; troca de jogador remove por evento nativo, não por cronômetro.
- Cada tiro normal real/vermelho que causa dano em outro jogador também retira
  1 Frenzy atual na básica. Na melhoria, retira até 2 pontos atuais e 1 capacidade
  máxima, conforme esclarecimento do jogador: consome 1 ponto e remove outro junto
  de seu slot. Tudo limitado a zero; com apenas 1 ponto disponível, retira apenas 1.
- Rajada aplica a regra por impacto. Falsa, tiro em si ou bloqueio que deixa
  dano zero não ativam a regra. Rocket/Alucinógeno/duelo não são tiros normais.
- A redução da capacidade é mantida no estado durante a partida; não se reverte
  ao remover o buff da Diana. O cliente recebe delta no campo 19 do outline;
  campo 23 do jogador guarda a capacidade absoluta. Não confundir os dois.
- Carga inicial/recarga da skill: 3. A melhoria segue o desbloqueio existente
  (estrela 5 ou desbloqueio explícito), sem modificar progresso/inventário GM.
- Bots podem ativar a skill com munição real e adversário com Frenzy, respeitando
  carga, proibição de skill, alvo próprio e buff já ativo. Sem prever a próxima bala.

## Roteiro manual

1. Escolher Diana (leoa), partida de três participantes com loja. Esperar carregar
   a skill (ou usar Energy Pump). Conferir nome/descrição do nível equipado.
2. Anotar HP e caveiras **preenchidas e vazias** de um bot; preferir bot com pelo
   menos 1 Frenzy preenchido. Ativar a skill: conferir animação e ícone na própria HUD.
3. Dar um tiro normal no bot. Se sair real, o dano habitual permanece e o bot perde
   até 1 Frenzy adicional na básica, ou até 2 na melhoria. Esta remove 1 espaço máximo,
   inclusive se o espaço estiver vazio. Se sair falsa, não há esse efeito adicional.
4. Conferir que o ícone próprio some quando a vez passa e que a redução do limite
   do bot permanece nas jogadas seguintes. Não contar redução de limite como HP perdido.
5. Em outra ativação, uma falsa em si mantém a vez e o buff, sem reduzir seu limite.
   Rajada em oponente deve aplicar o efeito por tiro real; Bucket/robô que bloqueia
   dano não devem deixar passar o efeito adicional.
6. Registrar animação, câmera, som, ícone, HP, Frenzy e limite antes/depois. O nível
   básico precisa de validação separada; não rebaixar o save GM para consegui-la.

## Evidência automatizada e pendências

`server/tests/test_diana.py`: desbloqueio sem mutação, limites zero, real/vermelha,
rajada, falsa/próprio/bloqueado, efeito antes da eliminação, snapshot que preserva
demais campos, delta nativo por impacto, bots e rejeições, ativação/TCP nos dois
níveis, falsa em si conservando buff e remoção na troca de vez.

Teste automatizado não confirma a apresentação do cliente. Sem confirmação manual
por enquanto; multiplayer, outros modos e aquisição natural continuam fora do escopo.

Verificação anterior: `tools/Test-Project.ps1` passou com **300 testes**, auditoria de
compartilhamento sem problemas e fixtures de sincronização aprovadas. Destes,
12 testes pertencem à Diana, incluindo os dois níveis no fluxo TCP real do servidor.

### Correção após primeiro teste do jogador

O log da primeira implementação registrou `2/2 → 1/1` com tiro real e melhoria.
O jogador esclareceu que espera `2/2 → 0/1`: dois pontos perdidos, um slot removido.
Esta interpretação foi solicitada explicitamente; não é prova de execução original
recuperada só pelas descrições. Corrigida a regra de pontos sem alterar a básica,
gatilho, duração ou dano de HP. Novo teste cobre o exemplo e deltas `HP=-1`,
`Frenzy=-2`, `limite=-1`. Reteste manual da correção ainda pendente.
Após a correção: **301 testes passaram**, incluindo 13 da Diana; auditoria de
compartilhamento e testes de sincronização também aprovados.

### Reteste manual aprovado — 2026-10-05

Jogador: “Foi, da uma verificada ai, e bora para a proxima etapa”. Conferência da
última sessão: ativou `10033/10052`, depois atingiu o Bot 1 com munição real.
Antes: HP 4, Frenzy 2/2. Depois: HP 3, Frenzy 0/1. Log de efeito registra
`frenzy_delta=-2`, `cap_delta=-1`, `cap=1`; o snapshot publicado confirma o estado.
Confirmação restrita à melhoria neste cenário local. Não estende aprovação à básica,
rajada, bloqueios, multiplayer ou detalhes individuais de som/câmera.

Nota de infraestrutura: os dois testes de política de compartilhamento rodam no
repositório; na cópia de runtime são ignorados porque `tools.audit_share` não faz
parte do servidor sincronizado. Testes de gameplay continuam obrigatórios.
