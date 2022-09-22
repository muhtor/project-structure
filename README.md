# Backend development
This is a Django project which primarily builds APIs using Django REST Framework.

### How to clone project

```
git clone https://gitlab.com/Ahrorbek/kennekt-beckend-front-end.git
```
## Guide for developers
Developers do not have direct access to master branch. Only the maintainer has access to master. Develops need to push to the branch 'dev'. The maintainer merges 'dev' with 'master' if need be.

Create 'dev' branch:
```
git branch dev
```

Activate 'dev' branch as by default 'master' is activate:
```
git checkout dev
```

See which branch is active:
```
git branch
```

Commit to local git:
```
git commit -m "Changes made to this app with some details"
```

Push commits to remote git:
```
git push origin dev
```

Pull from remote git:
```
git pull origin dev
```

# DOCKER

### Django commands
Running migrations with docker-compose (if `run` is used instead of `exec`, then new container is created instead of using the existing one - hence it's better to use `exec`)
```
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic
docker-compose exec web python manage.py createsuperuser
```

### Other commands

Deleting all images and containers (dangerous please use it with caution)
```
docker system prune -a --volumes
```

```
docker images
docker container ls
```
