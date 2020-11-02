[![Build Status](https://travis-ci.org/defivelo/db.svg?branch=master)](https://travis-ci.org/defivelo/db)

# L’Intranet Défi Vélo

Ce dépôt contient tout ce qui est nécessaire à faire tourner l’Intranet Défi Vélo.

Il a pour objectif de simplifier et améliorer la gestion des saisons, sessions,
Qualifs, établissements, etc, et vise principalement à être utilisée par
les collaborateurs du Défi Vélo, aux différents échelons cantonaux et
inter-cantonaux.

## Local setup
```
git clone --recursive git@gitlab.liip.ch:swing/defivelo/intranet
vagrant up
```

```
vagrant ssh
fab prod import-db
./manage.py set_fake_passwords
make help
```

## Deploy
```
vagrant ssh
fab [staging|prod] deploy
```
