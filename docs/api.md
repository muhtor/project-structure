# User Create

POST: http://127.0.0.1:8000/api/auth/v1/create/

### JSON request

```
{
    "user": {
        "first_name": "eshmat",
        "last_name": "toshmat",
	    "email": "testgobazar@gmail.com",
	    "password": "12345678"
    }
}
```

### JSON response

```
{
    "user": {
        "email": "weboasis9002@gmail.com"
    }
}
```
-----------------------------
# User Auth

POST: http://127.0.0.1:8000/auth-token/create/

BODY > x-www-from-urlencoded:

email : test@gmail.com / password : 123test

-----------------------------

