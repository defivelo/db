# Comment mettre en place son environnement de développement

## Cloner le dépôt

`$ git clone -b master https://github.com/defivelo/db.git DB-DefiVelo`

## Installer les outils

- vagrant: https://liip-drifter.readthedocs.io/en/latest/requirements.html#install-requirements

## Créer un environnement virtuel et s'y connecter

```
cd DB-DefiVelo
vagrant up
vagrant ssh
```

## Créer un utilisateur super-administrateur

```
./manage.py createsuperuser
```

## Lancer le serveur Web de test

```
./manage.py runserver_plus
```

## Autre

Les autres tâches sont décrites dans le `Makefile` à la racine du projet.
Lancer `make help` dans l'environnement virtuel pour les lister,
et `make ma_tache` pour les exécuter.
