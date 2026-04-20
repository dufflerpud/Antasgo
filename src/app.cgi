#!/usr/bin/perl -w
#
#indx#	app.cgi - An application to turn life improvement tasks into Bingo
#@HDR@	$Id: app.cgi,v 1.1 2020/08/12 21:17:31 chris Exp chris $
#@HDR@
#@HDR@	Copyright (c) 2024-2026 Christopher Caldwell (Christopher.M.Caldwell0@gmail.com)
#@HDR@
#@HDR@	Permission is hereby granted, free of charge, to any person
#@HDR@	obtaining a copy of this software and associated documentation
#@HDR@	files (the "Software"), to deal in the Software without
#@HDR@	restriction, including without limitation the rights to use,
#@HDR@	copy, modify, merge, publish, distribute, sublicense, and/or
#@HDR@	sell copies of the Software, and to permit persons to whom
#@HDR@	the Software is furnished to do so, subject to the following
#@HDR@	conditions:
#@HDR@	
#@HDR@	The above copyright notice and this permission notice shall be
#@HDR@	included in all copies or substantial portions of the Software.
#@HDR@	
#@HDR@	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
#@HDR@	KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
#@HDR@	WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
#@HDR@	AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#@HDR@	HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#@HDR@	WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#@HDR@	FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#@HDR@	OTHER DEALINGS IN THE SOFTWARE.
#
#hist#	2024-04-18 - c.m.caldwell@alumni.unh.edu - Created
#hist#	2026-02-10 - Christopher.M.Caldwell0@gmail.com - Standard header
########################################################################
#doc#	app.cgi - An application to turn life improvement tasks into Bingo
#doc#	User completes tasks to win Bingo.  Typically used for exercise	#
#doc#	but potentially anything.					#
#########################################################################

use strict;
use MIME::Lite;
use JSON;
use Date::Parse;
use lib "/usr/local/lib/perl";
use cpi_send_file qw(sendmail);
use cpi_user qw(all_prog_users logout_select name_to_group);
use cpi_translate qw(xprint);
use cpi_db qw(DBadd DBdel DBdelkey DBget DBnewkey DBpop DBput DBread DBwrite dbget dbread);
use cpi_filename qw(filename_to_text text_to_filename);
use cpi_file qw(cleanup echodo fatal files_in read_file write_file);
use cpi_template qw(subst_list);
use cpi_cgi qw(show_vars);
use cpi_setup qw(setup);
use cpi_english qw( nword );


#	Some definitions:
#	game		A set of parameters which can be used to generate
#			an instance of a game, including what the board
#			would look like and what percentage of the files
#			on the board would be of each type of task.
#			Note that the difficulty of each task will be
#			determined by the user's previous attempts at
#			performing the task.  Included is the people
#			who have been invited to play the game, when
#			the game starts and when it stops.  We'll
#			probably also make the ability to clone a game
#			only changing start/stop and invitees.
#	instance	An actual game in progress.  Information includes
#			what tiles have been turned over
#	user		Keyed with same indices as common user.  User's
#			must be included in the can_run_antasgo group.
#			Includes information about how many of each step
#			user has taken.

$cpi_vars::TABLE_TAGS	= "bgcolor=\"#c0c0d0\"";
$cpi_vars::TABLE_TAGS	= "USECSS";

package main;

my $FORMNAME = "form";

&setup(
	stderr=>"Antasgo",
	#allow_account_creation=>1,
	require_valid_email=>1,
	require_valid_address=>1,
	Qpreset_language=>"en",
	Qrequire_captcha=>1
	);
$cpi_vars::URL = "https://www.brightsands.com/$cpi_vars::WEBOFFSET/$cpi_vars::PROG.cgi"
    if( ! $cpi_vars::URL && $cpi_vars::WEBOFFSET );

#my $ANDREGO_MAIL = "$cpi_vars::PROG\@$cpi_vars::DOMAIN";
my $ANDREGO_MAIL = "$cpi_vars::PROG";

#########################################################################
#	Variable declarations.						#
#########################################################################

our $AGENT		= $ENV{HTTP_USER_AGENT};

our $form_top;

$cpi_vars::SENDMAIL	= "/usr/lib/sendmail";
my $LIB			= "$cpi_vars::BASEDIR/lib";
my $LOG			= "$cpi_vars::BASEDIR/log";
my $GAME_TASKS		= "$LIB/tasks";
my $PATTERN_FILES	= "$LIB/patterns";
my $JS_DIR		= "$LIB/js";
my $HELP_DIR		= "$cpi_vars::BASEDIR/help";
my $HELP		= "$HELP_DIR/Help.html";
my $JS_ALL		= "$JS_DIR/all.js";
my $JS_USER		= "$JS_DIR/user.js";
my $JS_GAME		= "$JS_DIR/game.js";
my $JS_INSTANCE		= "$JS_DIR/instance.js";
my $JS_FOOTER		= "$JS_DIR/footer.js";
my $CURRENT_USER	= $cpi_vars::USER;
my @GAME_FORM_MUSTHAVES = ("name","pattern","start","stop","invitees");
my %PCT_OF_TYPE		= ("swap"=>5,"deduct"=>5);	#5% of non-required
my $MINRAN		= 95;
my $MAXRAN		= 120;
my $SECONDS_PER_DAY	= 24 * 60 * 60;
$cpi_vars::NOW		= time();
my $INSTANCE_CUTOFF	= $cpi_vars::NOW - 27 * $SECONDS_PER_DAY;	# 7 days ago
my $DAYS_IN_GUESS_CALC	= 4;
my $NENE		= "/usr/local/bin/nene";

$MINRAN=$MAXRAN=100;

my %game_tasks;

#########################################################################
#	Return true if the first item appears in the remaining list.	#
#########################################################################
sub inlist
    {
    my( $item, @list ) = @_;
    return grep( $_ eq $item, @list );
    }

