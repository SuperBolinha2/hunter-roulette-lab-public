# Melhorias de personagem — auditoria 30/09/2026

v59: Katie10022/10031 implementada para teste próprio no trio com loja;
279 testes aprovados. Proteção e recompensa independentes do Bucket;
visual/interceptação em partida aguardam aprovação. Ver KATIE_SKILL_TEST.md.

v58: Annie10018 aprovada manualmente em si e bot2. Trace confirma troca
azul→vermelha própria e azul→amarela inimiga sem mudar total de munições.
Ver ANNIE_SKILL_TEST.md. Próxima: Katie10022/10023 (Musical Barrier).

v57: Arthur aprovado nos três duelos v56; Shelby aprovado manualmente nas
duas trocas, -1HP/+500 e -300/+1HP.269 testes locais aprovados.
Ver ARTHUR_DUEL_TEST.md e SHELBY_SKILL_TEST.md para limites ainda pendentes.
Próxima implementação: Annie10017/10018 (Forced Reloading).

v55: macaco confirmado manualmente; Arthur10005/10014 em primeiro teste,
261 testes locais aprovados. Ver ARTHUR_DUEL_TEST.md para câmera/animações
nativas e limites, incluindo espectador pós-morte por duelo ainda pendente.

Atualização v54: urso10004 confirmado manualmente; coelha10003 confirmada em
si com dado6/+2HP (inimigos: testes locais); macaco10002/10013 implementados,
252 testes locais aprovados, validação visual pendente. Ver
RABBIT_UPGRADE_TEST.md e MONKEY_UPGRADE_TEST.md.
As pendências históricas abaixo não significam que esses três executores
continuam ausentes. Compra/ativação1135 e demais melhorias seguem pendentes.

## Fontes e evidências

Inspeção somente leitura dos bundles da cópia, usando
`tools/inspect_hero_upgrade.py` e o decoder existente de `audit_weapon_skills.py`.
Efeitos base/melhorados: `WEAPON_SKILL_RESEARCH.md`, hero_cfg e skill_info_cfg.

- LanguageEnglish 1121 confirma melhoria em 5 estrelas. Isso é starLevel,
  não fightLevel/XP de combate. Não inferir um nível de XP equivalente.
- RouletteHeroInfo.GetSkillID lê GamerHero.skillId retornado pelo servidor.
- Steam Preview mostra botão/lock quando starLevel<5 e bloqueia uso em 5.
- Preview consome 1 item via GamerUseGoods, cmd8/act2. Janela Update apenas
  apresenta o resultado, não executa a melhoria no servidor.
- item_base/Steam: use_result_type1135, itens204000–204009, use_result_value[0]
  identifica o personagem. Item204001 é do urso hero1.
- Loja Steam: Enhance Hero, shop10000010/sub901; preço original300000 da
  moeda102000. Coelha/urso têm actual_price240000; demais300000.
  item_sell15000 é preço de VENDA, não de compra.
- hero_up_cfg Steam mantém progressão por estrelas. hero_badge nível5
  function5 é troca do efeito ativo. Progressão histórica e Steam têm custos
  diferentes; não fundir tabelas indiscriminadamente.
- Inventário atual do laboratório: dez heróis starLevel5 mas skillId básico.
  Consumível1135 não é tratado no servidor: uso atualmente termina em erro396.

## Regra solicitada pelo jogador

Condição autoritativa: starLevel>=5 OU melhoria permanente comprada/ativada.
Primeira condição alcançada desbloqueia uma vez; segunda não duplica nem cobra.
Compra do prop deve manter fluxo nativo: comprar no Enhance Hero e usar1.
Não rebaixar estrelas existentes para possibilitar teste. Não aumentar estrelas
para simular compra: pode conceder benefícios de outros sistemas por acidente.
Cliente Steam presume melhoria=star5; caminho comprado sem alterar estrelas
exige alinhar lock/botão à skillId melhorada, ou verificar se o item original
promovia starLevel. Essa decisão de UI/progressão ainda não foi implementada.
Os dados locais não comprovam a cronologia das mudanças de monetização.

## Efeitos da melhoria e ordem de implementação

| Personagem | Skill básica → melhorada | Diferença |
|---|---|---|
| No.13 / urso |10001→10004|Converte Frenzy em HP preservando o excedente que não pôde curar.|
| Yu / coelha |10000→10003|Dado6 cura/causa2; demais resultados seguem a básica.|
| Mr.R / macaco |10002→10013|Transforma3 ofertas em caixas gratuitas, em vez de2.|
| Arthur |10005→10014|Bala adicionada para Fair Duel é aprimorada.|
| Shelby |10020→10021|Even Trade permitido em Frenzied State.|
| Annie |10017→10018|Conversão em aliado produz bala aprimorada.|
| Katie |10022→10023|Se robô não sofrer ataque durante proteção, expiração rende2 chips.|
| Diana |10032→10033|Dano normal adicional ao Frenzy também reduz seu limite máximo em1.|
| Vera |10035→10036|Roubo prioriza balas de execução/aprimoradas.|
| Hawke |10038→10039|Metade das reais para drone arredondada para cima, em vez debaixo.|

Reusar animações/câmeras/ícones configurados por skillId, sem inventar VFX.
Cada básica deve ser auditada antes da melhoria; algumas ainda não têm executor.

## Etapas e testes necessários

1. Resolver skill efetiva por progresso/compra, sem migração silenciosa do save.
2. Comprar/usar prop: saldo, quantidade, hero snapshot, persistência, duplicação,
   herói não possuído e saldo insuficiente. Seguir preços atuais do cliente.
3. Urso: básica gasta todos os Frenzy; melhorada gasta somente o efetivamente
   convertido. Testar HP0, HP quase cheio, Toxin e limite de HP; decidir consumo
   sob Toxin pelos buffs nativos, não pela fórmula improvisada.
4. Integrar skillId melhorada no lobby, PvP e IA; cooldown inicial separado do
   cooldown após uso. Não habilitar IDs sem executar efeito correspondente.
5. Validar um personagem por vez com jogador. Depois progressão natural por
   partidas/nível: regra histórica de XP exata ainda não recuperada.

Status: pesquisa e planejamento concluídos; compra/ativação e executores
melhorados ainda pendentes. Nenhuma alteração no inventário ou jogo nesta etapa.

## Conta laboratorial: normalização solicitada

Auditoria atual: dez heróis em5 estrelas/fightLevel10, todas42 armas,66skins;
moedas101000=10000000 e102000=7114999. Esses dados facilitam testes mas não
representam progressão normal. PvP começa com10000 fixos no trio com loja,
independentemente do inventário; não confundir moedas de lobby com R-Chips.
Protocolo ainda assume starLevel5 quando campo ausente — default privilegiado.
Usuário solicitou correção; escolha de preservar desbloqueios ou recomeçar
progressão foi perguntada. Não mudar save enquanto escopo não estiver definido.
Próxima implementação deve manter snapshot recuperável e separar perfil de
testes/progressão, evitando rebaixar compras por inferência de origem.
