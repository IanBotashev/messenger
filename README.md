# messenger
Simple messenger app written in python with Twisted.  
Uses a hand-made, server-client protocol to store messages in a central server.  
Servers can be self-hosted, and support a multitude of settings.

## Installation
1. Clone this github repository to your machine.
```shell
git clone https://github.com/IanBotashev/messenger
```
2. Change directory to the newly created directory (most likely `messenger`).
```shell
cd messenger
```
3. Install all required python packages (you might either use `pip` or `pip3`).
```shell
pip3 install -r requirements.txt
```

## Running
### Client
To run the client, use the following command:
```shell
./client.py -ht HOST [-p PORT]
```

### Server
To run the server on your machine you first must create a new folder titled "persistent" 
(or change the `config.toml` lines `log_file` and `session.database.db` to not have the `persistent/` prefix. Note: this won't work for docker.)
```shell
mkdir persistent
```

To run in the console:
```shell
./server.py
```

Using docker compose:
```shell
docker compose up
```

Using just docker:
```shell
docker build -t messenger-server .
docker run -p 49153:49153 -v {FULL_PATH_TO}/persistent:/app/persistent -it messenger-server
```

## Server config.toml
Example config.toml file for a server.  
Any changes to the settings file require a server reboot.
```toml
port = 49153  # Port to host on. Standard is 49153. Only matters outside of a docker installation.
log_file = "persistent/server.log"  # persistent can be removed, but will be incompatible with docker.

# Session settings.
[session]
    [session.server_user]
        name = "server"  # The account used by the server for announcements.
        password = "admin"  # Not a security threat as you cannot login twice as the server.
        # If a user with these credentials does not exist, one will be created automatically.

    # Database currently is SQLite3.
    [session.database]
        db = "persistent/messenger.db"  # Name of the database file to use. If it doesn't exist, one will be created.
        allow_user_creation = true  # Allows anonymous connections to create accounts.
        max_shown_messages = 100  # Max amount of messages in the catalog to be sent to a client.
        message_character_limit = 200  # The maximum length of a message that can be posted by a client.
        username_character_limit = 20  # Maximum length of a username that can be used by a client.
    
    # Server announces certain events using these string. 
    # {user} gets replaced with the name of the user in question.
    [session.announcements]
        leave = "{user} has left."  # For when a user logs out.
        join = "{user} has joined."  # For when an anonymous connection logs itself in.
        abrupt_leave = "{user} left unexpectedly."  # When a user leaves without logging out first.
        # It might mean that it was abrupt; or just that they forgot to log out before leaving.
 ```