update:
	git fetch
	git pull

deploy:
	echo "Removing all containers..."
	sudo docker rm $(sudo docker ps -a -q)
	sudo fn deploy --verbose --create-app --local --no-bump $(NAME)

deploy-all:
	echo "Removing all containers..."
	sudo docker rm $(sudo docker ps -a -q)
	sudo fn deploy --verbose --create-app --all --local --no-bump