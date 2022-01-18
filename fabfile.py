import functools
import inspect
import os
import random
import subprocess
import time
from datetime import datetime
from io import StringIO
from tempfile import NamedTemporaryFile

import dj_database_url
from dulwich import porcelain
from fabric import task
from fabric.connection import Connection
from invoke import Exit
from invoke.context import Context
from invoke.exceptions import UnexpectedExit

ENVIRONMENTS = {
    "prod": {
        "root": "/var/www/intranet.defi-velo.ch/prod/",
        "host": "wpy10809@onhp-python3.iron.bsa.oriented.ch:29992",
        "pid": "/run/uwsgi/app/intranet.defi-velo.ch/pid",
        "ini": "/etc/uwsgi/apps-enabled/intranet.defi-velo.ch.ini",
        "settings": {
            "ALLOWED_HOSTS": "\n".join(["intranet.defi-velo.ch"]),
            "MEDIA_URL": "/media/",
            "STATIC_URL": "/static/",
            "MEDIA_ROOT": "/var/www/intranet.defi-velo.ch/prod/media/",
            "STATIC_ROOT": "/var/www/intranet.defi-velo.ch/prod/static/",
            "SITE_DOMAIN": "intranet.defi-velo.ch",
            "VIRTUAL_ENV": "/var/www/intranet.defi-velo.ch/prod/venv",
        },
    },
    "staging": {
        "root": "/var/www/intranet.defi-velo.ch/staging/",
        "host": "wpy10809@onhp-python3.iron.bsa.oriented.ch:29992",
        "pid": "/run/uwsgi/app/staging.intranet.defi-velo.ch/pid",
        "ini": "/etc/uwsgi/apps-enabled/staging.intranet.defi-velo.ch.ini",
        "requirements": "staging",
        "settings": {
            "ALLOWED_HOSTS": "\n".join(["staging.intranet.defi-velo.ch"]),
            "MEDIA_URL": "/media/",
            "STATIC_URL": "/static/",
            "MEDIA_ROOT": "/var/www/intranet.defi-velo.ch/staging/media/",
            "STATIC_ROOT": "/var/www/intranet.defi-velo.ch/staging/static/",
            "SITE_DOMAIN": "staging.intranet.defi-velo.ch",
            "VIRTUAL_ENV": "/var/www/intranet.defi-velo.ch/staging/venv",
            "USE_DB_EMAIL_BACKEND": "1",
            "DJANGO_SETTINGS_MODULE": "defivelo.settings.staging",
        },
    },
}

project_name = "defivelo"
project_name_verbose = "Intranet Défi Vélo"

PRODUCTION_DB_NAME = "intranetdefiveloch001"


def remote(task_func):
    """
    Decorate task functions to check for presence of a Connection instance in their context.
    Also pass the Connection instance in argument for convenience.
    """

    @functools.wraps(task_func)
    def call_task_with_connection(ctx, *args, **kwargs):
        if not hasattr(ctx, "conn"):
            raise RuntimeError("Trying to run a remote task with no environment loaded")
        return task_func(ctx, *args, **kwargs)

    call_task_with_connection.__signature__ = inspect.signature(task_func)
    return call_task_with_connection


def ensure_absolute_path(path):
    if not os.path.isabs(path):
        raise ValueError("{!r} is not an absolute path.".format(path))


