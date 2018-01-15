cd /home/bi/source/freetime/freetime/support/logserver
export PYTHONPATH=/home/bi/source/freetime:${PYTHONPATH}
rm -fr nohup.out

nohup pypy run.py AG01 127.0.0.1 7901 0 &
nohup pypy run.py AG02 127.0.0.1 7901 0 &
nohup pypy run.py AG03 127.0.0.1 7901 0 &
nohup pypy run.py AG04 127.0.0.1 7901 0 &
nohup pypy run.py AG05 127.0.0.1 7901 0 &
nohup pypy run.py AG06 127.0.0.1 7901 0 &

nohup pypy run.py LI01 127.0.0.1 7901 0 &
nohup pypy run.py LI02 127.0.0.1 7901 0 &
nohup pypy run.py LI03 127.0.0.1 7901 0 &
nohup pypy run.py LI04 127.0.0.1 7901 0 &
nohup pypy run.py LI05 127.0.0.1 7901 0 &
nohup pypy run.py LI06 127.0.0.1 7901 0 &
nohup pypy run.py LI07 127.0.0.1 7901 0 &
nohup pypy run.py LI08 127.0.0.1 7901 0 &

nohup pypy run.py LI09 127.0.0.1 7901 0 &
nohup pypy run.py LI10 127.0.0.1 7901 0 &
nohup pypy run.py LI11 127.0.0.1 7901 0 &
nohup pypy run.py LI12 127.0.0.1 7901 0 &
nohup pypy run.py LI13 127.0.0.1 7901 0 &
nohup pypy run.py LI14 127.0.0.1 7901 0 &
nohup pypy run.py LI15 127.0.0.1 7901 0 &
nohup pypy run.py LI16 127.0.0.1 7901 0 &

nohup pypy run.py LI17 127.0.0.1 7901 0 &
nohup pypy run.py LI18 127.0.0.1 7901 0 &
nohup pypy run.py LI19 127.0.0.1 7901 0 &
nohup pypy run.py LI20 127.0.0.1 7901 0 &
nohup pypy run.py LI21 127.0.0.1 7901 0 &
nohup pypy run.py LI22 127.0.0.1 7901 0 &
nohup pypy run.py LI23 127.0.0.1 7901 0 &
nohup pypy run.py LI24 127.0.0.1 7901 0 &

nohup pypy run.py LW01 127.0.0.1 7901 0 &
nohup pypy run.py LW02 127.0.0.1 7901 0 &
nohup pypy run.py LW03 127.0.0.1 7901 0 &
nohup pypy run.py LW04 127.0.0.1 7901 0 &
nohup pypy run.py LW05 127.0.0.1 7901 0 &
nohup pypy run.py LW06 127.0.0.1 7901 0 &
nohup pypy run.py LW07 127.0.0.1 7901 0 &
nohup pypy run.py LW08 127.0.0.1 7901 0 &

nohup pypy run.py LW09 127.0.0.1 7901 0 &
nohup pypy run.py LW10 127.0.0.1 7901 0 &
nohup pypy run.py LW11 127.0.0.1 7901 0 &
nohup pypy run.py LW12 127.0.0.1 7901 0 &
nohup pypy run.py LW13 127.0.0.1 7901 0 &
nohup pypy run.py LW14 127.0.0.1 7901 0 &
nohup pypy run.py LW15 127.0.0.1 7901 0 &
nohup pypy run.py LW16 127.0.0.1 7901 0 &

nohup pypy run.py LW17 127.0.0.1 7901 0 &
nohup pypy run.py LW18 127.0.0.1 7901 0 &
nohup pypy run.py LW19 127.0.0.1 7901 0 &
nohup pypy run.py LW20 127.0.0.1 7901 0 &
nohup pypy run.py LW21 127.0.0.1 7901 0 &
nohup pypy run.py LW22 127.0.0.1 7901 0 &
nohup pypy run.py LW23 127.0.0.1 7901 0 &
nohup pypy run.py LW24 127.0.0.1 7901 0 &
