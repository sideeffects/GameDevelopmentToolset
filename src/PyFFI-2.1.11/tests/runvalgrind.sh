#!/bin/sh
valgrind --log-file=valgrind_nothing.txt /usr/bin/python /usr/bin/niftoaster.py check_read nothing
valgrind --log-file=valgrind_check_read.txt /usr/bin/python /usr/bin/niftoaster.py check_read nif/test_skincenterradius.nif
cat valgrind_nothing.txt | tail -n 14 | sed 's/==.*== //' > valgrind_summary_nothing.txt
cat valgrind_check_read.txt | tail -n 14 | sed 's/==.*== //' > valgrind_summary_check_read.txt

