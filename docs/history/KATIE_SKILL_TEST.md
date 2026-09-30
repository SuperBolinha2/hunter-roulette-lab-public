# Katie — Musical Barrier v59, 2026-09-30

Fontes nativas: skill10022/10023; melhoria dificuldade2/3 10030/10031;
buffs de controle10030/10032/10048/10050 (lógica25), proteção visível
10029/10031/10047/10049 (lógica48). Recompensas0/2/20/200 conformevariante.
Descrições975–977,1694–1695: próximo tiro inimigo é bloqueado; se intacto
até expirar, melhoria paga. No trio10031/buff10049 rende200chips.

Implementação de laboratório: uso próprio em trio com loja, não equipes.
Buff de proteção visível adicionado diretamente; controle de validade
server separado de Bucket. Dura até próximo turno do proprietário. Próximo
tiro inimigo normal (incluindo falsa) consome, não seu próprio tiro.
Bloqueio anula todo dano do primeiro disparo (amarela/vermelha/Rocket).
Rajada: segundo disparo não fica protegido. Não paga ao interceptar ou
quando derrotado. Não confundir skill10031 com buff10031 básico melhorado.

Type_Skill3/cooldown9/Enum_Buff_Update10 adiciona proteção. Remoção no
evento do tiro, delBuffs, sincronizada com snapshot sem Bucket bool residual.
Expiração usa Type_Behavior17 passivo para não desviar mira, deltaCoin com
razão20 nativa Coin_By_Hold_Off_Buff_Auto_Deal. Charge inicial3/uso3.
TV_CAT_skill/Slate4s, skillShowTime3s, margem1s: barreira8s paraapresentação.
CâmeraCamera01_CatSkill, fonte47/46; alvo0, cutscene8. Cliente játem
efeitos nativos do buff; visual do robô ainda requer jogador.

279 testes locais aprovados: seis novos cobrem resolverdesbloqueio/valores,
interceptaçãoúnica/bypasspróprio/semrecompensa, expiraçãoindividual/defeito,
executorbot, eventospassivos de remoção/recompensa e sessãoTCP ativação/
snapshot/cooldown/rejeição. Bloqueio de dano em partida real e animações
ainda pendentes; não afirmarque somente esses testes provamrenderização.

Pendênciasforaescopo do primeiroteste: equipe/alvoaliado, demaismodos,
interação com FairDuel e outras skills de ataque; robotshot câmera/sons e
timing exato de expiração devem ser confirmados manualmente.

Roteiro: Katie/gata,trio,carregar por turnos/EnergyPump. Ativar e ver
robô/ícone. Passarturno atacandooutro e observarprimeirotiroinimigo: se real,
zeroHP/Frenzy deduzido,robôsai; próximotirodesprotegido. Testerecompensa
intacta exige que ninguématinjaKatie:ao voltar sua vez,robôsai e+200.
Não exigirúltimocaso se bots focarem você; logs distinguemresultado.

## Correção v60 — saída visual do robô

Teste manual v59: Katie ativada18:49:41 e tiroinimigo real interceptado
18:50:01 (sessão183930). HP preservado corretamente, mas robô permaneceu.
Diagnóstico nativo RemoveBuff: somente existTyp3 aciona anim_Pet_Other_Del81;
existTyp2 aciona anim_Pet_Auto_Del82/básico ou132/melhorado. Pacote anterior
omitira existTyp, removendo ícone/estado sem animação de saída do pet.
v60 envia tipo3 no buff destruído pelo tiro e tipo2 na expiração natural,
com sourceIdx do dono preservado. Regressão cobre ambos payloads.
Jogador confirmou saída visual v60. Proteção lógica já confirmada.

## Ajuste v61 — falsas não destroem o robô

Correção histórica acima: jogador esclareceu que tiro falso não deve
destruir o pet naquele instante. Intercept agora recebe cfg da munição:
300 mantém proteção/buff; real1 ou vermelha2 de inimigo consome no impacto.
Sem impacto real, expiração continua no próximo turno do proprietário,
com animação de saída natural e recompensa. Dois testes novos cobrem
falsas consecutivas→expiração e falsa→vermelha→sem recompensa duplicada.
Visual desta diferença ainda aguardando reteste. Não alterar tiro real.

## Correção v62 — Rocket não passa pela proteção

Sessão185958,19:02:14 Bot2 usou2032 emKatie protegida; caminho de itemRPG
era independente dos tirosnormais e ignorava guard. Agora executoresbot
e humano(compra direta/armazenado) consultamguard antesdano. Real/RPG
consomepet e anulaHP/Frenzy doalvo; mantém muniçõesconsumidas/recarga.
Falso preservapet atéexpiração. EnumRpg39 não processaUpdateBuffs: adicionado
EnumBuffUpdate10 separado com existTyp3 paraanim81, sem premiar expiração.
Regressões específicas: botRocket→proteção/saída e resolverhumano real/falso,
consumo/recarga,semHP/Frenzy deduzido. Visual aguardando reteste.

## v63 — Grazier e duelo Arthur

Usuário pediu cobertura Grazier, ainda sem teste manual. Tiro normal já
consulta proteção depois do sorteio/prioridade da vermelha. Lacuna encontrada:
FairDuel não consultava proteção. Executor compartilhado agora recebe o
mesmo guard em humano e bot; falsa mantém, real/vermelha consomepet e
anula danoHP/Frenzy. Duelo acaba ao sair real mesmo se bloqueada, munição
é consumida, sem recompensa por expiração posterior.
Regressão cobre Grazier como iniciador e como oponente no duelo, prioridade
vermelha, HP/Frenzy preservados e existTyp3 para saída do pet.
Sessão190623,19:08:13 confirma expiração Katie com200chips; nenhuma
interceptação Rocket registrada nesse novo teste. Não assumir retesteRocket
manual por aprovação genérica do jogador; Grazier visual pendente também.
