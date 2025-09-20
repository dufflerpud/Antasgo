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
//	game.js		- Routines used by game design page of app.	//
//////////////////////////////////////////////////////////////////////////

var TASK_LIST = %%GAME_TASKS%%;

function update_task_pcts()
    {
    var sum = 0;
    for( const tsk in TASK_LIST )
        { sum += parseInt(window.document.form["task_"+tsk].value,10); }
    for( const tsk in TASK_LIST )
        {
	(document.getElementById("span_"+tsk)).innerHTML =
	    ( sum==0
	    ? ""
	    : Math.floor(100*window.document.form["task_"+tsk].value/sum)+"%" );
	}
    }
