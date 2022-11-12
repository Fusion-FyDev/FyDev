#!bin/bash
#The scripts to start jenkins-bluocean container
#docker volumes create jenkins-data
#docker build -t blueocean_plugin:v0.1 .

docker run \
-u root \
--rm \
-d \
-p 8088:8080 \
-p 50000:50000 \
-v jenkins-data-plugin:/var/jenkins_home \
-v /var/run/docker.sock:/var/run/docker.sock \
--name jenkins-blueocean-plugin \
blueocean_plugin:v0.1
#jenkinsci/blueocean


