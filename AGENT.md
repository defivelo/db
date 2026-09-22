# DEFIVELO-292 — Weblate source language FR (repo cleanup)

Ticket: https://track.liip.ch/issue/DEFIVELO-292

Weblate had the `intranet` component's **source language set to English**, while the
code's source language is **French** (`LANGUAGE_CODE = "fr"`, `LANGUAGES = (fr, de)`).
Because Weblate's source-language field is read-only after creation, the component must
be **recreated with French as source language**. Before that can happen, the repository
had to be cleaned so that no project string is written in English anymore.

This branch performs **only that repository cleanup** (ticket step 1). Recreating the
Weblate component (step 2) is a separate, manual operation and is **not** done here.

## Repository layout

`locale/` is a **git submodule** → `git@gitlab.liip.ch:swing/defivelo/intranet-i18n.git`
(the Weblate-managed i18n repo). Every `.po` change lives in the submodule; the parent
repo only records the submodule pointer.

- Parent feature branch: `feature/DEFIVELO-292`
- Submodule feature branch: `DEFIVELO-292`

## What we did (3 logical steps, one commit each per repo)

The 47 real overrides in the old `locale/fr/` catalogue (`msgstr != msgid`, all with
project references) were the exact work-list. Deleting `locale/fr/` without acting first
would have reverted these 47 strings to their English (or `Publié`) `msgid` on the
French site.

1. **46 English `msgid`s → French source** (parent `5d3196bd`, submodule `db39044`)
   - Rewrote the English source strings to French in 18 source files: the allauth
     override templates (`defivelo/templates/account/**`), `header.html`,
     `apps/article/models.py`, `apps/common/__init__.py`, `defivelo/settings/base.py`,
     `apps/email_outbox/**`, `apps/user/templates/auth/user_form.html`.
   - In `locale/de`, renamed the matching `msgid`s English → French while **keeping the
     existing German `msgstr`**. This is required because Django merges catalogues by
     `msgid`: once the `msgid` is French, django-allauth's built-in German catalogue no
     longer matches, so the German translation must live in our `locale/de`.

2. **`Publié` → `Ouvert`** (parent `14cee1f2`, submodule `707e49d`)
   - `apps/article/forms.py` label `_("Publié")` → `_("Ouvert")` (the site already showed
     "Ouvert" via a FR→FR override). `locale/de` `msgid` `Publié` → `Ouvert`, German kept
     as `Veröffentlicht`.

3. **Remove `locale/fr/`** (parent `43399fa8`, submodule `cbd8334`)
   - French is the source language, so no French catalogue is needed.

### Deliberate decisions / edge cases

- `Emails` had a wrong French override (`Ajouter E-mail`) that **collided** with
  `Add E-mail` but had a **different** German (`E-Mails` vs `E-Mail hinzufügen`). We gave
  `Emails` the correct French **`E-mails`** (matching its German), fixing the bug and
  removing the duplicate-`msgid` conflict.
- Clean merges (identical German), now single entries in `locale/de`:
  `Password Reset E-mail` = `Password Reset` → `Réinitialisation du mot de passe`;
  `Please Confirm Your E-mail Address` = `Confirm E-mail Address` →
  `Confirmer l'adresse e-mail`. Also `Title`→`Titre` and `Confirm`→`Confirmer` unified
  with pre-existing identical-German entries from `apps/challenge`.
- Two old `fr` overrides without any project reference (`Users`,
  `type some text in this autocomplete`) were third-party/stale and left untouched — they
  disappear with the `locale/fr/` removal.

### Validation

`locale/de/LC_MESSAGES/django.po` passes `msgfmt --check-format`, has no duplicate
`msgid`s, and the multiline email `blocktrans` bodies (narrow-no-break-space `U+202F`,
no-break-space `U+00A0`) were verified byte-identical to the extracted French keys.

> **Not run yet:** `just translate` (Docker was down). The `#:` line references in
> `locale/de` are therefore slightly stale for renamed entries — see below.

## How to rebase / merge upstream into this feature

Because of the submodule, do the **submodule first**, then the parent.

1. **Submodule** — bring `DEFIVELO-292` up to date with upstream:
   ```sh
   cd locale
   git fetch origin
   git rebase origin/master        # (or: git merge origin/master)
   # resolve any .po conflicts, keeping our French msgids + German msgstr
   git push
   cd ..
   ```

2. **Parent** — rebase onto the target branch (`staging`, else `main`):
   ```sh
   git fetch origin
   git rebase origin/staging feature/DEFIVELO-292
   # if the submodule pointer conflicts, take our tip:
   #   git -C locale checkout DEFIVELO-292 && git add locale
   ```

3. **Regenerate catalogues** (this is the `just translate` we could not run). It refreshes
   `#:` references, extracts any new source strings introduced by upstream, and recompiles
   `.mo` (which are git-ignored):
   ```sh
   just translate       # makemessages -a (django + djangojs) + compilemessages
   ```
   If upstream added/changed source strings, translate the new German entries in
   `locale/de`, then commit them in the submodule and bump the parent pointer.

4. Push both branches.

## Follow-up (not part of this branch)

- Recreate the Weblate `intranet` component with **source language = French (fr)**, file
  format gettext PO, mask `locale/*/LC_MESSAGES/django.po`, recreating the `djangojs`
  domain if the old config had it. Sync Weblate → repo before deleting the old component.
  Translation memory is stored at the project level and is preserved.
