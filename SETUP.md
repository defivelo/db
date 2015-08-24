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

## Installer les dépendances du projet et initialiser la DB

```
pip install -r requirements/dev.txt
echo "sqlite:///defivelo.sqlite" > envdir/local/DATABASE_URL
./manage.py migrate
```

## Créer un utilisateur super-administrateur

```
./manage.py createsuperadmin
```

## Lancer le serveur Web de test

```
./manage.py runserver_plus
```
