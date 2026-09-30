# Arthur — Fair Duel básico/melhorado (v55, 30/09/2026)

## Evidências e apresentação adicional solicitada pelo jogador

Descrição nativa LanguageEnglish411/468: Arthur adiciona uma real (básica)
ou aprimorada (melhoria), começa o duelo e os dois alternam tiros de skill
até sair uma real. Skill10005/10014→buff10013/10039→logic31 args1/2.
Cooldown3; skill_typ10, canSelect_Die0, alvo inimigo.

Cutscene7 chama TV_Bull_skill (Slate.Cutscene4s). Configuração esconde
cadeiras de ambos, mostra arma da fonte; ambos os participantes são ligados
à cena, não simular dois tiros normais na mesa. Câmeras Camera02_Right e
Camera02_Left. Ícone básicoUI_Skill_Bull, melhoradoUI_Skill_Bull_up.

Lua nativa: UseSkill→OnCutSceneFinish→StartUseSkill→UseSkill_Cowboy.
Esse último prepara fonte com SkillPre_Bull85 e alvo com ReadyShoot;
Enum_Fix_Ammo_Befor_Duel52 vai para fila BeforeShoot; Enum_Shoot2 vai
para filas ShootEvent_Cowboy e PlayerAnimEvent. WaitForNextShoot consome
um evento alternado por callback; Shoot_Cowboy_Target69 é distinto do
tiro normal. UpdateEvent_BeforeShoot aplica a bala adicional na HUD.

Clips nativos de Arthur/urso encontrados em fight_playeranimation.ab:
SH/BH_AttackStart_ForBullSkill chamam WaitForNextShoot aos0,833s;
há RealHit_ForBullSkill e KillByOther_ForBullSkill próprios. O último
chama OnShootOver0,933s e UpdateSkillUIInfo0,967s. Portanto há preparação,
troca de tiro, impacto e morte específicos, além da câmera/cena de4s.
As poses/cena lado a lado foram confirmadas historicamente pelo jogador;
validação visual desta implementação ainda pendente.

## Implementação

- hero14 em5 estrelas ou flag permanente resolve10014 sem alterar save.
- fair_duel.py executa a mesma sequência para humanos/bots e gera um único
  Type_Skill3 com skillId e pequenos eventos9/52/2 (e recarga1 se preciso).
- Arthur começa; falsa alterna participante, real1/aprimorada2 termina.
- Consome munição do dono de cada tiro; dano1/2 usa HP e overflow emFrenzy.
- Bala extra da skill pode ultrapassar temporariamente capacidade normal:
  trata-se de Enum52 nativo, não item comprado de adicionar munição.
- Não aplica recompensa/frenzy nem Burst/Manutenção de tiro normal aos
  tiros da skill. Interações desses buffs com duelo original precisam
  confirmação separada; política local conservadora atual.
- Recarrega sobrevivente sem reais no fim; se adversário totalmente vazio
  ao chegar sua vez de duelo, recarrega antes. Caso extremo de recarga
  durante o duelo precisa verificação visual (callback nativo usa fila própria).
- Barreira estimada4s de cena+margem1+2,5s/tiro+3s/recarga; não atraso artificial
  de HUD. Valores pós-cena exigem ajuste visual do jogador.
- Eliminação e resultado em fim de partida têm notificações; se humano
  morre com dois bots vivos, recebe derrota e ações próprias são bloqueadas,
  mas automação dos bots em espectador após essa skill ainda não conectada
  ao agendador de turnos existente. Não marcar essa transição como concluída.
- Veneno/Wanted/Bucket e outras armas durante tiros de duelo ainda não
  auditados como combinações especiais. Não afirmar100% fora teste básico.

## Testes

261 testes passaram, incluindo nove novos: unlock básico/melhorado sem
mutação de inventário; extraamarela/vermelha; dano1/2; alternância falsa,
falsa,real; possibilidade do alvo vencer; recarga automática; overflow e
derrota sóHP+Frenzy0; bloqueio de alvo próprio; executor bot e manutenção
dos modificadores não usados. TCP real: login10014, três tiros0→1/1→0/0→1,
snapshotsHP, cooldown3 e rejeição durante a barreira.

## Primeiro teste manual

Selecionar Arthur/touro; trio com loja; carregar skill por turnos/Energy Pump.
Usar em bot com HP alto, você também com HP alto, sem buffs especiais.
Conferir abertura da cena lado a lado, primeira bala extra vermelha na
melhoria, alternância se sair falsa, consumo da munição de cada participante,
fim ao sair real, dano1/amarela ou2/vermelha e retorno ao jogo/cooldown.
Se o primeiro tiro for real, duelo termina imediatamente; alternância exige
uma falsa antes. Não forçar dado/munição na partida real para produzir isso.

Snapshot compartilhável v52 permanece intacto; não contém este módulo.

## Correção v56 — prioridade exclusiva da Grazier no duelo

Jogador confirmou problema na sessão20260930-172530,17:36:04: fonte0/gun7
atirou falsa, alvo2 falsa, fonte0 amarela; causou1HP e preservou vermelha.
Diagnóstico: callback draw era chamado sem gun_id, então ignorava prioridade.

Resolver agora passa o resultado pela função compartilhada
prioritize_shot_ammo usando a arma do atirador atual (não só quem iniciou).
Família Grazier7/18/31: se saiu amarela e existe vermelha, dispara/consome
vermelha e causa2. Falsas mantidas; sem vermelha, amarela normal. Outras
armas não recebem prioridade. Ejector e demais remoções não mudam.

264 testes aprovados: regressões da família/exclusividade, consumo correto,
falsa/falsa/real→vermelha, ausência de vermelha e prioridade quando o alvo
é quem dispara com Grazier. TCP também força sorteio amarela após duas
falsas e confirma evento cfg2 e dano2.

## Validação manual v56 — 2026-09-30

Jogador confirmou três usos, incluindo alternância de falsas e prioridade
da vermelha. Sessão server-session-20260930-174053.err.log:
17:43:54 e 17:44:27: primeiro tiro cfg2, dano2 no alvo2;
17:47:05: fonte0 falsa300, alvo1 falsa300, fonte0 vermelha2.
Último duelo terminou com ambos os bots derrotados. Nenhum ERROR/Traceback
encontrado nessa auditoria. Suite local:264 testes aprovados.
Fluxo básico do Arthur aprovado manualmente; combinações especiais e
espectador descritos acima continuam pendentes, não cobertos por esta aprovação.

Próxima etapa: Shelby/cervo, skill10020/10021. Cliente nativo oferece duas
escolhas (Effect_One/Effect_Two): vida/Frenzy por dinheiro e dinheiro por HP.
UpdateSkill_Deer impede gastar o último ponto total de HP+Frenzy; a melhoria
permite comprar HP quando o alvo está com HP0. Em trio a configuração
de dificuldade usa500 ganhos/300 custo, não os5/3 da configuração básica.
Implementação e validação dessa próxima skill ainda pendentes.
