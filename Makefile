update:
git fetch
git pull

deploy:
ifneq ($(sudo docker ps -q),)
echo "Stopping all containers..."
sudo docker stop $(sudo docker ps -q)
endif
sudo fn deploy --verbose --create-app --local --no-bump $(NAME)

deploy-all:
ifneq ($(sudo docker ps -q),)
echo "Stopping all containers..."
sudo docker stop $(sudo docker ps -q)
endif
sudo fn deploy --verbose --create-app --all --local --no-bump