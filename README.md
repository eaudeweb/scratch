# Scratch

### Python Django Scratch 

## Installation 

1. Clone project using SSH key:

        git clone git@github.com:eaudeweb/scratch.git
        
2. Copy docker example files:

        cd scratch/
        cp docker-compose.override.yml.example docker-compose.override.yml
        cd docker/
        cp app.env.example app.env
        cp db.env.example db.env
        
 3. Create the stack and start it:
 
        cd ..
        docker-compose up -d
        
4. Verify if the containers were created:

        docker-compose ps
        
5. Go into application container:
        
        docker exec -it scratch.app sh
        


## Useful commands:

1. Go into database container:

        docker exec -it scratch.db sh
        
2.  Stop the stack:

        docker-compose stop
        
3. Stop and delete the stack:
    
        docker-compose down
        
4. See container log:

        docker logs container_name
