#!/usr/bin/perl -w
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

my $DIRNAME = ".";
my $TABLE_TAGS = "bgcolor='#a0e0ff' border=5";

print "Content-type:  text/html\n\n";

opendir(D,$DIRNAME) || die("Cannot opendir($DIRNAME):  $!");
my @files = map { "$DIRNAME/$_" } grep( /\.png/, readdir(D) );
closedir(D);

print "<html><body><center><table $TABLE_TAGS>\n";
my $ctr = 0;
my $sep = "<tr>";
foreach my $fn ( @files )
    {
    print $sep, "\n" if( $ctr++ % 4 == 0 );
    $sep = "</tr><tr>";
    $_ =$fn;
    s:.*/::g;
    s:\.png$::;
    s:_: :g;
    
    print "	<td><img src='$fn'><br>$_</td>\n";
    }
print "</tr></table></center></body></html>\n";
