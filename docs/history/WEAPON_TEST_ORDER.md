# Teste de traits das armas — uma arma por etapa

## 1. Screwdriver — funcionamento confirmado pelo jogador e trace (v34)

Retorno de 29/09: jogador informou bom funcionamento. Trace da sessão
`20260929-211320` confirma cfg2 causando -2 HP e recarga seguinte com
2 falsas + 1 real + 1 aprimorada. Recargas forçadas/itens também têm testes
automatizados; esse trace não contém um teste manual de Spare Magazine.

Use a Screwdriver normal, recomendada para No.13 (urso). O efeito pertence
à arma equipada, não ao personagem. Versões de tutorial sem skill não contam.
Comece uma partida nova para carregar o trait no estado inicial.

1. Ao entrar na partida, capacidade 4 sem bala vermelha automática. Após a
   primeira recarga durante a partida, capacidade 4, incluindo uma bala
   vermelha aprimorada. Ela substitui uma amarela; não adiciona um quinto slot.
   O sorteio atual pode deixar uma vermelha e três falsas, ou uma vermelha,
   uma amarela e duas falsas. Pesos oficiais das misturas seguem pendentes.
2. Atire até consumir a vermelha. Sem Kit, Arms Voucher, Burst ou Bucket,
   ela deve causar 2 de dano, consumindo uma única bala. Reais e falsas
   também podem sair antes dela: priorizar a vermelha é outro trait, Grazier.
3. Quando acabar toda munição real (amarela + vermelha), deve haver recarga
   automática. A nova recarga volta à capacidade 4 e cria uma vermelha.
4. Use Spare Magazine na sua Screwdriver: mesma regra, uma vermelha na nova
   recarga, nunca acumulando vermelhas da recarga anterior. Observe o aviso
   da habilidade da arma na HUD e a animação de recarga.
5. Opcional: repita Spare Magazine no Bot 1 se ele estiver com Screwdriver;
   seu carregador também deve mostrar a conversão.

Informe qual passo falhou e o que apareceu (munição antes/depois, dano,
HUD/animação). Teste sem modificadores de dano para não confundir o resultado.
Depois desse retorno, conferir o trace da sessão antes de avançar.

## 2. Little Maniac — bônus e HUD confirmados; carga inicial corrigida (v37)

Jogador confirmou cigarro e skill. Correção v36 envia atualização nativa do
buff além da recarga. Reteste curto: consuma Lucky Streak, use Spare Magazine,
confira o ícone ainda no seu turno; consuma novamente e repita Spare Magazine.
Nas duas vezes o ícone deve voltar sem aguardar a troca de turno.

Equipe Little Maniac (arma recomendada da coelha Yu) e comece partida nova.
O efeito pertence à arma, não ao personagem. Não confundir com skill ativa
ou com arma de tutorial sem trait.

1. Ao entrar na partida não deve existir Lucky Streak. Após a primeira
   recarga durante a partida, deve existir um ícone Lucky Streak na HUD, perto de
   nome/HP/munição. Passe o mouse para conferir a descrição.
2. Use Cigarros Molhados ou Multa. O dado deve mostrar seu resultado e depois
   +2: 1→3, 2→4, 3→5, 4/5/6→6. O ícone do efeito é consumido.
3. Role outro dado antes de recarregar: não deve receber novo +2.
   Itens comprados/guardados e skill da coelha compartilham o mesmo efeito.
4. Use Spare Magazine na Little Maniac: o ícone deve voltar; o próximo dado
   ganha +2 novamente. Repetir recarga sem usar o efeito não acumula +4/+6.
5. Opcional: use a skill ativa da coelha com Lucky Streak. O efeito da skill
   deve usar o resultado já acrescido do bônus; até um dado original 1 vira 3.

Observe o ícone, resultado original, animação +2 e efeito (cura/dinheiro/skill).
Não precisa testar tudo no mesmo turno. Testes TCP locais confirmam consumo,
recarga, uso comprado/guardado, skill e bots; visual/som aguardam o jogador.

