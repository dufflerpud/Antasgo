//indx#	all.js - Javascript support for all Antasgo game
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
//doc#	all.js - Javascript support for all Antasgo game
//////////////////////////////////////////////////////////////////////////

var URL_ALL_ARGS = window.location.href.split('?');
var URL_CGI = URL_ALL_ARGS.shift();
var URL_ARGS =
	( URL_ALL_ARGS.length
	? URL_ALL_ARGS[0].split('&')
	: new Array() );

//////////////////////////////////////////////////////////////////////////
//	Return time suitable for use in input type=datetime-local	//
//////////////////////////////////////////////////////////////////////////
function datetimelocal_string( today )
    {
    today.setMinutes(today.getMinutes() - today.getTimezoneOffset());
    return today.toISOString().slice(0, -1);
    }

//////////////////////////////////////////////////////////////////////////
//	Send a query upstream to be answered in the iframe query_id	//
//////////////////////////////////////////////////////////////////////////
var query_id_ptr;
function server_query( arg )
    {
    query_id_ptr ||= ebid("query_id");
    query_id_ptr.src = URL_CGI + "?" + arg
    }

//////////////////////////////////////////////////////////////////////////
//	Lightup the named screen, turn everybody else off.		//
//	If we're done, light up previous screen.			//
//////////////////////////////////////////////////////////////////////////
var screen_all_ids = {};
var screen_previous_ids = new Array();
var screen_current_id;
function lightup( id )
    {
    if( screen_previous.ids.length > 0 )
	{ screen_all_ids[screen_previous.ids.split(-1)].display = 'none'; }
    screen_previous_ids.push( id );
    alert("lightup previous_ids now ["+screen_previous_ids.join("/")+"]");
    screen_all_ids[id] ||= (ebid(id)).style;
    screen_all_ids[id].display = "on";
    }

//////////////////////////////////////////////////////////////////////////
//	Whatever the current page is is turned off.  Previous one	//
//	is turned on.							//
//////////////////////////////////////////////////////////////////////////
function lightdown()
    {
    if( screen_previous_ids.length <= 0 )
	{ alert("lightdown() called with no screens at all"); }
    else
	{ alert("lightdown() called with ["+screen_previous_ids.join(",")+"]"); }
    if( screen_previous_ids.length < 2 )
        { alert("lightdown() called without any previous screens on it."); }
    else
	{
	screen_all_ids[screen_previous_ids.pop()].display = "none";
	screen_all_ids[screen_previous_ids.split(-1)].display = "on";
	}
    }

//////////////////////////////////////////////////////////////////////////
//	Return word with first letter capitalized (ie perl's ucfirst())	//
//////////////////////////////////////////////////////////////////////////
function capitalize( s )
    {
    return s && s[0].toUpperCase() + s.slice(1);
    }

//////////////////////////////////////////////////////////////////////////
//	Draw a one-of prompt.						//
//////////////////////////////////////////////////////////////////////////
function oneof( asking, prompt_text, answers )
    {
    var s = new Array(
	"<table border=1 class=fixedtable>",
        "<tr><th width=100%>"+prompt_text+"</th></tr>" );

    for( const a of answers )
        {
	var value = a;
	var txt = a;
	var color = "";
	if( typeof( a ) == "object" )
	    { value=a.value; txt=a.txt||a.value; color=a.color||""; }
	s.push( "<tr><td>",
		"<input type=button style='background-color:"+color+"'",
		" onClick='"+asking+"(\""+ value+"\");'",
		" class=bigtext value='"+txt+"'/></td></tr>" );
	}
    s.push( "</table>" );
    (ebid("id_full_screen")).innerHTML = s.join("");
    return lightup("oneof");
    }

//////////////////////////////////////////////////////////////////////////
//	Get a number from the user by replacing current page with a	//
//	number - not interesting anywhere on mobile devices.		//
//////////////////////////////////////////////////////////////////////////
var gn_asking;
var gn_prompt;
var gn_units;
var gn_default_val;
var gn_min_val;
var gn_max_val;
function get_number_helper( val )
    {
    var s = new Array();

    // alert("CMC get_number_helper(" + (val||"UNDEF") + ")");
    if( val == undefined )
        { }
    else if( ! /^-[0-9]+$/.test(val) && ! /^[0-9]+$/.test(val) )
	{ s.push("Answer must be an integer number of ",gn_units); }
    else
	{
	val = parseInt(val,10);
	if( val < gn_min_val || val > gn_max_val )
	    { s.push( "Answer must be between "+gn_min_val+" and "+gn_max_val+".\n" ); }
	else
	    {
	    // lightdown();
	    return gn_asking( val );
	    }
	}

    s.push( gn_prompt, ":<br>",
	    "<input type=number name=task_val",
	    " inputmode=decimal autofocus",
	    " min="+gn_min_val,
	    " max="+gn_max_val,
	    " value='" + gn_default_val + "'",
	    " onChange='get_number_helper(this.value);'",
	    ">" );

    (ebid("id_full_screen")).innerHTML = s.join("");
    return 1;
    }

//////////////////////////////////////////////////////////////////////////
//	Set up global variables and then call the helper.  Structured	//
//	this way so that we can (ick) recurse.				//
//////////////////////////////////////////////////////////////////////////
function get_number( gna_asking, gna_prompt, gna_units, gna_default_val, gna_min_val, gna_max_val )
    {
    gn_asking		= gna_asking;
    gn_prompt		= gna_prompt;
    gn_units		= gna_units;
    gn_default_val	= gna_default_val;
    gn_min_val		= gna_min_val;
    gn_max_val		= gna_max_val;
//    alert(
//	"Asking=["+gn_asking+"]\n"
//    +	"prompt=["+gn_prompt+"]\n"
//    +	"gn_units=["+gn_units+"]\n"
//    +	"default_val=["+gn_default_val+"]\n"
//    +	"gn_min_val=["+gn_min_val+"]\n"
//    +	"gn_max_val=["+gn_max_val+"]\n" )

    get_number_helper();
    }

//////////////////////////////////////////////////////////////////////////
//	Get *ALL* properties from an object including inherited ones.	//
//////////////////////////////////////////////////////////////////////////
function list_all_properties(o)
    {
    var ret = new Array();
    for( ; o !== null; o=Object.getPrototypeOf(o) )
	{ ret = ret.concat( Object.getOwnPropertyNames(o) ); }
    return ret;
    }

//////////////////////////////////////////////////////////////////////////
//	Called when frame is totally loaded.				//
//////////////////////////////////////////////////////////////////////////
function frame_updated()
    {
    // alert("Frame updated!");
    }

//////////////////////////////////////////////////////////////////////////
//	Encode stuff we're passing upstream and submit form.		//
//	Note that "arg" is a hash, which gives us the ability to pass	//
//	anything we want.						//
//////////////////////////////////////////////////////////////////////////
function update_server( func, arg )
    {
    window.document.form.func.value = func;
    window.document.form.arg.value =
	( typeof arg == "object"
	? JSON.stringify( arg )
	: arg );
    // alert( "arg=["+arg+"] form=["+window.document.form.arg.value+"]" )
    window.document.form.submit();
    }

//////////////////////////////////////////////////////////////////////////
//	Basically so COMMON::logout works.				//
//////////////////////////////////////////////////////////////////////////
function submit_func( func )
    {
    window.document.form.func.value = func;
    window.document.form.submit();
    }
