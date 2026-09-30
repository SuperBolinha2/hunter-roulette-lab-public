# Annie — Forced Reloading v58, 2026-09-30

Config nativo10017/buff10022 lógica44 args1,1;10018/buff10023 lógica45
args1,1,0,2. Básica troca1 falsa300 por real1; melhoria própria por
aprimorada2, inimigo por real1. Capacidade/total invariantes; sem falsa,
pedido rejeitado sem gastar carga. Nenhuma recarga ou trait de recarga
aplicada à simples substituição. Carregamento inicial3 e após uso3.

Type_Skill3 com cooldown9 e Enum_Ammo_Replace8: CAmmo campo11
source300x1→target1/2x1, rAmmo campo5 lista completa pós-troca. Snapshot
de gun e contadores servidor também atualizados, inclusive vermelhas.
RouletteGamePlayer trata Enum8 com CAmmo como substituição animada.
Config: câmeraCamera01, fonte47/46; alvo86, próprio melhorado87;
isTargetAnimLater1, isNeedUpdateTargetAmmo1, skillShowTime6000ms.
Barreira6s+1 margem, sem atraso artificial no envio daHUD.

Resolver de desbloqueio hero16 básico10017/melhorado10018 porstar5 ouflag
permanente. Não modifica save, moedas ou itens. IA usa a mesma regra em
si própria. Uso em aliado descrito pela config nativa, mas integração em
equipes ainda pendente; laboratório atual tem somente adversários.

273 testes locais aprovados:4 novos, com dois fluxosTCP de alvo próprio
e inimigo, saldo de munição/total/verm./amarela/evento nativo e cooldown;
regra pura cobre aliado, básica/melhoria, limite/ausência de falsa e
executorbot. Não afirmar validação visual nem equipe nesta etapa.

Teste manual: Annie/polvo, trio com loja. Ter pelo menos1 falsa, carregar
skill por turnos ouEnergyPump. Usar em si: uma azul transforma em vermelha,
sem adicionar slot. Recarregar skill, usar em bot com falsa: uma azul vira
amarela. Verificar animação e atualização daHUD antes da próxima jogada.

## Aprovação manual e auditoria da sessão v58

Jogador relata funcionamento. Sessão20260930-182443, 18:28:46 próprio:
antes4falsas/1real, depois3falsas/1real/1vermelha (total5 preservado).
18:30:57 alvo2: antes4falsas/2reais, depois3falsas/3reais (total6 preservado).
Trace255/2 confirma paresCAmmo300→2 e300→1, skill10018 e cooldown3.
Nenhum ERROR/Traceback nem rejeição da skill encontrado nesta auditoria.
Fluxos próprio/inimigo aprovados; equipe e combinações especiais pendentes.
