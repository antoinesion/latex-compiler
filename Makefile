update:
	git fetch
	git pull

deploy:
	sudo fn deploy --verbose --create-app --local --no-bump $(NAME)

deploy-all:
	sudo fn deploy --verbose --create-app --all --local --no-bump