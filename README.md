# Scratch ![alt text](https://travis-ci.com/eaudeweb/scratch.svg?branch=master) [![Coverage Status](https://coveralls.io/repos/github/eaudeweb/scratch/badge.svg?branch=master)](https://coveralls.io/github/eaudeweb/scratch?branch=master) [![Docker](https://img.shields.io/docker/cloud/build/eaudeweb/scratch?label=Docker&style=flat)](https://hub.docker.com/r/eaudeweb/scratch/builds)

### Python Django Scratch 

## Installation 

1. Clone project using SSH key:

        git clone git@github.com:eaudeweb/scratch.git
        
2. Copy docker example files:

        cd scratch/
        cp docker-compose.override.yml.example docker-compose.override.yml
        cp docker/app.env.example docker/app.env
        cp docker/db.env.example docker/db.env
        
 3. Create the stack and start it:
 
        docker-compose up -d
        
4. Verify if the containers were created:

        docker-compose ps
        
5. Go into application container:
        
        docker exec -it scratch.app sh
        
6. Run server:

        python manage.py runserver 0.0.0.0:8000
        
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
        
## Errors

- Bootstrap checks failed: When starting the Elasticsearch container, this error may ocurr. The following command should fix it.
        
        sudo sysctl -w vm.max_map_count=262144

  
