# Mr.R / macaco — skill e melhoria (v54, 30/09/2026)

## Evidência nativa

LanguageEnglish2488/2489: transforma2/3 itens aleatórios da loja em Caixas
Surpresa gratuitas. skill_cfg10002/10013 usam buff10014/10038, logic67,
argumentos[36,2/3,0]. Card36 tem variante do trio2036 e skill1038.
Cooldown3, cutscene6 TV_Monkey_skill, Camera01_MonkeySkill, anim47,
skillShowTime3000ms, skillFinishCallBackType1 (Monkey).

Inspeção somente leitura por tools/inspect_monkey_cutscene.py encontrou
Slate.Cutscene Cutscene2 sob TV_Monkey_skill com duração4s. IA espera
cutscene4+UI3+margem1=8s antes da próxima ação.

ClientAnimExpression.UpdateShopItemShow_Skill e OnEndSkillUIShow buscam
Enum_Shop38 e target.cards; callback final executa UpdateShopItems e
ShopMonkey. Portanto pacote Type_Skill3, skillId10002/10013, eventoCD9 e
eventoShop38 com cards no campo42. Não reutilizar refresh83/System11:
isso perderia a animação de personagem e o callback da skill.

## Implementação e limites

- GM com starLevel5 recebe10013 em lobby/PvP sem alteração do save.
- Básica também implementada:2 caixas. Melhorada:3 caixas.
- Escolha aleatória sem reposição, mantendo posições das ofertas.
- Sem custo de chips. Caixas2036 têm preço0, status disponível, IDs novos.
- IDs antigos selecionados deixam de ser ofertas válidas.
- Slots vendidos e caixas2036 já gratuitas não são reconvertidos. Se restam
  menos ofertas elegíveis, converte as restantes. Se nenhuma, rejeita sem
  consumir a skill. Política local conservadora: esses casos limite ainda
  não foram confirmados manualmente no servidor original.
- Escopo humano atual: modo1/sub6 (trio com loja). Não afirmar suporte aos
  outros modos/economias. Bots usam executor compartilhado quando têm essa
  skill; personagens fixos da partida manual não foram trocados.
- Permission Ban e cooldown impedem usar a skill; Purchase Ban continua
  impedindo comprar/abrir ofertas, inclusive gratuitas.
- Ajustado executor de compra/uso para aceitar especificamente2036 preço0;
  preços negativos/zero de outros itens não foram liberados.
- Enhance Hero comprado/progressão conta nova seguem pendentes.

## Testes e status

252 testes locais aprovados (seis novos). Incluem básica/melhorada,
aleatoriedade, slots vendidos/sem elegíveis, IDs únicos, executor bot,
Permission Ban e contrato nativo38/42. TCP real localhost testa login,
cooldown, transformação2/3, abertura de caixa gratuita sem desconto e
status vendido após uso. Visual/câmera/som ainda aguardam jogador.

## Roteiro manual

1. Selecionar Mr.R/macaco; entrar em trio com loja.
2. Carregar skill por turnos ou Energy Pump. Não gastar ofertas antes do
   primeiro teste para ter quatro disponíveis.
3. Usar skill. Deve haver animação dele e três ofertas devem virar Caixas
   Surpresa gratuitas; quarta permanece. Saldo não muda pela skill.
4. Abrir uma caixa: deve entregar item sem cobrar e ficar vendida.
5. Confirmar retorno dos controles/Fire e cooldown, sem congelamento.

Snapshot compartilhável v52 é anterior a essas alterações e permanece intacto.

Validação manual: jogador confirmou100%. Sessão20260930-164922:
17:08:54 skill10013 converted3;17:09:03/18/32 caixas2036 deram2032/2016/2008.
Sem ERROR/Traceback nessa sessão. Etapa aceita pelo jogador.
