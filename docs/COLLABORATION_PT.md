# Trabalhar e compartilhar

## Para o dono do laboratório

Você pode continuar editando no laboratório existente. Antes de publicar,
exporte os arquivos aprovados para este repositório:

```powershell
.\tools\Sync-Lab.ps1 -Direction Export -GameCopyRoot 'CAMINHO DA COPIA'
# Confira a lista; depois:
.\tools\Sync-Lab.ps1 -Direction Export -GameCopyRoot 'CAMINHO DA COPIA' -Execute
.\tools\Test-Project.ps1
git switch -c work/minha-correcao
git add server docs
git diff --cached
git commit -m 'Corrige protecao da Katie'
git push -u origin HEAD
```

Uma branch é uma linha separada de trabalho. Abra um Pull Request para
integrar à main. Quem revisa confere os testes e o que mudou. A main é a
versão compartilhada, não um lugar para misturar alterações sem revisão.

## Para os colaboradores

Clone o mesmo repositório privado. Antes de trabalhar, atualize com
`tools/Update-Project.ps1`. Faça uma branch própria e siga o mesmo fluxo.
Não copie seus saves/logs para o repositório. Para testar no jogo, use uma
cópia compatível e feche jogo/servidor antes de Apply:

```powershell
.\tools\Sync-Lab.ps1 -Direction Apply -GameCopyRoot 'CAMINHO DA COPIA'
.\tools\Sync-Lab.ps1 -Direction Apply -GameCopyRoot 'CAMINHO DA COPIA' -Execute
```

Apply cria backup dos arquivos que substituir; conta e inventário não mudam.
Se ambos os lados modificaram o mesmo arquivo desde a última sincronização,
o script para e exige resolução manual. Não existe sobrescrita silenciosa.
Use `git diff` para conferir e GitHub Desktop para resolver os conflitos.

## O que é automático

- Testes e auditoria de arquivos rodam a cada push/PR após configurar o GitHub.
- `Watch-Export.ps1` pode exportar mudanças locais ao salvar; é opcional,
  roda enquanto a janela estiver aberta e **não publica na nuvem**.
- Push envia sua branch; pull baixa as mudanças da branch atual. O script
  não troca sua branch nem integra branches alheias sem revisão.
- Outras pessoas só recebem sua mudança na main depois da integração e
  de atualizar suas cópias. Nunca atualize código durante uma partida.

## GitHub: primeira publicação

Crie um repositório **privado e vazio**, sem README inicial, com nome
`hunter-roulette-lab` (ou outro escolhido). Autentique via navegador/Git
Credential Manager; não compartilhe senha/token pelo chat.

```powershell
git remote add origin https://github.com/SEU_USUARIO/hunter-roulette-lab.git
git push -u origin main
```

Convide usuários específicos após confirmar os nomes. Nas configurações de
Rulesets/Branches, exija Pull Request e checks `test` antes de integrar,
quando disponível no plano da conta. Não restringimos licenciamento nem
concedemos acesso a pessoas sem a decisão do dono.
