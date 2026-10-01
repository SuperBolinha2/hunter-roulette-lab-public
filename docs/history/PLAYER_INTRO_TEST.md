# Apresentação dos participantes — 2026-09-30

Status: implementado no servidor local; validação visual pendente. Não publicado.

Validação final desta etapa: 285 testes locais passaram (unittest discover).
Teste Wanted também corrigido: a fila de notificações não pode reciclar um
pacote introdutório indefinidamente nem interpretar sessão TV como evento de tiro.

O cliente possui StartGamerShow/StartGamerShow(data), com os retratos, nomes,
armas e itens dos participantes. O contrato nativo é NotifyPvpStatusGamerHeroInfo
(255/16), pvpInfo no campo 1 e Pvp_Gamer_Hero_Info=15. Não é uma animação nova.

Antes, 3/14 entregava estado de jogo e imediatamente 255/7: a apresentação era
pulada. Agora o carregamento entrega estado 15 e 255/16, aguarda 4 segundos,
envia 255/7 com estado jogável e preserva os 11 segundos de preparação da munição.
OnGameStart_New fecha a apresentação com EndGamerShow. O turno é bloqueado
por toda a sequência de 15 segundos. Quatro segundos são um intervalo experimental
do laboratório, não uma duração original confirmada.

Os atrasos da fila são relativos ao pacote anterior, não ao início da sequência.
O teste de protocolo verifica estado, ordem, três participantes e espera antes
da munição. Os demais testes devem continuar validando o fluxo de partida.

Após o usuário confirmar duas cenas, habilitado StartTvShow/PlayCutScene_GameStart
(255/18) ANTES do painel. Carregamento recebe status 18; 255/11 e 255/18
acionam a cena. Após 8,5s, 255/11 com status 15 limpa o estado TV e 255/16
mostra o painel. Depois 4s vem a munição; após mais 11s vem o turno (23,5s total).
O campo session de 255/18 não é consumido pelo HandlerTvShow.
Inspector read-only inspect_match_intro.py confirmou cutsceneindex=1 no modo 1
e timelines TV_kaichang de 6,4 a 8s: espera é 8s + margem de 0,5s.
Ainda precisa validar visualmente câmera, encerramento e ordem com o usuário.

Teste manual: iniciar partida nova com loja; confirmar apresentação dos três
participantes, transição para preparação/recarga e liberação normal do turno.
Verificar se nome, retrato e arma correspondem aos participantes e se o painel
some antes de jogar. Informar se a intro lembrada era este painel ou a cena 3D.

Backup: research/rollback/20260930-pre-player-intro (server e teste anterior).
Nenhum bundle, save ou arquivo da instalação original foi alterado.

## Correção do intervalo entre cenas

Usuário relatou retorno à mesa antes do painel. Log confirmou Katie (hero 17):
timeline dura 6,4s, mas a espera uniforme era 8,5s (intervalo indevido de 2,1s).
Substituída por duração nativa por personagem menos 0,1s, para o painel cobrir
o retorno da câmera. Katie: painel em 6,3s. Valores para personagens base do
modo 1 foram medidos no bundle; IDs desconhecidos ainda usam fallback 7,9s.
Continuidade visual e margem de 0,1s ainda exigem validação manual.

## Transição pelo callback nativo (substitui o temporizador do painel)

O ajuste por duração não resolveu visualmente. Investigação do GameAssembly
em modo somente leitura confirmou: CutSceneObj.OnCutSceneFinish (RVA BF1050)
restaura câmera via SceneController.SetCameraShow(true) e chama
SceneController.OnCutSceneFinish(-1) (RVA C313A0), que chega ao HandlerAnimEvent
Lua como OnCutSceneFinish. Antes, esse handler só encaminhava para o executor
de skills: não ligava a abertura ao painel de participantes.

Agora 255/16 é pré-carregado imediatamente depois de 255/18. O cliente guarda
o painel enquanto labOpeningCinema estiver ativo. No callback de fim com
índice -1, limpa a flag e abre o painel no mesmo frame; outras cenas de skill
mantêm o encaminhamento anterior. ClearData elimina estado pendente entre
partidas. Não há timer local de painel nem valor fixo por personagem para a
troca visual. O timer do servidor permanece para preparação/turno; sincronizar
essas fases por confirmação explícita do cliente é uma melhoria separada.

Patch: patch_match_intro_handoff.py; preview releu o bundle serializado e
verificou que os outros 839 TextAssets não mudaram. Backup separado em
research/rollback/20260930-native-intro-handoff/lua-before-handoff.ab.
286 testes do servidor passaram. Validação visual ainda pendente.
Usuário confirmou a continuidade da abertura. Detectou botão Exit oculto:
UpdateGameState depende de isStartPvp=true, mas os avisos da intro definiam
false. Adicionado 255/11 com status 2/isStartPvp=true antes de 255/7 para
restaurar a UI nativa, sem forçar visibilidade do botão ou mudar as cenas.
Teste de protocolo verifica saída dos estados 18/15 e restauração desse flag.
Não publicado: exportação compartilhada do patch de cliente exige auditoria
e um instalador portátil; não enviar bundles proprietários ao GitHub.