class CustomConnection(Connection):
    """
    Add helpers function on Connection
    """

    @property
    def site_root(self):
        return self.config.root

    @property
    def project_root(self):
        """
        Return the path to the root of the project on the remote server.
        """
        return os.path.join(self.site_root, project_name)

    @property
    def venv_path(self):
        return os.path.join(self.site_root, "venv")

    @property
    def envdir_path(self):
        return os.path.join(self.project_root, "envdir")

    @property
    def backups_root(self):
        """
        Return the path to the backups directory on the remote server.
        """
        return os.path.join(self.site_root, "backups")

    @property
    def media_root(self):
        """
        Return the path to the media directory on the remote server.
        """
        try:
            path = self.config.settings["MEDIA_ROOT"]
        except KeyError:
            return os.path.join(self.site_root, "media")
        else:
            ensure_absolute_path(path)
            return path

    @property
    def static_root(self):
        """
        Return the path to the static directory on the remote server.
        """
        try:
            path = self.config.settings["STATIC_ROOT"]
        except KeyError:
            return os.path.join(self.site_root, "static")
        else:
            ensure_absolute_path(path)
            return path

    def run_in_project_root(self, cmd, **kwargs):
        """
        Run command after a cd to the project_root
        """
        with self.cd(self.project_root):
            return self.run(cmd, **kwargs)

    def git(self, gitcmd, **kwargs):
        """
        git from the project_root
        """
        return self.run_in_project_root("git {}".format(gitcmd), **kwargs)

    def run_in_venv(self, cmd, args, **run_kwargs):
        """
        Binaries from the venv
        """
        return self.run_in_project_root(
            "{} {}".format(os.path.join(self.venv_path, "bin", cmd), args), **run_kwargs
        )

    def mk_venv(self, **run_kwargs):
        """
        Create the venv
        """

        with self.cd(self.site_root):
            self.run("python3 -m venv venv", **run_kwargs)

    def pip(self, args, **run_kwargs):
        """
        pip from the venv, in the project_root
        """
        return self.run_in_venv("pip", args, **run_kwargs)

    def python(self, args, **run_kwargs):
        """
        python from the venv, in the project_root
        """
        return self.run_in_venv("python", args, **run_kwargs)

    def manage_py(self, args, debug=False, **run_kwargs):
        """
        manage.py with the python from the venv, in the project_root
        """
        try:
            env = {
                "DJANGO_SETTINGS_MODULE": self.config.settings["DJANGO_SETTINGS_MODULE"]
            }
        except KeyError:
            env = {}
        if debug:
            env["DEBUG"] = 1
        return self.python("./manage.py {}".format(args), env=env, **run_kwargs)

    def set_setting(self, name, value=None, force: bool = True):
        """
        Set a setting in the environment directory, for use by Django
        """
        envfile_path = os.path.join(self.envdir_path, name)

        will_write = force
        if not force:
            try:
                # Test that it does exist
                self.run_in_project_root("test -r {}".format(envfile_path), hide=True)
            except UnexpectedExit:
                will_write = True

        if will_write:
            if value is None:
                value = input("Value for {}: ".format(name))

            # Convert booleans into values understood as such by Django
            if isinstance(value, bool):
                value = "1" if value else ""
            self.put(StringIO("{}\n".format(value)), envfile_path)

    def db_creds(self):
        """
        Return DB dictionary of credentials from the DATABASE_URL envdir var
        """
        with self.cd(self.project_root):
            db_credentials = self.run(
                "cat envdir/DATABASE_URL", hide=True
            ).stdout.strip()
        db_credentials_dict = dj_database_url.parse(db_credentials)

        if not is_supported_db_engine(db_credentials_dict["ENGINE"]):
            raise NotImplementedError(
                "The dump_db task doesn't support the remote database engine"
            )
        return db_credentials_dict

    def dump_db(self, destination):
        """
        Dump the database to the given directory and return the path to the file created.
        This creates a gzipped SQL file.
        """
        db_credentials_dict = self.db_creds()

        outfile = os.path.join(
            destination, datetime.now().strftime("%Y-%m-%d_%H%M%S.sql.gz")
        )

        self.run(
            "pg_dump -O -x -h '{host}' -U '{user}' '{db}'|gzip > {outfile}".format(
                host=db_credentials_dict["HOST"],
                user=db_credentials_dict["USER"],
                db=db_credentials_dict["NAME"],
                outfile=outfile,
            ),
            env={"PGPASSWORD": db_credentials_dict["PASSWORD"].replace("$", "\$")},
        )

        return outfile

    def drop_and_recreate_db(
        self, production_db_name: str = PRODUCTION_DB_NAME, **kwargs
    ):
        """
        Drop and recreate an empty DB for this environment
        """
        db_creds = self.db_creds()
        try:
            confirmed = kwargs.pop("confirm_that_this_is_really_what_I_want")
        except KeyError:
            confirmed = False

        if not confirmed:
            raise Exit("You need to pass the righteous argument to proceed with this")

        if db_creds["NAME"] == production_db_name:
            raise Exit("This is the production DB, abort.")
        self.run(
            f"dropdb -h '{db_creds['HOST']}' -U '{db_creds['USER']}' '{db_creds['NAME']}'",
            env={"PGPASSWORD": db_creds["PASSWORD"].replace("$", "\$")},
        )
        self.run(
            f"createdb -h '{db_creds['HOST']}' -U '{db_creds['USER']}' '{db_creds['NAME']}'",
            env={"PGPASSWORD": db_creds["PASSWORD"].replace("$", "\$")},
        )

    def restore_dump(self, db_dump_gz):
        """
        Restore a gz DB dump to our database
        """
        db_creds = self.db_creds()
        self.run(
            f"gunzip -c {db_dump_gz} | psql -h '{db_creds['HOST']}' -U '{db_creds['USER']}' '{db_creds['NAME']}'",
            env={"PGPASSWORD": db_creds["PASSWORD"].replace("$", "\$")},
        )

    def create_structure(self):
        """
        Create the basic directory structure on the remote server.
        """
        command = " ".join(
            [
                "mkdir -p",
                self.project_root,
                self.backups_root,
                self.static_root,
                self.media_root,
            ]
        )
        self.run(command)

    def clean_old_database_backups(self, nb_backups_to_keep):
        """
        Remove old database backups from the system and keep `nb_backups_to_keep`.
        """
        backups = self.ls(self.backups_root)
        backups = sorted(backups, reverse=True)

        if len(backups) > nb_backups_to_keep:
            backups_to_delete = backups[nb_backups_to_keep:]
            file_to_remove = [
                os.path.join(self.backups_root, backup_to_delete)
                for backup_to_delete in backups_to_delete
            ]
            self.run('rm "%s"' % '" "'.join(file_to_remove))
            print("%d backups deleted." % len(backups_to_delete))
        else:
            print("No backups to delete.")

    def ls(self, path):
        """
        Return the list of the files in the given directory, omitting . and ...
        """
        with self.cd(path):
            files = self.run("for i in *; do echo $i; done", hide=True).stdout.strip()
            files_list = files.replace("\r", "").split("\n")

        return files_list