## 3. LoveSong — confirmada pelo jogador em dois testes (v38)

Equipe LoveSong e comece partida nova. Não recebe carga extra ao entrar.
O efeito pertence à arma, não exige usar Katie.

1. Com a skill ainda não pronta, observe as cargas/indicador antes de usar
   Spare Magazine em si. Após recarregar deve ganhar exatamente1 carga,
   ainda no mesmo turno, junto do aviso da arma.
2. Repita em outra recarga: ganha mais1 até ficar pronta. Se já pronta,
   recarregar não deve armazenar usos extras da skill.
3. Use a skill e depois recarregue: volta a ganhar1 normalmente.
4. Opcional: gaste a última munição real para provocar recarga automática;
   o mesmo ganho deve ocorrer. Confira antes da troca de turno, pois o
   ganho normal do novo turno é separado.

Informe cargas antes/depois, aviso e eventual atraso na HUD.

## 4. Artemis — funcionamento e apresentação confirmados (v40)

Equipe Artemis e comece uma partida nova.

1. A entrada não converte balas. A arma tem capacidade6.
2. Use Spare Magazine em si: uma falsa da nova composição vira verdadeira,
   total continua6. Com a mistura3 reais+3 falsas, resultado4 reais+2 falsas;
   com sorteio ativo, outras misturas são possíveis, sempre com conversão1.
3. Confira atualização da munição e aviso da arma, ainda no mesmo turno.
   Deve mostrar a recarga base primeiro e depois1 falsa virando verdadeira.
   No último teste o sorteio foi1 real+5 falsas: deve apresentar isso antes
   da troca para2 reais+4 falsas, não saltar direto ao resultado final.
4. Repita: não acumula conversões de carregadores anteriores. Opcional:
   consuma a última real para conferir o mesmo efeito na recarga automática.

Informe contagens antes/depois e eventual problema de HUD/animação.

## 5. Grazier — confirmada pelo jogador e log (v41)

Equipe Grazier (arma do Arthur), partida nova, capacidade5. Não cria bala
vermelha automaticamente. Evite Kit/Burst/Rocket para isolar o teste.

1. Use Arms Voucher para transformar uma amarela em vermelha. Para testar
   prioridade, mantenha pelo menos1 amarela comum além da vermelha.
2. Atire em um bot: pode sair falsa. Quando sair real, deve consumir a
   vermelha primeiro, causar2 de dano e mostrar aviso da arma.
3. A amarela comum permanece; depois de consumir a vermelha, tiros reais
   comuns voltam a causar1. Não é necessário perder HP atirando em si.
4. Opcional: com amarela+vermelha novamente, Alucinógeno em si também deve
   priorizar vermelha quando sair real. Falsa não consome a vermelha.

Se a recarga tiver apenas1 amarela, adicione Bala Real+1 ou recarregue antes
do Voucher para ter uma amarela comum e uma vermelha simultaneamente.

## 6. Ghosts — confirmada pelo jogador e log (v44)

Equipe Ghosts (arma do Hawke) e comece partida nova. Capacidade7; não há
bala extra na entrada. Evite Rocket/Burst no primeiro teste para isolar.

1. Dispare uma falsa (em si ou em bot): não ganha real ainda.
2. Dispare a segunda falsa, mesmo em turno posterior: deve entrar1 real,
   com animação de adição na HUD e aviso da arma. Real intercalada não zera.
3. Repita duas falsas: entra exatamente1 real novamente.
4. Depois de apenas1 falsa, use Spare Magazine: contador zera. A primeira
   falsa pós-recarga não deve adicionar real; a segunda deve adicionar.
5. Ejector não conta. Opcional: Alucinógeno em você disparando falsa conta
   normalmente. Conte falsas efetivamente disparadas, não só slots removidos.

Reset em recarga adotado conforme lembrança do jogador; ajustável após teste.

## 7. RedSiren — confirmada pelo jogador (v45)

Equipe RedSiren (arma padrão da Pirate Octopus — Annie), partida nova. Sem Burst/Kit/Rocket no teste.

