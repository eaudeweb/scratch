# Scratch ![alt text](https://travis-ci.com/eaudeweb/scratch.svg?branch=master) [![Coverage Status](https://coveralls.io/repos/github/eaudeweb/scratch/badge.svg?branch=master)](https://coveralls.io/github/eaudeweb/scratch?branch=master) [![Docker](https://img.shields.io/docker/cloud/build/eaudeweb/scratch?label=Docker&style=flat)](https://hub.docker.com/r/eaudeweb/scratch/builds)

### Python Django Scratch

## Installation

1. Clone project using SSH key:

        git clone git@github.com:eaudeweb/scratch.git

1. Copy docker example files:

        cd scratch/
        cp docker-compose.override.yml.example docker-compose.override.yml
        cp docker/app.env.example docker/app.env
        cp docker/db.env.example docker/db.env
        cp docker/redis.env.example docker/redis.env
        cp docker/tika.env.example docker/tika.env
        cp docker/cachet.env.example docker/cachet.env

    > NOTE:
    > 1. LDAP variables in `app.env` must be configured manually.
    > 2. If you're on macOS, you might need to customze docker-compose.override to use the `amd64/elasticsearch:6.8.23` image in elasticsearch services.

        docker-compose up -d

1. Verify if the containers were created:

        docker-compose ps

1. Go into application container:

        docker compose exec web sh

1. Run migrations:
    ```
    python manage.py migrate
    ```
1. Load CPV codes, TED Countries and UNSPSC codes to the database:
   ```commandline
       python manage.py load_initial_data
    ```
   > NOTE: Run the command with `--reverse` flag to delete the data added by the command
1. Run server:
    ```commandline
    python manage.py runserver 0.0.0.0:8000
    ```
### [Cachet Setup Info](Cachet.md)
## Running with NGINX

If you want to use NGINX to serve the project you need to do the following:

Comment the web service the ports in docker-compose.yml
```
    web:
      ...
      ports:
        - 8000:8000
```

Create docker-compose.override.yml from  docker-compose.override.yml.nginx.example
```
    cp docker-compose.override.yml.nginx.example docker-compose.override.yml
```

Create the stack and start it:
```
    docker-compose up
```

## Testing

You can run the test suite as follows:

    python manage.py test --settings=scratch.test_settings

## ElasticSearch Web Client

If you need to debug ElasticSearch during development, you can connect to the
web client at http://localhost:1358/?appname=%2A&url=http://localhost:9200/

## Errors

- Bootstrap checks failed: When starting the Elasticsearch container, this error may ocurr. The following command should fix it.

        sudo sysctl -w vm.max_map_count=262144
- TenderDocument objects have no actual file associated: Due to a failed request to download a tender document,
TenderDocument objects without an actual document may be created and saved in the db. After the cause of the request
failure is resolved, you can fix the incomplete objects already saved in the db by running the following command,
which will download the documents for the instances where they are missing:

   ```commandline
  python manage.py add_documents
   ```

## Management Commands

-   **add_award:** Adds Contract Awards for expired UNGM tenders
-   **deadline_notifications:** Sends e-mails with favourite tenders that have deadline in DEADLINE_NOTIFICATIONS days
-   **delete_expired_tenders:** Deletes tenders from archive with deadline passed since DELETE_EXPIRED_DAYS days ago or more
-   **notify:** Sends an e-mail for every new tender or winner(default) or an e-mail with all new tenders and winners(digest parameter specified);
-   **notify_favourites:** Sends e-mails for favourites tenders, according to digest parameter described previously
-   **notify_keywords:** Sends e-mails for tenders with keywords, according to digest parameter described previously
-   **remove_unnecessary_newlines:** Removes newlines Vendors' names
-   **update_ted:** Add new TED tenders, according to days_ago parameter or beginning with latest published date
    from database, if not specified
-   **update_ungm:** Add new UNGM tenders, according to days_ago parameter or beginning with latest published date from
    database, if not specified