def generate_secret_key():
    """
    Generate a random secret key, suitable to be used as a SECRET_KEY setting.
    """
    return "".join(
        [
            random.SystemRandom().choice(
                "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
            )
            for i in range(50)
        ]
    )


def is_supported_db_engine(engine):
    return engine in [
        "django.db.backends.postgresql_psycopg2",
        "django.db.backends.postgresql",
    ]


@task
@remote
def fetch_db(c, destination="."):
    """
    Dump the database on the remote host and retrieve it locally.

    The destination parameter controls where the dump should be stored locally.
    """
    dump_path = c.conn.dump_db("~")
    filename = os.path.basename(dump_path)

    subprocess.run(
        [
            "scp",
            "-P",
            str(c.conn.port),
            "{user}@{host}:{directory}".format(
                user=c.conn.user, host=c.conn.host, directory=dump_path
            ),
            destination,
        ]
    )
    c.conn.run("rm %s" % dump_path)

    return os.path.join(destination, filename)


@task
@remote
def reset_db_from_prod(c):
    """
    Restore the given database dump.

    The dump must be a gzipped SQL dump. If the dump_file parameter is not set,
    the database will be dumped and retrieved from the remote host.
    """
    if not c.environment == "staging":
        raise Exit(
            "reset_db_from_prod can only be executed for the staging environment"
        )

    # Get PROD connection information
    try:
        prod_conf = ENVIRONMENTS["prod"]
    except KeyError:
        raise Exit("reset_db_from_prod needs to access the 'prod' environment")

    #  Do a pre-backup
    c.conn.dump_db(c.conn.backups_root)

    prod_ctx = Context(prod_conf)
    prod_ctx.conn = CustomConnection(host=prod_conf["host"], inline_ssh_env=True)
    prod_ctx.conn.config.load_overrides(prod_conf)

    with NamedTemporaryFile() as local_transit_file:

        # Handle the production part:
        with prod_ctx.conn as conn:
            # Dump the PROD DB
            prod_dump_path = conn.dump_db("~")

            # Download it here, assuming PROD and STAGING can be on complete different servers (it's not the case I know)
            subprocess.run(
                [
                    "scp",
                    "-P",
                    str(conn.port),
                    f"{conn.user}@{conn.host}:{prod_dump_path}",
                    local_transit_file.name,
                ]
            )

            # Delete the PROD dump from the server
            conn.run("rm %s" % prod_dump_path)

        # Now push to staging
        with c.conn as conn:
            # Put it to ~
            subprocess.run(
                [
                    "scp",
                    "-P",
                    str(conn.port),
                    local_transit_file.name,
                    f"{conn.user}@{conn.host}:{prod_dump_path}",
                ]
            )
            # OK. Now we have a prod backup on the staging environment. Proceed to restoring it
            conn.drop_and_recreate_db(confirm_that_this_is_really_what_I_want=True)
            # Restore the dump there
            conn.restore_dump(prod_dump_path)
            # Now remove the dump from the remote path too
            conn.run("rm %s" % prod_dump_path)

    # Run what's needed to bring the target env to a working state
    dj_migrate_database(c)
    dj_sync_roles(c)
    c.conn.manage_py(
        f'set_default_site --name "{project_name_verbose} ({c.environment})" --domain "{c.config.settings["SITE_DOMAIN"]}"'
    )
    c.conn.manage_py("set_fake_passwords", debug=True)
    restart_uwsgi(c)


