# Auditoria antes de tornar público

Data:2026-10-07. Somente inspeção e este relatório; visibilidade não alterada,
sem remoção, reescrita de histórico, commit/push ou mudança de código/save.

## Resultado

Não foram detectados padrões de credenciais nas superfícies examinadas, nem
saves reais, dumps completos de Lua, assets/binários do cliente ou logs pessoais
nos arquivos candidatos à publicação e blobs do histórico Git inspecionado.
Isso é evidência de varredura, não garantia absoluta de ausência de segredos,
nem autorização de redistribuição de conteúdo de terceiros.

Recomendação: manter privado até o proprietário decidir os pontos de privacidade
e distribuição abaixo. Não há justificativa observada para rotação emergencial
de tokens, pois não foi encontrado token vazado nesta auditoria.

## Escopo verificado

- Repo GitHub SuperBolinha2/hunter-roulette-lab: privado, main,4 branches remotas;
  pontas comparadas com refs locais. main25b40a0 e heads de PRs estão nos objetos
  auditados. Sem tags/releases, wiki desativada, sem webhooks ou artifacts Actions.
-12 commits alcançáveis por refs locais,130 blobs únicos, mensagens de commit e
  metadados de autoria. Nenhum blob binário ou caminho de save/asset proibido.
-108 arquivos atuais rastreados ou novos não ignorados, incluindo trabalho ainda
  não publicado de Clan/perfil. Guardrail tools/audit_share.py passou sem problemas.
-3 PRs, corpos/comentários/reviews disponíveis e15 runs Actions,30 arquivos de log
  (243528 bytes). Varredura33 documentos, sem matches de padrões fortes de segredo
  ou e-mail no conteúdo dessas superfícies; nenhum log indisponível/truncado.
-Busca suplementar por tokens GitHub/OpenAI/AWS, chave privada, atribuições de
  senha/API key, e-mails, caminhos de usuário Windows, IPs e padrões de IDs Steam.
  Único IP literal nos blobs históricos:127.0.0.1. Hosts de URLs eram referências
  públicas de documentação/Steam/GitHub/Python, não endpoints privados observados.

Itens locais ignorados (saves, traces, backups, fixtures em.local) não fazem parte
do repositório público; a auditoria não autoriza zipar a instalação do jogo nem
publicar pastas externas. Reflogs/objetos órfãos não foram objeto de uma varredura
forense e normalmente não são enviados por push. Não foram examinadas contas,
tokens armazenados no Windows ou recursos inacessíveis fora deste repositório.

## Pontos para decisão antes da mudança

| Prioridade | Achado | Ação proposta, sem execução automática |
| --- | --- | --- |
| Privacidade | Metadados Git contêm nome civil do autor e2 identidades de e-mail reais; não presentes no texto dos arquivos | Proprietário decidir se aceita exposição. Caso queira anonimizar, planejar reescrita coordenada com colaboradores; configurar noreply apenas nos próximos commits não corrige os antigos |
| Revisão de distribuição | tools/patch_match_intro_handoff.py contém nomes de funções e pequenos trechos/âncoras de Lua nativa (não um dump completo), além de código de patch escrito no lab | Revisar o que se pretende distribuir e as permissões aplicáveis; não presumir que ausência de assets resolve toda questão de direitos |
| Licença | Não há LICENSE rastreada nem licença declarada no GitHub | Escolher conscientemente licença para código próprio e esclarecer escopo/exclusão de material de terceiros; não aplicar licença indiscriminadamente a conteúdo que o projeto não possui |
| Segurança operacional | Backend documentado como localhost sem autenticação pública; --host aceita parâmetro, default127.0.0.1 | Publicação do código não é publicação de servidor; manter aviso, não abrir portas/proxy/interface pública sem projeto separado |
| Expectativa dos usuários | Cliente compatível modificado necessário; README não promete preparar Steam limpo. Docs/CURRENT_STATUS.md possui retrato histórico286 testes e pendências já superadas parcialmente | Atualizar apresentação do estado atual antes de chamar novos colaboradores; manter referências históricas com data e sem afirmar suporte total |

Nenhuma evidência de save pessoal, executável, bundle ou arquivo de credencial
exigindo remoção foi identificada nesta inspeção. E-mails dos commits não são
reproduzidos neste documento, para não ampliar sua exposição.

## Próximos passos opcionais

1. Decidir exposição de autoria/e-mails e política de distribuição/licença.
2. Se houver ajustes autorizados, reauditar os diffs e o histórico resultante.
3. Revisar o que será publicado do trabalho ainda não commitado: Clan/perfil
   estão no checkout local, não automaticamente no GitHub.
4. Somente após aprovação explícita, mudar a visibilidade do repositório.

Auditoria documental não altera status de gameplay nem confirma features novas.

## Preparação autorizada pelo proprietário —2026-10-07

Licença AGPL-3.0-only adicionada para código/documentação originais; escopo em
LICENSING.md. Identidade dos próximos commits do checkout configurada como
SuperBolinha2 e noreply GitHub, sem alterar configurações globais.
Backup privado recuperável do histórico criado em.local; espelho sanitizado
de12 commits reescrito nessa pasta privada. Autor/committer pessoal substituídos
no espelho; autoria de merges GitHub preservada. Nenhum force-push realizado.

Histórico do repositório remoto e checkout original ainda não foi reescrito:
PRs/caches podem reter commits antigos, mesmo depois de trocar branches. Publicação
depende da escolha do proprietário: novo repo público sem refs antigas, preservando
atual privado, ou limpar refs/caches do mesmo repo com GitHub antes de torná-lo público.
Colaboradores precisarão reclonar/migrar; backups e clones antigos não são apagados.

Recomendação conservadora: não incluir o helper opcional de patch do cliente no
primeiro pacote público, preservando-o no arquivo privado para revisão separada.
Não há alteração de assets/gameplay implícita nessa decisão. Nenhuma licença nova
concede direitos sobre o jogo original; AGPL permite forks/versões próprias sob
suas obrigações, incluindo uso comercial, sem exigir envio ao repo original.
