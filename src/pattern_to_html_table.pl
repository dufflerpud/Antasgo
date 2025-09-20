#!/usr/local/bin/perl -w
#@HDR@	$Id$
#@HDR@		Copyright 2024 by
#@HDR@		Christopher Caldwell/Brightsands
#@HDR@		P.O. Box 401, Bailey Island, ME 04003
#@HDR@		All Rights Reserved
#@HDR@
#@HDR@	This software comprises unpublished confidential information
#@HDR@	of Brightsands and may not be used, copied or made available
#@HDR@	to anyone, except in accordance with the license under which
#@HDR@	it is furnished.

use strict;

my $PARAMS = " width=3px";

print "<table cellspacing=0 cellpadding=0 style='font-size:2px'>\n";
while( $_ = <STDIN> )
    {
    chomp( $_ );
    print "<tr style='height:3px'>",
	( map
	    { $_ eq "O"
		? "<th$PARAMS bgcolor=red  >.</th>"
		: "<th$PARAMS bgcolor=white>.</th>" } split(//) ), "</tr>\n";
    }
print "</table>\n";
