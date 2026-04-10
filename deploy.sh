#!/bin/bash

#remove the old image (optional)
docker rmi -f dennismuga/whatsapp-spammer   

#build the image
docker build -t dennismuga/whatsapp-spammer .  

#push to dockerhub (optional)
docker push dennismuga/whatsapp-spammer
