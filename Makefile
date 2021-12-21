deploy:
	sudo fn deploy --verbose --create-app --all --local --no-bump

update:
	git fetch
	git pull