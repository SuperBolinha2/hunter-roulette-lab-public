# Yu / coelha — melhoria da skill (v53, 30/09/2026)

## Fontes locais e regra

Dados nativos copiados, artefato `private-server/config-extract/weapon-skill-audit.json`:
skill_cfg10000/10003, skill_info_cfg10003, LanguageEnglish153/470 e
buff_cfg10033→10034/10035. As faixas do dado são 1–2 falha, 3–5 efeito1,
6 efeito2. Skill básica10000 tem efeito1 inclusive no6.

Upgrade10003 mantém cooldown3, câmeras Camera01, cutscenes4/5,
animações47/46/48/156 e skillShowTime6000ms. Ícone UI_Skill_Rabbit_up.
Não criar efeito visual ou duração diferente da configuração original.

Resolver compartilhado ativa melhoria por starLevel>=5 OU flag permanente
skillUpgradeUnlocked OU skillId melhorada já salva. Não muda inventário,
estrelas, equipamentos, moedas ou perfil GM. Compra/uso de Enhance Hero
ainda não implementados; a flag é contrato do executor, não compra pronta.

Humano e bots usam mesma fórmula após modificador Lucky Streak (+2, máximo6).
Em si cura até limite4; no inimigo usa executor de dano existente, incluindo
Frenzy quando HP não basta. Toxin suprime1 da cura e é consumido como antes.
Bots agora também podem escolher cura própria quando têm espaço para HP.

## Validação local

Suite de regressão: 246 testes aprovados. Seis novos testes cobrem:
- unlock das duas rotas/ID persistido, sem mutar inventário;
- todos os seis dados na básica/melhorada;
- executor bot em si/inimigo, reset de cooldown e barreira nativa;
- cura limitada e Toxin;
- Lucky Streak antes do cálculo do upgrade;
- TCP real localhost: 12 cenários (dados1–6, alvo próprio/inimigo), login10003,
  snapshots HP e rejeição de segundo uso sem recarga de habilidade.

Resultados do dado são fixados somente nos testes automatizados.
O jogo manual continua aleatório. Validação visual ainda pendente.

## Roteiro manual

1. Selecionar Yu/coelha na conta GM e entrar no trio com loja.
2. Ganhar cargas naturalmente por turnos ou usar Energy Pump até liberar skill.
3. Com pelo menos2HP faltando, usar em si. Dado1–2 não cura;3–5 cura1;
   6 cura2. Se falta apenas1HP, cura só1 mesmo com6.
4. Recarregar a skill e usar em bot com pelo menos2HP. Dado1–2 sem dano;
   3–5 dano1;6 dano2. Verificar dado, animação, HUD e cooldown após uso.
5. Para alcançar6 mais rápido, Lucky Streak da Little Maniac pode somar2 ao
   dado: base4→6 também deve dar efeito2. Não precisa trocar arma para teste
   normal; evitar modificadores no primeiro teste facilita comparar resultados.

Não encerrar como visualmente100% até retorno do jogador. Snapshot de
compartilhamento v52 permanece intacto; esta alteração é posterior ao pacote.

Retorno manual: jogador confirmou dado6 em si curando2HP. Log da sessão
20260930-162606, às16:30:54: skill10003 target0 roll6 hpDelta2 virDelta0 cd3.
Sem ERROR/Traceback nessa sessão. Dano2 em inimigos permanece aprovado em
teste automatizado, sem confirmação visual manual do6. Jogador autorizou seguir.