@task
@remote
def import_db(c, dump_file=None):
    """
    Restore the given database dump.

    The dump must be a gzipped SQL dump. If the dump_file parameter is not set,
    the database will be dumped and retrieved from the remote host.
    """
    db_credentials = os.environ.get("DATABASE_URL")
    if not db_credentials:
        with open("envdir/DATABASE_URL", "r") as db_credentials_file:
            db_credentials = db_credentials_file.read()
    db_credentials_dict = dj_database_url.parse(db_credentials)

    if not is_supported_db_engine(db_credentials_dict["ENGINE"]):
        raise NotImplementedError(
            "The import_db task doesn't support your database engine"
        )

    if dump_file is None:
        dump_file = fetch_db(c)

    db_info = {
        "host": db_credentials_dict["HOST"],
        "user": db_credentials_dict["USER"],
        "db": db_credentials_dict["NAME"],
        "db_dump": dump_file,
    }
    env = {"PGPASSWORD": db_credentials_dict["PASSWORD"].replace("$", "\$")}

    c.run(
        """
        psql -h '{host}' -U '{user}' '{db}' '$(./manage.py sqldsn -q)' <<<'
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE pid != pg_backend_pid()'
        """.format(
            **db_info
        ),
        env=env,
    )

    c.run("dropdb -h '{host}' -U '{user}' '{db}'".format(**db_info), env=env)
    c.run("createdb -h '{host}' -U '{user}' '{db}'".format(**db_info), env=env)
    c.run(
        "gunzip -c {db_dump}|psql -h '{host}' -U '{user}' '{db}'".format(**db_info),
        env=env,
    )


@task
@remote
def deploy(c):
    """
    Execute all deployment steps
    """
    c.conn.create_structure()
    push_code_update(c, "HEAD")
    sync_settings(c)
    c.conn.dump_db(c.conn.backups_root)
    install_requirements(c)
    dj_collect_static(c)
    django_compress(c)
    dj_migrate_database(c)
    dj_sync_roles(c)
    compile_messages(c)
    restart_uwsgi(c)
    c.conn.clean_old_database_backups(nb_backups_to_keep=10)


