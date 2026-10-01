# Modelo — descoberta / teste de função

Copie este modelo para uma nova nota em docs/ ou use seu resumo em FEATURE_CHECKLIST.md.
Não marque esta folha-modelo como se fosse um teste concluído.

## Identificação

- ID estável da tarefa: AREA-XX
- Estado: AUDITAR / FAZER / PARCIAL / TESTAR / CONFIRMADO / FUTURO
- Caminho no jogo: Login → Lobby → menu → submenu
- Nome que aparece no cliente:
- Origem: print / referência UI-xxx / tabela e cfgId / descrição / log
- Versão/data:
- Responsável / Issue / PR, se houver:

## O que a função deve fazer

Descrever a regra, efeito e limites. Separar lembrança do jogador, descrição nativa,
inferência e decisão do laboratório. Não tratar inferência como regra recuperada.

## Passos para testar

1. Preparação: personagem, skill básica/melhorada, arma, itens, conta e modo/submodo.
2. Estado antes: HP, Frenzy, munição, saldo, duração, inventário, progressão.
3. Ação:
4. Resultado esperado:
5. Resultado observado:
6. Esperar término da animação e próxima vez; confirmar estado final.
7. Se aplicável, sair/reabrir/reiniciar para conferir persistência.

## Checks específicos — preencher conforme função

- [ ] Regra/efeito corretos
- [ ] Alvo próprio / aliado / inimigo válido
- [ ] Custo, saldo e quantidade corretos
- [ ] Limites: cheio / vazio / morto / bloqueado / saldo insuficiente
- [ ] HUD imediatamente correta
- [ ] Animação / câmera / efeitos / som corretos
- [ ] Duração e remoção independentes por alvo
- [ ] Repetição, falha e cancelamento sem cobrar/duplicar
- [ ] Persistência / próximo turno / reconexão corretos
- [ ] Testes automáticos relevantes
- [ ] Teste manual aprovado no escopo registrado

Use “não se aplica” para verificações sem sentido; não inventar passos para preencher todas.

## Evidência e fechamento

- Evidência resumida: evento/resultado sem dados pessoais, segredo ou dump do cliente.
- Arquivo/teste automatizado:
- Relato do jogador:
- O que está concluído:
- O que continua parcial:
- Outros modos/combinações ainda não testados:

Atualizar a linha da checklist principal. Em bug ativo, uma Issue pode guardar discussão,
mas não deve virar outra lista completa concorrente.