#########################################################################
#	VERY primitive method of doing includes for javascript etc.	#
#	UNUSED.								#
#########################################################################
sub handle_includes
    {
    my( $contents ) = @_;
    my $lib = ".";
    while( 1 )
	{
	my @bpieces =
	    grep( defined($_),
		split( m~(<script)([^>]*)src="([^:">]*)"([^>]*)>(.*?)</script>|(<link)([^>]*)href="([^:">]*)"([^>]*?)/*>~ims, $contents)
	    );
	return $contents if( scalar(@bpieces) <= 1 );

	my @epieces = ();
	my ( $tag, $preincsrc, $incsrc, $postincsrc, $tagbody );
	while( my $pc = shift(@bpieces) )
	    {
	    undef $tag;
	    if( $pc eq "<script" )
		{
		( $tag, $preincsrc, $incsrc, $postincsrc, $tagbody ) =
		    ( "script", shift(@bpieces), "$lib/".shift(@bpieces), shift(@bpieces), shift(@bpieces) );
		}
	    elsif( $pc eq "<link" )
		{
		( $tag, $preincsrc, $incsrc, $postincsrc, $tagbody ) =
		    ( "style", shift(@bpieces), "$lib/".shift(@bpieces), shift(@bpieces), "" );
		}
	    if( ! $tag )
		{ push( @epieces, $pc ); }
	    else
		{
		push( @epieces,
		    "<$tag", $preincsrc, "incsrc='", $incsrc, "'",
		    $postincsrc, ">\n",
		    &read_file( $incsrc ),
		    $tagbody, "\n",
		    "</$tag>\n" );
		}
	    }
	$contents = join("",@epieces);
	}
    }

#########################################################################
#	Used by the common administrative functions.			#
#########################################################################
sub footer
    {
    my( $mode ) = @_;

    $mode = "admin" if( !defined($mode) );

    #return if( $cpi_vars::FORM{func} =~ /instance/ );

    my @s;
    push( @s, "<script type=text/javascript>\n",
	&read_file( $JS_FOOTER ), <<EOF );
</script>
<form name=footerform method=post>
<input type=hidden name=func>
<input type=hidden name=SID value="$cpi_vars::SID">
<input type=hidden name=USER value="$cpi_vars::USER">
EOF
    push( @s, <<EOF );
    <center><table $cpi_vars::TABLE_TAGS border=0>
    <tr><th><table $cpi_vars::TABLE_TAGS><tr><th
EOF
    my $gameind = $cpi_vars::FORM{gameind};
    foreach my $button (
	"Help:XL(Help)",
	"List_games:XL(Games)",
	"List_tasks:XL(Tasks)",
	"Show_user:XL(Players)",
	"Dump_user_log:XL(Dump user log)" )
        {
	my( $butdest, $buttext ) = split(/:/,$button);
	next if( $butdest eq "List_tasks" && ! &antasgo_can("read","tasks") );
	push( @s, "><input type=button help=${button}_button onClick='footerfunc(\"$butdest\");'" .
	    ( ($butdest eq $mode) ? " style='background-color:cyan'" : "" ) .
	    " value=\"$buttext\"\n" );
	}
    push( @s, ">", &logout_select(), <<EOF );
	</th></tr>
	</table></th></tr></table></center></form>
EOF
    &xprint( join("",@s) );
    }

#########################################################################
#	Return true if we need to print content header.			#
#########################################################################
sub check_if_app_needs_header()
    {
    return ! &inlist(($cpi_vars::FORM{func}||""),"download","view");
    }

#########################################################################
#	Mostly for debugging.  Pick a random file from a directory.	#
#########################################################################
sub random_file
    {
    my( $dirname ) = @_;
    my @flist = &files_in( $dirname );
    return $dirname."/".$flist[ rand(scalar(@flist)) ];
    }

#########################################################################
#	Read all the lib.pl files from the directory tree of tasks.	#
#########################################################################
sub read_game_tasks
    {
    my $task_url = $cpi_vars::URL;
    $task_url =~ s+\.cgi+/tasks+;

    foreach my $task ( &files_in( $GAME_TASKS ) )
	{
	my $fn = join("/",$GAME_TASKS,$task,"lib.pl");
	next if( ! -r $fn );
	eval( &read_file($fn) );
	my $task_name				= &filename_to_text($task);
	$game_tasks{$task}{icon}		||= "tasks/$task/icon.png";
	$game_tasks{$task}{accomplished}	= 0;
	next if( $game_tasks{$task}{range} !~ /(\d+)-(\d+)-(\d+)\s+(.*)$/ );
	$game_tasks{$task}{min}			= $1;
	$game_tasks{$task}{max}			= $2;
	$game_tasks{$task}{default}		= $3;
	$game_tasks{$task}{units}		= $4;
	$game_tasks{$task}{base_url}		= "$task_url/$task";
	$game_tasks{$task}{task_name}		= $task_name;
	$game_tasks{$task}{task_units}		= ( lc($task_name) eq ${4}."s"
						    ? $task_name : "$task_name ${4}s" );
	$game_tasks{$task}{digits}		= int( log($3)/log(10) ) + 1;
	}
    }

#########################################################################
#	Read a file in the form of a pattern.				#
#	Return hash with following elements:				#
#		$width							#
#		$height							#
#		\%num_type						#
#		\@cells							#
#		\%game_tasks						#
#########################################################################
sub form_to_static_game
    {
    my( $gameind ) = @_;

    my $static_game_json = &DBget("game",$gameind,"static");
    return &decode_json( $static_game_json ) if( $static_game_json );

    my $pattern = &DBget("game",$gameind,"pattern");
    my $contents = &read_file( $PATTERN_FILES."/".$pattern );
    my $left;
    my $right;
    my $top;
    my $bottom;
    my $linenum=0;
    my %num_type;

    $contents =~ s/\w/1/g;
    $contents =~ s/[^\w\n]/0/g;
    foreach my $ln ( split(/\n/,$contents) )
	{
	if( $ln =~ /1/ )
	    {
	    $top = $linenum if( ! defined($top) );
	    $bottom = $linenum;
	    $_=$ln;	s/1.*//;	$_=length($_);
	    $left=$_ if( !defined($left) || $_<$left );
	    $_=$ln;	s/[^1]$//;	$_=length($_);
	    $right=$_ if( !defined($right) || $_>$right );
	    }
	$linenum++;
	}
    $linenum=0;
    my $width = $right - $left;
    my $height = $bottom - $top + 1;
    my @cells;
    foreach my $ln ( split(/\n/ms,$contents) )
	{
	next if( $linenum<$top || $linenum > $bottom );
	foreach $_ ( split(//,sprintf("%-*s",$width,substr($ln,$left))))
	    {
	    my $type = ( $_ eq "1" ? "required" : "other" );
	    $num_type{$type}++;
	    push( @cells, {type=>$type} );
	    }
	}

    foreach my $tsk ( keys %game_tasks )
	{
	$game_tasks{$tsk}{odds} = &DBget("game",$gameind,$tsk)
	    if( &DBget("game",$gameind,$tsk) );
	}

    return
	{	width		=>$width,
		height		=>$height,
		num_type	=>\%num_type,
		pattern		=>$pattern,
		cells		=>\@cells,
		tasks		=>\%game_tasks,
		mode		=>"uncover",
		gameind		=>$gameind };
    }

#########################################################################
#	Given parameters, return javascript to play a game.		#
#########################################################################
sub user_specific_game
    {
    my( $gameind, $userind ) = @_;

    my $game_p = &form_to_static_game( $gameind );

    my @task_map;
    foreach my $tsk ( keys %{$game_p->{tasks}} )
	{
	for( my $ctr=($game_p->{tasks}{$tsk}{odds}||0); $ctr-->0; )
	    { push(@task_map,$tsk); }
	}

    my %num_tiles_of_task;
    my %num_required_tiles_of_task;
    foreach my $cell_p ( @{$game_p->{cells}} )
	{
	my $cell_task		= $task_map[ rand(@task_map) ];
	$cell_p->{task}		= $cell_task;
	$num_tiles_of_task{$cell_task}++;
	$num_required_tiles_of_task{$cell_task}++
	    if( $cell_p->{typel} eq "required" );
	}

    my $duration
	= &DBget("game",$gameind,"stop")
	- &DBget("game",$gameind,"start");
    printf("In %d seconds or %.3f days:<br>\n",
	$duration,1.0*$duration/$SECONDS_PER_DAY);
    my %task_difficulty;
    my( $task_sum_p, $task_last_p, $task_all_p, $task_day_sum_p )
        = &user_event_log( $cpi_vars::USER, undef, 0, 0,);
    foreach my $tsk ( keys %num_tiles_of_task )
	{
#	my $days = &DBget("days",$userind,$tsk)||1;
#	my $total = &DBget("total",$userind,$tsk)
#		    || $game_p->{tasks}{$tsk}{default};
#	my $count_per_day = 1.0 * $total / $days;
	my ( $days, $total, $per_day )
	    = &calculate_user_goal_per_day( $tsk, $task_day_sum_p->{$tsk} );
        $task_difficulty{$tsk} =
	    $per_day * $duration / $SECONDS_PER_DAY /
	    ($num_required_tiles_of_task{$tsk}||$num_tiles_of_task{$tsk});
	printf("%s days=%d total=%d count/day=%f nt=%d dif=%f.<br>\n",
	    $tsk, $days, $total, $per_day,
	    $num_tiles_of_task{$tsk}, $task_difficulty{$tsk} );
	}

    my $num_required = 0;
    my $num_not_required = 0;
    foreach my $cell_p ( @{$game_p->{cells}} )
	{
	my $tsk			= $cell_p->{task};
	$cell_p->{start}	= int($task_difficulty{$tsk}
				      * ($MINRAN+rand($MAXRAN-$MINRAN)) / 100);
	$cell_p->{start}	= 1 if( $cell_p->{start} <= 0 );
	$cell_p->{left}		= $cell_p->{start};
	if( $cell_p->{type} eq "required" )
	    { $num_required++; }
	else
	    { $num_not_required++; }
	#print join(" ",( map {$_=$cell{$_}} sort keys %cell )),".<br>\n";
	}

    foreach my $type ( keys %PCT_OF_TYPE )
	{
	# $game_p->{tasks}{num_type}{$type} += $PCT_OF_TYPE{$type};
	# $game_p->{tasks}{num_type}{other} -= $PCT_OF_TYPE{$type};
	for( my $ctr=int($PCT_OF_TYPE{$type}*$num_not_required/100); $ctr-->0; )
	    {
	    do { $_=rand(scalar(@{$game_p->{cells}})); }
		while( $game_p->{cells}[$_]{type} ne "other" );
	    $game_p->{cells}[$_]{type} = $type;
	    }
	}

    return $game_p;
    }

#########################################################################
#	Rudimentary permission logic.					#
#########################################################################
sub antasgo_can
    {
    my( $op, $thing, $ind ) = @_;

    return $CURRENT_USER eq "chris" if( $thing eq "tasks" );

    #return &inlist($CURRENT_USER,split(/,/,&DBget($thing,$ind,$op)));
    #my @able_users = split( /,/, &DBget($thing,$ind,$op) );
    my @able_users = &DBget($thing,$ind,$op);
    return &inlist($CURRENT_USER,@able_users);
    }

#########################################################################
#	Convert a player to a string containing the player and time	#
#	they won which should sort correctly.  HACK!			#
#########################################################################
sub sort_invitee
    {
    my( $gameind, $u ) = @_;
    my $modified = &DBget("completed",$gameind,$u);
    $modified = ( $modified ? &time_to_str($modified) : "Playing" );
    return $modified . " " . $u;
    }

#########################################################################
#	Convert a player to a string to sort order of who is winning.	#
#########################################################################
sub sort_winner
    {
    my( $gameind, $u ) = @_;
    my $modified = &DBget("completed",$gameind,$u);
    $modified = ( $modified ? &time_to_str($modified) : "Playing" );
    return $modified . " " . $u;
    }

#########################################################################
#	Convert a player to a string containing the player and time	#
#	they won which should sort correctly.  HACK!			#
#########################################################################
sub invitee
    {
    my( $gameind, $u ) = @_;
    my $modified = &DBget("completed",$gameind,$u);
    $modified = ( $modified ? &time_to_str($modified) : "&nbsp;" );
    return $u . "</td><td>" . $modified;
    }

#########################################################################
#	Delete existing task unimplemented for permission reasons.	#
#########################################################################
sub delete_task
    {
    &fatal("XL(No task specified.)") if( ! $cpi_vars::FORM{task_name} );
    my $task = &text_to_filename($cpi_vars::FORM{task_name} );
    my $fqdirname = "$GAME_TASKS/$task";
    &fatal("XL(Task does not exist.)") if( ! -d $fqdirname );
    system("rm -rf $fqdirname");
    delete $game_tasks{$task};
    &list_tasks();
    }

#########################################################################
#	Incoming new or updated task.  Error check and create files.	#
#########################################################################
sub update_task
    {
    my @problems = ();
    foreach my $v ("task_name","min","max","default","units")
	{
	if( ! defined($cpi_vars::FORM{$v}) )
	    { push( @problems, "$v XL(is not defined)" ); }
	elsif( &inlist($v,"min","max","default")
		&& $cpi_vars::FORM{$v} !~ /^\d+$/ )
	    { push( @problems, "$v XL(must be an integer)" ); }
	}
    &fatal( @problems ) if( @problems );

    my $task = &text_to_filename($cpi_vars::FORM{task_name});
    $cpi_vars::FORM{task_name} = &filename_to_text( $task );
    my $dname = "$GAME_TASKS/$task";
    &echodo("mkdir -p '$dname'") if( ! -d $dname );
    &write_file( "$dname/lib.pl",
	sprintf("\$game_tasks{\$task}{\"range\"}=\"%d-%d-%d %s\";\n",
	    $cpi_vars::FORM{min},
	    $cpi_vars::FORM{max},
	    $cpi_vars::FORM{default},
	    $cpi_vars::FORM{units} ) );
    &write_file( "$dname/index.html", $cpi_vars::FORM{explanation} );
    if( $cpi_vars::FORM{icon} )
	{
	my $rawfile = "$dname/icon.raw";
	&write_file( $rawfile, $cpi_vars::FORM{icon} );
	my $file_output = &read_file("file $rawfile |");
	my $cmd = "convert - -crop 1x1+1+1 txt:- <$rawfile|grep -om1 '#\\w\\+'";
	print STDERR "cmd=[$cmd]\n";
	my $bgcolor = &read_file( "$cmd |" );
	chomp( $bgcolor );
	print STDERR "bgcolor='$bgcolor'.\n";
	$cmd = join(";",
		    # https://stackoverflow.com/questions/3426059/convert-non-transparent-pixels-to-black
		    "convert - -resize 100x100 -fuzz 20% -transparent '$bgcolor' -alpha extract -threshold 0 -negate -transparent white $dname/icon.png < $rawfile"
		    );
	print STDERR "+ $cmd\n";
	system( $cmd );
	}
    $cpi_vars::FORM{arg} = $task;
    &show_task();
    }

#########################################################################
#	Show specified task and allow user to update it.		#
#########################################################################
sub show_task
    {
    my ( @s )= $form_top;
    my $task = $cpi_vars::FORM{arg};
    my $dname = "$GAME_TASKS/$task";
    my $explanation = &read_file( "$dname/index.html", "" );
    push( @s, <<EOF,
<center id=id_full_screen><table border=0 cellpadding=2 cellspacing=0>
<tr help='input_task_name'><th align=left width=50%>XL(Task name):</th><td width=50%>
EOF
	"<input type=text name=task_name value='",
	( $task ? $game_tasks{$task}{task_name} : "" ),
	"'></td></tr>\n",
	"<tr help='input_task_units'><th align=left>XL(Units):</th><td>",
	"<input type=text name=units value='",
	( $task ? $game_tasks{$task}{units} : "" ),
	"'></td></tr>\n",
	"<tr help='input_task_min_increase'><th align=left>XL(Minimum increase)</th><td>",
	"<input type=number imputmode=decimal name=min value='",
	( $task ? $game_tasks{$task}{min} : "" ),
	"'></td></tr>\n",
	"<tr help='input_task_max_increase'><th align=left>XL(Maximum increase):</th><td>",
	"<input type=number imputmode=decimal name=max value='",
	( $task ? $game_tasks{$task}{max} : "" ),
	"'></td></tr>\n",
	"<tr help='input_task_normal'><th align=left>XL(Reasonable per day):</th><td>",
	"<input type=number imputmode=decimal name=default value='",
	( $task ? $game_tasks{$task}{default} : "" ),
	"'></td></tr>\n",
	"<tr help='input_task_icon'><th align=left>XL(Icon PNG):</th><td>",
	"<input type=file name=icon accept='image/*'></td></tr>\n",
	"<tr help='input_task_help'><th align=left colspan=2>XL(Help):</th>",
	"</tr><tr><td colspan=2>",
	"<textarea rows=20 cols=80 name=explanation>",
	$explanation,
	"</textarea></td></tr>\n");
    push( @s,
	<<EOF
<tr><th align=left>
    <input type=button help='button_update_task' onClick='game_func("Update_task","");'
	    value='XL(Update)'"></th><th align=right>
	<input type=button help='button_delete_task' Qdisabled onClick='game_func("Delete_task","");'
	    value='XL(Delete)'"></th></tr></table></th></tr>
</table></center></form>
EOF
    );
    &xprint(
        &subst_list(
	    join("",@s),
	    '%%JSCRIPT%%',''
	));
    &footer("List_tasks");
    &cleanup( 0 );
    }

#########################################################################
#	Display list of all the games.					#
#########################################################################
sub list_games
    {
    my( @s ) = $form_top;
    my @games = &DBget( "games" );
    my $jscript = &read_file( $JS_ALL );

    push( @s, <<EOF );
<script>
%%JSCRIPT%%
</script>
<input type=hidden name=gameind value="">
<center id=id_full_screen>
<table border=1 style='border-collapse:collapse;border:solid'>
<tr><th>XL(Select)</th>
    <th>XL(Game)</th>
    <th>XL(Start)<br>XL(Stop)</th>
    <th>XL(Pattern)</th>
    <th>XL(Tasks)</th>
    <th>XL(Modified)</th>
    <th>XL(Player)</th>
    <th>XL(Done)</th>
    </tr>
EOF

    foreach my $gameind ( @games )
        {
	next if( ! &antasgo_can( "read", "game", $gameind ) );
	my @invitees = split(/,/,&DBget("game",$gameind,"invitees"));
	my $rs = " rowspan=".scalar(@invitees);
	my @tsklist =
	    map {"<nobr>".&DBget("game",$gameind,"$_")." ".&filename_to_text($_)."</nobr>"}
		sort
	            grep( &DBget("game",$gameind,"$_"), %game_tasks );
	push( @s, "<tr><th$rs>",
	    ( &antasgo_can("write","game",$gameind)
	        ? "<input type=button help='button_edit_game' value='XL(Edit)' onClick='game_func(\"Show_game\",\"$gameind\");'><br>"
		: "" ),
	    ( &antasgo_can("read","game",$gameind)
	        ? "<input type=button help='button_play_game' value='XL(Play)' onClick='game_func(\"Show_instance\",\"$gameind\");'>"
		: "" ),
	    "</th><td$rs valign=top>",
	    &DBget("game",$gameind,"name"),
	    "</td><td$rs valign=top>",
	    &time_to_str( &DBget("game",$gameind,"start") ), "<br>",
	    &time_to_str( &DBget("game",$gameind,"stop") ),
	    "</td><td$rs valign=top>",
	    &DBget("game",$gameind,"pattern"),
	    "</td><td$rs valign=top>",
	    join(", ",@tsklist),
	    "</td><td$rs valign=top>",
	    &DBget("game",$gameind,"modified"),
	    " ",
	    &DBget("game",$gameind,"owner"),
	    "</td><td valign=top>",
		join("</td></tr><tr><td valign=top>",
		    map { &invitee($gameind,$_) }
			sort {	&sort_invitee($gameind,$a) cmp
				&sort_invitee($gameind,$b) }
			    @invitees ),
	    "</td></tr>\n" );
	}
    push( @s, <<EOF );
<tr><th colspan=9><input type=button help='button_add_game' onClick='game_func(\"Show_game\",\"\");' value="XL(Add game)"></th></tr>
</table></center></form>
EOF
    &xprint(
	&subst_list(
	    join("",@s),
	    "%%JSCRIPT%%",$jscript
	));
    &footer("List_games");
    }

#########################################################################
#	Display list of all the tasks.					#
#########################################################################
sub list_tasks
    {
    my( @s ) = $form_top;
    my $jscript = &read_file( $JS_ALL );

    push( @s, <<EOF );
<script>
%%JSCRIPT%%
</script>
<center id=id_full_screen>
<table border=1 style='border-collapse:collapse;border:solid'>
<tr><th>XL(Task)</th>
    <th>XL(Minimum)</th>
    <th>XL(Maximum)</th>
    <th>XL(Default)</th>
    <th>XL(Units)</th>
    <th>XL(Icon)</th>
EOF

    foreach my $tsk ( sort keys %game_tasks )
	{
	my $task_url = $cpi_vars::URL;
	$task_url =~ s+\.cgi$+/tasks/$tsk+;
	my $click = "onClick='game_func(\"Show_task\",\"$tsk\");'";
	push( @s, "</tr>\n<tr>",
	    "<td><input type=button style='width:100%;text-align:left;' help='button_view_task' value='",
	    "XL(",$game_tasks{$tsk}{task_name},")' $click></td>",
	    "<td align=right>", $game_tasks{$tsk}{min}, "</td>",
	    "<td align=right>", $game_tasks{$tsk}{max}, "</td>",
	    "<td align=right>", $game_tasks{$tsk}{default}, "</td>",
	    "<td align=right>XL(", $game_tasks{$tsk}{units}, "s)</td>",
	    "<td align=center>",
		"<img alt='$tsk alternate'",
		    " width=25px",
		    " height=25px",
		    " src='",$game_tasks{$tsk}{icon},"'>",
		"</td>" );
	}
    push( @s, <<EOF );
</tr><tr><th colspan=6><input type=button help='button_add_task' onClick='game_func(\"Show_task\",\"\");' value="XL(Add task)"></th></tr>
</table></center></form>
EOF
    &xprint(
	&subst_list(
	    join("",@s),
	    "%%JSCRIPT%%",$jscript
	));
    &footer("List_tasks");
    }

#########################################################################
#########################################################################
sub QDBget
    {
    my( $tbl, $ind, $fld ) = @_;
    my $ret = &DBget( $tbl, $ind, $fld );
    print STDERR "DBget(",
	join(",",
	    ($tbl||"UNDEF"),
	    ($ind||"UNDEF"),
	    ($fld||"UNDEF")),") returns [",$ret||"UNDEF","]\n";
    return $ret;
    }

#########################################################################
#	Create some e-mail.						#
#	Right now, this is really stupid.  It generates all of the	#
#	email and then only sends out to the specified list of users.	#
#########################################################################
sub generate_email
    {
    my( $dest ) = @_;

    &dbread( $cpi_vars::ACCOUNTDB );

    my @dests =
	( ( !$dest || $dest eq "all" )
	? &all_prog_users()
	: ( $dest ) );
    #print "dests=[",join(":",@dests),"].\n";

    &DBread();

    my $since = &DBget("last_dump") || 0;

    my %tables_per_user = ();
    foreach my $gameind ( &DBget( "games" ) )
        {
	if( &DBget("game",$gameind,"start") >= $INSTANCE_CUTOFF )
	    {	# We don't care about old games
	    my $game_table = &instance_status_to_table( $gameind );
	    foreach my $u ( split(/,/,&DBget("game",$gameind,"invitees")) )
	        { $tables_per_user{$u}{$gameind} = $game_table; }
	    }
	}

    foreach $dest ( @dests )
	{
        my $dest_email =
	    &dbget($cpi_vars::ACCOUNTDB, "users", $dest, "email");
	if( ! $dest_email )
	    { print "${dest}:  No e-mail on record.  Skipping.\n"; }
	else
	    {
	    my @s;
	    if( $tables_per_user{$dest} )
		{
		foreach my $gameind
		    ( sort
			{ &DBget("game",$a,"name") cmp &DBget("game",$b,"name") }
			keys %{$tables_per_user{$dest}} )
		    {
		    my $start = &DBget("game",$gameind,"start");
		    my $stop = &DBget("game",$gameind,"stop");
		    my ( $status, $color ) =
			( $cpi_vars::NOW < $start		? ("will run","lightBlue")
			: $cpi_vars::NOW > $stop		? ("ran","lightGrey")
			:			  ("is running","lightGreen") );
		    push( @s, "<br><div style='background-color:$color'>",
			&DBget("game",$gameind,"name" ), " ",
			$status, " from ",
			&time_to_str($start), " to ",
			&time_to_str($stop), ":</div>",
			$tables_per_user{$dest}{$gameind} );
		    }
		}

	    push( @s, "\n<p>Activity since ",&time_to_str($since),":$_" )
	        if( $_ = &log_dump_string( $dest, undef, $since, 0 ) );

	    if( ! @s )
		{ print "${dest}:  No current games or activity.  Skipping.\n"; }
	    else
		{
		${cpi_vars::PROG} if(0);	# Get rid of only used once warnings
		print "${dest}:  Sending report to $dest_email.\n";
		my $mime_msg = MIME::Lite->new
		    (
		    From	=> $ANDREGO_MAIL,
		    To		=> $dest_email,
		    Subject	=> "Your ${cpi_vars::PROG} games",
		    Type	=> "Multipart/mixed"
		    ) || die("Cannot setup mime:  $!");

		$mime_msg->attach
		    (
		    Type	=> "text/html",
		    Encoding	=> "base64",
		    Data	=> join("",
					"<html><head></head><body>\n",
					@s,
		    			"</body></html>")
		    ) || die("Cannot attach to mime message:  $!");

		open( OUT, "| $cpi_vars::SENDMAIL -t 2>&1" )
		    || die("Cannot run $cpi_vars::SENDMAIL:  $!");
		print OUT $mime_msg->as_string;
		close( OUT );
		}
	    }
	}
    &DBwrite();
    &DBput( "last_dump", $cpi_vars::NOW );
    &DBpop();
    &cleanup(0);
    }

#########################################################################
#	Turn a filename into the probable menu item name.		#
#########################################################################
sub filename_to_item
    {
    my( $fn ) = @_;
    $fn =~ s+.*/++;
    $fn =~ s+\.jpg$++;
    $fn =~ s/_/ /g;
    return $fn;
    }

#########################################################################
#	Return string unique per day.  Used to verify if two events	#
#	happened on the same clock day.					#
#########################################################################
sub day_of
    {
    my($sec,$min,$hour,$mday,$month,$year) = localtime($_[0]);
    return sprintf("%04d-%02d-%02d", $year+1900, $month+1, $mday );
    }

#########################################################################
#	Convert seconds since the epoch to whatever I decide works out	#
#	to be the most flexible format.  May well just call one of the	#
#	standard routines.						#
#########################################################################
sub time_to_str
    {
    my($sec,$min,$hour,$mday,$month,$year) = localtime($_[0]);
    return sprintf("%04d-%02d-%02d:%02d:%02d:%02d",
	$year+1900, $month+1, $mday, $hour, $min, $sec );
    }

#########################################################################
#	Convert seconds since the epoch to format html			#
#	<input type=datetime-local> likes				#
#########################################################################
sub time_to_datetimelocal
    {
    my($sec,$min,$hour,$mday,$month,$year) = localtime($_[0]);
    return sprintf("%04d-%02d-%02dT%02d:%02d:%02d",
	$year+1900, $month+1, $mday, $hour, $min, $sec );
    }

#########################################################################
#	Return seconds since the epoch.					#
#########################################################################
sub seconds_since_epoch
    {
    my( $orig ) = @_;
    return $cpi_vars::NOW			if( ! $orig );
    return $orig		if( $orig =~ /^\d+$/ );
    return str2time($orig);
    }

#########################################################################
#	Return events since a particular date/time for a user		#
#########################################################################
sub user_event_log
    {
    my( $user, $check_task, $start_at, $stop_at ) = @_;
    #print "user_event_log($user,$check_task,$start_at,$stop_at)<br>\n";
    my $logfile = join("/",$LOG,$user);
    my %task_sum;
    my %task_last;
    my %task_all;
    my %task_day_sum;
    if( open(INF,$logfile) )
	{
	while( $_ = <INF> )
	    {
	    chomp($_);
	    if( /^([^\s]+)\s+(.*?)\s+(\d+)\s*$/ )
		{ my ($when,$task,$count) = ($1,$2,$3);
		next if( $check_task && $task ne $check_task );
		$when = &seconds_since_epoch($when) if( $when !~ /^\d+$/ );
		#print "$task comparing when=$when start_at=$start_at stop_at=$stop_at.<br>\n";
		$task_day_sum{$task}{ &day_of($when) } += $count;
		next if( $start_at && $when < $start_at );
		next if( $stop_at && $when > $stop_at );
		#print "$task had $count when $when > since $start_at.<br>\n";
		push( @{$task_all{$task}}, { when=>$when, count=>$count } );
		$task_last{$task} = $when
		    if( ! $task_last{$task} || $when > $task_last{$task} );
		$task_sum{$task} += $count;
		}
	    }
	close(INF);
	}
#    print "user_event_log tasks = [",
#	join(', ',map { "$_=$task_sum{$_}" } sort keys %task_sum ),"]<br>\n";
    return ( \%task_sum, \%task_last, \%task_all, \%task_day_sum );
    }

#########################################################################
#	User has completed some part of a task.				#
#########################################################################
sub update_user_task
    {
    my $argp = &decode_json( $cpi_vars::FORM{arg} );
    my $userind		=		$argp->{userind} || $CURRENT_USER;
    my $task		=		$argp->{task};
    my $to_add		=		$argp->{to_add};
    my $caller		=		$argp->{caller};
    my $arg		=		$argp->{arg};

    if( ! $argp->{goback} )
	{
	my $modified = $cpi_vars::NOW;

	my $logfile = join("/",$LOG,$cpi_vars::USER);
	open(LOGF,">>$logfile")||&fatal("Cannot append to ${logfile}:  $!");
	print LOGF join("\t",&time_to_str($modified),$task,$to_add),"\n";
	close( LOGF );

	&DBwrite();

	my $last_modified	= &DBget("modified",	$userind,$task) || 0;
	my $total		= &DBget("total",	$userind,$task) || 0;
	my $days		= &DBget("days",	$userind,$task) || 0;

	$modified = &seconds_since_epoch( $modified );
	$last_modified = &seconds_since_epoch( $last_modified );
	#print "modified=$modified last_modified=$last_modified.<br>\n";
	&DBput("modified",$userind,$task,$modified);
	&DBput("total",$userind,$task,$total+=$to_add);

	#print "Comparing [$last_modified] with [",day_of($modified),"]<br>\n";
	&DBput("days",$userind,$task,++$days)
	    if( &day_of($last_modified) ne &day_of($modified) );
	&DBpop();
	}

    $cpi_vars::FORM{userind} = $userind;

    #print "Caller=",($caller||"UNDEF"), ", arg=",($arg||"UNDEF"), ".<br>\n";
    if( $caller && $caller eq "instance" )
	{
	$cpi_vars::FORM{gameind} = $arg;
	&show_instance(0);
	}
    else
        { &show_user(); }
    }

#########################################################################
#	From the log, calculate what the goal should for this user	#
#	should be for this task.					#
#########################################################################
sub calculate_user_goal_per_day
    {
    my( $tsk, $day_sum_p ) = @_;
    my $days=0;
    my $total=0;
    my $per_day=0;
    my $today = &day_of( $cpi_vars::NOW );
    if( $day_sum_p )
	{
	my @days_of_task = sort keys %{ $day_sum_p };

	# Ignore today
	pop( @days_of_task ) if( $days_of_task[$#days_of_task] eq $today );

	if( @days_of_task )
	    {
	    $days = scalar( @days_of_task );
	    grep( $total+=$day_sum_p->{$_}, @days_of_task );

	    my $day_count;
	    for($day_count=0;
		@days_of_task && $day_count<$DAYS_IN_GUESS_CALC;
		$day_count++ )
		{
		$per_day += $day_sum_p->{pop(@days_of_task)};
		}
	    $per_day /= $day_count;
	    }
	}
    $per_day = $game_tasks{$tsk}{default} if( $days==0 );
    return ( $days, $total, $per_day, ($day_sum_p->{$today} || 0) );
    }

#########################################################################
#	User is viewing statistics on various tasks done previously.	#
#########################################################################
sub show_user
    {
    my ( @s )= $form_top;
    my $ntasks = scalar( keys %game_tasks );
    my $userind = $cpi_vars::FORM{userind} || $cpi_vars::FORM{arg} || $cpi_vars::USER;
    #print "f=$cpi_vars::FORM{userind} a=$cpi_vars::FORM{arg} u=$cpi_vars::USER.<br>\n";
    $cpi_vars::FORM{userind} = $userind;
    my $can_edit = ( $cpi_vars::FORM{userind} eq $cpi_vars::USER );

    my $check_group = &name_to_group( "can_run_" . $cpi_vars::PROG );
    my @ulist = &all_prog_users();
    $_ = ( scalar(@ulist) > 10 ? 10 : scalar(@ulist) ) + 1;

    push( @s, <<EOF );
<center id=id_full_screen><table border=0 cellspacing=0 cellpadding=2>
<tr><th align=left>XL(Player name):</th>
<td colspan=4><select name=userind size=$_
  onChange='game_func("Show_user");'>
<option disabled>XL(Select player to view)</option>
EOF
    foreach my $u ( @ulist )
	{
	push( @s, "<option value='$u'".($u eq $userind ? " selected":"").">",
	    &dbget($cpi_vars::ACCOUNTDB,"users",$u,"fullname"),
	    "</option>\n" );
	}
    push( @s, <<EOF );
</select></td></tr><tr>
EOF
    my( $task_sum_p, $task_last_p, $task_all_p, $task_day_sum_p )
	= &user_event_log( $userind, undef, 0, 0,);
    push( @s, map{"<th>XL($_)</th>"} ("Task","Total","Days","Recent per day","Units") );
    foreach my $tsk ( sort keys %game_tasks )
	{
	my $modified	= &DBget("modified",	$userind,$tsk)||0;
	my $click	= "onClick='update_user_task(\"$userind\",\"$tsk\",\"Show_user\",\"\");'";
	my $task_url = $cpi_vars::URL;
	$task_url =~ s+\.cgi$+/tasks/$tsk+;

#	my( $task_sum_p, $task_last_p, $task_all_p, $task_day_sum_p )
#	    = &user_event_log( $userind, undef, 0, 0,);
	my ( $days, $total, $per_day, $done_today )
	    = &calculate_user_goal_per_day( $tsk, $task_day_sum_p->{$tsk} );
	push( @s, "</tr>\n<tr>",
	    "<td><input type=button style='width:100%;text-align:left;' value='",
	    "XL(",$game_tasks{$tsk}{task_name},")' $click></td>",
	    "<td align=right>$total+$done_today</td>\n",
	    "<td align=right>$days</td>\n",
	    "<td align=right>", sprintf("%.3f",$per_day), "</td>",
	    "<td>", $game_tasks{$tsk}{units}, "s</td>" );
	}
    push( @s, <<EOF );
</tr></table></center></form>
EOF
    my $jscript = &read_file($JS_ALL). &read_file($JS_USER);
    my $json_game_tasks = &encode_json( \%game_tasks );
    $_ = join("",@s);
    &xprint(
        &subst_list(
	    join("",@s),
	    "%%JSCRIPT%%",$jscript,
	    "%%TASK_LIST%%",$json_game_tasks
	));
    &footer("Show_user");
    &cleanup( 0 );
    }

#########################################################################
#	User is modifying/creating a new game.				#
#########################################################################
sub show_game
    {
    my ( @s )= $form_top;
    my $ntasks = scalar( keys %game_tasks );
    my $gameind = $cpi_vars::FORM{gameind} || $cpi_vars::FORM{arg} || $cpi_vars::NOW;
    $gameind = $cpi_vars::NOW if( $gameind !~ /^\d+/ );
    $cpi_vars::FORM{gameind} = $gameind;
    grep( $cpi_vars::FORM{$_}=&DBget("game",$gameind,$_)||"",
	@GAME_FORM_MUSTHAVES );
    grep( $cpi_vars::FORM{"task_$_"}=DBget("game",$gameind,$_)||"0",
        keys %game_tasks );
    #print "CMC start was $cpi_vars::FORM{start}.<br>\n";
    $cpi_vars::FORM{start} = &seconds_since_epoch( $cpi_vars::FORM{start} );
    $cpi_vars::FORM{stop}  = &seconds_since_epoch( $cpi_vars::FORM{stop}  );
    #print "CMC start is $cpi_vars::FORM{start}.<br>\n";
    my $task_list = join(",", map { "'$_'" } keys %game_tasks );
    my $jscript = &read_file($JS_ALL). &read_file($JS_GAME);

    my $pretty_start = &time_to_datetimelocal( $cpi_vars::FORM{start} );
    my $pretty_stop  = &time_to_datetimelocal( $cpi_vars::FORM{stop}  );
    push( @s, <<EOF );
<input type=hidden name=gameind value="$gameind">
<center id=id_full_screen><table border=0 cellpadding=2 cellspacing=0>
<tr><th align=left width=50%>XL(Game name):</th><td width=50%>
	<input type=text name=name required value='$cpi_vars::FORM{name}'></td></tr>
<tr><th align=left>XL(Start game when):</th><td>
	<input type='datetime-local' required name=start value='$pretty_start'></td></tr>
<tr><th align=left>XL(Stop game when):</th><td>
	<input type='datetime-local' required name=stop value='$pretty_stop'></td></tr>
<tr><th align=left>XL(Pattern):</th><td><select required name=pattern>
EOF
    $cpi_vars::FORM{pattern} ||= "";
    push(@s,"<option selected hidden disabled>XL(Select pattern)</option>\n")
        if( ! $cpi_vars::FORM{pattern} );
    my %patlist;
    foreach my $fl ( &files_in($PATTERN_FILES,"^\\w") )
	{
	my $pat = &read_file( "$PATTERN_FILES/$fl" );
	$pat =~ s/[^O]//gms;
	$patlist{$fl} = length( $pat );
	}
    foreach my $pat (sort { $patlist{$a}<=>$patlist{$b} } keys %patlist )
	{
	push( @s, "    <option value='$pat'"
	    . ( $cpi_vars::FORM{pattern} eq $pat ? " selected" : "")
	    . ">$pat ($patlist{$pat})</option>\n" );
	}
    push( @s, <<EOF );
    </select></td></tr>
<tr><th>XL(Included tasks):</th><th>Percentage</th></tr>
EOF

    push( @s,
        map
	    { "<tr><th align=left>".$game_tasks{$_}{task_name}.":</th>"
	    . "<td><input type=number id=id_$_ name=task_$_ value='"
	    . $cpi_vars::FORM{"task_$_"}
	    . "' min=0 max=100 size=3 inputmode=decimal"
	    . " onChange='update_task_pcts();'>"
	    . "<span id=span_$_></span>"
	    . "</td></tr>\n"
	    } sort keys %game_tasks );
    my %selflag =
	map { ($_," selected") }
	    split(/,/,$cpi_vars::FORM{invitees}||"");
    my @ulist = &all_prog_users();
    $_ = ( scalar(@ulist) > 10 ? 10 : scalar(@ulist) ) + 1;
    push( @s, "<tr><th align=left valign=top>XL(Players):</th>",
	"<td><select name=invitees required size=$_ multiple>",
	"<option disabled>XL(Select users in game)</option>" );
    foreach my $u ( @ulist )
	{
	push( @s, "<option value='$u'".($selflag{$u}||"").">",
	    &dbget($cpi_vars::ACCOUNTDB,"users",$u,"fullname"),
	    "</option>" );
	}
    push( @s, <<EOF );
</select></td></tr>
<tr><th colspan=2><table width=100% border=0><tr><th align=left>
	<input type=button onClick='game_func("Update_game","$gameind");'
	    value='XL(Update)'"></th><th align=right>
	<input type=button onClick='game_func("Delete_game","$gameind");'
	    value='XL(Delete)'"></th></tr></table></th></tr>
</table></center></form>
EOF
    my $json_game_tasks = &encode_json( \%game_tasks );
    &xprint(
        &subst_list(
	    join("",@s),
	    "%%JSCRIPT%%",$jscript,
	    "%%GAME_TASKS%%",$json_game_tasks
	));
    &footer("directory");
    &xprint("<script>\nupdate_task_pcts();\n</script>\n");
    &cleanup( 0 );
    }

#########################################################################
#	Write form data to database.					#
#########################################################################
sub delete_game
    {
    my $gameind = $cpi_vars::FORM{gameind};
    &xprint("Gameind not specified.") if( ! $gameind );
    &DBwrite();
    &DBdel( "games", $gameind );
    &DBpop();
    return &list_games();
    }

#########################################################################
#	Return the first name of the supplied user.			#
#########################################################################
sub player_name
    {
    my( $name ) = &dbget($cpi_vars::ACCOUNTDB,"users",$_[0],"fullname");
    $name =~ s/ .*//g;
    return $name;
    }

#########################################################################
#	Send e-mail to all of the people playing a game.		#
#########################################################################
sub invitee_email
    {
    my( $gameind, $subject, $message ) = @_;

    foreach my $invitee ( split(/,/,&DBget("game",$gameind,"invitees")) )
	{
	my $dest_email =
	    &dbget( $cpi_vars::ACCOUNTDB, "users", $invitee, "email" );

	&sendmail( $ANDREGO_MAIL, $dest_email, $subject,
	    "Dear ".&player_name($invitee).",\n\n" . $message )
	    if( $dest_email );
	}
    }

#########################################################################
#	Write form data to database.					#
#########################################################################
sub update_game
    {
    my( $arg ) = @_;
    my $datetime = `date +"%m/%d/%Y %H:%M"`;
    chomp( $datetime );

    my @probs;
    foreach my $vn ( "gameind", @GAME_FORM_MUSTHAVES )
        {
	if( ! defined($_ = $cpi_vars::FORM{$vn}) )
            { push(@probs,"<li> $vn XL(is not set or truncated)"); }
	elsif( ($vn eq "start" || $vn eq "stop")
	    && ! /^\d$/ && !($cpi_vars::FORM{$vn}=&seconds_since_epoch($_)))
	    { push( @probs, "<li> $vn XL(is not in a known date/time format)" ); }
	}

    push( @probs, "<li> XL(Starting time must be before stopping time)" )
        if( $cpi_vars::FORM{start} >= $cpi_vars::FORM{stop} );

    if( @probs )
        {
        &xprint( join("","<ul>",@probs,"</ul>",
	    "<p><input onClick='window.history.go(-1); return false;'
		type=submit value='Go back and fix these settings.'>"));
        &cleanup();
        return;
        }
    #
    # We want time as seconds since the epoch, but if it in any other
    # form, call seconds_since_epoch() and ... um ... hope.
    $cpi_vars::FORM{start} = &seconds_since_epoch( $cpi_vars::FORM{start} );
    $cpi_vars::FORM{stop}  = &seconds_since_epoch( $cpi_vars::FORM{stop}  );

    my $gameind = $cpi_vars::FORM{gameind};

    &DBwrite();
    if( 1 )
	{
	grep( &DBput( "game", $gameind, $_, $cpi_vars::FORM{$_} ),
	    @GAME_FORM_MUSTHAVES );
	&DBput( "game", $gameind, "owner",	$CURRENT_USER );
	&DBput( "game", $gameind, "modified",	$datetime );
	grep( &DBput( "game", $gameind, $_, $cpi_vars::FORM{"task_$_"}||0),
	    keys %game_tasks );
	grep( &DBadd( "game", $gameind, "read", $_ ),
	    split(/,/,$cpi_vars::FORM{invitees}) );
	&DBadd( "game", $gameind, "read", $CURRENT_USER );
	&DBadd( "game", $gameind, "write", $CURRENT_USER );
	&DBadd( "games", $gameind );
	&DBput( "game", $gameind, "static",
	    encode_json( &form_to_static_game($gameind) ) );
	}
    else	# Currently not an option
        {
	&DBdel( "games", $gameind );
	$cpi_vars::FORM{gameind} = "";
	}
    &DBpop();

    my $game_name	= &DBget("game",$gameind,"name"),
    my $start		= &time_to_str( &DBget("game",$gameind,"start") );
    my $stop		= &time_to_str( &DBget("game",$gameind,"stop") );

    my $inviter_name = &player_name($CURRENT_USER);
    &invitee_email($gameind,
        "$inviter_name invites you to $game_name",<<EOF);
$inviter_name has invited you to a game of $game_name.

The game starts at $start and ends $stop.

Click on $cpi_vars::URL
EOF
    return &list_games();
    }

#########################################################################
#	Turn a user's log file (testing the ability to read it) into a	#
#	string.  NOT instance dependent, only user dependent.		#
#########################################################################
sub log_dump_string
    {
    my( $task_sum_p, $task_last_p, $task_all_p, $task_day_sum_p )
	= &user_event_log( @_ );
    my $today = &day_of( $cpi_vars::NOW );
    my @s;
    my $sep = "<center>"
	. "<table border=1 style='border-collapse:collapse;border:solid'>"
	. "<tr><th>Task</th><th>When</th><th>How many</th></tr>"
	. "<tr>";
    foreach my $task ( sort keys %{$task_all_p} )
	{
	my %entry_counts_towards_goal;
	if( $task_day_sum_p->{$task} )
	    {
	    my @days = sort keys %{$task_day_sum_p->{$task}};
	    pop( @days ) if( $days[$#days] eq $today );
	    for(my $daynum=0; @days && $daynum<$DAYS_IN_GUESS_CALC; $daynum++)
		{ $entry_counts_towards_goal{ pop(@days) } = 1; }
	    }
	my @entries = @{$task_all_p->{$task}};
	push( @s,"$sep<th rowspan=",scalar(@entries)," align=left valign=top>",
	    &filename_to_item($task), ":</th>\n");
	$sep = "<td>";
	foreach my $ep ( @entries )
	    {
	    my $whenstr = &time_to_str( $ep->{when} );
	    $whenstr = "<b>$whenstr</b>"
	        if( $entry_counts_towards_goal{ &day_of($ep->{when}) } );
	    push( @s, $sep, $whenstr,
		"</td><td>",
		&nword( $task, $ep->{count} ) );
	    $sep = "</td></tr>\n<tr><td>";
	    }
	$sep = "</td></tr>\n<tr>";
	}
    push( @s, "</td></tr></table>\n" ) if( @s );
    return join("",@s) || "";
    }

#########################################################################
#	Dump the user's log file (testing the ability to read it).	#
#	NOT instance dependent, only user dependent.			#
#########################################################################
sub dump_log
    {
    &xprint(
        &subst_list(
	    join("",
		$form_top,
		&log_dump_string( $cpi_vars::USER, undef, 0, 0 ),
		"</form>" ),
	    '%%JSCRIPT%%', '' ) );
    &footer("Dump_user_log");
    }

#########################################################################
#########################################################################
sub show_help
    {
    &xprint(
        &subst_list(
	    join("",
		$form_top,
		&read_file( $HELP ),
		"</form>"),
	    '%%JSCRIPT%%', '' ) );
    &footer("Help");
    }

#########################################################################
#	Figure out if the user has won the game.  Alas, no prize.	#
#########################################################################
sub game_is_winner
    {
    my( $game_p ) = @_;
    foreach my $cell_p ( @{ $game_p->{cells} } )
	{
	return 0 if( $cell_p->{type} eq "required" && $cell_p->{left} );
	}
    return 1;
    }

#########################################################################
#	Return a simple table showing the status of one user in a game.	#
#########################################################################
sub user_status_to_table
    {
    my( $gameind, $game_p, $invitee ) = @_;
    my $width = $game_p->{width};
    my $CELL_PARAMS="width=10px height=10px";
    my( @s ) = (
	"<table border=0 cellspacing=0 cellpadding=0",
	" style='font-size:2px'>" );
    my @pieces = split(//,&DBget("status",$gameind,$invitee)||"");
    my $sep = "<tr>";
    for( my $ind=0; ( defined( $_ = shift(@pieces) ) ); $ind++ )
	{
	push( @s, $sep ) if( $ind%$width == 0 );
	$sep = "</tr><tr>";
	push( @s,
	    "<th $CELL_PARAMS bgcolor=" .
		("white","gray","pink","red")[ $_ ] .
	    ">&nbsp;</th>" );
	}
    push( @s, "</tr></table>" );
    return join("",@s);
    }

#########################################################################
#	Return a string showing all of the player's stati.		#
#########################################################################
sub instance_status_to_table
    {
    my( $gameind, $game_p ) = @_;

    $game_p = &form_to_static_game( $gameind ) if( ! $game_p );
    my $width = $game_p->{width};
    my $height = $game_p->{height};
    my @invitees = split(/,/,&DBget("game",$gameind,"invitees"));
    my @tiles;
    my $offset = 0;
    my $pct = int( 100 / scalar(@invitees) );
    my @s = ("<table border=0 cellspacing=0 cellpadding=0 width=90%><tr>");
    foreach my $invitee ( @invitees )
	{
	push( @s, "<th valign=top width=$pct%><center>",
	    &player_name($invitee), "<br>",
	    &user_status_to_table($gameind,$game_p,$invitee),
	    "</center></th>" );
	}
    push( @s, "</tr></table>");
    return join("",@s);
    }

#########################################################################
#	Default screen							#
#########################################################################
sub show_instance
    {
    my( $is_update ) = @_;
    $_=$cpi_vars::BASEDIR; # Eliminate message about variable used only once
    my @s = $form_top;

    my $gameind=($cpi_vars::FORM{gameind}||$cpi_vars::FORM{arg});
    my $userind=$CURRENT_USER;

    my @game_status;
    my $game_to_write;
    my $game_p;
    if( $_ = &DBget("instance",$gameind,$cpi_vars::USER) )
	{ $game_p = &decode_json($_); }
    else
	{ $game_to_write = $game_p = &user_specific_game($gameind,$userind); }

    # $game_p now points to a fully populated game (which we might have
    # just made up), database is not writable.
    
    if( $is_update )
	{
	my $cell_ind = $cpi_vars::FORM{arg};
	if( $cell_ind =~ /(\d+),(\d+)/ )	# This is a swap
	    {
	    my( $i0, $i1 ) = ( $1, $2 );
	    my( $c0, $c1 ) = ( $game_p->{cells}[$i0], $game_p->{cells}[$i1] );
	    ( $game_p->{cells}[$i0], $game_p->{cells}[$i1] ) = ( $c1, $c0 );
	    $_ = $c0->{type};
	    $c0->{type} = ( $c1->{type} eq "required" ? "required" : "other" );
	    $c1->{type} = ( $_ eq "required" ? "required" : "other" );
	    $game_p->{mode} = "uncover";
	    }
	else
	    {
	    my $current_mode = $game_p->{mode};
	    my $cell_type = $game_p->{cells}[$cell_ind]{type};
	    my $cell_task = $game_p->{cells}[$cell_ind]{task};
	    if( $current_mode eq "uncover" )
		{
		$game_p->{tasks}{$cell_task}{used} +=
		    $game_p->{cells}[$cell_ind]{left};
		$game_p->{cells}[$cell_ind]{left} = 0;
		$game_p->{mode} =
		    ( $cell_type eq "other" || $cell_type eq "required"
		    ? "uncover"
		    : $cell_type );
		}
	    elsif( $current_mode eq "deduct" )
		{
		$game_p->{cells}[$cell_ind]{left} =
		    ( ($_=rand(100)) >= 80
		    ? 0
		    : int($game_p->{cells}[$cell_ind]{left} * $_ / 100) );
		$game_p->{mode} = "uncover";
		}
	    }
	foreach my $cell_p ( @{$game_p->{cells}} )
	    {
	    my $turned_over	= ( $cell_p->{left} == 0 ? 1 : 0 );
	    my $required	= ( $cell_p->{type} eq "required" );
	    push( @game_status,
		( $cell_p->{left} == 0 ? 1 : 0 )
	      + ( $cell_p->{type} eq "required" ? 2 : 0 ) );
	    }
	$game_to_write = $game_p;
	}

    my $winning_tasks;
    if( $game_to_write )
	{
	&DBwrite();
	if( ! $game_p->{won} && &game_is_winner( $game_p ) )
	    {
	    &DBput("completed",$gameind,$cpi_vars::USER,$cpi_vars::NOW);
	    $game_p->{won} = 1;
	    $winning_tasks = "<center><table width=80%><tr><th align=left>"
		. join("</td></tr><tr><th align=left>",
		map { &filename_to_item($_).":</th><td>".&nword($_,$game_p->{tasks}{$_}{used}) }
		    sort grep($game_p->{tasks}{$_}{used}, %{$game_p->{tasks}}))
	            . "</td></tr></table></center>";
	    }
	&DBput("instance",$gameind,$cpi_vars::USER,&encode_json($game_to_write));
	&DBput("status",$gameind,$cpi_vars::USER,join("",@game_status));
	&DBpop();
	}

    if( $winning_tasks )
        {
	my $winner_name = &player_name($cpi_vars::USER);
	my $game_name = &DBget("game",$gameind,"name");
        &invitee_email($gameind,"$winner_name has completed $game_name",<<EOF);
$winner_name has completed $game_name with:

	$winning_tasks
EOF
	}

    # For now, we really only care about the counts for the tasks involved
    # in the game.  Note that the instance DOES NOT MODIFY the number
    # counts per task, only the number of counts used in the game.
    # Therefore, the only thing we need from the log is $task_sum_p.
    # I may get rid of the rest, but for now I keep them because we
    # may want to be able to debug the log file with $task_all_p
    # which returns ALL the events per task since the beginning of time.
#    print "start($gameind)=",(&DBget("game",$gameind,"start") || 0),
#		", stop=",(&DBget("game",$gameind,"stop") || 0), ", now=",$cpi_vars::NOW,".<br>\n";
    my( $task_sum_p, $task_last_p, $task_all_p, $task_day_sum_p )
	= &user_event_log(
	    $cpi_vars::USER,
	    undef,
	    &DBget("game",$gameind,"start") || 0,
	    &DBget("game",$gameind,"stop")  || 0
	    );

    foreach my $task ( keys %{$task_sum_p} )
	{
	# $task_sum_p->{task} contains number of whatever accomplished
	# since game began.
	$game_p->{tasks}{$task}{accomplished} = $task_sum_p->{$task};
	#print "Theoretically set [$task] to ",$task_sum_p->{$task}, ".<br>\n";
	}

    my $jscript =
	&subst_list(
	    &read_file($JS_ALL)
	  . &read_file($JS_USER)
	  . &read_file($JS_INSTANCE),
	  	"%%GAME%%",&encode_json($game_p),
		"%%STATI%%",&instance_status_to_table( $gameind, $game_p ),
		"%%TASK_LIST%%",&encode_json( \%game_tasks ) );

    #my $game = ( &DBget( "game", $gameind, "data" ) || "" );
    #my $name = ( &DBget( "game", $gameind, "name" ) || "" );

    push( @s, <<EOF );
<input type=hidden name=gameind value="$gameind">
<center id=id_full_screen></center>
<script type="text/javascript">setup();</script>
</form>
EOF

    &xprint(
        &subst_list(
	    join("",@s),
	    "%%JSCRIPT%%",	$jscript,
	    "%%FORMNAME%%",	$FORMNAME,
	    "%%WEB%%",		$cpi_vars::PROG
	));
    &footer("List_games");
    &cleanup( 0 );
    }

##########################################################################
##	Player has changed something.  Update the database.		#
##########################################################################
#sub update_instance
#    {
#    print "CMC update_instance $cpi_vars::FORM{gameind}/$cpi_vars::USER<br>",
#	"with [[ ", $cpi_vars::FORM{arg}, " ]]<br>\n";
#    &DBwrite();
#    &DBput("instance",$cpi_vars::FORM{gameind},$cpi_vars::USER,
#	$cpi_vars::FORM{instance_update} );
#    &DBpop();
#    &show_instance(1);
#    }

#########################################################################
#	Handle regular user commands					#
#########################################################################
sub user_logic
    {
    my $fnc = ( $cpi_vars::FORM{func} || "" );

    # $fnc might be one of the following, but we should treat any of
    # these as the same.
    $fnc = "List_games" if( &inlist($fnc,"","dologin","email") );
 
    if( $fnc eq "Show_game" )		{ &show_game();			}
    elsif( $fnc eq "Update_game" )	{ &update_game();		}
    elsif( $fnc eq "Delete_game" )	{ &delete_game();		}
    elsif( $fnc eq "List_games" )	{ &list_games();		}

    elsif( $fnc eq "Show_instance" ) 	{ &show_instance(0);		}
    elsif( $fnc eq "Update_instance" ) 	{ &show_instance(1);		}
    elsif( $fnc eq "Update_user_task" )	{ &update_user_task();		}

    elsif( $fnc eq "Show_task" )	{ &show_task();			}
    elsif( $fnc eq "Update_task" )	{ &update_task();		}
    elsif( $fnc eq "Delete_task" )	{ &delete_task();		}
    elsif( $fnc eq "List_tasks" )	{ &list_tasks();		}

    elsif( $fnc eq "Show_user" )	{ &show_user();			}
    elsif( $fnc eq "Dump_user_log" )	{ &dump_log();			}
    elsif( $fnc eq "Help" )		{ &show_help();			}
    else
        { &fatal("Unrecognized function \"$fnc\"."); }
    }

#########################################################################
#	Main								#
#########################################################################

&read_game_tasks();

if( ($ENV{SCRIPT_NAME}||"") eq "" )
    {
    my $fnc = ( $ARGV[0] || "" );
    if( $fnc =~ /email=(.*)/ )		{ generate_email($1);	}
    else
	{
	&fatal("XL(Usage):  $cpi_vars::PROG.cgi (dump|dumpaccounts|dumptranslations|undump|undumpaccounts|undumptranslations) [ dumpname ]",0)
	}
    }

my $using_agent =
    $ENV{HTTP_USER_AGENT}
    || $cpi_vars::FORM{genform}
    || $cpi_vars::FORM{client}
    || "unknown";
my $agent =
#    ( $cpi_vars::FORM{genform} ? "PhoneGap_" . $cpi_vars::FORM{genform}
#    : $cpi_vars::FORM{client} ? "PhoneGap_" . $cpi_vars::FORM{client}
#    : $ENV{HTTP_USER_AGENT}
#    );
    (($cpi_vars::FORM{genform} || $cpi_vars::FORM{client}) ? "PhoneGap_" : "") .
    ( $using_agent =~ /iPhone/ ? "iPhone"
        : ( $using_agent =~ /Wget/ ? "iPhone"
	: ( $using_agent =~ /iPad/ ? "iPad"
	: $using_agent ) ) );

print STDERR "Using_agent=[$using_agent], Agent=[$agent]\n";

#my($nam,$pass,$uid,$gid,$quota,$comment,$gcos,$dir,$shell)
#    = getpwnam("$cpi_vars::USER");

#&show_vars()
#    if( ! &inlist(($cpi_vars::FORM{func}||""),"download","view") );

$form_top = <<EOF;
<script>

function game_func( fnc, val )
    {
    with( window.document.$FORMNAME )
	{
	func.value = fnc;
	if( typeof(val) != "undefined" ) { arg.value = val ; }
	submit();
	}
    }
%%JSCRIPT%%
</script>
</head><body $cpi_vars::BODY_TAGS onSubmit='alert("somebody submit!");'>
<iframe style='display:none' id=query_id onLoad='frame_updated();'>?</iframe>
$cpi_vars::HELP_IFRAME
<form name=$FORMNAME method=post ENCTYPE="multipart/form-data">
<input type=submit value=crap id=stupid_firefox_submit_button_bug style='display:none'>
<input type=hidden name=func>
<input type=hidden name=arg>
<input type=hidden name=SID value="$cpi_vars::SID">
<input type=hidden name=USER value="$cpi_vars::USER">
EOF

&user_logic();

&cleanup(0);
