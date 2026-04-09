#!/bin/bash

#remove eks image if exists
docker rmi -f whatsapp-spammer

#build the image
docker build -t whatsapp-spammer .  

#stop container
docker rm -f whatsapp-spammer  

#run container
#docker run -d --name whatsapp-spammer whatsapp-spammer

#push to dockerhub (optional)
docker push dennismuga/whatsapp-spammer
