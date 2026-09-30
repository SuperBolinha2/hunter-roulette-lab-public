# Shelby — Even Trade, v57 (2026-09-30)

Implementação restrita à cópia. Conta GM, inventário e snapshot compartilhado
v52 preservados. Skill de lobby10020/10021; no trio com loja, IDs nativos
de dificuldade3:10026/10027. Config/buff fornecem500chips por1HP/Frenzy ou
300chips por1HP. Variantes básicas5/3 e dificuldade2 50/30 também cobertas
pela regra pura, mas outros modos não foram validados em partida.

Fonte: skill_cfg/buff_cfg e Lua atual do bundle; UpdateSkill_Deer no cliente.
Pedido GamerPvpGamerUseHeroSkillC2S usa tIdx1, effect3 (não act2).
Effect_One1 gasta HP primeiro; HP0 gasta Frenzy. Deve restar pelo menos1
ponto no total, como bloqueio nativo. Effect_Two2 requer saldo e espaço deHP;
básica não restaura emHP0, melhoria permite se jogador ainda vivo.
HP máximo4 do laboratório. Toxin anula regeneração pelo executor existente,
sem devolver o custo. Sem alvo inimigo no trio; modo equipes/aliados pendente.

Eventos: Type_Skill3, cooldown9, Enum_View_Exchange_Hp_Or_Coin48 com
buffEffect47 e ChangeCoin razões18/19; HP/Frenzy em Enum61 alvo, uma única
aplicação de cada delta. Câmera nativa Camera01_DeerSkill, animações47/157.
Carga inicial3 preservada; após uso2. Barreira6s nativos+1s margem; HUD
recebe evento imediatamente, sem atraso artificial. Timing visual pendente.

IA usa mesma regra: prioriza cura se ferida e com saldo; troca HP excedente
quando sem dinheiro. Escolha incluída na revalidação para bloquear efeito
forjado. Não usa conhecimento de munição secreta.

269 testes locais aprovados:5 novos, incluindo duas sessões TCP para ambos
efeitos, snapshotHP/saldo, IDs, cooldown, rejeição e payload visual; regra
de Frenzy/limites/HP0, desbloqueio sem mutação e executorbot. Esses testes
não confirmam efeitos visuais/sons nem partida de equipe.

Teste manual: selecionar Shelby/cervo, trio com loja. Carregar skill por
turnos ou Energy Pump. Usar opçãoHP→chips: -1HP,+500 imediatamente no saldo.
Recarregar skill e usar chips→HP estando ferido: -300,+1HP. Observar escolha,
câmera, animações e volta à jogada. Se possível, melhoria comHP0 e Frenzy>0:
comprarHP deve recuperar1. Não é obrigatório produzirHP0 no primeiro teste.

## Aprovação manual

Jogador aprovou a apresentação e funcionamento. Log da sessão
server-session-20260930-180320.err.log confirma18:07:27 efeito1: -1HP,+500;
18:10:56 efeito2: +1HP,-300. Ambos skill10027, alvo próprio, cooldown2.
Nenhum ERROR/Traceback encontrado nesta auditoria. Fluxos básicos aprovados;
HP0 melhorado, equipes e combinações especiais não confirmados manualmente.
Próxima skill na ordem: Annie/polvo, Forced Reloading10017/10018.