1. Remova falsas com Ejector, até manter apenas reais. Deixe pelo menos2
   amarelas; use Bala Real+1 se precisar, sem disparar a última real antes.
2. Atire num bot com vida suficiente: devem sair2 tiros separados,
   consumir2 balas e causar1 de dano cada. Deve aparecer aviso da arma.
3. Com pelo menos1 falsa no carregador, ataque normal não ganha tiro extra.
4. Com apenas reais, atirar em si continua sendo1 tiro. Se só houver1 real
   disponível, não fabrica a segunda; após esgotar reais, recarrega normalmente.

Informe sequência, dano, munição consumida e aviso. Combinação com Burst é
teste separado; soma adicional atual é provisória até confirmação do jogador.

## 8. Carnivore — confirmada pelo jogador e log (v46)

Equipe Carnivore (Gentle Deer — Shelby), partida nova. Não use Wanted,
Burst ou Kit no primeiro teste; anote saldo imediatamente antes de disparar.

1. Acerte bala real num bot: saldo deve subir2, com apresentação de moedas
   e aviso da arma. Confira logo após tiro, antes de compras/ações dos bots.
2. Bala falsa num bot não dá recompensa; tiro em si também não.
3. Opcional: bala vermelha causando2 de dano continua rendendo apenas2.
4. Opcional: Burst com dois acertos deve render4; um acerto+falso rende2.

Sem multiplicadores de modo nesta etapa; validação das escalas é futura.

## 9. Lady J — confirmada pelo jogador e log (v47)

Equipe Lady J. Sem outros modificadores, use itens para preparar3 reais e3
falsas, se possível; capacidade7, mas teste pode usar carregador parcial.

1. Com reais≥falsas, dispare falsa em si: valor ganho deve ser o dobro da
   tabela normal. Exemplo3 reais/3 falsas:400 vira800, antes de combo.
2. Confira valor em Collect Bounty, aviso da arma e saldo depois de coletar.
3. Com reais<falsas antes do tiro, recompensa normal. Exemplo3/4:300 sem
   combo; consumir a falsa deixa3/3 e só o próximo tiro passa a dobrar.
4. Tiro contra bot não recebe esse bônus. Reais vermelhas contam como reais.

Não precisa reproduzir exatamente3/3: anote composição antes do tiro e
valor recebido. Combo interage com cálculo; informe se parecer diferente.

## 10. Venom Stinger — funcionamento confirmado pelo jogador no trio (v50)

Equipe Venom Stinger, partida nova no modo3 participantes com loja.

1. Acerte real em bot: deve aparecer Toxin na HUD do alvo.
2. Observe cura por cigarro/skill: cura1 vira0 e ícone sai; cura2 vira1.
   Se conseguir outra cura no mesmo turno, deve recuperar normalmente.
3. Para controlar o teste, você pode atirar real em si com Venom Stinger,
   conferir Toxin e usar cigarro até obter sucesso no dado.
4. Sem curar, efeito permanece durante próximo turno do alvo e expira no
   começo da vez seguinte dele. Outros personagens não removem o veneno.

Dado de cura falho não deve consumir Toxin. Não testar HP0 com cigarro,
pois ele já é inútil nessa situação. Informe alvo, cura esperada e HUD.

Confirmação manual em 30/09: jogador informou funcionamento correto após
ajustes v50 de encerramento da fumaça e saldo imediato do refresh. Não
estender essa confirmação a outros modos ou ataques especiais não testados.

## Pendências após as dez armas com trait

- Cobertura da Venom Stinger fora do trio e ataques especiais ainda pendente.
- Lucky Revolver, Lucky Shotgun e Dealer não têm trait na configuração
  auditada; precisam apenas de validação básica nos modos correspondentes.
- Composições originais de recarga e combinações de efeitos permanecem para
  auditoria posterior; não são novas habilidades de armas.

Upgrades de skills ativas dos personagens são outra etapa. Não declarar
uma arma concluída só porque seus IDs, ícones ou textos foram recuperados.
