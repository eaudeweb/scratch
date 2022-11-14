# Cachet
### Status page for _Scratch_
Link: http://localhost:81/

Documentation: https://docs.cachethq.io/

## Setup

1. After the docker containers started, access the Cachet page to complete the setup.

1. On the Environment Setup page set:
   1. Cache Driver to Redis
   1. Queue Driver to Database
   1. Session Driver to Redis 

1. On Status Page Setup choose a name for the status page, the site domain and a timezone.
1. Create an admin user

After the setup is complete you can log in with the admin account and add components and components groups.

Create the following components:
   - **Scratch** - for monitoring the main app
   - **Elasticsearch** - for monitoring the elasticsearch service
   - **Scratch.async** - for monitoring the async service
   - **Scratch.cron** - for monitoring the cron service

## Cachet-URL-Monitor

https://hub.docker.com/r/mtakaki/cachet-url-monitor

Plugin for cachet that monitors an URL and update the status of the associated cachet component

## Setup 

1. Create a config file:
   1. Copy the ```config.yml.example``` file 
   ```commandline
   cd cachet-url-monitor
   cp config/config.yml.example config/config.yml
   ```
   1. For every component created in Cachet, complete the configurations in [cachet-url-monitor/config/config.yml](https://github.com/eaudeweb/scratch/blob/199debe9e0deadfbafa00bf28bd09533ad1ba2bc/cachet-url-monitor/config/config.yml)
   >    NOTE: for more info about the config file checkout: https://hub.docker.com/r/mtakaki/cachet-url-monitor
1. After the config file is complete run the docker container:
   ```commandline
   docker-compose up
   ```