# Contributions

## Checklist before and after a change

Read the relevant section of the [feature checklist](docs/FEATURE_CHECKLIST.md)
before changing game behavior. In the same commit/PR, update its stable task IDs,
tested scope, status and remaining checks. Mark CONFIRMADO only after recorded
manual approval; automated tests alone normally leave the feature in TESTAR.
Docs/tooling-only changes may state that feature status is unchanged.

AI assistants: follow [AGENTS.md](AGENTS.md). If your tool does not load that
file automatically, include it in the prompt/context. These instructions and the
pull request template are reminders, not an automatic guarantee of compliance.

- Português: antes de mexer, consulte a área na checklist; depois atualize o estado e a evidência. Só dê check no que foi validado.
- Русский: перед изменением найдите нужный пункт; после обновите состояние и результаты проверки. Отмечайте завершение только в проверенном объёме.
- Français : consultez la fonction avant de modifier le code, puis actualisez son état et les preuves. Ne cochez que le périmètre validé.
- Español: consulta la función antes de cambiar el código y después actualiza su estado y las pruebas. Marca solo lo validado.

## Development workflow

1. Keep the original client read-only; work on an isolated compatible copy.
2. Pull on a clean tree; create `work/<short-topic>` for each change.
3. Change only the intended modules. Do not refactor the entire protocol or
   move server handlers while an unrelated gameplay fix is under validation.
4. Add regression tests and run `tools/Test-Project.ps1` before committing.
5. Record authoritative state, native-contract evidence and manual validation
   separately. Automated checks do not establish visual correctness.
6. Submit a pull request with expected/actual behavior, mode, hero/weapon/item
   cfg IDs and test results. Never attach raw login/packet traces or GM saves.
7. Resolve overlapping edits explicitly; never force-push the shared main.

Module boundaries: protocol.py encodes protobuf envelopes; server.py handles
sessions and authoritative state; bot_ai.py chooses actions; bot_actions.py
executes them; bot_presentation.py separates animation barriers from cooldowns;
weapon_skills.py/hero_skills.py contain shared rules; fair_duel.py,
hero_shop.py and katie_guard.py implement focused mechanics.

Future refactoring should move one handler/mechanic at a time with tests, not
split server.py by arbitrary line counts. Collaborators should agree ownership
of a module in an issue before simultaneous large edits.
