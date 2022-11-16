# Cachet
### Status page for _Scratch_
Link: http://localhost:81/

Documentation: https://docs.cachethq.io/

## Setup

1. Copy the cachet.env.example file and complete the cachet.env file
   ```commandline
   cp docker/cachet.env.example docker/cachet.env
   ```
   > NOTE: If the scratch.cachet container is started and the APP_KEY variable in cachet.env is not set, the service will
   > exit with an error message which will contain a generated key. You can add the suggested value to the environment 
   > file and restart the container.
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

Plugin for cachet that monitors a URL and update the status of the associated cachet component

## Setup 

1. Create a config file:
   1. Copy the ```config.yml.example``` file 
   ```commandline
   cd cachet-url-monitor
   cp config/config.yml.example config/config.yml
   ```
   1. For every component created in Cachet, complete the configurations in [cachet-url-monitor/config/config.yml](https://github.com/eaudeweb/scratch/blob/199debe9e0deadfbafa00bf28bd09533ad1ba2bc/cachet-url-monitor/config/config.yml):
      1. Complete the urls in the file by replacing ``example`` with the ip address of the host
      1. Add the id from cachet for every component. You can see the component ids by accessing the cachet api at http://localhost:81/api/v1/components
      1. Add the API token from cachet. You can get the token from the profile page (http://localhost:81/dashboard/user)
   >    NOTE: for more info about the config file checkout: https://hub.docker.com/r/mtakaki/cachet-url-monitor
1. After the config file is complete run the docker container:
   ```commandline
   docker-compose up
   ```