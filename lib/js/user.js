//indx#	user.js - Support for user statistics
//@HDR@	$Id$
//@HDR@
//@HDR@	Copyright (c) 2024-2026 Christopher Caldwell (Christopher.M.Caldwell0@gmail.com)
//@HDR@
//@HDR@	Permission is hereby granted, free of charge, to any person
//@HDR@	obtaining a copy of this software and associated documentation
//@HDR@	files (the "Software"), to deal in the Software without
//@HDR@	restriction, including without limitation the rights to use,
//@HDR@	copy, modify, merge, publish, distribute, sublicense, and/or
//@HDR@	sell copies of the Software, and to permit persons to whom
//@HDR@	the Software is furnished to do so, subject to the following
//@HDR@	conditions:
//@HDR@	
//@HDR@	The above copyright notice and this permission notice shall be
//@HDR@	included in all copies or substantial portions of the Software.
//@HDR@	
//@HDR@	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
//@HDR@	KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
//@HDR@	WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
//@HDR@	AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
//@HDR@	HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
//@HDR@	WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
//@HDR@	FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
//@HDR@	OR OTHER DEALINGS IN THE SOFTWARE.
//
//hist#	2026-02-10 - Christopher.M.Caldwell0@gmail.com - Created
////////////////////////////////////////////////////////////////////////
//doc#	user.js - Support for user statistics
//////////////////////////////////////////////////////////////////////////

var TASK_LIST = %%TASK_LIST%%;
var gut_info;

//////////////////////////////////////////////////////////////////////////
//	User asking to increase number of times a particular task has	//
//	been performed.							//
//////////////////////////////////////////////////////////////////////////
function updated_user_task( completed_flag )
    {
    // alert("updated_user_task("+completed_flag+")");
    var now_str = datetimelocal_string( new Date() );
    var errs = 0;
    var msg;
    var val;

    if( ! completed_flag )
        { gut_info.goback = 1; }
    else
	{
	msg = "";
	if( ! ( val = (ebid("id_when")).value ) )
	    {
	    msg = "Must specify when (date AND time) before " + now_str
		+ " when " + gut_info.task+" was done<br>";
	    }
	else
	    {
	    gut_info.when = val;
	    }
	(ebid("id_msg_when")).innerHTML = msg;
	if( msg ) { errs++; }

	var units = TASK_LIST[gut_info.task].units+"s";
	msg = "";
	if( ! ( val = (ebid("id_to_add")).value ) )
	    {
	    msg = "Must specify how many " + units + " were done<br>";
	    }
	else if( ! /^-[0-9]+$/.test(val) && ! /^[0-9]+$/.test(val) )
	    {
	    msg = "Answer must be an integer number of " + units + "<br>";
	    }
	else if( (val=parseInt(val,10)) < 0 || val > TASK_LIST[gut_info.task].max )
	    {
	    msg = "Answer must be between "
		    + TASK_LIST[gut_info.task].min + " and "
		    + TASK_LIST[gut_info.task].max + " " + units + "<br>";
	    }
	else
	    {
	    gut_info.to_add = val;
	    }
	(ebid("id_msg_to_add")).innerHTML = msg;
	if( msg ) { errs++; }
	}

    if( ! errs )
        {
	update_server("Update_user_task",gut_info);
	}
    return;
    }

//////////////////////////////////////////////////////////////////////////
//	HTML loaded in iframe, put it in-line in the named element.	//
//////////////////////////////////////////////////////////////////////////
function html_loaded( frameptr, element_name )
    {
    element = ebid( element_name );
    element.innerHTML = frameptr.contentDocument.documentElement.innerHTML;	// Frame now gone! //
    element.style.display = 'block';
    return element;
    }

//////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////
function update_user_task( userind, task, caller, arg )
    {
    gut_info = { userind:userind, task:task, caller:caller, arg:arg };
    var plunit = TASK_LIST[task].units+"s";
    (ebid("id_full_screen")).innerHTML =
	[
	"<table border=0 cellspacing=0>",
	    "<tr><th><h1>", TASK_LIST[task].task_name,
		"</h1></th><th><img src='"+TASK_LIST[task].icon+"'</th></tr>",
	    "<tr><td colspan=2><span id=help_goes_here style='display:none'>",
		"<iframe style='display:none' src='",TASK_LIST[task].base_url,"' onLoad='html_loaded(this,\"help_goes_here\");'></iframe>",
		"</span><hr></td></tr>",
	    "<tr><th align=left>When:</th>",
		"<td><font color=red id=id_msg_when></font>",
		    "<input name=when id=id_when type=datetime-local",
			" value='", datetimelocal_string( new Date() ), "'>",
			"</td></tr>",
	    "<tr><th align=left>", TASK_LIST[task].task_units, " to log:</th>",
		"<td><font color=red id=id_msg_to_add></font>",
		    "<input name=to_add id=id_to_add type=number min=0",
			" max=",TASK_LIST[task].max,
			" size=",TASK_LIST[task].digits,
			" inputmode=decimal></td></tr>",
	    "<tr><td align=left><input type=button style='qwidth:100%'",
			" onClick='updated_user_task(0);' value=Back></td>",
		"<td align=right><input type=button style='qwidth:100%'",
			" onClick='updated_user_task(1);' value=Done></td></tr>",
	"</div></th></tr>",
	"</table>"
	].join("");
    }
