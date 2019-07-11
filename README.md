# Scratch

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


