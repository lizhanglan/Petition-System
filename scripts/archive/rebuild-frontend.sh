#!/bin/bash
cd ~/lizhanglan/Petition-System
docker-compose build frontend --no-cache
docker-compose up -d frontend
echo "Frontend rebuilt successfully!"
