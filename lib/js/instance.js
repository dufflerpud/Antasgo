//@HDR@	$Id$
//@HDR@		Copyright 2024 by
//@HDR@		Christopher Caldwell/Brightsands
//@HDR@		P.O. Box 401, Bailey Island, ME 04003
//@HDR@		All Rights Reserved
//@HDR@
//@HDR@	This software comprises unpublished confidential information
//@HDR@	of Brightsands and may not be used, copied or made available
//@HDR@	to anyone, except in accordance with the license under which
//@HDR@	it is furnished.
//////////////////////////////////////////////////////////////////////////
//	instance.js	- Routines used by instance of a running game.	//
//////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////
var DEBUG		= 0;

//////////////////////////////////////////////////////////////////////////
//	Global variables.						//
//////////////////////////////////////////////////////////////////////////

var GAME = %%GAME%%;
var SELECTABLE = { false:" style='opacity:0.3'", true:" style='opacity:1.0'" };
var NO_SWAP = -1;

//////////////////////////////////////////////////////////////////////////
//	Give a number some units (correctly pluralized) based on task.	//
//////////////////////////////////////////////////////////////////////////
function sinplu( val, tsk )
    {
    return val + " " + GAME.tasks[tsk].units.toLowerCase() + (val==1?"":"s");
    }

//////////////////////////////////////////////////////////////////////////
//	Called when user clicks on a cell.				//
//////////////////////////////////////////////////////////////////////////
var cell_to_swap = -1;
function update_cell( ind )
    {
    var tsk = GAME.cells[ind].task;
    var message = "";
    var header = "";
    if( GAME.mode == "uncover" )
	{
	if( GAME.cells[ind].left > GAME.tasks[tsk].accomplished )
	    {		// Should not happen because user can't click on it.
	    header=message =
		"You need at least "
		+ sinplu( GAME.cells[ind].left - GAME.tasks[tsk].accomplished, tsk )
		+ " to clear this square.";
	    }
	}
    else if( GAME.mode == "deduct" )
	{
	if( GAME.cells[ind].left <= 0 )
	    { header=message =
		"This tile is already complete.\nSelect another."; }
	}
    else if( GAME.mode == "swap" )
	{
	if( ind == cell_to_swap )
	    { header=message= "Select a different second tile to swap"; }
	else if( cell_to_swap >= 0 )
	    { ind = cell_to_swap + "," + ind; }
	else
	    {
	    cell_to_swap = ind;
	    return draw_game();
	    }
	}
    else
    	{
	header=message =
	    "Unknown game mode:  "+GAME.mode
	    + "\nThis should not happen.";
	}

    if( ! header )
        { return update_server( "Update_instance", ind ); }
    else
	{
        if( message )
	    { alert(message); }
	return draw_game( header );
	}
    }

//////////////////////////////////////////////////////////////////////////
//	Return number of points we can use to turn over a tile.		//
//////////////////////////////////////////////////////////////////////////
function useable( tsk )
    {
    return GAME.tasks[tsk].accomplished - (GAME.tasks[tsk].used||0);
    }

//////////////////////////////////////////////////////////////////////////
//	Draw the current instance.					//
//////////////////////////////////////////////////////////////////////////
function draw_game( message )
    {
    var cell_width	= Math.round(     window.innerWidth /GAME.width  ) + "px";
    var cell_height	= Math.round(     window.innerHeight/GAME.height ) + "px";
    var img_height	= Math.round( 0.6*window.innerHeight/GAME.height ) + "px";

    var s		= new Array();

    if( message )
	{ s.push( message ); }

    s.push("<table width=90%>\n<tr>");

    for( const tsk in GAME.tasks )
        { GAME.tasks[tsk].left=0; }

    if( GAME.mode == "deduct" )
        { s.push("<caption bgcolor=yellow><h2>Select a tile to make easier:</h2></caption>" ); }
    else if( GAME.mode == "swap" )
        {
	s.push("<caption bgcolor=yellow><h2>Select ",
	    (cell_to_swap < 0 ? "first" : "second" ),
	    " tile to swap:</h2></caption>" );
	}
    else
    	{ s.push("<caption><h2>Select a tile to turn over:</h2></caption>"); }
    for( const ind in GAME.cells )
	{
	if( ! /^[0-9]+$/.test(ind) )	{ continue; }
	if( ind % GAME.width==0 )	{ s.push("</tr>\n<tr>"); }
	if( ! GAME.cells[ind].left )	{ GAME.cells[ind].left= 0; }
	var tsk = GAME.cells[ind].task;
	var bgcolor =
	    ( ind == cell_to_swap
	    ? "#ffd0d0"
	    :	( GAME.cells[ind].type == "required"
	    	?   ( GAME.cells[ind].left > 0
		    ? "#a0e0ff"
		    : "#70b0ff" )
		:   ( GAME.cells[ind].left > 0
		    ? "white"
		    : "#d0d0d0" )
		)
	    )

	var can_select;
	if( GAME.mode == "uncover" )
	    {
	    can_select=(GAME.cells[ind].left>0 && useable(GAME.cells[ind].task)>=GAME.cells[ind].left);
	    // alert("ind="+ind+", task="+GAME.cells[ind].task+", saved="+GAME.tasks[GAME.cells[ind].task].accomplished+", left="+GAME.cells[ind].left+", can_select="+can_select);
	    }
	else if( GAME.mode == "deduct" )
	    { can_select = GAME.cells[ind].left; }
	else if( GAME.mode == "swap" )
	    { can_select = (cell_to_swap!=ind); }
	s.push("<th bgcolor='", bgcolor, "'",
	    ( can_select ? " onClick='update_cell("+ind+");'" : "" ),
	    " width=", cell_width,
	    " height=", cell_height, ">");
	s.push( GAME.cells[ind].type,
	    "<br>",
	    "<img",
	    SELECTABLE[ can_select ],
	    " height=", img_height,
	    " src='",GAME.tasks[tsk].icon,"'><br>" )
	if( GAME.cells[ind].left <= 0 )
	    {
	    s.push(	GAME.won && (GAME.cells[ind].type=="required")
		    ?	"<font color=red>WINNER</font>"
		    :	"Complete" )
	    }
	else
	    { s.push( sinplu(GAME.cells[ind].left,tsk) ); }
	s.push( "</th>" );
	GAME.tasks[ GAME.cells[ind].task ].left += GAME.cells[ind].left;
	sep = "</tr><tr>";
	}
    s.push("</tr></table><table width=90%><tr>");
    for( const tsk in GAME.tasks )
	{
	if( GAME.tasks[tsk].left )
	    {
	    s.push(
		"<th onClick='update_user_task(\"",
		"\",\"",tsk,
		"\",\"instance\",\"",GAME.gameind,"\");'>",
		"<img height=",img_height,"px src='",GAME.tasks[tsk].icon,"'>",
		"<br>",sinplu(useable(tsk),tsk),"</th>");
	    }
	}
    s.push("</tr></table>");
    s.push("%%STATI%%");
    (ebid("id_full_screen")).innerHTML = s.join("");
    }

//////////////////////////////////////////////////////////////////////////
//	Setup_page							//
//	Called when .html file loaded to do any javascript setup.	//
//	Obviously will not get called when javascript is not running	//
//	(which is to say, when result is being printed).		//
//////////////////////////////////////////////////////////////////////////
function setup()
    {
    draw_game();
    }
