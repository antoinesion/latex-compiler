deploy:
	sudo fn deploy --create-app --all --local --no-bump

update:
	git fetch
	git pull