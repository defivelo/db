# Comment mettre en place son environnement de développement

## Cloner le dépôt

`$ git clone -b master https://github.com/defivelo/db.git DB-DefiVelo`

## Installer les outils

- virtualenvwrapper (pour mkvirtualenv)

## Créer un environnement virtuel et installer les dépendances du projet

```
cd DB-DefiVelo
mkvirtualenv -a . -r requirements/dev.txt DefiVelo
```