@task
@remote
def push_code_update(c, git_ref):
    """
    Synchronize the remote code repository
    """
    with c.conn.cd(c.conn.project_root):
        # First, check that the remote deployment directory exists
        try:
            c.conn.run("test -d .", hide=True)
        except UnexpectedExit:
            raise Exit(
                "Provisioning not finished, directory {} doesn't exist!".format(
                    c.config["root"]
                )
            )
        # Now make sure there's git, and a git repository
        try:
            c.conn.git("--version", hide=True)
        except UnexpectedExit:
            raise Exit("Provisioning not finished, git not available!")

        try:
            c.conn.git("rev-parse --git-dir", hide=True)
        except UnexpectedExit:
            c.conn.git("init")

    git_remote_url = "ssh://{user}@{host}:{port}/{directory}".format(
        user=c.conn.user,
        host=c.conn.host,
        port=c.conn.port,
        directory=c.conn.project_root,
    )

    # Now push our code to the remote, always as FABHEAD branch
    porcelain.push(".", git_remote_url, "{}:FABHEAD".format(git_ref))

    with c.conn.cd(c.conn.project_root):
        c.conn.git("checkout -f -B master FABHEAD", hide=True)
        c.conn.git("branch -d FABHEAD", hide=True)
        # Force using an absolute URL for locale submodule since the relative one would fail
        # (this uses a deploy key generated on the server)
        c.conn.git(
            "config submodule.locale.url git@gitlab.liip.ch:swing/defivelo/intranet-i18n.git",
            hide=True,
        )
        c.conn.git("submodule update --init", hide=True)

        vcs_commit = subprocess.run(
            ["git", "rev-parse", git_ref], stdout=subprocess.PIPE
        ).stdout.decode()
        vcs_version = subprocess.run(
            ["git", "describe", "--tags", git_ref], stdout=subprocess.PIPE
        ).stdout.decode()
        c.conn.set_setting("VCS_COMMIT", vcs_commit)
        c.conn.set_setting("VCS_VERSION", vcs_version)


@task
@remote
def install_requirements(c):
    """
    Install project requirements in venv
    """
    try:
        c.conn.run("test -r {}".format(c.conn.venv_path), hide=True)
    except UnexpectedExit:
        c.conn.mk_venv()

    try:
        requirements_variant = c.config.requirements
    except AttributeError:
        requirements_variant = "base"

    c.conn.pip(f"install -r requirements/{requirements_variant}.txt")


@task
@remote
def sync_settings(c):
    """
    Synchronize the settings from the above environment to the server
    """

    required_settings = set(
        [
            "DATABASE_URL",
            "MEDIA_ROOT",
            "STATIC_ROOT",
            "MEDIA_URL",
            "STATIC_URL",
            "ALLOWED_HOSTS",
        ]
    )

    env_settings = getattr(c.config, "settings", {})
    for setting, value in env_settings.items():
        c.conn.set_setting(setting, value=value)

    # Ask for settings that are required but were not set in the parameters
    # file
    for setting in required_settings - set(env_settings.keys()):
        c.conn.set_setting(setting, force=False)

    c.conn.set_setting(
        "DJANGO_SETTINGS_MODULE",
        value="%s.settings.base" % project_name,
        force=False,
    )
    c.conn.set_setting("SECRET_KEY", value=generate_secret_key(), force=False)


@task
@remote
def dj_collect_static(c):
    """
    Django: collect the statics
    """
    c.conn.manage_py("collectstatic --noinput")


@task
@remote
def dj_migrate_database(c):
    """
    Django: Migrate the database
    """
    c.conn.manage_py("migrate")


@task
@remote
def dj_sync_roles(c):
    """
    Django: Synchronize Groups/Permissions with defivelo.roles
    """
    c.conn.manage_py("sync_roles --reset_user_permissions")


@task
@remote
def restart_uwsgi(c):
    """
    Restart uWSGI processes
    """
    c.conn.run(f"uwsgi --stop '{c.conn.config.pid}'")
    time.sleep(2)
    c.conn.run(f"uwsgi --start '{c.conn.config.ini}'")


@task
@remote
def django_compress(c):
    """
    Minify assets with django-compressor
    """
    c.conn.manage_py("compress --force")


@task
@remote
def compile_messages(c):
    c.conn.manage_py("compilemessages -l fr -l de -l en -l it")


# Environment handling stuff
############################
def create_environment_task(name, env_conf):
    """
    Create a task function from an environment name
    """

    @task(name=name)
    def load_environment(ctx):
        conf = env_conf.copy()
        conf["environment"] = name
        # So now conf is the ENVIRONMENTS[env] dict plus "environment" pointing to the name
        # Push them in the context config dict
        ctx.config.load_overrides(conf)
        # Add the common_settings in there
        ctx.conn = CustomConnection(host=conf["host"], inline_ssh_env=True)
        ctx.conn.config.load_overrides(conf)

    load_environment.__doc__ = (
        """Prepare connection and load config for %s environment""" % name
    )
    return load_environment


def load_environments_tasks(environments):
    """
    Load environments as fabric tasks
    """
    for name, env_conf in environments.items():
        globals()[name] = create_environment_task(name, env_conf)


# Yes, do it
load_environments_tasks(ENVIRONMENTS)
